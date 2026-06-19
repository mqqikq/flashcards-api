from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/decks", tags=["decks"])


def get_deck_or_404(deck_id: int, db: Session) -> models.Deck:
    deck = db.get(models.Deck, deck_id)
    if deck is None:
        raise HTTPException(status_code=404, detail="deck not found")
    return deck


@router.post("", response_model=schemas.DeckOut, status_code=201)
def create_deck(deck: schemas.DeckCreate, db: Session = Depends(get_db)) -> models.Deck:
    if db.query(models.Deck).filter(models.Deck.name == deck.name).first() is not None:
        raise HTTPException(status_code=409, detail="a deck with this name already exists")
    db_deck = models.Deck(name=deck.name)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck


@router.get("", response_model=list[schemas.DeckOut])
def list_decks(db: Session = Depends(get_db)) -> list[models.Deck]:
    return list(db.query(models.Deck).order_by(models.Deck.id).all())


@router.get("/{deck_id}", response_model=schemas.DeckOut)
def get_deck(deck_id: int, db: Session = Depends(get_db)) -> models.Deck:
    return get_deck_or_404(deck_id, db)


@router.delete("/{deck_id}", status_code=204)
def delete_deck(deck_id: int, db: Session = Depends(get_db)) -> None:
    deck = get_deck_or_404(deck_id, db)
    db.delete(deck)
    db.commit()
