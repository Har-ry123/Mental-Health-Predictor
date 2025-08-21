from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import desc
from sqlmodel import Session, select

from ..db import get_session
from ..models import MoodEntry, MoodEntryCreate, MoodEntryRead, MoodEntryUpdate


router = APIRouter(prefix="/moods", tags=["moods"])


@router.get("/", response_model=List[MoodEntryRead])
def list_moods(session: Session = Depends(get_session)) -> List[MoodEntry]:
    statement = select(MoodEntry).order_by(desc(MoodEntry.created_at))
    return list(session.exec(statement))


@router.post("/", response_model=MoodEntryRead)
def create_mood(payload: MoodEntryCreate, session: Session = Depends(get_session)) -> MoodEntry:
    entry = MoodEntry(mood_score=payload.mood_score, note=payload.note)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=MoodEntryRead)
def get_mood(entry_id: int, session: Session = Depends(get_session)) -> MoodEntry:
    entry = session.get(MoodEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Mood entry not found")
    return entry


@router.patch("/{entry_id}", response_model=MoodEntryRead)
def update_mood(entry_id: int, payload: MoodEntryUpdate, session: Session = Depends(get_session)) -> MoodEntry:
    entry = session.get(MoodEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Mood entry not found")
    if payload.mood_score is not None:
        entry.mood_score = payload.mood_score
    if payload.note is not None:
        entry.note = payload.note
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204, response_class=Response)
def delete_mood(entry_id: int, session: Session = Depends(get_session)) -> Response:
    entry = session.get(MoodEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Mood entry not found")
    session.delete(entry)
    session.commit()
    return Response(status_code=204)


