"""Run me: `python examples/tool_agent.py`  (no network, no keys).

A *complete* agent built from harnesslab: an LLM drives a tool-use loop over a Gateway of
tools, and the experience layer records the run. The LLM here is a tiny deterministic
stand-in so the demo runs offline; the commented block at the bottom swaps in a real
model (DeepSeek or any OpenAI-compatible endpoint).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harnesslab import Agent, ExperienceStore, Gateway

# --- the agent's tools ---
gw = Gateway()
gw.register("add", lambda a, b: a + b)
gw.register("mul", lambda a, b: a * b)


def fake_llm(prompt: str) -> str:
    """A 3-line stand-in that plays out a two-step plan for the demo task."""
    if "ACTION mul" in prompt:  # multiply already done -> finish
        return "FINAL: (2+3)*10 = 50"
    if "ACTION add" in prompt:  # add done -> multiply the result by 10
        return 'ACTION: mul\nARGS: {"a": 5, "b": 10}'
    return 'ACTION: add\nARGS: {"a": 2, "b": 3}'  # first step


def main() -> None:
    store = ExperienceStore()
    agent = Agent(
        fake_llm, gateway=gw, experience=store,
        tools_doc={"add": "add two numbers", "mul": "multiply two numbers"},
    )
    res = agent.run("compute (2+3)*10")

    print("answer     :", res.answer)
    print("tool calls :", [(s.action, s.observation) for s in res.steps if s.action])
    print("gateway log:", gw.stats())
    print("episode ok :", store.all()[0].success)


# --- driving it with a real model (DeepSeek / any OpenAI-compatible endpoint) ---
#
# from harnesslab.llm import make_llm
# agent = Agent(make_llm(), gateway=gw, experience=store,
#               tools_doc={"add": "add two numbers", "mul": "multiply two numbers"})
# print(agent.run("compute (2+3)*10").answer)
# # set HARNESSLAB_LLM_BASE_URL=https://api.deepseek.com/v1  HARNESSLAB_LLM_API_KEY=sk-...


if __name__ == "__main__":
    main()
