import os
import json
import random
import hashlib
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    RobertaTokenizer,
    RobertaForSequenceClassification,
    DataCollatorWithPadding,
)
from tqdm import tqdm
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    precision_recall_curve,
)

# Config (must match training)
MODEL_DIR = "trained_model_ctssb_pair_github_style"
LOCKED_TEST_CSV = os.path.join(MODEL_DIR, "ctssb_pair_test_locked.csv")

# saved split json from training, we can read settings from it
SPLIT_INFO_JSON = os.path.join(MODEL_DIR, "ctssb_pair_split_info.json")

MAX_LEN = 256
BATCH_SIZE = 128
SEED = 42

# Make eval difficulty similar to training
NEGATIVES_PER_POSITIVE = 1
LENGTH_BUCKET_SIZE = 64
NEG_TRIES = 50

# If you still have access to the original full dataset, we can rebuild the train map:
FULL_DATA_CSV = "ctssb_1m_cleaned.csv"
ALT_FULL_DATA_CSV = "/mnt/data/ctssb_1m_cleaned.csv"

# Helpers
def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

def normalize_code(s: str) -> str:
    s = str(s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = "\n".join(line.strip() for line in s.split("\n"))
    s = " ".join(s.split())
    return s

def sha1_u64(s: str) -> int:
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()
    return int(h[:16], 16)

def pick_best_model(model_dir: str) -> str:
    best_ap = os.path.join(model_dir, "best_ap")
    if os.path.exists(best_ap):
        return best_ap
    best_acc = os.path.join(model_dir, "best_acc")
    if os.path.exists(best_acc):
        return best_acc
    last = os.path.join(model_dir, "checkpoint-last")
    if os.path.exists(last):
        return last
    return model_dir

def try_load_split_info():
    if os.path.exists(SPLIT_INFO_JSON):
        try:
            with open(SPLIT_INFO_JSON, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def build_buggy_to_valid_fixed_map_from_train(full_df: pd.DataFrame, train_mask: np.ndarray):
    mapping = {}

    buggy = full_df.loc[train_mask, "buggy_code"].astype(str).tolist()
    fixed = full_df.loc[train_mask, "fixed_code"].astype(str).tolist()

    for b, f in tqdm(zip(buggy, fixed), total=len(buggy), desc="Rebuilding safe-negative map (train only)"):
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

# Dataset (matches training style)
class PairEvalDataset(Dataset):
    # For each original test pair i, we emit:
    #   - Positive: (buggy[i], fixed[i]) -> 1
    #   - Negative(s): (buggy[i], fixed[j]) -> 0, where fixed[j] is swapped
    # Negatives are:
    #   - deterministic per item
    #   - bucketed by length (harder)
    #   - safe (won't pick a known valid fix for same buggy)
    def __init__(
        self,
        df_test: pd.DataFrame,
        tokenizer,
        max_len: int,
        seed: int,
        negatives_per_positive: int,
        length_bucket_size: int,
        safe_map: dict,
    ):
        self.df = df_test.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.seed = int(seed)
        self.nneg = int(negatives_per_positive)
        self.bucket_size = int(length_bucket_size)
        self.safe_map = safe_map or {}

        self.buggy = self.df["buggy_code"].astype(str).tolist()
        self.fixed = self.df["fixed_code"].astype(str).tolist()
        self.ids = self.df["id"].tolist()

        self.num_pos = len(self.buggy)
        self.num_samples = self.num_pos * (1 + self.nneg)

        # Length buckets over fixed (for harder negatives)
        self.fixed_lens = np.array([len(x) for x in self.fixed], dtype=np.int32)
        buckets = (self.fixed_lens // self.bucket_size).astype(np.int32)
        self.bucket_to_indices = {}
        for b in np.unique(buckets):
            self.bucket_to_indices[int(b)] = np.where(buckets == b)[0]

        # Hash caches
        self.buggy_hash = np.array([sha1_u64(normalize_code(x)) for x in self.buggy], dtype=np.uint64)
        self.fixed_hash = np.array([sha1_u64(normalize_code(x)) for x in self.fixed], dtype=np.uint64)

    def __len__(self):
        return self.num_samples

    def _rng(self, idx: int):
        return np.random.RandomState(self.seed + idx)

    def _is_valid_fix(self, buggy_h: int, fixed_h: int) -> bool:
        cur = self.safe_map.get(int(buggy_h))
        if cur is None:
            return False
        if isinstance(cur, int):
            return int(cur) == int(fixed_h)
        return int(fixed_h) in cur

    def _sample_negative_j(self, i: int, rng):
        buggy_h = self.buggy_hash[i]
        my_fixed_h = self.fixed_hash[i]

        target_bucket = int(self.fixed_lens[i] // self.bucket_size)
        candidates = self.bucket_to_indices.get(target_bucket)

        def ok(j: int):
            if j == i:
                return False
            if int(self.fixed_hash[j]) == int(my_fixed_h):
                return False
            if self._is_valid_fix(buggy_h, self.fixed_hash[j]):
                return False
            return True

        # Try same-length bucket first (harder)
        if candidates is not None and len(candidates) > 1:
            for _ in range(NEG_TRIES):
                j = int(candidates[rng.randint(0, len(candidates))])
                if ok(j):
                    return j

        # Fallback random
        for _ in range(NEG_TRIES):
            j = int(rng.randint(0, self.num_pos))
            if ok(j):
                return j

        return (i + 1) % self.num_pos

    def __getitem__(self, idx: int):
        i = idx // (1 + self.nneg)
        offset = idx % (1 + self.nneg)

        if offset == 0:
            a = self.buggy[i]
            b = self.fixed[i]
            label = 1
            pair_type = "pos"
        else:
            rng = self._rng(idx)
            j = self._sample_negative_j(i, rng)
            a = self.buggy[i]
            b = self.fixed[j]
            label = 0
            pair_type = "neg"

        enc = self.tokenizer(a, b, truncation=True, max_length=self.max_len)
        return {
            "input_ids": enc["input_ids"],
            "attention_mask": enc["attention_mask"],
            "labels": torch.tensor(label, dtype=torch.long),
            "id": self.ids[i],
            "pair_type": pair_type,
            "buggy_text": self.buggy[i],
            "fixed_text": b,
        }


# Main eval
def main():
    device = get_device()
    print(f"Using device: {device}")

    if not os.path.exists(LOCKED_TEST_CSV):
        print(f"Locked test set not found: {LOCKED_TEST_CSV}")
        return

    print(f"Loading locked test set: {LOCKED_TEST_CSV}")
    df_test = pd.read_csv(LOCKED_TEST_CSV)
    df_test["buggy_code"] = df_test["buggy_code"].astype(str)
    df_test["fixed_code"] = df_test["fixed_code"].astype(str)
    print(f"Loaded {len(df_test):,} test pairs.")

    # Load model
    model_path = pick_best_model(MODEL_DIR)
    print(f"Loading model from: {model_path}")
    tokenizer = RobertaTokenizer.from_pretrained(model_path)
    model = RobertaForSequenceClassification.from_pretrained(model_path).to(device)
    model.eval()

    # Build SAFE MAP (train-only) if possible:
    safe_map = {}
    split_info = try_load_split_info()

    # If we can reconstruct train split, we do it (best).
    # If not, evaluation still runs but negatives might be slightly noisier.
    full_path = FULL_DATA_CSV if os.path.exists(FULL_DATA_CSV) else ALT_FULL_DATA_CSV
    if os.path.exists(full_path) and split_info is not None and "group_by_buggy" in split_info:
        print("Rebuilding train-only safe-negative map (recommended)...")
        full_df = pd.read_csv(full_path, usecols=lambda c: c in {"buggy_code", "fixed_code"})
        full_df["buggy_code"] = full_df["buggy_code"].astype(str)
        full_df["fixed_code"] = full_df["fixed_code"].astype(str)

        # We can't perfectly rebuild the exact train split without stored indices.
        # So here we do a practical alternative:
        # build safe-map from ALL data EXCEPT the locked test buggy/fixed pairs.
        # This avoids pulling exact test pairs into the map.
        test_pairs_set = set(zip(df_test["buggy_code"], df_test["fixed_code"]))
        mask = np.array([(b, f) not in test_pairs_set for b, f in zip(full_df["buggy_code"], full_df["fixed_code"])])
        safe_map = build_buggy_to_valid_fixed_map_from_train(full_df, mask)
    else:
        print("Safe-map not rebuilt (missing full dataset or split info). Using empty safe-map.")

    # Dataset + loader
    ds = PairEvalDataset(
        df_test=df_test,
        tokenizer=tokenizer,
        max_len=MAX_LEN,
        seed=SEED,
        negatives_per_positive=NEGATIVES_PER_POSITIVE,
        length_bucket_size=LENGTH_BUCKET_SIZE,
        safe_map=safe_map,
    )

    collator = DataCollatorWithPadding(tokenizer=tokenizer, padding="longest", return_tensors="pt")
    loader = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collator, num_workers=4)

    # AMP
    use_cuda = (device.type == "cuda")
    try:
        from torch.amp import autocast
    except ImportError:
        from torch.cuda.amp import autocast

    all_labels, all_preds, all_probs = [], [], []
    rows = []

    with torch.no_grad():
        for batch in tqdm(loader, desc="Evaluating"):
            ids = batch.pop("id")
            pair_type = batch.pop("pair_type")
            buggy_text = batch.pop("buggy_text")
            fixed_text = batch.pop("fixed_text")

            labels = batch["labels"].detach().cpu().numpy()
            all_labels.extend(labels.tolist())

            batch = {k: v.to(device) for k, v in batch.items()}

            if use_cuda:
                with autocast(device_type="cuda", dtype=torch.bfloat16):
                    out = model(**batch)
            else:
                out = model(**batch)

            probs = torch.softmax(out.logits, dim=1)[:, 1].detach().cpu().numpy()
            preds = torch.argmax(out.logits, dim=1).detach().cpu().numpy()

            all_probs.extend(probs.tolist())
            all_preds.extend(preds.tolist())

            # store for failure cases
            for i in range(len(preds)):
                rows.append({
                    "id": ids[i],
                    "pair_type": pair_type[i],
                    "true_label": int(labels[i]),
                    "pred_label": int(preds[i]),
                    "prob_positive": float(probs[i]),
                    "buggy_code": buggy_text[i],
                    "candidate_fixed_code": fixed_text[i],
                })

    # Metrics
    acc = accuracy_score(all_labels, all_preds)
    ap = average_precision_score(all_labels, all_probs)
    try:
        roc = roc_auc_score(all_labels, all_probs)
    except Exception:
        roc = 0.0

    print("\n" + "=" * 50)
    print(f"RESULTS: {model_path}")
    print("=" * 50)
    print(f"Accuracy: {acc:.4f}")
    print(f"AP:       {ap:.4f}")
    print(f"ROC-AUC:  {roc:.4f}")
    print("-" * 50)
    print(classification_report(all_labels, all_preds, target_names=["Negative (Swapped)", "Positive (Correct)"]))
    print("-" * 50)
    print("Confusion Matrix:")
    print(confusion_matrix(all_labels, all_preds))

    # Save results
    results_dir = os.path.join(MODEL_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)

    df_rows = pd.DataFrame(rows)
    df_rows.to_csv(os.path.join(results_dir, "all_predictions.csv"), index=False)

    failures = df_rows[df_rows["true_label"] != df_rows["pred_label"]].copy()
    failures.to_csv(os.path.join(results_dir, "failed_cases.csv"), index=False)
    print(f"\nSaved {len(failures)} failure cases to: {os.path.join(results_dir, 'failed_cases.csv')}")

    # PR curve
    try:
        import matplotlib.pyplot as plt
        pr_precision, pr_recall, _ = precision_recall_curve(all_labels, all_probs)
        plt.figure()
        plt.plot(pr_recall, pr_precision, label=f"AP={ap:.2f}")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Precision-Recall Curve (Pairwise)")
        plt.legend()
        out_path = os.path.join(results_dir, "pr_curve.png")
        plt.savefig(out_path)
        print(f"Saved PR curve to: {out_path}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
