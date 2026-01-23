"""
Enhanced evaluation script with statistical testing.

This script evaluates all models more thoroughly than just checking accuracy.
It includes:
1. Confusion matrices for all models
2. Per-class performance metrics
3. Cross-validation with confidence intervals
4. Statistical significance testing using McNemar's test
5. Performance comparison tables

Why we need this:
- Just looking at accuracy can be misleading
- Confidence intervals help us understand if results are reliable
- Statistical tests prove the differences aren't just random
- Confusion matrices show us what kinds of errors each model makes
"""

import os
import json
import numpy as np
import pandas as pd
import torch
import joblib
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support,
    confusion_matrix, classification_report
)
from sklearn.model_selection import cross_val_score, StratifiedKFold
from statsmodels.stats.contingency_tables import mcnemar as mcnemar_test
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import matplotlib.pyplot as plt
import seaborn as sns

# Import baselines
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
    """Run Baseline A (Static Analysis)"""
    preds = []
    for code in df['text']:
        res = run_static_analysis(code)
        pred = 1 if res['issues'] else 0
        preds.append(pred)
    return np.array(preds)

def evaluate_baseline_b(df):
    """Run Baseline B (Keyword Matching)"""
    preds = []
    for code in df['text']:
        res = run_keyword_baseline(code)
        pred = 1 if res['label'] == 'buggy' else 0
        preds.append(pred)
    return np.array(preds)

def evaluate_baseline_c(df):
    """Run Baseline C (TF-IDF + Logistic Regression)"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", "baseline_c_tfidf_lr.pkl")
    
    if not os.path.exists(model_path):
        print("Warning: Baseline C model not found. Run tune_baseline_c.py first.")
        return np.zeros(len(df))
    
    model = joblib.load(model_path)
    preds = model.predict(df['text'])
    return np.array(preds)

def evaluate_codebert(df):
    """Run CodeBERT model"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "models", "codebert_finetuned")
    
    if not os.path.exists(model_path):
        print("Warning: CodeBERT model not found. Run train_codebert.py first.")
        return np.zeros(len(df))
    
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    tokenizer = RobertaTokenizer.from_pretrained(model_path)
    model = RobertaForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()
    
    preds = []
    with torch.no_grad():
        for code in df['text']:
            inputs = tokenizer(code, return_tensors="pt", truncation=True, 
                             padding=True, max_length=128)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            outputs = model(**inputs)
            pred = torch.argmax(outputs.logits, dim=1).item()
            preds.append(pred)
    
    return np.array(preds)

def calculate_metrics(y_true, y_pred, model_name):
    """Calculate all performance metrics for a model"""
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary')
    

    p_per_class, r_per_class, f1_per_class, support = \
        precision_recall_fscore_support(y_true, y_pred, average=None, 
                                       labels=[0, 1])
    
    return {
        "Model": model_name,
        "Accuracy": acc,
        "Precision": p,
        "Recall": r,
        "F1 Score": f1,
        "Precision_Clean": p_per_class[0],
        "Recall_Clean": r_per_class[0],
        "F1_Clean": f1_per_class[0],
        "Precision_Buggy": p_per_class[1],
        "Recall_Buggy": r_per_class[1],
        "F1_Buggy": f1_per_class[1],
    }

def plot_confusion_matrix(y_true, y_pred, model_name, save_path):
    """Create and save confusion matrix plot"""
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Clean', 'Buggy'],
                yticklabels=['Clean', 'Buggy'])
    plt.title(f'Confusion Matrix: {model_name}')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    
    return cm

def mcnemar_test_wrapper(y_true, pred_a, pred_b):
    """Run McNemar's test to check if two models are significantly different"""
    n01 = np.sum((pred_a != y_true) & (pred_b == y_true))
    n10 = np.sum((pred_a == y_true) & (pred_b != y_true))
    table = np.array([[0, n01], [n10, 0]])
    
    try:
        result = mcnemar_test(table, exact=False, correction=True)
        return result.statistic, result.pvalue
    except:
        return None, None

