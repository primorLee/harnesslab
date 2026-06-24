"""Run me: `python examples/quickstart.py` (no network, no keys needed).

Shows the self-evolving loop: the agent fails the first round, the failure is distilled
into a lesson, and the lesson is reinjected so the second round succeeds.

To drive it with a real model instead of the toy solver below, see the commented block
at the bottom -- it works with DeepSeek (or any OpenAI-compatible endpoint).
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # run from a fresh clone

from harnesslab import ExperienceStore, solve_with_experience


def toy_solver(task: str, seed: str):
    """Stand-in for a real agent. Only 'knows' the trick once it's been told."""
    if "startup circuit" in seed.lower():
        return True, "Converged: added the startup circuit from the prior lesson.", ""
    return False, "Stuck at 0V output.", "Bandgaps need a startup circuit or they latch at 0V."


def main() -> None:
    path = "/tmp/harnesslab-demo/exp.jsonl"
    if os.path.exists(path):
        os.remove(path)  # start from a clean slate so the demo is reproducible
    store = ExperienceStore(path)

    ok, _ = solve_with_experience(
        task="size a 1.2V bandgap reference",
        solver=toy_solver,
        store=store,
        tags=["analog", "bandgap"],
        max_rounds=3,
    )

    print(f"solved={ok} in {len(store.all())} attempt(s):")
    for i, ep in enumerate(store.all(), 1):
        print(f"  round {i}: [{'ok  ' if ep.success else 'FAIL'}] {ep.summary}")

    lesson = next((ep.lesson for ep in store.all() if not ep.success), "")
    print(f"\nlesson distilled from the failure:\n  {lesson}")

    print("\nwarm-start block a NEW similar task would receive:")
    print(store.seed_prompt("design a bandgap reference"))


# --- Driving it with a real model (DeepSeek / any OpenAI-compatible endpoint) ---
#
# from harnesslab.llm import make_llm
# llm = make_llm()  # reads HARNESSLAB_LLM_BASE_URL / _API_KEY / _MODEL from env
#
# def llm_solver(task, seed):
#     out = llm(f"{seed}\n\nTask: {task}\nReturn DONE on the first line if solved.")
#     ok = out.strip().upper().startswith("DONE")
#     return ok, out, ""            # plug your own lesson extraction here
#
# solve_with_experience(task="...", solver=llm_solver, store=store)


if __name__ == "__main__":
    main()
