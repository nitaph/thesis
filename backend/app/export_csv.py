import asyncio, csv, json, os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.models import Big5Score, CachedResponse, Rating
from sqlalchemy import select

def _flatten(value, parent_key="", sep="_"):
    items = {}
    if isinstance(value, dict):
        for key, nested in value.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            items.update(_flatten(nested, new_key, sep))
    elif isinstance(value, list):
        for idx, nested in enumerate(value):
            new_key = f"{parent_key}{sep}{idx}" if parent_key else str(idx)
            items.update(_flatten(nested, new_key, sep))
    elif parent_key:
        items[parent_key] = value
    return items

async def main():
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    os.makedirs("exports", exist_ok=True)

    async with async_session() as s:
        # Cached responses
        res = await s.execute(select(CachedResponse).order_by(CachedResponse.id))
        rows = res.scalars().all()
        base_header = [
            "participant_id",
            "task_id",
            "condition",
            "response_id",
            "model",
            "tokens_in",
            "tokens_out",
            "latency_ms",
            "created_at",
            "system_prompt",
            "user_prompt",
            "prompt_text",
            "text",
        ]
        processed_rows = []
        flattened_keys = []
        seen_keys = set()
        for r in rows:
            row_values = [
                r.participant_id,
                r.task_id,
                r.condition,
                r.response_id,
                r.model,
                r.tokens_in,
                r.tokens_out,
                r.latency_ms,
                r.created_at,
                r.system_prompt,
                r.user_prompt,
                r.prompt_text,
                r.text,
            ]
            flattened = {}
            if r.text:
                try:
                    parsed = json.loads(r.text)
                except json.JSONDecodeError:
                    parsed = None
                if isinstance(parsed, (dict, list)):
                    flattened = _flatten(parsed)
            for key in flattened:
                if key not in seen_keys:
                    seen_keys.add(key)
                    flattened_keys.append(key)
            processed_rows.append((row_values, flattened))
        header = base_header + flattened_keys
        with open("exports/generations.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            for row_values, flattened in processed_rows:
                appended = []
                for key in flattened_keys:
                    value = flattened.get(key)
                    appended.append("" if value is None else value)
                w.writerow(row_values + appended)

        # Big Five
        res = await s.execute(select(Big5Score))
        rows = res.scalars().all()
        with open("exports/big5_scores.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["participant_id","O","C","E","A","N","created_at"])
            for r in rows:
                w.writerow([r.participant_id, r.O, r.C, r.E, r.A, r.N, r.created_at])

        # Ratings
        res = await s.execute(select(Rating))
        rows = res.scalars().all()
        with open("exports/ratings.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["participant_id","task_id","condition","response_id","usefulness","novelty","shown_slot","created_at"])
            for r in rows:
                w.writerow([r.participant_id, r.task_id, r.condition, r.response_id, r.usefulness, r.novelty, r.shown_slot, r.created_at])

        print("Exported to exports/generations.csv, exports/big5_scores.csv and exports/ratings.csv")

if __name__ == "__main__":
    asyncio.run(main())
