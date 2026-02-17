import pandas as pd
import torch
from difflib import unified_diff
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

# CONFIG
INPUT_CSV = "educational_llm/data/codebert_results_small_python.csv"
OUTPUT_CSV = "outputs/results_with_explanations.csv"
MODEL_ID = "Qwen/Qwen2.5-Coder-7B-Instruct"

MAX_NEW_TOKENS = 160  # keep short

# LOAD DATA
print("Loading dataset...")
df = pd.read_csv(INPUT_CSV)

required_cols = {"buggy_code", "fixed_code", "predicted_label"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# LOAD MODEL (4-bit)
print("Loading Qwen2.5-Coder-7B-Instruct (4-bit)...")

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
)

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

# Ensure padding works
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    quantization_config=bnb_config,
)
model.eval()

# HELPERS
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

def explain(buggy: str, fixed: str, label: str) -> str:
    diff_text = make_diff(buggy, fixed)

    prompt = f"""You are a senior programming tutor and code reviewer.
Be faithful to the provided code and diff. Do NOT invent extra context.
If uncertain, say "Based on the diff...".

Bug type (predicted by classifier): {label}

[DIFF]
{diff_text}

[BUGGY CODE]
{buggy}

[FIXED CODE]
{fixed}

Return EXACTLY this format:

1) Summary (1–2 lines):
- ...

2) Why it's buggy (2–4 bullets):
- ...

3) How the fix works (2–4 bullets):
- ...

4) Learning tip (1 bullet):
- ...
"""

    messages = [
        {"role": "system", "content": "You are a precise, helpful programming tutor."},
        {"role": "user", "content": prompt},
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(text, return_tensors="pt", truncation=True).to(model.device)

    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,  # deterministic (best for research)
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id,
        )

    gen_tokens = out[0][inputs["input_ids"].shape[-1]:]
    return tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

# RUN
print("Generating explanations...")
diffs = []
explanations = []

for idx, row in df.iterrows():
    buggy = str(row["buggy_code"])
    fixed = str(row["fixed_code"])
    label = str(row["predicted_label"])

    diffs.append(make_diff(buggy, fixed))
    explanations.append(explain(buggy, fixed, label))
    print(f"Done {idx + 1}/{len(df)}")

df["diff_text"] = diffs
df["llm_explanation"] = explanations

print(f"Saving to {OUTPUT_CSV} ...")
df.to_csv(OUTPUT_CSV, index=False)
print("Done.")
