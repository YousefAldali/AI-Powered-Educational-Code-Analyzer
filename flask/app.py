from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from models.CodeBERT_Python.classifier import CodeClassifier
from models.CodeBERT_Java.classifier import JavaCodeClassifier
from models.CodeBERT_CSharp.classifier import CSharpCodeClassifier
from models.codebert_baselines.baseline import run_static_analysis
from models.llm.tutor import generate_educational_explanation
from models.llm.code_patterns import analyze_code

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]}})

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# Language-specific classifiers
python_classifier = CodeClassifier()
java_classifier = JavaCodeClassifier()
csharp_classifier = CSharpCodeClassifier()

CLASSIFIERS = {
    "python": python_classifier,
    "java": java_classifier,
    "csharp": csharp_classifier,
}


@app.route("/api/review", methods=["POST"])
def review():
    code = ""
    language = "python"

    # Accept either a file upload or raw JSON body
    if request.content_type and "multipart/form-data" in request.content_type:
        file = request.files.get("file")
        if file:
            filename = file.filename.lower()
            if filename.endswith(".java"):
                language = "java"
            elif filename.endswith(".py"):
                language = "python"
            elif filename.endswith(".cs"):
                language = "csharp"
            else:
                return jsonify({"error": "Only .py, .java, and .cs files are supported."}), 400
            try:
                code = file.read().decode("utf-8")
            except Exception:
                return jsonify({"error": "Could not read uploaded file."}), 400
        else:
            code = request.form.get("code", "")
            language = request.form.get("language", "python")
    else:
        body = request.get_json(silent=True) or {}
        code = body.get("code", "")
        language = body.get("language", "python")

    if not code or not code.strip():
        return jsonify({"error": "No code provided."}), 400

    # Pick the right classifier for the language
    classifier = CLASSIFIERS.get(language)
    if classifier is None:
        return jsonify({"error": f"Unsupported language: {language}"}), 400

    #Run the analysis pipeline 

    # 1. Static Analysis (Bandit for Python, not yet available for Java)
    static_result = run_static_analysis(code, language=language)
    static_issues = static_result.get("issues", [])

    # 2. CodeBERT deep learning prediction (smart: chunks large files into functions/methods)
    # second check: CodeBERT AI (it can split big files)
    codebert_result = classifier.classify_smart(code)
    cb_label = codebert_result.get("label", "clean").lower()
    is_buggy = cb_label == "buggy"
    is_uncertain = cb_label == "uncertain"
    codebert_confidence = codebert_result.get("confidence", None)

    # 3. Combine verdicts: if Bandit finds security issues but CodeBERT says clean,
    overall_label = codebert_result.get("label", "clean")
    if static_issues and cb_label == "clean":
        overall_label = "buggy"
    elif static_issues and cb_label == "uncertain":
        overall_label = "buggy"

    # 3b. Pattern analysis: catch obvious bugs that CodeBERT may miss
    code_patterns = analyze_code(code, language)
    high_severity_patterns = [p for p in code_patterns if p.get("severity") == "high"]
    med_severity_patterns = [p for p in code_patterns if p.get("severity") in ("high", "medium")]

    # Override to buggy if high or medium severity patterns found regardless of CodeBERT
    if med_severity_patterns and cb_label in ("clean", "uncertain"):
        overall_label = "buggy"

    # 3c. Smart uncertain handling (no patterns found):
    #   - If NO patterns and confidence < 0.52 → downgrade to clean
    #   - If NO patterns but confidence >= 0.52 → keep uncertain (CodeBERT suspects a bug)
    if cb_label == "uncertain" and overall_label == "uncertain":
        if codebert_confidence is not None and codebert_confidence < 0.52 and not static_issues:
            overall_label = "clean"

    # 4. Educational LLM explanation (only when final verdict is NOT clean)
    llm_explanation = None
    if overall_label != "clean":
        llm_explanation = generate_educational_explanation(
            code=code,
            language=language,
            static_issues=static_issues,
            codebert_label=overall_label,
            flagged_functions=codebert_result.get("flagged_functions", [])
        )

    return jsonify({
        "prediction": {
            "label": overall_label,                             # Combined verdict
            "codebert_label": codebert_result.get("label", "clean"),  # Original CodeBERT-only verdict
            "confidence": codebert_confidence,
            "method": codebert_result.get("method", "direct"),  # "direct" | "chunked"
        },
        "static_analysis": {
            "issues": static_issues,
            "summary": static_result.get("summary", ""),
        },
        "code_patterns": code_patterns,                         # Pattern matches with line numbers
        "educational_explanation": llm_explanation,           # Markdown string from Qwen
        "language": language,
        "flagged_functions": codebert_result.get("flagged_functions", []),
        "total_functions": codebert_result.get("total_functions", 0),
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="127.0.0.1")
