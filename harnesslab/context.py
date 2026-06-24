"""Long-context management: stay grounded across a long, multi-phase run.

Two jobs the model won't do for you on a 50+ step task:

* keep the goal / anchors in view every phase (re-grounding), and
* fit the working context into a token budget by compacting the old, not dropping the
  important.

Token-budget-aware assembly: pinned blocks always survive; the rest are kept by priority;
overflow is compacted (pluggable summariser) or dropped lowest-priority-first.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence


def estimate_tokens(text: str) -> int:
    """~4 chars/token -- a provider-agnostic heuristic, good enough for budgeting."""
    return max(1, (len(text) + 3) // 4)


@dataclass
class Block:
    """A unit of context with a keep-priority."""

    text: str
    priority: int = 0  # higher = kept longer under pressure
    pinned: bool = False  # pinned blocks are never dropped or compacted


# Shorten a block's text (an LLM summariser in practice).
Compactor = Callable[[str], str]


def assemble(
    blocks: Sequence[Block], budget: int, compactor: Optional[Compactor] = None
) -> str:
    """Pack ``blocks`` into ``budget`` tokens, preserving the input order in the output.

    Pinned blocks are always included (keep them small -- they bypass the budget). The
    rest are admitted by descending priority; a block that won't fit is compacted if a
    ``compactor`` is given, else dropped.
    """
    pinned = [b for b in blocks if b.pinned]
    rest = sorted((b for b in blocks if not b.pinned), key=lambda b: b.priority, reverse=True)

    chosen: list = []
    used = 0
    for b in pinned:
        chosen.append((b, b.text))
        used += estimate_tokens(b.text)
    for b in rest:
        need = estimate_tokens(b.text)
        if used + need <= budget:
            chosen.append((b, b.text))
            used += need
        elif compactor is not None:
            short = compactor(b.text)
            need = estimate_tokens(short)
            if used + need <= budget:
                chosen.append((b, short))
                used += need

    order = {id(b): i for i, b in enumerate(blocks)}
    chosen.sort(key=lambda bt: order[id(bt[0])])
    return "\n\n".join(text for _, text in chosen)


def reground(goal: str, *anchors: str) -> Block:
    """A pinned block that re-states the goal (and anchors) -- re-inject it every phase."""
    body = goal if not anchors else goal + "\n" + "\n".join(f"- {a}" for a in anchors)
    return Block(f"## Goal (re-grounded)\n{body}", priority=10_000, pinned=True)


def window(
    turns: Sequence[str], keep_recent: int = 6, compactor: Optional[Compactor] = None
) -> list:
    """Recent turns verbatim; older turns folded into one compacted summary block.

    This is the long-horizon anti-forgetting move: don't let early context fall off a
    cliff -- summarise it and keep the gist.
    """
    turns = list(turns)
    if len(turns) <= keep_recent:
        return [Block(t, priority=1) for t in turns]
    old, recent = turns[:-keep_recent], turns[-keep_recent:]
    joined = "\n".join(old)
    summary = compactor(joined) if compactor else f"[summary of {len(old)} earlier turns]"
    return [Block(summary, priority=2)] + [Block(t, priority=1) for t in recent]
