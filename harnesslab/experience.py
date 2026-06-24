"""Self-evolving experience store.

An agent that cannot learn from its own runs repeats its own mistakes. This module
captures each attempt as an :class:`Episode`, distills a lesson from failures, and
reinjects the most relevant prior lessons as warm-start context for similar future
tasks. That capture -> distill -> reinject loop is what makes the harness *self-evolving*:
the agent gets better at a task family without retraining the model.

Clean-room and domain-neutral, distilled from a production analog-IC design agent whose
experience layer warm-started a CMA-ES/GP optimizer across a 154-netlist benchmark and a
60+ paper reproduction suite. No product or customer code is included.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional, Tuple

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set:
    return set(_WORD.findall(text.lower()))


def token_overlap(a: str, b: str) -> float:
    """Jaccard similarity over word tokens. Cheap, dependency-free default.

    Swap in an embedding-based similarity for production; the store only needs a
    ``Callable[[str, str], float]``.
    """
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


Similarity = Callable[[str, str], float]
Distiller = Callable[["Episode"], str]
# solver(task, seed_prompt) -> (success, summary, lesson)
Solver = Callable[[str, str], Tuple[bool, str, str]]


@dataclass
class Episode:
    """One attempt at a task and what was learned from it."""

    task: str
    success: bool
    summary: str = ""
    lesson: str = ""
    tags: list = field(default_factory=list)
    steps: int = 0
    ts: float = 0.0
    id: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "Episode":
        return cls(**json.loads(line))


def _heuristic_distiller(ep: "Episode") -> str:
    """Fallback lesson generator used when no LLM-backed distiller is supplied."""
    if ep.lesson:
        return ep.lesson
    body = ep.summary.strip()
    head = body.splitlines()[0] if body else ep.task
    return f"A prior attempt failed here: {head}. Check this assumption before retrying."


class ExperienceStore:
    """Append-only JSONL store of episodes with warm-start retrieval.

    Parameters
    ----------
    path:
        JSONL file the episodes are appended to (parent dirs are created).
    similarity:
        Ranks a query task against stored tasks. Defaults to token overlap.
    distiller:
        Turns a failed episode into a reusable lesson. Defaults to a heuristic;
        pass an LLM-backed callable for real distillation.
    """

    def __init__(
        self,
        path,
        similarity: Similarity = token_overlap,
        distiller: Optional[Distiller] = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.similarity = similarity
        self.distiller = distiller or _heuristic_distiller

    def record(self, episode: Episode) -> Episode:
        """Persist an episode, distilling a lesson first if it failed without one."""
        if not episode.ts:
            episode.ts = time.time()
        if not episode.id:
            episode.id = f"{int(episode.ts * 1000):x}-{abs(hash(episode.task)) & 0xFFFF:04x}"
        if not episode.success and not episode.lesson:
            episode.lesson = self.distiller(episode)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(episode.to_json() + "\n")
        return episode

    def all(self) -> list:
        if not self.path.exists():
            return []
        return [
            Episode.from_json(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def retrieve(self, task: str, k: int = 3, prefer_failures: bool = True) -> list:
        """Return up to ``k`` prior episodes most relevant to ``task``.

        Failures are nudged up the ranking: they carry the actionable lessons.
        """
        scored = []
        for ep in self.all():
            sim = self.similarity(task, ep.task + " " + " ".join(ep.tags))
            if sim <= 0:
                continue
            boost = 1.25 if (prefer_failures and not ep.success) else 1.0
            scored.append((sim * boost, ep))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:k]]

    def seed_prompt(self, task: str, k: int = 3) -> str:
        """Render retrieved lessons into a prompt block to prepend to the next attempt."""
        seeds = self.retrieve(task, k=k)
        if not seeds:
            return ""
        lines = ["## Lessons from prior attempts (warm-start)"]
        for ep in seeds:
            flag = "FAILED" if not ep.success else "ok"
            lines.append(f"- [{flag}] {ep.lesson or ep.summary}")
        return "\n".join(lines)


def solve_with_experience(
    task: str,
    solver: Solver,
    store: ExperienceStore,
    *,
    tags: Optional[list] = None,
    max_rounds: int = 3,
) -> Tuple[bool, Episode]:
    """Run ``solver`` against ``task``, warm-starting each round from prior lessons.

    The solver receives ``(task, seed_prompt)`` and returns
    ``(success, summary, lesson)``. Every round is recorded, so failures in early
    rounds become warm-start seeds for later rounds (and future calls).
    """
    tags = list(tags or [])
    last: Optional[Episode] = None
    for _ in range(max_rounds):
        seed = store.seed_prompt(task)
        success, summary, lesson = solver(task, seed)
        last = store.record(
            Episode(task=task, success=success, summary=summary, lesson=lesson, tags=tags)
        )
        if success:
            return True, last
    assert last is not None  # max_rounds >= 1
    return False, last
