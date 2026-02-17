import os
import re
import sys
import gc
import logging
from pathlib import Path
from difflib import unified_diff
from datetime import datetime

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig


# CONFIGURATION
INPUT_CSV = "data/codebert_results_small_python.csv"
OUTPUT_CSV = "outputs/results_with_explanations.csv"
CHECKPOINT_CSV = "outputs/checkpoint.csv"

MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
SEED = 42

# Inference parameters
MAX_NEW_TOKENS = 360
MIN_NEW_TOKENS = 0
DO_SAMPLE = False
TEMPERATURE = 0.2
TOP_P = 0.95
REPETITION_PENALTY = 1.05

# Context window
MAX_INPUT_TOKENS = 4096

# Content limits
LIMIT_ROWS = None
MAX_CODE_CHARS = 3500
MAX_EXPLANATION_CHARS = 3000

# Changed-lines clipping for PROMPT only (validation always uses full)
CLIP_CHANGED_LINES_PROMPT = True
MAX_CHANGED_LINES_PROMPT_CHARS = 1500

# Section 3 injection parameters
MAX_SECTION3_DIFF_LINES = 8  # keep Section 3 compact

# Resume/checkpoint
CHECKPOINT_EVERY = 5
RESUME_FROM_CHECKPOINT = True

# Memory hints 
USE_MAX_MEMORY_SHARDING_HINT = True
GPU_MAX_MEMORY_GIB = 14
CPU_MAX_MEMORY_GIB = 32

# If no diff, skip model
SKIP_MODEL_WHEN_NO_DIFF = True

# periodic cache clearing
EMPTY_CACHE_EVERY = 20


# LOGGING
log_dir = Path("outputs/logs")
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# GPU OPT
if torch.cuda.is_available():
    try:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        logger.info("TF32 enabled")
    except Exception:
        pass


# UTILITIES
def set_seed(seed: int) -> None:
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def clip_text(s: str, max_chars: int) -> str:
    s = "" if s is None else str(s)
    return s if len(s) <= max_chars else s[:max_chars] + "\n... [clipped]"


def decode_escaped_newlines(s: str) -> str:
    s = "" if s is None else str(s)
    return s.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", "\t")


# DIFF HELPERS
def make_diff(buggy_full: str, fixed_full: str) -> str:
    try:
        buggy_lines = buggy_full.splitlines(keepends=False)
        fixed_lines = fixed_full.splitlines(keepends=False)
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
    except Exception as e:
        logger.warning(f"make_diff error: {e}")
        return "(error generating diff)"


def extract_changed_lines(diff_text: str) -> str:
    try:
        out = []
        for line in diff_text.splitlines():
            if line.startswith(("---", "+++", "@@")):
                continue
            if line.startswith("-") or line.startswith("+"):
                out.append(line)
        return "\n".join(out) if out else "(no changed lines found)"
    except Exception as e:
        logger.warning(f"extract_changed_lines error: {e}")
        return "(error extracting changes)"


def tokens_from_changed_lines(changed_lines: str) -> str:

    # Token hint only. Keep it lightweight; don't over-restrict the model.
    try:
        text = re.sub(r"^[+-]\s*", "", str(changed_lines), flags=re.MULTILINE)
        toks = re.findall(
            r"""
            "(?:\\.|[^"\\])*" | '(?:\\.|[^'\\])*' |
            [A-Za-z_]\w* | \d+(?:\.\d+)? |
            ==|!=|<=|>=|\*\*|//|<<|>>|\+=|-=|\*=|/=|%=|&=|\|=|\^=|->|:=|
            =|<|>|\+|-|\*|/|%|&|\||\^|~|:|\.|,|\(|\)|\[|\]|\{|\}|;|@
            """,
            text,
            flags=re.VERBOSE,
        )
        seen = set()
        ordered = []
        for t in toks:
            if t not in seen:
                seen.add(t)
                ordered.append(t)
        return ", ".join(ordered[:80]) if ordered else "(no tokens)"
    except Exception:
        return "(error extracting tokens)"


