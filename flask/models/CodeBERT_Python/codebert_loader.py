import os
import json
import torch
import torch.nn as nn
import traceback
from transformers import AutoTokenizer, AutoModel


class BugDetectionModel(nn.Module):
    
    # Must mirror the exact architecture used during training (CodeBERT.py).
    # encoder -> CLS pooling -> dropout -> linear(768, 2)
    
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


class CodeBERTModel:
    def __init__(self):
        print("Loading CodeBERT Model...")

        # Model lives alongside this file
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        model_abs_path = os.path.join(self.base_dir, "fine_tuned_model")

        # Load configuration
        self.max_length = 384  # Matches training script
        print(f"Using max_length: {self.max_length}")

        # True only when the fine-tuned state dict was actually loaded
        self.weights_loaded = False

        try:
            self.device = torch.device("mps") if torch.backends.mps.is_available() else (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
            print(f"Inference Device: {self.device}")

            # Load tokenizer from saved directory
            if os.path.exists(model_abs_path):
                print(f"Loading Fine-Tuned CodeBERT from {model_abs_path}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_abs_path)
            else:
                print(f"WARNING: Model not found at {model_abs_path}. Using Base CodeBERT tokenizer.")
                self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")

            # Build the model architecture (downloads base encoder weights)
            self.model = BugDetectionModel("microsoft/codebert-base")

            # Load the fine-tuned state dict on top
            weights_path = os.path.join(model_abs_path, "pytorch_model.bin")
            if os.path.exists(weights_path):
                state_dict = torch.load(weights_path, map_location=self.device, weights_only=True)
                self.model.load_state_dict(state_dict)
                self.weights_loaded = True
                print(f"Loaded fine-tuned weights from {weights_path}")
            else:
                print(f"WARNING: pytorch_model.bin not found at {weights_path}. Using base weights only.")

            # Load deployment policy (threshold)
            self.threshold = 0.494  # default
            policy_path = os.path.join(model_abs_path, "deployment_policy.json")
            if os.path.exists(policy_path):
                with open(policy_path) as f:
                    policy = json.load(f)
                    self.threshold = policy.get("decision_threshold", 0.494)
                    print(f"Decision threshold: {self.threshold}")

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
        # Predict if code is buggy (1) or clean (0).
        # Returns: (prediction, probability_buggy, logits)
        if self.model is None:
            print("Model is not loaded.")
            # Neutral probability: must not read as a confident "clean" verdict
            return 0, 0.5, torch.tensor([0.0, 0.0])

        encoded = self.tokenize(code)
        input_ids = encoded["input_ids"].to(self.device)
        attention_mask = encoded["attention_mask"].to(self.device)

        with torch.no_grad():
            logits = self.model(
                input_ids=input_ids,
                attention_mask=attention_mask
            )

        probs = torch.softmax(logits, dim=1)
        prob_buggy = probs[0, 1].item()  # probability of being buggy
        prediction = 1 if prob_buggy >= self.threshold else 0

        return prediction, prob_buggy, logits.cpu()
