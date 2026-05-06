"""Process-wide registry of all known intents."""

from __future__ import annotations

from citas_bot.intents.base import Intent
from citas_bot.intents.book import BOOK
from citas_bot.intents.cancel import CANCEL
from citas_bot.intents.default import DEFAULT
from citas_bot.intents.handoff import HANDOFF
from citas_bot.intents.info import INFO
from citas_bot.intents.list_mine import LIST_MINE
from citas_bot.intents.reschedule import RESCHEDULE


class IntentRegistry:
    """Holds the available intents in dispatch order.

    The ``default`` intent is always last and matches when nothing else does.
    """

    def __init__(self, intents: list[Intent]) -> None:
        if not any(i.name == "default" for i in intents):
            raise ValueError("registry must contain a 'default' intent")
        self._intents = intents

    def all(self) -> list[Intent]:
        return list(self._intents)

    def by_name(self, name: str) -> Intent | None:
        return next((i for i in self._intents if i.name == name), None)

    def default(self) -> Intent:
        intent = self.by_name("default")
        assert intent is not None  # enforced in __init__
        return intent


def build_default_registry() -> IntentRegistry:
    """The shipped registry: 6 intents + default fallback."""

    return IntentRegistry(
        [LIST_MINE, RESCHEDULE, CANCEL, BOOK, HANDOFF, INFO, DEFAULT]
    )
