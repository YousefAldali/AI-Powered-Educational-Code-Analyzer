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


# Configuration
INPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "codebert_results_small_python.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "outputs", "baseline_2_results.csv")
CHECKPOINT_CSV = os.path.join(os.path.dirname(__file__), "..", "outputs", "baseline_2_checkpoint.csv")

MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"
SEED = 42

# Inference parameters (same as Baseline 3 for fair comparison)
MAX_NEW_TOKENS = 360
DO_SAMPLE = False
TEMPERATURE = 0.2
TOP_P = 0.95
REPETITION_PENALTY = 1.05
MAX_INPUT_TOKENS = 4096

# Content limits
LIMIT_ROWS = None
MAX_CODE_CHARS = 3500

# Resume/checkpoint
CHECKPOINT_EVERY = 5
RESUME_FROM_CHECKPOINT = True

# Memory hints
USE_MAX_MEMORY_SHARDING_HINT = True
GPU_MAX_MEMORY_GIB = 14
CPU_MAX_MEMORY_GIB = 32

# Periodic cache clearing
EMPTY_CACHE_EVERY = 20


# Logging
log_dir = Path(os.path.dirname(__file__)) / ".." / "outputs" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"baseline_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# GPU Optimization
if torch.cuda.is_available():
    try:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        logger.info("TF32 enabled")
    except Exception:
        pass


# Helpers

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


def make_diff(buggy: str, fixed: str) -> str:
    try:
        diff_lines = list(
            unified_diff(
                buggy.splitlines(keepends=False),
                fixed.splitlines(keepends=False),
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


# Zero-Shot Prompt (intentionally minimal)

def build_zero_shot_prompt(buggy_code: str, fixed_code: str, label: str) -> str:
    # A deliberately simple, unstructured prompt.
    # No tutor persona, no section format, no diff-grounding rules.
    # Just: here is buggy code and fixed code, explain the bug.

    return f"""Here is some buggy code and its fixed version.

Bug type: {label}

Buggy code:
{buggy_code}

Fixed code:
{fixed_code}

Explain the bug and how it was fixed."""


# Model Calls

def call_model(tokenizer, model, user_prompt: str) -> str:
    messages = [
        {"role": "user", "content": user_prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=MAX_INPUT_TOKENS
    ).to(model.device)

    gen_kwargs = dict(
        max_new_tokens=MAX_NEW_TOKENS,
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


# Quality Checks
# Baseline 2 output is unstructured on purpose, so we use simpler checks.

def basic_quality_flag(explanation: str) -> str:
    """Simple quality check for unstructured output."""
    text = str(explanation).strip()
    if not text or text.startswith("[ERROR"):
        return "empty"
    if len(text) < 30:
        return "too_short"
    return "ok"


# Main

def load_with_resume() -> pd.DataFrame:
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
        df = pd.read_csv(os.path.abspath(INPUT_CSV))
        logger.info(f"Loaded INPUT: {len(df)} rows")

    for col in ["diff_text", "changed_lines_only", "baseline2_explanation", "baseline2_quality_flag"]:
        if col not in df.columns:
            df[col] = None

    if LIMIT_ROWS is not None:
        df = df.head(LIMIT_ROWS).copy()

    return df


def get_start_index(df: pd.DataFrame) -> int:
    start_idx = len(df)
    vals = df["baseline2_explanation"].tolist() if "baseline2_explanation" in df.columns else []
    for i, val in enumerate(vals):
        if pd.isna(val) or str(val).strip() == "" or str(val).startswith("[ERROR"):
            start_idx = i
            break
    return start_idx


def main():
    logger.info("Baseline 2 (Zero-Shot Qwen) -- starting")
    set_seed(SEED)

    df = load_with_resume()
    start_idx = get_start_index(df)

    if start_idx >= len(df):
        logger.info("All rows already processed.")
        return

    # Load model
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
        try:
            if idx > 0 and idx % EMPTY_CACHE_EVERY == 0 and torch.cuda.is_available():
                torch.cuda.empty_cache()
                gc.collect()

            row = df.iloc[idx]
            label = str(row.get("predicted_label", ""))

            buggy_full = decode_escaped_newlines(row.get("buggy_code", ""))
            fixed_full = decode_escaped_newlines(row.get("fixed_code", ""))

            # Compute diff (stored for later comparison, but NOT given to the model)
            diff_text = make_diff(buggy_full, fixed_full)
            changed_lines = extract_changed_lines(diff_text)

            df.at[idx, "diff_text"] = diff_text
            df.at[idx, "changed_lines_only"] = changed_lines

            # Build the minimal zero-shot prompt
            buggy_prompt = clip_text(buggy_full, MAX_CODE_CHARS)
            fixed_prompt = clip_text(fixed_full, MAX_CODE_CHARS)

            prompt = build_zero_shot_prompt(buggy_prompt, fixed_prompt, label)
            explanation = call_model(tokenizer, model, prompt)

            flag = basic_quality_flag(explanation)

            df.at[idx, "baseline2_explanation"] = explanation
            df.at[idx, "baseline2_quality_flag"] = flag

            logger.info(f"[{idx+1}/{len(df)}] label={label}  flag={flag}  len={len(explanation)}")

            if (idx + 1) % CHECKPOINT_EVERY == 0:
                df.to_csv(CHECKPOINT_CSV, index=False)

            if idx % 50 == 0:
                gc.collect()

        except torch.cuda.OutOfMemoryError:
            logger.error(f"Row {idx}: CUDA OOM. Clearing cache.")
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            df.at[idx, "baseline2_explanation"] = "[ERROR] CUDA OOM"
            df.at[idx, "baseline2_quality_flag"] = "oom"
            if (idx + 1) % CHECKPOINT_EVERY == 0:
                df.to_csv(CHECKPOINT_CSV, index=False)
            continue

        except KeyboardInterrupt:
            df.to_csv(CHECKPOINT_CSV, index=False)
            raise

        except Exception as e:
            logger.error(f"Row {idx} Error: {e}")
            df.at[idx, "baseline2_explanation"] = f"[ERROR] {e}"
            df.at[idx, "baseline2_quality_flag"] = "error"
            continue

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    logger.info(f"Done. Saved to {OUTPUT_CSV}")

    if os.path.exists(CHECKPOINT_CSV):
        os.remove(CHECKPOINT_CSV)


if __name__ == "__main__":
    main()
