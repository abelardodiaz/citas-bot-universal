"""'default' intent: catches anything the bot does not understand."""

from __future__ import annotations

from citas_bot.intents.base import (
    Intent,
    IntentContext,
    IntentResult,
    Reply,
)


_DEFAULT_TEXT = (
    "Disculpa, aun no entiendo eso. "
    "Puedes preguntarme sobre: horarios, ubicacion, o agendar una cita."
)


async def handle_default(ctx: IntentContext) -> IntentResult:
    return IntentResult(reply=Reply(text=_DEFAULT_TEXT), clear_state=True)


DEFAULT = Intent(
    name="default",
    description="Fallback cuando ningun otro intent matchea",
    examples=[],
    handler=handle_default,
    keywords=[],
)
