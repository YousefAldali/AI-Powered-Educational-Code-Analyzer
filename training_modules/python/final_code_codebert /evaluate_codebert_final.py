import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics import (
    f1_score, recall_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)
import pandas as pd
import json
import os
import random
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt


# Configuration (same setup used in training + evaluation)
MODEL_NAME   = "microsoft/codebert-base"
MODEL_DIR    = "trained_model_codebert_final"
BATCH_SIZE   = 128
MAX_LEN      = 512
DEVICE       = "cuda" if torch.cuda.is_available() else "cpu"
SEED         = 42


# Model (must match the training architecture exactly)
class BugDetectionModel(nn.Module):
    def __init__(self, model_name, num_classes=2, dropout_prob=0.2):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout_prob)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # CLS token embedding
        pooled = self.dropout(pooled)
        logits = self.classifier(pooled)
        return logits


# compile-safe loading (works even if model was wrapped)
def load_state_dict_safe(model, state_dict):
    target = model._orig_mod if hasattr(model, "_orig_mod") else model
    target.load_state_dict(state_dict)


# Dataset (single snippet classification)
# - each row is a pair: buggy_code + fixed_code
# - we convert it to 2 samples: (buggy -> 1) and (fixed -> 0)
class CodeSnippetDataset(Dataset):
    def __init__(self, csv_path, tokenizer, max_len=512):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.samples = []

        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            buggy = str(row["buggy_code"]).strip()
            fixed = str(row["fixed_code"]).strip()
            self.samples.append({"code": buggy, "label": 1})
            self.samples.append({"code": fixed, "label": 0})

        # fixed shuffle for stable evaluation runs
        random.seed(SEED)
        random.shuffle(self.samples)

        n_buggy = sum(1 for s in self.samples if s["label"] == 1)
        n_clean = sum(1 for s in self.samples if s["label"] == 0)
        print(f"  Loaded {len(self.samples):,} samples ({n_buggy:,} buggy + {n_clean:,} clean)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        enc = self.tokenizer(
            item["code"],
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(item["label"], dtype=torch.long),
        }


# Plot helpers (all saved to: MODEL_DIR/results/plots/)
def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def save_roc_curve(y_true, y_prob, out_path):
    # ROC only makes sense if both classes exist
    if len(np.unique(y_true)) < 2:
        return False

    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc = roc_auc_score(y_true, y_prob)

    plt.figure()
    plt.plot(fpr, tpr, label=f"AUC = {auc:.4f}")
    plt.plot([0, 1], [0, 1], linestyle="--", label="Random")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return True


def save_pr_curve(y_true, y_prob, out_path):
    # PR only makes sense if both classes exist
    if len(np.unique(y_true)) < 2:
        return False

    precision, recall, _ = precision_recall_curve(y_true, y_prob)
    ap = average_precision_score(y_true, y_prob)

    plt.figure()
    plt.plot(recall, precision, label=f"AP = {ap:.4f}")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision–Recall Curve (Python - CodeBERT)")
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    return True


def save_confusion_matrix(cm, class_names, out_path):
    # simple confusion matrix plot (good for report screenshots)
    plt.figure()
    plt.imshow(cm, interpolation="nearest")
    plt.title("Confusion Matrix")
    plt.colorbar()

    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45, ha="right")
    plt.yticks(tick_marks, class_names)

    thresh = cm.max() / 2.0 if cm.max() > 0 else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j, i, format(cm[i, j], "d"),
                ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black"
            )

    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def save_threshold_sweep_plots(sweep_results, out_path_f1, out_path_recalls):
    # analysis only: helps show how sensitive the model is to threshold choice
    th = [r["threshold"] for r in sweep_results]
    mf1 = [r["macro_f1"] for r in sweep_results]
    cr = [r["clean_recall"] for r in sweep_results]
    br = [r["buggy_recall"] for r in sweep_results]

    plt.figure()
    plt.plot(th, mf1, marker="o")
    plt.xlabel("Threshold")
    plt.ylabel("Macro-F1")
    plt.title("Threshold Sweep: Macro-F1")
    plt.tight_layout()
    plt.savefig(out_path_f1, dpi=200)
    plt.close()

    plt.figure()
    plt.plot(th, cr, marker="o", label="Clean Recall")
    plt.plot(th, br, marker="o", label="Buggy Recall")
    plt.xlabel("Threshold")
    plt.ylabel("Recall")
    plt.title("Threshold Sweep: Recalls")
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(out_path_recalls, dpi=200)
    plt.close()


