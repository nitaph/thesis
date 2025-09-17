from fastapi import APIRouter
from app.config import settings
from app.services.llm import cache

router = APIRouter()

@router.get("/health")
async def health():
    return {"ok": True, "model": settings.LLM_MODEL}

@router.get("/version")
async def version():
    return {"promptVersion": settings.LOG_PROMPT_VERSION}

@router.post("/reset-cache")
async def reset_cache():
    await cache.clear()
    return {"cleared": True}
