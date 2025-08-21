from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import SQLModel, Field


class MoodEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    mood_score: int = Field(ge=1, le=10, index=True)
    note: Optional[str] = Field(default=None)


class JournalEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    title: str
    content: str


# Request/response schemas
class MoodEntryCreate(BaseModel):
    mood_score: int = PydanticField(ge=1, le=10)
    note: Optional[str] = None


class MoodEntryRead(BaseModel):
    id: int
    created_at: datetime
    mood_score: int
    note: Optional[str]


class MoodEntryUpdate(BaseModel):
    mood_score: Optional[int] = PydanticField(default=None, ge=1, le=10)
    note: Optional[str] = None


class JournalEntryCreate(BaseModel):
    title: str
    content: str


class JournalEntryRead(BaseModel):
    id: int
    created_at: datetime
    title: str
    content: str


class JournalEntryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = None


class ChatResponse(BaseModel):
    reply: str
    suggestions: list[str]
    used_model: str
    safety_notice: str


class ResourceItem(BaseModel):
    name: str
    country: str
    phone: str | None = None
    url: str | None = None
    notes: str | None = None


