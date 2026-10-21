import ast
import re
from typing import List, Dict


#Python

def _paren_depth(text: str) -> int:
    return text.count("(") - text.count(")")


def _while_can_terminate(loop: ast.While) -> bool:
    # True if the loop body contains anything that can change state or exit:
    # an assignment, a break (not belonging to a nested loop), return/raise,
    # or a mutating method call on a name used in the loop condition
    # (e.g. `while stack: stack.pop()`). Nested function/class bodies are ignored.
    cond_names = {n.id for n in ast.walk(loop.test) if isinstance(n, ast.Name)}
    stack = [(stmt, False) for stmt in loop.body]
    while stack:
        node, in_nested_loop = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        if isinstance(node, (ast.Return, ast.Raise)):
            return True
        if isinstance(node, ast.Break) and not in_nested_loop:
            return True
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.NamedExpr)):
            return True
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id in cond_names):
            return True
        nested = in_nested_loop or isinstance(node, (ast.For, ast.AsyncFor, ast.While))
        for child in ast.iter_child_nodes(node):
            stack.append((child, nested))
    return False


def _class_attribute_names(tree: ast.AST) -> set:
    # Names used as `self.<name>` anywhere, plus names assigned directly in a class body.
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self":
            names.add(n.attr)
        elif isinstance(n, ast.ClassDef):
            for stmt in n.body:
                targets = stmt.targets if isinstance(stmt, ast.Assign) else (
                    [stmt.target] if isinstance(stmt, ast.AnnAssign) else [])
                names.update(t.id for t in targets if isinstance(t, ast.Name))
    return names


def _function_local_names(func: ast.AST) -> set:
    # Names bound locally in a function other than via augmented assignment
    # (parameters, `x = ...`, loop targets, with-as, etc.) plus global/nonlocal names.
    aug_targets = {id(n.target) for n in ast.walk(func) if isinstance(n, ast.AugAssign)}
    names = {a.arg for a in ast.walk(func.args) if isinstance(a, ast.arg)}
    for n in ast.walk(func):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and id(n) not in aug_targets:
            names.add(n.id)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            names.update(n.names)
    return names


