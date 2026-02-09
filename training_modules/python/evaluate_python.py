import os
import torch
import pandas as pd
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    average_precision_score,
    roc_auc_score,
    precision_recall_curve,
)

MODEL_DIR = "trained_model_augmented"
TEST_DATA = "../../flask/data/raw/python/augmented_test_set.csv"
if not os.path.exists(TEST_DATA):
    TEST_DATA = "flask/data/raw/python/augmented_test_set.csv"


def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def pick_model_path(model_dir: str) -> str:
    # Priority:
    #   1) best_ap
    #   2) checkpoint-last
    #   3) latest checkpoint-<n>
    #   4) model_dir
    if not os.path.exists(model_dir):
        return model_dir

    best_ap = os.path.join(model_dir, "best_ap")
    if os.path.isdir(best_ap):
        return best_ap

    last_ckpt = os.path.join(model_dir, "checkpoint-last")
    if os.path.isdir(last_ckpt):
        return last_ckpt

    checkpoints = [d for d in os.listdir(model_dir) if d.startswith("checkpoint-")]
    numbered = []
    for d in checkpoints:
        try:
            n = int(d.split("-")[1])
            numbered.append((n, d))
        except Exception:
            pass

    if numbered:
        numbered.sort(key=lambda x: x[0])
        return os.path.join(model_dir, numbered[-1][1])

    return model_dir


class CodeDataset(Dataset):
    def __init__(self, texts, labels, ids, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.ids = ids
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer.encode_plus(
            str(self.texts[idx]),
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "labels": torch.tensor(int(self.labels[idx]), dtype=torch.long),
            "id": torch.tensor(int(self.ids[idx]), dtype=torch.long),
        }


def plot_precision_recall_curve(trues, probs_buggy, ap, output_dir="results", title_suffix="Python"):
    os.makedirs(output_dir, exist_ok=True)

    try:
        import matplotlib.pyplot as plt

        precision, recall, _ = precision_recall_curve(trues, probs_buggy)

        plt.figure(figsize=(7, 6))
        plt.plot(
            recall,
            precision,
            linewidth=2,
            label=f"AP = {ap:.4f}"
        )
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title(f"Precision–Recall Curve ({title_suffix})")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        path = os.path.join(
            output_dir,
            f"precision_recall_curve_{title_suffix.lower()}.png"
        )
        plt.savefig(path)
        plt.close()

        print(f"Saved Precision–Recall curve to {path}")

    except ImportError:
        print("Skipping Precision–Recall curve (matplotlib not installed).")


def perform_error_analysis(trues, preds, ids, probs_buggy, df_test, output_dir="results", title_suffix="Python"):
    print(f"\nPerforming detailed error analysis for {title_suffix}...")
    os.makedirs(output_dir, exist_ok=True)

    if len(df_test) != len(trues):
        print("Warning: df_test length mismatch. Skipping text export.")
        df_test = None

    # Confusion matrix plot
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        cm = confusion_matrix(trues, preds)
        plt.figure(figsize=(6, 5))
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Fixed", "Buggy"],
            yticklabels=["Fixed", "Buggy"]
        )
        plt.title(f"Confusion Matrix ({title_suffix})")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"confusion_matrix_{title_suffix.lower()}.png"))
        plt.close()
        print(f"Saved confusion matrix plot to {output_dir}")
    except ImportError:
        print("Skipping confusion matrix plot (matplotlib/seaborn not installed).")

    # Failed cases
    failed_indices = [i for i, (t, p) in enumerate(zip(trues, preds)) if t != p]
    if not failed_indices:
        print("No failed cases.")
        return

    failed_data = []
    for i in failed_indices:
        row = df_test.iloc[i] if df_test is not None else None
        text_snippet = ""
        if row is not None:
            text_snippet = str(row["text"])[:200].replace("\n", " ")

        failed_data.append({
            "id": ids[i],
            "true_label": trues[i],
            "pred_label": preds[i],
            "prob_buggy": round(float(probs_buggy[i]), 4),
            "text_snippet": text_snippet
        })

    df_failed = pd.DataFrame(failed_data)
    path = os.path.join(output_dir, f"failed_cases_{title_suffix.lower()}.csv")
    df_failed.to_csv(path, index=False)
    print(f"Saved {len(df_failed)} failed cases to {path}")


def main():
    print(f"Loading Test Data from {TEST_DATA}...")
    if not os.path.exists(TEST_DATA):
        print("Test data not found.")
        return

    df = pd.read_csv(TEST_DATA)
    if len(df) == 0:
        print("Test CSV is empty.")
        return

    required = {"text", "label", "id"}
    if not required.issubset(df.columns):
        print(f"Missing columns. Found: {list(df.columns)}")
        return

    print(f"Found {len(df)} test samples.")
    print("Label counts:", df["label"].value_counts().to_dict())

    model_path = pick_model_path(MODEL_DIR)
    print(f"Loading Model from {model_path}...")

    model = RobertaForSequenceClassification.from_pretrained(model_path)
    tokenizer = RobertaTokenizer.from_pretrained(model_path)

    device = get_device()
    model.to(device)
    model.eval()
    print(f"Using device: {device}")

    ds = CodeDataset(
        df["text"].to_numpy(),
        df["label"].to_numpy(),
        df["id"].to_numpy(),
        tokenizer,
        MAX_LEN,
    )

    loader = DataLoader(
        ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4 if device.type == "cuda" else 0,
        pin_memory=(device.type == "cuda"),
    )

    preds, trues, ids = [], [], []
    probs_buggy = []

    print("Evaluating...")
    with torch.no_grad():
        for b in tqdm(loader):
            ii = b["input_ids"].to(device)
            am = b["attention_mask"].to(device)
            lbl = b["labels"].to(device)
            row_ids = b["id"].to(device)

            out = model(input_ids=ii, attention_mask=am)
            logits = out.logits

            p = torch.argmax(logits, dim=1)
            prob1 = torch.softmax(logits, dim=1)[:, 1]

            preds.extend(p.cpu().numpy())
            trues.extend(lbl.cpu().numpy())
            ids.extend(row_ids.cpu().numpy())
            probs_buggy.extend(prob1.cpu().numpy())

    acc = accuracy_score(trues, preds)

    ap = None
    auroc = None
    if len(set(trues)) == 2:
        ap = average_precision_score(trues, probs_buggy)
        auroc = roc_auc_score(trues, probs_buggy)

    print(f"\nPython Test Accuracy: {acc:.4f}")
    if ap is not None:
        print(f"Python Test AP (PR-AUC): {ap:.4f}")
        print(f"Python Test AUROC: {auroc:.4f}")
        plot_precision_recall_curve(trues, probs_buggy, ap)
    else:
        print("Python Test AP / AUROC: N/A")

    print("\nClassification Report:")
    print(classification_report(trues, preds, target_names=["Fixed", "Buggy"], digits=4))

    print("\nConfusion Matrix:")
    print(confusion_matrix(trues, preds))

    perform_error_analysis(trues, preds, ids, probs_buggy, df)

    print("\n--- Failed Cases (First 10) ---")
    shown = 0
    for i in range(len(preds)):
        if preds[i] != trues[i]:
            print(
                f"ID: {ids[i]} | True: {trues[i]} | Pred: {preds[i]} | P(Buggy): {probs_buggy[i]:.4f}"
            )
            shown += 1
            if shown >= 10:
                break


if __name__ == "__main__":
    main()
