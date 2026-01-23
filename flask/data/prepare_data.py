"""
Data Preparation Script with Anti-Leakage Guarantees

CRITICAL: This script prevents data leakage by splitting on Problem IDs, not rows.

Dataset Structure:
- Each Problem ID has TWO versions: buggy code and fixed code
- These versions are nearly identical (e.g., only 1-2 tokens different)
- If buggy and fixed versions appear in different splits, the model can "cheat"
  by memorizing near-duplicate patterns instead of learning bug detection

Anti-Leakage Strategy:
1. Extract unique Problem IDs
2. Shuffle IDs with fixed random seed (42) for reproducibility
3. Split IDs into 80% train, 10% val, 10% test
4. For each ID, BOTH buggy and fixed versions go to the SAME split
5. Verify no ID overlap between splits (assertions)

This ensures train/val/test are truly independent, preventing inflated metrics.

Labels:
- Buggy code: label = 1
- Fixed code: label = 0

Random Seed: 42 (for reproducibility)
Split Ratio: 80% train, 10% validation, 10% test
"""

import pandas as pd
import os
import random

def prepare_data():
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(base_dir, 'raw', 'code_bug_fix_pairs.csv')
    splits_dir = os.path.join(base_dir, 'splits')
    os.makedirs(splits_dir, exist_ok=True)

    print(f"Reading data from {raw_path}...")
    df = pd.read_csv(raw_path)

    # STRICT SEPARATION: Split by ID, NOT by row.
    unique_ids = list(df['id'].unique())
    print(f"Found {len(unique_ids)} unique problem IDs.")

    # Shuffle IDs specifically ensuring determinism
    random.seed(42)
    random.shuffle(unique_ids)

    # Split ratios: 80% Train, 10% Val, 10% Test
    n_total = len(unique_ids)
    n_train = int(n_total * 0.8)
    n_val = int(n_total * 0.1)
    # Remaining goes to test

    train_ids = unique_ids[:n_train]
    val_ids = unique_ids[n_train:n_train+n_val]
    test_ids = unique_ids[n_train+n_val:]

    print(f"Split IDs: Train={len(train_ids)}, Val={len(val_ids)}, Test={len(test_ids)}")

    # Verification: Ensure NO OVERLAP
    assert set(train_ids).isdisjoint(set(test_ids)), "CRITICAL ERROR: Train and Test IDs overlap!"
    assert set(train_ids).isdisjoint(set(val_ids)), "CRITICAL ERROR: Train and Val IDs overlap!"
    assert set(val_ids).isdisjoint(set(test_ids)), "CRITICAL ERROR: Val and Test IDs overlap!"
    print("Verification Passed: No ID overlap between splits.")

    def create_dataset(ids):
        # Filter dataframe by these IDs
        subset = df[df['id'].isin(ids)].copy()
        
        samples = []
        for _, row in subset.iterrows():
            # Label 1: Buggy Code
            samples.append({
                'text': row['buggy_code'],
                'label': 1,
                'id': row['id'],
                'type': 'buggy'
            })
            # Label 0: Fixed Code
            samples.append({
                'text': row['fixed_code'],
                'label': 0,
                'id': row['id'],
                'type': 'fixed'
            })
        return pd.DataFrame(samples)

    # Generate datasets
    train_df = create_dataset(train_ids)
    val_df = create_dataset(val_ids)
    test_df = create_dataset(test_ids)

    # Save to CSV
    train_df.to_csv(os.path.join(splits_dir, 'train.csv'), index=False)
    val_df.to_csv(os.path.join(splits_dir, 'val.csv'), index=False)
    test_df.to_csv(os.path.join(splits_dir, 'test.csv'), index=False)

    print(f"Saved splits to {splits_dir}")
    print(f"Train samples: {len(train_df)}")
    print(f"Val samples: {len(val_df)}")
    print(f"Test samples: {len(test_df)}")
    
    # Generate summary report
    print("\nData Split Summary Report")
    print(f"\nRandom Seed: 42")
    print(f"Split Ratio: 80% train, 10% val, 10% test")
    print(f"\nProblem ID Distribution:")
    print(f"  Train IDs:      {len(train_ids)}")
    print(f"  Validation IDs: {len(val_ids)}")
    print(f"  Test IDs:       {len(test_ids)}")
    print(f"  Total IDs:      {len(unique_ids)}")
    
    print(f"\nSample Distribution (buggy + fixed per ID):")
    print(f"  Train samples:      {len(train_df)} ({len(train_ids)} × 2)")
    print(f"  Validation samples: {len(val_df)} ({len(val_ids)} × 2)")
    print(f"  Test samples:       {len(test_df)} ({len(test_ids)} × 2)")
    
    print(f"\nClass Balance (label counts):")
    for split_name, split_df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
        clean = (split_df['label'] == 0).sum()
        buggy = (split_df['label'] == 1).sum()
        print(f"  {split_name:10s} - Clean: {clean}, Buggy: {buggy}")
    
    print("\nData leakage verification: PASSED")
    print("  No Problem IDs appear in multiple splits\n")

if __name__ == "__main__":
    prepare_data()
