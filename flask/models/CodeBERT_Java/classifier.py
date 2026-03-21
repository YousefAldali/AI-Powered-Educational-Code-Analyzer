import re
from .codebert_loader import CodeBERTModelJava

# Thresholds for confidence gating (same as Python classifier)
BUGGY_THRESHOLD = 0.65
UNCERTAIN_THRESHOLD = 0.45

# If code is shorter than this, classify directly without chunking
SHORT_CODE_THRESHOLD = 1500


def _extract_java_methods(code: str):
    # Extract functions from Java source using brace counting.

    lines = code.splitlines(keepends=True)
    chunks = []

   
    method_pattern = re.compile(
        r'^\s*'
        r'(?:(?:public|private|protected)\s+)?'
        r'(?:(?:static|final|abstract|synchronized|native)\s+)*'
        r'(?:[\w<>\[\],\s]+?)\s+'      # return type
        r'(\w+)'                         # method name
        r'\s*\([^)]*\)'                  # parameters
        r'(?:\s*throws\s+[\w\s,]+)?'     # optional throws
        r'\s*\{'                         # opening brace
    )

    i = 0
    while i < len(lines):
        match = method_pattern.match(lines[i])
        if match:
            method_name = match.group(1)
            start_line = i

            # Count braces to find the end of the method
            brace_count = 0
            j = i
            found_end = False
            while j < len(lines):
                for ch in lines[j]:
                    if ch == '{':
                        brace_count += 1
                    elif ch == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            found_end = True
                            break
                if found_end:
                    break
                j += 1

            end_line = j + 1 if found_end else len(lines)
            snippet = "".join(lines[start_line:end_line]).strip()

            if len(snippet) > 5:
                chunks.append({
                    "name": method_name,
                    "code": snippet,
                    "lineno": start_line + 1,
                    "type": "method",
                })

            i = end_line
        else:
            i += 1

    return chunks if chunks else None


class JavaCodeClassifier:
    def __init__(self):
        self.model = CodeBERTModelJava()

    def classify(self, code: str):
        # Classify a single code snippet
        pred, prob_buggy, logits = self.model.predict(code)
        label = "buggy" if pred == 1 else "clean"

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

        # Large code split into methods
        chunks = _extract_java_methods(code)

        if not chunks:
            # Couldn't parse or no methods found classify whole file
            result = self.classify(code)
            result = self._apply_confidence_gating(result)
            result["method"] = "direct"
            result["flagged_functions"] = []
            result["total_functions"] = 0
            return result

        # Classify each method individually
        per_function_results = []
        confident_buggy = []
        uncertain_buggy = []

        for chunk in chunks:
            r = self.classify(chunk["code"])
            prob_buggy = r["probability_buggy"]

            if prob_buggy >= BUGGY_THRESHOLD:
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

        # Aggregate: file is buggy only if at least one method is confidently buggy
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
