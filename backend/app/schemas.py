# app/schemas.py
from typing import List, Dict, Union, Literal
from pydantic import BaseModel, field_validator
import json

# ---------- Scoring ----------
class ScoreRequest(BaseModel):
    participantId: str
    # Accepts either a JSON list or a stringified list (Qualtrics sends a string)
    answers: Union[List[int], str]

    @field_validator("answers", mode="before")
    @classmethod
    def _parse_answers(cls, v):
        if isinstance(v, str):
            v = json.loads(v)
        return v

    @field_validator("answers")
    @classmethod
    def _validate_answers(cls, v: List[int]):
        if not isinstance(v, list):
            raise ValueError("answers must be a list")
        if len(v) != 50:
            raise ValueError("answers must have length 50")
        for x in v:
            if not isinstance(x, int) or x < 1 or x > 5:
                raise ValueError("each answer must be int 1–5")
        return v

class Big5Out(BaseModel):
    # Qualtrics-friendly wrapper (map traits.trait_*)
    traits: Dict[str, int]  # keys: trait_openness, trait_conscientiousness, trait_extraversion, trait_agreeableness, trait_neuroticism

# ---------- Generation (Qualtrics-friendly) ----------
Condition = Literal["baseline", "mirroring", "complementing", "creative"]

class TaskIn(BaseModel):
    participantId: str
    taskId: str
    # traits come as separate body params (Number type in Qualtrics)
    trait_openness: int
    trait_conscientiousness: int
    trait_extraversion: int
    trait_agreeableness: int
    trait_neuroticism: int
    taskPrompt: str | None = None  # optional

class OneText(BaseModel):
    condition: Condition
    response: str

class TaskOut(BaseModel):
    responses: List[OneText]  # fixed order for easy Qualtrics mapping
