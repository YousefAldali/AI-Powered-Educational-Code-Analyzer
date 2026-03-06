import pandas as pd
import numpy as np
import os
import hashlib
from tqdm import tqdm
from sklearn.metrics import accuracy_score, roc_auc_score, classification_report

# Config
LOCKED_TEST_CSV = "trained_model_ctssb_pair_github_style/ctssb_pair_test_locked.csv"
SEED = 42

def normalize_tokenize(code: str) -> set:
    """Simple tokenization: split by whitespace, remove special chars."""
    # This is a 'Bag of Tokens' approach
    code = str(code).lower()
    for char in "(){}[].!=+-*/;:,<>":
        code = code.replace(char, f" {char} ")
    return set(code.split())

def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def sha1_u64(s: str) -> int:
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()
    return int(h[:16], 16)

def main():
    print("--- Baseline: Jaccard Similarity (Token Overlap) ---")
    
    if not os.path.exists(LOCKED_TEST_CSV):
        print(f"Error: Locked test set not found at {LOCKED_TEST_CSV}")
        return

    print(f"Loading data: {LOCKED_TEST_CSV}")
    df = pd.read_csv(LOCKED_TEST_CSV)
    
    buggy_codes = df["buggy_code"].astype(str).tolist()
    fixed_codes = df["fixed_code"].astype(str).tolist()
    ids = df["id"].tolist()
    
    y_true = []
    y_scores = []
    y_pred = []
    
    print("Evaluating baseline...")
    
    # We evaluate exactly like the DL model: Positive vs Random Negative
    for i in tqdm(range(len(df))):
        buggy_tokens = normalize_tokenize(buggy_codes[i])
        
        # 1. Positive Pair
        fixed_pos_tokens = normalize_tokenize(fixed_codes[i])
        sim_pos = jaccard_similarity(buggy_tokens, fixed_pos_tokens)
        
        y_true.append(1)
        y_scores.append(sim_pos)
        
        # 2. Negative Pair (Deterministic Random)
        rng = np.random.RandomState(SEED + int(ids[i]) + i*999) # different seed offset
        rand_idx = i
        while rand_idx == i:
            rand_idx = rng.randint(0, len(df))
            
        fixed_neg_tokens = normalize_tokenize(fixed_codes[rand_idx])
        sim_neg = jaccard_similarity(buggy_tokens, fixed_neg_tokens)
        
        y_true.append(0)
        y_scores.append(sim_neg)
    
    # Threshold for accuracy? 
    # Jaccard isn't a probability, but we can treat it as a ranker.
    # For accuracy, we can't easily pick a threshold, but AUC is the gold standard for ranking.
    # Let's try a dynamic threshold: if sim > 0.8? No, that's arbitrary.
    # Let's just output AUC and average scores.
    
    auc = roc_auc_score(y_true, y_scores)
    
    # To get accuracy, we can cheat slightly and assume "Higher similarity = Positive"
    # But in reality, buggy and fixed are VERY similar (often 95%+), while buggy and random are dissimilar.
    # So a simple threshold like 0.5 works well for buggy vs RANDOM.
    # But buggy vs WRONG FIX might be harder. Here we test vs RANDOM (GitHub style).
    
    y_pred_50 = [1 if s > 0.5 else 0 for s in y_scores]
    acc_50 = accuracy_score(y_true, y_pred_50)
    
    print("\n" + "="*40)
    print("BASELINE RESULTS (Jaccard Similarity)")
    print("="*40)
    print(f"ROC-AUC:  {auc:.4f}")
    print(f"Accuracy (thresh=0.5): {acc_50:.4f}")
    print("-" * 40)
    
    # Save results
    out_file = "trained_model_ctssb_pair_github_style/results/baseline_results.txt"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        f.write("Baseline: Jaccard Similarity\n")
        f.write(f"ROC-AUC: {auc:.4f}\n")
        f.write(f"Accuracy (0.5): {acc_50:.4f}\n")
    print(f"Saved results to {out_file}")

if __name__ == "__main__":
    main()
