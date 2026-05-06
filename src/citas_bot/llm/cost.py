"""Token-to-USD cost helper.

Prices are hardcoded for known models as of 2026-05-06. Update as Anthropic
publishes new pricing or new models. Returns 0.0 for unknown models so callers
can still log without crashing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _ModelPricing:
    input_per_mtok: float  # USD per 1_000_000 input tokens
    output_per_mtok: float


_PRICING: dict[str, _ModelPricing] = {
    # Anthropic Claude (illustrative, verify against official pricing)
    "claude-haiku-4-5-20251001": _ModelPricing(input_per_mtok=0.80, output_per_mtok=4.00),
    "claude-sonnet-4-6": _ModelPricing(input_per_mtok=3.00, output_per_mtok=15.00),
    "claude-opus-4-7": _ModelPricing(input_per_mtok=15.00, output_per_mtok=75.00),
}


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    """Return the estimated USD cost for a single chat completion.

    Returns 0.0 for unknown models. Caller is responsible for keeping pricing
    fresh — this helper is illustrative, not authoritative.
    """

    pricing = _PRICING.get(model)
    if pricing is None:
        return 0.0
    cost_in = tokens_in * pricing.input_per_mtok / 1_000_000
    cost_out = tokens_out * pricing.output_per_mtok / 1_000_000
    return cost_in + cost_out