def analyze_python_patterns(code: str) -> List[Dict]:
    findings: List[Dict] = []
    lines = code.splitlines()

    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError):
        tree = None  # ValueError: e.g. null bytes in source
    # Checks that report syntax/indentation errors are only reported when the
    # code really fails to parse; on valid code they are false positives
    # (e.g. multi-line calls, aligned continuation lines, `elsewhere = 1`).
    parse_failed = tree is None

    #regex-based patterns 

    for i, line in enumerate(lines, 1):
        stripped = line.split("#")[0]  # ignore comments

        # 1. Swapped compound operators: =+  =-  =*  =/
        for op, correct in [("=+", "+="), ("=-", "-="), ("=*", "*="), ("=/", "/=")]:
            if op in stripped:
                # Ignore keyword arguments / defaults inside parentheses, e.g. f(step=-1)
                match = next(
                    (m for m in re.finditer(r"(\w+)\s*" + re.escape(op) + r"\s*", stripped)
                     if _paren_depth(stripped[:m.start()]) <= 0),
                    None,
                )
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
                # Check if there's already a guard or if the collection is hardcoded non-empty
                preceding = "\n".join(lines[max(0, i - 5) : i - 1])
                has_guard = (
                    f"if not {var}" in preceding
                    or f"len({var}) == 0" in preceding
                    or f"len({var}) > 0" in preceding
                    or f"if {var}" in preceding
                )
                # Check if variable is initialized with a non-empty literal
                is_hardcoded = bool(re.search(
                    rf'{var}\s*=\s*[\[\({{"\'].*[\]\)}}"\']',
                    preceding + "\n" + stripped
                ))
                if not has_guard and not is_hardcoded:
                    findings.append({
                        "line": i,
                        "type": "division_by_zero",
                        "severity": "high",
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
                "severity": "high",
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

        # 6. Mixed tabs and spaces
        if parse_failed and line and not line.isspace():
            leading = line[:len(line) - len(line.lstrip())]
            if "\t" in leading and " " in leading:
                findings.append({
                    "line": i,
                    "type": "indentation_error",
                    "severity": "high",
                    "description": "Mixed tabs and spaces in indentation",
                    "detail": (
                        "Python 3 does not allow mixing tabs and spaces for indentation. "
                        "This will cause an `IndentationError` or `TabError` at runtime."
                    ),
                    "fix": "Use only spaces (4 per level is the standard). Configure your editor to convert tabs to spaces.",
                    "line_content": line.rstrip(),
                    "concept": "Python Indentation Rules",
                })

    # 7. Inconsistent indentation levels
    indent_sizes = set()
    for line in lines:
        if line.strip() and not line.lstrip().startswith("#"):
            leading = line[:len(line) - len(line.lstrip())]
            if leading and "\t" not in leading:
                indent_sizes.add(len(leading))
    # Check for odd indentation (e.g., 3 spaces mixed with 4 spaces)
    if parse_failed and indent_sizes:
        diffs = sorted(indent_sizes)
        # Find the smallest non-zero indent
        base_indents = [d for d in diffs if d > 0]
        if base_indents:
            base = base_indents[0]
            for size in base_indents:
                if size % base != 0 and base % size != 0:
                    findings.append({
                        "line": 1,
                        "type": "indentation_error",
                        "severity": "high",
                        "description": f"Inconsistent indentation: found {size}-space and {base}-space indents",
                        "detail": (
                            "Python requires consistent indentation throughout a block. "
                            "Mixing different indent sizes (e.g., 3 spaces and 4 spaces) "
                            "causes `IndentationError` or unexpected behavior."
                        ),
                        "fix": "Use exactly 4 spaces per indent level throughout your code.",
                        "line_content": "",
                        "concept": "Python Indentation Rules",
                    })
                    break

    # 8. Missing indentation after block statement (if/for/while/def/class/else/elif/try/except/finally/with)
    for i, line in enumerate(lines if parse_failed else []):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Check if this line starts a block (ends with ':')
        if re.match(r"^\s*(if |elif |else\s*:|for |while |def |class |try\s*:|except|finally\s*:|with )", line) and stripped.endswith(":"):
            # Get the indentation of this line
            current_indent = len(line) - len(line.lstrip())
            # Check the next non-empty line
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                next_stripped = next_line.strip()
                if not next_stripped or next_stripped.startswith("#"):
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= current_indent:
                    findings.append({
                        "line": j + 1,
                        "type": "indentation_error",
                        "severity": "high",
                        "description": f"Expected indented block after `{stripped}` on line {i + 1}",
                        "detail": (
                            f"The line after `{stripped}` should be indented (typically by 4 spaces). "
                            f"Without proper indentation, Python will raise an `IndentationError`."
                        ),
                        "fix": f"Indent line {j + 1} by adding 4 spaces at the beginning.",
                        "line_content": next_stripped,
                        "concept": "Python Indentation Rules",
                    })
                break

    #AST-based patterns
    class_attrs = _class_attribute_names(tree) if tree else set()

    for node in ast.walk(tree) if tree else []:
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
                        "severity": "high",
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
                    "severity": "low",
                    "description": f"Variable `{node.id}` shadows the built-in `{node.id}()`",
                    "detail": (
                        f"Assigning to `{node.id}` hides Python's built-in function. "
                        f"Later code that tries to call `{node.id}()` will crash with a TypeError."
                    ),
                    "fix": f"Rename the variable (e.g. `{node.id}_value`, `my_{node.id}`).",
                    "line_content": "",
                    "concept": "Variable Naming & Scope",
                })

        # 9. While loop without increment (potential infinite loop)
        if isinstance(node, ast.While):
            # Flag only when nothing in the body can change state or leave the
            # loop (conditional `break`/`return` and nested updates count).
            if not _while_can_terminate(node):
                findings.append({
                    "line": node.lineno,
                    "type": "infinite_loop",
                    "severity": "high",
                    "description": "`while` loop may run forever — no increment or break found",
                    "detail": (
                        "This `while` loop does not appear to modify its loop variable "
                        "or contain a `break` statement, which could cause an infinite loop."
                    ),
                    "fix": "Add an increment (e.g., `i += 1`) or a `break`/`return` inside the loop body.",
                    "line_content": "",
                    "concept": "Loop Termination",
                })

        # 10. Missing self in class method (using instance var without self)
        if isinstance(node, ast.FunctionDef) and node.args.args:
            first_arg = node.args.args[0].arg if node.args.args else None
            if first_arg == "self":
                # Look for AugAssign targets that are bare Names (not self.x)
                local_names = _function_local_names(node)
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign):
                        if isinstance(child.target, ast.Name):
                            var_name = child.target.id
                            # Only flag when the name is an instance/class attribute
                            # and is NOT a local variable of this method (local
                            # accumulators like `total += x` are fine).
                            if var_name not in class_attrs or var_name in local_names:
                                continue
                            findings.append({
                                "line": child.lineno,
                                "type": "missing_self",
                                "severity": "high",
                                "description": f"`{var_name}` may need `self.{var_name}` to modify the instance attribute",
                                "detail": (
                                    f"Inside a class method, `{var_name} += 1` modifies a local variable, "
                                    f"not the instance attribute. Use `self.{var_name} += 1` instead."
                                ),
                                "fix": f"Change `{var_name}` to `self.{var_name}`.",
                                "line_content": "",
                                "concept": "Instance Attributes vs Local Variables",
                            })

        # 11. Off-by-one: range(1, n) misses n (common in prime/factorial checks)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'range':
            if len(node.args) == 2:
                # Check if range(2, n) where n should be n+1 for prime check
                pass  # Too many false positives

        # 12. Factorial initialized to 0 (result *= i with result=0 always gives 0)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'result':
                    if isinstance(node.value, ast.Constant) and node.value.value == 0:
                        # Check if result is used in multiplication later
                        for sibling in ast.walk(tree):
                            if isinstance(sibling, ast.AugAssign) and isinstance(sibling.op, ast.Mult):
                                if isinstance(sibling.target, ast.Name) and sibling.target.id == 'result':
                                    findings.append({
                                        "line": node.lineno,
                                        "type": "zero_init_multiply",
                                        "severity": "high",
                                        "description": "`result = 0` then `result *= ...` always gives 0",
                                        "detail": "Multiplying by 0 always stays 0. For factorial or product calculations, initialize to 1.",
                                        "fix": "Change `result = 0` to `result = 1`.",
                                        "line_content": "",
                                        "concept": "Multiplicative Identity",
                                    })
                                    break

    # 13-16. Regex patterns (run even on SyntaxError code)
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 13. String method without assignment
        if re.match(r'\w+\.(upper|lower|replace|strip|lstrip|rstrip|title|capitalize|swapcase)\(', stripped):
            if '=' not in line.split('#')[0] and 'print' not in line:
                findings.append({
                    "line": i,
                    "type": "immutable_string",
                    "severity": "high",
                    "description": "String method called but result is not assigned",
                    "detail": "Strings are immutable in Python. `.upper()`, `.replace()`, etc. return a NEW string — the original is unchanged.",
                    "fix": "Assign the result: `text = text.upper()`",
                    "line_content": stripped,
                    "concept": "String Immutability",
                })

        # 14. Assignment in condition (if x = 0:)
        if parse_failed and re.match(r'^\s*(if|while|elif)\s+[^=]+=\s*[^=:]+\s*:', line) and '==' not in line and '!=' not in line and '<=' not in line and '>=' not in line and ':=' not in line:
            findings.append({
                "line": i,
                "type": "assignment_in_condition",
                "severity": "high",
                "description": "Used `=` instead of `==` in condition",
                "detail": "In Python, `=` is assignment and `==` is comparison. Using `=` inside `if` is a SyntaxError.",
                "fix": "Change `=` to `==`.",
                "line_content": stripped,
                "concept": "Assignment vs Equality",
            })

        # 15. list.sort() assignment (returns None)
        if re.match(r'^\s*\w+\s*=\s*\w+\.sort\(\)', line):
            findings.append({
                "line": i,
                "type": "sort_assignment",
                "severity": "high",
                "description": "Assigning `.sort()` to a variable gives `None`",
                "detail": "`.sort()` sorts in-place and returns `None`. Use `sorted()` to get a new sorted list.",
                "fix": "Use `sorted_list = sorted(my_list)` or just `my_list.sort()`.",
                "line_content": stripped,
                "concept": "In-place Sort vs sorted()",
            })

        # 16. Python 2 print statement
        if parse_failed and re.match(r'^\s*print\s+["\']', line):
            findings.append({
                "line": i,
                "type": "python2_print",
                "severity": "high",
                "description": "Python 2 `print` statement — needs parentheses in Python 3",
                "detail": "In Python 3, `print` is a function: `print(...)`. Without parentheses it raises a SyntaxError.",
                "fix": "Add parentheses: `print(\"Hello\")`.",
                "line_content": stripped,
                "concept": "Python 2 vs 3 Syntax",
            })

        # 17. Missing colon after def/for/while/if/elif/else/class/with/try/except
        if parse_failed and re.match(r'^\s*(def |for |while |if |elif |else\b|class |with |try\b|except\b)', line):
            s = stripped.rstrip()
            if s and not s.endswith(':') and not s.endswith('\\') and not s.startswith('#'):
                # Check it's a complete statement (not multi-line)
                if '(' not in s or s.count('(') == s.count(')'):
                    findings.append({
                        "line": i,
                        "type": "missing_colon",
                        "severity": "high",
                        "description": f"Missing `:` at end of `{s.split()[0]}` statement",
                        "detail": "Python requires a colon `:` at the end of `def`, `for`, `while`, `if`, `elif`, `else`, `class`, and `try` statements.",
                        "fix": f"Add `:` at the end: `{s}:`",
                        "line_content": stripped,
                        "concept": "Python Block Syntax",
                    })

        # 18. Unmatched parentheses on a single line
        if parse_failed and stripped.count('(') != stripped.count(')') and not stripped.endswith('\\'):
            findings.append({
                "line": i,
                "type": "unmatched_parens",
                "severity": "high",
                "description": "Unmatched parentheses",
                "detail": "This line has a different number of `(` and `)`. This causes a SyntaxError.",
                "fix": "Check for missing or extra parentheses.",
                "line_content": stripped,
                "concept": "Balanced Delimiters",
            })

        # 19. Common typos: pritn, pirnt, esle, eles, retrun, reutrn
        typo_map = {
            r'\bpritn\b': ('pritn', 'print'),
            r'\bpirnt\b': ('pirnt', 'print'),
            r'\besle\b': ('esle', 'else'),
            r'\beles\b': ('eles', 'else'),
            r'\bretrun\b': ('retrun', 'return'),
            r'\breutrn\b': ('reutrn', 'return'),
            r'\bflase\b': ('flase', 'False'),
            r'\btreu\b': ('treu', 'True'),
            r'\bimprot\b': ('improt', 'import'),
        }
        for pattern, (typo, correct) in typo_map.items():
            if re.search(pattern, stripped):
                findings.append({
                    "line": i,
                    "type": "typo",
                    "severity": "high",
                    "description": f"Typo: `{typo}` should be `{correct}`",
                    "detail": f"`{typo}` is not a valid Python keyword or built-in. Did you mean `{correct}`?",
                    "fix": f"Change `{typo}` to `{correct}`.",
                    "line_content": stripped,
                    "concept": "Spelling / Typos",
                })

        # 20. Iterating dict without .items() for key-value unpacking
        m_dict = re.match(r'^\s*for\s+(\w+)\s*,\s*(\w+)\s+in\s+(\w+)\s*:', line)
        if m_dict:
            dict_name = m_dict.group(3)
            if '.items()' not in stripped and '.values()' not in stripped:
                # Check if the variable is assigned as a dict (not a list of tuples)
                is_likely_dict = False
                for prev_line in lines[:i-1]:
                    prev_s = prev_line.strip()
                    if re.match(rf'{dict_name}\s*=\s*\{{', prev_s):
                        is_likely_dict = True
                        break
                if is_likely_dict:
                    findings.append({
                        "line": i,
                        "type": "dict_iteration",
                        "severity": "high",
                        "description": f"Unpacking key/value from `{dict_name}` requires `.items()`",
                        "detail": f"Iterating a dict directly (`for k, v in d:`) only gives keys, not key-value pairs. Use `.items()` to get both.",
                        "fix": f"Change to `for {m_dict.group(1)}, {m_dict.group(2)} in {dict_name}.items():`",
                        "line_content": stripped,
                        "concept": "Dictionary Iteration",
                    })

    return findings


