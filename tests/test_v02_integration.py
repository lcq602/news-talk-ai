from fastapi.testclient import TestClient
from app import main


def test_comprehension_discussion_and_recurring_error(monkeypatch):
    calls = []

    async def fake(messages):
        calls.append(messages)
        return main.TutorResponse(
            reply_en="I see your point.", polished_version="AI can help shops.",
            corrections=[main.Correction(original="can helps", suggested="can help", type="grammar", explanation_zh="情态动词后用原形")],
            useful_phrases=[], follow_up_en="Why do you think so?"
        )

    monkeypatch.setattr(main, "ask_model", fake)
    with TestClient(main.app) as client:
        opening = client.post("/api/session")
        assert opening.status_code == 200
        sid = opening.json()["session_id"]
        assert opening.json()["feedback"]["phase"] == "comprehension"
        assert "COMPREHENSION CHECK" in calls[0][0]["content"]
        a = client.post("/api/chat", json={"session_id": sid, "message": "AI can helps."})
        assert a.status_code == 200
        assert a.json()["phase"] == "comprehension"
        assert a.json()["focus_tip"] is None
        b = client.post("/api/chat", json={"session_id": sid, "message": "Maya can helps."})
        assert b.status_code == 200
        assert b.json()["phase"] == "discussion"
        assert "grammar" in b.json()["focus_tip"]
        assert "second comprehension response" in calls[2][-2]["content"]
        c = client.post("/api/chat", json={"session_id": sid, "message": "AI can helps."})
        assert c.status_code == 200
        assert c.json()["phase"] == "discussion"
        assert c.json()["focus_tip"] is None
        assert "RECURRING PRACTICE TARGET" in calls[3][-2]["content"]
        assert client.delete("/api/session/" + sid).status_code == 200


def test_upstream_failure_does_not_advance_state(monkeypatch):
    from fastapi import HTTPException
    state = {"fail": False}

    async def fake(messages):
        if state["fail"]:
            raise HTTPException(status_code=502, detail="provider failed")
        return main.TutorResponse(
            reply_en="Hi", polished_version="", corrections=[],
            useful_phrases=[], follow_up_en="What happened?"
        )

    monkeypatch.setattr(main, "ask_model", fake)
    with TestClient(main.app) as client:
        sid = client.post("/api/session").json()["session_id"]
        state["fail"] = True
        assert client.post("/api/chat", json={"session_id": sid, "message": "Hello"}).status_code == 502
        assert main.PRACTICE[sid].completed_answers == 0
        assert sid not in main.SESSION_BUSY
        state["fail"] = False
        assert client.post("/api/chat", json={"session_id": sid, "message": "Hello"}).status_code == 200
        assert main.PRACTICE[sid].completed_answers == 1
        client.delete("/api/session/" + sid)