def save_length_distribution(dataset, tokenizer, out_path, title):
    # token length distribution (real length, no padding)
    # useful to check if train/val/test have similar length profiles
    lengths = []
    for sample in dataset.samples:
        toks = tokenizer(
            sample["code"],
            truncation=True,
            max_length=MAX_LEN,
            padding=False,
            return_tensors=None,
        )
        lengths.append(len(toks["input_ids"]))

    plt.figure()
    plt.hist(lengths, bins=50)
    plt.xlabel("Token Length")
    plt.ylabel("Frequency")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def save_length_overlay_by_class(dataset, tokenizer, out_path, title):
    # overlay: clean vs buggy lengths on the same plot
    # good to detect if one class is always shorter/longer (can bias training)
    clean_lengths = []
    buggy_lengths = []

    for sample in dataset.samples:
        toks = tokenizer(
            sample["code"],
            truncation=True,
            max_length=MAX_LEN,
            padding=False,
            return_tensors=None,
        )
        L = len(toks["input_ids"])
        if sample["label"] == 1:
            buggy_lengths.append(L)
        else:
            clean_lengths.append(L)

    plt.figure()
    plt.hist(clean_lengths, bins=50, alpha=0.6, label="clean")
    plt.hist(buggy_lengths, bins=50, alpha=0.6, label="buggy")
    plt.xlabel("Token Length")
    plt.ylabel("Frequency")
    plt.title(title)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()