# PROMPT
def build_prompt(buggy_prompt: str, fixed_prompt: str, label: str, changed_lines_prompt: str) -> str:
    allowed_tokens = tokens_from_changed_lines(changed_lines_prompt)
    return f"""You are Qwen, a precise first-year programming tutor.

CRITICAL INSTRUCTIONS:
1) Explain the bug and fix based ONLY on the provided [CHANGED LINES] and code context.
2) Do NOT invent identifiers, numbers, or operators not present in [CHANGED LINES].
3) In Section 3, you MUST paste exact lines from [CHANGED LINES], each line starting with + or -.
4) Do NOT use markdown code blocks (```) or backticks anywhere in Section 3.
5) Output exactly the 5 numbered sections.

Bug Type Detected: {label}

[CHANGED LINES]
{changed_lines_prompt}

[ALLOWED TOKENS] (hint only)
{allowed_tokens}

[BUGGY CODE CONTEXT]
{buggy_prompt}

[FIXED CODE CONTEXT]
{fixed_prompt}

RESPONSE FORMAT:

1) Goal (1 sentence):
- ...

2) The Bug (Tutor Style):
- Symptom: ...
- Cause (supported by changed lines / code): ...
- Common beginner misconception: ...
- Concept name: ...

3) The Fix (Anchor to Diff):
- Exact changed lines (paste from CHANGED LINES):
  - ...
  - ...
- Why this fixes it: ...

4) Mini-Lesson:
- Rule of thumb: ...
- Tiny example (ONE line): ...

5) Quick Check:
- One conceptual question: ...
"""


# OUTPUT CHECKS
def format_ok(text: str) -> bool:
    t = str(text)
    return all(re.search(rf"(^|\n)\s*{i}(\)|\.)\s", t) for i in range(1, 6))


def extract_section(text: str, section_num: int) -> str:
    t = str(text)
    if section_num == 5:
        m = re.search(r"(^|\n)\s*5(\)|\.).*$", t, flags=re.DOTALL)
        return m.group(0) if m else ""
    pattern = rf"(^|\n)\s*{section_num}(\)|\.)\s.*?(?=(^|\n)\s*{section_num+1}(\)|\.)\s|$)"
    m = re.search(pattern, t, flags=re.DOTALL)
    return m.group(0) if m else ""


def trim_after_section_5(text: str) -> str:
    t = str(text)
    m5 = re.search(r"(^|\n)\s*5(\)|\.)\s", t)
    if not m5:
        return t.strip()
    start5 = m5.start()
    m6 = re.search(r"(^|\n)\s*6(\)|\.)\s", t[start5:])
    return (t[: start5 + m6.start()] if m6 else t).strip()


def _norm_diff_line(s: str) -> str:
    s = str(s).rstrip()
    s = re.sub(r"^([+-])\s+", r"\1", s)
    return s


def extract_pasted_diff_lines_from_section3(explanation: str) -> list:
    # Strict+safe extractor:
    #   - ignores headers "Why this fixes it"
    #   - handles bullets/backticks
    #   - final extracted diff lines must start with +/-
    sec3 = extract_section(explanation, 3)
    if not sec3:
        return []

    header_pattern = re.compile(
        r"^\s*(?:-|\*|•)?\s*(?:"
        r"Symptom|Cause|Goal|Mini-?Lesson|The Bug|The Fix|"
        r"Exact changed lines|Why this fixes it"
        r")\b\s*[:(]?",
        re.IGNORECASE,
    )

    out = []
    for raw in sec3.splitlines():
        line = raw.strip()
        if not line:
            continue
        if header_pattern.match(line):
            continue

        # only strip bullets introducing a diff marker/backtick
        line = re.sub(r"^(?:-|\*|•)\s+(?=[`+-])", "", line)
        line = re.sub(r"^\d+\.\s+(?=[`+-])", "", line)

        line = line.strip("`").strip()

        if not re.match(r"^[+-]\s*\S.*$", line):
            continue

        out.append(line.strip("`").strip())

    # de-dup
    seen = set()
    ordered = []
    for x in out:
        nx = _norm_diff_line(x)
        if nx not in seen:
            seen.add(nx)
            ordered.append(x)
    return ordered


def fake_diff_in_section3(explanation: str, changed_lines_full: str) -> bool:
    if str(changed_lines_full).strip() == "(no changed lines found)":
        return False
    pasted = extract_pasted_diff_lines_from_section3(explanation)
    if not pasted:
        return True
    gt_lines = [ln for ln in str(changed_lines_full).splitlines() if ln.strip()]
    gt_set = set(_norm_diff_line(ln) for ln in gt_lines)
    for ln in pasted:
        if _norm_diff_line(ln) not in gt_set:
            return True
    return False


