import os
import json
import torch
import traceback
from transformers import RobertaTokenizer, RobertaForSequenceClassification

class CodeBERTModel:
    def __init__(self):
        print("Loading CodeBERT Model...")
        
        # Base directory (flask/models)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load configuration
        self.config = self._load_config()
        self.max_length = self.config.get("max_length", 512)
        print(f"Using max_length: {self.max_length}")

        # Check for fine-tuned model
        finetuned_path = os.path.join(self.base_dir, "codebert_finetuned")
        
        if os.path.exists(finetuned_path):
            model_path = finetuned_path
            print(f"Loading Fine-Tuned CodeBERT from {model_path}")
        else:
            model_path = "microsoft/codebert-base"
            print("Loading Base CodeBERT (Not Fine-Tuned)")

        try:
            # Load tokenizer
            self.tokenizer = RobertaTokenizer.from_pretrained(model_path)

            # Load model with classification head (2 labels: buggy / clean)
            self.model = RobertaForSequenceClassification.from_pretrained(
                model_path,
                num_labels=2
            )

            self.model.eval()
            print("CodeBERT Loaded Successfully")
        except Exception as e:
            print(f"Error loading CodeBERT: {e}")
            traceback.print_exc()
            self.model = None

    def _load_config(self):
        config_path = os.path.join(self.base_dir, "codebert_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load codebert_config.json: {e}")
        return {}

    def tokenize(self, code: str):
        return self.tokenizer(
            code,
            padding="max_length",
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        )

    def predict(self, code: str):
        if self.model is None:
            print("Model is not loaded.")
            return 0, torch.tensor([0.0, 0.0])

        encoded = self.tokenize(code)

        with torch.no_grad():
            output = self.model(
                input_ids=encoded["input_ids"],
                attention_mask=encoded["attention_mask"]
            )

        logits = output.logits
        prediction = torch.argmax(logits, dim=1).item()

        return prediction, logits
