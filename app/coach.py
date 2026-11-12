"""Deterministic learning flow; the LLM does the language assessment.

This module never asserts that a model correction is true. It only tracks
returned correction types and asks the tutor to revisit recurring issues.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from typing import Any

STAGES = ("comprehension", "discussion")
CORRECTION_TYPES = (
    "spelling", "grammar", "word_choice", "naturalness", "punctuation",
    "clarity", "factual",
)


@dataclass
class PracticeState:
    completed_answers: int = 0
    error_counts: Counter[str] = field(default_factory=Counter)
    review_issued_for: set[str] = field(default_factory=set

    @property
    def stage(self) -> str:
        # Two short comprehension turns; this is a checkpoint, NOT a pass/fail test.
        return "comprehension" if self.completed_answers < 2 else "discussion"

    @property
    def recurring_types(self) -> list[str]:
        # Factual discrepancies are not English errors, and style preferences
        # should not trigger remedial drills.
        return sorted(
            kind for kind, count in self.error_counts.items()
            if count >= 2 and kind in {"spelling", "grammar", "word_choice", "clarity"}
        )

    def coaching_instruction(self) -> str:
        if self.stage == "comprehension":
            phase = (
                "STAGE: COMPREHENSION CHECK. Ask a single concrete question about a "
                "fact, sequence, or cause explicitly described in the supplied passage. "
                "Help the learner locate evidence. Do not ask a generic opinion question yet. "
                "Two questions are a warm-up, NOT proof of understanding."
            )
        else:
            phase = (
                "STAGE: DISCUSSION. Ask one open-ended question about the passage's "
                "implications, the learner's view, a comparison, or a real-life example. "
                "Connect follow-up questions to the learner's actual answer."
            )
        recurring = self.recurring_types
        if recurring:
            phase += (
                " RECURRING PRACTICE TARGET: The tutor previously flagged "
                + ", ".join(recurring)
                + ". Briefly invite the learner to produce ONE fresh sentence practicing "
                "the most relevant pattern, ideally as part of the article discussion. "
                "Do not assert these previous corrections are infallible; if challenged, recheck them. "
                "Do not replace the natural reply with a worksheet."
            )
        return phase

    def record(self, corrections: list[Any]) -> str | None:
        self.completed_answers += 1
        for correction in corrections:
            kind = correction.type if hasattr(correction, "type") else correction.get("type")
            if kind in CORRECTION_TYPES:
                self.error_counts[kind] += 1
        recurring = self.recurring_types
        for kind in recurring:
            if kind not in self.review_issued_for:
                self.review_issued_for.add(kind)
                return (
                    f"你在本次对话中至少两次出现 {kind} 类建议。"
                    "接下来 AI 会尝试结合文章给你一次巩固练习。"
                    "注意：这是模型的分类统计，不代表所有纠错都一定正确。"
                )
        return None


def instruction_message(state: PracticeState) -> dict[str, str]:
    return {"role": "system", "content": state.coaching_instruction()}
