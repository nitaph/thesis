from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_session
from app.models import Participant, Big5Score
from app.schemas import ScoreRequest, Big5Out
from app.services.big5 import score_ipip50


router = APIRouter()

@router.post("/score-big5", response_model=Big5Out)
async def score_big5(payload: ScoreRequest, session: AsyncSession = Depends(get_session)):
    # upsert participant
    participant = await session.get(Participant, payload.participantId)
    if not participant:
        participant = Participant(participant_id=payload.participantId)
        session.add(participant)

    try:
        sums = score_ipip50(payload.answers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    session.add(Big5Score(
        participant_id=payload.participantId, O=sums["O"], C=sums["C"], E=sums["E"], A=sums["A"], N=sums["N"]
    ))
    await session.commit()
    return sums
