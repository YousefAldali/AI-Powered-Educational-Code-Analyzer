"""
Lightweight code pattern analyser for common bugs.
Used by the placeholder explanation when GPU / LLM is not available.

Each analyser returns a list of dicts with keys:
    line, type, severity (high|medium|low), description, detail, fix,
    line_content, concept
"""

import ast
import re
from typing import List, Dict


# ── Python ──────────────────────────────────────────────────────────

def analyze_python_patterns(code: str) -> List[Dict]:
    findings: List[Dict] = []
    lines = code.splitlines()

    # ── regex-based patterns ──

    for i, line in enumerate(lines, 1):
        stripped = line.split("#")[0]  # ignore comments

        # 1. Swapped compound operators: =+  =-  =*  =/
        for op, correct in [("=+", "+="), ("=-", "-="), ("=*", "*="), ("=/", "/=")]:
            if op in stripped:
                match = re.search(r"(\w+)\s*" + re.escape(op) + r"\s*", stripped)
                if match:
                    findings.append({
                        "line": i,
                        "type": "swapped_operator",
                        "severity": "high",
                        "description": f"`{op}` should likely be `{correct}` (compound assignment)",
                        "detail": (
                            f"Python reads `x {op} y` as `x = ({op[1]}y)` — a plain "
                            f"assignment with a unary `{op[1]}` — instead of `x {correct} y` "
                            f"which updates `x` in place."
                        ),
                        "fix": f"Change `{op}` to `{correct}`.",
                        "line_content": line.strip(),
                        "concept": "Compound Assignment Operators",
                    })

        # 2. Division by len() without empty-check
        if "/" in stripped and "//" not in stripped:
            m = re.search(r"/\s*len\((\w+)\)", stripped)
            if m:
                var = m.group(1)
                findings.append({
                    "line": i,
                    "type": "division_by_zero",
                    "severity": "medium",
                    "description": f"Division by `len({var})` without checking for empty input",
                    "detail": (
                        f"If `{var}` is an empty list (or string), `len({var})` returns 0, "
                        f"causing a `ZeroDivisionError` at runtime."
                    ),
                    "fix": f"Add a guard before dividing: `if not {var}: return 0`",
                    "line_content": line.strip(),
                    "concept": "Defensive Programming — Edge Cases",
                })

        # 3. Bare except
        if re.match(r"^\s*except\s*:\s*$", line):
            findings.append({
                "line": i,
                "type": "bare_except",
                "severity": "medium",
                "description": "Bare `except:` catches *all* exceptions, including KeyboardInterrupt",
                "detail": (
                    "A bare `except:` silently swallows every error, making debugging "
                    "very difficult. It even catches Ctrl-C (KeyboardInterrupt)."
                ),
                "fix": "Use `except Exception:` or a more specific type.",
                "line_content": line.strip(),
                "concept": "Exception Handling Best Practices",
            })

        # 4. Comparison with None using == / !=
        if re.search(r"==\s*None\b|None\s*==", stripped):
            findings.append({
                "line": i,
                "type": "none_comparison",
                "severity": "low",
                "description": "Use `is None` instead of `== None`",
                "detail": "`None` is a singleton — use identity (`is`) not equality (`==`).",
                "fix": "Replace `== None` with `is None`.",
                "line_content": line.strip(),
                "concept": "Identity vs Equality",
            })
        if re.search(r"!=\s*None\b|None\s*!=", stripped):
            findings.append({
                "line": i,
                "type": "none_comparison",
                "severity": "low",
                "description": "Use `is not None` instead of `!= None`",
                "detail": "`None` is a singleton — use identity (`is not`) not equality (`!=`).",
                "fix": "Replace `!= None` with `is not None`.",
                "line_content": line.strip(),
                "concept": "Identity vs Equality",
            })

        # 5. Using `type(x) == ...` instead of isinstance
        if re.search(r"type\(\w+\)\s*==", stripped):
            findings.append({
                "line": i,
                "type": "type_check",
                "severity": "low",
                "description": "Use `isinstance()` instead of `type() ==`",
                "detail": "`isinstance()` supports inheritance and is the Pythonic way to check types.",
                "fix": "Replace `type(x) == T` with `isinstance(x, T)`.",
                "line_content": line.strip(),
                "concept": "Polymorphism & Type Checking",
            })

    # ── AST-based patterns ──
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return findings

    for node in ast.walk(tree):
        # 6. Mutable default arguments
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            all_defaults = list(node.args.defaults) + [
                d for d in node.args.kw_defaults if d is not None
            ]
            for default in all_defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    kind = {ast.List: "list", ast.Dict: "dict", ast.Set: "set"}[type(default)]
                    findings.append({
                        "line": node.lineno,
                        "type": "mutable_default",
                        "severity": "medium",
                        "description": f"Mutable default argument ({kind}) in `{node.name}()`",
                        "detail": (
                            f"Default mutable objects are shared across calls. "
                            f"Changes persist between invocations, causing surprising results."
                        ),
                        "fix": f"Use `None` as default, then create inside: `if param is None: param = {kind}()`",
                        "line_content": "",
                        "concept": "Mutable Default Arguments",
                    })

        # 7. Return inside a for-else / while-else (common misunderstanding)
        # 8. Shadowing a built-in
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id in {"list", "dict", "set", "str", "int", "float", "type",
                           "input", "print", "range", "len", "map", "filter", "sum",
                           "min", "max", "open", "id", "hash", "next", "iter"}:
                findings.append({
                    "line": node.lineno,
                    "type": "builtin_shadow",
                    "severity": "medium",
                    "description": f"Variable `{node.id}` shadows the built-in `{node.id}()`",
                    "detail": (
                        f"Assigning to `{node.id}` hides Python's built-in function. "
                        f"Later code that tries to call `{node.id}()` will crash with a TypeError."
                    ),
                    "fix": f"Rename the variable (e.g. `{node.id}_value`, `my_{node.id}`).",
                    "line_content": "",
                    "concept": "Variable Naming & Scope",
                })

    return findings


