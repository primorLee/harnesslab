"""Subagent / Multi-Agent orchestration primitives.

Three composable patterns, all model-agnostic (workers and scorers are plain callables):

* :func:`fan_out`     -- run one worker over many items concurrently, order preserved,
                         per-item failures isolated to ``None`` (never sinks the batch).
* :func:`pipeline`    -- push each item through a chain of stages independently.
* :func:`judge_panel` -- score candidates with a panel of judges, return the winner.

Concurrency is thread-based because agent work is I/O-bound (LLM / tool calls). Swap in a
process pool behind the same signatures if you ever go CPU-bound.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional, Sequence


def fan_out(
    items: Sequence,
    worker: Callable,
    max_workers: int = 8,
    on_error: Optional[Callable] = None,
) -> list:
    """Run ``worker(item)`` over ``items`` concurrently; return results in input order.

    A worker that raises drops that slot to ``None`` (optionally reported via
    ``on_error(item, exc)``) instead of failing the whole batch.
    """
    items = list(items)
    if not items:
        return []
    results: list = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(items)))) as ex:
        fut_to_i = {ex.submit(worker, it): i for i, it in enumerate(items)}
        for fut in as_completed(fut_to_i):
            i = fut_to_i[fut]
            try:
                results[i] = fut.result()
            except Exception as exc:  # noqa: BLE001 -- isolation is the point
                if on_error is not None:
                    on_error(items[i], exc)
                results[i] = None
    return results


def pipeline(items: Sequence, *stages: Callable, max_workers: int = 8) -> list:
    """Push each item through ``stages`` independently (no barrier between stages).

    Item A can be in stage 3 while item B is still in stage 1. A stage that raises drops
    that item to ``None`` and skips its remaining stages.
    """

    def run_chain(item):
        value = item
        for stage in stages:
            value = stage(value)
        return value

    return fan_out(items, run_chain, max_workers=max_workers)


def judge_panel(
    candidates: Sequence,
    scorers: Sequence[Callable],
    aggregate: Optional[Callable] = None,
    max_workers: int = 8,
):
    """Score each candidate with every scorer; return ``(winner, scores)``.

    ``scorers`` is a list of ``candidate -> float`` callables (diverse lenses, or the
    same judge sampled N times). ``aggregate`` defaults to the mean. A candidate whose
    every scorer failed gets ``-inf`` so it can never win by default.
    """
    candidates = list(candidates)
    scorers = list(scorers)
    if not candidates or not scorers:
        raise ValueError("judge_panel needs at least one candidate and one scorer")
    aggregate = aggregate or (lambda xs: sum(xs) / len(xs))

    pairs = [(c, s) for c in candidates for s in scorers]
    flat = fan_out(pairs, lambda cs: cs[1](cs[0]), max_workers=max_workers)

    n = len(scorers)
    scores = []
    for ci in range(len(candidates)):
        vals = [v for v in flat[ci * n : (ci + 1) * n] if v is not None]
        scores.append(aggregate(vals) if vals else float("-inf"))
    winner = max(range(len(candidates)), key=lambda i: scores[i])
    return candidates[winner], scores
