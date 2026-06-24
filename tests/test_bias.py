from harnesslab.bias import diverse_sample, lenses


def _cycler(items):
    box = {"i": 0}

    def gen():
        v = items[box["i"] % len(items)]
        box["i"] += 1
        return v

    return gen


def test_diverse_sample_rejects_near_duplicates():
    # the 2nd item is too similar to the 1st and must be skipped.
    items = ["alpha one", "alpha one two", "beta gamma", "delta epsilon"]
    got = diverse_sample(_cycler(items), n=3, threshold=0.6)
    assert len(got) == 3
    assert "alpha one two" not in got  # rejected as a near-duplicate of "alpha one"
    assert set(got) == {"alpha one", "beta gamma", "delta epsilon"}


def test_diverse_sample_stops_at_max_tries():
    got = diverse_sample(lambda: "identical", n=5, threshold=0.6, max_tries=10)
    assert got == ["identical"]  # everything collides; only one distinct kept


def test_lenses_one_candidate_per_framing():
    out = lenses(lambda lens: f"idea via {lens}", ["safety", "cost", "biology"])
    assert out == [
        ("safety", "idea via safety"),
        ("cost", "idea via cost"),
        ("biology", "idea via biology"),
    ]
