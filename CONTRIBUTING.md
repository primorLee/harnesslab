# Contributing

Thanks for your interest. harnesslab is a small, dependency-light agent harness, and a few
principles keep it that way:

- **The core stays stdlib-only.** New backends (embedding similarity, a real CMA-ES, an
  LLM-backed distiller, …) go *behind the existing callable interfaces* as optional
  extras — never as a hard dependency of the core.
- **Every module ships with tests.** Run `pytest -q` (stdlib only, no network).
- **Stay model-agnostic.** The LLM is a `str -> str` callable; nothing should assume a
  vendor or a native function-calling API.
- **Keep storage boring.** Append-only JSONL and one-file-per-memory stay diffable and
  greppable.

For anything larger than a bug fix, please open an issue to discuss it first.

## Dev setup

```bash
pip install -e ".[dev]"
pytest -q
python examples/tool_agent.py     # offline end-to-end demo
```
