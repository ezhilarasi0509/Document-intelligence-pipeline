from __future__ import annotations

from .config import PRICES_PER_M


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Hypothetical paid cost in USD. You pay $0 on free tiers; this shows what scale would cost."""
    pin, pout = PRICES_PER_M.get(model, PRICES_PER_M["default"])
    return (prompt_tokens * pin + completion_tokens * pout) / 1_000_000
