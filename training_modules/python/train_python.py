import os
import random
import difflib
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    RobertaTokenizer,
    RobertaForSequenceClassification,
    get_linear_schedule_with_warmup
)
from torch.optim import AdamW
from tqdm import tqdm
from sklearn.metrics import accuracy_score, average_precision_score, roc_auc_score

# AMP support for mixed precision training on CUDA GPUs
try:
    from torch.amp import autocast
    try:
        from torch.amp import GradScaler
    except ImportError:
        from torch.cuda.amp import GradScaler
except ImportError:
    from torch.cuda.amp import autocast, GradScaler


# Configuration parameters
BATCH_SIZE = 32                 # Number of samples per gradient update
EPOCHS = 20                     # Total number of training passes over the dataset
LEARNING_RATE = 2e-5            # Standard fine-tuning learning rate for transformers
MAX_LEN = 384                   # Maximum token length per code snippet
WINDOW_SIZE = 5                 # Lines of context around the changed code
MODEL_NAME = "microsoft/codebert-base"
OUTPUT_DIR = "trained_model_augmented"
SEED = 42                       # Ensures reproducibility

# Flexible dataset path resolution
DATA_PATH = "data/python_augmented_dataset.csv"
if not os.path.exists(DATA_PATH):
    DATA_PATH = "../../flask/data/raw/python/python_augmented_dataset.csv"
if not os.path.exists(DATA_PATH):
    DATA_PATH = "flask/data/raw/python/python_augmented_dataset.csv"


# Device selection
def get_device():
    # Prefer CUDA if available
    if torch.cuda.is_available():
        return torch.device("cuda")
    # Apple Silicon fallback
    if torch.backends.mps.is_available():
        return torch.device("mps")
    # Otherwise CPU
    return torch.device("cpu")


