import argparse
import os
import sys
import json
import random
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    f1_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)
from tqdm import tqdm


# Config (must match CodeBERT.py exactly)
MODEL_NAME = "microsoft/codebert-base"
CSV_FILE = "ultimate_combined_dataset_pairs_v5.csv"
MAX_LEN = 384
BATCH_SIZE = 128
SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15


def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _default_csv_path():
    """Check a few likely locations for the dataset csv."""
    script_d = _script_dir()
    cwd = os.getcwd()
    for base in [script_d, cwd, os.path.join(script_d, "..")]:
        path = os.path.join(base, CSV_FILE)
        if os.path.isfile(path):
            return path
    return os.path.join(script_d, CSV_FILE)


# Dataset (same pair format as CodeBERT.py: buggy_code + fixed_code)
def _build_samples_from_df(df: pd.DataFrame):
    samples = []
    for _, row in df.iterrows():
        buggy = str(row["buggy_code"]).strip()
        fixed = str(row["fixed_code"]).strip()
        samples.append({"code": buggy, "label": 1})
        samples.append({"code": fixed, "label": 0})
    return samples


class CodeSnippetDataset(Dataset):
    def __init__(self, samples, tokenizer, max_len=384):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_len = max_len

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


# Split by unique ID (70/15/15, matches CodeBERT.py)
def split_by_id(df: pd.DataFrame, seed: int = SEED):
    unique_ids = df["id"].unique()
    np.random.seed(seed)
    np.random.shuffle(unique_ids)
    n = len(unique_ids)
    train_cut = int(TRAIN_RATIO * n)
    val_cut = int((TRAIN_RATIO + VAL_RATIO) * n)
    train_ids = set(unique_ids[:train_cut])
    val_ids = set(unique_ids[train_cut:val_cut])
    test_ids = set(unique_ids[val_cut:])
    train_df = df[df["id"].isin(train_ids)]
    val_df = df[df["id"].isin(val_ids)]
    test_df = df[df["id"].isin(test_ids)]
    return train_df, val_df, test_df


def get_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_base_model(device: str):
    #Load base CodeBERT with a random classification head (no fine-tuning).
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        problem_type="single_label_classification",
    )
    model.to(device)
    model.eval()
    return tokenizer, model


def run_inference(model, loader, device):
    all_probs, all_labels = [], []
    with torch.no_grad():
        for batch in tqdm(loader, desc="Inference", leave=False):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"]
            out = model(input_ids=input_ids, attention_mask=attention_mask)
            probs = F.softmax(out.logits, dim=-1)
            all_probs.append(probs[:, 1].cpu().numpy())
            all_labels.append(labels.numpy())
    return np.concatenate(all_probs), np.concatenate(all_labels)


