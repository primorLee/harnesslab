"""The agent loop must call tools, finish, and feed the experience layer."""
from harnesslab.agent import Agent
from harnesslab.experience import ExperienceStore
from harnesslab.gateway import Gateway


def scripted(replies):
    box = {"i": 0}

    def llm(prompt):
        r = replies[min(box["i"], len(replies) - 1)]
        box["i"] += 1
        return r

    return llm


def test_agent_calls_tool_then_finishes():
    gw = Gateway()
    gw.register("add", lambda a, b: a + b)
    agent = Agent(scripted(['ACTION: add\nARGS: {"a": 2, "b": 3}', "FINAL: the answer is 5"]),
                  gateway=gw, tools_doc={"add": "add two numbers"})
    res = agent.run("add 2 and 3")
    assert res.success is True and "5" in res.answer
    assert res.steps[0].action == "add" and res.steps[0].observation == "5"
    assert gw.stats()["ok"] == 1


def test_immediate_final():
    res = Agent(scripted(["FINAL: done"])).run("trivial")
    assert res.success and res.answer == "done" and len(res.steps) == 1


def test_step_budget_exhausted_records_failure():
    store = ExperienceStore()
    gw = Gateway()
    gw.register("noop", lambda: "ok")
    agent = Agent(scripted(['ACTION: noop\nARGS: {}']), gateway=gw, experience=store, max_steps=3)
    res = agent.run("loops forever")
    assert res.success is False and len(res.steps) == 3
    eps = store.all()
    assert len(eps) == 1 and eps[0].success is False


def test_verify_controls_success_and_distills_lesson():
    store = ExperienceStore()
    res = Agent(scripted(["FINAL: 42"]), experience=store).run(
        "what is the answer", verify=lambda t, a: a == "the truth"
    )
    assert res.success is False
    ep = store.all()[0]
    assert ep.success is False and ep.lesson  # a wrong answer becomes a distilled lesson


def test_tool_error_surfaces_as_observation():
    gw = Gateway()

    @gw.backend("boom")
    def _boom():
        raise ValueError("nope")

    agent = Agent(scripted(['ACTION: boom\nARGS: {}', "FINAL: gave up"]), gateway=gw)
    res = agent.run("trigger an error")
    assert "error" in res.steps[0].observation.lower()
    assert res.answer == "gave up"
