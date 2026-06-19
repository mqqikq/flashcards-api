from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..utils import today_utc

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=schemas.StatsOut)
def get_stats(db: Session = Depends(get_db)) -> schemas.StatsOut:
    today = today_utc()
    total_decks = db.query(func.count(models.Deck.id)).scalar() or 0
    total_cards = db.query(func.count(models.Card.id)).scalar() or 0
    cards_due_today = (
        db.query(func.count(models.Card.id)).filter(models.Card.due_date <= today).scalar() or 0
    )
    cards_reviewed_today = (
        db.query(func.count(models.Card.id))
        .filter(func.date(models.Card.last_reviewed_at) == today.isoformat())
        .scalar()
        or 0
    )
    return schemas.StatsOut(
        total_decks=total_decks,
        total_cards=total_cards,
        cards_due_today=cards_due_today,
        cards_reviewed_today=cards_reviewed_today,
    )
