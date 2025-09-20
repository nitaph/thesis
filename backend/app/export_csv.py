# app/export_csv.py
import asyncio, csv, json, os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from .config import settings
from .models import Big5Score, CachedResponse, Rating

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
    print("CWD:", os.getcwd())
    print("DATABASE_URL:", settings.DATABASE_URL)

    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # Use an absolute export dir (next to your backend folder)
    base_dir = Path(__file__).resolve().parents[1]
    export_dir = base_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    print("Export dir:", export_dir)

    async with async_session() as s:
        # ---------- CachedResponse ----------
        res = await s.execute(select(CachedResponse).order_by(CachedResponse.id))
        rows = res.scalars().all()
        print("CachedResponse rows:", len(rows))
        gen_path = export_dir / "generations.csv"

        base_header = [
            "participant_id","task_id","condition","response_id","model",
            "tokens_in","tokens_out","latency_ms","created_at",
            "system_prompt","user_prompt","prompt_text","text",
        ]
        processed_rows = []
        flattened_keys = []
        seen_keys = set()

        for r in rows:
            row_values = [
                r.participant_id, r.task_id, r.condition, r.response_id,
                r.model, r.tokens_in, r.tokens_out, r.latency_ms,
                r.created_at, r.system_prompt, r.user_prompt, r.prompt_text,
                r.text,
            ]
            flattened = {}
            if r.text:
                try:
                    parsed = json.loads(r.text)
                    if isinstance(parsed, (dict, list)):
                        flattened = _flatten(parsed)
                except json.JSONDecodeError:
                    pass
            for key in flattened:
                if key not in seen_keys:
                    seen_keys.add(key)
                    flattened_keys.append(key)
            processed_rows.append((row_values, flattened))

        header = base_header + flattened_keys
        with gen_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            for row_values, flattened in processed_rows:
                appended = [flattened.get(key, "") for key in flattened_keys]
                w.writerow(row_values + appended)

        print(f"Wrote {gen_path} ({gen_path.stat().st_size} bytes)")

        # ---------- Big Five ----------
        res = await s.execute(select(Big5Score))
        rows = res.scalars().all()
        print("Big5Score rows:", len(rows))
        big5_path = export_dir / "big5_scores.csv"
        with big5_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["participant_id","O","C","E","A","N","created_at"])
            for r in rows:
                w.writerow([r.participant_id, r.O, r.C, r.E, r.A, r.N, r.created_at])
        print(f"Wrote {big5_path} ({big5_path.stat().st_size} bytes)")

        # ---------- Ratings ----------
        res = await s.execute(select(Rating))
        rows = res.scalars().all()
        print("Rating rows:", len(rows))
        ratings_path = export_dir / "ratings.csv"
        with ratings_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["participant_id","task_id","condition","response_id","usefulness","novelty","shown_slot","created_at"])
            for r in rows:
                w.writerow([r.participant_id, r.task_id, r.condition, r.response_id, r.usefulness, r.novelty, r.shown_slot, r.created_at])
        print(f"Wrote {ratings_path} ({ratings_path.stat().st_size} bytes)")

if __name__ == "__main__":
    asyncio.run(main())