# Main evaluation
# - choose threshold from validation (macro-F1) 
# - freeze threshold and evaluate on test
# - save plots + json results
def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    print(f"{'='*60}")
    print("CodeBERT Final -- Test Evaluation")
    print(f"{'='*60}")
    print(f"  Model dir: {MODEL_DIR}")
    print(f"  Device: {DEVICE}")

    # tokenizer should be loaded from MODEL_DIR (so it matches saved config)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

    # model base is the same name as training, weights come from MODEL_DIR
    model = BugDetectionModel(MODEL_NAME).to(DEVICE)
    state_dict = torch.load(f"{MODEL_DIR}/pytorch_model.bin", map_location=DEVICE)
    load_state_dict_safe(model, state_dict)
    model.eval()
    print("  Model loaded successfully")

    # splits created by your training script
    train_path = "temp_train_split.csv"
    val_path   = "temp_val_split.csv"
    test_path  = "temp_test_split.csv"

    if not os.path.exists(test_path):
        print(f"\n  ERROR: {test_path} not found.")
        print("  Run the training script first to create the splits.")
        return

    # load datasets
    test_dataset = CodeSnippetDataset(test_path, tokenizer, max_len=MAX_LEN)
    test_loader  = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    train_dataset = None
    if os.path.exists(train_path):
        print("\n  Loading train set (for length plots only)...")
        train_dataset = CodeSnippetDataset(train_path, tokenizer, max_len=MAX_LEN)

    # Step 1: pick threshold using validation (macro-F1)
    if os.path.exists(val_path):
        print("\n  Loading validation set for threshold selection...")
        val_dataset = CodeSnippetDataset(val_path, tokenizer, max_len=MAX_LEN)
        val_loader  = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

        val_logits_all, val_labels_all = [], []
        with torch.no_grad():
            for batch in tqdm(val_loader, desc="  Val inference", leave=False):
                input_ids = batch["input_ids"].to(DEVICE, non_blocking=True)
                attention_mask = batch["attention_mask"].to(DEVICE, non_blocking=True)
                labels = batch["labels"].to(DEVICE, non_blocking=True)

                # keep autocast for cuda only (matches your earlier scripts)
                with torch.amp.autocast(
                    device_type=DEVICE,
                    dtype=torch.bfloat16,
                    enabled=(DEVICE == "cuda"),
                ):
                    logits = model(input_ids, attention_mask)

                val_logits_all.append(logits.cpu())
                val_labels_all.append(labels.cpu())

        val_logits = torch.cat(val_logits_all, dim=0)
        val_labels = torch.cat(val_labels_all, dim=0).numpy()
        val_probs  = F.softmax(val_logits, dim=1)[:, 1].numpy()

        best_f1, chosen_thresh = 0, 0.5
        sweep_lo = max(0.05, float(val_probs.min()))
        sweep_hi = min(0.95, float(val_probs.max()))

        for t in np.linspace(sweep_lo, sweep_hi, 80):
            preds = (val_probs >= t).astype(int)
            mf1 = f1_score(val_labels, preds, average="macro", zero_division=0)
            if mf1 > best_f1:
                best_f1 = mf1
                chosen_thresh = round(float(t), 3)

        print(f"  Val macro-F1 = {best_f1:.4f} at threshold = {chosen_thresh}")
    else:
        print(f"\n  WARNING: {val_path} not found. Using default threshold 0.5")
        chosen_thresh = 0.5
        val_dataset = None

    # Step 2: test inference with frozen threshold
    print(f"\n  Running test inference at frozen threshold={chosen_thresh}...")
    test_logits_all, test_labels_all = [], []

    with torch.no_grad():
        for batch in tqdm(test_loader, desc="  Test inference", leave=False):
            input_ids = batch["input_ids"].to(DEVICE, non_blocking=True)
            attention_mask = batch["attention_mask"].to(DEVICE, non_blocking=True)
            labels = batch["labels"].to(DEVICE, non_blocking=True)

            with torch.amp.autocast(
                device_type=DEVICE,
                dtype=torch.bfloat16,
                enabled=(DEVICE == "cuda"),
            ):
                logits = model(input_ids, attention_mask)

            test_logits_all.append(logits.cpu())
            test_labels_all.append(labels.cpu())

    test_logits = torch.cat(test_logits_all, dim=0)
    test_labels = torch.cat(test_labels_all, dim=0).numpy()
    test_probs  = F.softmax(test_logits, dim=1)[:, 1].numpy()
    test_preds  = (test_probs >= chosen_thresh).astype(int)

    # Step 3: metrics
    test_macro_f1     = f1_score(test_labels, test_preds, average="macro", zero_division=0)
    test_clean_recall = recall_score(test_labels, test_preds, pos_label=0, zero_division=0)
    test_buggy_recall = recall_score(test_labels, test_preds, pos_label=1, zero_division=0)
    test_clean_f1     = f1_score(test_labels, test_preds, pos_label=0, zero_division=0)
    test_buggy_f1     = f1_score(test_labels, test_preds, pos_label=1, zero_division=0)
    test_acc          = (test_preds == test_labels).mean()

    if len(np.unique(test_labels)) > 1:
        test_auc = roc_auc_score(test_labels, test_probs)
        test_ap  = average_precision_score(test_labels, test_probs)
    else:
        test_auc = 0.5
        test_ap  = 0.5

    cm = confusion_matrix(test_labels, test_preds)
    report = classification_report(
        test_labels, test_preds,
        target_names=["clean", "buggy"],
        zero_division=0
    )

    print(f"\n{'='*60}")
    print("TEST RESULTS (frozen threshold from validation)")
    print(f"{'='*60}")
    print(f"  Threshold:      {chosen_thresh} (from validation)")
    print(f"  Accuracy:       {test_acc:.4f}")
    print(f"  AUC:            {test_auc:.4f}")
    print(f"  AP:             {test_ap:.4f}")
    print(f"  Macro-F1:       {test_macro_f1:.4f}")
    print(f"  Clean Recall:   {test_clean_recall:.4f}")
    print(f"  Buggy Recall:   {test_buggy_recall:.4f}")
    print(f"  Clean F1:       {test_clean_f1:.4f}")
    print(f"  Buggy F1:       {test_buggy_f1:.4f}")
    print(f"\n  Confusion Matrix:\n  {cm}")
    print(f"\n  Classification Report:\n{report}")

    # Threshold sweep on test (analysis only)
    print(f"\n{'='*60}")
    print("THRESHOLD SWEEP (test set -- analysis only)")
    print(f"{'='*60}")

    sweep_results = []
    sweep_lo = max(0.05, float(test_probs.min()))
    sweep_hi = min(0.95, float(test_probs.max()))

    for t in np.linspace(sweep_lo, sweep_hi, 40):
        t = round(float(t), 3)
        preds = (test_probs >= t).astype(int)
        mf1 = f1_score(test_labels, preds, average="macro", zero_division=0)
        cr  = recall_score(test_labels, preds, pos_label=0, zero_division=0)
        br  = recall_score(test_labels, preds, pos_label=1, zero_division=0)

        sweep_results.append({
            "threshold": t,
            "macro_f1": round(float(mf1), 4),
            "clean_recall": round(float(cr), 4),
            "buggy_recall": round(float(br), 4),
        })

        marker = " <-- CHOSEN" if abs(t - chosen_thresh) < 0.015 else ""
        print(f"  t={t:.3f}  macro-F1={mf1:.4f}  clean_R={cr:.4f}  buggy_R={br:.4f}{marker}")

    # Save results + plots
    results_dir = os.path.join(MODEL_DIR, "results")
    plots_dir   = os.path.join(results_dir, "plots")
    ensure_dir(results_dir)
    ensure_dir(plots_dir)

    results = {
        "task": "defect_detection_codebert_final",
        "approach": "single-snippet classification (buggy=1, clean=0)",
        "threshold": chosen_thresh,
        "threshold_source": "validation set (NOT test)",
        "test_accuracy": float(test_acc),
        "test_auc": float(test_auc),
        "test_ap": float(test_ap),
        "test_macro_f1": float(test_macro_f1),
        "test_clean_recall": float(test_clean_recall),
        "test_buggy_recall": float(test_buggy_recall),
        "test_clean_f1": float(test_clean_f1),
        "test_buggy_f1": float(test_buggy_f1),
        "confusion_matrix": cm.tolist(),
        "threshold_sweep": sweep_results,
    }

    out_path = os.path.join(results_dir, "test_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    roc_path = os.path.join(plots_dir, "roc_curve.png")
    pr_path  = os.path.join(plots_dir, "precision_recall_curve_python.png")
    cm_path  = os.path.join(plots_dir, "confusion_matrix.png")
    f1_path  = os.path.join(plots_dir, "threshold_sweep_macro_f1.png")
    rec_path = os.path.join(plots_dir, "threshold_sweep_recalls.png")

    saved_any = False
    saved_any |= save_roc_curve(test_labels, test_probs, roc_path)
    saved_any |= save_pr_curve(test_labels, test_probs, pr_path)
    save_confusion_matrix(cm, ["clean", "buggy"], cm_path)
    save_threshold_sweep_plots(sweep_results, f1_path, rec_path)

    # Length distributions (train/val/test)
    if train_dataset is not None:
        save_length_distribution(
            train_dataset, tokenizer,
            os.path.join(plots_dir, "length_dist_python_train.png"),
            "Token Length Distribution - Train (Python)"
        )
        save_length_overlay_by_class(
            train_dataset, tokenizer,
            os.path.join(plots_dir, "length_overlay_python_train.png"),
            "Token Length Overlay (Clean vs Buggy) - Train (Python)"
        )

    if os.path.exists(val_path) and "val_dataset" in locals() and val_dataset is not None:
        save_length_distribution(
            val_dataset, tokenizer,
            os.path.join(plots_dir, "length_dist_python_val.png"),
            "Token Length Distribution - Validation (Python)"
        )
        save_length_overlay_by_class(
            val_dataset, tokenizer,
            os.path.join(plots_dir, "length_overlay_python_val.png"),
            "Token Length Overlay (Clean vs Buggy) - Validation (Python)"
        )

    save_length_distribution(
        test_dataset, tokenizer,
        os.path.join(plots_dir, "length_dist_python_test.png"),
        "Token Length Distribution - Test (Python)"
    )
    save_length_overlay_by_class(
        test_dataset, tokenizer,
        os.path.join(plots_dir, "length_overlay_python_test.png"),
        "Token Length Overlay (Clean vs Buggy) - Test (Python)"
    )

    print(f"\n  Results saved to: {out_path}")
    print(f"  Plots saved to:   {plots_dir}")
    if not saved_any:
        print("  Note: ROC/PR curves skipped because only one class was present.")
    print("  Done!")


if __name__ == "__main__":
    main()