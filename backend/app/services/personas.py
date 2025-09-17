from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Big5Score

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
CREATIVE_PROFILE_PATH = PROMPTS_DIR / "creative_profile.json"

def _clamp(v: int, lo: int = 10, hi: int = 50) -> int:
    return max(lo, min(hi, v))

def _mid() -> Dict[str, int]:
    return {"O": 30, "C": 30, "E": 30, "A": 30, "N": 30}

def _read_creative_profile() -> Dict:
    import json
    if CREATIVE_PROFILE_PATH.exists():
        data = json.loads(CREATIVE_PROFILE_PATH.read_text(encoding="utf-8"))
        persona = data.get("persona") or data
        guidance = data.get("guidance") or (
            "Favor unconventional, high-variance ideas; tolerate ambiguity; "
            "deprioritize rigid planning."
        )
        version = data.get("version", "v1")
        return {"persona": persona, "guidance": guidance, "version": version}
    return {
        "persona": {"O": 48, "C": 28, "E": 44, "A": 40, "N": 18},
        "guidance": "Favor unconventional, high-variance ideas; tolerate ambiguity; deprioritize rigid planning.",
        "version": "v1",
    }

async def _load_user_scores(participant_id: str, session: AsyncSession) -> Optional[Dict[str, int]]:
    stmt = select(Big5Score).where(Big5Score.participant_id == participant_id).order_by(Big5Score.created_at.desc())
    res = await session.execute(stmt)
    row = res.scalars().first()
    if not row:
        return None
    return {"O": row.O, "C": row.C, "E": row.E, "A": row.A, "N": row.N}

async def personas_for_participant(participant_id: str, session: AsyncSession) -> List[Dict]:
    scores = await _load_user_scores(participant_id, session)
    base = _mid()
    mirror = scores or base
    comp = {k: _clamp(60 - v) for k, v in mirror.items()}
    creative = _read_creative_profile()
    version = "v1"
    return [
        {"type": "baseline", "persona": base,   "guidance": None,                 "version": version},
        {"type": "mirror",   "persona": mirror, "guidance": None,                 "version": version},
        {"type": "comp",     "persona": comp,   "guidance": None,                 "version": version},
        {"type": "creative", "persona": creative["persona"], "guidance": creative["guidance"], "version": creative["version"]},
    ]
