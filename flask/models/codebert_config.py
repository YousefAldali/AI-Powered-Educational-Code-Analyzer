# CodeBERT Defect Detection — Final Model Configuration

# Model Architecture:
# - Base Model: microsoft/codebert-base
# - Parameters: ~125M
# - Architecture: RoBERTa-based transformer with 12 layers
# - Custom head: CLS pooling -> dropout(0.2) -> Linear(768, 2)

# Training Hyperparameters (Final):
# - Learning Rate: 5e-6
# - Batch Size: 128
# - Epochs: 20 (early stopped at epoch 18, best at epoch 14)
# - Max Sequence Length: 384 tokens
# - Optimizer: AdamW (weight_decay=0.01)
# - LR Schedule: cosine with warmup (6%)
# - Loss: Focal Loss (gamma=2.0, alpha=1.0)

# Overfitting Prevention:
# 1. Dropout 0.2
# 2. Focal Loss (down-weights easy examples)
# 3. Early Stopping on Macro-F1 (patience=4)
# 4. ID-based train/val/test split (anti-leakage)

# Task:
# - Input: single code snippet
# - Output: 0 = Clean Code, 1 = Buggy Code
# - Training data: 1.2M unique pairs -> ~2.4M single snippets

# Results (locked test set, threshold from validation):
# - Macro-F1: 0.6727
# - AUC-ROC: 0.7659
# - AP: 0.7755
# - Accuracy: 67.29%

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
    "learning_rate": 5e-6,
    "batch_size": 128,
    "num_epochs": 20,
    "early_stopped_at": 18,
    "best_epoch": 14,
    "max_length": 384,
    "random_seed": 42,

    # Optimizer Configuration
    "optimizer": "AdamW",
    "weight_decay": 0.01,
    "warmup_ratio": 0.06,
    "max_grad_norm": 1.0,
    "lr_schedule": "cosine",
    "loss": "Focal Loss (gamma=2.0, alpha=1.0)",

    # Regularization
    "dropout": 0.2,
    "early_stopping": True,
    "early_stopping_metric": "macro_f1",
    "early_stopping_patience": 4,

    # Tokenization
    "tokenizer": "AutoTokenizer (RobertaTokenizerFast)",
    "vocab_size": 50265,
    "truncation": True,
    "padding": "max_length",

    # Task
    "task": "defect_detection",
    "num_labels": 2,
    "label_0": "Clean Code",
    "label_1": "Buggy Code",

    # Data
    "dataset": "ultimate_combined_dataset_pairs_v5.csv",
    "total_pairs": 1208301,
    "split_method": "ID-based (70/15/15)",
    "split_train": 792857,
    "split_val": 169898,
    "split_test": 169899,
    "dataset_sources": [
        "CTSSB (814,416 pairs)",
        "Defectors (202,804 pairs)",
        "Synthetic (183,000 pairs across 20+ bug types)",
        "CTSSB Augmented (6,622 pairs)",
        "PyVul (1,474 pairs)",
    ],

    # Results (locked test set)
    "test_macro_f1": 0.6727,
    "test_accuracy": 0.6729,
    "test_auc": 0.7659,
    "test_ap": 0.7755,
    "test_clean_recall": 0.6978,
    "test_buggy_recall": 0.6480,
    "threshold": 0.494,
    "threshold_source": "validation (not test)",

    # Hardware
    "training_device": "NVIDIA RTX 5090 (32GB)",
    "inference_device": "mps/cpu",
    "precision": "bf16",

    # Notes
    "notes": [
        "Single-snippet defect detection (not pair matching)",
        "Final version: Focal Loss + 1.2M dataset + ID-based split",
        "Threshold selected on validation by max Macro-F1",
        "Early stopped at epoch 18 (best at epoch 14, patience 4 on Macro-F1)",
        "Python training complete — Java and C# to follow",
    ]
}

if __name__ == "__main__":
    import os
    output_path = os.path.join(os.path.dirname(__file__), "codebert_config.json")
    with open(output_path, 'w') as f:
        json.dump(CONFIG, f, indent=2)
    print(f"Configuration saved to: {output_path}")
