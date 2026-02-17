import os
import re
import pandas as pd
import torch
from difflib import unified_diff
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# CONFIGURATION
INPUT_CSV = "data/codebert_results_small_python.csv"
OUTPUT_CSV = "outputs/results_with_explanations.csv"
MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"

# Reproducibility
SEED = 42

# Generation settings
MAX_NEW_TOKENS = 400            # Increased to prevent cut-offs
MIN_NEW_TOKENS = 140            # Helps prevent early stopping
DO_SAMPLE = False               # Deterministic for research
TEMPERATURE = 0.4               # Only used if DO_SAMPLE=True
TOP_P = 0.9                     # Only used if DO_SAMPLE=True
REPETITION_PENALTY = 1.05
NO_REPEAT_NGRAM_SIZE = 4

# Data / prompt safety knobs
LIMIT_ROWS = None               # e.g. 5 for testing, or None for full dataset
MAX_CODE_CHARS = 3500           # Clip buggy/fixed
MAX_DIFF_CHARS = 2500           # Clip full diff
MAX_CHANGED_CHARS = 1200        # Clip changed-lines block
MAX_EXPLANATION_CHARS = 2500    # "too long" threshold

# SEED EVERYTHING
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# TEXT HELPERS
def clip_text(s: str, max_chars: int) -> str:
    s = str(s)
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n... [clipped]"


