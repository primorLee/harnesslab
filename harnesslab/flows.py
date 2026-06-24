"""Staged flows with mandatory gates, and a scored review gate.

A *flow* is an ordered list of steps; a step may carry a **gate** that must pass before
the flow proceeds -- e.g. "reproduction mode may not exit until a failing-case recipe was
recorded." That turns process discipline into something the harness enforces, not
something a model is trusted to remember.

:func:`scored_review` generalises a writer -> critic -> lead pipeline: score an output
across named dimensions and ship only when the *weakest* dimension clears the bar -- one
fatal flaw sinks it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence


class GateError(RuntimeError):
    """Raised when a flow step's gate refuses to let the flow continue."""


@dataclass
class Step:
    name: str
    run: Callable  # run(ctx) -> result
    gate: Optional[Callable] = None  # gate(result, ctx) -> bool


def run_flow(steps: Sequence[Step], ctx: Optional[dict] = None) -> dict:
    """Run steps in order, recording each result in ``ctx[name]``.

    If a step's gate returns falsy, raises :class:`GateError` -- the flow cannot proceed
    past an unmet gate.
    """
    ctx = dict(ctx or {})
    for step in steps:
        result = step.run(ctx)
        ctx[step.name] = result
        if step.gate is not None and not step.gate(result, ctx):
            raise GateError(f"gate failed at step {step.name!r}")
    return ctx


REVIEW_DIMENSIONS = (
    "correctness",
    "safety",
    "feasibility",
    "cost",
    "novelty",
    "completeness",
)


def scored_review(
    output,
    scorer: Callable,
    dimensions: Sequence[str] = REVIEW_DIMENSIONS,
    threshold: float = 7.0,
) -> dict:
    """Score ``output`` on each dimension and pass iff the minimum score clears threshold.

    ``scorer(output, dimension) -> float`` returns a 0..10 score. Returns the per-dimension
    scores, the minimum, and the verdict. A single weak dimension fails the review.
    """
    scores = {d: float(scorer(output, d)) for d in dimensions}
    worst = min(scores.values()) if scores else 0.0
    return {"scores": scores, "min": worst, "passed": worst >= threshold}
