from flask import Flask, render_template, request

app = Flask(__name__)

def simple_review(code: str) -> dict:
    issues = []
    lines = code.splitlines()

    if not code.strip():
        return {
            "issues": ["No code provided. Paste some code to get feedback."],
            "summary": "Nothing to review yet."
        }

    for i, line in enumerate(lines, start=1):
        if len(line) > 100:
            issues.append(f"Line {i}: This line is very long. Try splitting it for better readability.")

        if "TODO" in line:
            issues.append(f"Line {i}: You left a TODO comment  try finishing or removing it.")

    if "print(" in code:
        issues.append("You used print statements  fine for learning, but consider cleaner output handling later.")

    if not issues:
        issues.append("No simple issues found! For real reviews, i will add static tools and AI later.")

    summary = "This is a simple demo review. In the future, Later I will be adding Flake8, Bandit, and CodeBERT."

    return {"issues": issues, "summary": summary}


@app.route("/", methods=["GET", "POST"])
def index():
    code = ""
    review_result = None

    if request.method == "POST":
        code = request.form.get("code", "")
        review_result = simple_review(code)

    return render_template("index.html", code=code, review=review_result)


if __name__ == "__main__":
    app.run(debug=True)
