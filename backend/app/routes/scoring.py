# app/routes/scoring.py
from fastapi import APIRouter, HTTPException
from app.schemas import ScoreRequest, Big5Out
from app.services.big5 import score_ipip50  # your existing scorer

router = APIRouter()

@router.post("/score-big5", response_model=Big5Out)
async def score_big5(payload: ScoreRequest):
    try:
        sums = score_ipip50(payload.answers)  # {'O':..,'C':..,'E':..,'A':..,'N':..}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    traits = {
        "trait_openness":          sums["O"],
        "trait_conscientiousness": sums["C"],
        "trait_extraversion":      sums["E"],
        "trait_agreeableness":     sums["A"],
        "trait_neuroticism":       sums["N"],
    }
    return {"traits": traits}
