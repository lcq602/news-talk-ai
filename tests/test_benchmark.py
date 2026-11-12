import json
from pathlib import Path
from scripts.evaluate_tutor import classify


def test_dataset_has_adequate_coverage():
    data = json.loads((Path(__file__).resolve().parents[1] / "evaluation/cases.json").read_text(encoding="utf-8"))
    assert len(data) >= 40
    assert len({case["id"] for case in data}) == len(data)
    assert sum(not case["expect"] for case in data) >= 10
    assert {"grammar", "spelling", "word_choice", "naturalness", "clarity", "factual"} <= {t for case in data for t in case["expect"]}


def test_benchmark_scoring_does_not_call_valid_sentences_wrong():
    assert classify(set(), set(), False)["clean"] == 1
    assert classify(set(), {"grammar"}, False)["false_positive"] == 1
    assert classify({"naturalness"}, set(), True)["missed"] == 0
    assert classify({"grammar"}, {"grammar"}, False)["matched"] == 1
