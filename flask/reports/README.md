# Evaluation Reports

This directory stores automatically generated reports from the model evaluation scripts.

## Contents
When you run `python flask/evaluate_final.py`, the following will be generated here:

- **`FINAL_EVALUATION_REPORT.md`**: A comprehensive summary of model performance.
- **`enhanced_evaluation/`**: Detailed metrics and confusion matrices.
    - `detailed_metrics.csv`
    - `statistical_significance.csv`
    - `confusion_matrix_*.png`
- **`eda/`**: Exploratory Data Analysis charts (class distribution, code lengths).
- **`error_analysis/`**: Examples of where the model failed.
- **`codebert_ablation/`**: Results from ablation studies (if run).

## Usage
To generate these reports, run:
```bash
cd flask
python evaluate_final.py
```
