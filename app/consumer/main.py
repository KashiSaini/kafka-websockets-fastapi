import asyncio
import json
import logging
from decimal import Decimal

from aiokafka import AIOKafkaConsumer
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.common.config import get_settings
from app.common.database import AsyncSessionLocal, init_db
from app.common.models import Candle1m, LatestMarketSnapshot, TradeTick
from app.common.utils import ms_to_datetime, normalize_symbol, to_decimal

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("consumer")


async def save_trade(message: dict) -> None:
    payload = message["payload"]
    symbol = normalize_symbol(payload["s"])

    async with AsyncSessionLocal() as session:
        trade = TradeTick(
            symbol=symbol,
            trade_id=int(payload["t"]),
            event_time=ms_to_datetime(payload["E"]),
            trade_time=ms_to_datetime(payload["T"]),
            price=to_decimal(payload["p"]),
            quantity=to_decimal(payload["q"]),
            is_buyer_market_maker=bool(payload["m"]),
        )
        session.add(trade)

        snapshot_stmt = insert(LatestMarketSnapshot).values(
            symbol=symbol,
            last_price=to_decimal(payload["p"]),
            last_quantity=to_decimal(payload["q"]),
            last_trade_id=int(payload["t"]),
            last_trade_time=ms_to_datetime(payload["T"]),
            last_event_time=ms_to_datetime(payload["E"]),
        )
        snapshot_stmt = snapshot_stmt.on_conflict_do_update(
            index_elements=[LatestMarketSnapshot.symbol],
            set_={
                "last_price": to_decimal(payload["p"]),
                "last_quantity": to_decimal(payload["q"]),
                "last_trade_id": int(payload["t"]),
                "last_trade_time": ms_to_datetime(payload["T"]),
                "last_event_time": ms_to_datetime(payload["E"]),
            },
        )
        await session.execute(snapshot_stmt)

        try:
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            logger.warning("Skipping duplicate or failed trade insert: %s", exc)


async def save_kline(message: dict) -> None:
    payload = message["payload"]
    kline = payload["k"]

    if not kline.get("x", False):
        return

    symbol = normalize_symbol(kline["s"])

    async with AsyncSessionLocal() as session:
        candle_stmt = insert(Candle1m).values(
            symbol=symbol,
            interval=kline["i"],
            open_time=ms_to_datetime(kline["t"]),
            close_time=ms_to_datetime(kline["T"]),
            open_price=to_decimal(kline["o"]),
            high_price=to_decimal(kline["h"]),
            low_price=to_decimal(kline["l"]),
            close_price=to_decimal(kline["c"]),
            volume=to_decimal(kline["v"]),
            trade_count=int(kline["n"]),
            is_closed=bool(kline["x"]),
        )
        candle_stmt = candle_stmt.on_conflict_do_update(
            index_elements=[Candle1m.symbol, Candle1m.interval, Candle1m.open_time],
            set_={
                "close_time": ms_to_datetime(kline["T"]),
                "open_price": to_decimal(kline["o"]),
                "high_price": to_decimal(kline["h"]),
                "low_price": to_decimal(kline["l"]),
                "close_price": to_decimal(kline["c"]),
                "volume": to_decimal(kline["v"]),
                "trade_count": int(kline["n"]),
                "is_closed": bool(kline["x"]),
            },
        )
        await session.execute(candle_stmt)
        await session.commit()


async def consume_forever() -> None:
    await init_db()

    consumer = AIOKafkaConsumer(
        settings.kafka_topic_trades,
        settings.kafka_topic_klines,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        client_id=f"{settings.kafka_client_id}-consumer",
        enable_auto_commit=True,
        auto_offset_reset="earliest",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    await consumer.start()
    logger.info("Kafka consumer started")

    try:
        async for message in consumer:
            value = message.value
            if message.topic == settings.kafka_topic_trades:
                await save_trade(value)
            elif message.topic == settings.kafka_topic_klines:
                await save_kline(value)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume_forever())
