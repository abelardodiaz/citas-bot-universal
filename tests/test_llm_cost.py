"""Cost helper tests."""

from citas_bot.llm.cost import cost_usd


def test_cost_known_model_returns_positive() -> None:
    cost = cost_usd("claude-sonnet-4-6", tokens_in=1_000_000, tokens_out=1_000_000)
    assert cost == 18.0  # 3 input + 15 output per 1M


def test_cost_unknown_model_returns_zero() -> None:
    assert cost_usd("unknown-model-xyz", tokens_in=10_000, tokens_out=10_000) == 0.0


def test_cost_scales_linearly() -> None:
    a = cost_usd("claude-sonnet-4-6", tokens_in=1000, tokens_out=1000)
    b = cost_usd("claude-sonnet-4-6", tokens_in=2000, tokens_out=2000)
    assert b == 2 * a
