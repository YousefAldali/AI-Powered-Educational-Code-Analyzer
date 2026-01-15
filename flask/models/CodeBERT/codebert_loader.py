import os
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification

class CodeBERTModel:
    def __init__(self):
        print("Loading CodeBERT Model...")
        
        # Check for fine-tuned model
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        finetuned_path = os.path.join(base_dir, "codebert_finetuned")
        
        if os.path.exists(finetuned_path):
            model_path = finetuned_path
            print(f"Loading Fine-Tuned CodeBERT from {model_path}")
        else:
            model_path = "microsoft/codebert-base"
            print("Loading Base CodeBERT (Not Fine-Tuned)")

        # Load tokenizer
        self.tokenizer = RobertaTokenizer.from_pretrained(model_path)

        # Load model with classification head (2 labels: buggy / clean)
        self.model = RobertaForSequenceClassification.from_pretrained(
            model_path,
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
