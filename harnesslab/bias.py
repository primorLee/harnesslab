"""Divergence tools: defend against premature convergence and mode collapse.

The first plausible idea is a trap. A harness that always commits to attempt #1 inherits
the model's anchoring. These primitives force breadth *before* commitment:

* :func:`diverse_sample` -- keep sampling until you have N mutually-dissimilar candidates;
* :func:`lenses`        -- generate one candidate per framing/domain, so coverage is
                           structural rather than luck.
"""
from __future__ import annotations

from typing import Callable, Sequence

from .experience import Similarity, token_overlap


def diverse_sample(
    generate: Callable,
    n: int,
    similarity: Similarity = token_overlap,
    threshold: float = 0.6,
    max_tries: int = 0,
) -> list:
    """Collect ``n`` candidates, no two more than ``threshold`` similar.

    ``generate()`` returns a candidate string (ideally stochastic). Rejects a candidate
    too close to one already kept. Stops after ``max_tries`` attempts (default ``8*n``)
    even if fewer than ``n`` distinct candidates were found -- returns what it has.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    max_tries = max_tries or 8 * n
    kept: list = []
    for _ in range(max_tries):
        if len(kept) >= n:
            break
        cand = generate()
        if all(similarity(cand, k) < threshold for k in kept):
            kept.append(cand)
    return kept


def lenses(generate: Callable, lenses: Sequence[str]) -> list:
    """One candidate per lens: ``generate(lens) -> str``. Coverage by construction.

    Lenses are framings ("safety-first", "cost-first", "from biology", ...). Returns a
    list of ``(lens, candidate)`` pairs, guaranteeing breadth across the given angles.
    """
    return [(lens, generate(lens)) for lens in lenses]
