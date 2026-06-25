#!/usr/bin/env python
"""Real-LLM ablation: does the experience layer transfer a learned rule across a family?

`bench/ablation.py` is a deterministic simulation. This one drives an actual LLM through
the agent loop with real tool calls. Each task asks the agent to compute a custom
operation (e.g. `blend`) using only add/mul tools — but the operation's rule is NOT given
up front. On a failed task the environment reveals the rule as graded feedback. With
experience ON, that rule is shared across the family, so siblings are solvable; with
experience OFF every task is cold and the rule never carries over.

It measures a harness property (capture-on-failure + cross-task transfer), on a real
model, honestly: it reports whatever DeepSeek actually scores.

    export HARNESSLAB_LLM_BASE_URL=https://api.deepseek.com/v1
    export HARNESSLAB_LLM_API_KEY=sk-...
    export HARNESSLAB_LLM_MODEL=deepseek-chat
    python bench/real_eval.py
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harnesslab import Agent, Episode, ExperienceStore, Gateway
from harnesslab.llm import make_llm

# Custom ops: the rule is hidden until the environment reveals it on a failed task.
OPS = {
    "blend": (lambda a, b: a * 2 + b, "blend(a, b) = a*2 + b"),
    "warp": (lambda a, b: a + b * 3, "warp(a, b) = a + b*3"),
    "fold": (lambda a, b: (a + b) * a, "fold(a, b) = (a + b) * a"),
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
    solved = calls = total = 0
    for op, (rule, rule_text) in OPS.items():
        for a, b in VARIANTS:
            total += 1
            store = shared if mode == "on" else ExperienceStore()
            answer = rule(a, b)
            task = (
                f"Compute {op}({a}, {b}) using the add/mul tools. If the lessons above "
                f"define '{op}', use that definition. Reply FINAL: <number>."
            )
            agent = Agent(
                llm, gateway=gw, experience=store, max_steps=5,
                tools_doc={"add": "add two numbers", "mul": "multiply two numbers"},
            )
            res = agent.run(task, verify=lambda t, ans, e=answer: str(e) in ans)
            solved += int(res.success)
            calls += len([s for s in res.steps if s.action])
            # graded feedback: on a miss, teach the family the rule
            if mode == "on" and not res.success:
                store.record(Episode(task=f"the {op} operation", success=False,
                                     lesson=rule_text, summary="graded feedback"))
    return {"solve_rate": solved / total, "avg_calls": calls / total, "n": total}


def main() -> None:
    if not os.environ.get("HARNESSLAB_LLM_API_KEY"):
        print("No LLM key set. Configure an OpenAI-compatible endpoint (DeepSeek works):")
        print("  export HARNESSLAB_LLM_BASE_URL=https://api.deepseek.com/v1")
        print("  export HARNESSLAB_LLM_API_KEY=sk-...")
        print("  export HARNESSLAB_LLM_MODEL=deepseek-chat")
        print("then re-run:  python bench/real_eval.py")
        return
    llm = make_llm()
    model = os.environ.get("HARNESSLAB_LLM_MODEL", "deepseek-chat")
    print(f"real-LLM ablation · model={model} · {len(OPS) * len(VARIANTS)} tasks\n")
    print(f"{'mode':<6}{'solve rate':>13}{'avg tool calls':>17}")
    for mode in ("off", "on"):
        r = run(mode, llm)
        print(f"{mode.upper():<6}{r['solve_rate']*100:>12.0f}%{r['avg_calls']:>17.1f}")


if __name__ == "__main__":
    main()