def quality_flag(explanation: str, changed_lines_full: str) -> str:
    if not format_ok(explanation):
        return "bad_format"
    if len(str(explanation)) > MAX_EXPLANATION_CHARS:
        return "too_long"
    if str(changed_lines_full).strip() == "(no changed lines found)":
        return "no_diff"
    if fake_diff_in_section3(explanation, changed_lines_full):
        return "fake_diff"
    return "ok"


# SECTION 3 INJECTION (0% fake diffs)
def get_section3_diff_lines(changed_lines_full: str, k: int) -> list:
    lines = [ln.rstrip() for ln in str(changed_lines_full).splitlines() if ln.strip()]
    if not lines or lines == ["(no changed lines found)"]:
        return []
    # Prefer to keep ordering; just cap length
    return lines[:k]


def inject_ground_truth_section3(explanation: str, changed_lines_full: str) -> str:
    # Replace section 3 with ground-truth diff lines while preserving a meaningful
    # 'Why this fixes it' text extracted from the model's original section 3.
    sec1 = extract_section(explanation, 1).strip()
    sec2 = extract_section(explanation, 2).strip()
    sec3 = extract_section(explanation, 3).strip()
    sec4 = extract_section(explanation, 4).strip()
    sec5 = extract_section(explanation, 5).strip()

    # 1) Extract "why" BEFORE any cleaning that might drop bullet lines
    why = ""
    m = re.search(
        r"(?:-|\*|•)?\s*Why this fixes it\s*[:\-\u2013\u2014]\s*(.*)",
        sec3,
        flags=re.IGNORECASE,
    )
    if m:
        why = (m.group(1) or "").strip()

    # Fallback: collect non-diff prose lines from sec3
    if not why:
        clean_lines = []
        for ln in sec3.splitlines():
            if re.match(r"^\s*3(\)|\.)", ln):
                continue
            if "The Fix" in ln:
                continue
            if re.match(r"^\s*[+-]\s*\S", ln):
                continue
            # keep prose (including bullet prose)
            clean_lines.append(ln.strip())
        why = " ".join([x for x in clean_lines if x]).strip()

    if not why or len(why) < 10:
        why = "The logic was corrected to match the intended behavior shown in the diff."

    # 2) Ground truth diff lines
    gt_lines = get_section3_diff_lines(changed_lines_full, MAX_SECTION3_DIFF_LINES)

    # 3) Build new Section 3
    new_sec3_lines = [
        "3) The Fix (Anchor to Diff):",
        "- Exact changed lines (verbatim from CHANGED LINES):",
    ]
    if gt_lines:
        new_sec3_lines.extend(gt_lines)
    else:
        new_sec3_lines.append("(no changed lines found)")
    new_sec3_lines.append(f"- Why this fixes it: {why}")

    stitched = "\n".join([sec1, sec2, "\n".join(new_sec3_lines), sec4, sec5]).strip()
    return stitched


def safe_fallback_explanation(label: str, changed_lines_full: str) -> str:
    # Last resort: guaranteed format, grounded.
    gt_lines = get_section3_diff_lines(changed_lines_full, MAX_SECTION3_DIFF_LINES)
    sec3 = [
        "3) The Fix (Anchor to Diff):",
        "- Exact changed lines (verbatim from CHANGED LINES):",
    ]
    if gt_lines:
        sec3.extend(gt_lines)
    else:
        sec3.append("(no changed lines found)")
    sec3.append("- Why this fixes it: The fix matches the behavior indicated by the diff.")

    return "\n".join([
        "1) Goal (1 sentence):",
        f"- Provide a grounded explanation for bug type '{label}'.",
        "",
        "2) The Bug (Tutor Style):",
        "- Symptom: The code behaved incorrectly before the fix.",
        "- Cause (supported by changed lines / code): The root cause is reflected in the diff.",
        "- Common beginner misconception: Small token/operator changes don’t matter.",
        "- Concept name: Correctness / bug fix.",
        "",
        "\n".join(sec3),
        "",
        "4) Mini-Lesson:",
        "- Rule of thumb: Always anchor explanations to the exact lines that changed.",
        "- Tiny example (ONE line): Change the operator/variable to match the intended logic.",
        "",
        "5) Quick Check:",
        "- One conceptual question: Which exact line changed the behavior and why?",
    ]).strip()


