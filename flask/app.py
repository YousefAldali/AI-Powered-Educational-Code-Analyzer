from flask import Flask, render_template, request
import os
import subprocess
import tempfile
import json

app = Flask(__name__)


app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # Later I can change this to 50MB

def run_static_analysis(code_content: str) -> dict:
    issues = []
    temp_path = None
    
    try:
        # 1. Create a temporary file to hold the student code 
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(code_content)
            temp_path = temp_file.name
        
        # 2. Helper function to run analyzers safely
        def run_analyzer(command: list) -> str:
            process = subprocess.run(
                command,
                capture_output=True, text=True, timeout=10
            )
            return process.stdout
            
        # 3. Run Flake8 (style + bug checker)
        flake8_output = run_analyzer(["flake8", "--format=default", temp_path])
        
        if flake8_output:
            for line in flake8_output.splitlines():
                parts = line.split(":")
                if len(parts) >= 5:
                    line_num = parts[1].strip()
                    code_msg = parts[3].strip()
                    message = ":".join(parts[4:]).strip()
                    issues.append(f"[Style/Bug - {code_msg}] Line {line_num}: {message}")

        # 4. Run Bandit (security checker)
        bandit_output = run_analyzer(["bandit", "-r", temp_path, "-f", "json"])
        
        if bandit_output:
            try:
                bandit_data = json.loads(bandit_output)
                for result in bandit_data.get('results', []):
                    line_num = result['line_number']
                    message = result['issue_text']
                    severity = result['issue_severity']
                    issues.append(f"[Security - {severity}] Line {line_num}: {message}")
            except json.JSONDecodeError:
                pass  # Bandit failed to return JSON
        
    except subprocess.TimeoutError:
        issues.append("[Performance] Review timed out (Code ran too long).")
    except Exception as e:
        issues.append(f"[System Error] An unexpected issue occurred: {e}")
    finally:
        # 5. Remove temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    
    summary = (
        "Your code looks clean! No static analysis issues found."
        if not issues else
        f"Found {len(issues)} issues to review. Use the explanations below to improve."
    )

    return {"issues": issues, "summary": summary}

@app.route("/", methods=["GET", "POST"])
def index():
    code = ""
    review_result = None

    if request.method == "POST":
        file = request.files.get("file")
        
        if file and (file.filename.endswith(".py") or file.filename.endswith(".java")):
            try:
                code = file.read().decode("utf-8")
            except Exception:
                review_result = {"issues": ["Could not read uploaded file"], "summary": "Upload error."}
        else:
            code = request.form.get("code", "")
            
        if code and code.strip():
            review_result = run_static_analysis(code)
        else:
            review_result = {"issues": ["Please submit some code or upload a file."], "summary": "Empty input."}
                
    return render_template("index.html", code=code, review=review_result)

if __name__ == "__main__":
    if not os.path.isdir('templates'):
        os.mkdir('templates')
    if not os.path.isdir('static'):
        os.mkdir('static')
        
    print("Static Analyzer Review Tool is running..")
    app.run(debug=True)
