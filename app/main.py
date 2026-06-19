from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import init_db
from .routers import cards, decks, review, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Flashcards API",
    description="A spaced-repetition flashcard API with an SM-2-lite scheduler.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(decks.router)
app.include_router(cards.router)
app.include_router(review.router)
app.include_router(stats.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"name": "flashcards-api", "docs": "/docs"}
