from yxa342.flask.models.CodeBERT.codebert_loader import CodeBERTModel

class CodeClassifier:
    def __init__(self):
        self.model = CodeBERTModel()

    def classify(self, code: str):
        pred, logits = self.model.predict(code)
        label = "buggy" if pred == 1 else "clean"

        return {
            "label": label,
            "raw_prediction": pred,
            "logits": logits.tolist()
        }
