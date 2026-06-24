"""Closed-loop black-box optimizer.

A self-adapting (1+lambda) evolution strategy with the Rechenberg 1/5th success rule.
It needs nothing but an objective ``x -> float`` (lower is better), so it drives an agent
loop against any evaluator: a simulator, a metric, an LLM-scored rubric. This is the
domain-neutral core of a production design-space optimizer; swap in ``cma`` or a GP
surrogate behind the same :func:`optimize` signature when you outgrow it.

Deterministic for a fixed ``seed`` -- reproducible runs are a feature, not an accident.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence


@dataclass
class Result:
    x: list  # best parameter vector found
    fx: float  # its objective value
    evals: int  # objective evaluations spent
    history: list = field(default_factory=list)  # best-so-far per generation


def _clip(x: Sequence, bounds: Optional[Sequence]) -> list:
    if not bounds:
        return list(x)
    return [min(hi, max(lo, xi)) for xi, (lo, hi) in zip(x, bounds)]


def optimize(
    objective: Callable,
    x0: Sequence,
    bounds: Optional[Sequence] = None,
    budget: int = 200,
    sigma0: float = 0.3,
    lam: int = 8,
    seed: int = 0,
    target: Optional[float] = None,
) -> Result:
    """Minimize ``objective`` starting from ``x0`` within an evaluation ``budget``.

    Parameters
    ----------
    bounds:
        Optional per-dimension ``(low, high)`` pairs; offspring are clipped into the box.
    sigma0, lam:
        Initial mutation step size and offspring per generation.
    target:
        Stop early once the objective reaches this value or lower.
    """
    rng = random.Random(seed)
    dim = len(x0)
    parent = _clip(x0, bounds)
    f_parent = objective(parent)
    evals = 1
    sigma = sigma0
    history = [f_parent]

    while evals < budget:
        better = 0
        best_f, best_x = f_parent, parent
        for _ in range(lam):
            if evals >= budget:
                break
            child = _clip([parent[i] + sigma * rng.gauss(0, 1) for i in range(dim)], bounds)
            fc = objective(child)
            evals += 1
            if fc < f_parent:
                better += 1
            if fc < best_f:
                best_f, best_x = fc, child

        f_parent, parent = best_f, best_x
        history.append(f_parent)

        # Rechenberg 1/5th rule: succeed often -> step out boldly; rarely -> step in.
        ratio = better / lam
        sigma *= 1.5 if ratio > 0.2 else 0.817

        if target is not None and f_parent <= target:
            break

    return Result(x=list(parent), fx=f_parent, evals=evals, history=history)
