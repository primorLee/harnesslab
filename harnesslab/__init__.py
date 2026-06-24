"""harnesslab -- a self-evolving, model-agnostic agent harness.

Model + Harness = Agent. This package is the *harness* half: the scaffolding that lives
outside the model and turns it into an agent that learns from its own runs.
"""
from .evaluation import Task, make_suite, run_ablation
from .experience import (
    Episode,
    ExperienceStore,
    solve_with_experience,
    token_overlap,
)
from .gateway import Call, Gateway
from .memory import Memory, MemoryStore, relevance
from .optimize import Result, optimize
from .orchestration import fan_out, judge_panel, pipeline
from .review import refute_vote, writer_critic_judge
from .skills import Recipe, RecipeBook, Skill, SkillRegistry

__version__ = "0.2.0"

__all__ = [
    # experience + memory
    "Episode",
    "ExperienceStore",
    "solve_with_experience",
    "token_overlap",
    "Memory",
    "MemoryStore",
    "relevance",
    # multi-agent orchestration + self-verification
    "fan_out",
    "pipeline",
    "judge_panel",
    "refute_vote",
    "writer_critic_judge",
    # skills + recipes
    "Skill",
    "SkillRegistry",
    "Recipe",
    "RecipeBook",
    # unified tool/sim gateway
    "Gateway",
    "Call",
    # closed-loop optimizer
    "optimize",
    "Result",
    # evaluation harness
    "Task",
    "make_suite",
    "run_ablation",
    "__version__",
]
