import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import RobertaTokenizer, RobertaForSequenceClassification
from torch.optim import AdamW
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import random

# Set seed for reproducibility
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(42)

# Configuration
BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 2e-5
MAX_LEN = 128
MODEL_NAME = "microsoft/codebert-base"

def load_data(split_name):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, 'data', 'splits', f'{split_name}.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data split not found: {path}. Run prepare_data.py first.")
    
    df = pd.read_csv(path)
    # Ensure all text is string
    df['text'] = df['text'].astype(str).fillna('')
    return df['text'].tolist(), df['label'].tolist()

class CodeDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

def train_epoch(model, data_loader, optimizer, device, scheduler=None):
    model = model.train()
    losses = []
    correct_predictions = 0

    for d in data_loader:
        input_ids = d["input_ids"].to(device)
        attention_mask = d["attention_mask"].to(device)
        labels = d["labels"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss
        logits = outputs.logits
        _, preds = torch.max(logits, dim=1)
        correct_predictions += torch.sum(preds == labels)
        losses.append(loss.item())

        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    return correct_predictions.float() / len(data_loader.dataset), np.mean(losses)

def eval_model(model, data_loader, device):
    model = model.eval()
    losses = []
    correct_predictions = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for d in data_loader:
            input_ids = d["input_ids"].to(device)
            attention_mask = d["attention_mask"].to(device)
            labels = d["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            loss = outputs.loss
            logits = outputs.logits
            _, preds = torch.max(logits, dim=1)
            correct_predictions += torch.sum(preds == labels)
            losses.append(loss.item())
            
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    return correct_predictions.float() / len(data_loader.dataset), np.mean(losses), all_labels, all_preds

def main():
    # Setup device
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    
    print("\nCodeBERT Training Script\n")
    print(f"Using device: {device}\n")
    
    # Load data
    print("Loading data...")
    X_train, y_train = load_data('train')
    X_val, y_val = load_data('val')
    print(f"  Train samples: {len(X_train)}")
    print(f"  Val samples: {len(X_val)}")
    
    # Initialize model
    print("\nInitializing CodeBERT...")
    tokenizer = RobertaTokenizer.from_pretrained(MODEL_NAME)
    model = RobertaForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        problem_type="single_label_classification"
    )
    model = model.to(device)
    
    # Create datasets
    train_dataset = CodeDataset(X_train, y_train, tokenizer, MAX_LEN)
    val_dataset = CodeDataset(X_val, y_val, tokenizer, MAX_LEN)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)
    
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    
    # Training loop
    print("\nStarting training...\n")
    best_accuracy = 0
    best_model_state = None
    
    for epoch in range(EPOCHS):
        print(f"Epoch {epoch + 1}/{EPOCHS}")
        
        # Train
        model.train()
        train_acc, train_loss = train_epoch(model, train_loader, optimizer, device)
        
        # Validate
        model.eval()
        val_acc, val_loss, val_labels, val_preds = eval_model(model, val_loader, device)
        
        print(f"  Train loss: {train_loss:.4f}, accuracy: {train_acc:.4f}")
        print(f"  Val loss:   {val_loss:.4f}, accuracy: {val_acc:.4f}")
        
        # Save best model
        if val_acc > best_accuracy:
            print("  --> Validation accuracy improved. Saving model...")
            best_accuracy = val_acc
            best_model_state = model.state_dict()
    
    # Save final model
    print("\nTraining complete!")
    print(f"Best validation accuracy: {best_accuracy:.2%}")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_save_path = os.path.join(base_dir, "models", "codebert_finetuned")
    os.makedirs(model_save_path, exist_ok=True)
    
    model.load_state_dict(best_model_state)
    model.save_pretrained(model_save_path)
    tokenizer.save_pretrained(model_save_path)
    
    print(f"Model saved to: {model_save_path}")
    
    # Final evaluation
    print("\nClassification report (best model on validation set):")
    print(classification_report(val_labels, val_preds, target_names=['Clean', 'Buggy']))

if __name__ == "__main__":
    main()
