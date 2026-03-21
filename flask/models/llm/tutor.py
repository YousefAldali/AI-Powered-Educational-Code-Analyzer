import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

#GPU detection
try:
    import torch
    _GPU_AVAILABLE = torch.cuda.is_available()
except ImportError:
    _GPU_AVAILABLE = False

#Lazy-loaded model state
_model = None
_tokenizer = None

MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
MAX_NEW_TOKENS = 360
MAX_INPUT_TOKENS = 4096


def _load_model():
    #Load Qwen once
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

    logger.info("[LLM Tutor] Loading Qwen2.5-Coder-7B-Instruct (4-bit)…")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
    )
    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    _model.eval()

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    logger.info("[LLM Tutor] Model loaded successfully.")
    return _model, _tokenizer


def _build_prompt(code: str, language: str, static_issues: list, codebert_label: str, flagged_functions: list = None) -> str:
    issues_text = "\n".join(f"- {i}" for i in static_issues) if static_issues else "None detected."
    
    if flagged_functions:
        worst_func = max(flagged_functions, key=lambda f: f.get("confidence", 0))
        code_view = f"// Flagged chunk: {worst_func['name']}\n{worst_func['code']}"
    else:
        code_view = code[:3000]

    return f"""You are a precise first-year programming tutor.

INSTRUCTIONS:
1) Explain the bug and how to fix it based ONLY on the provided code.
2) Do NOT invent identifiers or examples not present in the code.
3) Static analysis issues below are hints only do not mention issues that are not visible in the code.
4) Write in a student-friendly, encouraging tone.
5) Output exactly 5 numbered sections below.

Language: {language.upper()}
CodeBERT Prediction: {codebert_label.upper()}
Static Analysis Issues (hints only):
{issues_text}

[CODE]
{code_view}

RESPONSE FORMAT:

1) Goal (1 sentence):
- ...

2) The Bug (Tutor Style):
- Symptom: ...
- Cause: ...
- Common beginner misconception: ...
- Concept name: ...

3) The Fix:
- What to change: ...
- Why this fixes it: ...

4) Mini-Lesson:
- Rule of thumb: ...
- Tiny example (ONE line): ...

5) Quick Check:
- One conceptual question: ...
"""


