import asyncio
import json
from app.services.cache import Cache

async def _roundtrip():
    c = Cache(None, 3600)  # in-memory
    key = c.make_key("p1","t1","mirror")
    assert await c.get(key) is None
    await c.set(key, json.dumps({"ok":True}))
    got = await c.get(key)
    assert json.loads(got)["ok"] is True

def test_cache_event_loop():
    asyncio.run(_roundtrip())
