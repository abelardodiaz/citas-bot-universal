# Changelog

All notable changes to citas-bot-universal will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-26

First public release. The template is feature-complete enough to be
forked and deployed to a VPS as a real WhatsApp appointment assistant.

### Added

- FastAPI app with `/health` and `GET|POST /webhook`
- HMAC-SHA256 verification of inbound Meta webhooks
- Anthropic Claude LLM provider with tenacity retry
- SQLAlchemy 2.0 async models for Customer, Appointment, Conversation
- Alembic migrations 0001 (initial schema), 0002 (handoff flag),
  0003 (reminder flags)
- Hybrid intent router: keyword match + LLM JSON classifier fallback
- 6 intents shipped: `book`, `cancel`, `reschedule`, `list_mine`,
  `handoff`, `info`, plus the catch-all `default`
- Slot-filling state machine for the booking flow (date -> time ->
  name -> confirm)
- Real Meta WhatsApp Cloud API sender with httpx + bearer auth
- APScheduler-backed reminder scanner (24h and 2h before each
  appointment) with idempotent per-row flags
- Recorded conversation fixtures (JSON) and a parameterized replay
  test for regression-proofing
- Docs: README, WEBHOOK, DATA_MODEL, INTENTS, ARCHITECTURE, DEPLOYMENT,
  CUSTOMIZATION
- One worked example (`examples/barberia`)

### Known limitations

See `BACKLOG.md`. The most prominent ones:

- The webhook handler logs payloads but does not yet auto-dispatch
  through `IntentRouter`; that wire-up is BACKLOG.
- DeepSeek provider raises NotImplementedError.
- Single-process deployment only.
