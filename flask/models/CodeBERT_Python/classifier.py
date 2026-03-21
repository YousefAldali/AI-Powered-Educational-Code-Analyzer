import ast
import textwrap
from .codebert_loader import CodeBERTModel

# Thresholds for confidence gating
BUGGY_THRESHOLD = 0.65
UNCERTAIN_THRESHOLD = 0.45

# If code is shorter than this, classify it directly without chunking
SHORT_CODE_THRESHOLD = 1500  # ~40 lines


def _extract_functions(code: str):
    # Parse Python source into individual top-level functions and classes.
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # Can't parse — fall back to whole-file classification

    lines = code.splitlines(keepends=True)
    chunks = []
    
    # Extract context (only imports, not massive variable assignments)
    context_lines = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
            context_lines.append("".join(lines[start:end]))
    
    context_str = "".join(context_lines)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno - 1
            end = node.end_lineno if hasattr(node, "end_lineno") and node.end_lineno else start + 1
            snippet = "".join(lines[start:end])
            combined_code = context_str + "\n\n" + snippet.strip() if context_str else snippet.strip()
            chunks.append({
                "name": node.name,
                "code": combined_code.strip(),
                "lineno": node.lineno,
                "type": "function",
            })
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start = child.lineno - 1
                    end = child.end_lineno if hasattr(child, "end_lineno") and child.end_lineno else start + 1
                    snippet = "".join(lines[start:end])
                    combined_code = context_str + "\n\n" + snippet.strip() if context_str else snippet.strip()
                    chunks.append({
                        "name": f"{node.name}.{child.name}",
                        "code": combined_code.strip(),
                        "lineno": child.lineno,
                        "type": "method",
                    })

    return chunks if chunks else None


class CodeClassifier:
    def __init__(self):
        self.model = CodeBERTModel()

    def classify(self, code: str):
        # Classify a single code snippet 
        pred, prob_buggy, logits = self.model.predict(code)
        label = "buggy" if pred == 1 else "clean"

        # Confidence: how sure the model is about its prediction
        confidence = prob_buggy if pred == 1 else (1.0 - prob_buggy)

        return {
            "label": label,
            "raw_prediction": pred,
            "probability_buggy": round(prob_buggy, 4),
            "confidence": round(confidence, 4),
            "logits": logits.tolist()
        }

    def _apply_confidence_gating(self, result):
        # Apply confidence thresholds to avoid false positives from low-confidence predictions
        prob_buggy = result["probability_buggy"]
        if prob_buggy >= BUGGY_THRESHOLD:
            result["label"] = "buggy"
            result["confidence"] = prob_buggy
        elif prob_buggy >= UNCERTAIN_THRESHOLD:
            result["label"] = "uncertain"
            result["confidence"] = prob_buggy
        else:
            result["label"] = "clean"
            result["raw_prediction"] = 0
            result["confidence"] = 1.0 - prob_buggy
        return result

    def classify_smart(self, code: str):
        # Short code: classify directly with confidence gating
        if len(code) < SHORT_CODE_THRESHOLD:
            result = self.classify(code)
            result = self._apply_confidence_gating(result)
            result["method"] = "direct"
            result["flagged_functions"] = []
            result["total_functions"] = 0
            return result

        # Large code: try to split into functions
        chunks = _extract_functions(code)

        if not chunks:
            # Couldn't parse or no functions found — classify whole file with confidence filter
            result = self.classify(code)
            result = self._apply_confidence_gating(result)
            result["method"] = "direct"
            result["flagged_functions"] = []
            result["total_functions"] = 0
            return result

        # Classify each function individually
        per_function_results = []
        confident_buggy = []
        uncertain_buggy = []

        for chunk in chunks:
            r = self.classify(chunk["code"])
            prob_buggy = r["probability_buggy"]
            
            # Heuristic: Pure configuration/argument parsing functions lack control flow
            # CodeBERT often misclassifies these as buggy due to missing error handling.
            # If a function name strongly implies config/args and has high buggy probability,
            # we force it to uncertain to prevent false positives.
            is_config_func = any(x in chunk["name"].lower() for x in ["parse_args", "get_args", "config", "setup"])
            
            if prob_buggy >= BUGGY_THRESHOLD:
                if is_config_func:
                    label = "uncertain"
                    conf = prob_buggy
                else:
                    label = "buggy"
                    conf = prob_buggy
            elif prob_buggy >= UNCERTAIN_THRESHOLD:
                label = "uncertain"
                conf = prob_buggy
            else:
                label = "clean"
                conf = 1.0 - prob_buggy

            func_result = {
                "name": chunk["name"],
                "type": chunk["type"],
                "lineno": chunk["lineno"],
                "label": label,
                "confidence": conf,
                "probability_buggy": prob_buggy,
                "code": chunk["code"],
            }
            per_function_results.append(func_result)

            if label == "buggy":
                confident_buggy.append(func_result)
            elif label == "uncertain":
                uncertain_buggy.append(func_result)

        # Aggregate: file is buggy only if at least one function is confidently buggy
        if confident_buggy:
            worst = max(confident_buggy, key=lambda f: f["probability_buggy"])
            overall_label = "buggy"
            overall_prob_buggy = worst["probability_buggy"]
            overall_confidence = overall_prob_buggy
            flagged = confident_buggy
        elif uncertain_buggy:
            worst = max(uncertain_buggy, key=lambda f: f["probability_buggy"])
            overall_label = "uncertain"
            overall_prob_buggy = worst["probability_buggy"]
            overall_confidence = overall_prob_buggy
            flagged = uncertain_buggy
        else:
            # No confident buggy functions — report as clean
            overall_label = "clean"
            clean_probs = [f["probability_buggy"] for f in per_function_results]
            overall_prob_buggy = max(clean_probs) if clean_probs else 0.0
            overall_confidence = 1.0 - overall_prob_buggy
            flagged = []

        return {
            "label": overall_label,
            "raw_prediction": 1 if overall_label == "buggy" else 0,
            "probability_buggy": round(overall_prob_buggy, 4),
            "confidence": round(overall_confidence, 4),
            "logits": [],
            "method": "chunked",
            "flagged_functions": flagged,
            "total_functions": len(per_function_results),
        }
