"""Skill routing and a recipe library.

* :class:`SkillRegistry` -- register named capabilities and route a natural-language
  query to the best-matching one (the ``Skills`` mechanism: the harness, not a giant
  prompt, decides which tool/flow applies).
* :class:`RecipeBook` -- persist a *successful procedure* (an ordered list of steps) and
  retrieve it for a similar future task. Where the experience layer stores *lessons*
  (what went wrong), recipes store *what worked*, ready to replay.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .experience import Similarity, token_overlap


@dataclass
class Skill:
    name: str
    description: str
    run: Callable  # run(query, **kwargs)
    tags: list = field(default_factory=list)


class SkillRegistry:
    """A keyed set of skills with relevance-based routing."""

    def __init__(self, similarity: Similarity = token_overlap) -> None:
        self.skills: dict = {}
        self.similarity = similarity

    def register(self, skill: Skill) -> Skill:
        self.skills[skill.name] = skill
        return skill

    def _key(self, s: Skill) -> str:
        return " ".join([s.name, s.description, *s.tags])

    def match(self, query: str, k: int = 3) -> list:
        scored = [(self.similarity(query, self._key(s)), s) for s in self.skills.values()]
        scored = [(sc, s) for sc, s in scored if sc > 0]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored[:k]]

    def route(self, query: str, **kwargs):
        """Run the single best-matching skill. Raises if nothing matches."""
        top = self.match(query, k=1)
        if not top:
            raise LookupError(f"no skill matches: {query!r}")
        return top[0].run(query, **kwargs)


@dataclass
class Recipe:
    task: str  # the task pattern this recipe solves
    steps: list  # ordered procedure (strings, or anything JSON-serialisable)
    tags: list = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "Recipe":
        return cls(**json.loads(line))


class RecipeBook:
    """Append-only JSONL store of procedures, retrieved by task similarity."""

    def __init__(self, path, similarity: Similarity = token_overlap) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.similarity = similarity

    def add(self, recipe: Recipe) -> Recipe:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(recipe.to_json() + "\n")
        return recipe

    def all(self) -> list:
        if not self.path.exists():
            return []
        return [
            Recipe.from_json(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def find(self, task: str, k: int = 1) -> list:
        scored = [
            (self.similarity(task, r.task + " " + " ".join(r.tags)), r) for r in self.all()
        ]
        scored = [(s, r) for s, r in scored if s > 0]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:k]]
