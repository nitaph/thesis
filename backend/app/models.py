from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.db import Base

class Participant(Base):
    __tablename__ = "participants"
    participant_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Big5Score(Base):
    __tablename__ = "big5_scores"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    participant_id: Mapped[str] = mapped_column(String(64), ForeignKey("participants.participant_id", ondelete="CASCADE"))
    O: Mapped[int] = mapped_column(Integer)
    C: Mapped[int] = mapped_column(Integer)
    E: Mapped[int] = mapped_column(Integer)
    A: Mapped[int] = mapped_column(Integer)
    N: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Task(Base):
    __tablename__ = "tasks"
    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    style: Mapped[str] = mapped_column(String(16))  # "A" or "B"
    prompt_text: Mapped[str] = mapped_column(Text)
    ordinal: Mapped[int] = mapped_column(Integer)

class CachedResponse(Base):
    __tablename__ = "cached_responses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    participant_id: Mapped[str] = mapped_column(String(64))
    task_id: Mapped[str] = mapped_column(String(64))
    condition: Mapped[str] = mapped_column(String(16))
    response_id: Mapped[str] = mapped_column(String(64))
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt:   Mapped[str] = mapped_column(Text)
    prompt_text: Mapped[str] = mapped_column(Text)      
    text: Mapped[str] = mapped_column(Text)            
    model: Mapped[str] = mapped_column(String(64))
    tokens_in: Mapped[int] = mapped_column(Integer)
    tokens_out: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Rating(Base):
    __tablename__ = "ratings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    participant_id: Mapped[str] = mapped_column(String(64))
    task_id: Mapped[str] = mapped_column(String(64))
    condition: Mapped[str] = mapped_column(String(16))
    response_id: Mapped[str] = mapped_column(String(64))
    usefulness: Mapped[int] = mapped_column(Integer)
    novelty: Mapped[int] = mapped_column(Integer)
    shown_slot: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())