def normalize_ws(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()

# DIFF HELPERS
def make_diff(buggy: str, fixed: str) -> str:
    buggy_lines = buggy.splitlines(keepends=False)
    fixed_lines = fixed.splitlines(keepends=False)
    diff_lines = list(
        unified_diff(
            buggy_lines,
            fixed_lines,
            fromfile="buggy",
            tofile="fixed",
            lineterm="",
            n=3,
        )
    )
    return "\n".join(diff_lines)


def extract_changed_lines(diff_text: str) -> str:
    # Keep only actual changed lines (+ / -), skipping headers.
    # IMPORTANT: This is the evidence block we force the model to copy.
    lines = []
    for line in diff_text.splitlines():
        if line.startswith(("---", "+++", "@@")):
            continue
        if line.startswith("-") or line.startswith("+"):
            lines.append(line)
    return "\n".join(lines) if lines else "(no changed lines found)"


def parse_changed_lines_set(changed_only: str) -> set:
    # Turn changed lines into a set for copy-checking.
    # Ignore empty lines.
    s = set()
    for line in str(changed_only).splitlines():
        line = line.strip()
        if not line:
            continue
        # Keep only lines starting with + or -
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            s.add(line)
    return s


def extract_section3_changed_lines(explanation: str) -> set:
    # Extract the bullet lines inside Section 3 'Changed lines:'.
    # We look for lines that start with '-' or '+' anywhere after section 3 starts.
    text = str(explanation)
    # Find section 3
    m = re.search(r"\b3\)\s", text)
    if not m:
        return set()

    section3 = text[m.start():]
    # Stop at section 4 if present
    m4 = re.search(r"\b4\)\s", section3)
    if m4:
        section3 = section3[:m4.start()]

    found = set()
    for line in section3.splitlines():
        line_stripped = line.strip()
        # allow bullets like "- - oldline" or "  - + newline"
        if line_stripped.startswith(("+", "-")) and not line_stripped.startswith(("+++", "---")):
            found.add(line_stripped)
        else:
            # handle cases like: "- `- oldline`" or "- - oldline"
            # extract first +/- line inside backticks
            bt = re.search(r"(`)([+-].+?)\1", line_stripped)
            if bt:
                found.add(bt.group(2).strip())
    return found

# PROMPT + CHECKS
def build_prompt(buggy: str, fixed: str, label: str, changed_only: str) -> str:
    # Key idea: We do NOT ask the model to recreate the diff.
    # We give it the 'changed_only' block and force COPY in section 3.
    return f"""You are a friendly first-year programming tutor.

CRITICAL RULES (must follow):
1. Be faithful ONLY to the provided code and the CHANGED LINES block.
2. In Section 3, you MUST copy-paste the changed lines EXACTLY as given in [CHANGED LINES ONLY].
   - Do NOT reformat them, do NOT fix spacing, do NOT add/remove characters.
3. Do NOT invent any additional changes.
4. If the change block is unclear, say "Not enough info" instead of guessing.
5. Output ALL 5 sections.

Bug Type (from classifier): {label}

[CHANGED LINES ONLY — COPY EXACTLY IN SECTION 3]
{changed_only}

[BUGGY CODE]
{buggy}

[FIXED CODE]
{fixed}

RESPONSE FORMAT (EXACT):

1) Goal (1 sentence):
- ...

2) The Bug (Tutor Style):
- Symptom:
- Cause (supported by changed lines/code):
- Common beginner misconception:
- Concept name:

3) The Fix (COPY EXACTLY):
- Changed lines (copy EXACTLY from [CHANGED LINES ONLY]):
<PASTE HERE>

- Why this fixes it:

4) Mini-Lesson:
- Rule of thumb:
- Tiny example (1–2 lines):

5) Quick Check:
- One conceptual question:
"""


def format_ok(text: str) -> bool:
    # Robust format check
    t = str(text)
    return all(re.search(rf"\b{i}\)\s", t) for i in range(1, 6))


def quality_flag(text: str) -> str:
    if not format_ok(text):
        return "bad_format"
    if len(str(text)) > MAX_EXPLANATION_CHARS:
        return "too_long"
    return "ok"


def diff_copy_ok(explanation: str, changed_only: str) -> bool:
    # Check if the model copied the changed lines correctly.
    # We compare the set of +/- lines it used in Section 3 to the actual changed line set.
    gold = parse_changed_lines_set(changed_only)
    pred = extract_section3_changed_lines(explanation)

    # If gold has no changes, we consider it OK if pred is empty too
    if not gold:
        return len(pred) == 0

    # Must contain ALL gold lines (exact string match)
    return gold.issubset(pred)


def hallucination_flag(explanation: str, changed_only: str) -> str:
    # If the model didn't copy diff lines, it's likely hallucinating changes.
    if not diff_copy_ok(explanation, changed_only):
        return "diff_not_copied"
    return "ok"


def generate_explanation(tokenizer, model, prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are a precise, helpful programming tutor."},
        {"role": "user", "content": prompt},
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(text, return_tensors="pt", truncation=True).to(model.device)

    gen_kwargs = dict(
        max_new_tokens=MAX_NEW_TOKENS,
        min_new_tokens=MIN_NEW_TOKENS,
        do_sample=DO_SAMPLE,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id,
        repetition_penalty=REPETITION_PENALTY,
        no_repeat_ngram_size=NO_REPEAT_NGRAM_SIZE,
    )

    if DO_SAMPLE:
        gen_kwargs["temperature"] = TEMPERATURE
        gen_kwargs["top_p"] = TOP_P

    with torch.inference_mode():
        out = model.generate(**inputs, **gen_kwargs)

    gen_tokens = out[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()


# MAIN 
def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    print(f"Loading dataset from {INPUT_CSV}...")
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: File not found at {INPUT_CSV}")
        return

    df = pd.read_csv(INPUT_CSV)

    if LIMIT_ROWS is not None:
        print(f"TEST MODE: Using first {LIMIT_ROWS} rows only.")
        df = df.head(LIMIT_ROWS).copy()

    required_cols = {"buggy_code", "fixed_code", "predicted_label"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    print(f"Loading model {MODEL_ID} (4-bit)...")
    try:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
        )

        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            device_map="auto",
            quantization_config=bnb_config,
        )
        model.eval()
    except Exception as e:
        print(f"CRITICAL ERROR loading model: {e}")
        print("This script requires an NVIDIA GPU + CUDA for bitsandbytes 4-bit.")
        return

    print("Generating educational explanations...")
    diffs = []
    changed_blocks = []
    explanations = []
    format_flags = []
    quality_flags = []
    copy_flags = []
    halluc_flags = []

    for idx, row in df.iterrows():
        buggy = clip_text(row["buggy_code"], MAX_CODE_CHARS)
        fixed = clip_text(row["fixed_code"], MAX_CODE_CHARS)
        label = str(row["predicted_label"])

        diff_text = make_diff(buggy, fixed)
        diff_text = clip_text(diff_text, MAX_DIFF_CHARS)

        changed_only = extract_changed_lines(diff_text)
        changed_only = clip_text(changed_only, MAX_CHANGED_CHARS)

        prompt = build_prompt(
            buggy=buggy,
            fixed=fixed,
            label=label,
            changed_only=changed_only,
        )

        explanation = generate_explanation(tokenizer, model, prompt)

        diffs.append(diff_text)
        changed_blocks.append(changed_only)
        explanations.append(explanation)

        f_ok = format_ok(explanation)
        q_flag = quality_flag(explanation)
        c_ok = diff_copy_ok(explanation, changed_only)
        h_flag = hallucination_flag(explanation, changed_only)

        format_flags.append(f_ok)
        quality_flags.append(q_flag)
        copy_flags.append(c_ok)
        halluc_flags.append(h_flag)

        print(
            f"[{idx + 1}/{len(df)}] {label} | "
            f"format_ok={f_ok} | quality={q_flag} | diff_copy_ok={c_ok} | hall={h_flag}"
        )

    df["diff_text"] = diffs
    df["changed_lines_only"] = changed_blocks
    df["llm_explanation"] = explanations
    df["llm_format_ok"] = format_flags
    df["llm_quality_flag"] = quality_flags
    df["llm_diff_copy_ok"] = copy_flags
    df["llm_hallucination_flag"] = halluc_flags

    print(f"Saving results to {OUTPUT_CSV} ...")
    df.to_csv(OUTPUT_CSV, index=False)
    print("Done ")


if __name__ == "__main__":
    main()
