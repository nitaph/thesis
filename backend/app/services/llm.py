# --- app/services/llm.py ---
import os, asyncio, json, uuid
from typing import Dict, Optional
from pathlib import Path
from time import perf_counter

# --------- light settings (no DB!) ----------
class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_TOP_P = float(os.getenv("LLM_TOP_P", "1.0"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "350"))
    LLM_SEED = int(os.getenv("LLM_SEED")) if os.getenv("LLM_SEED") else None
    TIMEOUT_S = int(os.getenv("TIMEOUT_S", "25"))
    STRIP_PII = os.getenv("STRIP_PII", "false").lower() == "true"
    CACHE_TTL_S = int(os.getenv("CACHE_TTL_S", "3600"))
    REDIS_URL = os.getenv("REDIS_URL")  # optional

settings = Settings()

# --------- cache (use your Redis cache if set, else in-memory) ----------
class _MemCache:
    def __init__(self): self._d = {}
    async def get(self, k): return self._d.get(k)
    async def set(self, k, v): self._d[k] = v
    def make_key(self, pid, tid, cond): return f"{pid}:{tid}:{cond}"

if settings.REDIS_URL:
    from app.services.cache import Cache  # your redis impl
    cache = Cache(settings.REDIS_URL, settings.CACHE_TTL_S)
else:
    cache = _MemCache()

# --------- tiny timer (no external utils) ----------
class timer_ms:
    def __enter__(self): self.t0 = perf_counter(); return self
    def __exit__(self, *a): pass
    def __call__(self): return int((perf_counter() - self.t0) * 1000)

def scrub_pii(text: str) -> str:
    # keep your own if you prefer; no-op here
    return text

# --------- OpenAI client ----------
try:
    from openai import AsyncOpenAI
    _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
except Exception:
    _client = None

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"

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
    try: return path.read_text(encoding="utf-8")
    except Exception: return fallback

def system_prompt_for(style: str, condition: str) -> str:
    group = FILES.get(style.upper())
    if not group:
        return "Produce a concise, high-quality answer in the requested style."
    if condition == "creative":
        return _read(group["creative"], "Favor unconventional, high-variance ideas; tolerate ambiguity.")
    if condition in ("mirror", "comp"):
        return _read(group["persona"], "Adopt the given personality (O,C,E,A,N) and respond accordingly.")
    return _read(group["baseline"], "Provide a sensible, neutral, concise answer.")

def persona_block(persona: Dict[str, int], guidance: Optional[str]) -> str:
    block = {"persona": persona}
    if guidance: block["guidance"] = guidance
    return json.dumps(block, ensure_ascii=False)

async def _call_openai(system_prompt: str, user_prompt: str) -> dict:
    if _client is None:
        return {"text": f"[MOCKED]\n{user_prompt[:160]}...", "model": "mock", "usage": {"prompt_tokens": 0, "completion_tokens": 0}}
    resp = await asyncio.wait_for(
        _client.chat.completions.create(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            top_p=settings.LLM_TOP_P,
            max_tokens=settings.LLM_MAX_TOKENS,
            seed=settings.LLM_SEED,
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
            response_format={"type": "json_object"},

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

CONDITION_ORDER = ["baseline", "mirror", "comp", "creative"]

async def generate_four(personas: list[dict], participant_id: str, task_id: str, style: str, prompt_text: str):
    async def one(cond: str, persona_payload: dict):
        sys_prompt = system_prompt_for(style, cond)

        key = cache.make_key(participant_id, task_id, cond)
        cached = await cache.get(key)
        if cached:
            data = json.loads(cached)
            return data | {"fromCache": True}

        pblock = "" if cond == "baseline" else persona_block(persona_payload["persona"], persona_payload.get("guidance"))
        user_msg = f"{prompt_text}\n\n{pblock}" if pblock else prompt_text

        with timer_ms() as t:
            llm = await _call_openai(sys_prompt, user_msg)
        latency_ms = t()

        text = scrub_pii(llm["text"]) if settings.STRIP_PII else llm["text"]
        payload = {
            "condition": cond,
            "responseId": str(uuid.uuid4()),
            "text": text,
            "model": llm["model"],
            "tokensIn": llm["usage"]["prompt_tokens"],
            "tokensOut": llm["usage"]["completion_tokens"],
            "generationTimeMs": latency_ms,
            "systemPrompt": sys_prompt,
            "userPrompt": user_msg,
        }
        await cache.set(key, json.dumps(payload))
        return payload

    tasks = [one(c, p) for c, p in zip(CONDITION_ORDER, personas)]
    return await asyncio.gather(*tasks)
