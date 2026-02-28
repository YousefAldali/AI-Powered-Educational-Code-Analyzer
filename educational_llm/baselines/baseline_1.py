"""
Baseline 1 -- Diff-Only Explanation Generator (No LLM)
======================================================
The simplest baseline: generates template-based explanations purely
from the unified diff between buggy and fixed code.
No model calls, no GPU needed.

The output follows the same 5-section format as Baseline 3
(the structured LLM explainer) so that quality metrics
(format_ok, fake_diff, etc.) can be compared apples-to-apples.

Baseline 1: Diff-Only (this file)
Baseline 2: Zero-shot Qwen (unstructured prompt)
Baseline 3: Structured educational prompt (run_explainer.py)
"""

import os
import re
import sys
import logging
from pathlib import Path
from difflib import unified_diff
from datetime import datetime

import pandas as pd


# ── CONFIGURATION ────────────────────────────────────────────────────
INPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "codebert_results_small_python.csv")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "outputs", "baseline_1_results.csv")

LIMIT_ROWS = None  # set to int for quick tests

# ── LOGGING ──────────────────────────────────────────────────────────
log_dir = Path(os.path.dirname(__file__)) / ".." / "outputs" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"baseline_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── HELPERS (same logic as run_explainer.py) ─────────────────────────

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


# ── QUALITY CHECKS (mirrors run_explainer.py) ────────────────────────

def format_ok(text: str) -> bool:
    t = str(text)
    return all(re.search(rf"(^|\n)\s*{i}(\)|\.)\s", t) for i in range(1, 6))


def _norm_diff_line(s: str) -> str:
    s = str(s).rstrip()
    s = re.sub(r"^([+-])\s+", r"\1", s)
    return s


def extract_section(text: str, section_num: int) -> str:
    t = str(text)
    if section_num == 5:
        m = re.search(r"(^|\n)\s*5(\)|\.)\s.*$", t, flags=re.DOTALL)
        return m.group(0) if m else ""
    pattern = rf"(^|\n)\s*{section_num}(\)|\.)\s.*?(?=(^|\n)\s*{section_num+1}(\)|\.)\s|$)"
    m = re.search(pattern, t, flags=re.DOTALL)
    return m.group(0) if m else ""


def extract_pasted_diff_lines_from_section3(explanation: str) -> list:
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
    if str(changed_lines_full).strip() == "(no changed lines found)":
        return "no_diff"
    if fake_diff_in_section3(explanation, changed_lines_full):
        return "fake_diff"
    return "ok"


# ── TEMPLATE GENERATOR ───────────────────────────────────────────────

def generate_diff_only_explanation(
    label: str,
    changed_lines: str,
    first_removed: str,
    first_added: str,
) -> str:
    """Build a mechanical 5-section explanation from diff data only."""

    # pick a readable snippet for Section 4
    example_line = first_added if first_added else first_removed
    if not example_line:
        example_line = "(no example available)"

    # format the diff lines for Section 3 (no extra indent — must match
    # ground truth exactly so the quality checker doesn't flag fake_diff)
    diff_block = "\n".join(
        ln for ln in changed_lines.splitlines() if ln.strip()
    )
    if not diff_block.strip():
        diff_block = "(no changed lines found)"

    return f"""1) Goal (1 sentence):
- Identify and explain the bug labelled '{label}'.

2) The Bug (Tutor Style):
- Symptom: The code produces incorrect or unexpected behaviour.
- Cause (supported by changed lines / code): The diff shows lines were modified to correct the logic.
- Common beginner misconception: Small token or operator changes do not affect program behaviour.
- Concept name: {label}

3) The Fix (Anchor to Diff):
- Exact changed lines (verbatim from CHANGED LINES):
{diff_block}
- Why this fixes it: The changed lines correct the identified issue by modifying the relevant tokens.

4) Mini-Lesson:
- Rule of thumb: Always review diffs carefully to understand what changed and why.
- Tiny example (ONE line): {example_line}

5) Quick Check:
- One conceptual question: Why was this particular change necessary to fix the bug?"""


# ── MAIN ─────────────────────────────────────────────────────────────

def main():
    logger.info("Baseline 1 (Diff-Only) -- starting")

    input_path = os.path.abspath(INPUT_CSV)
    if not os.path.exists(input_path):
        logger.error(f"Input CSV not found: {input_path}")
        sys.exit(1)

    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")

    if LIMIT_ROWS is not None:
        df = df.head(LIMIT_ROWS).copy()

    explanations = []
    flags = []
    fmt_oks = []
    diffs = []
    changed_lines_list = []

    for idx, row in df.iterrows():
        label = str(row.get("predicted_label", ""))
        buggy_full = decode_escaped_newlines(row.get("buggy_code", ""))
        fixed_full = decode_escaped_newlines(row.get("fixed_code", ""))

        diff_text = make_diff(buggy_full, fixed_full)
        changed_lines = extract_changed_lines(diff_text)

        # grab first removed / added line for the mini example
        first_removed = ""
        first_added = ""
        for ln in changed_lines.splitlines():
            if ln.startswith("-") and not first_removed:
                first_removed = ln
            if ln.startswith("+") and not first_added:
                first_added = ln

        explanation = generate_diff_only_explanation(
            label, changed_lines, first_removed, first_added
        )

        flag = quality_flag(explanation, changed_lines)
        fmt = format_ok(explanation)

        explanations.append(explanation)
        flags.append(flag)
        fmt_oks.append(fmt)
        diffs.append(diff_text)
        changed_lines_list.append(changed_lines)

        logger.info(f"[{idx+1}/{len(df)}] label={label}  flag={flag}  format_ok={fmt}")

    df["diff_text"] = diffs
    df["changed_lines_only"] = changed_lines_list
    df["baseline_explanation"] = explanations
    df["baseline_quality_flag"] = flags
    df["baseline_format_ok"] = fmt_oks

    output_path = os.path.abspath(OUTPUT_CSV)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Done. Saved {len(df)} rows to {output_path}")

    # quick summary
    flag_counts = df["baseline_quality_flag"].value_counts().to_dict()
    logger.info(f"Quality flags: {flag_counts}")


if __name__ == "__main__":
    main()
