from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC 'now'. All datetimes are stored naive-UTC (SQLite drops tzinfo)."""
    return datetime.now(UTC).replace(tzinfo=None)


def as_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def to_naive_utc(dt: datetime) -> datetime:
    return as_utc(dt).replace(tzinfo=None)
