import pytest

from harnesslab.flows import GateError, Step, run_flow, scored_review


def test_flow_runs_and_threads_context():
    steps = [
        Step("s1", lambda ctx: 5),
        Step("s2", lambda ctx: ctx["s1"] + 1, gate=lambda r, ctx: r > 0),
    ]
    ctx = run_flow(steps)
    assert ctx["s1"] == 5 and ctx["s2"] == 6


def test_unmet_gate_stops_the_flow():
    steps = [Step("s1", lambda ctx: 0, gate=lambda r, ctx: r > 0)]
    with pytest.raises(GateError):
        run_flow(steps)


def test_scored_review_fails_on_weakest_dimension():
    scorer = lambda out, dim: 5.0 if dim == "safety" else 9.0
    result = scored_review("design", scorer, threshold=7.0)
    assert result["passed"] is False
    assert result["min"] == 5.0


def test_scored_review_passes_when_all_clear():
    result = scored_review("design", lambda out, dim: 8.0, threshold=7.0)
    assert result["passed"] is True and result["min"] == 8.0
