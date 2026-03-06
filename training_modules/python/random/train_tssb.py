import os
import math
import json
import random
import hashlib
from typing import Dict, Union, Set, List, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

from transformers import (
    RobertaTokenizer,
    RobertaForSequenceClassification,
    DataCollatorWithPadding,
    get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from tqdm import tqdm
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    roc_auc_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

# Speed knobs (safe)
try:
    torch.set_float32_matmul_precision("high")
except Exception:
    pass

if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True

# AMP support (bf16 on CUDA)
try:
    from torch.amp import autocast, GradScaler
except ImportError:
    from torch.cuda.amp import autocast, GradScaler

# Configuration
BATCH_SIZE = 128               # 1024 is only realistic on huge GPUs; start safer
EPOCHS = 5
LEARNING_RATE = 1e-5
MAX_LEN = 256

MODEL_NAME = "microsoft/codebert-base"
OUTPUT_DIR = "trained_model_tssb_pair"
SEED = 42

# Dataset path
DATA_PATH = "../../flask/data/raw/python/tssb_3m_cleaned.csv"
ALT_DATA_PATH = "flask/data/raw/python/tssb_3m_cleaned.csv"

# Split sizes
TRAIN_FRAC = 0.80
VAL_FRAC = 0.10
TEST_FRAC = 0.10

# Pairwise negatives (CodeBERT GitHub style = swapped mismatch)
NEGATIVES_PER_POSITIVE = 1

# To reduce CTSSB noise (tiny snippets like "return")
MIN_CHARS = 30

# Leakage prevention:
# CTSSB has repeated buggy snippets, so splitting by buggy hash is stronger than "id".
GROUP_BY_BUGGY = True

# Training stability
WEIGHT_DECAY = 0.01
WARMUP_RATIO = 0.10
MAX_GRAD_NORM = 1.0
GRAD_ACCUM = 1

# DataLoader
NUM_WORKERS = 4
PIN_MEMORY = True

# Save locked test file
LOCKED_TEST_NAME = "tssb_pair_test_locked.csv"
SPLIT_INFO_NAME = "tssb_pair_split_info.json"


# Helpers
def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def normalize_code(s: str) -> str:
    # Light normalization only (don’t reformat code)
    s = str(s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = "\n".join(line.strip() for line in s.split("\n"))
    s = " ".join(s.split())
    return s


def sha1_u64(s: str) -> int:
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()
    return int(h[:16], 16)


def load_pairs_csv(path: str) -> pd.DataFrame:
    print(f"Loading dataset from: {path}")
    df = pd.read_csv(path, usecols=lambda c: c in {"id", "buggy_code", "fixed_code"})

    if "buggy_code" not in df.columns or "fixed_code" not in df.columns:
        raise ValueError("CSV must contain 'buggy_code' and 'fixed_code' columns")

    if "id" not in df.columns:
        df["id"] = np.arange(len(df), dtype=np.int64)

    df = df.dropna(subset=["buggy_code", "fixed_code"]).copy()
    df["buggy_code"] = df["buggy_code"].astype(str)
    df["fixed_code"] = df["fixed_code"].astype(str)

    # Filter tiny snippets
    if MIN_CHARS and MIN_CHARS > 0:
        before = len(df)
        df = df[(df["buggy_code"].str.len() >= MIN_CHARS) & (df["fixed_code"].str.len() >= MIN_CHARS)].copy()
        df.reset_index(drop=True, inplace=True)
        print(f"Filtered short snippets (<{MIN_CHARS} chars): {before:,} -> {len(df):,}")

    # Remove buggy==fixed
    before2 = len(df)
    df = df[df["buggy_code"] != df["fixed_code"]].copy()
    df.reset_index(drop=True, inplace=True)
    removed = before2 - len(df)
    if removed:
        print(f"Removed buggy==fixed rows: {removed:,}")

    return df


def grouped_split_by_hash(df: pd.DataFrame, seed: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Strong leakage prevention:
    #   - Group by buggy hash (or buggy+fixed if you set it)
    #   - Split by groups (so repeated buggy snippets don't leak across splits)
    buggy = df["buggy_code"].to_numpy()
    fixed = df["fixed_code"].to_numpy()

    group_keys = np.empty(len(df), dtype=np.uint64)

    if GROUP_BY_BUGGY:
        for i in tqdm(range(len(df)), desc="Hashing buggy group keys"):
            group_keys[i] = sha1_u64(normalize_code(buggy[i]))
    else:
        for i in tqdm(range(len(df)), desc="Hashing pair group keys"):
            b = normalize_code(buggy[i])
            f = normalize_code(fixed[i])
            group_keys[i] = sha1_u64(b + "\n<SEP>\n" + f)

    unique_groups = np.unique(group_keys)

    # Stable pseudo-random ordering per group
    scored = []
    for g in unique_groups:
        score = sha1_u64(f"{int(g)}_{seed}") / float(2**64 - 1)
        scored.append((int(g), score))
    scored.sort(key=lambda x: x[1])

    n = len(scored)
    n_train = int(n * TRAIN_FRAC)
    n_val = int(n * VAL_FRAC)

    train_groups = set(g for g, _ in scored[:n_train])
    val_groups = set(g for g, _ in scored[n_train:n_train + n_val])
    test_groups = set(g for g, _ in scored[n_train + n_val:])

    idx = np.arange(len(df))
    train_idx = idx[np.isin(group_keys, list(train_groups))]
    val_idx = idx[np.isin(group_keys, list(val_groups))]
    test_idx = idx[np.isin(group_keys, list(test_groups))]

    return train_idx, val_idx, test_idx


def build_buggy_to_valid_fixed_map(buggy_list: List[str], fixed_list: List[str]) -> Dict[int, Union[int, Set[int]]]:
    
    #Used for "safe negatives" so we don't accidentally sample a true fix as negative.
    
    mapping: Dict[int, Union[int, Set[int]]] = {}
    for b, f in tqdm(zip(buggy_list, fixed_list), total=len(buggy_list), desc="Indexing valid fixes (train only)"):
        bh = sha1_u64(normalize_code(b))
        fh = sha1_u64(normalize_code(f))
        cur = mapping.get(bh)
        if cur is None:
            mapping[bh] = fh
        elif isinstance(cur, int):
            if cur != fh:
                mapping[bh] = {cur, fh}
        else:
            cur.add(fh)
    return mapping


# Dataset (CodeBERT from Paper )
class PairMatchDataset(Dataset):

    # CodeBERT GitHub style: Train a classifier on PAIRS.
    #   - Positive: (buggy[i], fixed[i]) label=1
    #   - Negative: (buggy[i], fixed[j]) label=0   (swap second sequence)
    def __init__(
        self,
        buggy_list: List[str],
        fixed_list: List[str],
        tokenizer: RobertaTokenizer,
        max_len: int,
        seed: int,
        negatives_per_positive: int,
        deterministic: bool,
        buggy_to_valid_fixed: Dict[int, Union[int, Set[int]]],):

        assert len(buggy_list) == len(fixed_list)
        self.buggy = buggy_list
        self.fixed = fixed_list
        self.tokenizer = tokenizer
        self.max_len = max_len

        self.nneg = int(negatives_per_positive)
        self.seed = int(seed)
        self.deterministic = bool(deterministic)

        self.num_pos = len(self.buggy)
        self.num_samples = self.num_pos * (1 + self.nneg)

        # Hash caches (speed)
        self.buggy_hash = np.array([sha1_u64(normalize_code(x)) for x in self.buggy], dtype=np.uint64)
        self.fixed_hash = np.array([sha1_u64(normalize_code(x)) for x in self.fixed], dtype=np.uint64)

        # Train-known valid fixes for safe negative sampling
        self.buggy_to_valid_fixed = buggy_to_valid_fixed or {}

    def __len__(self):
        return self.num_samples

    def _rng(self, idx: int):
        # Deterministic negatives for val/test stability
        return np.random.RandomState(self.seed + idx)

    def _is_valid_fix(self, buggy_h: int, fixed_h: int) -> bool:
        cur = self.buggy_to_valid_fixed.get(int(buggy_h))
        if cur is None:
            return False
        if isinstance(cur, int):
            return int(cur) == int(fixed_h)
        return int(fixed_h) in cur

    def _sample_negative_j(self, i: int, rng) -> int:
        buggy_h = self.buggy_hash[i]
        my_fixed_h = self.fixed_hash[i]

        # Try a few random swaps
        for _ in range(50):
            j = int(rng.randint(0, self.num_pos))
            if j == i:
                continue
            if int(self.fixed_hash[j]) == int(my_fixed_h):
                continue
            if self._is_valid_fix(buggy_h, self.fixed_hash[j]):
                continue
            return j

        # Fallback
        return (i + 1) % self.num_pos

    def __getitem__(self, idx: int):
        i = idx // (1 + self.nneg)
        offset = idx % (1 + self.nneg)

        if offset == 0:
            b = self.buggy[i]
            f = self.fixed[i]
            label = 1
        else:
            rng = self._rng(idx) if self.deterministic else np.random
            j = self._sample_negative_j(i, rng)
            b = self.buggy[i]
            f = self.fixed[j]
            label = 0

        # pair encoding (this is the GitHub style part of CodeBERT)
        enc = self.tokenizer(
            b,
            f,
            truncation=True,
            max_length=self.max_len,
        )
        enc["labels"] = int(label)
        return enc


# Train / Eval
def train_epoch(model, loader, optimizer, scheduler, device, scaler):
    model.train()
    total_loss = 0.0
    all_labels, all_preds = [], []

    use_cuda = (device.type == "cuda")

    for step, batch in enumerate(tqdm(loader, desc="Training", leave=False), start=1):
        batch = {k: v.to(device, non_blocking=True) for k, v in batch.items()}

        optimizer.zero_grad(set_to_none=True)

        if use_cuda:
            with autocast(device_type="cuda", dtype=torch.bfloat16):
                out = model(**batch)
                loss = out.loss
        else:
            out = model(**batch)
            loss = out.loss

        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), MAX_GRAD_NORM)

        optimizer.step()
        scheduler.step()

        total_loss += float(loss.detach().cpu())

        preds = torch.argmax(out.logits, dim=1).detach().cpu().numpy()
        labels = batch["labels"].detach().cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels)

    acc = accuracy_score(all_labels, all_preds)
    return total_loss / max(1, len(loader)), acc


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    all_labels, all_probs, all_preds = [], [], []
    use_cuda = (device.type == "cuda")

    for batch in tqdm(loader, desc="Evaluating", leave=False):
        batch = {k: v.to(device, non_blocking=True) for k, v in batch.items()}
        labels = batch["labels"]

        if use_cuda:
            with autocast(device_type="cuda", dtype=torch.bfloat16):
                out = model(**batch)
        else:
            out = model(**batch)

        probs = torch.softmax(out.logits, dim=1)[:, 1]
        preds = torch.argmax(out.logits, dim=1)

        all_labels.extend(labels.detach().cpu().numpy())
        all_probs.extend(probs.detach().cpu().float().numpy())
        all_preds.extend(preds.detach().cpu().numpy())

    acc = accuracy_score(all_labels, all_preds)

    ap, auroc = None, None
    if len(set(all_labels)) == 2:
        ap = average_precision_score(all_labels, all_probs)
        auroc = roc_auc_score(all_labels, all_probs)

    p, r, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average="binary", zero_division=0)
    cm = confusion_matrix(all_labels, all_preds)

    return {
        "acc": acc,
        "ap": ap,
        "auroc": auroc,
        "precision": p,
        "recall": r,
        "f1": f1,
        "cm": cm,
    }


