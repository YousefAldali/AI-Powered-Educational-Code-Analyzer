import os
import pandas as pd
import torch
import joblib
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import RobertaTokenizer, RobertaForSequenceClassification

# Import Baselines
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from baselines.baseline import run_static_analysis, run_keyword_baseline

def load_test_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data", "splits", "test.csv")
    df = pd.read_csv(path)
    df['text'] = df['text'].astype(str).fillna('')
    return df

def evaluate_baseline_a(df):
    preds = []
    print("Running Baseline A (Static Analysis)...")
    for code in df['text']:
        res = run_static_analysis(code)
        pred = 1 if res['issues'] else 0
        preds.append(pred)
    return preds

def evaluate_baseline_b(df):
    preds = []
    print("Running Baseline B (keywords)...")
    for code in df['text']:
        res = run_keyword_baseline(code)
        pred = 1 if res['label'] == 'buggy' else 0
        preds.append(pred)
    return preds

def evaluate_baseline_c(df):
    print("Running Baseline C (TF-IDF)...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", "baseline_c_tfidf_lr.pkl")
    
    if not os.path.exists(model_path):
        print("Warning: Baseline C model not found.")
        return [0] * len(df) 

    model = joblib.load(model_path)
    preds = model.predict(df['text']).tolist()
    return preds

def evaluate_codebert(df):
    print("Running CodeBERT...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # CORRECT: Ensure we point to the fine-tuned folder
    model_path = os.path.join(base_dir, "models", "codebert_finetuned")
    
    print(f"Loading CodeBERT from: {model_path}")
    
    if not os.path.exists(model_path):
        print("Warning: CodeBERT model not found.")
        return [0] * len(df)

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    tokenizer = RobertaTokenizer.from_pretrained(model_path)
    model = RobertaForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()

    preds = []
    with torch.no_grad():
        for code in df['text']:
            inputs = tokenizer(code, return_tensors="pt", truncation=True, padding=True, max_length=128)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            outputs = model(**inputs)
            logits = outputs.logits
            pred = torch.argmax(logits, dim=1).item()
            preds.append(pred)
    return preds

def calculate_metrics(y_true, y_pred, name):
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
    return {
        "Model": name,
        "Accuracy": acc,
        "Precision": p,
        "Recall": r,
        "F1 Score": f1
    }

def main():
    print("="*60)
    print("FINAL EVALUATION ON TEST SET")
    print("="*60)

    try:
        df = load_test_data()
        y_true = df['label'].tolist()
        print(f"Loaded {len(df)} test samples.")
    except Exception as e:
        print(f"Error loading test data: {e}")
        return

    results = []

    # 1. Baseline A
    y_pred_a = evaluate_baseline_a(df)
    results.append(calculate_metrics(y_true, y_pred_a, "Baseline A (Static)"))

    # 2. Baseline B
    y_pred_b = evaluate_baseline_b(df)
    results.append(calculate_metrics(y_true, y_pred_b, "Baseline B (Keywords)"))

    # 3. Baseline C
    y_pred_c = evaluate_baseline_c(df)
    results.append(calculate_metrics(y_true, y_pred_c, "Baseline C (TF-IDF)"))

    # 4. CodeBERT
    y_pred_d = evaluate_codebert(df)
    results.append(calculate_metrics(y_true, y_pred_d, "Deep ML (CodeBERT)"))

    # Print Table
    results_df = pd.DataFrame(results)
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    print(results_df.to_string(index=False))
    
    # Save results
    results_df.to_csv("evaluation_results.csv", index=False)
    print("\nSaved results to evaluation_results.csv")

if __name__ == "__main__":
    main()
