import pytest

from harnesslab.experience import ExperienceStore
from harnesslab.gateway import Gateway


def test_routes_and_records_success():
    gw = Gateway()
    gw.register("add", lambda a, b: a + b)
    assert gw.call("add", a=2, b=3) == 5
    assert gw.stats() == {"total": 1, "ok": 1, "failed": 0}
    assert gw.calls[0].name == "add" and gw.calls[0].ok


def test_decorator_registration():
    gw = Gateway()

    @gw.backend("double")
    def _double(x):
        return x * 2

    assert gw.call("double", x=21) == 42


def test_unknown_backend_raises():
    gw = Gateway()
    with pytest.raises(KeyError):
        gw.call("nope")


def test_failure_is_recorded_and_distilled(tmp_path):
    store = ExperienceStore(tmp_path / "exp.jsonl")
    gw = Gateway(experience=store)

    @gw.backend("flaky")
    def _flaky():
        raise ValueError("backend exploded")

    with pytest.raises(ValueError):
        gw.call("flaky")

    assert gw.stats() == {"total": 1, "ok": 0, "failed": 1}
    # the failed call became a lesson in the experience store
    episodes = store.all()
    assert len(episodes) == 1 and episodes[0].success is False
    assert "exploded" in episodes[0].summary