def save_model(model, tokenizer, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    m = model._orig_mod if hasattr(model, "_orig_mod") else model
    m.save_pretrained(out_dir)
    tokenizer.save_pretrained(out_dir)


# Main
def main():
    set_seed(SEED)
    device = get_device()
    print(f"Using device: {device}")

    # Resolve data path
    path = DATA_PATH if os.path.exists(DATA_PATH) else ALT_DATA_PATH
    if not os.path.exists(path):
        print(f"Dataset not found: {DATA_PATH} or {ALT_DATA_PATH}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_pairs_csv(path)
    print(f"Total pairs after filtering: {len(df):,}")

    # Split by grouped hashing
    train_idx, val_idx, test_idx = grouped_split_by_hash(df, seed=SEED)
    print(f"Train pairs: {len(train_idx):,}")
    print(f"Val pairs:   {len(val_idx):,}")
    print(f"Test pairs:  {len(test_idx):,}")

    # Save split info + locked test set
    split_info = {
        "seed": SEED,
        "min_chars": MIN_CHARS,
        "group_by_buggy": GROUP_BY_BUGGY,
        "negatives_per_positive": NEGATIVES_PER_POSITIVE,
        "train_pairs": int(len(train_idx)),
        "val_pairs": int(len(val_idx)),
        "test_pairs": int(len(test_idx)),
        "note": "Pairwise (buggy,fixed) match classification; negatives via swapped fixed (CodeBERT GitHub style).",
    }
    with open(os.path.join(OUTPUT_DIR, SPLIT_INFO_NAME), "w") as f:
        json.dump(split_info, f, indent=2)

    locked_test_path = os.path.join(OUTPUT_DIR, LOCKED_TEST_NAME)
    df.loc[test_idx, ["id", "buggy_code", "fixed_code"]].to_csv(locked_test_path, index=False)
    print(f"Saved locked test set: {locked_test_path}")

    # Build safe-negative map using TRAIN ONLY
    train_buggy = df.loc[train_idx, "buggy_code"].tolist()
    train_fixed = df.loc[train_idx, "fixed_code"].tolist()
    buggy_to_valid_fixed = build_buggy_to_valid_fixed_map(train_buggy, train_fixed)

    # Tokenizer + model
    tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
    model = RobertaForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2).to(device)

    # Optional torch.compile
    if hasattr(torch, "compile") and device.type == "cuda":
        try:
            print("Compiling model with torch.compile...")
            model = torch.compile(model)
        except Exception:
            print("torch.compile failed, continuing without it")

    # Build val/test lists
    val_buggy = df.loc[val_idx, "buggy_code"].tolist()
    val_fixed = df.loc[val_idx, "fixed_code"].tolist()
    test_buggy = df.loc[test_idx, "buggy_code"].tolist()
    test_fixed = df.loc[test_idx, "fixed_code"].tolist()

    # Datasets (val/test use deterministic negatives for stable metrics)
    train_ds = PairMatchDataset(
        train_buggy, train_fixed, tokenizer, MAX_LEN, SEED,
        negatives_per_positive=NEGATIVES_PER_POSITIVE,
        deterministic=False,
        buggy_to_valid_fixed=buggy_to_valid_fixed,
    )
    val_ds = PairMatchDataset(
        val_buggy, val_fixed, tokenizer, MAX_LEN, SEED,
        negatives_per_positive=NEGATIVES_PER_POSITIVE,
        deterministic=True,
        buggy_to_valid_fixed=buggy_to_valid_fixed,
    )
    test_ds = PairMatchDataset(
        test_buggy, test_fixed, tokenizer, MAX_LEN, SEED,
        negatives_per_positive=NEGATIVES_PER_POSITIVE,
        deterministic=True,
        buggy_to_valid_fixed=buggy_to_valid_fixed,
    )

    # Dynamic padding (faster than padding="max_length")
    collator = DataCollatorWithPadding(tokenizer=tokenizer, padding="longest", return_tensors="pt")
    workers = min(NUM_WORKERS, os.cpu_count() or 2)

    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE, shuffle=True,
        num_workers=workers, pin_memory=PIN_MEMORY and device.type == "cuda",
        persistent_workers=(workers > 0), collate_fn=collator
    )
    val_loader = DataLoader(
        val_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=workers, pin_memory=PIN_MEMORY and device.type == "cuda",
        persistent_workers=(workers > 0), collate_fn=collator
    )
    test_loader = DataLoader(
        test_ds, batch_size=BATCH_SIZE, shuffle=False,
        num_workers=workers, pin_memory=PIN_MEMORY and device.type == "cuda",
        persistent_workers=(workers > 0), collate_fn=collator
    )

    # Optimizer (fused when possible)
    use_fused = (device.type == "cuda")
    try:
        optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY, fused=use_fused)
    except TypeError:
        optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

    total_steps = len(train_loader) * EPOCHS
    warmup_steps = int(WARMUP_RATIO * total_steps)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    scaler = GradScaler(enabled=False)  # bf16 autocast doesn't need scaling

    best_ap = -1.0
    best_acc = -1.0

    for epoch in range(EPOCHS):
        print(f"\n--- Epoch {epoch+1}/{EPOCHS} ---")

        tr_loss, tr_acc = train_epoch(model, train_loader, optimizer, scheduler, device, scaler)
        print(f"Train loss: {tr_loss:.4f} | Train acc: {tr_acc:.4f}")

        val = evaluate(model, val_loader, device)
        print(
            f"Val acc: {val['acc']:.4f} | F1: {val['f1']:.4f} | "
            f"AP: {val['ap'] if val['ap'] is not None else 'NA'} | "
            f"AUROC: {val['auroc'] if val['auroc'] is not None else 'NA'}"
        )
        print(f"Val CM:\n{val['cm']}")

        # Always save last
        save_model(model, tokenizer, os.path.join(OUTPUT_DIR, "checkpoint-last"))

        # Best model selection (prefer AP, else acc)
        improved = False
        if val["ap"] is not None:
            if val["ap"] > best_ap + 1e-6:
                best_ap = val["ap"]
                save_model(model, tokenizer, os.path.join(OUTPUT_DIR, "best_ap"))
                print(f"Saved best_ap (AP={best_ap:.4f})")
                improved = True
        else:
            if val["acc"] > best_acc + 1e-6:
                best_acc = val["acc"]
                save_model(model, tokenizer, os.path.join(OUTPUT_DIR, "best_acc"))
                print(f"Saved best_acc (ACC={best_acc:.4f})")
                improved = True

    # Final TEST evaluation (locked split)
    print("\n=== Final evaluation on LOCKED TEST ===")
    test = evaluate(model, test_loader, device)
    print(
        f"Test acc: {test['acc']:.4f} | F1: {test['f1']:.4f} | "
        f"AP: {test['ap'] if test['ap'] is not None else 'NA'} | "
        f"AUROC: {test['auroc'] if test['auroc'] is not None else 'NA'}"
    )
    print(f"Test CM:\n{test['cm']}")

    print(f"\nDone. Model dir: {OUTPUT_DIR}")
    print(f"Locked test CSV: {locked_test_path}")


if __name__ == "__main__":
    main()
