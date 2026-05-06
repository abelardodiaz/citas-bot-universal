# Deployment

## Single VPS (recommended)

A 1 GB RAM VPS is enough. Steps assume Ubuntu 22.04+.

### 1. Install runtime

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv git
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and configure

```bash
git clone https://github.com/abelardodiaz/citas-bot-universal.git
cd citas-bot-universal
cp .env.example .env
$EDITOR .env  # fill META_*, ANTHROPIC_API_KEY, BUSINESS_INFO_JSON
```

### 3. Migrate and seed (optional)

```bash
make install
make migrate
make seed   # creates a couple of demo customers + appointments
```

### 4. Run with uvicorn behind a reverse proxy

```bash
make run    # development; runs uvicorn with --reload
```

For production, prefer a process manager (systemd, supervisor) and a real
TLS frontend (Caddy or nginx). Example systemd unit:

```ini
[Unit]
Description=citas-bot-universal
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/citas-bot-universal
ExecStart=/opt/citas-bot-universal/.venv/bin/uvicorn citas_bot.main:app --host 127.0.0.1 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 5. Register the webhook in Meta

See `docs/WEBHOOK.md` for the dashboard walkthrough.

### 6. Smoke test

```bash
curl https://YOUR_DOMAIN/health
# {"status":"ok"}
```

## Tunneling for local testing

If you cannot expose your server directly, use ngrok:

```bash
ngrok http 8000
```

Use the resulting HTTPS URL as the Meta webhook callback. Free ngrok tier
rotates the URL whenever ngrok restarts; re-register if needed.

## Database backups

SQLite is a file. Back it up with:

```bash
cp citas_bot.db citas_bot.db.$(date +%F)
```

For larger deployments, switch to Postgres by changing `DATABASE_URL` and
running `make migrate`. SQLAlchemy 2.0 + async drivers (`asyncpg`) work
out-of-the-box.

## Monitoring

- `/health` is suitable for basic liveness probes.
- Logs are structured (JSON when `LOG_FORMAT=json`); ship them to Loki,
  ELK, or your favourite aggregator.
- The scheduler logs `reminders_scan_done` with `sent` count every tick.

## Updating

```bash
git pull
make install
make migrate
sudo systemctl restart citas-bot-universal
```

## Known limitations

- Single process only; horizontal scaling requires the items in
  `BACKLOG.md` (Redis dedupe + distributed scheduling).
- The Meta access token in `.env` must come from a system user to avoid
  expiring after 60 days.
