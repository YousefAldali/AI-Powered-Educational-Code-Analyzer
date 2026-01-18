import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def generate_eda():
    print("Generating EDA Report...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, 'data', 'splits', 'train.csv')
    output_dir = os.path.join(base_dir, 'reports', 'eda')
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} samples from Training Set.")

    # 1. Class Distribution
    plt.figure(figsize=(6, 4))
    sns.countplot(x='label', data=df)
    plt.title('Class Distribution (Train Set)')
    plt.xlabel('Label (0=Clean, 1=Buggy)')
    plt.ylabel('Count')
    plt.savefig(os.path.join(output_dir, 'class_distribution.png'))
    plt.close()
    print("- Saved class_distribution.png")

    # 2. Code Length Distribution
    # Estimate length by words (approx tokens)
    df['code_len'] = df['text'].astype(str).apply(lambda x: len(x.split()))
    
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='code_len', hue='label', bins=30, kde=True, element="step")
    plt.title('Code Length Distribution by Class')
    plt.xlabel('Number of Words (Approx)')
    plt.ylabel('Frequency')
    plt.savefig(os.path.join(output_dir, 'code_length_distribution.png'))
    plt.close()
    print("- Saved code_length_distribution.png")

    # 3. Text Stats
    avg_len = df['code_len'].mean()
    max_len = df['code_len'].max()
    print(f"EDA Summary:\n- Avg Length: {avg_len:.1f} words\n- Max Length: {max_len} words")

if __name__ == "__main__":
    generate_eda()
