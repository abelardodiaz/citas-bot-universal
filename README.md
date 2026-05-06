# citas-bot-universal

[![CI](https://github.com/abelardodiaz/citas-bot-universal/actions/workflows/ci.yml/badge.svg)](https://github.com/abelardodiaz/citas-bot-universal/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

> **Template Python para asistentes WhatsApp de citas.** Fork, personaliza, deploya.

Punto de partida para construir un bot WhatsApp que agende citas en tu negocio:
consultorios, barberias, talleres, salones, asesores con agenda. Sin LangChain,
sin SaaS, sin lock-in.

## Estado

**Pre-alpha (M01 - foundation).** Roadmap publico cuando llegue v0.1.0 (estimado
2026-05-26). Sigue el progreso en commits o suscribete a releases.

## Ideas centrales

- **FastAPI** + **SQLite** + **APScheduler** = stack minimo, 1 proceso
- **1 LLM provider** configurable (Anthropic default, DeepSeek alternativa)
- **Intent router** con state machine para slot filling
- **6 intents core**: agendar, cancelar, reprogramar, mis citas, info, hablar con humano
- **Sin Celery, sin Redis, sin Google Calendar**: complejidad fuera del template

## Para quien

Devs Python LATAM que quieren un asistente WhatsApp deployable en una VPS chica
para su negocio o cliente, sin atarse a frameworks generales de chatbot.

## Como contribuir

El proyecto sigue un roadmap incremental con planes individuales validados antes
de codear. Reportes de bugs y sugerencias bienvenidos como issues. PRs aceptados
una vez que v0.1.0 este publicado.

## License

MIT. Ver [LICENSE](LICENSE).

## Origen

Destilado generico de un sistema de produccion privado para consultorios medicos.
Comparativa publico vs privado disponible despues del release v0.1.0 en
https://abelardodiaz.dev/projects/citas-bot-universal