# Java

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
        if re.match(r"\s*\}?\s*catch\s*\(\s*Exception\s+\w+\s*\)", line):
            findings.append({
                "line": i,
                "type": "general_catch",
                "severity": "high",
                "description": "Catching generic `Exception` hides specific error types",
                "detail": "Broad catches make debugging harder and can mask unrelated errors.",
                "fix": "Catch specific exceptions (e.g., `IOException`, `NullPointerException`).",
                "line_content": line.strip(),
                "concept": "Exception Specificity",
            })

        # 4. Array index out of bounds risk
        m2 = re.search(r"(\w+)\[(\w+)\s*[\+\-]\s*1\]", stripped)
        if m2:
            findings.append({
                "line": i,
                "type": "index_out_of_bounds",
                "severity": "high",
                "description": f"Potential array index out of bounds: `{m2.group(0)}`",
                "detail": "Accessing array indices with `+1` or `-1` offsets is a common source of `ArrayIndexOutOfBoundsException`.",
                "fix": "Add bounds checking: `if (index >= 0 && index < array.length)`.",
                "line_content": line.strip(),
                "concept": "Array Bounds Checking",
            })

        # 5. Comparing wrapper objects with ==
        if re.search(r"(\w+)\s*==\s*(\w+)", stripped) and "null" not in stripped:
            if any(kw in stripped for kw in ["Integer", "Boolean", "Long", "Double", "Float"]):
                findings.append({
                    "line": i,
                    "type": "wrapper_comparison",
                    "severity": "high",
                    "description": "Comparing wrapper objects with `==` instead of `.equals()`",
                    "detail": "Wrapper types (Integer, Boolean, etc.) are objects. `==` compares references, not values.",
                    "fix": "Use `.equals()` for wrapper type comparisons: `a.equals(b)`.",
                    "line_content": line.strip(),
                    "concept": "Autoboxing & Reference Equality",
                })

        # 6. Missing break in switch case
        if re.match(r"\s*case\s+.+:", line):
            for j in range(i, min(i + 10, len(lines))):
                next_line = lines[j].strip()
                if "break;" in next_line or "return" in next_line or "throw" in next_line:
                    break
                if re.match(r"case\s+.+:", next_line) or next_line == "default:":
                    findings.append({
                        "line": i,
                        "type": "missing_break",
                        "severity": "high",
                        "description": "Missing `break` in switch — will fall through to next case",
                        "detail": "Without `break`, execution continues into the next `case` block (fall-through).",
                        "fix": "Add `break;` at the end of each case block.",
                        "line_content": line.strip(),
                        "concept": "Switch Fall-Through",
                    })
                    break

        # 7. While loop without increment
        # (skip the `while (...);` tail of a do-while loop)
        if re.match(r"\s*while\s*\(", line) and not stripped.rstrip().endswith(";") and "while(true)" not in stripped.replace(" ", "") and "while (true)" not in stripped:
            has_modifier = False
            for j in range(i, min(i + 15, len(lines))):
                check = lines[j].strip()
                if "++" in check or "--" in check or "+=" in check or "-=" in check:
                    has_modifier = True
                    break
                if "break;" in check or "return" in check:
                    has_modifier = True
                    break
                if check == "}":
                    break
            if not has_modifier:
                findings.append({
                    "line": i,
                    "type": "infinite_loop",
                    "severity": "high",
                    "description": "`while` loop may run forever — no increment or break found",
                    "detail": "This loop doesn't appear to modify its loop variable or contain a break.",
                    "fix": "Add an increment (e.g., `i++`) or a `break` statement inside the loop.",
                    "line_content": line.strip(),
                    "concept": "Loop Termination",
                })

        # 8. Integer division truncation
        if re.search(r"\b(int|long)\s+\w+\s*=.*\w+\s*/\s*\w+", stripped):
            if "double" not in stripped and "float" not in stripped and "(double)" not in stripped:
                findings.append({
                    "line": i,
                    "type": "integer_division",
                    "severity": "medium",
                    "description": "Integer division may truncate the result",
                    "detail": "Dividing two integers in Java discards the decimal. `5 / 2` gives `2`, not `2.5`.",
                    "fix": "Cast one operand to `double`: `(double) a / b`.",
                    "line_content": line.strip(),
                    "concept": "Integer vs Floating-Point Division",
                })

        # 9. Missing braces after if/for/while
        if re.match(r"\s*(if|for|while)\s*\(.*\)\s*$", line.rstrip()):
            if i < len(lines):
                next_line = lines[i].strip() if i < len(lines) else ""
                if next_line and not next_line.startswith("{") and not next_line.startswith("//"):
                    findings.append({
                        "line": i,
                        "type": "missing_braces",
                        "severity": "medium",
                        "description": "Missing braces `{}` after control statement",
                        "detail": "Without braces, only the next line is part of the body. This is error-prone when adding more lines later.",
                        "fix": "Always use braces: `if (condition) { ... }`",
                        "line_content": line.strip(),
                        "concept": "Code Block Scoping",
                    })

        # 10. Off-by-one: <= .length() or <= .size() (should be <)
        if re.search(r'\w+\s*<=\s*\w+\.(length|size)\(\)', stripped) or re.search(r'\w+\s*<=\s*\w+\.length\b', stripped):
            findings.append({
                "line": i,
                "type": "off_by_one",
                "severity": "high",
                "description": "Off-by-one: `<=` with `.length` causes `ArrayIndexOutOfBoundsException`",
                "detail": "Array/string indices go from 0 to length-1. Using `<=` accesses one element past the end.",
                "fix": "Change `<=` to `<`: `i < array.length`",
                "line_content": line.strip(),
                "concept": "Array Bounds / Off-By-One",
            })

        # 11. Lowercase class name (system.out instead of System.out)
        if re.search(r'\bsystem\.out\.print', stripped):
            findings.append({
                "line": i,
                "type": "wrong_case",
                "severity": "high",
                "description": "`system` should be `System` (Java is case-sensitive)",
                "detail": "Java class names start with uppercase. `system.out.println()` won't compile.",
                "fix": "Change `system` to `System`.",
                "line_content": line.strip(),
                "concept": "Case Sensitivity in Java",
            })

        # 12. String variable == variable (not just literal)
        m3 = re.search(r'(\w+)\s*==\s*(\w+)', stripped)
        if m3 and 'null' not in stripped and '"' not in stripped:
            v1, v2 = m3.group(1), m3.group(2)
            if v1[0].islower() and v2[0].islower() and v1 not in ('true','false','this') and v2 not in ('true','false','this','null'):
                # Only flag when one side is actually declared as a String
                # (previously any nearby `String[] args` triggered a false positive
                # on int comparisons).
                if any(re.search(rf'\bString\s+{re.escape(v)}\b', code) for v in (v1, v2)):
                    findings.append({
                        "line": i,
                        "type": "string_comparison",
                        "severity": "high",
                        "description": f"Comparing `{v1}` and `{v2}` with `==` — use `.equals()` for strings",
                        "detail": "In Java, `==` compares references, not content. Two different String objects with same text are NOT `==`.",
                        "fix": f"Use `{v1}.equals({v2})` instead.",
                        "line_content": line.strip(),
                        "concept": "Reference vs Value Equality",
                    })

        # 13. Immutable string method without assignment
        if re.match(r'\s+\w+\.(toUpperCase|toLowerCase|trim|replace|substring|concat)\(', line):
            if '=' not in stripped and 'System' not in stripped and 'return' not in stripped:
                findings.append({
                    "line": i,
                    "type": "immutable_string",
                    "severity": "high",
                    "description": "String method called but result not assigned — strings are immutable in Java",
                    "detail": "`.toUpperCase()`, `.replace()`, etc. return a NEW string. The original is NOT modified.",
                    "fix": "Assign the result: `text = text.toUpperCase();`",
                    "line_content": line.strip(),
                    "concept": "String Immutability",
                })

        # 14. Factorial/product initialized to 0
        if re.search(r'\b(int|long)\s+result\s*=\s*0\s*;', stripped):
            ctx_after = '\n'.join(lines[i:min(i+10, len(lines))])
            if 'result *=' in ctx_after or 'result = result *' in ctx_after:
                findings.append({
                    "line": i,
                    "type": "zero_init_multiply",
                    "severity": "high",
                    "description": "`result = 0` then `result *= ...` always gives 0",
                    "detail": "Multiplying by 0 always stays 0. For factorial/product, initialize to 1.",
                    "fix": "Change `int result = 0` to `int result = 1`.",
                    "line_content": line.strip(),
                    "concept": "Multiplicative Identity",
                })

        # 15. .split() without argument in Java (requires regex)
        if re.search(r'\w+\.split\(\)', stripped):
            findings.append({
                "line": i,
                "type": "missing_argument",
                "severity": "high",
                "description": "`.split()` requires a regex argument in Java",
                "detail": "Unlike Python, Java's `.split()` needs a regex string. `.split()` without args won't compile.",
                "fix": 'Use `.split(" ")` or `.split("\\\\s+")` to split by whitespace.',
                "line_content": line.strip(),
                "concept": "Java String.split() vs Python str.split()",
            })

        # 16. Missing semicolon (line ends with quote or identifier, no ;)
        if stripped and not stripped.endswith(';') and not stripped.endswith('{') and not stripped.endswith('}') and not stripped.endswith('//') and not stripped.startswith('//'):
            if re.search(r'["\w]\s*$', stripped) and not re.match(r'\s*(public|private|protected|class|import|package|if|else|for|while|try|catch|finally|switch|case|default|return|break|continue)', stripped.strip()):
                # Check if it looks like a statement (has = or method call)
                if '=' in stripped or re.search(r'\w+\(', stripped):
                    findings.append({
                        "line": i,
                        "type": "missing_semicolon",
                        "severity": "high",
                        "description": "Missing semicolon `;` at end of statement",
                        "detail": "Java requires a semicolon at the end of every statement.",
                        "fix": "Add `;` at the end of this line.",
                        "line_content": line.strip(),
                        "concept": "Java Statement Termination",
                    })

        # 17. Off-by-one: i <= num in prime check (should be < num)
        m_prime = re.search(r'for\s*\(\s*int\s+\w+\s*=\s*2\s*;\s*\w+\s*<=\s*(\w+)\s*;', stripped)
        if m_prime:
            var = m_prime.group(1)
            ctx_after = '\n'.join(lines[i-1:min(i+5, len(lines))])
            if '% ' + var in ctx_after or '%' + var in ctx_after:
                findings.append({
                    "line": i,
                    "type": "prime_check_off_by_one",
                    "severity": "high",
                    "description": f"Prime check uses `<= {var}` — should be `< {var}`",
                    "detail": f"When checking if `{var}` is prime, the loop should go up to `{var}-1` (use `< {var}`). Using `<=` means `{var} % {var} == 0` is always true, so every number appears non-prime.",
                    "fix": f"Change `<= {var}` to `< {var}`.",
                    "line_content": line.strip(),
                    "concept": "Prime Number Algorithm",
                })

    return findings


