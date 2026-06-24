"""Self-healing loop: retry with diagnosis, escalate only after N failures.

Mirrors the "fix it yourself; surface to a human only after consecutive failures"
discipline. The point is that each retry is *informed*: ``diagnose`` inspects the error
and proposes an adjustment, so attempt N+1 differs from attempt N instead of repeating it.
"""
from __future__ import annotations

from typing import Callable, Optional


class EscalationError(RuntimeError):
    """Raised when recovery exhausts its attempts and must hand off to a human."""

    def __init__(self, attempts: int, last_exc: Optional[BaseException]) -> None:
        super().__init__(f"escalated after {attempts} attempt(s): {last_exc!r}")
        self.attempts = attempts
        self.last_exc = last_exc


def with_recovery(
    action: Callable,
    diagnose: Optional[Callable] = None,
    max_attempts: int = 3,
    **kwargs,
):
    """Call ``action(**kwargs)``; on failure, diagnose -> adjust kwargs -> retry.

    ``diagnose(exc, attempt, kwargs) -> dict`` returns keyword overrides merged into the
    next attempt (default: retry unchanged). After ``max_attempts`` failures, raises
    :class:`EscalationError` carrying the last exception.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    last: Optional[BaseException] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return action(**kwargs)
        except Exception as exc:  # noqa: BLE001 -- recovery is the whole point
            last = exc
            if diagnose is not None and attempt < max_attempts:
                kwargs = {**kwargs, **(diagnose(exc, attempt, dict(kwargs)) or {})}
    raise EscalationError(max_attempts, last)
