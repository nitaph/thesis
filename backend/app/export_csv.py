import asyncio, csv, os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.models import Big5Score, Rating
from sqlalchemy import select

async def main():
    engine = create_async_engine(settings.DATABASE_URL, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    os.makedirs("exports", exist_ok=True)

    async with async_session() as s:
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

    print("Exported to exports/big5_scores.csv and exports/ratings.csv")

if __name__ == "__main__":
    asyncio.run(main())
