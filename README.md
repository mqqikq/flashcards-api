# flashcards-api

[![CI](https://github.com/mqqikq/flashcards-api/actions/workflows/ci.yml/badge.svg)](https://github.com/mqqikq/flashcards-api/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A REST API for studying flashcards with spaced repetition — decks, cards,
and a review endpoint that schedules each card's next appearance with an
SM-2-lite algorithm, the same family of algorithm Anki uses.

## Why this exists

Spaced repetition is the part of an app like Anki that actually does
something interesting: it isn't just CRUD, it's a small stateful algorithm
that decides *when* you'll see a card again based on how well you remembered
it. This project is that algorithm wrapped in a clean REST API — the kind of
backend a real flashcard app's client would talk to.

## Features

- CRUD for decks and cards (`SQLAlchemy` models, SQLite — zero setup, no DB
  server to run)
- `POST /review/{card_id}` schedules the next review with an **SM-2-lite**
  scheduler (`app/scheduler.py`) — a pure function, unit-tested independently
  of the API and the database
- `GET /review/{deck_id}/next` returns whichever card in a deck is due today
- `GET /stats` — total decks/cards, how many cards are due today, how many
  have already been reviewed today
- Input validation via Pydantic (e.g. a review quality outside 0–5, or an
  empty deck name, is rejected with `422` before it reaches the database)
- Auto-generated interactive docs at `/docs` (Swagger UI) and `/redoc`
- 19 pytest tests: the scheduler's branch logic in isolation, and the full
  HTTP surface via FastAPI's `TestClient` against an in-memory SQLite DB

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt

uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for interactive Swagger docs, or:

```bash
curl -s -X POST http://127.0.0.1:8000/decks -H 'Content-Type: application/json' \
  -d '{"name": "Spanish"}'
# {"id":1,"name":"Spanish"}

curl -s -X POST http://127.0.0.1:8000/decks/1/cards -H 'Content-Type: application/json' \
  -d '{"front": "perro", "back": "dog"}'
# {"id":1,"deck_id":1,"front":"perro","back":"dog","ease":2.5,"interval":0,"repetitions":0,"due_date":"2026-06-19","last_reviewed_at":null}

curl -s http://127.0.0.1:8000/review/1/next
# the same card -- it's due today, since every new card starts out due

curl -s -X POST http://127.0.0.1:8000/review/1 -H 'Content-Type: application/json' \
  -d '{"quality": 5}'
# {"id":1, ..., "interval":1, "repetitions":1, "due_date":"2026-06-20", "last_reviewed_at":"2026-06-19T09:05:10.827939"}
```

## API overview

| Method | Path | Description |
|---|---|---|
| `POST` | `/decks` | create a deck |
| `GET` | `/decks` | list decks |
| `GET` | `/decks/{id}` | get one deck |
| `DELETE` | `/decks/{id}` | delete a deck (and its cards) |
| `POST` | `/decks/{id}/cards` | add a card to a deck |
| `GET` | `/decks/{id}/cards` | list a deck's cards |
| `DELETE` | `/cards/{id}` | delete a card |
| `GET` | `/review/{deck_id}/next` | the next card in a deck that's due today (`404` if none) |
| `POST` | `/review/{card_id}` | submit a `{"quality": 0-5}` rating, reschedules the card |
| `GET` | `/stats` | total decks/cards, due-today and reviewed-today counts |

Full request/response schemas are in the auto-generated docs at `/docs`.

## How spaced repetition works

Every card tracks four numbers: `ease` (how easy this card is for you, starts
at 2.5), `interval` (days until the next review), `repetitions` (consecutive
successful reviews), and `due_date`.

When you review a card, you rate your recall quality from 0 (total
blackout) to 5 (perfect). `app/scheduler.py`'s `schedule_review()` then:

- **quality < 3 (a lapse):** resets `repetitions` to 0 and `interval` to 1
  day. `ease` is left untouched — a single bad review shouldn't permanently
  brand a card as "hard."
- **quality >= 3 (a pass):** `repetitions` increments, and `interval` becomes
  1 day (1st success), 6 days (2nd), or `round(previous_interval * ease)`
  (3rd onward) — each successful review pushes the next one further out.
  `ease` is then nudged by how *good* the recall was: quality 5 increases it
  (the card gets easier, so it's shown less often), quality 3 decreases it
  slightly, with a floor of 1.3 so a card never gets scheduled into
  oblivion.

This is the same shape as SuperMemo's SM-2 (the algorithm behind Anki),
trimmed to the handful of rules that matter for a small portfolio project —
no per-card learning steps or fuzz factor, just ease/interval/repetitions
driving a `due_date`.

## Testing

```bash
python -m pytest -v
```

`tests/test_scheduler.py` checks the algorithm's branches directly (lapses,
each of the first three successful reviews, the ease floor) with no FastAPI
or database involved. `tests/test_api.py` drives the full HTTP API through
FastAPI's `TestClient`, with `get_db` overridden to an in-memory SQLite
database that's recreated before every test for isolation.

## Architecture

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI app, router wiring, startup (`init_db`) |
| `app/models.py` | SQLAlchemy models: `Deck`, `Card` |
| `app/database.py` | engine/session setup (SQLite), `get_db` dependency |
| `app/schemas.py` | Pydantic request/response models |
| `app/scheduler.py` | the SM-2-lite algorithm, a pure function with no I/O |
| `app/routers/decks.py` | deck CRUD |
| `app/routers/cards.py` | card CRUD, nested under a deck |
| `app/routers/review.py` | `/review/*` — the scheduling endpoints |
| `app/routers/stats.py` | `/stats` aggregate counts |

## Roadmap

- [x] CRUD for decks and cards, SQLite persistence, `/docs`
- [x] SM-2-lite review scheduling
- [x] `/stats` (due today, reviewed today)
- [ ] Stretch: tags/search, simple API-key auth, small HTML front end, deploy

## License

[MIT](LICENSE)
