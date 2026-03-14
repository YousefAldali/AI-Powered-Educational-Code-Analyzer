import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics import (
    f1_score, recall_score, roc_auc_score, average_precision_score,
    accuracy_score, classification_report, confusion_matrix,
)
import pandas as pd
import json
import os
import random
from tqdm import tqdm
import numpy as np


# Must match the training script exactly
MODEL_NAME = "microsoft/codebert-base"
OUTPUT_DIR = "trained_model_codebert_csharp"
MAX_LEN    = 384
BATCH_SIZE = 128
SEED       = 42
DEVICE     = "cuda" if torch.cuda.is_available() else "cpu"

# Paths for the split CSVs saved during training
VAL_PATH  = "data/csharp_temp_val.csv"
TEST_PATH = "data/csharp_temp_test.csv"


# Model — must mirror the exact architecture used during training
class BugDetectionModel(nn.Module):
    def __init__(self, model_name, num_classes=2, dropout_prob=0.2):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout_prob)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]
        pooled = self.dropout(pooled)
        return self.classifier(pooled)


# Dataset — same as training
class CodeSnippetDataset(Dataset):
    def __init__(self, csv_path, tokenizer, max_len=384):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.samples = []

        df = pd.read_csv(csv_path)

        if 'code' in df.columns and 'label' in df.columns:
            for _, row in df.iterrows():
                code = str(row['code']).strip()
                label = int(row['label'])
                if len(code) >= 50:
                    self.samples.append({'code': code, 'label': label})
        elif 'buggy_code' in df.columns and 'fixed_code' in df.columns:
            for _, row in df.iterrows():
                buggy = str(row['buggy_code']).strip()
                fixed = str(row['fixed_code']).strip()
                self.samples.append({'code': buggy, 'label': 1})
                self.samples.append({'code': fixed, 'label': 0})
        else:
            raise ValueError(f"Unknown CSV format. Columns: {list(df.columns)}")

        random.shuffle(self.samples)

        n_buggy = sum(1 for s in self.samples if s['label'] == 1)
        n_clean = len(self.samples) - n_buggy
        print(f"  Loaded {len(self.samples):,} samples ({n_buggy:,} buggy + {n_clean:,} clean)")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        encoding = self.tokenizer(
            item['code'],
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(item['label'], dtype=torch.long),
        }


def load_state_dict_safe(model, state_dict):
    target = model._orig_mod if hasattr(model, '_orig_mod') else model
    target.load_state_dict(state_dict)


