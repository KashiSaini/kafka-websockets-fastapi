from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TradeTick(Base):
    __tablename__ = "trade_ticks"
    __table_args__ = (UniqueConstraint("symbol", "trade_id", name="uq_trade_symbol_trade_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    trade_id: Mapped[int] = mapped_column(BigInteger, index=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    trade_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    is_buyer_market_maker: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Candle1m(Base):
    __tablename__ = "candles_1m"
    __table_args__ = (UniqueConstraint("symbol", "interval", "open_time", name="uq_candle_symbol_interval_open_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    interval: Mapped[str] = mapped_column(String(10), index=True)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    open_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    high_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    low_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    close_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    volume: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    trade_count: Mapped[int] = mapped_column(Integer)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LatestMarketSnapshot(Base):
    __tablename__ = "latest_market_snapshots"

    symbol: Mapped[str] = mapped_column(String(20), primary_key=True)
    last_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    last_quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8))
    last_trade_id: Mapped[int] = mapped_column(BigInteger)
    last_trade_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
