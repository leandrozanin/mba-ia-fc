from datetime import UTC, datetime


def utc_now():
    """Agora em UTC, sem tzinfo, no mesmo formato das colunas DateTime já gravadas."""
    return datetime.now(UTC).replace(tzinfo=None)


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
