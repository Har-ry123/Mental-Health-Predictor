from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from ..models import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])


SYSTEM_PROMPT = (
    "You are a supportive, empathetic mental health companion. "
    "Provide brief, validating responses (4-7 sentences), suggest 1-2 gentle next steps, and when appropriate, a simple grounding/breathing exercise. "
    "Maintain a non-judgmental tone, avoid medical diagnoses, and always include a short reminder that you're not a replacement for professional help. "
    "If the user expresses intent to harm self or others, urge them to contact local emergency services or a crisis hotline immediately."
)


def _fallback_reply(user_message: str) -> ChatResponse:
    normalized = user_message.lower().strip()
    empathy = (
        "I hear you—thank you for sharing this with me. It sounds like you're dealing with a lot right now."
    )
    simple_tool = (
        "Try a 60-second grounding: notice 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste."
    )
    suggestions: List[str] = [
        "Take three slow breaths (4 in, 4 hold, 6 out)",
        "Write down one worry and one thing you can control today",
    ]
    crisis_note = (
        "If you're in immediate danger or considering self-harm, please contact local emergency services or your regional crisis line right now."
    )
    reply = f"{empathy} {simple_tool} {crisis_note}"
    return ChatResponse(
        reply=reply,
        suggestions=suggestions,
        used_model="fallback",
        safety_notice="This is not medical advice; consider speaking with a licensed professional.",
    )


def _openai_reply(req: ChatRequest) -> ChatResponse:
    # Lazy import to avoid dependency issues if key not set
    from openai import OpenAI

    client = OpenAI()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if req.history:
        for m in req.history:
            if m.role in {"user", "assistant"} and m.content:
                messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": req.message})

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=400,
    )
    reply_text = completion.choices[0].message.content or "I'm here with you."

    suggestions = [
        "Try a short grounding or breathing exercise",
        "Write what you’re feeling for 2 minutes without editing",
        "Drink some water and step outside for fresh air",
    ]

    return ChatResponse(
        reply=reply_text.strip(),
        suggestions=suggestions,
        used_model=model,
        safety_notice=(
            "I'm an AI companion, not a substitute for professional care. If you're in crisis, call your local emergency number or a crisis hotline."
        ),
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_reply(req.message)
    try:
        return _openai_reply(req)
    except Exception:
        # Safety fallback on any API failure
        return _fallback_reply(req.message)


