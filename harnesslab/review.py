"""Adversarial self-verification.

A capable model still emits plausible-but-wrong outputs. Verifying them is the harness's
job, not the model's good intentions. Two patterns, both model-agnostic:

* :func:`refute_vote`        -- N independent skeptics each try to *refute* a claim;
                                it survives only if a majority fail to.
* :func:`writer_critic_judge` -- a writer drafts, a critic attacks, the writer revises,
                                a judge scores. (Generalizes a writer -> reviewer -> lead
                                editorial pipeline into three swappable roles.)

Default to skepticism: a claim is kept only when the panel cannot break it.
"""
from __future__ import annotations

from typing import Callable, Optional

from .orchestration import fan_out


def refute_vote(
    claim: str,
    skeptic: Callable,
    n: int = 3,
    threshold: Optional[int] = None,
    max_workers: int = 8,
) -> dict:
    """Run ``n`` skeptics on ``claim``; survive only if refutations stay below threshold.

    ``skeptic(claim) -> bool`` returns ``True`` when it believes it has refuted the claim.
    ``threshold`` defaults to a simple majority. Skeptics that error are counted as
    *not* refuting (a failed attack is not evidence against the claim).
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    threshold = threshold if threshold is not None else (n // 2 + 1)
    votes = fan_out(range(n), lambda _i: bool(skeptic(claim)), max_workers=max_workers)
    refutations = sum(1 for v in votes if v)
    return {
        "claim": claim,
        "n": n,
        "refutations": refutations,
        "threshold": threshold,
        "survives": refutations < threshold,
    }


def writer_critic_judge(
    task: str,
    writer: Callable,
    critic: Callable,
    judge: Callable,
    max_rounds: int = 2,
) -> dict:
    """Draft -> critique -> revise loop, then score.

    Roles (all swappable callables):
      * ``writer(task, feedback) -> str``  -- drafts or revises given critic feedback
      * ``critic(task, draft) -> str``     -- returns a critique, or "" to pass
      * ``judge(task, draft) -> float``    -- final score

    Stops early once the critic passes (returns empty). Returns the vetted output, its
    score, and how many revision rounds it took.
    """
    draft = writer(task, "")
    rounds = 0
    for _ in range(max_rounds):
        critique = critic(task, draft)
        if not critique or not critique.strip():
            break
        draft = writer(task, critique)
        rounds += 1
    return {"output": draft, "score": judge(task, draft), "revisions": rounds}
