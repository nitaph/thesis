# app/routes/ratings.py
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from app.db import get_session
from app.schemas import SubmitRatingsRequest, SlotRating
from app.models import Rating

router = APIRouter()

@router.post("/submit-ratings")
async def submit_ratings(payload: SubmitRatingsRequest, session: AsyncSession = Depends(get_session)):
    # insert rows
    values = []
    for r in payload.ratings:
        # r is SlotRating (pydantic model). Use attributes, not dict keys.
        values.append({
            "participant_id": payload.participantId,
            "task_id": payload.taskId,
            "condition": r.condition,
            "response_id": r.responseId,
            "usefulness": r.usefulness,
            "novelty": r.novelty,
            "shown_slot": r.slot,               # <-- map slot -> shown_slot (DB column)
        })
    if values:
        await session.execute(insert(Rating), values)
        await session.commit()

    # mirror to Embedded-Data-like shape
    # ensure 1..4 ordering
    ordered = sorted(payload.ratings, key=lambda x: x.slot)
    return {
        "participantId": payload.participantId,
        "taskId": payload.taskId,
        "taskIdxInBlock": payload.taskIdxInBlock,
        "ConditionSlot": [r.condition for r in ordered],
        "RespId":        [r.responseId for r in ordered],
        "Usefulness":    [r.usefulness for r in ordered],
        "Novelty":       [r.novelty for r in ordered],
        "GenMs":         [r.generationTimeMs for r in ordered],
    }
