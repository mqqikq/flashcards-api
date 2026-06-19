from datetime import date

import pytest

from app.scheduler import schedule_review


def test_low_quality_resets_repetitions_and_leaves_ease_unchanged():
    result = schedule_review(ease=2.5, interval=10, repetitions=3, quality=2, today=date(2024, 1, 1))
    assert result.repetitions == 0
    assert result.interval == 1
    assert result.ease == 2.5
    assert result.due_date == date(2024, 1, 2)


def test_first_successful_review_schedules_one_day_out():
    result = schedule_review(ease=2.5, interval=0, repetitions=0, quality=4, today=date(2024, 1, 1))
    assert result.repetitions == 1
    assert result.interval == 1
    assert result.due_date == date(2024, 1, 2)


def test_second_successful_review_schedules_six_days_out():
    result = schedule_review(ease=2.5, interval=1, repetitions=1, quality=4, today=date(2024, 1, 1))
    assert result.repetitions == 2
    assert result.interval == 6


def test_third_successful_review_multiplies_by_ease_before_this_reviews_update():
    result = schedule_review(ease=2.5, interval=6, repetitions=2, quality=4, today=date(2024, 1, 1))
    assert result.repetitions == 3
    assert result.interval == round(6 * 2.5)  # uses ease as it stood *before* this review


def test_quality_4_leaves_ease_unchanged():
    result = schedule_review(ease=2.5, interval=6, repetitions=2, quality=4)
    assert result.ease == 2.5


def test_perfect_quality_increases_ease():
    result = schedule_review(ease=2.5, interval=6, repetitions=2, quality=5)
    assert result.ease > 2.5


def test_ease_never_drops_below_the_floor():
    result = schedule_review(ease=1.3, interval=6, repetitions=2, quality=3)
    assert result.ease == 1.3


def test_quality_out_of_range_rejected():
    with pytest.raises(ValueError):
        schedule_review(ease=2.5, interval=1, repetitions=0, quality=6)
    with pytest.raises(ValueError):
        schedule_review(ease=2.5, interval=1, repetitions=0, quality=-1)
