from datetime import UTC, datetime
from decimal import Decimal


def ms_to_datetime(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=UTC)


def to_decimal(value: str | int | float | Decimal) -> Decimal:
    return Decimal(str(value))


def normalize_symbol(symbol: str) -> str:
    return symbol.upper().strip()
