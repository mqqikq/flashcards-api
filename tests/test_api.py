import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import Base

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def _fresh_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_create_and_list_deck():
    resp = client.post("/decks", json={"name": "Spanish"})
    assert resp.status_code == 201
    deck = resp.json()
    assert deck["name"] == "Spanish"
    assert "id" in deck

    resp = client.get("/decks")
    assert resp.status_code == 200
    assert [d["name"] for d in resp.json()] == ["Spanish"]


def test_duplicate_deck_name_is_rejected():
    assert client.post("/decks", json={"name": "Dup"}).status_code == 201
    resp = client.post("/decks", json={"name": "Dup"})
    assert resp.status_code == 409


def test_get_and_delete_missing_deck_404():
    assert client.get("/decks/9999").status_code == 404
    assert client.delete("/decks/9999").status_code == 404


def test_empty_deck_name_is_rejected():
    resp = client.post("/decks", json={"name": ""})
    assert resp.status_code == 422


def test_card_crud_within_a_deck():
    deck = client.post("/decks", json={"name": "Math"}).json()
    resp = client.post(f"/decks/{deck['id']}/cards", json={"front": "2+2", "back": "4"})
    assert resp.status_code == 201
    card = resp.json()
    assert card["ease"] == 2.5
    assert card["interval"] == 0
    assert card["repetitions"] == 0
    assert card["deck_id"] == deck["id"]

    cards = client.get(f"/decks/{deck['id']}/cards").json()
    assert len(cards) == 1
    assert cards[0]["front"] == "2+2"

    assert client.delete(f"/cards/{card['id']}").status_code == 204
    assert client.get(f"/decks/{deck['id']}/cards").json() == []


def test_cards_require_an_existing_deck():
    resp = client.post("/decks/9999/cards", json={"front": "x", "back": "y"})
    assert resp.status_code == 404


def test_review_flow_advances_the_schedule():
    deck = client.post("/decks", json={"name": "History"}).json()
    card = client.post(f"/decks/{deck['id']}/cards", json={"front": "1492", "back": "Columbus"}).json()

    # A freshly created card is due today.
    next_up = client.get(f"/review/{deck['id']}/next")
    assert next_up.status_code == 200
    assert next_up.json()["id"] == card["id"]

    resp = client.post(f"/review/{card['id']}", json={"quality": 5})
    assert resp.status_code == 200
    reviewed = resp.json()
    assert reviewed["repetitions"] == 1
    assert reviewed["interval"] == 1
    assert reviewed["due_date"] != card["due_date"] or reviewed["interval"] > 0

    # Now scheduled a day out, so it's no longer the next card due today.
    assert client.get(f"/review/{deck['id']}/next").status_code == 404


def test_review_rejects_out_of_range_quality():
    deck = client.post("/decks", json={"name": "Bio"}).json()
    card = client.post(f"/decks/{deck['id']}/cards", json={"front": "x", "back": "y"}).json()
    resp = client.post(f"/review/{card['id']}", json={"quality": 9})
    assert resp.status_code == 422


def test_review_nonexistent_card_404():
    resp = client.post("/review/9999", json={"quality": 4})
    assert resp.status_code == 404


def test_next_review_requires_an_existing_deck():
    resp = client.get("/review/9999/next")
    assert resp.status_code == 404


def test_stats_reflect_decks_cards_and_reviews():
    resp = client.get("/stats")
    assert resp.status_code == 200
    assert resp.json() == {
        "total_decks": 0,
        "total_cards": 0,
        "cards_due_today": 0,
        "cards_reviewed_today": 0,
    }

    deck = client.post("/decks", json={"name": "Stats"}).json()
    card = client.post(f"/decks/{deck['id']}/cards", json={"front": "x", "back": "y"}).json()

    stats = client.get("/stats").json()
    assert stats["total_decks"] == 1
    assert stats["total_cards"] == 1
    assert stats["cards_due_today"] == 1  # freshly created cards are due today
    assert stats["cards_reviewed_today"] == 0

    client.post(f"/review/{card['id']}", json={"quality": 5})

    stats = client.get("/stats").json()
    assert stats["cards_reviewed_today"] == 1
