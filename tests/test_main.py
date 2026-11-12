import json

import pytest
from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def sample_feedback() -> main.TutorResponse:
    return main.TutorResponse(
        reply_en="That's an interesting idea.",
        polished_version="I think AI can help small shops.",
        corrections=[
            main.Correction(
                original="AI can helps",
                suggested="AI can help",
                type="grammar",
                explanation_zh="情态动词 can 后用动词原形。",
            )
        ],
        useful_phrases=[main.UsefulPhrase(phrase="save time", meaning_zh="节省时间")],
        follow_up_en="What about customers who prefer human advice?",
    )


def test_article_contains_original_passage():
    response = client.get("/api/article")
    assert response.status_code == 200
    assert "Maya" in response.json()["content"]
    assert response.json()["type"] == "fictional-learning-passage"


def test_requires_api_configuration(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    with pytest.raises(main.HTTPException) as exc:
        main.provider_settings()
    assert exc.value.status_code == 503


def test_feedback_contract_and_cleanup():
    value = sample_feedback()
    parsed = main.decode_feedback("```json\n" + value.model_dump_json() + "\n```")
    assert parsed.corrections[0].type == "grammar"
    with pytest.raises(main.HTTPException) as exc:
        main.decode_feedback("not valid json")
    assert exc.value.status_code == 502


def test_full_session_flow(monkeypatch):
    async def fake_model(messages):
        return sample_feedback()

    monkeypatch.setattr(main, "ask_model", fake_model)
    start = client.post("/api/session")
    assert start.status_code == 200
    sid = start.json()["session_id"]
    assert len(sid) >= 20
    result = client.post("/api/chat", json={"session_id": sid, "message": "AI can helps small shops."})
    assert result.status_code == 200
    assert result.json()["corrections"][0]["suggested"] == "AI can help"
    assert client.delete("/api/session/" + sid).json() == {"deleted": True}
    assert client.post("/api/chat", json={"session_id": sid, "message": "Hello"}).status_code == 404


def test_empty_message_rejected():
    result = client.post("/api/chat", json={"session_id": "missing", "message": ""})
    assert result.status_code == 422


def test_message_limit():
    result = client.post("/api/chat", json={"session_id": "missing", "message": "x" * 2001})
    assert result.status_code == 422
