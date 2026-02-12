import pandas as pd
import os
import random

def prepare_data():
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    clean_dir = os.path.join(base_dir, 'clean')
    languages_dir = os.path.join(clean_dir, 'languages')
    splits_dir = os.path.join(clean_dir, 'splits')
    os.makedirs(splits_dir, exist_ok=True)

    print("Reading data...")
    # Define raw files with their language labels (path relative to raw/)
    raw_files = [
        (os.path.join('languages', 'python', 'tssb_3m_cleaned.csv'), 'python'),   # Python dataset
        (os.path.join('languages', 'java', 'java_bug_fix_pairs.csv'), 'java'),     # Java data
        (os.path.join('languages', 'csharp', 'csharp_bug_fix_pairs.csv'), 'csharp'), # C# data
    ]
    
    dfs = []
    for filename, language in raw_files:
        path = os.path.join(base_dir, 'raw', filename)
        if os.path.exists(path):
            temp_df = pd.read_csv(path)
            temp_df['language'] = language
            print(f"  - Loaded {filename}: {len(temp_df)} pairs ({language})")
            dfs.append(temp_df)
        else:
            print(f"  - Warning: {filename} not found (skipping)")
            
    if not dfs:
        raise FileNotFoundError("No raw data files found in flask/data/raw/")
        
    df = pd.concat(dfs, ignore_index=True)
    
    # Print language distribution
    print(f"\nLanguage distribution:")
    for lang in df['language'].unique():
        count = len(df[df['language'] == lang])
        print(f"  {lang}: {count} pairs")

    # Save cleaned data per language into clean/languages/<lang>/
    print("\nSaving cleaned data per language...")
    for lang in df['language'].unique():
        lang_dir = os.path.join(languages_dir, lang)
        os.makedirs(lang_dir, exist_ok=True)
        lang_df = df[df['language'] == lang].copy()
        out_path = os.path.join(lang_dir, f'{lang}_cleaned.csv')
        lang_df.to_csv(out_path, index=False)
        print(f"  - Saved {lang}: {len(lang_df)} pairs -> clean/languages/{lang}/{lang}_cleaned.csv")

    # STRICT SEPARATION: Split by ID, NOT by row.
    unique_ids = list(df['id'].unique())
    print(f"\nFound {len(unique_ids)} unique problem IDs.")

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
            language = row.get('language', 'python')
            # Label 1: Buggy Code
            samples.append({
                'text': row['buggy_code'],
                'label': 1,
                'id': row['id'],
                'type': 'buggy',
                'language': language
            })
            # Label 0: Fixed Code
            samples.append({
                'text': row['fixed_code'],
                'label': 0,
                'id': row['id'],
                'type': 'fixed',
                'language': language
            })
        return pd.DataFrame(samples)

    # Generate datasets
    train_df = create_dataset(train_ids)
    val_df = create_dataset(val_ids)
    test_df = create_dataset(test_ids)

    # Save splits to clean/splits/
    train_df.to_csv(os.path.join(splits_dir, 'train.csv'), index=False)
    val_df.to_csv(os.path.join(splits_dir, 'val.csv'), index=False)
    test_df.to_csv(os.path.join(splits_dir, 'test.csv'), index=False)

    print(f"\nSaved splits to {splits_dir}")
    print(f"Train samples: {len(train_df)}")
    print(f"Val samples: {len(val_df)}")
    print(f"Test samples: {len(test_df)}")
    
    # Save per-language splits too
    print("\nSaving per-language splits...")
    for lang in df['language'].unique():
        lang_split_dir = os.path.join(languages_dir, lang, 'splits')
        os.makedirs(lang_split_dir, exist_ok=True)
        lang_train = train_df[train_df['language'] == lang]
        lang_val = val_df[val_df['language'] == lang]
        lang_test = test_df[test_df['language'] == lang]
        lang_train.to_csv(os.path.join(lang_split_dir, 'train.csv'), index=False)
        lang_val.to_csv(os.path.join(lang_split_dir, 'val.csv'), index=False)
        lang_test.to_csv(os.path.join(lang_split_dir, 'test.csv'), index=False)
        print(f"  - {lang}: train={len(lang_train)}, val={len(lang_val)}, test={len(lang_test)}")

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