def _call_model(tokenizer, model, prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful and precise programming tutor."},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_INPUT_TOKENS,
    ).to(model.device)

    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            repetition_penalty=1.05,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True,
        )

    gen_tokens = out[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()


def _format_as_markdown(raw: str) -> str:
    #Convert output to clean Markdown and enforce exactly 5 sections.
    text = raw.strip()

    # Normalize section headers: accept "1)", "1.", "1 -" formats
    text = re.sub(r"(?m)^(\d)\s*[\)\.\-]\s*", r"\1) ", text)

    # Bold numbered headers
    text = re.sub(r"(?m)^([1-5]\))", r"**\1**", text)

    # Truncate anything after section 5 (remove any extra "6)" or beyond)
    parts = re.split(r"(?m)^\s*6\)\s", text)
    text = parts[0].strip()

    return text


def _placeholder_explanation(code: str, language: str, codebert_label: str, static_issues: list, flagged_functions: list = None) -> str:
    """Dynamic fallback: uses lightweight pattern analysis + CodeBERT/static
    results to build a *specific*, actionable explanation without a GPU."""
    from models.llm.code_patterns import analyze_code

    cb_label = codebert_label.lower()
    is_buggy = cb_label == "buggy"
    is_uncertain = cb_label == "uncertain"
    has_static = bool(static_issues)

    # ── Run pattern analysis on the user's code ──
    patterns = analyze_code(code, language)

    # Also analyse individual flagged functions (may catch patterns the
    # whole-file scan missed because of duplicate line numbers, etc.)
    if flagged_functions:
        seen = {(p["line"], p["type"]) for p in patterns}
        for func in flagged_functions:
            for p in analyze_code(func.get("code", ""), language):
                key = (p["line"], p["type"])
                if key not in seen:
                    p["function"] = func["name"]
                    patterns.append(p)
                    seen.add(key)

    has_patterns = bool(patterns)

    # ── 1) Goal ──
    parts = []
    if has_patterns:
        parts.append(f"Pattern analysis found **{len(patterns)} likely issue(s)**")
    if has_static:
        parts.append(f"static analysis flagged **{len(static_issues)} security issue(s)**")
    if is_buggy and not has_patterns and not has_static:
        parts.append("CodeBERT detected potential logical issues")
    if is_uncertain and not has_patterns and not has_static:
        parts.append("CodeBERT is uncertain about this code")

    if parts:
        goal = " and ".join(parts) + " in your code."
    else:
        goal = "Your code looks good — no issues detected!"

    # ── 2) The Bug ──
    if has_patterns:
        main = patterns[0]
        symptom = (
            f"**Line {main['line']}:** `{main['line_content']}`"
            if main.get("line_content")
            else main["description"]
        )
        cause = main["detail"]
        concept = main.get("concept", "Code Quality")

        finding_lines = []
        for p in patterns:
            loc = f"Line {p['line']}" if p.get("line") else ""
            func_note = f" (in `{p['function']}`) " if p.get("function") else ""
            finding_lines.append(f"  - **{loc}**{func_note}: {p['description']}")
        if has_static:
            for issue in static_issues:
                finding_lines.append(f"  - {issue}")
        findings_text = "\n".join(finding_lines)
    elif has_static:
        symptom = f"Static analysis flagged **{len(static_issues)} issue(s)**."
        cause = "These indicate potential security vulnerabilities or code-quality problems."
        concept = "Static analysis catches security and style issues that ML models may not focus on."
        findings_text = "\n".join(f"  - `{i}`" for i in static_issues)
    else:
        flag_msg = ""
        if flagged_functions:
            funcs = ", ".join(f"`{f['name']}`" for f in flagged_functions)
            flag_msg = f"\n  - **CodeBERT flagged:** {funcs}"
        if is_buggy:
            symptom = f"CodeBERT classified this code as **buggy**.{flag_msg}"
            cause = "The model detected patterns resembling common bug structures in real-world software."
            concept = "Deep learning models can detect subtle semantic bugs that rule-based tools miss."
        elif is_uncertain:
            symptom = f"CodeBERT is **uncertain** about this code.{flag_msg}"
            cause = "The code may contain patterns the model hasn't been trained on extensively."
            concept = "When ML models are uncertain, manual review is recommended."
        else:
            symptom = "No issues detected."
            cause = "The code follows standard, correct patterns."
            concept = "Even clean code should be tested with edge cases."
        findings_text = "  - No specific patterns were identified by the analyser."

    # ── 3) The Fix ──
    if has_patterns:
        fix_bullets = "\n".join(
            f"  - **Line {p['line']}:** {p['fix']}" for p in patterns
        )
        fix_why = "Each fix targets a specific bug pattern — fixing them prevents runtime errors, incorrect results, and unexpected behaviour."
    elif has_static:
        fix_bullets = "  - Address each flagged issue individually, paying attention to severity levels."
        fix_why = "Resolving security and quality issues prevents vulnerabilities and unexpected behaviour."
    else:
        fix_bullets = "  - Review your code for logic errors, off-by-one mistakes, wrong operators, or missing edge-case handling."
        fix_why = "CodeBERT's neural analysis suggests careful manual review."

    # ── 4) Mini-Lesson (contextual) ──
    _LESSONS = {
        "swapped_operator": (
            "In Python, `+=` is the compound addition operator. "
            "Writing `=+` changes the meaning entirely — it becomes a plain assignment with a unary `+`.",
            "`total += n` (correct)  vs  `total =+ n` (wrong — Python reads this as `total = (+n)`)",
        ),
        "division_by_zero": (
            "Always validate inputs before operations that can fail. "
            "Division by zero is one of the most common runtime crashes.",
            "`if not numbers: return 0` — guard clause before dividing by `len(numbers)`",
        ),
        "mutable_default": (
            "Never use mutable objects (lists, dicts, sets) as default arguments — "
            "they are shared across all calls to the function.",
            "`def foo(items=None): items = items or []` — safe pattern",
        ),
        "bare_except": (
            "Always catch specific exceptions. "
            "Bare `except:` hides real bugs and makes debugging very difficult.",
            "`except ValueError:` — catches only what you expect",
        ),
        "string_comparison": (
            "In Java, always use `.equals()` to compare string content. "
            "`==` compares object references, not the actual characters.",
            '`str1.equals(str2)` (correct)  vs  `str1 == str2` (wrong — compares references)',
        ),
        "resource_leak": (
            "Always close resources (files, connections, streams) when done. "
            "Use try-with-resources or `using` statements.",
            '`try (var r = new BufferedReader(...)) { ... }` — auto-closes on exit',
        ),
        "none_comparison": (
            "`None` is a singleton in Python — use `is`/`is not` for identity checks, not `==`/`!=`.",
            "`if x is None:` (correct)  vs  `if x == None:` (wrong)",
        ),
        "builtin_shadow": (
            "Avoid naming variables after Python built-ins — it silently hides the original function.",
            "Use `total_list` instead of `list`, `user_input` instead of `input`.",
        ),
        "general_catch": (
            "Catching the base `Exception` class swallows all errors, making bugs invisible.",
            "Catch specific types: `catch (IOException ex)` or `except ValueError:`.",
        ),
    }
    if has_patterns:
        main_type = patterns[0]["type"]
        lesson_rule, lesson_example = _LESSONS.get(
            main_type,
            (
                f"**{patterns[0].get('concept', 'Code Quality')}** — understanding this concept prevents a whole category of bugs.",
                "Review the pattern description above and practise with small examples.",
            ),
        )
    else:
        lesson_rule = "Always test your code with edge cases — empty inputs, zero values, very large numbers, and `None` values."
        lesson_example = "Use `with` statements for file handling, validate user inputs, and avoid bare `except:` blocks."

    # ── 5) Quick Check (contextual) ──
    _CHECKS = {
        "swapped_operator": lambda p: (
            f"What is the difference between `{p['line_content']}` and using `+=` instead? "
            f"Trace through the loop: what value does the variable have after each iteration?"
        ),
        "division_by_zero": lambda p: (
            "What happens if you call this function with an empty list `[]`? "
            "How would you prevent the crash?"
        ),
        "mutable_default": lambda _: (
            "If you call the function twice *without* passing the argument, "
            "do both calls get a fresh default or the same one?"
        ),
        "bare_except": lambda _: (
            "What types of exceptions would a bare `except:` catch that "
            "`except Exception:` would not?"
        ),
        "string_comparison": lambda _: (
            "If two Java strings contain the same characters but were created with `new String(...)`, "
            "what does `==` return vs `.equals()`?"
        ),
        "resource_leak": lambda _: (
            "If an exception is thrown between opening and closing a file, "
            "what happens to the file handle?"
        ),
    }
    if has_patterns:
        checker = _CHECKS.get(patterns[0]["type"])
        quick_check = checker(patterns[0]) if checker else (
            f"Can you explain why line {patterns[0]['line']} might cause unexpected behaviour?"
        )
    else:
        quick_check = "Can you identify which line(s) could cause problems if the input is empty or `None`?"

    # ── Assemble ──
    return f"""### 1) Goal
- {goal}

### 2) The Bug (Tutor Style)
- **Symptom:** {symptom}
- **Findings:**
{findings_text}
- **Cause:** {cause}
- **Concept:** {concept}

### 3) The Fix
- **What to change:**
{fix_bullets}
- **Why this fixes it:** {fix_why}

### 4) Mini-Lesson
- **Rule of thumb:** {lesson_rule}
- **Example:** {lesson_example}

### 5) Quick Check
- {quick_check}
"""


#Public API

def generate_educational_explanation(
    code: str,
    language: str = "python",
    static_issues: Optional[list] = None,
    codebert_label: str = "buggy",
    flagged_functions: Optional[list] = None,
) -> str:
    #Generate a student-friendly educational explanation
    if static_issues is None:
        static_issues = []

    if not _GPU_AVAILABLE:
        logger.info("[LLM Tutor] CUDA GPU not detected — using placeholder explanation.")
        return _placeholder_explanation(code, language, codebert_label, static_issues, flagged_functions)

    try:
        model, tokenizer = _load_model()
        prompt = _build_prompt(code, language, static_issues, codebert_label, flagged_functions)
        raw = _call_model(tokenizer, model, prompt)
        return _format_as_markdown(raw)
    except Exception as e:
        logger.exception("[LLM Tutor] GPU generation failed — falling back to placeholder.")
        return _placeholder_explanation(code, language, codebert_label, static_issues, flagged_functions)
