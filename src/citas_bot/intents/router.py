"""IntentRouter: classify -> dispatch -> persist conversation state."""

from __future__ import annotations

import json
from collections import deque
from typing import TYPE_CHECKING

from pydantic import ValidationError

from citas_bot.intents.base import Classification, IntentContext, IntentResult, Reply
from citas_bot.intents.registry import IntentRegistry
from citas_bot.llm import LLMError, Message
from citas_bot.observability import get_logger

if TYPE_CHECKING:
    from citas_bot.config import BusinessInfo
    from citas_bot.data.repositories import ConversationRepository
    from citas_bot.domain import Conversation, Customer
    from citas_bot.llm import LLMProvider


from pydantic import BaseModel, Field

log = get_logger(__name__)


class _ClassifierJSON(BaseModel):
    intent_name: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str | None = None


class IntentRouter:
    """Routes inbound messages to intent handlers.

    Two-step classification: keyword match first (cheap, deterministic), LLM
    fallback otherwise. Maintains an in-memory dedupe set keyed by Meta's
    ``message_id`` so duplicate webhook deliveries are no-ops.
    """

    def __init__(
        self,
        registry: IntentRegistry,
        llm: LLMProvider,
        business_info: BusinessInfo,
        conversation_repo: ConversationRepository,
        dedupe_cache_size: int = 100,
        confidence_threshold: float = 0.5,
    ) -> None:
        self._registry = registry
        self._llm = llm
        self._business_info = business_info
        self._conversations = conversation_repo
        self._seen_message_ids: deque[str] = deque(maxlen=dedupe_cache_size)
        self._threshold = confidence_threshold

    def already_processed(self, message_id: str) -> bool:
        return message_id in self._seen_message_ids

    def mark_processed(self, message_id: str) -> None:
        self._seen_message_ids.append(message_id)

    async def route(
        self,
        customer: Customer,
        conversation: Conversation,
        text: str,
        message_id: str | None = None,
    ) -> Reply | None:
        """Process one inbound text message; returns the Reply or None if dedupe hit."""

        if message_id is not None and self.already_processed(message_id):
            log.info("dedupe_skip", message_id=message_id)
            return None

        classification = await self._classify(text)
        intent = self._registry.by_name(classification.intent_name)
        if intent is None or classification.confidence < self._threshold:
            log.info(
                "intent_fallback_to_default",
                proposed=classification.intent_name,
                confidence=classification.confidence,
            )
            intent = self._registry.default()

        ctx = IntentContext(
            customer=customer,
            conversation=conversation,
            text=text,
            business_info=self._business_info,
            llm=self._llm,
        )
        result: IntentResult = await intent.handler(ctx)

        await self._persist_state(conversation, result, intent_name=intent.name)

        if message_id is not None:
            self.mark_processed(message_id)

        log.info(
            "intent_dispatched",
            intent=intent.name,
            confidence=classification.confidence,
            reply_type=result.reply.type,
        )
        return result.reply

    async def _classify(self, text: str) -> Classification:
        # 1. keyword match
        for intent in self._registry.all():
            if intent.name == "default":
                continue
            for kw in intent.keywords:
                if kw.lower() in text.lower():
                    return Classification(
                        intent_name=intent.name,
                        confidence=1.0,
                        reasoning=f"keyword:{kw}",
                    )
        # 2. LLM fallback
        return await self._classify_with_llm(text)

    async def _classify_with_llm(self, text: str) -> Classification:
        system = _build_classifier_prompt(self._registry)
        try:
            response = await self._llm.chat(
                [
                    Message(role="system", content=system),
                    Message(role="user", content=text),
                ],
                max_tokens=120,
                temperature=0.0,
            )
        except LLMError as exc:
            log.warning("classifier_llm_error", error=str(exc))
            return Classification(intent_name="default", confidence=1.0, reasoning="llm_error")

        try:
            payload = _ClassifierJSON.model_validate_json(_extract_json(response.text))
        except (ValidationError, ValueError) as exc:
            log.warning("classifier_parse_error", raw=response.text, error=str(exc))
            return Classification(intent_name="default", confidence=1.0, reasoning="parse_error")

        return Classification(
            intent_name=payload.intent_name,
            confidence=payload.confidence,
            reasoning=payload.reasoning,
        )

    async def _persist_state(
        self,
        conversation: Conversation,
        result: IntentResult,
        intent_name: str,
    ) -> None:
        if result.clear_state:
            await self._conversations.clear(conversation)
            return

        await self._conversations.update_state(
            conversation,
            intent=result.new_intent if result.new_intent is not None else intent_name,
            slots=result.new_slots,
        )


def _build_classifier_prompt(registry: IntentRegistry) -> str:
    lines = [
        "Clasifica el siguiente mensaje del usuario en uno de los intents listados.",
        "Responde SOLO con un JSON con esta forma:",
        '{"intent_name":"<nombre>","confidence":<0..1>,"reasoning":"<breve>"}',
        "",
        "Intents disponibles:",
    ]
    for intent in registry.all():
        examples = ", ".join(f'"{e}"' for e in intent.examples[:3])
        lines.append(f"- {intent.name}: {intent.description}")
        if examples:
            lines.append(f"  Ejemplos: {examples}")
    lines.append("")
    lines.append("Si dudas, usa intent_name='default' con confidence baja.")
    return "\n".join(lines)


def _extract_json(text: str) -> str:
    """Best-effort: locate the first JSON object in a free-form LLM response."""

    text = text.strip()
    if text.startswith("```"):
        # remove possible code fence
        text = text.strip("`").lstrip("json").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no json object in response")
    candidate = text[start : end + 1]
    json.loads(candidate)  # validate
    return candidate