# ── Java ────────────────────────────────────────────────────────────

def analyze_java_patterns(code: str) -> List[Dict]:
    findings: List[Dict] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.split("//")[0]

        # 1. String comparison with ==
        if re.search(r'"\w*"\s*==\s*\w+|\w+\s*==\s*"\w*"', stripped):
            findings.append({
                "line": i,
                "type": "string_comparison",
                "severity": "high",
                "description": "Comparing strings with `==` instead of `.equals()`",
                "detail": (
                    "In Java, `==` compares object references, not string content. "
                    "Two strings with identical text can be different objects."
                ),
                "fix": 'Use `.equals()`: `str1.equals(str2)` or `"literal".equals(variable)`.',
                "line_content": line.strip(),
                "concept": "Reference vs Value Equality",
            })

        # 2. Resource opened without try-with-resources
        m = re.search(
            r"new\s+(FileReader|BufferedReader|FileWriter|BufferedWriter|Scanner"
            r"|FileInputStream|FileOutputStream|PrintWriter|Socket)\s*\(",
            stripped,
        )
        if m:
            ctx = "\n".join(lines[max(0, i - 4) : i])
            if "try (" not in ctx and "try(" not in ctx:
                res = m.group(1)
                findings.append({
                    "line": i,
                    "type": "resource_leak",
                    "severity": "high",
                    "description": f"`{res}` opened without try-with-resources",
                    "detail": f"If an exception occurs, the `{res}` may never be closed, leaking resources.",
                    "fix": f"Use try-with-resources: `try ({res} r = new {res}(...)) {{ ... }}`",
                    "line_content": line.strip(),
                    "concept": "Resource Management / AutoCloseable",
                })

        # 3. Catching generic Exception
        if re.match(r"\s*catch\s*\(\s*Exception\s+\w+\s*\)", line):
            findings.append({
                "line": i,
                "type": "general_catch",
                "severity": "medium",
                "description": "Catching generic `Exception` hides specific error types",
                "detail": "Broad catches make debugging harder and can mask unrelated errors.",
                "fix": "Catch specific exceptions (e.g., `IOException`, `NullPointerException`).",
                "line_content": line.strip(),
                "concept": "Exception Specificity",
            })

        # 4. Null dereference hint: method call without null check
        m2 = re.search(r"(\w+)\.(length|size|toString|equals|get)\b", stripped)
        if m2:
            var = m2.group(1)
            if var not in ("this", "System", "Math", "Arrays", "Collections", "String", "Integer", "Objects"):
                ctx = "\n".join(lines[max(0, i - 5) : i])
                if f"{var} != null" not in ctx and f"{var} == null" not in ctx and "Optional" not in ctx:
                    # Only flag if variable was a parameter or assigned from a method return
                    pass  # Too noisy for a lightweight linter — skip

        # 5. Array access outside loop bounds (simple heuristic)
        #    Skipped — too high false-positive rate

    return findings


