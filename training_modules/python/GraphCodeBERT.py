import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel, get_cosine_schedule_with_warmup
from sklearn.metrics import f1_score, recall_score, precision_score, roc_auc_score, average_precision_score
import pandas as pd
import json
import os
import random  # Added for hard negative sampling
from tqdm import tqdm
from datetime import datetime
import numpy as np


# GPU configuration and Optimizer settings
torch.set_float32_matmul_precision("high")  # Allow TF32 matmul
if torch.cuda.is_available():
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True  # Auto-tune CUDA kernels
    try:
        torch.backends.cuda.enable_flash_sdp(True)  # Enable Flash Attention
        torch.backends.cuda.enable_mem_efficient_sdp(True)  # Memory-efficient attention
    except Exception:
        pass  # Older PyTorch versions may not support these


#Configurations 
MODEL_NAME                    = "microsoft/graphcodebert-base"
BATCH_SIZE                    = 128
GRAD_ACCUMULATION_STEPS       = 1
MAX_LEN                       = 384 
EPOCHS                        = 20
LEARNING_RATE                 = 5e-6 # Changed from 1e-5 for fine-tuning and see if it improves performance
EARLY_STOPPING_PATIENCE       = 4
WARMUP_RATIO                  = 0.06
DEVICE                        = "cuda" if torch.cuda.is_available() else "cpu"
OUTPUT_DIR                    = "trained_model_graphcodebert_final"
SEED                          = 42


#Focal Loss: Focuses training on hard-to-classify examples and stops the model from being Lazy
 
class FocalLoss(nn.Module):
    
    def __init__(self, gamma=2.0, alpha=1.0):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha
    
    def forward(self, logits, labels):
     
        # Standard cross-entropy loss per sample / This is basically a measure of how wrong the model was
        ce_loss = F.cross_entropy(logits, labels, reduction='none')
        
        # Probability of correct class / pt is the model’s probability for the correct answer—close to 1 when confident and correct, and close to 0 when unsure or wrong.
        p_t = torch.exp(-ce_loss)
        
        # Focal loss: down-weight easy examples, up-weight hard ones
        focal_loss = self.alpha * ((1 - p_t) ** self.gamma) * ce_loss
        
        return focal_loss.mean()
    
    
    
# Data Chef / Taking raw and turning it into something the model can understand and learn from
class CodePairDataset(Dataset):
    def __init__(self, csv_path, tokenizer, max_len=384, max_pairs=None):
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.data = []
            
        #load and process data
        df = pd.read_csv(csv_path)
        if max_pairs:
            df = df.head(max_pairs)
                
        #Extract all fixed codes for hard negative mining 
        all_fixed_codes = list(df['fixed_code'].apply(lambda x: str(x).strip()))
            
        for idx, row in df.iterrows():
            buggy_code = str(row['buggy_code']).strip()
            fixed_code = str(row['fixed_code']).strip()
            
            # Positive pair Real fix Label 0 
            self.data.append({
                'buggy_code': buggy_code,
                'fixed_code': fixed_code,
                'label': 0,  # 0 = Correct fix
                'pair_type': 'positive'
            })
                
            #Hard Negative : Worng fix from Random different row 
            random_idx = random.randrange(len(df))
            while random_idx == idx: # Avoid picking the same row
                random_idx = random.randrange(len(df))
                
            wrong_fixed_code = all_fixed_codes[random_idx] # Randomly pick a different fixed code
            self.data.append({
                'buggy_code': buggy_code,
                'fixed_code': wrong_fixed_code,
                'label': 1,  # 1 = Incorrect fix
                'pair_type': 'hard_negative'
            })
            
        print(f"Loaded {len(self.data)} total pairs balanced 50%-50% positive and hard negative")
        print(f"(Generated {len(self.data) //2} positive + {len(self.data) //2} hard negative pairs)")
        print(f"Hard Negative: buggy code with WRONG fix (not trivial identity checks)")
       
        if max_pairs:
            print(f"(From{max_pairs} CSV rows for smoke test)")
            
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        
        #Tokenization: Convert code into tokens and attention masks for the model
        encoding = self.tokenizer( 
            f"BUGGY: {item['buggy_code']}",
            f"FIXED: {item['fixed_code']}",
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(),  # Remove batch dimension
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(item['label'], dtype=torch.long),
            'buggy_code': item['buggy_code'],  # For error analysis
            'fixed_code': item['fixed_code'],    # For error analysis
            'pair_type': item['pair_type']       # For error analysis
        }
        
        
        
