# Backlog (post v0.1.0)

These items are intentionally out of v0.1.0 scope. They are tracked here so
adopters know what to expect and contributors know where to start.

## Pipeline

- Wire `IntentRouter` inside `webhooks/router.py` end-to-end (lookup
  customer, fetch conversation, dispatch, send via `MetaSender`).
- Persist webhook idempotency in DB instead of in-memory deque (Redis or
  a simple `processed_messages` table).
- Status webhook handling (Meta posts back delivery + read receipts).

## Intents

- Multi-language replies (gettext or simple per-locale dict).
- LLM-generated reminder copy with personalization.
- Free-form rescheduling ("mover la del lunes al viernes 11").
- Owner notification when `handoff_active` flips on (Slack, Telegram).

## LLM

- DeepSeek provider implementation (currently raises NotImplementedError).
- OpenAI provider implementation.
- Streaming responses.
- Tool / function calling.
- Provider fallback (e.g., Anthropic primary, DeepSeek backup).

## Messaging

- Interactive button / list / reply templates.
- Outbound template messages outside the 24h customer-care window.
- Media (image/audio/document) replies.

## Scheduling

- Distributed scheduler (currently single-process owns the reminders).
- Per-customer custom reminder windows.
- SMS / email fallback when WhatsApp delivery fails.

## Operations

- Prometheus metrics endpoint.
- Loki / ELK shippers preconfigured in Docker compose.
- Database backups script + S3 upload helper.
- Helm chart for Kubernetes deployments.

## Persistence

- Postgres async driver tested in CI matrix (currently SQLite only).
- `BINARY(16)` UUID storage option for denser indexes.

## Quality

- Mutation testing (mutmut or cosmic-ray).
- Property-based tests for the date parser.
- Load testing harness (Locust).

## Documentation

- Spanish translation of README and key docs.
- Diagrams as code (Mermaid) for ARCHITECTURE.md.
- Tutorial / video for first-time setup.
