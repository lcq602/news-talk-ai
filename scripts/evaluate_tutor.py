"""Benchmark model corrections against hand-labeled example categories.

This needs real API configuration. No fake-model score is treated as quality.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path

from app.main import ask_model

ROOT = Path(__file__).resolve().parent.parent


def classify(expected: set[str], predicted: set[str], optional: bool) -> dict[str, int]:
    # Multi-label category-level heuristic, not accuracy of exact rewriting.
    if optional and not predicted:
        return {"matched": 1, "missed": 0, "unexpected": 0, "clean": 0, "false_positive": 0}
    if not expected:
        return {"matched": 0, "missed": 0, "unexpected": len(predicted), "clean": int(not predicted), "false_positive": int(bool(predicted))}
    return {
        "matched": int(bool(expected & predicted)),
        "missed": int(not bool(expected & predicted)),
        "unexpected": len(predicted - expected),
        "clean": 0,
        "false_positive": 0,
    }


async def run(limit: int | None) -> dict:
    cases = json.loads((ROOT / "evaluation/cases.json").read_text(encoding="utf-8"))
    cases = cases[:limit] if limit else cases
    totals: Counter[str] = Counter()
    details = []
    for case in cases:
        try:
            result = await ask_model([
                {"role": "user", "content": "Please review this learner message, correct it, and reply about the passage: " + case["text"]}
            ])
            predicted = {item.type for item in result.corrections}
            metrics = classify(set(case["expect"]), predicted, case.get("optional", False))
            totals.update(metrics)
            details.append({
                "id": case["id"], "input": case["text"],
                "expected_types": case["expect"], "predicted_types": sorted(predicted),
                "corrections": [c.model_dump() for c in result.corrections], **metrics
            })
            print(f'{case["id"]}: expected={case["expect"]} predicted={sorted(predicted)}')
        except Exception as exc:
            totals["api_or_format_failures"] += 1
            details.append({"id": case["id"], "error": str(exc)})
            print(f'{case["id"]}: ERROR {type(exc).__name__}')
    return {
        "note": "Heuristic category-level benchmark. Human review required to confirm each correction and optional case.",
        "total": len(cases), "metrics": dict(totals), "details": details
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Evaluate only the first N cases")
    parser.add_argument("--output", default="evaluation/results.local.json")
    args = parser.parse_args()
    report = asyncio.run(run(args.limit))
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RESULTS:", report["metrics"])
    print("Saved to", args.output)


if __name__ == "__main__":
    main()
