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

#Lazy-loaded model state (only populated when GPU is present)
_model = None
_tokenizer = None

MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
MAX_NEW_TOKENS = 360
MAX_INPUT_TOKENS = 4096


def _load_model():
    #Load Qwen once, cache globally.
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
    # Dynamic fallback: builds explanation strictly from CodeBERT + static analysis outputs.
    # No hardcoded bug-specific heuristics — works correctly for any code snippet.
    cb_label = codebert_label.lower()
    is_buggy = cb_label == "buggy"
    is_uncertain = cb_label == "uncertain"
    has_issues = bool(static_issues)

    flag_msg = ""
    if flagged_functions:
        funcs = ", ".join(f"`{f['name']}`" for f in flagged_functions)
        flag_msg = f"\n  - **CodeBERT flagged:** {funcs}"

    if has_issues:
        issue_bullets = "\n".join(f"  - `{i}`" for i in static_issues)
        symptom = f"Static analysis flagged **{len(static_issues)} issue(s)** in your code.{flag_msg}"
        cause = "The issues listed above indicate potential security vulnerabilities or code quality problems."
        fix = "Address each flagged issue individually. Pay close attention to the severity levels reported."
    else:
        issue_bullets = "  - No specific lines were flagged by static analysis."
        symptom = f"CodeBERT's analysis classified this code as **{codebert_label}**.{flag_msg}"
        if is_buggy:
            cause = "The model detected patterns in your code that resemble common bug structures found in real-world software."
            fix = "Review your code for logic errors, off-by-one mistakes, wrong operators, or missing edge-case handling."
        elif is_uncertain:
            cause = "This file likely contains boilerplate structure (like imports or config logic) that CodeBERT was not explicitly trained on, lowering its confidence."
            fix = "Ensure your logic is correct manually. CodeBERT abstains from making a prediction here to avoid false positives."
        else:
            cause = "The model evaluated the semantic structure and found no known defect patterns."
            fix = "No immediate fixes required. Ensure your logic covers all business requirements."

    if has_issues:
        if is_buggy:
            verdict = "Both CodeBERT and static analysis found potential problems."
            concept = "Defence in depth — using multiple analysis tools catches more issues than any single tool alone."
        elif is_uncertain:
            verdict = "Static analysis found issues, but CodeBERT was uncertain about the file's overall semantics."
            concept = "ML models struggle with out-of-distribution boilerplate logic, making static analysis a crucial fallback."
        else:
            verdict = "Static analysis found issues, though CodeBERT considered the overall logic acceptable."
            concept = "Static analysis catches security and style issues, while ML models focus on logical correctness — both perspectives matter."
    else:
        if is_buggy:
            verdict = "CodeBERT detected potential issues, though static analysis did not flag any specific lines."
            concept = "Deep learning models can detect subtle semantic bugs (wrong logic, swapped variables) that rule-based tools miss."
        elif is_uncertain:
            verdict = "No static analysis issues found, and CodeBERT is uncertain about the file's validity."
            concept = "When ML models analyze code that looks different from their short training snippets, they safely abstain rather than guessing."
        else:
            verdict = "Your code looks good!"
            concept = "Even when tools report clean code, always test with edge cases to be sure."

    return f"""### 1) Goal
- {verdict}

### 2) The Bug (Tutor Style)
- **Symptom:** {symptom}
- **Findings:**
{issue_bullets}
- **Cause:** {cause}
- **Concept:** {concept}

### 3) The Fix
- **What to change:** {fix}
- **Why this fixes it:** Addressing the identified patterns prevents runtime errors, security vulnerabilities, and unexpected behaviour.

### 4) Mini-Lesson
- **Rule of thumb:** Always test your code with edge cases — empty inputs, zero values, very large numbers, and `None` values.
- **Best practice:** Use `with` statements for file handling, validate user inputs, and avoid bare `except:` blocks.

### 5) Quick Check
- Can you identify which line(s) could cause problems if the input is empty or `None`?
"""


#Public API

def generate_educational_explanation(
    code: str,
    language: str = "python",
    static_issues: Optional[list] = None,
    codebert_label: str = "buggy",
    flagged_functions: Optional[list] = None,
) -> str:
    #Generate a student-friendly educational explanation for a buggy code snippet.
    #Returns a Markdown string suitable for rendering with react-markdown.
    #Falls back to a structured placeholder if no GPU is available.
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
