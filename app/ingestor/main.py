import asyncio
import json
import logging
from datetime import UTC, datetime

from aiokafka import AIOKafkaProducer
from websockets import connect

from app.common.config import get_settings

settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ingestor")


def build_stream_url() -> str:
    streams: list[str] = []
    for symbol in settings.tracked_symbols:
        lower_symbol = symbol.lower()
        streams.append(f"{lower_symbol}@trade")
        streams.append(f"{lower_symbol}@kline_{settings.candle_interval}")
    return f"{settings.binance_ws_base}{'/'.join(streams)}"


async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        client_id=settings.kafka_client_id,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )
    await producer.start()
    return producer


async def publish_forever() -> None:
    url = build_stream_url()
    logger.info("Connecting to Binance stream: %s", url)

    producer = await create_producer()

    try:
        while True:
            try:
                async with connect(url, ping_interval=20, ping_timeout=20) as websocket:
                    logger.info("Connected to Binance WebSocket")

                    async for raw_message in websocket:
                        envelope = json.loads(raw_message)
                        stream = envelope.get("stream", "")
                        data = envelope.get("data", {})
                        received_at = datetime.now(UTC).isoformat()

                        if stream.endswith("@trade"):
                            message = {
                                "source": "binance",
                                "kind": "trade",
                                "stream": stream,
                                "received_at": received_at,
                                "payload": data,
                            }
                            await producer.send_and_wait(settings.kafka_topic_trades, message)

                        elif f"@kline_{settings.candle_interval}" in stream:
                            message = {
                                "source": "binance",
                                "kind": "kline",
                                "stream": stream,
                                "received_at": received_at,
                                "payload": data,
                            }
                            await producer.send_and_wait(settings.kafka_topic_klines, message)

            except Exception as exc:  # noqa: BLE001
                logger.exception("Ingestor loop failed, reconnecting: %s", exc)
                await asyncio.sleep(5)
    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(publish_forever())