# MODEL CALLS
def _call_model(tokenizer, model, user_prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are a helpful and precise programming tutor."},
        {"role": "user", "content": user_prompt},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS).to(model.device)

    gen_kwargs = dict(
        max_new_tokens=MAX_NEW_TOKENS,
        min_new_tokens=MIN_NEW_TOKENS,
        do_sample=DO_SAMPLE,
        repetition_penalty=REPETITION_PENALTY,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
        use_cache=True,
    )
    if DO_SAMPLE:
        gen_kwargs.update(dict(temperature=TEMPERATURE, top_p=TOP_P))

    with torch.inference_mode():
        out = model.generate(**inputs, **gen_kwargs)

    gen_tokens = out[0][inputs["input_ids"].shape[-1]:]
    result = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

    del inputs, out, gen_tokens
    return result


def repair_format(tokenizer, model, bad_output: str) -> str:
    repair_prompt = f"""Reformat into EXACTLY 5 numbered sections (1..5). Do NOT add new facts.
Do NOT use code blocks.

[INPUT]
{bad_output}

Return ONLY the reformatted 5 sections.
"""
    return _call_model(tokenizer, model, repair_prompt)


# MAIN
def load_with_resume_priority() -> pd.DataFrame:
    df = None
    if RESUME_FROM_CHECKPOINT:
        if os.path.exists(CHECKPOINT_CSV):
            try:
                df = pd.read_csv(CHECKPOINT_CSV)
                logger.info(f"Resuming from CHECKPOINT: {len(df)} rows")
            except Exception:
                df = None
        if df is None and os.path.exists(OUTPUT_CSV):
            try:
                df = pd.read_csv(OUTPUT_CSV)
                logger.info(f"Resuming from OUTPUT: {len(df)} rows")
            except Exception:
                df = None

    if df is None:
        df = pd.read_csv(INPUT_CSV)
        logger.info(f"Loaded INPUT: {len(df)} rows")

    # Ensure columns exist
    for col in ["diff_text", "changed_lines_only", "llm_explanation", "llm_quality_flag", "llm_format_ok"]:
        if col not in df.columns:
            df[col] = None

    if LIMIT_ROWS is not None:
        df = df.head(LIMIT_ROWS).copy()

    return df


def get_start_index(df: pd.DataFrame) -> int:
    start_idx = len(df)
    vals = df["llm_explanation"].tolist() if "llm_explanation" in df.columns else []
    for i, val in enumerate(vals):
        if pd.isna(val) or str(val).strip() == "" or str(val).startswith("[ERROR"):
            start_idx = i
            break
    return start_idx


