from app.coach import PracticeState, instruction_message


def test_staged_flow():
    state = PracticeState()
    assert state.stage == "comprehension"
    assert "fact" in instruction_message(state)["content"]
    state.record([])
    assert state.stage == "comprehension"
    state.record([])
    assert state.stage == "discussion"
    assert "open-ended" in instruction_message(state)["content"]


def test_repeated_errors_trigger_one_reminder():
    state = PracticeState()
    assert state.record([{"type": "grammar"}]) is None
    reminder = state.record([{"type": "grammar"}])
    assert reminder is not None
    assert "grammar" in reminder
    assert "RECURRING PRACTICE TARGET" in state.coaching_instruction()
    assert state.record([{"type": "grammar"}]) is None


def test_fact_and_style_do_not_trigger_grammar_drills():
    state = PracticeState()
    for _ in range(3):
        state.record([{"type": "factual"}, {"type": "naturalness"}])
    assert state.recurring_types == []
    assert "RECURRING PRACTICE TARGET" not in state.coaching_instruction()


def test_tracks_several_categories():
    state = PracticeState()
    state.record([{"type": "spelling"}, {"type": "word_choice"}])
    state.record([{"type": "word_choice"}, {"type": "spelling"}])
    assert state.recurring_types == ["spelling", "word_choice"]

def test_two_errors_same_category_in_single_message_is_not_recurring():
    state = PracticeState()
    assert state.record([{"type": "grammar"}, {"type": "grammar"}]) is None
    assert state.error_counts["grammar"] == 1
