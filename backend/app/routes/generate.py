# app/routes/generate.py
from fastapi import APIRouter
from app.schemas import TaskIn, TaskOut, OneText

router = APIRouter()

@router.post("/generate-task", response_model=TaskOut)
async def generate_task(payload: TaskIn) -> TaskOut:
    # TODO: call your LLM(s) using payload.taskPrompt + trait_* to produce real text
    # Return in fixed order so Qualtrics can map by index: 0,1,2,3
    outputs = [
        OneText(condition="baseline",      response="Baseline output text"),
        OneText(condition="mirroring",     response="Mirroring output text"),
        OneText(condition="complementing", response="Complementing output text"),
        OneText(condition="creative",      response="Creative output text"),
    ]
    return TaskOut(responses=outputs)
