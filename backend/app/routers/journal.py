from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import desc
from sqlmodel import Session, select

from ..db import get_session
from ..models import (
    JournalEntry,
    JournalEntryCreate,
    JournalEntryRead,
    JournalEntryUpdate,
)


router = APIRouter(prefix="/journal", tags=["journal"])


@router.get("/", response_model=List[JournalEntryRead])
def list_journal(session: Session = Depends(get_session)) -> List[JournalEntry]:
    statement = select(JournalEntry).order_by(desc(JournalEntry.created_at))
    return list(session.exec(statement))


@router.post("/", response_model=JournalEntryRead)
def create_entry(payload: JournalEntryCreate, session: Session = Depends(get_session)) -> JournalEntry:
    entry = JournalEntry(title=payload.title, content=payload.content)
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.get("/{entry_id}", response_model=JournalEntryRead)
def get_entry(entry_id: int, session: Session = Depends(get_session)) -> JournalEntry:
    entry = session.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.patch("/{entry_id}", response_model=JournalEntryRead)
def update_entry(entry_id: int, payload: JournalEntryUpdate, session: Session = Depends(get_session)) -> JournalEntry:
    entry = session.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if payload.title is not None:
        entry.title = payload.title
    if payload.content is not None:
        entry.content = payload.content
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204, response_class=Response)
def delete_entry(entry_id: int, session: Session = Depends(get_session)) -> Response:
    entry = session.get(JournalEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    session.delete(entry)
    session.commit()
    return Response(status_code=204)


