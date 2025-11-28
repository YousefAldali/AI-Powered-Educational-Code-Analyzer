from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch

class CodeBERTModel:
    def __init__(self):
        print("Loading CodeBERT Model...")

        # Load tokenizer
        self.tokenizer = RobertaTokenizer.from_pretrained(
            "microsoft/codebert-base"
        )

        # Load model with classification head (2 labels: buggy / clean)
        self.model = RobertaForSequenceClassification.from_pretrained(
            "microsoft/codebert-base",
            num_labels=2
        )

        self.model.eval()
        print("CodeBERT Loaded Successfully")

    def tokenize(self, code: str):
        return self.tokenizer(
            code,
            padding="max_length",
            max_length=512,   # TOKEN LIMIT!
            truncation=True,
            return_tensors="pt"
        )

    def predict(self, code: str):
        encoded = self.tokenize(code)

        with torch.no_grad():
            output = self.model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"]
            )

        logits = output.logits
        prediction = torch.argmax(logits, dim=1).item()

        return prediction, logits
