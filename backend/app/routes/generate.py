from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from app.db import get_session
from app.schemas import GenerateRequest, GenerateResponse, SingleResponse
from app.services.llm import generate_four
from app.models import CachedResponse
from app.services.personas import personas_for_participant

router = APIRouter()

@router.post("/generate-responses", response_model=GenerateResponse)
async def generate_responses(req: GenerateRequest, session: AsyncSession = Depends(get_session)):
    # build the 4 personas (baseline/mirror/comp/creative)
    personas = await personas_for_participant(req.participantId, session)

    # call LLM for the 4 conditions
    results = await generate_four(
        personas=personas,
        participant_id=req.participantId,
        task_id=req.taskId,
        style=req.taskStyle,
        prompt_text=req.promptText,
    )

    # ⬇️ persist each response
    rows = [{
        "participant_id": req.participantId,
        "task_id": req.taskId,
        "condition": r["condition"],
        "response_id": r["responseId"],
        "prompt_text": req.promptText,
        "text": r["text"],
        "model": r["model"],
        "tokens_in": r["tokensIn"],
        "tokens_out": r["tokensOut"],
        "latency_ms": r["generationTimeMs"],
        "system_prompt": r["systemPrompt"],
        "user_prompt":   r["userPrompt"],
    } for r in results]

    if rows:
        await session.execute(insert(CachedResponse), rows)
        await session.commit()

    return GenerateResponse(
        participantId=req.participantId,
        taskId=req.taskId,
        responses=[SingleResponse(**r) for r in results],
    )
