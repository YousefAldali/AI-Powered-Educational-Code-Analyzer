import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report

def load_data(split_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'clean', 'splits', f'{split_name}.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data split not found: {path}. Run prepare_data.py first.")
    
    df = pd.read_csv(path)
    # Ensure all text is string
    df['text'] = df['text'].astype(str).fillna('')
    return df['text'].tolist(), df['label'].tolist()

def train_baseline_c(X_train, y_train, save_path):
   
    print("Training Baseline C (TF-IDF + Logistic Regression)...")

    # Create a pipeline with TF-IDF and Logistic Regression
    model = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.9
        )),
        ('classifier', LogisticRegression(
            max_iter=1000,
            random_state=42
        ))
    ])

    # Train the model
    model.fit(X_train, y_train)

    # Save the model
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    joblib.dump(model, save_path)

    print(f"Model saved to: {save_path}")
    return model


def evaluate_model(model, X_test, y_test):
    print("\nEvaluating model...")

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\nAccuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Clean', 'Buggy']))

    return accuracy


def main():
    print("\nBaseline C Training Script\n")

    # Load datasets
    print("Loading datasets...")
    try:
        X_train, y_train = load_data('train')
        X_val, y_val = load_data('val')
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    
    # Class distribution
    print(f"  Train class distribution: Clean={y_train.count(0)}, Buggy={y_train.count(1)}")

    # Train model
    print("\nTraining model...")
    # Get the path relative to the baselines directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flask_root = os.path.dirname(script_dir)
    model_path = os.path.join(flask_root, "models", "baseline_c_tfidf_lr.pkl")
    model = train_baseline_c(X_train, y_train, model_path)

    # Evaluate model
    print("\nEvaluating on validation set...")
    accuracy = evaluate_model(model, X_val, y_val)

    print("\nTraining complete!")
    print(f"Model saved at: {model_path}\n")

if __name__ == "__main__":
    main()
