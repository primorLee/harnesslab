from harnesslab.orchestration import fan_out, judge_panel, pipeline


def test_fan_out_preserves_order():
    assert fan_out([1, 2, 3, 4], lambda x: x * x) == [1, 4, 9, 16]


def test_fan_out_isolates_failures():
    seen = []

    def worker(x):
        if x == 2:
            raise ValueError("boom")
        return x * 10

    out = fan_out([1, 2, 3], worker, on_error=lambda item, exc: seen.append(item))
    assert out == [10, None, 30]
    assert seen == [2]  # the failing item was reported, the batch survived


def test_fan_out_empty():
    assert fan_out([], lambda x: x) == []


def test_pipeline_runs_all_stages():
    out = pipeline([1, 2, 3], lambda x: x + 1, lambda x: x * 2)
    assert out == [4, 6, 8]


def test_pipeline_drops_failing_item():
    def stage2(x):
        if x == 0:
            raise ZeroDivisionError
        return 10 // x

    assert pipeline([1, 0, 2], lambda x: x, stage2) == [10, None, 5]


def test_judge_panel_picks_highest_mean():
    cands = ["a", "b", "c"]
    scorers = [lambda c: len(c), lambda c: 1.0 if c == "b" else 0.0]
    winner, scores = judge_panel(cands, scorers)
    assert winner == "b"
    assert scores[1] > scores[0] and scores[1] > scores[2]
