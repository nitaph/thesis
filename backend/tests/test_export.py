import asyncio
import csv

from app.routes.export import export_generations


class DummyResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class DummySession:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, _query):
        return DummyResult(self._rows)


def test_export_generations_includes_prompts():
    row = (
        "participant-1",
        "task-1",
        "baseline",
        "resp-1",
        "gpt-test",
        10,
        20,
        30,
        "2024-01-01T00:00:00",
        "system",
        "user",
        "Prompt body",
        '{"answer":"value"}',
    )

    async def call_export():
        response = await export_generations(session=DummySession([row]))
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        return "".join(chunks)

    csv_payload = asyncio.run(call_export())
    reader = list(csv.reader(csv_payload.splitlines()))
    header, data = reader[0], reader[1]

    assert header[9:13] == ["system_prompt", "user_prompt", "prompt_text", "text"]
    assert data[9:13] == ["system", "user", "Prompt body", '{"answer":"value"}']
