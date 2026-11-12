import asyncio
import json
import httpx
from app import main


def test_openai_compatible_http_contract(monkeypatch):
    expected = main.TutorResponse(
        reply_en="A useful idea.", polished_version="AI can help.",
        corrections=[main.Correction(original="can helps", suggested="can help", type="grammar", explanation_zh="情态动词后用原形")],
        useful_phrases=[], follow_up_en="Why?"
    )
    calls = []
    def handle(request: httpx.Request):
        calls.append((request.url.path, request.headers.get("Authorization"), json.loads(request.content)))
        return httpx.Response(200, json={"choices": [{"message": {"content": expected.model_dump_json()}}]})

    original = httpx.AsyncClient
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    monkeypatch.setenv("OPENAI_API_KEY", "key-for-test")
    monkeypatch.setenv("OPENAI_MODEL", "demo-model")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.invalid/v1")

    result = asyncio.run(main.ask_model([{"role": "user", "content": "AI can helps."}]))
    assert result.corrections[0].suggested == "can help"
    path, auth, payload = calls[0]
    assert path == "/v1/chat/completions"
    assert auth == "Bearer key-for-test"
    assert payload["model"] == "demo-model"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][-1]["content"] == "AI can helps."
