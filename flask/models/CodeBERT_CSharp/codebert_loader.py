import os
import json
import torch
import torch.nn as nn
import traceback
from transformers import AutoTokenizer, AutoModel


# Must mirror the exact architecture used during training (same as Python & Java)
# encoder -> CLS pooling -> dropout -> linear(768, 2)
class BugDetectionModel(nn.Module):
    def __init__(self, model_name="microsoft/codebert-base", num_classes=2, dropout_prob=0.2):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout_prob)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_classes)

    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # CLS token
        pooled = self.dropout(pooled)
        return self.classifier(pooled)


class CodeBERTModelCSharp:
    def __init__(self):
        print("Loading C# CodeBERT Model...")

        # Model lives alongside this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(base_dir, "fine_tuned_model")

        # Max token length — matches training script (384)
        self.max_length = 384
        print(f"C# model max_length: {self.max_length}")

        # Default threshold (updated after training via deployment_policy.json)
        self.threshold = 0.5

        try:
            # Pick device
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
            print(f"C# Inference Device: {self.device}")

            # Load tokenizer from saved directory
            if os.path.exists(model_dir):
                print(f"Loading C# Fine-Tuned CodeBERT from {model_dir}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            else:
                print(f"WARNING: C# model not found at {model_dir}. Using base CodeBERT tokenizer.")
                self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

            # Build the model architecture (downloads base encoder weights)
            self.model = BugDetectionModel("microsoft/codebert-base")

            # Load the fine-tuned state dict on top
            weights_path = os.path.join(model_dir, "pytorch_model.bin")
            if os.path.exists(weights_path):
                state_dict = torch.load(weights_path, map_location=self.device, weights_only=True)
                self.model.load_state_dict(state_dict)
                print(f"Loaded fine-tuned weights from {weights_path}")
            else:
                print(f"WARNING: pytorch_model.bin not found at {weights_path}. Using base weights only.")

            # Load deployment policy (threshold)
            policy_path = os.path.join(model_dir, "deployment_policy.json")
            if os.path.exists(policy_path):
                with open(policy_path) as f:
                    policy = json.load(f)
                    self.threshold = policy.get("decision_threshold", 0.5)
                    print(f"C# decision threshold: {self.threshold}")

            self.model.to(self.device)
            self.model.eval()
            print("C# CodeBERT Loaded Successfully")

        except Exception as e:
            print(f"Error loading C# CodeBERT: {e}")
            traceback.print_exc()
            self.model = None

    def tokenize(self, code: str):
        return self.tokenizer(
            code,
            padding=True,
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        )

    def predict(self, code: str):
        # Returns: (prediction, probability_buggy, logits)
        if self.model is None:
            print("C# model is not loaded.")
            return 0, 0.0, torch.tensor([0.0, 0.0])

        encoded = self.tokenize(code)
        input_ids = encoded["input_ids"].to(self.device)
        attention_mask = encoded["attention_mask"].to(self.device)

        with torch.no_grad():
            logits = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

        probs = torch.softmax(logits, dim=1)
        prob_buggy = probs[0, 1].item()
        prediction = 1 if prob_buggy >= self.threshold else 0

        return prediction, prob_buggy, logits.cpu()
