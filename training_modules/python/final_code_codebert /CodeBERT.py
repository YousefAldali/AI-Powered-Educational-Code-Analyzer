import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_cosine_schedule_with_warmup
from sklearn.metrics import f1_score, recall_score, roc_auc_score, average_precision_score
import pandas as pd
import json
import os
import random
from tqdm import tqdm
import numpy as np


# GPU configuration
torch.set_float32_matmul_precision("high")
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True
    try:
        torch.backends.cuda.enable_flash_sdp(True)
        torch.backends.cuda.enable_mem_efficient_sdp(True)
    except Exception:
        pass


# Configurations
MODEL_NAME              = "microsoft/codebert-base"
BATCH_SIZE              = 128
GRAD_ACCUMULATION_STEPS = 1
MAX_LEN                 = 384
EPOCHS                  = 20
LEARNING_RATE           = 5e-6
EARLY_STOPPING_PATIENCE = 4
WARMUP_RATIO            = 0.06
DEVICE                  = "cuda" if torch.cuda.is_available() else "cpu"
OUTPUT_DIR              = "trained_model_codebert_final"
SEED                    = 42
CSV_FILE                = "combined_ctssb_synthetic_170k.csv"


# Focal Loss
class FocalLoss(nn.Module):
    def __init__(self, gamma=2.0, alpha=1.0):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits, labels):
        ce_loss = F.cross_entropy(logits, labels, reduction='none')
        p_t = torch.exp(-ce_loss)
        focal_loss = self.alpha * ((1 - p_t) ** self.gamma) * ce_loss
        return focal_loss.mean()


# Dataset: supports both formats
#   Format A (Defectors+PyVul combined): columns [code, label, source, id]
#   Format B (CTSSB original): columns [buggy_code, fixed_code, source, id]
class CodeSnippetDataset(Dataset):
    def __init__(self, csv_path, tokenizer, max_len=512):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.samples = []

        df = pd.read_csv(csv_path)

        if 'code' in df.columns and 'label' in df.columns:
            # Format A: pre-processed single-snippet (Defectors+PyVul)
            for _, row in df.iterrows():
                code = str(row['code']).strip()
                label = int(row['label'])
                if len(code) >= 50:
                    self.samples.append({'code': code, 'label': label})
        elif 'buggy_code' in df.columns and 'fixed_code' in df.columns:
            # Format B: pairs (CTSSB) -> split into 2 samples each
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


# Model
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


# torch.compile-safe helpers
def get_state_dict(model):
    return model._orig_mod.state_dict() if hasattr(model, '_orig_mod') else model.state_dict()

def load_state_dict_safe(model, state_dict):
    target = model._orig_mod if hasattr(model, '_orig_mod') else model
    target.load_state_dict(state_dict)


# Training loop
def train_epoch(model, dataloader, optimizer, scheduler, device, criterion, grad_accum_steps=1):
    model.train()
    total_loss = 0
    pbar = tqdm(dataloader, desc="Training")
    optimizer.zero_grad(set_to_none=True)

    for step, batch in enumerate(pbar):
        input_ids = batch['input_ids'].to(device, non_blocking=True)
        attention_mask = batch['attention_mask'].to(device, non_blocking=True)
        labels = batch['labels'].to(device, non_blocking=True)

        with torch.amp.autocast(device_type=device, dtype=torch.bfloat16, enabled=(device == "cuda")):
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels) / grad_accum_steps

        loss.backward()

        if (step + 1) % grad_accum_steps == 0 or (step + 1) == len(dataloader):
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad(set_to_none=True)

        total_loss += loss.item() * grad_accum_steps
        pbar.set_postfix({'loss': f"{loss.item() * grad_accum_steps:.4f}"})

    return total_loss / len(dataloader)