# Reproducibility
def set_seed(seed=42):
    # Fix all random generators for consistent experiments
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# Extract a window of context around the changed lines
def extract_diff_window(buggy_code, fixed_code, window_size=5):
    buggy_lines = str(buggy_code).split("\n")
    fixed_lines = str(fixed_code).split("\n")

    matcher = difflib.SequenceMatcher(None, buggy_lines, fixed_lines)

    buggy_changed = set()
    fixed_changed = set()

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            for i in range(i1, i2):
                buggy_changed.add(i)
            for j in range(j1, j2):
                fixed_changed.add(j)

    if not buggy_changed:
        buggy_changed.add(len(buggy_lines) // 2)
    if not fixed_changed:
        fixed_changed.add(len(fixed_lines) // 2)

    b_min = max(0, min(buggy_changed) - window_size)
    b_max = min(len(buggy_lines), max(buggy_changed) + window_size + 1)

    f_min = max(0, min(fixed_changed) - window_size)
    f_max = min(len(fixed_lines), max(fixed_changed) + window_size + 1)

    return "\n".join(buggy_lines[b_min:b_max]), "\n".join(fixed_lines[f_min:f_max])


# Load and validate dataset
def load_pairs_csv(path):
    print(f"Loading dataset from: {path}")
    df = pd.read_csv(path)

    # Ensure required columns exist
    if "buggy_code" not in df.columns or "fixed_code" not in df.columns:
        raise ValueError("CSV must contain 'buggy_code' and 'fixed_code' columns")

    # Generate IDs if missing
    if "id" not in df.columns:
        if "Unnamed: 0" in df.columns:
            df["id"] = df["Unnamed: 0"]
            print("Using 'Unnamed: 0' as id column")
        else:
            print("ID column missing. Generating sequential IDs.")
            df["id"] = range(len(df))

    # Remove rows with missing values
    df = df.dropna(subset=["buggy_code", "fixed_code"]).copy()

    # Ensure ID is numeric
    try:
        df["id"] = df["id"].astype(int)
    except:
        df["id"] = df["id"].apply(lambda x: hash(str(x)) % 10000000)

    return df


# Leakage-safe 80/10/10 split
def split_ids(df, seed=42):
    # Extract unique pair IDs
    unique_ids = df["id"].unique().tolist()

    # Shuffle IDs for randomness
    rng = np.random.default_rng(seed)
    rng.shuffle(unique_ids)

    # Compute split boundaries
    n = len(unique_ids)
    train_end = int(0.8 * n)
    val_end = int(0.9 * n)

    # Split IDs
    train_ids = set(unique_ids[:train_end])
    val_ids = set(unique_ids[train_end:val_end])
    test_ids = set(unique_ids[val_end:])

    # Filter original dataframe by ID sets
    train_df = df[df["id"].isin(train_ids)].reset_index(drop=True)
    val_df = df[df["id"].isin(val_ids)].reset_index(drop=True)
    test_df = df[df["id"].isin(test_ids)].reset_index(drop=True)

    return train_df, val_df, test_df


# Convert pairs into classification samples
def pairs_to_samples(df, window_size=5):
    # Convert each pair into two samples:
    # buggy window -> label 1
    # fixed window -> label 0
    samples = []

    for _, row in df.iterrows():
        row_id = int(row["id"])
        buggy_window, fixed_window = extract_diff_window(
            row["buggy_code"], row["fixed_code"], window_size
        )

        if len(buggy_window.strip()) > 5:
            samples.append({"text": buggy_window, "label": 1, "id": row_id})
        if len(fixed_window.strip()) > 5:
            samples.append({"text": fixed_window, "label": 0, "id": row_id})

    df_out = pd.DataFrame(samples)

    # Shuffle samples for better stochastic training
    if not df_out.empty:
        df_out = df_out.sample(frac=1, random_state=SEED).reset_index(drop=True)

    return df_out


# Custom PyTorch Dataset
class CodeDataset(Dataset):
    # Wraps text, label, and id into tokenized tensors
    def __init__(self, texts, labels, ids, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.ids = ids
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        # Tokenize input text
        enc = self.tokenizer(
            str(self.texts[idx]),
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )

        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(int(self.labels[idx]), dtype=torch.long),
            "id": torch.tensor(int(self.ids[idx]), dtype=torch.long),
        }


# Training loop
def train_epoch(model, loader, optimizer, scheduler, device, scaler):
    model.train()
    loss_fn = torch.nn.CrossEntropyLoss()

    total_loss = 0
    correct = 0
    total = 0

    for batch in tqdm(loader, desc="Training", leave=False):
        input_ids = batch["input_ids"].to(device)
        mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        optimizer.zero_grad(set_to_none=True)

        # Mixed precision if CUDA
        if device.type == "cuda":
            with autocast("cuda"):
                outputs = model(input_ids=input_ids, attention_mask=mask)
                loss = loss_fn(outputs.logits, labels)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(input_ids=input_ids, attention_mask=mask)
            loss = loss_fn(outputs.logits, labels)
            loss.backward()
            optimizer.step()

        scheduler.step()

        total_loss += loss.item()
        preds = torch.argmax(outputs.logits, dim=1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    return total_loss / len(loader), correct / total


# Validation with AP + AUROC
def evaluate(model, loader, device):
    model.eval()

    all_labels = []
    all_probs = []
    all_preds = []

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=mask)
            probs = torch.softmax(outputs.logits, dim=1)[:, 1]
            preds = torch.argmax(outputs.logits, dim=1)

            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())

    acc = accuracy_score(all_labels, all_preds)

    if len(set(all_labels)) == 2:
        ap = average_precision_score(all_labels, all_probs)
        auroc = roc_auc_score(all_labels, all_probs)
    else:
        ap = None
        auroc = None

    return acc, ap, auroc


# Main training procedure
def main():
    set_seed(SEED)
    device = get_device()
    print("Using device:", device)

    if not os.path.exists(DATA_PATH):
        print("Dataset not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)

    # Load full dataset
    df_pairs = load_pairs_csv(DATA_PATH)
    print("Total pairs:", len(df_pairs))

    # Split dataset without leakage
    train_pairs, val_pairs, test_pairs = split_ids(df_pairs, seed=SEED)

    # Convert pairs to classification samples
    train_df = pairs_to_samples(train_pairs, window_size=WINDOW_SIZE)
    val_df = pairs_to_samples(val_pairs, window_size=WINDOW_SIZE)
    test_df = pairs_to_samples(test_pairs, window_size=WINDOW_SIZE)

    print("Train samples:", len(train_df))
    print("Validation samples:", len(val_df))
    print("Test samples:", len(test_df))

    # Save locked test set for final evaluation
    test_csv = "../../flask/data/raw/python/augmented_test_set.csv"
    if not os.path.exists(os.path.dirname(test_csv)):
        test_csv = "flask/data/raw/python/augmented_test_set.csv"
    test_df.to_csv(test_csv, index=False)

    # Load tokenizer and model
    tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
    model = RobertaForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    model.to(device)

    # Create DataLoaders
    train_loader = DataLoader(
        CodeDataset(train_df["text"], train_df["label"], train_df["id"], tokenizer, MAX_LEN),
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=4 if device.type == "cuda" else 0,
        pin_memory=(device.type == "cuda")
    )

    val_loader = DataLoader(
        CodeDataset(val_df["text"], val_df["label"], val_df["id"], tokenizer, MAX_LEN),
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4 if device.type == "cuda" else 0,
        pin_memory=(device.type == "cuda")
    )

    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)

    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(0.1 * total_steps),
        num_training_steps=total_steps
    )

    scaler = GradScaler() if device.type == "cuda" else None

    best_ap = -1

    # Training loop
    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch+1}/{EPOCHS}")

        train_loss, train_acc = train_epoch(model, train_loader, optimizer, scheduler, device, scaler)
        print("Train Loss:", round(train_loss, 4), "| Train Acc:", round(train_acc, 4))

        val_acc, val_ap, val_auroc = evaluate(model, val_loader, device)

        if val_ap is not None:
            print("Val Acc:", round(val_acc, 4),
                  "| AP:", round(val_ap, 4),
                  "| AUROC:", round(val_auroc, 4))
        else:
            print("Val Acc:", round(val_acc, 4))

        # Save best model based on AP
        if val_ap is not None and val_ap > best_ap:
            best_ap = val_ap
            model.save_pretrained(os.path.join(OUTPUT_DIR, "best_ap"))
            tokenizer.save_pretrained(os.path.join(OUTPUT_DIR, "best_ap"))
            print("Saved BEST_AP model")

    # Always save final model
    model.save_pretrained(os.path.join(OUTPUT_DIR, "checkpoint-last"))
    tokenizer.save_pretrained(os.path.join(OUTPUT_DIR, "checkpoint-last"))
    print("Saved final checkpoint")


if __name__ == "__main__":
    main()