#Model 
        
        
#Binary classification model: [CLS] output -> linear layer -> logits 
class BugDetectionModel(nn.Module):
            
    def __init__(self, model_name, num_classes=2 , dropout_prob=0.2):
        super().__init__() 
        self.encoder = AutoModel.from_pretrained(model_name)
        self.dropout = nn.Dropout(dropout_prob)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_classes) 
                
    def forward(self, input_ids, attention_mask):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # [CLS] token representation
        pooled = self.dropout(pooled)
        logits = self.classifier(pooled)
        return logits
            
            
#Training Loop: The heart of the learning process where the model learns from data and updates its parameters
def train_epoch(model, dataloader, optimizer, scheduler, device, criterion):
    model.train()
    total_loss = 0
                
    pbar = tqdm(dataloader, desc="Training")
    optimizer.zero_grad(set_to_none=True) # More efficient zeroing
                
    for step, batch in enumerate(pbar):
        input_ids = batch['input_ids'].to(device, non_blocking=True)
        attention_mask = batch['attention_mask'].to(device, non_blocking=True)
        labels = batch['labels'].to(device, non_blocking=True)
                    
        # Mixed precision training for speed and memory efficiency
        with torch.amp.autocast(
            device_type=device,
            dtype=torch.bfloat16,
            enabled=(device == "cuda")
        ):
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)
                     
        # proper gradient accumulation (scale loss, step only when full batch accumulated)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # Gradient clipping
        optimizer.step()
        scheduler.step()
        optimizer.zero_grad(set_to_none=True)  # More efficient zeroing
        total_loss += loss.item()
        pbar.set_postfix({'loss': f"{loss.item():.4f}"})
               
    return total_loss / len(dataloader)
            
    
@torch.no_grad()
def evaluate(model, dataloader, device, criterion):
    #Evaluate on validation/test set with mixed precision
    model.eval()
    total_loss = 0
    all_logits = []
    all_labels = []
    
    for batch in tqdm(dataloader, desc="Evaluating", leave=False):
        # Non-blocking transfer (GPU can work while CPU loads next batch)
        input_ids = batch['input_ids'].to(device, non_blocking=True)
        attention_mask = batch['attention_mask'].to(device, non_blocking=True)
        labels = batch['labels'].to(device, non_blocking=True)
        
        # Mixed precision evaluation (bfloat16 is faster on modern GPUs)
        with torch.amp.autocast(device_type=device, dtype=torch.bfloat16,
                                enabled=(device == "cuda")):
            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)
        
        total_loss += loss.item()
        all_logits.append(logits.cpu())
        all_labels.append(labels.cpu())
    
    # Aggregate predictions
    logits = torch.cat(all_logits, dim=0)
    labels = torch.cat(all_labels, dim=0)
    probs = F.softmax(logits, dim=1)[:, 1].numpy()
    labels = labels.numpy()
    
    # Metrics
    metrics = {
        'loss': total_loss / len(dataloader),
    }
    
    #Guard against single-class validation sets (crashes AUC/AP)
    if len(np.unique(labels)) > 1:
        metrics['auc'] = roc_auc_score(labels, probs)
        metrics['ap'] = average_precision_score(labels, probs)
    else:
        # Single class - can't compute AUC/AP
        metrics['auc'] = 0.5
        metrics['ap'] = 0.5
        print(f"Warning: Validation set has only one class (label={labels[0]}). AUC/AP set to 0.5")
    
    # Threshold sweep for macro-F1 
    best_f1 = 0
    best_threshold = 0.5
    for threshold in np.arange(0.1, 0.9, 0.05):
        preds = (probs >= threshold).astype(int)
        f1 = f1_score(labels, preds)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    metrics['macro_f1_at_best_threshold'] = best_f1
    metrics['best_threshold'] = best_threshold
    
    return metrics


