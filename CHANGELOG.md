# Changelog

## 0.4.0
- **`Agent`** — a model-agnostic tool-using agent loop that composes the harness:
  experience warm-start, memory recall, recorded gateway tool calls, optional answer
  verification, and episode recording so the next run is smarter.
- `examples/tool_agent.py`: a complete agent running end-to-end, offline.
- CI (GitHub Actions) across Python 3.10–3.12.

## 0.3.0
- Long-context management (`context`), divergence / anti-bias (`bias`), flow gates
  (`flows`), self-healing recovery (`recover`).
- Reproducible ablation figure (`bench/plot_ablation.py`); bilingual README.

## 0.2.0
- Multi-agent orchestration, adversarial self-verification, skills + recipe library,
  recorded tool / sim gateway, self-adapting (1+λ) optimizer, evaluation harness.

## 0.1.0
- Self-evolving experience layer + anti-staleness long-term memory; model-agnostic LLM
  adapter.