def threshold_sweep_macro_f1(labels, probs, n_steps=80):
    #Sweep thresholds on validation to pick the best macro-F1 cutoff.
    sweep_lo = max(0.05, float(np.min(probs)))
    sweep_hi = min(0.95, float(np.max(probs)))
    best_f1, best_t = 0.0, 0.5
    for t in np.linspace(sweep_lo, sweep_hi, n_steps):
        preds = (probs >= t).astype(int)
        mf1 = f1_score(labels, preds, average="macro", zero_division=0)
        if mf1 > best_f1:
            best_f1 = mf1
            best_t = round(float(t), 3)
    return best_t, best_f1


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate pre-trained CodeBERT (same setup as CodeBERT.py)."
    )
    parser.add_argument("--csv", type=str, default=None, help=f"Path to {CSV_FILE}")
    parser.add_argument("--output_dir", type=str, default=None, help="Where to save results JSON")
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE, help="Batch size")
    args = parser.parse_args()

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    csv_path = args.csv or _default_csv_path()
    if not os.path.isfile(csv_path):
        print(f"ERROR: Dataset not found: {csv_path}")
        print(f"Place {CSV_FILE} in this folder or pass --csv /path/to/{CSV_FILE}")
        sys.exit(1)

    device = get_device()
    print(f"Device: {device}")
    print(f"Model: {MODEL_NAME} (no fine-tuned weights)")
    print(f"Dataset: {csv_path}")
    print(f"MAX_LEN: {MAX_LEN}   Split: 70/15/15 by ID (same as CodeBERT.py)")

    df = pd.read_csv(csv_path)
    print(f"  Total rows: {len(df):,}")
    train_df, val_df, test_df = split_by_id(df)
    print(f"  Train: {len(train_df):,}  Val: {len(val_df):,}  Test: {len(test_df):,}")

    val_samples = _build_samples_from_df(val_df)
    test_samples = _build_samples_from_df(test_df)
    random.seed(SEED)
    random.shuffle(val_samples)
    random.shuffle(test_samples)
    print(f"  Val samples:  {len(val_samples):,}   Test samples: {len(test_samples):,}")

    tokenizer, model = load_base_model(device)
    print("Model loaded (random head).")

    val_dataset = CodeSnippetDataset(val_samples, tokenizer, max_len=MAX_LEN)
    test_dataset = CodeSnippetDataset(test_samples, tokenizer, max_len=MAX_LEN)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False)

    # pick threshold on validation only
    print("\n--- Validation: threshold sweep (macro-F1) ---")
    val_probs, val_labels = run_inference(model, val_loader, device)
    chosen_threshold, val_macro_f1 = threshold_sweep_macro_f1(val_labels, val_probs)
    print(f"Chosen threshold: {chosen_threshold} (val macro-F1 = {val_macro_f1:.4f})")

    # freeze threshold, evaluate on test once
    print("\n--- Test: single evaluation (frozen threshold) ---")
    test_probs, test_labels = run_inference(model, test_loader, device)
    test_preds = (test_probs >= chosen_threshold).astype(int)

    test_acc = (test_preds == test_labels).mean()
    test_macro_f1 = f1_score(test_labels, test_preds, average="macro", zero_division=0)
    test_clean_recall = recall_score(test_labels, test_preds, pos_label=0, zero_division=0)
    test_buggy_recall = recall_score(test_labels, test_preds, pos_label=1, zero_division=0)
    test_clean_f1 = f1_score(test_labels, test_preds, pos_label=0, zero_division=0)
    test_buggy_f1 = f1_score(test_labels, test_preds, pos_label=1, zero_division=0)
    test_auc = roc_auc_score(test_labels, test_probs) if len(np.unique(test_labels)) > 1 else 0.5
    test_ap = average_precision_score(test_labels, test_probs) if len(np.unique(test_labels)) > 1 else 0.5

    cm = confusion_matrix(test_labels, test_preds)
    report = classification_report(test_labels, test_preds, target_names=["clean", "buggy"], zero_division=0)

    print(f"\n{'='*60}")
    print("PRE-TRAINED CodeBERT (base) — TEST RESULTS")
    print(f"{'='*60}")
    print(f"  Threshold (from val): {chosen_threshold}")
    print(f"  Accuracy:             {test_acc:.4f}")
    print(f"  Macro-F1:              {test_macro_f1:.4f}")
    print(f"  AUC:                   {test_auc:.4f}")
    print(f"  AP:                    {test_ap:.4f}")
    print(f"  Clean Recall:          {test_clean_recall:.4f}")
    print(f"  Buggy Recall:          {test_buggy_recall:.4f}")
    print(f"\n  Confusion Matrix:\n  {cm}")
    print(f"\n  Classification Report:\n{report}")
    print(f"{'='*60}\n")

    out_dir = args.output_dir or _script_dir()
    os.makedirs(out_dir, exist_ok=True)
    results = {
        "model": MODEL_NAME,
        "note": "Pre-trained CodeBERT, no fine-tuning",
        "dataset": csv_path,
        "split": "70/15/15 by unique ID (same as CodeBERT.py)",
        "max_len": MAX_LEN,
        "threshold": chosen_threshold,
        "threshold_source": "validation only, NOT test",
        "val_macro_f1_at_threshold": float(val_macro_f1),
        "test_accuracy": float(test_acc),
        "test_macro_f1": float(test_macro_f1),
        "test_auc": float(test_auc),
        "test_ap": float(test_ap),
        "test_clean_recall": float(test_clean_recall),
        "test_buggy_recall": float(test_buggy_recall),
        "test_clean_f1": float(test_clean_f1),
        "test_buggy_f1": float(test_buggy_f1),
        "confusion_matrix": cm.tolist(),
    }
    out_path = os.path.join(out_dir, "evaluate_pretrained_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {out_path}")


if __name__ == "__main__":
    main()
