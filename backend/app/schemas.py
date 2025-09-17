from typing import Annotated, Literal, List, Dict, Optional
from pydantic import BaseModel, Field

# ---- Common constrained types ----
Score = Annotated[int, Field(ge=1, le=5)]
Answers50 = Annotated[List[Score], Field(min_length=50, max_length=50)]

SlotIdx = Annotated[int, Field(ge=1, le=4)]
Likert7 = Annotated[int, Field(ge=1, le=7)]
MsNonNegative = Annotated[int, Field(ge=0)]

# ---- Big Five scoring ----
class ScoreRequest(BaseModel):
    participantId: Annotated[str, Field(max_length=64)]
    answers: Answers50

class Big5Out(BaseModel):
    O: int
    C: int
    E: int
    A: int
    N: int

# ---- Personas ----
class PersonaPayload(BaseModel):
    type: Literal["baseline", "mirror", "comp", "creative"]
    persona: Dict[str, int]  # expects keys {"O","C","E","A","N"} with 10..50 ints
    guidance: Optional[str] = None
    version: str

class PersonaRequest(BaseModel):
    participantId: str

class PersonaResponse(BaseModel):
    participantId: str
    personas: List[PersonaPayload]

# ---- Generation ----
class GenerateRequest(BaseModel):
    participantId: str
    taskId: str
    taskStyle: Literal["A", "B"]
    promptText: str

class SingleResponse(BaseModel):
    condition: Literal["baseline", "mirror", "comp", "creative"]
    responseId: str
    text: str
    model: str
    tokensIn: MsNonNegative
    tokensOut: MsNonNegative
    generationTimeMs: MsNonNegative

class GenerateResponse(BaseModel):
    participantId: str
    taskId: str
    responses: List[SingleResponse]  # fixed order A/B/C/D

# ---- Ratings ----
class SlotRating(BaseModel):
    slot: SlotIdx
    condition: Literal["baseline", "mirror", "comp", "creative"]
    responseId: str
    usefulness: Likert7
    novelty: Likert7
    generationTimeMs: MsNonNegative

class SubmitRatingsRequest(BaseModel):
    participantId: str
    taskId: str
    taskIdxInBlock: Annotated[int, Field(ge=1)]  # 1-based index within the block
    ratings: Annotated[List[SlotRating], Field(min_length=4, max_length=4)]
