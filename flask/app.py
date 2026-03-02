from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from models.CodeBERT.classifier import CodeClassifier
from baselines.baseline import run_static_analysis
from models.llm.tutor import generate_educational_explanation

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]}})

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

classifier = CodeClassifier()


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
            else:
                return jsonify({"error": "Only .py and .java files are supported."}), 400
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

    # --- Run the analysis pipeline ---

    # 1. Static Analysis (Bandit for Python)
    static_result = run_static_analysis(code)
    static_issues = static_result.get("issues", [])

    # 2. CodeBERT deep learning prediction (smart: chunks large files into functions)
    codebert_result = classifier.classify_smart(code)
    cb_label = codebert_result.get("label", "clean").lower()
    is_buggy = cb_label == "buggy"
    is_uncertain = cb_label == "uncertain"
    codebert_confidence = codebert_result.get("confidence", None)

    # 3. Educational LLM explanation (only if bugs found or uncertain)
    llm_explanation = None
    if is_buggy or is_uncertain or static_issues:
        llm_explanation = generate_educational_explanation(
            code=code,
            language=language,
            static_issues=static_issues,
            codebert_label=codebert_result.get("label", "clean"),
            flagged_functions=codebert_result.get("flagged_functions", [])
        )

    return jsonify({
        "prediction": {
            "label": codebert_result.get("label", "clean"),   # "buggy" | "clean"
            "confidence": codebert_confidence,
            "method": codebert_result.get("method", "direct"),  # "direct" | "chunked"
        },
        "static_analysis": {
            "issues": static_issues,
            "summary": static_result.get("summary", ""),
        },
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
