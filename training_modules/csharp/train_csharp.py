import os
import random
import difflib
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import RobertaTokenizer, RobertaForSequenceClassification, get_linear_schedule_with_warmup
from torch.optim import AdamW
from tqdm import tqdm

from sklearn.metrics import accuracy_score, average_precision_score, roc_auc_score

# AMP compatibility
try:
    from torch.amp import autocast
    try:
        from torch.amp import GradScaler
    except ImportError:
        from torch.cuda.amp import GradScaler
except ImportError:
    from torch.cuda.amp import autocast, GradScaler


# Configuration
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 2e-5
MAX_LEN = 256         #can change to 512
WINDOW_SIZE = 5
MODEL_NAME = "microsoft/codebert-base"
OUTPUT_DIR = "trained_model_csharp"


DATA_PATH = "data/csharp_combined_dataset.csv"
if not os.path.exists(DATA_PATH):
    # Fallback to project structure
    DATA_PATH = "../../flask/data/raw/csharp/csharp_combined_dataset.csv"
    if not os.path.exists(DATA_PATH):
        DATA_PATH = "flask/data/raw/csharp/csharp_combined_dataset.csv"

SEED = 42


# Utils
def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


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


def load_pairs_csv(path: str) -> pd.DataFrame:
    print(f"Loading {path} ...")
    df_raw = pd.read_csv(path)

    required = {"id", "buggy_code", "fixed_code"}
    missing = required - set(df_raw.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}. Found: {list(df_raw.columns)}")

    df_raw = df_raw.dropna(subset=["id", "buggy_code", "fixed_code"]).copy()
    df_raw["id"] = df_raw["id"].astype(int)
    return df_raw


def split_ids(df_pairs: pd.DataFrame, seed=42):
    
    # Leakage-safe splitting: split by unique pair 'id'

    unique_ids = df_pairs["id"].unique().tolist()
    rng = np.random.default_rng(seed)
    rng.shuffle(unique_ids)

    n_ids = len(unique_ids)
    train_end = int(0.8 * n_ids)
    val_end = int(0.9 * n_ids)

    train_ids = set(unique_ids[:train_end])
    val_ids = set(unique_ids[train_end:val_end])
    test_ids = set(unique_ids[val_end:])

    train_pairs = df_pairs[df_pairs["id"].isin(train_ids)].reset_index(drop=True)
    val_pairs = df_pairs[df_pairs["id"].isin(val_ids)].reset_index(drop=True)
    test_pairs = df_pairs[df_pairs["id"].isin(test_ids)].reset_index(drop=True)

    return train_pairs, val_pairs, test_pairs


def perform_eda(df: pd.DataFrame, output_dir: str, title_suffix="CSharp"):
    # Generates EDA plots.
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        print("Skipping EDA plots: matplotlib/seaborn not installed.")
        return

    print(f"Generating EDA graphs for {title_suffix}...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Class Distribution
    plt.figure(figsize=(6, 4))
    sns.countplot(x='label', data=df)
    plt.title(f'Class Distribution ({title_suffix})')
    plt.xlabel('Label (0=Fixed, 1=Buggy)')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'class_dist_{title_suffix.lower()}.png'))
    plt.close()

    # 2. Length Distribution
    # Calculate lengths
    df = df.copy() # Safe copy
    df['length'] = df['text'].apply(lambda x: len(str(x).split()))
    
    # Dynamic Limit (95th percentile) to avoid long tail skewing
    if not df.empty:
        limit_95 = int(np.percentile(df['length'], 95))
        x_limit = max(limit_95, 100) # At least 100
    else:
        x_limit = 512

    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='length', hue='label', kde=True, bins=50)
    plt.title(f'Code Length Distribution ({title_suffix})')
    plt.xlabel('Number of Tokens (Approx)')
    plt.ylabel('Frequency')
    plt.xlim(0, x_limit)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'length_dist_{title_suffix.lower()}.png'))
    plt.close()
    
    print(f"EDA plots saved to {output_dir}")



