"""harnesslab -- a self-evolving, model-agnostic agent harness.

Model + Harness = Agent. This package is the *harness* half: the scaffolding that lives
outside the model and turns it into an agent that learns from its own runs.
"""
from .experience import (
    Episode,
    ExperienceStore,
    solve_with_experience,
    token_overlap,
)
from .memory import Memory, MemoryStore, relevance

__version__ = "0.1.0"

__all__ = [
    "Episode",
    "ExperienceStore",
    "solve_with_experience",
    "token_overlap",
    "Memory",
    "MemoryStore",
    "relevance",
    "__version__",
]
