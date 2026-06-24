import pytest

from harnesslab.recover import EscalationError, with_recovery


def test_recovers_after_an_informed_retry():
    calls = {"n": 0}

    def action(ok=False):
        calls["n"] += 1
        if not ok:
            raise ValueError("not ready")
        return "done"

    # diagnose flips the flag so attempt 2 is informed, not a blind repeat.
    out = with_recovery(action, diagnose=lambda exc, attempt, kw: {"ok": True}, max_attempts=3)
    assert out == "done"
    assert calls["n"] == 2


def test_escalates_after_max_attempts():
    def boom():
        raise RuntimeError("always broken")

    with pytest.raises(EscalationError) as ei:
        with_recovery(boom, max_attempts=3)
    assert ei.value.attempts == 3
    assert isinstance(ei.value.last_exc, RuntimeError)
