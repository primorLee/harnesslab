from harnesslab.review import refute_vote, writer_critic_judge


def test_claim_survives_when_skeptics_cannot_refute():
    result = refute_vote("2 + 2 = 4", skeptic=lambda claim: False, n=5)
    assert result["survives"] is True
    assert result["refutations"] == 0


def test_claim_dies_under_majority_refutation():
    result = refute_vote("the moon is cheese", skeptic=lambda claim: True, n=5)
    assert result["survives"] is False
    assert result["refutations"] == 5


def test_skeptic_errors_count_as_not_refuting():
    def flaky(claim):
        raise RuntimeError("skeptic crashed")

    result = refute_vote("uncertain claim", skeptic=flaky, n=3)
    assert result["refutations"] == 0 and result["survives"] is True


def test_writer_critic_judge_revises_until_pass():
    # critic complains until the draft contains "v2", then passes.
    def writer(task, feedback):
        return "draft v2" if feedback else "draft v1"

    def critic(task, draft):
        return "" if "v2" in draft else "needs work"

    result = writer_critic_judge(
        "task", writer, critic, judge=lambda t, d: float(len(d)), max_rounds=3
    )
    assert result["output"] == "draft v2"
    assert result["revisions"] == 1
