import asyncio
from datetime import UTC, datetime

from app.common.auth import require_admin, require_user_or_admin

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.config import get_settings
from app.common.database import AsyncSessionLocal, get_db, init_db
from app.common.models import Candle1m, LatestMarketSnapshot, TradeTick
from app.common.schemas import CandleResponse, LatestSnapshotResponse, TodayStatsResponse
from app.common.utils import normalize_symbol

settings = get_settings()
app = FastAPI(title=settings.project_name)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/symbols")
async def get_symbols(_: str = Depends(require_user_or_admin)) -> dict[str, list[str]]:
    return {"symbols": settings.tracked_symbols}


@app.get("/symbols/{symbol}/latest", response_model=LatestSnapshotResponse, dependencies=[Depends(require_admin)])
async def get_latest(symbol: str, db: AsyncSession = Depends(get_db)) -> LatestSnapshotResponse:
    normalized = normalize_symbol(symbol)

    result = await db.execute(
        select(LatestMarketSnapshot).where(LatestMarketSnapshot.symbol == normalized)
    )
    snapshot = result.scalar_one_or_none()

    if snapshot is None:
        raise HTTPException(status_code=404, detail="No latest snapshot found for symbol")

    return LatestSnapshotResponse(
        symbol=snapshot.symbol,
        last_price=snapshot.last_price,
        last_quantity=snapshot.last_quantity,
        last_trade_id=snapshot.last_trade_id,
        last_trade_time=snapshot.last_trade_time,
        last_event_time=snapshot.last_event_time,
    )


@app.get("/symbols/{symbol}/candles", response_model=list[CandleResponse])
async def get_candles(
    symbol: str,
    interval: str = Query(default="1m"),
    limit: int = Query(default=100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(require_user_or_admin),
) -> list[CandleResponse]:
    normalized = normalize_symbol(symbol)

    result = await db.execute(
        select(Candle1m)
        .where(Candle1m.symbol == normalized, Candle1m.interval == interval)
        .order_by(Candle1m.open_time.desc())
        .limit(limit)
    )
    candles = result.scalars().all()

    return [
        CandleResponse(
            symbol=item.symbol,
            interval=item.interval,
            open_time=item.open_time,
            close_time=item.close_time,
            open_price=item.open_price,
            high_price=item.high_price,
            low_price=item.low_price,
            close_price=item.close_price,
            volume=item.volume,
            trade_count=item.trade_count,
        )
        for item in reversed(candles)
    ]


@app.get("/symbols/{symbol}/stats/today", response_model=TodayStatsResponse, dependencies=[Depends(require_admin)])
async def get_today_stats(symbol: str, db: AsyncSession = Depends(get_db)) -> TodayStatsResponse:
    normalized = normalize_symbol(symbol)
    start_of_day_utc = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    result = await db.execute(
        select(
            func.count(TradeTick.id),
            func.coalesce(func.sum(TradeTick.quantity), 0),
            func.coalesce(func.avg(TradeTick.price), 0),
            func.coalesce(func.max(TradeTick.price), 0),
            func.coalesce(func.min(TradeTick.price), 0),
        ).where(TradeTick.symbol == normalized, TradeTick.trade_time >= start_of_day_utc)
    )
    trade_count, total_volume, avg_price, high_price, low_price = result.one()

    return TodayStatsResponse(
        symbol=normalized,
        trade_count=int(trade_count or 0),
        total_volume=total_volume,
        avg_price=avg_price,
        high_price=high_price,
        low_price=low_price,
    )


@app.websocket("/ws/live")
async def live_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    requested = websocket.query_params.get("symbols", "")
    if requested:
        symbols = [normalize_symbol(item) for item in requested.split(",") if item.strip()]
    else:
        symbols = settings.tracked_symbols

    try:
        while True:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(LatestMarketSnapshot)
                    .where(LatestMarketSnapshot.symbol.in_(symbols))
                    .order_by(LatestMarketSnapshot.symbol.asc())
                )
                rows = result.scalars().all()

                payload = [
                    {
                        "symbol": row.symbol,
                        "last_price": str(row.last_price),
                        "last_quantity": str(row.last_quantity),
                        "last_trade_id": row.last_trade_id,
                        "last_trade_time": row.last_trade_time.isoformat(),
                        "last_event_time": row.last_event_time.isoformat(),
                    }
                    for row in rows
                ]

                await websocket.send_json(payload)

            await asyncio.sleep(settings.ws_push_interval_seconds)
    except WebSocketDisconnect:
        return
