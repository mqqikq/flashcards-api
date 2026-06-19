from datetime import date, datetime


def today_utc() -> date:
    """The current UTC date.

    Used everywhere "today" matters -- due dates, review timestamps, stats
    -- so they can't disagree near a local midnight boundary the way
    date.today() (local time) and datetime.utcnow() (UTC) would if mixed.
    """
    return datetime.utcnow().date()