# ── C# ──────────────────────────────────────────────────────────────

def analyze_csharp_patterns(code: str) -> List[Dict]:
    findings: List[Dict] = []
    lines = code.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.split("//")[0]

        # 1. IDisposable without using
        m = re.search(
            r"new\s+(StreamReader|StreamWriter|FileStream|SqlConnection"
            r"|HttpClient|TcpClient|BinaryReader|BinaryWriter)\s*\(",
            stripped,
        )
        if m:
            ctx = "\n".join(lines[max(0, i - 3) : i])
            if "using" not in ctx and "using" not in stripped:
                res = m.group(1)
                findings.append({
                    "line": i,
                    "type": "resource_leak",
                    "severity": "high",
                    "description": f"`{res}` created without `using` statement",
                    "detail": f"`{res}` implements IDisposable — without `using`, the resource may leak.",
                    "fix": f"Use `using var r = new {res}(...);` or a `using` block.",
                    "line_content": line.strip(),
                    "concept": "IDisposable Pattern",
                })

        # 2. Catching generic Exception
        if re.match(r"\s*catch\s*(\(\s*Exception\s*\))?\s*$", line.rstrip()):
            findings.append({
                "line": i,
                "type": "general_catch",
                "severity": "medium",
                "description": "Catching generic `Exception` (or bare catch) hides specific errors",
                "detail": "Broad catches make debugging harder. Use specific exception types.",
                "fix": "Catch specific exceptions: `catch (ArgumentNullException ex) { ... }`",
                "line_content": line.strip(),
                "concept": "Exception Handling Specificity",
            })

        # 3. String interpolation without $ prefix
        if re.search(r'"[^"]*\{[^"]*\}"', stripped) and "$" not in stripped and "String.Format" not in stripped:
            findings.append({
                "line": i,
                "type": "missing_interpolation",
                "severity": "medium",
                "description": "String contains `{…}` but is missing `$` prefix for interpolation",
                "detail": "Without `$`, curly braces are literal text, not variable placeholders.",
                "fix": 'Add `$` before the string: `$"Hello {name}"`.',
                "line_content": line.strip(),
                "concept": "String Interpolation",
            })

    return findings


# ── Public API ──────────────────────────────────────────────────────

def analyze_code(code: str, language: str) -> List[Dict]:
    """Run language-appropriate pattern analysis and return findings
    sorted by severity (high → medium → low)."""
    lang = language.lower()
    if lang == "python":
        results = analyze_python_patterns(code)
    elif lang == "java":
        results = analyze_java_patterns(code)
    elif lang == "csharp":
        results = analyze_csharp_patterns(code)
    else:
        results = []

    severity_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda p: severity_order.get(p.get("severity", "low"), 3))
    return results
