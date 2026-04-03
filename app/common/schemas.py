from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SymbolResponse(BaseModel):
    symbol: str


class LatestSnapshotResponse(BaseModel):
    symbol: str
    last_price: Decimal
    last_quantity: Decimal
    last_trade_id: int
    last_trade_time: datetime
    last_event_time: datetime


class CandleResponse(BaseModel):
    symbol: str
    interval: str
    open_time: datetime
    close_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    trade_count: int


class TodayStatsResponse(BaseModel):
    symbol: str
    trade_count: int
    total_volume: Decimal
    avg_price: Decimal
    high_price: Decimal
    low_price: Decimal


class LiveTickResponse(BaseModel):
    symbol: str
    last_price: Decimal
    last_quantity: Decimal
    last_trade_time: datetime
    updated_at: datetime | None = None
