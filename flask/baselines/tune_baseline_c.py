import os
import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, make_scorer, f1_score
import joblib
from datetime import datetime

def load_data(split_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'splits', f'{split_name}.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data split not found: {path}")
    
    df = pd.read_csv(path)
    df['text'] = df['text'].astype(str).fillna('')
    return df['text'].tolist(), df['label'].tolist()

def tune_baseline_c():
    print("\nStarting hyperparameter tuning for Baseline C...\n")
    
    print("Loading training data...")
    X_train, y_train = load_data('train')

    print(f"  Class distribution: Clean={y_train.count(0)}, Buggy={y_train.count(1)}")
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer()),
        ('classifier', LogisticRegression(max_iter=1000, random_state=42))
    ])
    
    # Define hyperparameter search space
    print("\nSetting up hyperparameter search space...")
    param_grid = {
        # TF-IDF parameters
        'tfidf__max_features': [1000, 5000, 10000],
        'tfidf__ngram_range': [(1, 1), (1, 2), (1, 3)],
        'tfidf__min_df': [1, 2, 5],
        'tfidf__max_df': [0.7, 0.9, 1.0],
        
        # Logistic Regression parameters
        'classifier__C': [0.01, 0.1, 1.0, 10.0],
        'classifier__penalty': ['l2'],  # l1 requires different solver
        'classifier__class_weight': [None, 'balanced']
    }
    
    total_combinations = (
        len(param_grid['tfidf__max_features']) *
        len(param_grid['tfidf__ngram_range']) *
        len(param_grid['tfidf__min_df']) *
        len(param_grid['tfidf__max_df']) *
        len(param_grid['classifier__C']) *
        len(param_grid['classifier__penalty']) *
        len(param_grid['classifier__class_weight'])
    )
    
    print(f"  Total parameter combinations: {total_combinations}")
    print(f"  Using 5-fold cross-validation")
    print(f"  Total fits: {total_combinations * 5}")
    
    # Perform grid search
    print("\nStarting GridSearchCV (this will take a few minutes)...") 
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=5,  # 5-fold cross-validation
        scoring='f1',  # Optimize for F1 score (balanced metric)
        n_jobs=-1,  # Use all CPU cores
        verbose=2,
        return_train_score=True
    )
    
    grid_search.fit(X_train, y_train)
    
    # Results
    print("\nTuning complete!\n")
    
    print(f"Best F1 Score (Cross-Validation): {grid_search.best_score_:.4f}\n")
    print("Best Parameters:")
    for param, value in grid_search.best_params_.items():
        print(f"  {param}: {value}")
    
    # Save best model
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    model_path = os.path.join(models_dir, 'baseline_c_tfidf_lr.pkl')
    
    # Backup old model if it exists
    if os.path.exists(model_path):
        backup_path = os.path.join(models_dir, 'baseline_c_tfidf_lr_backup.pkl')
        os.rename(model_path, backup_path)
        print(f"\nOld model backed up to: baseline_c_tfidf_lr_backup.pkl")
    
    joblib.dump(grid_search.best_estimator_, model_path)
    print(f"Best model saved to: {model_path}")
    
    # Save hyperparameter search results
    results_df = pd.DataFrame(grid_search.cv_results_)
    results_path = os.path.join(models_dir, 'baseline_c_tuning_results.csv')
    results_df.to_csv(results_path, index=False)
    print(f"Full results saved to: baseline_c_tuning_results.csv")
    
    # Save best parameters as JSON for documentation
    params_dict = {
        'best_params': grid_search.best_params_,
        'best_cv_f1_score': float(grid_search.best_score_),
        'tuning_date': datetime.now().isoformat(),
        'total_combinations_tested': total_combinations,
        'cv_folds': 5,
        'training_samples': len(X_train),
        'optimization_metric': 'f1',
        'search_space': {k: [str(v) for v in vals] for k, vals in param_grid.items()}
    }
    
    params_path = os.path.join(models_dir, 'baseline_c_best_params.json')
    with open(params_path, 'w') as f:
        json.dump(params_dict, f, indent=2)
    print(f"Parameters documented in: baseline_c_best_params.json")
    
    # Evaluate on validation set
    print("\nEvaluating on validation set...\n")
    
    X_val, y_val = load_data('val')
    y_pred = grid_search.best_estimator_.predict(X_val)
    
    print(f"Validation Samples: {len(X_val)}\n")
    print("Classification Report:")
    print(classification_report(y_val, y_pred, target_names=['Clean', 'Buggy']))
    
    # Compare to default parameters
    print("\nComparing tuned vs default parameters:\n")
    
    default_pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2), min_df=1, max_df=0.9)),
        ('classifier', LogisticRegression(max_iter=1000, random_state=42))
    ])
    default_pipeline.fit(X_train, y_train)
    default_pred = default_pipeline.predict(X_val)
    default_f1 = f1_score(y_val, default_pred)
    tuned_f1 = f1_score(y_val, y_pred)
    
    print(f"  Default Parameters F1: {default_f1:.4f}")
    print(f"  Tuned Parameters F1:   {tuned_f1:.4f}")
    print(f"  Improvement:           {(tuned_f1 - default_f1):.4f} ({((tuned_f1/default_f1 - 1) * 100):.1f}%)")
    
    print("\nNote for academic purposes:")
    print("""
This hyperparameter tuning makes sure we're comparing Baseline C fairly to CodeBERT.
Without this, someone could argue that Baseline C only lost because we didn't
configure it well, rather than because TF-IDF has fundamental limitations.

The tuned parameters will be used in all our evaluations from now on.
    """)

if __name__ == "__main__":
    tune_baseline_c()
