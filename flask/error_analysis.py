import os
import pandas as pd
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification

def run_error_analysis():
    print("Running Error Analysis on Test Set...")
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(base_dir, 'data', 'splits', 'test.csv')
    model_path = os.path.join(base_dir, 'models', 'codebert_finetuned')
    report_dir = os.path.join(base_dir, 'reports', 'error_analysis')
    os.makedirs(report_dir, exist_ok=True)

    # Load Data
    df = pd.read_csv(test_path)
    df['text'] = df['text'].astype(str).fillna('')
    targets = df['label'].tolist()
    texts = df['text'].tolist()
    ids = df['id'].tolist()

    # Load Model
    if not os.path.exists(model_path):
        print("Error: Fine-tuned model not found.")
        return

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Loading model from {model_path} on {device}...")
    tokenizer = RobertaTokenizer.from_pretrained(model_path)
    model = RobertaForSequenceClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()

    # Predict
    preds = []
    print("Predicting...")
    with torch.no_grad():
        for code in texts:
            inputs = tokenizer(code, return_tensors="pt", truncation=True, padding=True, max_length=128)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            outputs = model(**inputs)
            pred = torch.argmax(outputs.logits, dim=1).item()
            preds.append(pred)

    # Analyze Errors
    errors = []
    for i in range(len(preds)):
        if preds[i] != targets[i]:
            errors.append({
                'id': ids[i],
                'label': targets[i],
                'prediction': preds[i],
                'length': len(texts[i]),
                'code_snippet': texts[i][:200] + "..." if len(texts[i]) > 200 else texts[i]
            })

    # Save Report
    error_df = pd.DataFrame(errors)
    csv_path = os.path.join(report_dir, 'failed_samples.csv')
    error_df.to_csv(csv_path, index=False)
    
    print(f"Analysis Complete.")
    print(f"Total Test Samples: {len(preds)}")
    print(f"Total Errors: {len(errors)}")
    print(f"Accuracy: {1 - len(errors)/len(preds):.2%}")
    print(f"Detailed error report saved to: {csv_path}")

if __name__ == "__main__":
    run_error_analysis()
