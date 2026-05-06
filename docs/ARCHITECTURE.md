# Architecture

## Layers

```
+-----------------------------------------------------------+
|              FastAPI (citas_bot.main)                     |
|   GET /webhook        POST /webhook        GET /health    |
+-----------------------------------------------------------+
                |                    |
                v                    v
       +-----------------+  +-----------------+
       |   webhooks/     |  |  scheduling/    |
       |  router +       |  |  reminders.py   |
       |  security       |  |  (APScheduler)  |
       +-----------------+  +-----------------+
                |                    |
                v                    v
       +-----------------+  +-----------------+
       |    intents/     |  |   messaging/    |
       |  IntentRouter   |  |  MetaSender     |
       |  6 handlers     |  |  (httpx +       |
       |  + default      |  |   tenacity)     |
       +-----------------+  +-----------------+
                |
                v
       +-----------------------------------+
       |          domain + data            |
       |  Customer / Appointment /         |
       |  Conversation                     |
       |  Repositories + AsyncSession      |
       +-----------------------------------+
                |
                v
              SQLite (aiosqlite, Alembic)
```

## Pipeline of an inbound message

1. Meta posts to `POST /webhook` with HMAC signature
2. `verify_signature` dependency checks `X-Hub-Signature-256` (M02)
3. Handler parses Pydantic shell (object/entry/changes), logs, returns 200
4. (Wire-up beyond M07 is deferred to v0.2.0): the intent router would
   look up the customer by WhatsApp number, fetch the active conversation,
   call `IntentRouter.route(...)`, and send the resulting `Reply` via
   `MetaSender.send(...)`.

## Pipeline of a reminder tick

1. APScheduler (configured at FastAPI lifespan startup) calls `scan_and_send`
   every `REMINDER_SCAN_INTERVAL_SECONDS`
2. `ReminderJob` queries appointments with status SCHEDULED or CONFIRMED
3. For each appointment whose `scheduled_at` falls inside the 24h or 2h
   window (centered, ±`REMINDER_WINDOW_MINUTES`), the job calls
   `MetaSender.send(...)` and flips the corresponding boolean flag

## Key design decisions

| Decision | Rationale |
|---|---|
| FastAPI async + aiosqlite | Single process, no Celery, no Redis |
| SQLAlchemy 2.0 (no SQLModel) | Stable mapping, mypy strict, easy Postgres switch |
| UUID v4 PKs | Non-enumerable, fork-safe |
| pydantic-settings BaseSettings | Typed config, .env support |
| structlog dual mode | console for dev, JSON for prod |
| Hybrid intent classifier | Keyword first (free, instant); LLM fallback only when needed |
| State machine via slot dict | No ML-ops, no extra deps; flow is the data |
| dateparser + ES locale | Handles "manana", "lunes 12 de mayo", etc. |
| Tenacity retry | Already used by AnthropicProvider and MetaSender |
| In-memory dedupe (last 100 msg ids) | Sufficient for single-process; Redis-backed in BACKLOG |
| Boolean flags for reminders | Simple, idempotent across restarts |

## Module map

```
src/citas_bot/
  main.py                  FastAPI app, lifespan, /health
  config.py                Settings + BusinessInfo
  observability/           structlog setup
  webhooks/                Meta webhook handlers + HMAC
  llm/                     Provider Protocol + AnthropicProvider
  data/                    SQLAlchemy engine, session, repositories, CLI
  domain/                  Customer, Appointment, Conversation models
  api/schemas/             Pydantic DTOs
  intents/                 IntentRouter + 6 handlers + default + base + intl
  scheduling/              APScheduler reminders
  messaging/               LogOnlySender + MetaSender (Meta Cloud API)
```

## What is *not* here (BACKLOG)

- Wiring the IntentRouter inside `webhooks/router.py` end-to-end
- Sending interactive button / list messages (Meta supports them)
- Webhook idempotency persisted in DB (current is in-memory)
- DeepSeek LLM provider (currently raises NotImplementedError)
- Multi-tenant (a single instance serves a single business)
- Distributed scheduling (one process owns the reminders)
