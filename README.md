# CryptoPayment Integration Backend Infra

Backend API for creating and processing **crypto pay orders** for merchant organizations.

Built with **FastAPI + SQLAlchemy + PostgreSQL**, this service allows organizations to:
- Create sale/deposit pay orders.
- Request quote options based on wallet balances.
- Generate payment details (deposit address + routing details).
- Submit an on-chain transaction hash for payment verification and state transitions.

---

## Table of Contents
- [Overview](#overview)
- [Core Concepts](#core-concepts)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [Run with Docker](#run-with-docker)
- [Operational Notes](#operational-notes)
- [Roadmap / Known Gaps](#roadmap--known-gaps)

---

## Overview

This service is the infrastructure API for crypto payment orchestration. It handles pay order lifecycle transitions and coordinates integrations with external quote/routing providers.

At startup, it:
- Initializes FastAPI app and middleware.
- Creates DB tables from SQLAlchemy models.
- Exposes pay order routes under `/pay-orders`.

---

## Core Concepts

### PayOrder Modes
- **SALE**: Merchant sells goods/services and receives value in configured settlement currencies or a specified destination currency.
- **DEPOSIT**: User deposits one crypto asset to be routed into a specified destination currency/address.

### PayOrder Statuses
`PENDING → AWAITING_PAYMENT → AWAITING_CONFIRMATION | EXECUTING_ORDER → COMPLETED | FAILED | EXPIRED | REFUNDED`

### Organization
An API consumer (merchant) identified by:
- `api_key`
- `api_secret`
- `settlement_currencies` (used for SALE flow when destination currency is not explicitly provided)

---

## Architecture

### Request flow (high-level)
1. Client creates a pay order.
2. Client requests quote options for a wallet.
3. Client chooses source currency and requests payment details.
4. Service creates an exchange route (currently via ChangeNow) and returns deposit details.
5. Client submits tx hash to process payment.
6. Service validates transfer details and advances pay order state.

### External Integrations
- **CoinGecko**: token metadata and pricing.
- **ChangeNow**: routing/exchange execution.
- **Alchemy/Solana/Sui RPC**: chain data, balances, transaction validation.
- Additional utility modules exist for Uniswap/Jupiter/CCTP and chain-specific logic.

---

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Uvicorn
- Docker

---

## Project Structure

```text
src/
  main.py                  # FastAPI app bootstrap + middleware + router registration
  config.py                # App config constants
  routes/
    payorder.py            # Pay order HTTP endpoints
  services/
    payorder.py            # Pay order business logic
    quote.py               # Quote calculation/orchestration
    changenow.py           # ChangeNow integration
    coingecko.py           # CoinGecko integration
  database/
    database.py            # SQLAlchemy engine/session setup
    dependencies.py        # FastAPI auth/db dependencies
  models/
    database_models.py     # SQLAlchemy models (Organization, PayOrder)
    schemas/payorder.py    # Request/response Pydantic schemas
    enums.py               # Domain enums
  utils/                   # Chain, currency, signature, and provider helpers
```

---

## API Endpoints

Base path: `/pay-orders`

| Method | Path | Purpose |
|---|---|---|
| POST | `/` | Create a pay order |
| POST | `/{payorder_id}/quote` | Get quote options for available source currencies |
| POST | `/{payorder_id}/payment-details` | Generate final payment/deposit details |
| GET | `/{payorder_id}/process?tx_hash=...` | Process submitted payment transaction hash |
| GET | `/{payorder_id}` | Get single pay order |
| GET | `/` | List all pay orders for current organization |

Swagger docs are available at:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

---

## Authentication

Two auth mechanisms are used depending on endpoint/flow:

1. **API Key header**
   - Header: `X-API-KEY: <organization_api_key>`

2. **Signature Authorization header** (used for SALE creation flow)
   - Header format:
     ```text
     APIKey=<api_key>,signature=<sha512>,timestamp=<unix_seconds>
     ```
   - Signature is generated from:
     ```text
     SHA512(APIKey + api_secret + timestamp)
     ```
   - Timestamp validity window: ±5 minutes.

---

## Environment Variables

Create a `.env` file in repository root.

### Required

```dotenv
POSTGRES_DB=crypto_payments
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

ALCHEMY_API_KEY=your_alchemy_key
SOLANA_RPC_URL=https://...
SUI_RPC_URL=https://...
CHANGENOW_API_KEY=your_changenow_key
COINGECKO_API_KEY=your_coingecko_pro_key
```

### Optional / Integration-specific

```dotenv
JUPITER_API_KEY=optional_if_used
```

> Note: several modules read env vars at import/runtime. Missing required values may raise startup/runtime exceptions.

---

## Local Development

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start API

```bash
uvicorn src.main:app --reload --port 8000
```

---

## Run with Docker

### Option A: direct docker commands

```bash
docker build -t coin-voyage-api .
docker run -p 8000:8000 --env-file .env coin-voyage-api
```

### Option B: helper script

```bash
chmod +x run.sh
./run.sh
```

`run.sh` builds the image, stops existing container on port 8000, and runs a new container with `.env`.

---

## Operational Notes

- CORS is currently open (`allow_origins=["*"]`).
- GZip middleware is enabled (`minimum_size=1024`).
- DB tables are auto-created on startup via `Base.metadata.create_all(engine)`.
- Current process endpoint updates status but does not yet include retry/background orchestration for confirmation execution.

---

## Roadmap / Known Gaps

- Add Alembic migrations for schema versioning.
- Tighten auth/error handling consistency in route/service layers.
- Add background workers/retry mechanism for asynchronous settlement states.
- Add health/readiness endpoints.
- Add automated test coverage (unit + integration).
- Harden production configuration (CORS allowlist, secret management, observability, and Gunicorn/HTTPS deployment strategy).
