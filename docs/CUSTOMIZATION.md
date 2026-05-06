# Customization

After forking, here is what you typically tweak to make the bot fit your
business.

## 1. Business info

Edit `BUSINESS_INFO_JSON` in `.env` (or set it in your environment). It is a
JSON string with the following keys:

```json
{
  "name": "Barberia X",
  "hours": "Lunes a Sabado 9-19",
  "address": "Calle Y 123, CDMX",
  "phone": "+5215555555555",
  "description": "Cortes clasicos y modernos"
}
```

`name` is used in reminders and the info handler. `hours` is parsed for the
opening-hours range; the parser looks for two integers (e.g. `9-18`,
`9am-6pm`). Falls back to 9-18 if no integers are found.

## 2. Timezone and appointment duration

```
BUSINESS_TIMEZONE=America/Mexico_City
APPOINTMENT_DURATION_MINUTES=30
```

## 3. LLM provider

Default is Anthropic Claude. Set `LLM_PROVIDER=anthropic` and provide
`ANTHROPIC_API_KEY` and (optionally) `ANTHROPIC_MODEL`.

`LLM_PROVIDER=deepseek` is reserved for v0.2.0+ and currently raises
`NotImplementedError` at startup.

## 4. Reminders

```
REMINDER_SCAN_INTERVAL_SECONDS=300   # how often the scanner runs
REMINDER_WINDOW_MINUTES=5            # +/- window around the 24h / 2h marks
```

## 5. Adding an intent

See `docs/INTENTS.md`. The shortest path:

1. Create `src/citas_bot/intents/my_intent.py` with an `Intent` value and
   an async `handle_*` function.
2. Register it in `src/citas_bot/intents/registry.py` before `DEFAULT`.
3. Add a fixture in `tests/fixtures/conversations/`.

## 6. Customizing the reminder text

The templates live in `src/citas_bot/scheduling/reminders.py`:

```python
REMINDER_24H_TPL = "Hola{name_part}. Te recordamos tu cita en {business_name} manana a las {hora}."
REMINDER_2H_TPL  = "Recordatorio: tu cita en {business_name} es en aprox. 2 horas (a las {hora})."
```

Edit those strings (or move them to `intents/intl.py` if you want a single
location for translatable copy).

## 7. Switching to Postgres

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/citas
```

`pip install asyncpg` and run `make migrate`. The migrations are
schema-portable.

## 8. Adding a new locale

Strings shown to the user are isolated in `src/citas_bot/intents/intl.py`.
Replacing them (or wrapping them with `gettext`) is the entry point for a
multi-language bot. PRs welcome.
