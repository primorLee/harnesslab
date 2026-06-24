"""A reproducible ablation: does the experience layer actually help?

A harness claim is only worth a measured before/after. This is a *controlled* benchmark
with a transparent simulated agent, so it runs deterministically with no API key; the
exact same harness drives a real LLM agent (see ``bench/ablation.py``).

Agent model (stated, so the result isn't a black box): each task hides a family-wide
"trick" (a lesson). On an attempt the agent succeeds with probability ``p_warm`` if that
lesson is already in its warm-start seed, else with a small base rate ``p_base``. Either
way it names the trick in its post-mortem, so the lesson can be stored.

Question measured: does sharing ONE experience store across a family of related tasks
(experience ON) beat solving each task cold with its own store (experience OFF)? The
signal is *transfer* -- a lesson learned on one task lifting first-try success on its
siblings -- which is exactly what a self-evolving harness should buy you.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Optional

from .experience import ExperienceStore, solve_with_experience

_TOPICS = ["bandgap", "ldo", "ota", "pll", "comparator", "adc", "ring-osc", "serdes"]


@dataclass
class Task:
    name: str
    prompt: str
    family: str
    lesson: str


def make_suite(families: int = 6, variants: int = 4) -> list:
    """A suite of ``families * variants`` tasks; variants in a family share one trick."""
    suite = []
    for f in range(families):
        topic = _TOPICS[f % len(_TOPICS)]
        lesson = f"{topic}: apply design trick #{f}"
        for v in range(variants):
            suite.append(Task(f"{topic}-{v}", f"design a {topic}, configuration {v}", topic, lesson))
    return suite


def simulated_solver(task: Task, rng: random.Random, p_base: float, p_warm: float) -> Callable:
    """A transparent stand-in agent (see module docstring for its behaviour model)."""

    def solver(prompt: str, seed_prompt: str):
        warm = task.lesson.lower() in seed_prompt.lower()
        ok = rng.random() < (p_warm if warm else p_base)
        if ok:
            return True, f"solved {task.name}", task.lesson
        return False, f"missed the trick on {task.name}", task.lesson

    return solver


def run_ablation(
    suite: Optional[list] = None,
    rounds: int = 3,
    seed: int = 0,
    p_base: float = 0.1,
    p_warm: float = 0.95,
) -> dict:
    """Run the suite with experience OFF and ON; return per-mode metrics.

    OFF gives each task its own fresh store (no cross-task transfer); ON shares one store
    across the whole suite. Both modes use the same RNG seed for a fair comparison.
    """
    suite = suite or make_suite()
    report = {}
    for mode in ("off", "on"):
        rng = random.Random(seed)
        shared = ExperienceStore() if mode == "on" else None  # in-memory
        first_try = solved = evals = 0
        for task in suite:
            store = shared if mode == "on" else ExperienceStore()
            base = simulated_solver(task, rng, p_base, p_warm)
            counter = {"n": 0}

            def solver(prompt, seed_prompt, _base=base, _c=counter):
                _c["n"] += 1
                return _base(prompt, seed_prompt)

            ok, _ = solve_with_experience(
                task.prompt, solver, store, tags=[task.family], max_rounds=rounds
            )
            evals += counter["n"]
            solved += int(ok)
            first_try += int(ok and counter["n"] == 1)

        n = len(suite)
        report[mode] = {
            "tasks": n,
            "solve_rate": solved / n,
            "first_try_rate": first_try / n,
            "evals": evals,
        }
    return report
