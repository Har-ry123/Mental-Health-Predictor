from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..models import ResourceItem


router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/", response_model=List[ResourceItem])
def get_resources() -> List[ResourceItem]:
    return [
        ResourceItem(
            name="988 Suicide & Crisis Lifeline",
            country="US",
            phone="988",
            url="https://988lifeline.org/",
            notes="24/7 free and confidential support",
        ),
        ResourceItem(
            name="Samaritans",
            country="UK & ROI",
            phone="116 123",
            url="https://www.samaritans.org/",
            notes="24/7 helpline",
        ),
        ResourceItem(
            name="Lifeline Australia",
            country="AU",
            phone="13 11 14",
            url="https://www.lifeline.org.au/",
            notes="24/7 crisis support",
        ),
        ResourceItem(
            name="Kiran Mental Health Helpline",
            country="IN",
            phone="1800-599-0019",
            url="https://www.mohfw.gov.in/",
            notes="National helpline",
        ),
        ResourceItem(
            name="Your local emergency number",
            country="Global",
            phone="",
            url="",
            notes="If you are in immediate danger, call emergency services",
        ),
    ]


