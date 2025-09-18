# app/routes/generate.py
from fastapi import APIRouter, HTTPException
from app.schemas import TaskIn, TaskOut, OneText
from app.services.llm import generate_four
from pathlib import Path
import json

router = APIRouter()

# ----------------- helpers -----------------
def _clamp(v: int, lo: int = 10, hi: int = 50) -> int:
    return max(lo, min(hi, v))

def _read_creative_profile():
    p = Path(__file__).resolve().parents[1] / "prompts" / "creative_profile.json"
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return {"persona": data.get("persona", data), "guidance": data.get("guidance")}
    # default fallback persona if file missing
    return {"persona": {"O": 48, "C": 28, "E": 44, "A": 40, "N": 18}, "guidance": None}

# prefer to show a single text field to raters
_PREFERRED_FIELDS = ("narrative", "answer", "text", "idea", "output", "summary")

def _extract_text_from_json(s: str) -> str:
    """Return a single display string from the model's JSON output."""
    s = (s or "").strip()
    try:
        obj = json.loads(s)
    except Exception:
        # model didn't follow JSON (rare if response_format is used) — just return raw
        return s
    if isinstance(obj, dict):
        for k in _PREFERRED_FIELDS:
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        # fallback: compact whole JSON
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    # if it's a list or something else, compact it
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

# ----------------- route -----------------
@router.post("/generate-task", response_model=TaskOut)
async def generate_task(payload: TaskIn) -> TaskOut:
    try:
        # Build Big Five dict from Qualtrics fields
        mirror = {
            "O": payload.trait_openness,
            "C": payload.trait_conscientiousness,
            "E": payload.trait_extraversion,
            "A": payload.trait_agreeableness,
            "N": payload.trait_neuroticism,
        }
        comp = {k: _clamp(60 - v) for k, v in mirror.items()}
        creative = _read_creative_profile()

        personas = [
            {"type": "baseline", "persona": {"O": 30, "C": 30, "E": 30, "A": 30, "N": 30}, "guidance": None},
            {"type": "mirror",   "persona": mirror,   "guidance": None},
            {"type": "comp",     "persona": comp,     "guidance": None},
            {"type": "creative", "persona": creative["persona"], "guidance": creative.get("guidance")},
        ]

        # choose style family (A/B). Keep "A" unless you split by task blocks/arms.
        style = "A"
        prompt_text = payload.taskPrompt or payload.taskId

        # four independent generations (run concurrently inside generate_four)
        results = await generate_four(
            personas,
            payload.participantId,
            payload.taskId,
            style,
            prompt_text,
        )

        # map internal -> Qualtrics labels
        name_map = {
            "baseline": "baseline",
            "mirror": "mirroring",
            "comp": "complementing",
            "creative": "creative",
        }

        # pick a single display string from each JSON response (prefer "narrative")
        out = [
            OneText(condition=name_map[r["condition"]], response=_extract_text_from_json(r["text"]))
            for r in results
        ]

        # ensure fixed order for Qualtrics piping
        order = {"baseline": 0, "mirroring": 1, "complementing": 2, "creative": 3}
        out.sort(key=lambda x: order[x.condition])

        return TaskOut(responses=out)

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Generation temporarily unavailable: {e}")
