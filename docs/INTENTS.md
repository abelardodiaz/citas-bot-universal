# Intents

The intent layer lives in `src/citas_bot/intents/` and is responsible for
turning a user's text message into a reply.

## Pipeline

```
text + customer + conversation
        |
        v
+--------------------------+
| IntentRouter.route()     |
+--------------------------+
|  1. dedupe by message_id |
|  2. classify (keyword    |
|     match -> LLM)        |
|  3. dispatch to handler  |
|  4. persist new state    |
+--------------------------+
        |
        v
       Reply
```

Two-step classification keeps the bot cheap and snappy:

1. **Keyword match**: each `Intent` declares a `keywords` list. A
   case-insensitive substring match returns confidence 1.0 with no LLM call.
2. **LLM fallback**: when no keyword matches, the LLM is asked to return
   `{"intent_name": ..., "confidence": ..., "reasoning": ...}` as JSON. The
   classifier prompt is built dynamically from the registry, so adding an
   intent automatically updates the prompt.

If classification fails (LLM error or bad JSON), or confidence falls below
the threshold (`0.5` by default), the `default` intent runs.

## Available intents

### `info`

Answers questions about the business (hours, address, services, costs)
using the `BusinessInfo` from settings. Calls the LLM with a system prompt
that lists the business facts; falls back to a static reply with name,
hours, and address if the LLM is unreachable.

Keywords: `horario`, `horarios`, `donde`, `ubicacion`, `ubicados`, `costo`, `precio`.

### `default`

Catch-all when no other intent matches with sufficient confidence. Replies
with a friendly "I don't understand yet, you can ask me about: ..." message
and clears the conversation state.

## Adding your own intent

1. Create `src/citas_bot/intents/my_intent.py`:

   ```python
   from citas_bot.intents.base import Intent, IntentContext, IntentResult, Reply

   async def handle_my_intent(ctx: IntentContext) -> IntentResult:
       return IntentResult(reply=Reply(text="hola"))

   MY_INTENT = Intent(
       name="my_intent",
       description="Describe what this intent handles",
       examples=["frase ejemplo 1", "frase ejemplo 2"],
       handler=handle_my_intent,
       keywords=["palabra1", "palabra2"],
   )
   ```

2. Register it in `intents/registry.py`:

   ```python
   from citas_bot.intents.my_intent import MY_INTENT

   def build_default_registry() -> IntentRegistry:
       return IntentRegistry([INFO, MY_INTENT, DEFAULT])
   ```

3. Add a test in `tests/test_intents.py`.

## Conversation state

The router writes back `current_intent` and (when slot-filling kicks in
v0.2.0+) `slots_filled` after every message. Handlers do not touch the
database; they return an `IntentResult` and the router persists it. This
keeps handlers pure and easy to unit-test.

## Idempotency

`IntentRouter` keeps an in-memory deque of the last 100 `message_id`s seen.
A duplicate webhook delivery (Meta retries) is silently ignored. For
horizontally scaled deployments, replace this with a Redis-backed dedupe
table — see the BACKLOG.md.

## Wiring into the webhook

In M05 the intent layer is implemented and tested in isolation. The actual
wiring inside `webhooks/router.py` (extract text from payload, lookup
customer, fetch conversation, call `IntentRouter.route`) lands in M06 once
slot-filling is in place — that is when the full request needs all the
moving parts together.

## What is not implemented yet

- Slot filling for multi-step flows (M06)
- Sending the reply back to Meta's Send API (M07)
- Other intents: book, cancel, reschedule, list_mine, handoff (M06-M07)
- Persistent dedupe table (BACKLOG)
- Interactive buttons / list messages (BACKLOG)
