from datetime import datetime, timezone


def utcnow():
    """UTC "naive", compatível com as colunas DateTime já gravadas (substitui datetime.utcnow)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value, fmt):
    try:
        return datetime.strptime(value, fmt)
    except (TypeError, ValueError):
        return None
