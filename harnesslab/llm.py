"""Thin, model-agnostic LLM adapter.

The harness never hard-codes a vendor. Anything that maps ``(messages) -> text`` works;
:func:`chat` ships a stdlib-only client for any OpenAI-compatible endpoint, which
includes DeepSeek out of the box::

    export HARNESSLAB_LLM_BASE_URL=https://api.deepseek.com/v1
    export HARNESSLAB_LLM_API_KEY=sk-...
    export HARNESSLAB_LLM_MODEL=deepseek-chat

No keys are read at import time and none are stored; they come from the environment at
call time.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Callable, Optional

# An LLM is just this: turn a prompt into text.
LLM = Callable[[str], str]


def chat(
    prompt: str,
    *,
    system: str = "",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
    timeout: float = 60.0,
) -> str:
    """Single-turn completion against an OpenAI-compatible chat endpoint.

    Falls back to environment variables ``HARNESSLAB_LLM_{BASE_URL,API_KEY,MODEL}``.
    """
    base_url = (base_url or os.environ.get("HARNESSLAB_LLM_BASE_URL", "")).rstrip("/")
    api_key = api_key or os.environ.get("HARNESSLAB_LLM_API_KEY", "")
    model = model or os.environ.get("HARNESSLAB_LLM_MODEL", "deepseek-chat")
    if not base_url or not api_key:
        raise RuntimeError(
            "Set base_url/api_key (or HARNESSLAB_LLM_BASE_URL / HARNESSLAB_LLM_API_KEY)."
        )

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature}
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


def make_llm(**defaults) -> LLM:
    """Bind endpoint defaults into a plain ``str -> str`` callable for the harness."""

    def _llm(prompt: str) -> str:
        return chat(prompt, **defaults)

    return _llm
