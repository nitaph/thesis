from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.responses import StreamingResponse
from io import StringIO
import csv

from app.db import get_session
from app.models import CachedResponse, Rating, Big5Score

router = APIRouter()

def _to_csv(rows, header):
    def gen():
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(header); yield buf.getvalue(); buf.seek(0); buf.truncate(0)
        for row in rows:
            w.writerow(row); yield buf.getvalue(); buf.seek(0); buf.truncate(0)
    return gen()

@router.get("/export/generations.csv")
async def export_generations(session: AsyncSession = Depends(get_session)):
    q = select(
        CachedResponse.participant_id,
        CachedResponse.task_id,
        CachedResponse.condition,
        CachedResponse.response_id,
        CachedResponse.model,
        CachedResponse.tokens_in,
        CachedResponse.tokens_out,
        CachedResponse.latency_ms,
        CachedResponse.created_at,
        CachedResponse.system_prompt,
        CachedResponse.user_prompt,
        CachedResponse.prompt_text,
        CachedResponse.text,
    ).order_by(CachedResponse.id)
    rows = (await session.execute(q)).all()
    header = ["participant_id","task_id","condition","response_id","model",
              "tokens_in","tokens_out","latency_ms","created_at","prompt_text","text"]
    return StreamingResponse(_to_csv(rows, header),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=generations.csv"}
    )

@router.get("/export/ratings.csv")
async def export_ratings(session: AsyncSession = Depends(get_session)):
    q = select(
        Rating.participant_id, Rating.task_id, Rating.condition, Rating.response_id,
        Rating.usefulness, Rating.novelty, Rating.shown_slot, Rating.created_at
    ).order_by(Rating.id)
    rows = (await session.execute(q)).all()
    header = ["participant_id","task_id","condition","response_id",
              "usefulness","novelty","shown_slot","created_at"]
    return StreamingResponse(_to_csv(rows, header),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=ratings.csv"}
    )

@router.get("/export/big5_scores.csv")
async def export_big5(session: AsyncSession = Depends(get_session)):
    q = select(
        Big5Score.participant_id, Big5Score.O, Big5Score.C, Big5Score.E, Big5Score.A, Big5Score.N, Big5Score.created_at
    ).order_by(Big5Score.id)
    rows = (await session.execute(q)).all()
    header = ["participant_id","O","C","E","A","N","created_at"]
    return StreamingResponse(_to_csv(rows, header),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=big5_scores.csv"}
    )
