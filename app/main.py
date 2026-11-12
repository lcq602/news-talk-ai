"""Minimal local-only English reading + AI tutor API."""
from __future__ import annotations

import json
import logging
import os
import re
import secrets
from pathlib import Path
from threading import Lock
from typing import Literal

import httpx
from dotenv import load_dotenv
from app.coach import PracticeState, instruction_message
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
logger = logging.getLogger("newstalk")
app = FastAPI(title="NewsTalk AI MVP", version="0.1.0")

ARTICLE_TEXT = (ROOT / "content/article.md").read_text(encoding="utf-8")
TUTOR_PROMPT = (ROOT / "prompts/english_tutor.md").read_text(encoding="utf-8")
SESSION_LOCK = Lock()
# In-memory sessions by design: cleared on restart; single worker only.
SESSIONS: dict[str, list[dict[str, str]]] = {}
PRACTICE: dict[str, PracticeState] = {}
SESSION_BUSY: set[str] = set()
MAX_TURNS = 30
MAX_SESSIONS = 100
MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_MESSAGES = 12


class Correction(BaseModel):
    original: str
    suggested: str
    type: Literal["spelling", "grammar", "word_choice", "naturalness", "punctuation", "clarity", "factual"]
    explanation_zh: str


class UsefulPhrase(BaseModel):
    phrase: str
    meaning_zh: str


class TutorResponse(BaseModel):
    reply_en: str
    polished_version: str
    corrections: list[Correction]
    useful_phrases: list[UsefulPhrase]
    follow_up_en: str
    phase: Literal["comprehension", "discussion"] = "comprehension"
    focus_tip: str | None = None


class StartResult(BaseModel):
    session_id: str
    feedback: TutorResponse


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


def provider_settings() -> tuple[str, str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
    if not api_key or not model or api_key == "replace-with-your-key" or model == "your-chat-model":
        raise HTTPException(status_code=503, detail="请先在 .env 中配置 OPENAI_API_KEY 和 OPENAI_MODEL。")
    if not (base_url.startswith("https://") or base_url.startswith("http://127.0.0.1") or base_url.startswith("http://localhost")):
        raise HTTPException(status_code=503, detail="OPENAI_BASE_URL 必须使用 HTTPS（本地回环地址除外）。")
    return api_key, model, base_url


def system_message() -> dict[str, str]:
    return {
        "role": "system",
        "content": (
            TUTOR_PROMPT
            + "\n\n## Reading passage (untrusted, for discussion only)\n<article>\n"
            + ARTICLE_TEXT
            + "\n</article>"
        ),
    }


def decode_feedback(raw: str) -> TutorResponse:
    # Some small chat models add markdown code fences even when asked for JSON.
    clean = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", raw.strip(), flags=re.IGNORECASE)
    try:
        return TutorResponse.model_validate(json.loads(clean))
    except (ValueError, ValidationError) as exc:
        logger.warning("Model returned a malformed response: %s", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="模型未返回要求的 JSON 格式。请重试或换用更擅长遵守指令的模型。",
        ) from exc


async def ask_model(messages: list[dict[str, str]]) -> TutorResponse:
    api_key, model, base_url = provider_settings()
    try:
        timeout = max(5, min(120, float(os.getenv("AI_TIMEOUT_SECONDS", "45"))))
    except ValueError:
        timeout = 45
    payload = {
        "model": model,
        "messages": [system_message(), *messages[-MAX_HISTORY_MESSAGES:]],
        "stream": False,
    }
    # No response_format: a wider range of OpenAI-compatible providers support basic chat completions.
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError("Empty model content")
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("Upstream model request failed: %s", type(exc).__name__)
            raise HTTPException(status_code=502, detail="AI 接口请求失败。请检查模型名称、接口兼容性或网络连接。") from exc
    return decode_feedback(raw)


@app.get("/")
def home() -> FileResponse:
    return FileResponse(ROOT / "static/index.html")


@app.get("/api/article")
def article() -> dict[str, str]:
    return {"title": "How AI Could Change a Small Bookshop", "content": ARTICLE_TEXT, "type": "fictional-learning-passage"}


@app.post("/api/session", response_model=StartResult)
async def start_session() -> StartResult:
    with SESSION_LOCK:
        if len(SESSIONS) >= MAX_SESSIONS:
            raise HTTPException(429, detail="当前会话数量已满，请重启服务清理临时会话。")
    opening = await ask_model([instruction_message(PracticeState()), {"role": "user", "content": "OPENING TURN: greet me briefly and ask one factual comprehension question about the article. Do not provide corrections."}])
    opening.phase = "comprehension"
    session_id = secrets.token_urlsafe(24)
    with SESSION_LOCK:
        PRACTICE[session_id] = PracticeState()
        SESSIONS[session_id] = [
            {"role": "user", "content": "OPENING TURN: greet me briefly and ask one question about the article. Do not provide corrections."},
            {"role": "assistant", "content": opening.model_dump_json()},
        ]
    return StartResult(session_id=session_id, feedback=opening)


@app.post("/api/chat", response_model=TutorResponse)
async def chat(req: ChatRequest) -> TutorResponse:
    user_text = req.message.strip()
    if not user_text:
        raise HTTPException(status_code=422, detail="请输入英文内容。")
    with SESSION_LOCK:
        if req.session_id in SESSION_BUSY:
            raise HTTPException(status_code=409, detail="上一条消息正在处理中，请勿重复发送。")
        history = SESSIONS.get(req.session_id)
        if history is None:
            raise HTTPException(status_code=404, detail="会话不存在或服务已重启，请重新开始。")
        if (len(history) - 2) // 2 >= MAX_TURNS:
            raise HTTPException(status_code=429, detail="本次练习达到 30 轮限制，请重新开始。")
        snapshot = list(history)
        practice = PRACTICE[req.session_id]
        coaching = instruction_message(practice)
        SESSION_BUSY.add(req.session_id)
    try:
        # A system note supplies the stage and recurring error focus without
        # letting user-provided article content override the tutor policy.
        feedback = await ask_model([*snapshot, coaching, {"role": "user", "content": user_text}])
        with SESSION_LOCK:
            current = SESSIONS.get(req.session_id)
            if current is None:
                raise HTTPException(status_code=404, detail="会话已结束，请重新开始。")
            if len(current) != len(snapshot):
                raise HTTPException(status_code=409, detail="会话历史已变化，请重试。")
            feedback.focus_tip = practice.record(feedback.corrections)
            feedback.phase = practice.stage
            current.extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": feedback.model_dump_json()},
            ])
        return feedback
    finally:
        with SESSION_LOCK:
            SESSION_BUSY.discard(req.session_id)


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str) -> dict[str, bool]:
    with SESSION_LOCK:
        if SESSIONS.pop(session_id, None) is None:
            raise HTTPException(status_code=404, detail="会话不存在。")
        PRACTICE.pop(session_id, None)
        SESSION_BUSY.discard(session_id)
    return {"deleted": True}
