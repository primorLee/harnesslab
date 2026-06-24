"""The agent loop -- the piece that composes the harness into a running agent.

`Agent` runs a ReAct-style think -> act -> observe loop over a set of tools, and wires in
the rest of the harness: it warm-starts from the experience layer, recalls long-term
memory, calls tools through the recorded gateway, and (optionally) verifies its own answer
and records the episode so the *next* run is smarter. Everything is model-agnostic: the
LLM is a plain ``str -> str`` callable.

Tool protocol (a deliberately simple text convention, so it works on any chat endpoint
without native function-calling): the model replies with either

    ACTION: <tool_name>
    ARGS: {"arg": "value"}

to call a tool, or

    FINAL: <answer>

to finish.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from .experience import Episode, ExperienceStore
from .gateway import Gateway
from .memory import MemoryStore

LLM = Callable[[str], str]

_ACTION_RE = re.compile(r"ACTION:\s*([A-Za-z0-9_\-]+)", re.I)
_ARGS_RE = re.compile(r"ARGS:\s*(\{.*\})", re.I | re.S)
_FINAL_RE = re.compile(r"FINAL:\s*(.+)", re.I | re.S)

_PROMPT = """You are a tool-using agent. Solve the task using the available tools.

{lessons}{memories}Available tools:
{tools}

Reply in ONE of these two forms, and nothing else:
  ACTION: <tool_name>
  ARGS: {{"arg": "value"}}
or, when you have the answer:
  FINAL: <answer>

Task: {task}

History so far:
{history}
"""


@dataclass
class Step:
    thought: str
    action: Optional[str]  # tool name, or None when finishing
    args: dict
    observation: str = ""


@dataclass
class AgentResult:
    task: str
    answer: str
    success: bool  # verified correct (if a verifier was given) else "produced an answer"
    steps: list = field(default_factory=list)


class Agent:
    """A model-agnostic tool-using agent that composes the harness.

    Parameters
    ----------
    llm:        ``str -> str`` chat callable (see :mod:`harnesslab.llm`).
    gateway:    tools the agent may call (see :class:`~harnesslab.gateway.Gateway`).
    memory:     optional long-term memory recalled into the prompt.
    experience: optional experience store -- warm-starts the prompt and records episodes.
    tools_doc:  ``{name: one-line description}`` shown to the model; defaults to the
                gateway's registered backend names.
    """

    def __init__(
        self,
        llm: LLM,
        gateway: Optional[Gateway] = None,
        memory: Optional[MemoryStore] = None,
        experience: Optional[ExperienceStore] = None,
        max_steps: int = 8,
        tools_doc: Optional[dict] = None,
    ) -> None:
        self.llm = llm
        self.gateway = gateway
        self.memory = memory
        self.experience = experience
        self.max_steps = max_steps
        if tools_doc is not None:
            self.tools_doc = tools_doc
        elif gateway is not None:
            self.tools_doc = {name: "" for name in gateway._backends}
        else:
            self.tools_doc = {}

    def _tools_block(self) -> str:
        if not self.tools_doc:
            return "(none)"
        return "\n".join(f"- {n}: {d}".rstrip() for n, d in self.tools_doc.items())

    def _call_tool(self, tool: str, args: dict) -> str:
        if self.gateway is None:
            return "error: no tools available"
        try:
            return str(self.gateway.call(tool, **args))
        except Exception as exc:  # noqa: BLE001 -- surfaced to the model as an observation
            return f"error: {type(exc).__name__}: {exc}"

    def run(self, task: str, verify: Optional[Callable] = None) -> AgentResult:
        """Run the loop until the agent finishes or exhausts its step budget.

        If ``verify(task, answer) -> bool`` is given, it decides episode success (so the
        experience layer learns from *wrong* answers too); otherwise success means the
        agent produced a final answer in time.
        """
        lessons = ""
        if self.experience is not None:
            seed = self.experience.seed_prompt(task)
            if seed:
                lessons = seed + "\n\n"
        memories = ""
        if self.memory is not None:
            recalled = self.memory.recall(task, k=3)
            if recalled:
                memories = "Relevant notes:\n" + "\n".join(
                    f"- {m.description}: {m.body}" for m in recalled
                ) + "\n\n"

        steps: list = []
        history = ""
        answer = ""
        finished = False
        for _ in range(self.max_steps):
            prompt = _PROMPT.format(
                lessons=lessons, memories=memories, tools=self._tools_block(),
                task=task, history=history or "(nothing yet)",
            )
            reply = self.llm(prompt)
            final, action = _FINAL_RE.search(reply), _ACTION_RE.search(reply)

            if final and not (action and action.start() < final.start()):
                answer = final.group(1).strip()
                finished = True
                steps.append(Step(reply.strip(), None, {}, answer))
                break
            if action:
                tool = action.group(1)
                args: dict = {}
                argm = _ARGS_RE.search(reply)
                if argm:
                    try:
                        args = json.loads(argm.group(1))
                    except (ValueError, TypeError):
                        args = {}
                obs = self._call_tool(tool, args)
                steps.append(Step(reply.strip(), tool, args, obs))
                history += f"\nACTION {tool}({args}) -> {obs}"
            else:
                # Unparseable reply: take it as the final answer rather than loop blindly.
                answer = reply.strip()
                finished = True
                steps.append(Step(reply.strip(), None, {}, answer))
                break

        success = verify(task, answer) if verify is not None else finished
        if self.experience is not None:
            self.experience.record(
                Episode(
                    task=task,
                    success=bool(success),
                    summary=answer if finished else "did not finish within step budget",
                    steps=len(steps),
                )
            )
        return AgentResult(task=task, answer=answer, success=bool(success), steps=steps)
