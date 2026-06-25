#!/usr/bin/env python
"""Real-LLM ablation: does shared graded experience help a *real* model on real tool use?

`bench/ablation.py` is a deterministic simulation. This one drives an actual LLM through
the agent loop with real tool calls. Each task asks the agent to compute a custom
operation (e.g. `blend`) whose rule it must INFER from worked examples, using add/mul
tools. On a wrong answer the environment reveals the correct value (a graded signal).
With experience ON, those worked examples are shared across the family, so the model can
infer the rule for siblings; with experience OFF every task starts cold.

    export HARNESSLAB_LLM_BASE_URL=https://api.deepseek.com/v1
    export HARNESSLAB_LLM_API_KEY=sk-...
    export HARNESSLAB_LLM_MODEL=deepseek-chat
    python bench/real_eval.py

Honest by design: it reports whatever the real numbers turn out to be.
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harnesslab import Agent, Episode, ExperienceStore, Gateway
from harnesslab.llm import make_llm

# Custom ops whose rule is hidden from the agent; it must infer them from worked examples.
OPS = {
    "blend": lambda a, b: a * 2 + b,
    "warp": lambda a, b: a + b * 3,
    "fold": lambda a, b: (a + b) * a,
}
VARIANTS = [(2, 3), (4, 1), (5, 2), (3, 4)]


def calculator() -> Gateway:
    gw = Gateway()
    gw.register("add", lambda a, b: a + b)
    gw.register("mul", lambda a, b: a * b)
    return gw


def run(mode: str, llm) -> dict:
    gw = calculator()
    shared = ExperienceStore() if mode == "on" else None
    first_try = solved = total = 0
    for op, rule in OPS.items():
        for a, b in VARIANTS:
            total += 1
            store = shared if mode == "on" else ExperienceStore()
            answer = rule(a, b)
            task = (
                f"Compute {op}({a}, {b}). '{op}' is a custom operation whose rule you must "
                f"INFER from any worked examples in the lessons above, using the add/mul "
                f"tools. Reply FINAL: <number>."
            )
            agent = Agent(
                llm, gateway=gw, experience=store, max_steps=4,
                tools_doc={"add": "add two numbers", "mul": "multiply two numbers"},
            )
            res = agent.run(task, verify=lambda t, ans, e=answer: str(e) in ans)
            n_calls = len([s for s in res.steps if s.action])
            solved += int(res.success)
            first_try += int(res.success and n_calls <= 2)
            # graded feedback: on a miss, reveal the worked example to the family
            if store is not None and not res.success:
                store.record(Episode(task=f"{op} custom operation", success=False,
                                     lesson=f"{op}({a},{b}) = {answer}", summary="graded feedback"))
    return {"first_try_rate": first_try / total, "solve_rate": solved / total, "n": total}


def main() -> None:
    if not os.environ.get("HARNESSLAB_LLM_API_KEY"):
        print("No LLM key set. Configure an OpenAI-compatible endpoint (DeepSeek works):")
        print("  export HARNESSLAB_LLM_BASE_URL=https://api.deepseek.com/v1")
        print("  export HARNESSLAB_LLM_API_KEY=sk-...")
        print("  export HARNESSLAB_LLM_MODEL=deepseek-chat")
        print("then re-run:  python bench/real_eval.py")
        return
    llm = make_llm()
    print(f"real-LLM ablation · model={os.environ.get('HARNESSLAB_LLM_MODEL', 'deepseek-chat')}\n")
    print(f"{'mode':<6}{'first-try solve':>18}{'final solve':>14}")
    for mode in ("off", "on"):
        r = run(mode, llm)
        print(f"{mode.upper():<6}{r['first_try_rate']*100:>16.0f}%{r['solve_rate']*100:>13.0f}%")


if __name__ == "__main__":
    main()
