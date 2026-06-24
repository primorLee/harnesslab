from harnesslab.evaluation import make_suite, run_ablation


def test_suite_shape():
    suite = make_suite(families=5, variants=4)
    assert len(suite) == 20
    # variants within a family share one lesson
    fam = [t for t in suite if t.family == suite[0].family]
    assert len({t.lesson for t in fam}) == 1


def test_experience_transfer_beats_cold():
    rep = run_ablation(rounds=3, seed=0)
    assert rep["on"]["first_try_rate"] > rep["off"]["first_try_rate"]
    assert rep["on"]["evals"] <= rep["off"]["evals"]
    assert rep["on"]["solve_rate"] >= rep["off"]["solve_rate"]


def test_deterministic():
    assert run_ablation(seed=1) == run_ablation(seed=1)