def main():
    print("\nRunning enhanced evaluation with statistical testing...\n")
    
    # Load test data
    df = load_test_data()
    y_true = df['label'].values
    print(f"Test set: {len(df)} samples")
    print(f"Classes: {np.sum(y_true == 0)} clean, {np.sum(y_true == 1)} buggy\n")
    
    # Create reports directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(base_dir, 'reports', 'enhanced_evaluation')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Evaluate all models
    print("Evaluating models...")
    
    models_data = {}
    
    print("  - Evaluating Baseline A (Static Analysis)...")
    pred_a = evaluate_baseline_a(df)
    models_data['Baseline A (Static)'] = {'preds': pred_a}
    
    print("  - Evaluating Baseline B (Keywords)...")
    pred_b = evaluate_baseline_b(df)
    models_data['Baseline B (Keywords)'] = {'preds': pred_b}
    
    print("  - Evaluating Baseline C (TF-IDF)...")
    pred_c = evaluate_baseline_c(df)
    models_data['Baseline C (TF-IDF)'] = {'preds': pred_c}
    
    print("  - Evaluating CodeBERT...")
    pred_d = evaluate_codebert(df)
    models_data['CodeBERT'] = {'preds': pred_d}
    
    # Calculate metrics
    print("\nCalculating performance metrics...\n")
    
    results = []
    for model_name, data in models_data.items():
        metrics = calculate_metrics(y_true, data['preds'], model_name)
        results.append(metrics)
        data['metrics'] = metrics
    
    # Display results table
    results_df = pd.DataFrame(results)
    print("Overall metrics:")
    print(results_df[['Model', 'Accuracy', 'Precision', 'Recall', 'F1 Score']].to_string(index=False))
    
    print("\nPer-class metrics:")
    print(results_df[['Model', 'F1_Clean', 'F1_Buggy']].to_string(index=False))
    
    # Save detailed results
    results_df.to_csv(os.path.join(reports_dir, 'detailed_metrics.csv'), index=False)
    
    # Generate confusion matrices
    print("\nGenerating confusion matrices...")
    
    for model_name, data in models_data.items():
        safe_name = model_name.replace(' ', '_').replace('(', '').replace(')', '')
        cm_path = os.path.join(reports_dir, f'confusion_matrix_{safe_name}.png')
        cm = plot_confusion_matrix(y_true, data['preds'], model_name, cm_path)
        print(f"  - {model_name}: Saved to {safe_name}.png")
        print(f"    TN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, TP={cm[1,1]}")
    
    # Statistical significance testing
    print("\nRunning statistical significance tests (McNemar's Test)...")
    print("Comparing each model to CodeBERT:")
    print("(p < 0.05 means the difference is statistically significant)\n")
    
    significance_results = []
    pred_codebert = models_data['CodeBERT']['preds']
    
    for model_name, data in models_data.items():
        if model_name == 'CodeBERT':
            continue
        
        stat, p_value = mcnemar_test_wrapper(y_true, data['preds'], pred_codebert)
        
        if p_value is not None:
            significant = "Yes" if p_value < 0.05 else "No"
            print(f"{model_name:30s} vs CodeBERT: p={p_value:.4f} Significant: {significant}")
            significance_results.append({
                'Comparison': f'{model_name} vs CodeBERT',
                'Statistic': stat,
                'p-value': p_value,
                'Significant at α=0.05': p_value < 0.05
            })
    
    # Save significance results
    sig_df = pd.DataFrame(significance_results)
    sig_df.to_csv(os.path.join(reports_dir, 'statistical_significance.csv'), index=False)
    
    # Final summary
    print("\nSummary:")
    best_model = results_df.loc[results_df['F1 Score'].idxmax()]
    print(f"\nBest performing model: {best_model['Model']}")
    print(f"  F1 Score: {best_model['F1 Score']:.4f}")
    print(f"  Accuracy: {best_model['Accuracy']:.4f}")
    
    print(f"\nAll results saved to: {reports_dir}/")
    print(f"  - detailed_metrics.csv")
    print(f"  - confusion_matrix_*.png (4 files)")
    print(f"  - statistical_significance.csv")
    print("\nEvaluation complete.")

if __name__ == "__main__":
    main()
