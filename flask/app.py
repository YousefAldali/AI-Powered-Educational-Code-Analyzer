from flask import Flask, render_template, request
import os
import subprocess
import tempfile
import json
from models.CodeBERT.classifier import CodeClassifier
from baselines.baseline import run_static_analysis, run_keyword_baseline, run_tfidf_baseline

app = Flask(__name__)


app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # Later I can change this to 50MB

classifier = CodeClassifier()


@app.route("/", methods=["GET", "POST"])
def index():
    code = ""
    review_result = None
    baseline_b_result = None
    baseline_c_result = None
    codebert_result = None

    if request.method == "POST":
        file = request.files.get("file")
        
        if file and (file.filename.endswith(".py") or file.filename.endswith(".java")):
            try:
                code = file.read().decode("utf-8")
            except:
                review_result = {
                    "issues": ["Could not read uploaded file"],
                    "summary": "Upload error."
                }
        else:
            code = request.form.get("code", "")
        
        if code and code.strip():
            # Baseline A
            review_result = run_static_analysis(code)

            # Baseline B
            baseline_b_result = run_keyword_baseline(code)
            
            # Baseline C
            baseline_c_result = run_tfidf_baseline(code)
            
            # Deep ML (CodeBERT)
            codebert_result = classifier.classify(code)
        else:
            review_result = {
                "issues": ["Please submit some code or upload a file."],
                "summary": "Empty input."
            }

    return render_template(
        "index.html",
        code=code,
        review=review_result,
        baseline_b=baseline_b_result,
        baseline_c=baseline_c_result,
        codebert=codebert_result
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