def main():
    logger.info("Starting Pipeline - V6.3 (GT Section 3 injection + OOM safe)")
    set_seed(SEED)

    df = load_with_resume_priority()
    start_idx = get_start_index(df)

    if start_idx >= len(df):
        logger.info("All rows processed.")
        return

    # Load model once
    logger.info("Loading model...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type="nf4",
    )
    model_kwargs = dict(
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    if USE_MAX_MEMORY_SHARDING_HINT and torch.cuda.is_available():
        if torch.cuda.device_count() >= 2:
            model_kwargs["max_memory"] = {
                0: f"{GPU_MAX_MEMORY_GIB}GiB",
                1: f"{GPU_MAX_MEMORY_GIB}GiB",
                "cpu": f"{CPU_MAX_MEMORY_GIB}GiB",
            }
        else:
            model_kwargs["max_memory"] = {
                0: f"{GPU_MAX_MEMORY_GIB}GiB",
                "cpu": f"{CPU_MAX_MEMORY_GIB}GiB",
            }

    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **model_kwargs)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info(f"Processing from row {start_idx}...")

    for idx in range(start_idx, len(df)):
        # Initialize to avoid UnboundLocalError in exception handlers
        changed_lines_full = "(no changed lines found)"
        label = ""

        try:
            if idx > 0 and idx % EMPTY_CACHE_EVERY == 0 and torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()

            row = df.iloc[idx]
            label = str(row.get("predicted_label", ""))

            # Decode once (IMPORTANT: prompt uses decoded)
            buggy_full = decode_escaped_newlines(row.get("buggy_code", ""))
            fixed_full = decode_escaped_newlines(row.get("fixed_code", ""))

            diff_text = make_diff(buggy_full, fixed_full)
            changed_lines_full = extract_changed_lines(diff_text)

            df.at[idx, "diff_text"] = diff_text
            df.at[idx, "changed_lines_only"] = changed_lines_full

            if str(changed_lines_full).strip() == "(no changed lines found)" and SKIP_MODEL_WHEN_NO_DIFF:
                df.at[idx, "llm_explanation"] = "SKIPPED: No diff found"
                df.at[idx, "llm_quality_flag"] = "no_diff"
                df.at[idx, "llm_format_ok"] = True
                if (idx + 1) % CHECKPOINT_EVERY == 0:
                    df.to_csv(CHECKPOINT_CSV, index=False)
                continue

            # Prompt diff clipping (prompt only)
            changed_lines_prompt = changed_lines_full
            if CLIP_CHANGED_LINES_PROMPT and len(changed_lines_full) > MAX_CHANGED_LINES_PROMPT_CHARS:
                changed_lines_prompt = clip_text(changed_lines_full, MAX_CHANGED_LINES_PROMPT_CHARS)

            buggy_prompt = clip_text(buggy_full, MAX_CODE_CHARS)
            fixed_prompt = clip_text(fixed_full, MAX_CODE_CHARS)

            prompt = build_prompt(buggy_prompt, fixed_prompt, label, changed_lines_prompt)
            explanation = _call_model(tokenizer, model, prompt)
            explanation = trim_after_section_5(explanation)

            # Repair format if needed
            if not format_ok(explanation):
                logger.info(f"Row {idx}: repairing format...")
                explanation = repair_format(tokenizer, model, explanation)
                explanation = trim_after_section_5(explanation)

            # If fake diff -> inject ground truth section 3 (no extra LLM call needed)
            flag = quality_flag(explanation, changed_lines_full)
            if flag == "fake_diff":
                explanation = inject_ground_truth_section3(explanation, changed_lines_full)
                explanation = trim_after_section_5(explanation)
                flag = quality_flag(explanation, changed_lines_full)

            # If still not ok, hard fallback (guaranteed format)
            if flag in {"bad_format", "fake_diff"}:
                explanation = safe_fallback_explanation(label, changed_lines_full)
                flag = "hard_fallback"

            fmt_ok = format_ok(explanation)

            df.at[idx, "llm_explanation"] = explanation
            df.at[idx, "llm_quality_flag"] = flag
            df.at[idx, "llm_format_ok"] = fmt_ok

            logger.info(f"[{idx+1}/{len(df)}] flag={flag} format_ok={fmt_ok}")

            if (idx + 1) % CHECKPOINT_EVERY == 0:
                df.to_csv(CHECKPOINT_CSV, index=False)

            if idx % 50 == 0:
                gc.collect()

        except torch.cuda.OutOfMemoryError:
            logger.error(f"Row {idx}: CUDA OOM. Clearing cache and writing fallback.")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            explanation = safe_fallback_explanation(label, changed_lines_full)
            df.at[idx, "llm_explanation"] = explanation
            df.at[idx, "llm_quality_flag"] = "oom_fallback"
            df.at[idx, "llm_format_ok"] = True
            if (idx + 1) % CHECKPOINT_EVERY == 0:
                df.to_csv(CHECKPOINT_CSV, index=False)
            continue

        except KeyboardInterrupt:
            df.to_csv(CHECKPOINT_CSV, index=False)
            raise

        except Exception as e:
            logger.error(f"Row {idx} Error: {e}")
            explanation = safe_fallback_explanation(label, changed_lines_full)
            df.at[idx, "llm_explanation"] = explanation
            df.at[idx, "llm_quality_flag"] = "error_fallback"
            df.at[idx, "llm_format_ok"] = True
            continue

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    logger.info(f"Done. Saved to {OUTPUT_CSV}")

    if os.path.exists(CHECKPOINT_CSV):
        os.remove(CHECKPOINT_CSV)


if __name__ == "__main__":
    main()