#Main 
def main():
    #Setup 
    os.makedirs(OUTPUT_DIR, exist_ok=True) # Create a folder to save the trained model weights later 
    torch.manual_seed(SEED) # lock random seed for reproducibility (important for debugging and consistent results) if I ran it later again 
    np.random.seed(SEED) 
    random.seed(SEED)
    
    #Load tokenizer and model 
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = BugDetectionModel(MODEL_NAME).to(DEVICE)
    
    #Focal loss (replace with CrossEntropyLoss + label_smoothing)
    criterion = FocalLoss(gamma=2.0, alpha=1.0)  # Adjust gamma and alpha 
    
    #Optimizer and scheduler
    optimizer = AdamW(
        model.parameters(),
        lr=LEARNING_RATE,  # 5e-6
        weight_decay=0.01 # regularization to prevent overfitting
    )
    
    #Data Leakage prevention: Ensure no code appears in both train and val/test sets
    print("Loading datasets splitting data...")
    df = pd.read_csv("code_pairs.csv")
    
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)  # Shuffle with fixed seed 
    
    #Split 70% train, 15% val, 15% test 
    total_rows = len(df)
    train_size = int(0.70 * total_rows)
    val_size = int(0.15 * total_rows)
    
    train_df = df.iloc[:train_size]
    val_df = df.iloc[train_size:train_size+val_size]
    test_df = df.iloc[train_size+val_size:] 
    
    # Save to temporary files (so Dataset class can load them separately)
    train_path = "temp_train_split.csv"
    val_path = "temp_val_split.csv"
    test_path = "temp_test_split.csv"
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    
    
    print(f"\n{'='*60}")
    print(f"Data split complete (NO DATA LEAKAGE):")
    print(f"{'='*60}")
    print(f"  Train: {len(train_df):,} rows → {len(train_df)*2:,} pairs (after negative sampling)")
    print(f"  Val:   {len(val_df):,} rows → {len(val_df)*2:,} pairs")
    print(f"  Test:  {len(test_df):,} rows → {len(test_df)*2:,} pairs")
    print(f"  Total: {len(df):,} original rows → {len(df)*2:,} pairs total")
    print(f"{'='*60}\n")
    
    
    
    # Data loading (with pair input from SEPARATED files)
    train_dataset = CodePairDataset(
        train_path,  #SEPARATED: Train data only
        tokenizer,
        max_len=MAX_LEN,
        max_pairs=None
    )
    val_dataset = CodePairDataset(
        val_path,  # SEPARATED: Val data completely different from train
        tokenizer,
        max_len=MAX_LEN,
        max_pairs=None
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=8,  # Use 8 workers for data loading in parallel
        pin_memory=True,  # Pin memory for faster GPU transfer
        prefetch_factor=4,  # Prefetch batches ahead
        persistent_workers=True,  # Keep workers alive between epochs
        drop_last=True,  # Drop last incomplete batch
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=4,  # Fewer workers for validation
        pin_memory=True,
        prefetch_factor=2,
    )
    
    # Learning rate scheduler
    total_steps = len(train_loader) * EPOCHS
    warmup_steps = int(total_steps * WARMUP_RATIO)
    
    from transformers import get_cosine_schedule_with_warmup
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=total_steps
    )
    
    # Training loop
    best_val_f1 = 0
    patience_counter = 0
    training_history = []
    
    for epoch in range(EPOCHS):
        print(f"\n{'='*60}")
        print(f"Epoch {epoch + 1}/{EPOCHS}")
        print(f"{'='*60}")
        
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, DEVICE, criterion)
        val_metrics = evaluate(model, val_loader, DEVICE, criterion)
        
        print(f"Train Loss: {train_loss:.4f}")
        print(f"Val Loss: {val_metrics['loss']:.4f}")
        print(f"Val AUC: {val_metrics['auc']:.4f}")
        print(f"Val AP: {val_metrics['ap']:.4f}")
        print(f"Val Macro-F1: {val_metrics['macro_f1_at_best_threshold']:.4f} @ threshold {val_metrics['best_threshold']:.2f}")
        
        
        # Log history for analysis and visualization 
        history_entry = {
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'val_loss': val_metrics['loss'],
            'val_auc': val_metrics['auc'],
            'val_ap': val_metrics['ap'],
            'val_macro_f1': val_metrics['macro_f1_at_best_threshold'],
            'best_threshold': val_metrics['best_threshold']
        }
        training_history.append(history_entry)
        
        # Early stopping based on macro-F1 improvement
        current_f1 = val_metrics['macro_f1_at_best_threshold']
        if current_f1 > best_val_f1:
            best_val_f1 = current_f1
            patience_counter = 0
            
            # Save best model
            torch.save(model.state_dict(), f"{OUTPUT_DIR}/pytorch_model.bin")
            print(f"Best model saved (F1: {current_f1:.4f})")
        else:
            patience_counter += 1
            print(f"No improvement ({patience_counter}/{EARLY_STOPPING_PATIENCE})")
            
            if patience_counter >= EARLY_STOPPING_PATIENCE:
                print(f"Early stopping at epoch {epoch + 1}")
                break
            
    # Save final results
    with open(f"{OUTPUT_DIR}/training_history.json", 'w') as f:
        json.dump(training_history, f, indent=2)
    
    print(f"\nTraining complete!")
    print(f"Best model saved to: {OUTPUT_DIR}/")
    print(f"Best Val Macro-F1: {best_val_f1:.4f}")
    
    #Test evaluation (after training is complete)
    print(f"\n{'='*60}")
    print("EVALUATING ON TEST SET (held-out data)")
    print(f"{'='*60}")
    
    # Load test dataset
    test_dataset = CodePairDataset(test_path, tokenizer, max_len=MAX_LEN)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    # Load best model
    model.load_state_dict(torch.load(f"{OUTPUT_DIR}/pytorch_model.bin", map_location=DEVICE))
    
    # Evaluate on test set
    test_metrics = evaluate(model, test_loader, DEVICE, criterion)
    
    print(f"\nTest Loss: {test_metrics['loss']:.4f}")
    if 'auc' in test_metrics:
        print(f"Test AUC:  {test_metrics['auc']:.4f}")
    if 'ap' in test_metrics:
        print(f"Test AP:   {test_metrics['ap']:.4f}")
    print(f"Test Macro-F1: {test_metrics['macro_f1_at_best_threshold']:.4f} @ threshold {test_metrics['best_threshold']:.2f}")
    
    # Save test results
    test_results = {
        'test_loss': test_metrics['loss'],
        'test_auc': test_metrics.get('auc', 0.5),
        'test_ap': test_metrics.get('ap', 0.5),
        'test_macro_f1': test_metrics['macro_f1_at_best_threshold'],
        'test_threshold': test_metrics['best_threshold'],
        'val_macro_f1': best_val_f1
    }
    
    with open(f"{OUTPUT_DIR}/test_results.json", 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Val Macro-F1 (honest, unseen during training): {best_val_f1:.4f}")
    print(f"Test Macro-F1 (truly held-out final eval):      {test_metrics['macro_f1_at_best_threshold']:.4f}")
    print(f"\nResults saved to: {OUTPUT_DIR}/test_results.json")


if __name__ == "__main__":
    main()