# Evaluation with macro-F1 threshold sweep
@torch.no_grad()
def evaluate(model, dataloader, device, criterion):
    model.eval()
    total_loss = 0
    all_logits, all_labels = [], []

    for batch in tqdm(dataloader, desc="Evaluating", leave=False):
        input_ids = batch['input_ids'].to(device, non_blocking=True)
        attention_mask = batch['attention_mask'].to(device, non_blocking=True)
        labels = batch['labels'].to(device, non_blocking=True)

        with torch.amp.autocast(device_type=device, dtype=torch.bfloat16, enabled=(device == "cuda")):
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)

        total_loss += loss.item()
        all_logits.append(logits.cpu())
        all_labels.append(labels.cpu())

    logits = torch.cat(all_logits, dim=0)
    labels = torch.cat(all_labels, dim=0)
    probs = F.softmax(logits, dim=1)[:, 1].float().numpy()
    labels = labels.numpy()

    metrics = {'loss': total_loss / len(dataloader)}

    if len(np.unique(labels)) > 1:
        metrics['auc'] = roc_auc_score(labels, probs)
        metrics['ap'] = average_precision_score(labels, probs)
    else:
        metrics['auc'] = 0.5
        metrics['ap'] = 0.5

    # Threshold sweep for MACRO-F1
    best_f1, best_threshold = 0, 0.5
    sweep_lo = max(0.05, float(probs.min()))
    sweep_hi = min(0.95, float(probs.max()))
    for threshold in np.linspace(sweep_lo, sweep_hi, 80):
        preds = (probs >= threshold).astype(int)
        macro_f1 = f1_score(labels, preds, average='macro', zero_division=0)
        if macro_f1 > best_f1:
            best_f1 = macro_f1
            best_threshold = round(float(threshold), 3)

    best_preds = (probs >= best_threshold).astype(int)
    metrics['macro_f1'] = best_f1
    metrics['best_threshold'] = best_threshold
    metrics['clean_recall'] = recall_score(labels, best_preds, pos_label=0, zero_division=0)
    metrics['buggy_recall'] = recall_score(labels, best_preds, pos_label=1, zero_division=0)
    metrics['clean_f1'] = f1_score(labels, best_preds, pos_label=0, zero_division=0)
    metrics['buggy_f1'] = f1_score(labels, best_preds, pos_label=1, zero_division=0)
    metrics['accuracy'] = (best_preds == labels).mean()

    return metrics


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = BugDetectionModel(MODEL_NAME).to(DEVICE)

    if hasattr(torch, 'compile'):
        try:
            model = torch.compile(model)
            print("torch.compile enabled")
        except Exception:
            pass

    criterion = FocalLoss(gamma=2.0, alpha=1.0)
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)

    # Load data and split by unique id
    print(f"Loading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    print(f"  Total rows: {len(df):,}")

    unique_ids = df['id'].unique()
    np.random.seed(SEED)
    np.random.shuffle(unique_ids)

    train_cut = int(0.70 * len(unique_ids))
    val_cut = int(0.85 * len(unique_ids))

    train_ids = set(unique_ids[:train_cut])
    val_ids = set(unique_ids[train_cut:val_cut])
    test_ids = set(unique_ids[val_cut:])

    train_df = df[df['id'].isin(train_ids)]
    val_df = df[df['id'].isin(val_ids)]
    test_df = df[df['id'].isin(test_ids)]

    # Save splits
    train_path, val_path, test_path = "temp_train.csv", "temp_val.csv", "temp_test.csv"
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    print(f"\n{'='*60}")
    print(f"Data split (by unique ID):")
    print(f"  Train: {len(train_df):,}")
    print(f"  Val:   {len(val_df):,}")
    print(f"  Test:  {len(test_df):,}")
    print(f"{'='*60}\n")

    train_dataset = CodeSnippetDataset(train_path, tokenizer, MAX_LEN)
    val_dataset = CodeSnippetDataset(val_path, tokenizer, MAX_LEN)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,
                              num_workers=8, pin_memory=True, prefetch_factor=4,
                              persistent_workers=True, drop_last=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False,
                            num_workers=4, pin_memory=True, prefetch_factor=2,
                            persistent_workers=True)

    total_steps = len(train_loader) * EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATIO)
    scheduler = get_cosine_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    # Training
    best_val_f1 = 0
    patience_counter = 0
    training_history = []

    for epoch in range(EPOCHS):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch + 1}/{EPOCHS}")
        print(f"{'='*60}")

        train_loss = train_epoch(model, train_loader, optimizer, scheduler, DEVICE, criterion, GRAD_ACCUMULATION_STEPS)
        val_metrics = evaluate(model, val_loader, DEVICE, criterion)

        print(f"Train Loss:   {train_loss:.4f}")
        print(f"Val Loss:     {val_metrics['loss']:.4f}")
        print(f"Val AUC:      {val_metrics['auc']:.4f}")
        print(f"Val AP:       {val_metrics['ap']:.4f}")
        print(f"Val Macro-F1: {val_metrics['macro_f1']:.4f} @ t={val_metrics['best_threshold']}")
        print(f"Val Clean R:  {val_metrics['clean_recall']:.4f}  Buggy R: {val_metrics['buggy_recall']:.4f}")

        training_history.append({
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_metrics['loss'],
            'val_auc': val_metrics['auc'],
            'val_ap': val_metrics['ap'],
            'val_macro_f1': val_metrics['macro_f1'],
            'val_clean_recall': val_metrics['clean_recall'],
            'val_buggy_recall': val_metrics['buggy_recall'],
            'best_threshold': val_metrics['best_threshold'],
        })

        current_f1 = val_metrics['macro_f1']
        if current_f1 > best_val_f1:
            best_val_f1 = current_f1
            patience_counter = 0
            torch.save(get_state_dict(model), f"{OUTPUT_DIR}/pytorch_model.bin")
            tokenizer.save_pretrained(OUTPUT_DIR)
            print(f"Best model + tokenizer saved (macro-F1: {current_f1:.4f})")
        else:
            patience_counter += 1
            print(f"No improvement ({patience_counter}/{EARLY_STOPPING_PATIENCE})")
            if patience_counter >= EARLY_STOPPING_PATIENCE:
                print(f"Early stopping at epoch {epoch + 1}")
                break

    with open(f"{OUTPUT_DIR}/training_history.json", 'w') as f:
        json.dump(training_history, f, indent=2)

    print(f"\nTraining complete! Best Val Macro-F1: {best_val_f1:.4f}")

    # Test evaluation
    print(f"\n{'='*60}")
    print("TEST EVALUATION (held-out data)")
    print(f"{'='*60}")

    test_dataset = CodeSnippetDataset(test_path, tokenizer, MAX_LEN)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    state_dict = torch.load(f"{OUTPUT_DIR}/pytorch_model.bin", map_location=DEVICE)
    load_state_dict_safe(model, state_dict)

    # Threshold from validation
    val_final = evaluate(model, val_loader, DEVICE, criterion)
    chosen_thresh = val_final['best_threshold']
    print(f"  Threshold: {chosen_thresh} (from validation)")

    # Test forward pass
    model.eval()
    all_logits_test, all_labels_test = [], []
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Test inference", leave=False):
            ids = batch['input_ids'].to(DEVICE, non_blocking=True)
            mask = batch['attention_mask'].to(DEVICE, non_blocking=True)
            labs = batch['labels'].to(DEVICE, non_blocking=True)
            with torch.amp.autocast(device_type=DEVICE, dtype=torch.bfloat16, enabled=(DEVICE == "cuda")):
                logits = model(ids, mask)
            all_logits_test.append(logits.cpu())
            all_labels_test.append(labs.cpu())

    test_logits = torch.cat(all_logits_test, dim=0)
    test_labels = torch.cat(all_labels_test, dim=0).numpy()
    test_probs = F.softmax(test_logits, dim=1)[:, 1].float().numpy()
    test_preds = (test_probs >= chosen_thresh).astype(int)

    test_f1 = f1_score(test_labels, test_preds, average='macro', zero_division=0)
    test_clean_r = recall_score(test_labels, test_preds, pos_label=0, zero_division=0)
    test_buggy_r = recall_score(test_labels, test_preds, pos_label=1, zero_division=0)
    test_acc = (test_preds == test_labels).mean()
    test_auc = roc_auc_score(test_labels, test_probs) if len(np.unique(test_labels)) > 1 else 0.5
    test_ap = average_precision_score(test_labels, test_probs) if len(np.unique(test_labels)) > 1 else 0.5

    print(f"\nTest Results (frozen threshold={chosen_thresh}):")
    print(f"  Accuracy:     {test_acc:.4f}")
    print(f"  AUC:          {test_auc:.4f}")
    print(f"  AP:           {test_ap:.4f}")
    print(f"  Macro-F1:     {test_f1:.4f}")
    print(f"  Clean Recall: {test_clean_r:.4f}")
    print(f"  Buggy Recall: {test_buggy_r:.4f}")

    os.makedirs(f"{OUTPUT_DIR}/results", exist_ok=True)
    test_results = {
        'dataset': CSV_FILE,
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
        'val_macro_f1': best_val_f1,
    }
    with open(f"{OUTPUT_DIR}/results/test_results.json", 'w') as f:
        json.dump(test_results, f, indent=2)

    deployment = {
        'model': MODEL_NAME,
        'model_type': 'CodeBERT single-snippet classifier',
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

    print(f"\nSaved to: {OUTPUT_DIR}/results/test_results.json")
    print(f"          {OUTPUT_DIR}/deployment_policy.json")


if __name__ == "__main__":
    main()