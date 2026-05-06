# citas-bot-universal

[![CI](https://github.com/abelardodiaz/citas-bot-universal/actions/workflows/ci.yml/badge.svg)](https://github.com/abelardodiaz/citas-bot-universal/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **Template Python para asistentes WhatsApp de citas.** Fork, personaliza,
> deploya en una VPS y empieza a recibir clientes el mismo dia.

Punto de partida para construir un bot WhatsApp que agende citas en tu
negocio: consultorios, barberias, talleres, salones, asesores con agenda.
Sin LangChain, sin SaaS, sin lock-in.

## Que incluye

- **FastAPI** + **SQLite** + **APScheduler** = stack minimo, 1 proceso
- **6 intents listos**: agendar, cancelar, reprogramar, mis citas,
  hablar con humano, informacion del negocio
- **Slot-filling state machine** para flujos multi-step
- **Hybrid intent classifier**: keyword first (instantaneo, gratis), LLM
  fallback (Anthropic) cuando hace falta
- **Recordatorios automaticos** 24h y 2h antes de cada cita
- **Meta WhatsApp Cloud API** sender con HMAC + retry
- **Tests con coverage 87%** y fixtures de conversaciones grabadas

## Quickstart (5 minutos)

```bash
git clone https://github.com/abelardodiaz/citas-bot-universal.git
cd citas-bot-universal
cp .env.example .env
# edita .env con tus credenciales Meta + Anthropic + datos del negocio

make install
make migrate
make seed     # opcional: datos demo
make run      # arranca uvicorn en :8000
```

Detalles paso a paso en [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) y
[docs/WEBHOOK.md](docs/WEBHOOK.md).

## Para quien

Devs Python LATAM que quieren un asistente WhatsApp deployable en una VPS
chica para su negocio o cliente, sin atarse a frameworks generales de
chatbot.

## Como contribuir

Reportes de bugs y sugerencias bienvenidos como issues. PRs aceptados;
cada release sigue un roadmap incremental con planes individuales validados
antes de codear (ver el repo `web26-073-portfolio-organico` para detalles).

## Documentacion

| Archivo | Para |
|---|---|
| [README.md](README.md) | Vista general (este archivo) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura interna |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Despliegue VPS |
| [docs/WEBHOOK.md](docs/WEBHOOK.md) | Registro del webhook en Meta |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Schema y migraciones |
| [docs/INTENTS.md](docs/INTENTS.md) | Como agregar tus propios intents |
| [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) | Variables de entorno + customizacion |
| [BACKLOG.md](BACKLOG.md) | Features deferidos para v0.2.0+ |
| [CHANGELOG.md](CHANGELOG.md) | Historial de releases |

## License

MIT. Ver [LICENSE](LICENSE).

## Origen

Destilado generico de un sistema de produccion privado para consultorios
medicos. La comparativa privado vs publico esta en
https://abelardodiaz.dev/projects/clinica-bot-public-vs-private (sale tras
el release).
