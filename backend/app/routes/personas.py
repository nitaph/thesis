from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import PersonaRequest, PersonaResponse, PersonaPayload
from app.services.personas import personas_for_participant

router = APIRouter()

@router.post("/persona-profile", response_model=PersonaResponse)
async def persona_profile(req: PersonaRequest, session: AsyncSession = Depends(get_session)):
    personas = await personas_for_participant(req.participantId, session)
    return PersonaResponse(
        participantId=req.participantId,
        personas=[PersonaPayload(**p) for p in personas],
    )
