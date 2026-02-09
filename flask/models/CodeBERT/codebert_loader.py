import os
import sys
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
        self.max_length = 256  # Matches Augmented Training
        print(f"Using max_length: {self.max_length}")

        # Import config from base_dir (flask/models)
        try:
            sys.path.append(self.base_dir) 
            from codebert_config import CONFIG
            config_model_path = CONFIG.get("model_path", "")
        except ImportError as e:
            print(f"Warning: Could not load codebert_config.py: {e}")
            config_model_path = ""

        # Resolve path
        if config_model_path:
            model_abs_path = os.path.abspath(os.path.join(self.base_dir, config_model_path))
        else:
            model_abs_path = os.path.join(self.base_dir, "CodeBERT", "fine_tuned_model")

        if os.path.exists(model_abs_path):
            print(f"Loading Fine-Tuned CodeBERT from {model_abs_path}")
            model_path = model_abs_path
        else:
            print(f"WARNING: Model not found at {model_abs_path}. Using Base CodeBERT.")
            model_path = "microsoft/codebert-base"

        try:
            self.device = torch.device("mps") if torch.backends.mps.is_available() else (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
            print(f"Inference Device: {self.device}")

            # Load tokenizer
            self.tokenizer = RobertaTokenizer.from_pretrained(model_path)

            # Load model with classification head (2 labels: buggy / clean)
            self.model = RobertaForSequenceClassification.from_pretrained(
                model_path,
                num_labels=2
            )
            self.model.to(self.device)
            self.model.eval()
            print("CodeBERT Loaded Successfully")
        except Exception as e:
            print(f"Error loading CodeBERT: {e}")
            traceback.print_exc()
            self.model = None

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
        input_ids = encoded["input_ids"].to(self.device)
        attention_mask = encoded["attention_mask"].to(self.device)

        with torch.no_grad():
            output = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

        logits = output.logits
        prediction = torch.argmax(logits, dim=1).item()

        return prediction, logits.cpu()
