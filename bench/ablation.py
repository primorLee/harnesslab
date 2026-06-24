#!/usr/bin/env python
"""Run the experience-layer ablation and print a results table.

    python bench/ablation.py                 # default suite, deterministic
    python bench/ablation.py --rounds 4 --families 8 --variants 5

The numbers are reproducible for a fixed seed; that's the point. To drive the same suite
with a real model, wire harnesslab.llm into a solver (see examples/quickstart.py) and
swap it in for the simulated agent.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from harnesslab.evaluation import make_suite, run_ablation


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--families", type=int, default=6)
    ap.add_argument("--variants", type=int, default=4)
    args = ap.parse_args()

    suite = make_suite(args.families, args.variants)
    rep = run_ablation(suite, rounds=args.rounds, seed=args.seed)
    off, on = rep["off"], rep["on"]

    print(
        f"suite: {off['tasks']} tasks "
        f"({args.families} families x {args.variants} variants), "
        f"rounds={args.rounds}, seed={args.seed}\n"
    )
    print(f"{'mode':<6}{'first-try solve':>16}{'final solve':>14}{'evals':>9}")
    print("-" * 45)
    for name, m in (("OFF", off), ("ON", on)):
        print(
            f"{name:<6}{m['first_try_rate'] * 100:>15.0f}%"
            f"{m['solve_rate'] * 100:>13.0f}%{m['evals']:>9}"
        )

    d_first = (on["first_try_rate"] - off["first_try_rate"]) * 100
    d_evals = (off["evals"] - on["evals"]) / off["evals"] * 100 if off["evals"] else 0.0
    print(
        f"\nexperience transfer lifts first-try success by +{d_first:.0f} points "
        f"and cuts total evaluations by {d_evals:.0f}%."
    )


if __name__ == "__main__":
    main()
