"""
CodeBERT Training Configuration

This file documents all hyperparameters used for training CodeBERT
to ensure reproducibility and transparency for academic evaluation.

Model Architecture:
- Base Model: microsoft/codebert-base
- Parameters: ~125M
- Architecture: RoBERTa-based transformer with 12 layers
- Hidden Size: 768
- Attention Heads: 12
- Pre-training: Trained on 6 programming languages (Python, Java, JavaScript, PHP, Ruby, Go)

Training Hyperparameters:
- Learning Rate: 2e-5 (typical for fine-tuning transformers)
- Batch Size: 8 (limited by GPU memory)
- Epochs: 3 (with early stopping based on validation accuracy)
- Max Sequence Length: 128 tokens
- Optimizer: AdamW (weight decay variant of Adam)
- Weight Decay: 0.01 (L2 regularization)
- Random Seed: 42

Overfitting Prevention:
1. Early Stopping: Save best model based on validation accuracy
2. Weight Decay: L2 regularization via AdamW optimizer
3. Dropout: Inherent in RoBERTa architecture (0.1 by default)
4. Data Split: Separate validation set for monitoring
5. Limited Epochs: Only 3 epochs to prevent overfitting on small dataset

Tokenization:
- Tokenizer: RoBERTa BPE (Byte-Pair Encoding)
- Special Tokens: [CLS], [SEP]
- Vocabulary Size: 50,265 tokens
- Truncation: Yes (max_length=128)
- Padding: To max_length

Hardware:
- Device: Apple Silicon MPS (Metal Performance Shaders) / CPU fallback
- Mixed Precision: Not used

Data Preprocessing:
- Input: Raw Python source code
- Labels: 0 = Clean, 1 = Buggy
- No additional preprocessing (CodeBERT handles raw code)

Notes:
- Conservative hyperparameters chosen to prevent overfitting
- 3 epochs sufficient given pre-trained weights
- Low batch size (8) due to memory constraints
- Could potentially improve with larger batch size and learning rate tuning
"""

import json

CONFIG = {
    # Model Configuration
    "model_name": "microsoft/codebert-base",
    "model_type": "RoBERTa-based Transformer",
    "num_parameters": "125M",
    "num_layers": 12,
    "hidden_size": 768,
    "num_attention_heads": 12,
    
    # Training Hyperparameters
    "learning_rate": 2e-5,
    "batch_size": 8,
    "num_epochs": 3,
    "max_length": 128,
    "random_seed": 42,
    
    # Optimizer Configuration
    "optimizer": "AdamW",
    "weight_decay": 0.01,
    "adam_epsilon": 1e-8,
    
    # Regularization
    "dropout": 0.1,
    "early_stopping": True,
    "early_stopping_metric": "validation_accuracy",
    
    # Tokenization
    "tokenizer": "RoBERTa BPE",
    "vocab_size": 50265,
    "truncation": True,
    "padding": "max_length",
    
    # Data
    "num_labels": 2,
    "label_0": "Clean Code",
    "label_1": "Buggy Code",
    
    # Device
    "device": "mps/cpu",
    
    # Notes
    "notes": [
        "Conservative hyperparameters to prevent overfitting",
        "3 epochs sufficient with pre-trained weights",
        "Early stopping based on validation accuracy",
        "No hyperparameter tuning performed (future work)"
    ]
}

if __name__ == "__main__":
    # Save configuration to JSON
    import os
    output_path = os.path.join(os.path.dirname(__file__), "codebert_config.json")
    with open(output_path, 'w') as f:
        json.dump(CONFIG, f, indent=2)
    print(f"Configuration saved to: {output_path}")
