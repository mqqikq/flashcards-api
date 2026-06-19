from dataclasses import dataclass
from datetime import date, timedelta

from .utils import today_utc

DEFAULT_EASE = 2.5
MIN_EASE = 1.3


@dataclass(frozen=True)
class ScheduleResult:
    ease: float
    interval: int
    repetitions: int
    due_date: date


def schedule_review(
    *,
    ease: float,
    interval: int,
    repetitions: int,
    quality: int,
    today: date | None = None,
) -> ScheduleResult:
    """SM-2-lite: given a card's current scheduling state and a 0-5 quality
    rating for *this* review, returns its next state.

    quality < 3 is a lapse: repetitions and interval reset, ease is left
    untouched (only a successful recall adjusts ease). quality >= 3 advances
    the schedule -- 1 day after the first successful review, 6 after the
    second, and `previous_interval * ease` after that, using the ease factor
    as it stood *before* this review updates it.
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"quality must be between 0 and 5, got {quality}")
    today = today if today is not None else today_utc()

    if quality < 3:
        repetitions = 0
        interval = 1
    else:
        repetitions += 1
        if repetitions == 1:
            interval = 1
        elif repetitions == 2:
            interval = 6
        else:
            interval = round(interval * ease)
        ease = max(MIN_EASE, ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    return ScheduleResult(
        ease=ease,
        interval=interval,
        repetitions=repetitions,
        due_date=today + timedelta(days=interval),
    )
