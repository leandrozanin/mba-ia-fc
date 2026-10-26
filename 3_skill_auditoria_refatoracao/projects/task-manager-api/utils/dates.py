from datetime import datetime, timezone


def utcnow():
    """UTC sem tzinfo, compatível com as colunas DateTime existentes.

    Substitui `datetime.utcnow()`, deprecated desde o Python 3.12.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
