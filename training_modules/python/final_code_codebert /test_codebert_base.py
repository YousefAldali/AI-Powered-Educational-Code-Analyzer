import argparse
import os
import sys
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F


def load_model(device: str):
    """Load base CodeBERT with a random classification head (no fine-tuning)."""
    model_name = "microsoft/codebert-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        problem_type="single_label_classification",
    )
    model.to(device)
    model.eval()
    return tokenizer, model


def predict(code: str, tokenizer, model, device: str):
    inputs = tokenizer(
        code,
        max_length=384,
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    ).to(device)
    with torch.no_grad():
        logits = model(**inputs).logits.squeeze(0)
        probs = F.softmax(logits, dim=-1)
    buggy_prob = probs[1].item()
    label = "buggy" if buggy_prob >= 0.5 else "clean"
    return {
        "logits": logits.cpu().tolist(),
        "prob_buggy": buggy_prob,
        "label": label,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Quick check: run base CodeBERT on a single snippet or file."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--code", type=str, help="Raw code string (use quotes).")
    group.add_argument("--file", type=str, help="Path to a .py (or any text) file to classify.")
    args = parser.parse_args()

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"Using device: {device}")

    tokenizer, model = load_model(device)

    if args.code:
        code = args.code
    else:
        if not os.path.isfile(args.file):
            sys.exit(f"File not found: {args.file}")
        with open(args.file, "r", encoding="utf-8") as f:
            code = f.read()

    result = predict(code, tokenizer, model, device)

    print(f"\nLabel          : {result['label']}")
    print(f"Buggy prob.    : {result['prob_buggy']:.4f}")
    print(f"Logits (clean, buggy): {result['logits']}")


if __name__ == "__main__":
    main()
