import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report


def create_sample_dataset():
 
    # Sample clean code examples
    clean_codes = [
        "def add(a, b):\n    return a + b",
        "def multiply(x, y):\n    result = x * y\n    return result",
        "class Calculator:\n    def __init__(self):\n        self.result = 0",
        "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
        "def is_even(num):\n    return num % 2 == 0",
    ]

    # Sample buggy code examples
    buggy_codes = [
        "def divide(a, b):\n    return a / b",  # No zero check
        "while True:\n    print('infinite loop')",  # Infinite loop
        "result = eval(user_input)",  # Dangerous eval
        "password = input('Enter password: ')\nif password == 'admin':\n    login()",  # Hardcoded password
        "exec(user_code)",  # Dangerous exec
    ]

    # Create labels (0 = clean, 1 = buggy)
    X = clean_codes + buggy_codes
    y = [0] * len(clean_codes) + [1] * len(buggy_codes)

    return X, y


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
    print("=" * 60)
    print("Baseline C Training Script")
    print("=" * 60)

    # Load or create dataset
    print("\n1. Loading dataset...")
    X, y = create_sample_dataset()
    print(f"   Total samples: {len(X)}")
    print(f"   Clean samples: {sum(1 for label in y if label == 0)}")
    print(f"   Buggy samples: {sum(1 for label in y if label == 1)}")

    # Split dataset
    print("\n2. Splitting dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Training samples: {len(X_train)}")
    print(f"   Testing samples: {len(X_test)}")

    # Train model
    print("\n3. Training model...")
    # Get the path relative to the baselines directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flask_root = os.path.dirname(script_dir)
    model_path = os.path.join(flask_root, "models", "baseline_c_tfidf_lr.pkl")
    model = train_baseline_c(X_train, y_train, model_path)

    # Evaluate model
    print("\n4. Evaluating model...")
    accuracy = evaluate_model(model, X_test, y_test)

    # Test with sample predictions
    print("\n5. Testing sample predictions...")
    test_samples = [
        "def safe_divide(a, b):\n    if b == 0:\n        return None\n    return a / b",
        "while True:\n    pass"
    ]

    for i, sample in enumerate(test_samples, 1):
        pred = model.predict([sample])[0]
        prob = model.predict_proba([sample])[0]
        label = "Buggy" if pred == 1 else "Clean"
        confidence = max(prob)

        print(f"\nSample {i}: {label} (confidence: {confidence:.2%})")
        print(f"Code: {sample[:50]}...")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    print(f"\nYou can now use Baseline C in your Flask app.")
    print(f"The model is saved at: {model_path}")


if __name__ == "__main__":
    main()
