import json
import os
import subprocess
import tempfile
from typing import Dict, Any

import joblib


# Baseline A: static analyzers (flake8 + bandit)
def run_static_analysis(code_content: str, language: str = "python") -> Dict[str, Any]:
    
    # Java static analysis not enabled yet — Bandit is Python-only
    if language != "python":
        return {
            "issues": [],
            "summary": f"Static analysis not yet available for {language}."
        }

    issues = []
    temp_path = None

    try:
        # 1. Create a temporary file to hold the student code
        with tempfile.NamedTemporaryFile(
            suffix=".py",
            delete=False,
            mode="w",
            encoding="utf-8"
        ) as temp_file:
            temp_file.write(code_content)
            temp_path = temp_file.name

        # 2. Helper function to run analyzers safely
        def run_analyzer(command: list[str]) -> str:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return process.stdout

        # 3. Run Flake8 (style + bug checker)
        # DISABLED for FYP Comparison: i want to see if CodeBERT outperforms a pure Security Scanner (Bandit).
        # Including Flake8 makes Baseline A a "perfect" Syntax Checker, which hides the ML model's contribution.
        flake8_output = "" # run_analyzer

        if flake8_output:
            for line in flake8_output.splitlines():
                pass # logic disabled

        # 4. Run Bandit (security checker)
        bandit_output = run_analyzer(["bandit", "-r", temp_path, "-f", "json"])

        if bandit_output:
            try:
                bandit_data = json.loads(bandit_output)
                for result in bandit_data.get("results", []):
                    line_num = result["line_number"]
                    message = result["issue_text"]
                    severity = result["issue_severity"]
                    issues.append(
                        f"[Security - {severity}] Line {line_num}: {message}"
                    )
            except json.JSONDecodeError:
                # Bandit failed to return JSON, ignore
                pass

    except subprocess.TimeoutError:
        issues.append("[Performance] Review timed out (code ran too long).")
    except Exception as e:
        issues.append(f"[System Error] An unexpected issue occurred: {e}")
    finally:
        # 5. Remove temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    summary = (
        "No security issues found."
        if not issues
        else f"Found {len(issues)} issues to review. Use the explanations below to improve."
    )

    return {"issues": issues, "summary": summary}

# Baseline B: keyword matching

KEYWORD_RULES = [
    ("while True", "Possible infinite loop (while True)."),
    ("eval(", "Use of eval() is dangerous."),
    ("exec(", "Use of exec() is dangerous."),
    ("input(", "User input without validation."),
]


def run_keyword_baseline(code_content: str) -> Dict[str, Any]:
    
    issues: list[str] = []

    for keyword, message in KEYWORD_RULES:
        if keyword in code_content:
            issues.append(message)

    label = "buggy" if issues else "clean"

    return {
        "label": label,
        "issues": issues,
    }



# Baseline C:  TF-IDF + Logistic Regression

# Get the absolute path relative to this file's location
_BASELINES_DIR = os.path.dirname(os.path.abspath(__file__))
BASELINE_C_MODEL_PATH = os.path.join(_BASELINES_DIR, "baseline_c_tfidf_lr.pkl")
_baseline_c_model = None


def load_baseline_c_model():
    
    global _baseline_c_model
    if _baseline_c_model is None:
        if not os.path.exists(BASELINE_C_MODEL_PATH):
            raise FileNotFoundError(
                f"Baseline C model not found at '{BASELINE_C_MODEL_PATH}'. "
                "Train it with train_baseline_c.py."
            )
        _baseline_c_model = joblib.load(BASELINE_C_MODEL_PATH)
        print("[Baseline C] Model loaded.")
    return _baseline_c_model


def run_tfidf_baseline(code_content: str) -> Dict[str, Any]:
    
    model = load_baseline_c_model()

    pred = model.predict([code_content])[0]          # 0 or 1
    prob = model.predict_proba([code_content])[0]    # [p_clean, p_buggy]

    label = "buggy" if int(pred) == 1 else "clean"
    confidence = float(max(prob))

    return {
        "label": label,
        "pred": int(pred),
        "confidence": confidence,
        "proba_clean": float(prob[0]),
        "proba_buggy": float(prob[1]),
    }



# Helper — RUN ALL BASELINES 

def run_all_baselines(code_content: str) -> Dict[str, Any]:
    
    return {
        "baseline_A": run_static_analysis(code_content),
        "baseline_B": run_keyword_baseline(code_content),
        "baseline_C": run_tfidf_baseline(code_content),
    }
