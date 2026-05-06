"""'info' intent: answers business-related questions (hours, address, etc.)."""

from __future__ import annotations

from citas_bot.intents.base import (
    Intent,
    IntentContext,
    IntentResult,
    Reply,
)
from citas_bot.llm import LLMError, Message
from citas_bot.observability import get_logger

log = get_logger(__name__)


_SYSTEM_TEMPLATE = """\
Eres el asistente WhatsApp de {name}.
Responde la pregunta del cliente usando solo la informacion del negocio:

- Nombre: {name}
- Horario: {hours}
- Direccion: {address}
- Telefono: {phone}
- Descripcion: {description}

Si la pregunta no se puede responder con esos datos, di que no tienes la
informacion y sugiere preguntar por otros temas (citas, horarios, ubicacion).
Responde en espanol, breve, en 1-3 frases.
"""


async def handle_info(ctx: IntentContext) -> IntentResult:
    info = ctx.business_info
    system = _SYSTEM_TEMPLATE.format(
        name=info.name,
        hours=info.hours,
        address=info.address,
        phone=info.phone or "(no proporcionado)",
        description=info.description or "(no proporcionado)",
    )
    messages = [
        Message(role="system", content=system),
        Message(role="user", content=ctx.text),
    ]
    try:
        response = await ctx.llm.chat(messages, max_tokens=200, temperature=0.4)
        text = response.text.strip() or "Disculpa, no pude generar una respuesta."
    except LLMError as exc:
        log.warning("info_handler_llm_error", error=str(exc))
        text = (
            f"Hola, soy el asistente de {info.name}. "
            f"Horario: {info.hours}. Direccion: {info.address}."
        )

    return IntentResult(reply=Reply(text=text), new_intent=None)


INFO = Intent(
    name="info",
    description="Preguntas generales sobre el negocio: horario, ubicacion, costos, servicios",
    examples=[
        "?donde estan ubicados?",
        "?a que hora abren?",
        "?cuanto cuesta una consulta?",
        "?aceptan tarjetas?",
    ],
    handler=handle_info,
    keywords=["horario", "horarios", "donde", "ubicacion", "ubicados", "costo", "precio"],
)