def pairs_to_samples(df_pairs: pd.DataFrame, window_size=5) -> pd.DataFrame:
    # Expands each pair into two samples:
    #   buggy window -> label=1
    #   fixed window -> label=0
    samples = []
    pbar = tqdm(df_pairs.iterrows(), total=len(df_pairs), desc="Windowing", leave=False)

    for _, row in pbar:
        row_id = int(row["id"])
        b_w, f_w = extract_diff_window(row["buggy_code"], row["fixed_code"], window_size)

        if len(b_w.strip()) > 5:
            samples.append({"text": b_w, "label": 1, "id": row_id})
        if len(f_w.strip()) > 5:
            samples.append({"text": f_w, "label": 0, "id": row_id})

    df = pd.DataFrame(samples)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle within split
    return df

# Dataset
class CodeDataset(Dataset):
    def __init__(self, texts, labels, ids, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.ids = ids
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer.encode_plus(
            str(self.texts[idx]),
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(int(self.labels[idx]), dtype=torch.long),
            "id": torch.tensor(int(self.ids[idx]), dtype=torch.long),
        }


# Train / Eval
def train_epoch(model, loader, opt, sched, dev, scaler):
    model.train()
    ce = torch.nn.CrossEntropyLoss()

    losses = []
    correct = 0
    total = 0

    pbar = tqdm(loader, desc="Train", leave=False)
    for b in pbar:
        ii = b["input_ids"].to(dev)
        mask = b["attention_mask"].to(dev)
        lbl = b["labels"].to(dev)

        opt.zero_grad(set_to_none=True)

        if dev.type == "cuda":
            with autocast("cuda"):
                out = model(input_ids=ii, attention_mask=mask)
                loss = ce(out.logits, lbl)
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            # MPS AMP can be flaky; keep it simple and stable
            out = model(input_ids=ii, attention_mask=mask)
            loss = ce(out.logits, lbl)
            loss.backward()
            opt.step()

        sched.step()

        losses.append(loss.item())
        preds = torch.argmax(out.logits, dim=1)
        correct += (preds == lbl).sum().item()
        total += lbl.size(0)

        pbar.set_postfix({"loss": f"{loss.item():.4f}", "acc": f"{correct/total:.3f}"})

    return float(np.mean(losses)), float(correct / total)


def evaluate_ap_auroc(model, loader, dev):
    model.eval()
    all_labels = []
    all_probs = []
    all_preds = []

    with torch.no_grad():
        for b in loader:
            ii = b["input_ids"].to(dev)
            mask = b["attention_mask"].to(dev)
            lbl = b["labels"].to(dev)

            out = model(input_ids=ii, attention_mask=mask)
            probs_buggy = torch.softmax(out.logits, dim=1)[:, 1]  # P(label=1 buggy)
            preds = torch.argmax(out.logits, dim=1)

            all_labels.extend(lbl.detach().cpu().numpy().tolist())
            all_probs.extend(probs_buggy.detach().cpu().numpy().tolist())
            all_preds.extend(preds.detach().cpu().numpy().tolist())

    acc = accuracy_score(all_labels, all_preds)

    ap = None
    auroc = None
    if len(set(all_labels)) == 2:
        ap = average_precision_score(all_labels, all_probs)
        auroc = roc_auc_score(all_labels, all_probs)

    return acc, ap, auroc


# Main
def main():
    set_seed(SEED)
    device = get_device()
    print(f"Using device: {device}")

    if not os.path.exists(DATA_PATH):
        print(f"File not found: {DATA_PATH}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)  # FIX: ensure folder exists

    # 1) Load pairs
    df_pairs = load_pairs_csv(DATA_PATH)
    print(f"Loaded pairs: {len(df_pairs)}")

    # 2) Leakage-safe split by id
    train_pairs, val_pairs, test_pairs = split_ids(df_pairs, seed=SEED)
    print(f"Pair split (by id): Train={len(train_pairs)}, Val={len(val_pairs)}, Test={len(test_pairs)}")

    # 3) Expand each split into samples (buggy/fixed)
    print("Preparing TRAIN samples...")
    train_df = pairs_to_samples(train_pairs, window_size=WINDOW_SIZE)
    print("Preparing VAL samples...")
    val_df = pairs_to_samples(val_pairs, window_size=WINDOW_SIZE)
    print("Preparing TEST samples...")
    test_df = pairs_to_samples(test_pairs, window_size=WINDOW_SIZE)
    
    # Perform EDA on all splits
    perform_eda(train_df, "results", title_suffix="CSharp_Train")
    if not val_df.empty:
        perform_eda(val_df, "results", title_suffix="CSharp_Val")
    if not test_df.empty:
        perform_eda(test_df, "results", title_suffix="CSharp_Test")

    # Logging counts
    def class_counts(df):
        return df["label"].value_counts().to_dict()

    print(f"Samples: Train={len(train_df)} {class_counts(train_df)}")
    print(f"Samples: Val={len(val_df)} {class_counts(val_df)}")
    print(f"Samples: Test={len(test_df)} {class_counts(test_df)}")

    # 4) Save test set for later evaluation
    test_csv = os.path.join("data", "csharp_test_set.csv")
    test_df.to_csv(test_csv, index=False)
    print(f"Saved Test Set to {test_csv}")

    # 5) Model + tokenizer
    tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
    model = RobertaForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2).to(device)

    # 6) Datasets + loaders
    tr_ds = CodeDataset(
        train_df["text"].to_numpy(),
        train_df["label"].to_numpy(),
        train_df["id"].to_numpy(),
        tokenizer,
        MAX_LEN,
    )
    val_ds = CodeDataset(
        val_df["text"].to_numpy(),
        val_df["label"].to_numpy(),
        val_df["id"].to_numpy(),
        tokenizer,
        MAX_LEN,
    )

    # FIX: device-aware dataloader settings
    if device.type == "cuda":
        num_workers = 4
        pin_memory = True
    else:
        num_workers = 0
        pin_memory = False

    tr_load = DataLoader(tr_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=num_workers, pin_memory=pin_memory)
    val_load = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)

    # 7) Optimizer + scheduler
    opt = AdamW(model.parameters(), lr=LEARNING_RATE)
    steps = len(tr_load) * EPOCHS
    sched = get_linear_schedule_with_warmup(opt, num_warmup_steps=int(0.1 * steps), num_training_steps=steps)

    scaler = GradScaler() if device.type == "cuda" else None

    # 8) Train loop with AP/AUROC
    best_ap = -1.0
    best_dir = os.path.join(OUTPUT_DIR, "best_ap")
    last_dir = os.path.join(OUTPUT_DIR, "checkpoint-last")

    for ep in range(EPOCHS):
        print(f"\nEpoch {ep+1}/{EPOCHS}")

        tl, ta = train_epoch(model, tr_load, opt, sched, device, scaler)
        print(f"Train Loss: {tl:.4f} | Train Acc: {ta:.4f}")

        val_acc, val_ap, val_auroc = evaluate_ap_auroc(model, val_load, device)

        if val_ap is None:
            print(f"Val Acc: {val_acc:.4f} | AP: N/A | AUROC: N/A (val has only one class)")
        else:
            print(f"Val Acc: {val_acc:.4f} | AP: {val_ap:.4f} | AUROC: {val_auroc:.4f}")

            # FIX: save best by AP (better than accuracy for bug detection)
            if val_ap > best_ap:
                best_ap = val_ap
                os.makedirs(best_dir, exist_ok=True)
                model.save_pretrained(best_dir)
                tokenizer.save_pretrained(best_dir)
                print(f"Saved BEST_AP -> {best_dir} (AP={best_ap:.4f})")

    # save last
    os.makedirs(last_dir, exist_ok=True)
    model.save_pretrained(last_dir)
    tokenizer.save_pretrained(last_dir)
    print(f"\nSaved LAST checkpoint -> {last_dir}")


if __name__ == "__main__":
    main()
