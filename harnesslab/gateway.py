"""Unified tool / simulation gateway with auto-record.

Every tool an agent can call goes through one door. The gateway routes a call to a
registered backend *and* captures it -- name, args, success, duration -- into an
in-memory run log, optionally distilling failures into an :class:`~harnesslab.experience.
ExperienceStore`. That single choke point is what makes an agent's actions observable,
replayable, and a source of self-evolution instead of a black box.

This is the domain-neutral shape of a production "all simulations through one bridge,
every run recorded" gateway, with the circuit-specific parts removed.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .experience import Episode, ExperienceStore


def _brief(obj, limit: int = 80) -> str:
    text = repr(obj)
    return text if len(text) <= limit else text[: limit - 1] + "…"


@dataclass
class Call:
    """One recorded gateway invocation."""

    name: str
    args: dict
    ok: bool
    duration: float
    result: object = None
    error: str = ""


class Gateway:
    """Route tool calls through registered backends and record every one."""

    def __init__(self, experience: Optional[ExperienceStore] = None) -> None:
        self._backends: dict = {}
        self.calls: list = []
        self.experience = experience

    def register(self, name: str, fn: Callable) -> Callable:
        self._backends[name] = fn
        return fn

    def backend(self, name: str) -> Callable:
        """Decorator form: ``@gw.backend("simulate")``."""

        def deco(fn: Callable) -> Callable:
            self.register(name, fn)
            return fn

        return deco

    def call(self, name: str, **kwargs):
        """Invoke backend ``name``; record the call whether it succeeds or raises."""
        if name not in self._backends:
            raise KeyError(f"no backend registered: {name!r}")
        start = time.time()
        ok, result, error = True, None, ""
        try:
            result = self._backends[name](**kwargs)
            return result
        except Exception as exc:  # noqa: BLE001 -- recorded, then re-raised
            ok, error = False, f"{type(exc).__name__}: {exc}"
            raise
        finally:
            self.calls.append(
                Call(
                    name=name,
                    args=dict(kwargs),
                    ok=ok,
                    duration=time.time() - start,
                    result=result if ok else None,
                    error=error,
                )
            )
            if self.experience is not None and not ok:
                self.experience.record(
                    Episode(
                        task=f"call {name}({_brief(kwargs)})",
                        success=False,
                        summary=error,
                        tags=["gateway", name],
                    )
                )

    def stats(self) -> dict:
        """Quick run-log summary: total / ok / failed call counts."""
        ok = sum(1 for c in self.calls if c.ok)
        return {"total": len(self.calls), "ok": ok, "failed": len(self.calls) - ok}