def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    # Check required files exist
    weights_path = f"{OUTPUT_DIR}/pytorch_model.bin"
    if not os.path.exists(weights_path):
        print(f"Model weights not found at {weights_path}. Run train_csharp.py first.")
        return

    if not os.path.exists(TEST_PATH):
        print(f"Test data not found at {TEST_PATH}. Run train_csharp.py first.")
        return

    if not os.path.exists(VAL_PATH):
        print(f"Validation data not found at {VAL_PATH}. Run train_csharp.py first.")
        return

    # Load tokenizer and model
    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(OUTPUT_DIR)
    model = BugDetectionModel(MODEL_NAME).to(DEVICE)

    state_dict = torch.load(weights_path, map_location=DEVICE)
    load_state_dict_safe(model, state_dict)
    model.eval()
    print(f"Model loaded from {weights_path}")
    print(f"Using device: {DEVICE}")

    # Load validation data to determine threshold
    print(f"\nLoading validation data from {VAL_PATH}...")
    val_dataset = CodeSnippetDataset(VAL_PATH, tokenizer, MAX_LEN)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    print("Running validation inference for threshold selection...")
    val_probs, val_labels = _run_inference(model, val_loader, DEVICE)

    # Threshold sweep on validation (same as training script)
    best_f1, chosen_thresh = 0, 0.5
    sweep_lo = max(0.05, float(val_probs.min()))
    sweep_hi = min(0.95, float(val_probs.max()))
    for threshold in np.linspace(sweep_lo, sweep_hi, 80):
        preds = (val_probs >= threshold).astype(int)
        macro_f1 = f1_score(val_labels, preds, average='macro', zero_division=0)
        if macro_f1 > best_f1:
            best_f1 = macro_f1
            chosen_thresh = round(float(threshold), 3)

    print(f"  Validation Macro-F1: {best_f1:.4f} @ threshold={chosen_thresh}")

    # Load test data
    print(f"\nLoading test data from {TEST_PATH}...")
    test_dataset = CodeSnippetDataset(TEST_PATH, tokenizer, MAX_LEN)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # Test inference
    print("Running test inference...")
    test_probs, test_labels = _run_inference(model, test_loader, DEVICE)
    test_preds = (test_probs >= chosen_thresh).astype(int)

    # Metrics
    test_f1 = f1_score(test_labels, test_preds, average='macro', zero_division=0)
    test_clean_r = recall_score(test_labels, test_preds, pos_label=0, zero_division=0)
    test_buggy_r = recall_score(test_labels, test_preds, pos_label=1, zero_division=0)
    test_acc = accuracy_score(test_labels, test_preds)
    test_auc = roc_auc_score(test_labels, test_probs) if len(np.unique(test_labels)) > 1 else 0.5
    test_ap = average_precision_score(test_labels, test_probs) if len(np.unique(test_labels)) > 1 else 0.5

    print(f"\n{'='*60}")
    print(f"TEST RESULTS (frozen threshold={chosen_thresh})")
    print(f"{'='*60}")
    print(f"  Accuracy:     {test_acc:.4f}")
    print(f"  AUC:          {test_auc:.4f}")
    print(f"  AP:           {test_ap:.4f}")
    print(f"  Macro-F1:     {test_f1:.4f}")
    print(f"  Clean Recall: {test_clean_r:.4f}")
    print(f"  Buggy Recall: {test_buggy_r:.4f}")

    print(f"\nClassification Report:")
    print(classification_report(test_labels, test_preds, target_names=["Clean", "Buggy"], digits=4))

    print("Confusion Matrix:")
    print(confusion_matrix(test_labels, test_preds))

    # Save results
    os.makedirs(f"{OUTPUT_DIR}/results", exist_ok=True)
    test_results = {
        'dataset': 'csharp_ultimate_combined.csv',
        'language': 'csharp',
        'model': MODEL_NAME,
        'approach': 'single-snippet classification',
        'threshold': chosen_thresh,
        'threshold_source': 'validation (not test)',
        'test_accuracy': float(test_acc),
        'test_auc': float(test_auc),
        'test_ap': float(test_ap),
        'test_macro_f1': float(test_f1),
        'test_clean_recall': float(test_clean_r),
        'test_buggy_recall': float(test_buggy_r),
        'val_macro_f1': best_f1,
    }
    with open(f"{OUTPUT_DIR}/results/test_results.json", 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nSaved to: {OUTPUT_DIR}/results/test_results.json")

    # Update deployment policy with correct threshold
    deployment = {
        'model': MODEL_NAME,
        'model_type': 'CodeBERT single-snippet classifier (C#)',
        'decision_threshold': chosen_thresh,
        'usage': {
            'if_P_buggy_gte_threshold': 'Flag as buggy -> call Qwen for fix + explanation',
            'if_P_buggy_lt_threshold':  'Mark as clean',
        },
        'expected_performance': {
            'macro_f1': float(test_f1),
            'clean_recall': float(test_clean_r),
            'buggy_recall': float(test_buggy_r),
        }
    }
    with open(f"{OUTPUT_DIR}/deployment_policy.json", 'w') as f:
        json.dump(deployment, f, indent=2)
    print(f"Saved to: {OUTPUT_DIR}/deployment_policy.json")

    # Error analysis — save failed cases
    _error_analysis(test_labels, test_preds, test_probs, OUTPUT_DIR)


def _run_inference(model, dataloader, device):
    # Run inference and return (probs, labels) as numpy arrays
    all_logits, all_labels = [], []

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Inference", leave=False):
            input_ids = batch['input_ids'].to(device, non_blocking=True)
            attention_mask = batch['attention_mask'].to(device, non_blocking=True)
            labels = batch['labels'].to(device, non_blocking=True)

            with torch.amp.autocast(device_type=device, dtype=torch.bfloat16, enabled=(device == "cuda")):
                logits = model(input_ids, attention_mask)

            all_logits.append(logits.cpu())
            all_labels.append(labels.cpu())

    logits = torch.cat(all_logits, dim=0)
    labels = torch.cat(all_labels, dim=0).numpy()
    probs = F.softmax(logits, dim=1)[:, 1].float().numpy()

    return probs, labels


def _error_analysis(labels, preds, probs, output_dir):
    # Save failed cases for manual inspection
    results_dir = f"{output_dir}/results"
    os.makedirs(results_dir, exist_ok=True)

    failed_indices = [i for i in range(len(labels)) if labels[i] != preds[i]]
    if not failed_indices:
        print("No failed cases.")
        return

    failed_data = []
    for i in failed_indices:
        failed_data.append({
            'index': i,
            'true_label': int(labels[i]),
            'pred_label': int(preds[i]),
            'prob_buggy': round(float(probs[i]), 4),
        })

    df_failed = pd.DataFrame(failed_data)
    csv_path = os.path.join(results_dir, "failed_cases_csharp.csv")
    df_failed.to_csv(csv_path, index=False)
    print(f"Saved {len(df_failed)} failed cases to {csv_path}")

    # Confusion matrix plot (optional)
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        cm = confusion_matrix(labels, preds)
        plt.figure(figsize=(6, 5))
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Clean", "Buggy"],
            yticklabels=["Clean", "Buggy"]
        )
        plt.title("Confusion Matrix (C#)")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig(os.path.join(results_dir, "confusion_matrix_csharp.png"))
        plt.close()
        print(f"Saved confusion matrix plot to {results_dir}")
    except ImportError:
        print("Skipping confusion matrix plot (matplotlib/seaborn not installed).")


if __name__ == "__main__":
    main()
