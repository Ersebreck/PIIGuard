"""Evalúa la calidad de detect_llm (precision/recall/F1) contra eval/dataset.py.

Uso: cd src && python -m eval.run_eval   (requiere Ollama corriendo local)
"""
import tempfile

from ai.detect_graph import detect_llm
from eval.dataset import CASES


def _score(expected: set, got: set) -> dict:
    tp = len(expected & got)
    fp = len(got - expected)
    fn = len(expected - got)
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def run():
    totals = {"tp": 0, "fp": 0, "fn": 0}
    with tempfile.NamedTemporaryFile(suffix=".sqlite") as f:
        for case in CASES:
            verified, _timings = detect_llm(case["text"], job_id=case["id"], db_path=f.name)
            got = {(m["type"], m["value"]) for m in verified}
            score = _score(case["expected"], got)
            for k in ("tp", "fp", "fn"):
                totals[k] += score[k]

            status = "OK" if score["fp"] == 0 and score["fn"] == 0 else "MISS"
            print(f"[{status}] {case['id']}: precision={score['precision']:.2f} recall={score['recall']:.2f}")
            if score["fp"] or score["fn"]:
                print(f"    esperado:   {case['expected']}")
                print(f"    detectado:  {got}")

    p = totals["tp"] / (totals["tp"] + totals["fp"]) if (totals["tp"] + totals["fp"]) else 1.0
    r = totals["tp"] / (totals["tp"] + totals["fn"]) if (totals["tp"] + totals["fn"]) else 1.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    print(f"\nTOTAL: precision={p:.2f} recall={r:.2f} f1={f1:.2f} (tp={totals['tp']} fp={totals['fp']} fn={totals['fn']})")


if __name__ == "__main__":
    run()