# C#

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
        if re.match(r"\s*\}?\s*catch\s*(\(\s*Exception\s*(\w+)?\s*\))?\s*\{?\s*$", line.rstrip()):
            findings.append({
                "line": i,
                "type": "general_catch",
                "severity": "high",
                "description": "Catching generic `Exception` (or bare catch) hides specific errors",
                "detail": "Broad catches make debugging harder. Use specific exception types.",
                "fix": "Catch specific exceptions: `catch (ArgumentNullException ex) { ... }`",
                "line_content": line.strip(),
                "concept": "Exception Handling Specificity",
            })

        # 3. String interpolation without $ prefix
        # Placeholder must start with an identifier: `{0}` / `{1:N2}` are valid
        # composite-format items (Console.WriteLine("{0}", x), string.Format).
        if re.search(r'"[^"]*\{[A-Za-z_][^"]*\}"', stripped) and "$" not in stripped and "String.Format" not in stripped and "{{" not in stripped:
            findings.append({
                "line": i,
                "type": "missing_interpolation",
                "severity": "high",
                "description": "String contains `{…}` but is missing `$` prefix for interpolation",
                "detail": "Without `$`, curly braces are literal text, not variable placeholders.",
                "fix": 'Add `$` before the string: `$"Hello {name}"`.',
                "line_content": line.strip(),
                "concept": "String Interpolation",
            })

        # 4. async void methods
        if re.search(r"\basync\s+void\s+\w+", stripped):
            if "Main" not in stripped and "EventHandler" not in stripped:
                findings.append({
                    "line": i,
                    "type": "async_void",
                    "severity": "high",
                    "description": "`async void` method — exceptions will crash the application",
                    "detail": "`async void` methods cannot be awaited and their exceptions cannot be caught.",
                    "fix": "Change `async void` to `async Task` and await the method.",
                    "line_content": line.strip(),
                    "concept": "Async/Await Best Practices",
                })

        # 5. Missing break in switch case
        if re.match(r"\s*case\s+.+:", line):
            for j in range(i, min(i + 10, len(lines))):
                next_line = lines[j].strip()
                if "break;" in next_line or "return" in next_line or "throw" in next_line or "goto" in next_line:
                    break
                if re.match(r"case\s+.+:", next_line) or next_line == "default:":
                    findings.append({
                        "line": i,
                        "type": "missing_break",
                        "severity": "high",
                        "description": "Missing `break` in switch case — compilation error in C#",
                        "detail": "C# does not allow fall-through. Each case must end with `break`, `return`, or `goto`.",
                        "fix": "Add `break;` at the end of the case block.",
                        "line_content": line.strip(),
                        "concept": "Switch Statement Rules",
                    })
                    break

        # 6. Potential null dereference
        m2 = re.search(r"(\w+)\.(Length|Count|ToString|Equals|Contains|IndexOf|Substring)\b", stripped)
        if m2:
            var = m2.group(1)
            if var not in ("this", "Console", "Math", "string", "String", "Convert", "Environment", "int", "double", "DateTime"):
                ctx = "\n".join(lines[max(0, i - 5) : i])
                if f"{var} != null" not in ctx and f"{var} == null" not in ctx and f"{var}?" not in ctx and "?." not in stripped:
                    # Skip if variable is locally initialized (new, literal, or method return)
                    is_initialized = bool(re.search(
                        rf'{var}\s*=\s*(new\s|"|\{{|\[|["\d]|.*\.\w+\()',
                        ctx + "\n" + stripped
                    ))
                    if not is_initialized:
                        findings.append({
                            "line": i,
                            "type": "null_dereference",
                            "severity": "medium",
                            "description": f"`{var}` may be null when `.{m2.group(2)}` is called",
                            "detail": f"If `{var}` is null, calling `.{m2.group(2)}` throws `NullReferenceException`.",
                            "fix": f"Use null-conditional: `{var}?.{m2.group(2)}` or add a null check.",
                            "line_content": line.strip(),
                            "concept": "Null Safety",
                        })

        # 7. While loop without increment
        # (skip the `while (...);` tail of a do-while loop)
        if re.match(r"\s*while\s*\(", line) and not stripped.rstrip().endswith(";") and "while(true)" not in stripped.replace(" ", "") and "while (true)" not in stripped:
            has_modifier = False
            for j in range(i, min(i + 15, len(lines))):
                check = lines[j].strip()
                if "++" in check or "--" in check or "+=" in check or "-=" in check:
                    has_modifier = True
                    break
                if "break;" in check or "return" in check:
                    has_modifier = True
                    break
                if check == "}":
                    break
            if not has_modifier:
                findings.append({
                    "line": i,
                    "type": "infinite_loop",
                    "severity": "high",
                    "description": "`while` loop may run forever — no increment or break found",
                    "detail": "This loop doesn't appear to modify its loop variable or contain a break.",
                    "fix": "Add an increment (e.g., `i++`) or a `break` statement inside the loop.",
                    "line_content": line.strip(),
                    "concept": "Loop Termination",
                })

        # 8. String comparison with ==
        if re.search(r'"\w*"\s*==\s*\w+|\w+\s*==\s*"\w*"', stripped):
            pass  # In C# == works for strings but already noted above

        # 9. Missing braces after if/for/while
        if re.match(r"\s*(if|for|while|foreach)\s*\(.*\)\s*$", line.rstrip()):
            if i < len(lines):
                next_line = lines[i].strip() if i < len(lines) else ""
                if next_line and not next_line.startswith("{") and not next_line.startswith("//"):
                    findings.append({
                        "line": i,
                        "type": "missing_braces",
                        "severity": "medium",
                        "description": "Missing braces `{}` after control statement",
                        "detail": "Without braces, only the next line is part of the body. This is error-prone.",
                        "fix": "Always use braces: `if (condition) { ... }`",
                        "line_content": line.strip(),
                        "concept": "Code Block Scoping",
                    })

        # 10. Off-by-one: <= .Length or <= .Count (should be <)
        if re.search(r'\w+\s*<=\s*\w+\.(Length|Count)\b', stripped):
            findings.append({
                "line": i,
                "type": "off_by_one",
                "severity": "high",
                "description": "Off-by-one: `<=` with `.Length` causes `IndexOutOfRangeException`",
                "detail": "Array indices go from 0 to Length-1. Using `<=` goes past the end.",
                "fix": "Change `<=` to `<`: `i < array.Length`",
                "line_content": line.strip(),
                "concept": "Array Bounds / Off-By-One",
            })

        # 11. Immutable string method without assignment
        if re.match(r'\s+\w+\.(ToUpper|ToLower|Trim|Replace|Substring)\(', line):
            if '=' not in stripped and 'Console' not in stripped and 'return' not in stripped:
                findings.append({
                    "line": i,
                    "type": "immutable_string",
                    "severity": "high",
                    "description": "String method called but result not assigned — strings are immutable in C#",
                    "detail": "`.ToUpper()`, `.Replace()`, etc. return a NEW string. The original is NOT modified.",
                    "fix": "Assign the result: `text = text.ToUpper();`",
                    "line_content": line.strip(),
                    "concept": "String Immutability",
                })

        # 12. Factorial/product initialized to 0
        if re.search(r'\b(int|long)\s+result\s*=\s*0\s*;', stripped):
            ctx_after = '\n'.join(lines[i:min(i+10, len(lines))])
            if 'result *=' in ctx_after or 'result = result *' in ctx_after:
                findings.append({
                    "line": i,
                    "type": "zero_init_multiply",
                    "severity": "high",
                    "description": "`result = 0` then `result *= ...` always gives 0",
                    "detail": "Multiplying by 0 always stays 0. For factorial/product, initialize to 1.",
                    "fix": "Change `int result = 0` to `int result = 1`.",
                    "line_content": line.strip(),
                    "concept": "Multiplicative Identity",
                })

        # 13. Wrong method case: Writeline vs WriteLine
        if re.search(r'Console\.Writeline\b', stripped):
            findings.append({
                "line": i,
                "type": "wrong_case",
                "severity": "high",
                "description": "`Console.Writeline` should be `Console.WriteLine` (capital L)",
                "detail": "C# is case-sensitive. `Writeline` is not a valid method — it's `WriteLine`.",
                "fix": "Change `Writeline` to `WriteLine`.",
                "line_content": line.strip(),
                "concept": "Case Sensitivity in C#",
            })

        # 14. Assignment in condition: if (x = y) instead of ==
        m_assign = re.search(r'if\s*\(\s*(\w+)\s*=\s*(\w+)\s*\)', stripped)
        if m_assign and '==' not in stripped and '!=' not in stripped:
            findings.append({
                "line": i,
                "type": "assignment_in_condition",
                "severity": "high",
                "description": f"Used `=` instead of `==` in `if` condition",
                "detail": "In C#, `=` is assignment and `==` is comparison. Using `=` inside `if()` assigns instead of comparing.",
                "fix": "Change `=` to `==`.",
                "line_content": line.strip(),
                "concept": "Assignment vs Equality",
            })

        # 15. Comparing char to string: c == "a" instead of c == 'a'
        if re.search(r"\bchar\b", '\n'.join(lines[max(0,i-5):i])):
            if re.search(r'==\s*"[a-zA-Z]"', stripped):
                findings.append({
                    "line": i,
                    "type": "char_vs_string",
                    "severity": "high",
                    "description": "Comparing `char` to a `string` — use single quotes for char",
                    "detail": 'In C#, `char` values use single quotes (`\'a\'`), not double quotes (`"a"`). Using double quotes creates a `string`, which cannot be compared to a `char` with `==`.',
                    "fix": 'Change `"a"` to `\'a\'`.',
                    "line_content": line.strip(),
                    "concept": "Char vs String Types",
                })

        # 16. Prime check off-by-one: i <= num
        m_prime = re.search(r'for\s*\(\s*int\s+\w+\s*=\s*2\s*;\s*\w+\s*<=\s*(\w+)\s*;', stripped)
        if m_prime:
            var = m_prime.group(1)
            ctx_after = '\n'.join(lines[i-1:min(i+5, len(lines))])
            if '% ' + var in ctx_after or '%' + var in ctx_after:
                findings.append({
                    "line": i,
                    "type": "prime_check_off_by_one",
                    "severity": "high",
                    "description": f"Prime check uses `<= {var}` — should be `< {var}`",
                    "detail": f"`{var} % {var}` is always 0, making every number appear non-prime.",
                    "fix": f"Change `<= {var}` to `< {var}`.",
                    "line_content": line.strip(),
                    "concept": "Prime Number Algorithm",
                })

    return findings


# Public API

def analyze_code(code: str, language: str) -> List[Dict]:
    lang = (language or "").lower()
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

