#!/usr/bin/env python
"""Render the experience-layer ablation to assets/ablation.png (+ .zh.png).

Runs the same deterministic ablation as bench/ablation.py across a sweep of retry
budgets and plots two panels: first-try solve rate (the transfer effect) and total
evaluations (the efficiency win). Reproducible -- the figure is generated from the
harness, not drawn by hand. Emits an English and a Chinese figure.

    python bench/plot_ablation.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from harnesslab.evaluation import run_ablation

ON = "#2f5fbf"
OFF = "#9aa0a6"
RETRIES = [1, 2, 3]

LABELS = {
    "en": {
        "font": "DejaVu Sans",
        "suptitle": "harnesslab — experience-layer ablation",
        "subtitle": "controlled benchmark · 24 tasks (6 families × 4 variants) · deterministic, seed=0",
        "t1": "First-try solve rate", "y1": "solved on first try (%)", "x": "retry budget",
        "on": "experience ON", "off": "experience OFF", "pts": "pts",
        "t2": "Total evaluations to clear suite", "y2": "evaluations",
        "out": "ablation.png",
    },
    "zh": {
        "font": "Noto Sans CJK JP",
        "suptitle": "harnesslab —— 经验层消融实验",
        "subtitle": "受控基准 · 24 个任务（6 族 × 4 变体）· 确定性可复现，seed=0",
        "t1": "首次成功率", "y1": "首次即解出（%）", "x": "重试预算",
        "on": "经验层 开", "off": "经验层 关", "pts": "点",
        "t2": "清空任务集所需评测次数", "y2": "评测次数",
        "out": "ablation.zh.png",
    },
}


def render(lang: str) -> None:
    L = LABELS[lang]
    off_first, on_first, off_evals, on_evals = [], [], [], []
    for r in RETRIES:
        rep = run_ablation(rounds=r, seed=0)
        off_first.append(rep["off"]["first_try_rate"] * 100)
        on_first.append(rep["on"]["first_try_rate"] * 100)
        off_evals.append(rep["off"]["evals"])
        on_evals.append(rep["on"]["evals"])

    plt.rcParams.update({
        "font.sans-serif": [L["font"]], "font.family": "sans-serif",
        "axes.unicode_minus": False, "axes.grid": True,
        "grid.color": "#e6e8eb", "axes.edgecolor": "#c9ced3",
    })
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.7), facecolor="white")
    fig.suptitle(L["suptitle"], fontsize=13, fontweight="bold")
    fig.text(0.5, 0.90, L["subtitle"], ha="center", fontsize=8.5, color="#5a5a5a")

    ax1.set_facecolor("white")
    ax1.plot(RETRIES, on_first, "-o", color=ON, lw=2.4, ms=7, label=L["on"])
    ax1.plot(RETRIES, off_first, "--o", color=OFF, lw=2.0, ms=7, label=L["off"])
    ax1.set_title(L["t1"], fontsize=11)
    ax1.set_xlabel(L["x"]); ax1.set_ylabel(L["y1"])
    ax1.set_xticks(RETRIES); ax1.set_ylim(-5, 100)
    ax1.legend(frameon=False, fontsize=9, loc="center right")
    ax1.annotate(f"+{on_first[0]-off_first[0]:.0f} {L['pts']}",
                 xy=(1, on_first[0]), xytext=(1.25, 45), fontsize=9, color=ON, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=ON))

    x = range(len(RETRIES)); w = 0.36
    ax2.set_facecolor("white")
    ax2.bar([i - w / 2 for i in x], off_evals, w, color=OFF, label=L["off"])
    ax2.bar([i + w / 2 for i in x], on_evals, w, color=ON, label=L["on"])
    ax2.set_title(L["t2"], fontsize=11)
    ax2.set_xlabel(L["x"]); ax2.set_ylabel(L["y2"])
    ax2.set_xticks(list(x)); ax2.set_xticklabels(RETRIES)
    ax2.legend(frameon=False, fontsize=9, loc="upper left")
    drop = (off_evals[-1] - on_evals[-1]) / off_evals[-1] * 100
    ax2.annotate(f"-{drop:.0f}%", xy=(2 + w / 2, on_evals[-1]), xytext=(2 - 0.1, on_evals[-1] + 9),
                 fontsize=10, color=ON, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=ON))

    fig.tight_layout(rect=[0, 0, 1, 0.88])
    out = pathlib.Path(__file__).resolve().parent.parent / "assets" / L["out"]
    out.parent.mkdir(exist_ok=True)
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    for lang in ("en", "zh"):
        render(lang)


if __name__ == "__main__":
    main()
