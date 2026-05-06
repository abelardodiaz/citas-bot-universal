# Example: Barberia Demo

A worked example of customizing the template for a fictional barber shop.

The values below go in `.env` at the repo root.

```
BUSINESS_INFO_JSON='{"name":"Barberia Buena Pinta","hours":"Mar-Sab 10-19","address":"Av. Insurgentes 100, CDMX","phone":"+5215555550100","description":"Cortes clasicos, fade y barba"}'
BUSINESS_TIMEZONE=America/Mexico_City
APPOINTMENT_DURATION_MINUTES=45
```

Reminder templates can stay as the defaults; they pull `business_name` from
`BUSINESS_INFO_JSON.name`.

After updating `.env`, run:

```bash
make install
make migrate
make run
```

Then send `mis citas` to the bot to confirm the end-to-end pipeline.
