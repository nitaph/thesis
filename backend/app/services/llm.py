# --- app/services/llm.py ---
import asyncio, json, uuid
from typing import Dict, Optional
from pathlib import Path

from app.config import settings
from app.services.cache import Cache
from app.services.logging_utils import timer_ms
from app.services.utils import scrub_pii

try:
    from openai import AsyncOpenAI
    _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except Exception:
    _client = None

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"

# filenames we expect to exist (use persona.txt for mirror/comp; creative.txt for creative)
FILES = {
    "A": {
        "baseline": PROMPTS_DIR / "style_a_baseline.txt",
        "persona":  PROMPTS_DIR / "style_a_persona.txt",
        "creative": PROMPTS_DIR / "style_a_creative.txt",
    },
    "B": {
        "baseline": PROMPTS_DIR / "style_b_baseline.txt",
        "persona":  PROMPTS_DIR / "style_b_persona.txt",
        "creative": PROMPTS_DIR / "style_b_creative.txt",
    },
}

def _read(path: Path, fallback: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return fallback

def system_prompt_for(style: str, condition: str) -> str:
    """
    style: 'A' | 'B'
    condition: 'baseline' | 'mirror' | 'comp' | 'creative'
    """
    group = FILES.get(style.upper())
    if not group:
        # fallback minimal systems
        if style.upper() == "A":
            group = {
                "baseline": Path(),
                "persona": Path(),
                "creative": Path(),
            }
            return "Generate 3 concise, distinct ideas. Avoid fluff. Each idea has a bullet and one-sentence why."
        else:
            group = {
                "baseline": Path(),
                "persona": Path(),
                "creative": Path(),
            }
            return "Produce one well-argued concept: summary (≤50w), 4–6 steps, 2–3 risks, quick test."
    if condition == "creative":
        return _read(group["creative"],
                     "Produce creative output: favor unconventional, high-variance ideas; tolerate ambiguity.")
    if condition in ("mirror", "comp"):
        return _read(group["persona"],
                     "Adopt the given personality (O,C,E,A,N) and respond accordingly.")
    # baseline
    return _read(group["baseline"],
                 "Generate 3 concise, distinct ideas. Avoid fluff. Each idea has a bullet and one-sentence why.")

def persona_block(persona: Dict[str, int], guidance: Optional[str]) -> str:
    block = {"persona": persona}
    if guidance:
        block["guidance"] = guidance
    return json.dumps(block, ensure_ascii=False)

async def _call_openai(system_prompt: str, user_prompt: str) -> dict:
    if _client is None:
        return {
            "text": f"[MOCKED]\nSYSTEM:{system_prompt[:120]}...\nUSER:{user_prompt[:160]}...",
            "model": "mock",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0},
        }
    resp = await asyncio.wait_for(
        _client.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            top_p=settings.LLM_TOP_P,
            max_tokens=settings.LLM_MAX_TOKENS,
            seed=settings.LLM_SEED,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
        ),
        timeout=settings.TIMEOUT_S,
    )
    text = (resp.choices[0].message.content or "").strip()
    usage = getattr(resp, "usage", None)
    return {
        "text": text,
        "model": getattr(resp, "model", settings.LLM_MODEL),
        "usage": {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
        },
    }

cache = Cache(settings.REDIS_URL, settings.CACHE_TTL_S)

CONDITION_ORDER = ["baseline", "mirror", "comp", "creative"]

async def generate_four(
    personas: list[dict],
    participant_id: str,
    task_id: str,
    style: str,
    prompt_text: str,
):
    async def one(cond: str, persona_payload: dict):
        # compute per-condition system prompt INSIDE the function
        sys_prompt = system_prompt_for(style, cond)

        key = cache.make_key(participant_id, task_id, cond)
        cached = await cache.get(key)
        if cached:
            data = json.loads(cached)
            return data | {"fromCache": True}

        # persona injection goes into the USER message (baseline => none)
        pblock = "" if cond == "baseline" else persona_block(
            persona_payload["persona"], persona_payload.get("guidance")
        )
        user_msg = f"{prompt_text}\n\n{pblock}" if pblock else prompt_text

        with timer_ms() as elapsed:
            llm = await _call_openai(sys_prompt, user_msg)
        latency_ms = elapsed()

        text = scrub_pii(llm["text"]) if settings.STRIP_PII else llm["text"]
        payload = {
            "condition": cond,
            "responseId": str(uuid.uuid4()),
            "text": text,
            "model": llm["model"],
            "tokensIn": llm["usage"]["prompt_tokens"],
            "tokensOut": llm["usage"]["completion_tokens"],
            "generationTimeMs": latency_ms,
            # store prompts so you can export them
            "systemPrompt": sys_prompt,
            "userPrompt": user_msg,
        }
        await cache.set(key, json.dumps(payload))
        return payload

    tasks = [one(c, p) for c, p in zip(CONDITION_ORDER, personas)]
    return await asyncio.gather(*tasks, return_exceptions=False)
