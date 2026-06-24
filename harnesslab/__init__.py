"""harnesslab -- a self-evolving, model-agnostic agent harness.

Model + Harness = Agent. This package is the *harness* half: the scaffolding that lives
outside the model and turns it into an agent that learns from its own runs.
"""
from .bias import diverse_sample, lenses
from .context import Block, assemble, estimate_tokens, reground, window
from .evaluation import Task, make_suite, run_ablation
from .experience import (
    Episode,
    ExperienceStore,
    solve_with_experience,
    token_overlap,
)
from .flows import GateError, Step, run_flow, scored_review
from .gateway import Call, Gateway
from .memory import Memory, MemoryStore, relevance
from .optimize import Result, optimize
from .orchestration import fan_out, judge_panel, pipeline
from .recover import EscalationError, with_recovery
from .review import refute_vote, writer_critic_judge
from .skills import Recipe, RecipeBook, Skill, SkillRegistry

__version__ = "0.3.0"

__all__ = [
    # experience + memory
    "Episode",
    "ExperienceStore",
    "solve_with_experience",
    "token_overlap",
    "Memory",
    "MemoryStore",
    "relevance",
    # long-context management
    "Block",
    "assemble",
    "reground",
    "window",
    "estimate_tokens",
    # multi-agent orchestration + self-verification
    "fan_out",
    "pipeline",
    "judge_panel",
    "refute_vote",
    "writer_critic_judge",
    # divergence / anti-bias
    "diverse_sample",
    "lenses",
    # flows + gates
    "Step",
    "run_flow",
    "scored_review",
    "GateError",
    # self-healing
    "with_recovery",
    "EscalationError",
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
