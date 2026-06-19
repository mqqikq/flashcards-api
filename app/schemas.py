from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class DeckCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class CardCreate(BaseModel):
    front: str = Field(min_length=1)
    back: str = Field(min_length=1)


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deck_id: int
    front: str
    back: str
    ease: float
    interval: int
    repetitions: int
    due_date: date
    last_reviewed_at: datetime | None = None


class ReviewIn(BaseModel):
    quality: int = Field(ge=0, le=5, description="0 (total blackout) to 5 (perfect recall)")


class StatsOut(BaseModel):
    total_decks: int
    total_cards: int
    cards_due_today: int
    cards_reviewed_today: int
