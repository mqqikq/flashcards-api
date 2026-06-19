from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..scheduler import schedule_review
from ..utils import today_utc
from .cards import get_card_or_404
from .decks import get_deck_or_404

router = APIRouter(tags=["review"])


@router.get("/review/{deck_id}/next", response_model=schemas.CardOut)
def next_card(deck_id: int, db: Session = Depends(get_db)) -> models.Card:
    get_deck_or_404(deck_id, db)
    card = (
        db.query(models.Card)
        .filter(models.Card.deck_id == deck_id, models.Card.due_date <= today_utc())
        .order_by(models.Card.due_date)
        .first()
    )
    if card is None:
        raise HTTPException(status_code=404, detail="no cards due for review")
    return card


@router.post("/review/{card_id}", response_model=schemas.CardOut)
def review_card(card_id: int, review: schemas.ReviewIn, db: Session = Depends(get_db)) -> models.Card:
    card = get_card_or_404(card_id, db)
    result = schedule_review(
        ease=card.ease,
        interval=card.interval,
        repetitions=card.repetitions,
        quality=review.quality,
    )
    card.ease = result.ease
    card.interval = result.interval
    card.repetitions = result.repetitions
    card.due_date = result.due_date
    card.last_reviewed_at = datetime.utcnow()
    db.commit()
    db.refresh(card)
    return card
