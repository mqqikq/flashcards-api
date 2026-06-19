from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from .decks import get_deck_or_404

router = APIRouter(tags=["cards"])


def get_card_or_404(card_id: int, db: Session) -> models.Card:
    card = db.get(models.Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="card not found")
    return card


@router.post("/decks/{deck_id}/cards", response_model=schemas.CardOut, status_code=201)
def create_card(
    deck_id: int, card: schemas.CardCreate, db: Session = Depends(get_db)
) -> models.Card:
    get_deck_or_404(deck_id, db)
    db_card = models.Card(deck_id=deck_id, front=card.front, back=card.back)
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card


@router.get("/decks/{deck_id}/cards", response_model=list[schemas.CardOut])
def list_cards(deck_id: int, db: Session = Depends(get_db)) -> list[models.Card]:
    get_deck_or_404(deck_id, db)
    return list(
        db.query(models.Card).filter(models.Card.deck_id == deck_id).order_by(models.Card.id).all()
    )


@router.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: int, db: Session = Depends(get_db)) -> None:
    card = get_card_or_404(card_id, db)
    db.delete(card)
    db.commit()
