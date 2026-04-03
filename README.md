```md
# Live Crypto Stream

Live crypto market backend built with **FastAPI**, **WebSockets**, **Kafka**, and **PostgreSQL**.

The project connects to Binance public WebSocket streams, receives real-time trade and candle data, sends it through Kafka, stores processed data in PostgreSQL, and exposes REST and WebSocket APIs for clients.

## Stack

- FastAPI
- WebSockets
- Apache Kafka
- PostgreSQL
- SQLAlchemy
- Docker Compose

## Architecture

Binance WebSocket → Ingestor → Kafka → Consumer → PostgreSQL → FastAPI

## Services

- **api** — FastAPI service for REST and WebSocket endpoints
- **ingestor** — receives live Binance market data and publishes it to Kafka
- **consumer** — reads Kafka events and stores them in PostgreSQL
- **postgres** — database for trades, candles, and latest snapshots
- **kafka** — message broker for streaming data between services

## Features

- Real-time crypto trade ingestion
- Kafka-based event pipeline
- PostgreSQL storage for structured market data
- Latest market snapshot endpoint
- Candle history endpoint
- Daily stats endpoint
- Live WebSocket feed for frontend clients
- Dockerized local setup

## Endpoints

### REST
- `GET /health`
- `GET /symbols`
- `GET /symbols/{symbol}/latest`
- `GET /symbols/{symbol}/candles?interval=1m&limit=100`
- `GET /symbols/{symbol}/stats/today`

### WebSocket
- `WS /ws/live?symbols=BTCUSDT,ETHUSDT`
- `test_ws.html` — for live updates over html page

## Getting Started

```bash
cp .env.example .env
docker compose up --build