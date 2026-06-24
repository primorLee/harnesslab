"""The self-evolving loop must actually improve a solver across rounds."""
from harnesslab.experience import Episode, ExperienceStore, solve_with_experience


def test_failure_is_distilled_and_retrieved(tmp_path):
    store = ExperienceStore(tmp_path / "exp.jsonl")
    store.record(Episode(task="size a bandgap reference", success=False,
                         summary="forgot the startup circuit"))

    seeds = store.retrieve("size a bandgap reference for 1.2V")
    assert len(seeds) == 1
    # a failure with no explicit lesson gets one distilled on record()
    assert seeds[0].lesson
    assert "startup" in store.seed_prompt("bandgap reference").lower()


def test_prefer_failures_ranking(tmp_path):
    store = ExperienceStore(tmp_path / "exp.jsonl")
    store.record(Episode(task="tune the LDO loop", success=True, summary="worked"))
    store.record(Episode(task="tune the LDO loop", success=False, summary="unstable"))
    top = store.retrieve("tune the LDO loop", k=1)[0]
    assert top.success is False  # the lesson-bearing failure wins the tie


def test_solve_with_experience_warm_starts(tmp_path):
    store = ExperienceStore(tmp_path / "exp.jsonl")

    # A solver that only succeeds once a prior lesson has been reinjected.
    def solver(task, seed):
        if "warm-start" in seed.lower():
            return True, "succeeded using the prior lesson", "remember the startup circuit"
        return False, "missing the startup circuit", "needs a startup circuit"

    ok, last = solve_with_experience(task="size a bandgap", solver=solver, store=store,
                                     tags=["analog"], max_rounds=3)
    assert ok is True
    # round 1 failed (no seed yet), round 2 succeeded (seeded) -> two episodes recorded
    episodes = store.all()
    assert len(episodes) == 2
    assert episodes[0].success is False and episodes[1].success is True


def test_round_trip_serialization(tmp_path):
    store = ExperienceStore(tmp_path / "exp.jsonl")
    store.record(Episode(task="t", success=True, summary="s", tags=["a", "b"], steps=4))
    (reloaded,) = ExperienceStore(store.path).all()
    assert reloaded.tags == ["a", "b"] and reloaded.steps == 4
