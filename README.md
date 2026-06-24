# harnesslab

**A self-evolving, model-agnostic agent harness.**

> *Model + Harness = Agent.* This is the **harness** half — the scaffolding that lives
> *outside* the model and turns a capable LLM into an agent that **learns from its own
> runs** instead of repeating its own mistakes.

`harnesslab` is a small, dependency-light toolkit for the parts of an agent the model
doesn't give you for free: **long-term memory that doesn't go stale**, an **experience
layer** that distills lessons from failures and reinjects them as warm-start context,
and — on the roadmap — **multi-agent self-verification** and an **evaluation harness** to
measure whether any of it actually helps.

It is distilled *clean-room and domain-neutral* from a production analog-IC design agent
whose experience layer warm-started a CMA-ES / GP optimizer across a **154-netlist
benchmark** and a **60+ paper reproduction suite**. No product, customer, or
infrastructure code is included — only the general method.

---

## The problem

The gap between a model's raw capability and an agent's real-world performance is mostly
*harness*, not weights. Three failure modes show up again and again:

1. **The agent repeats its own mistakes.** Each run starts cold; yesterday's hard-won
   lesson is gone. There is no cheap memory of *what went wrong and why*.
2. **Long-term memory rots.** Notes that referenced a file, symbol, or endpoint stay in
   the store long after that artifact moved — and the agent confidently acts on advice
   that is no longer true.
3. **Nobody measures the harness.** Harness changes ship on vibes because there's no
   before/after on a real task suite.

`harnesslab` takes these as first-class, testable concerns.

## The idea: a self-evolving loop

```
        ┌─────────── retrieve warm-start seeds ──────────┐
        │                                                ▼
   ExperienceStore                                  attempt task
        ▲                                                │
        └──── record outcome ◄── distill lesson ◄── (on failure) ─┘
```

`record → distill-on-failure → retrieve` is what makes the harness *self-evolving*: the
agent gets better at a **task family** with zero model retraining. Failures are nudged up
the retrieval ranking on purpose — they carry the actionable lessons.

## What's here (v0.1)

| Module | What it does | Maps to |
|---|---|---|
| `experience` | Self-evolving episode store: record → distill-on-failure → retrieve warm-start seeds; `solve_with_experience()` runs the loop. | self-evolving agent, experience replay |
| `memory` | File-based long-term memory with **anti-staleness** recall — drops advice whose referenced artifacts no longer resolve (pluggable validator: files, symbols, endpoints). | long-term memory |
| `llm` | Thin model-agnostic adapter; any OpenAI-compatible endpoint, **DeepSeek out of the box**. No keys read at import time. | tool/model plumbing |

Core is **stdlib-only**. Swap token-overlap similarity for embeddings, or the heuristic
distiller for an LLM, behind the same interfaces.

## Quickstart

```bash
python examples/quickstart.py     # no network, no keys
```

```python
from harnesslab import ExperienceStore, solve_with_experience

store = ExperienceStore("exp.jsonl")

def solver(task, seed):                 # seed = warm-start lessons from prior runs
    ...                                  # your agent; returns (success, summary, lesson)

ok, last = solve_with_experience("size a 1.2V bandgap", solver, store, max_rounds=3)
```

Anti-staleness in one breath:

```python
from harnesslab import Memory, MemoryStore

store = MemoryStore("memory/")
store.write(Memory(name="ldo-trim", description="how the LDO trim works",
                   body="Set the 6-bit trim before measuring.",
                   refs=["src/ldo.py"]))          # this memory is only valid while src/ldo.py exists
store.recall("ldo trim")                          # silently skips memories gone stale
store.stale()                                     # ...and lists them for pruning
```

## Evaluation (work in progress)

A harness claim is only worth a measured before/after, so this section will hold an
**ablation, not adjectives**: experience layer **ON vs OFF** on a public multi-step task
suite, reporting success rate and steps-to-solve across rounds. Protocol is landing next;
numbers will appear here when they're real.

## Roadmap

- [ ] Multi-agent adversarial self-verification (writer → critic → judge)
- [ ] Evaluation harness + ablation on a public task suite
- [ ] Skill / recipe library (promote a repeated success path into a reusable skill)
- [ ] Embedding-backed similarity and an LLM-backed distiller as drop-in adapters

## Design notes

- **Model-agnostic by construction.** The model is a `str -> str` callable; nothing in
  the harness assumes a vendor.
- **Boring storage on purpose.** Append-only JSONL and one-file-per-memory are diffable,
  greppable, and trivial to inspect — the harness should never be a black box.
- **Clean-room.** Patterns are reimplemented from scratch; no code is lifted from the
  production system they were learned in.

## License

MIT © Wenzhen Li (李文振)
