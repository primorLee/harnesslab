"""File-based long-term memory with anti-staleness recall.

Each memory is one file with YAML-ish frontmatter. Recall ranks by relevance *and*
drops memories whose referenced artifacts (files, symbols, endpoints) no longer
resolve -- so the agent never acts on advice that has gone stale against a codebase
that moved underneath it. Staleness is the failure mode that quietly poisons
long-lived agent memory; here it is a first-class, testable concern.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

_WORD = re.compile(r"[a-z0-9]+")
_LINK = re.compile(r"\[\[([^\]]+)\]\]")


def _tokens(text: str) -> set:
    return set(_WORD.findall(text.lower()))


def relevance(query: str, mem: "Memory") -> float:
    """Fraction of the query's tokens covered by the memory. Dependency-free default."""
    q = _tokens(query)
    m = _tokens(mem.description + " " + mem.body)
    if not q or not m:
        return 0.0
    return len(q & m) / len(q)


# A ref resolves if this returns True. Default: it's a path that exists.
Validator = Callable[[str], bool]


def _default_validator(ref: str) -> bool:
    return Path(ref).exists()


@dataclass
class Memory:
    """A single fact plus the artifacts it depends on to stay true."""

    name: str
    description: str
    body: str = ""
    refs: list = field(default_factory=list)
    ts: float = 0.0

    @property
    def links(self) -> list:
        """``[[other-memory]]`` references found in the body."""
        return _LINK.findall(self.body)


class MemoryStore:
    """One-file-per-memory store with relevance recall and staleness pruning."""

    def __init__(self, directory, validator: Validator = _default_validator) -> None:
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.validator = validator

    def write(self, mem: Memory) -> Path:
        if not mem.ts:
            mem.ts = time.time()
        front = ["---", f"name: {mem.name}", f"description: {mem.description}"]
        if mem.refs:
            front.append("refs: " + ", ".join(mem.refs))
        front += [f"ts: {mem.ts}", "---", "", mem.body, ""]
        path = self.dir / f"{mem.name}.md"
        path.write_text("\n".join(front), encoding="utf-8")
        return path

    @staticmethod
    def _parse(path: Path) -> Memory:
        text = path.read_text(encoding="utf-8")
        name, desc, refs, ts, body = path.stem, "", [], 0.0, text
        if text.startswith("---"):
            parts = text.split("---", 2)  # ['', frontmatter, body] -- body may contain '---'
            if len(parts) == 3:
                _, front, body = parts
                for line in front.strip().splitlines():
                    key, sep, val = line.partition(":")
                    if not sep:
                        continue
                    key, val = key.strip(), val.strip()
                    if key == "name" and val:
                        name = val
                    elif key == "description":
                        desc = val
                    elif key == "refs":
                        refs = [r.strip() for r in val.split(",") if r.strip()]
                    elif key == "ts":
                        try:
                            ts = float(val)
                        except ValueError:
                            ts = 0.0
        return Memory(name=name, description=desc, body=body.strip(), refs=refs, ts=ts)

    def read_all(self) -> list:
        return [self._parse(p) for p in sorted(self.dir.glob("*.md"))]

    def is_stale(self, mem: Memory) -> bool:
        """True if any referenced artifact no longer resolves."""
        return any(not self.validator(ref) for ref in mem.refs)

    def stale(self) -> list:
        """Memories that should be reviewed or pruned -- their world moved."""
        return [m for m in self.read_all() if self.is_stale(m)]

    def recall(self, query: str, k: int = 5, drop_stale: bool = True) -> list:
        """Return up to ``k`` relevant memories, skipping stale ones by default."""
        cands = self.read_all()
        if drop_stale:
            cands = [m for m in cands if not self.is_stale(m)]
        scored = [(relevance(query, m), m) for m in cands]
        scored = [(s, m) for s, m in scored if s > 0]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:k]]
