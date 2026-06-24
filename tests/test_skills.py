from harnesslab.skills import Recipe, RecipeBook, Skill, SkillRegistry


def test_skill_routing_picks_best_match():
    reg = SkillRegistry()
    reg.register(Skill("sim", "run a numerical simulation of a model", run=lambda q: "sim"))
    reg.register(Skill("plot", "draw a chart from results data", run=lambda q: "plot"))
    assert reg.route("run a simulation of this model") == "sim"
    assert reg.route("draw a chart of the data") == "plot"


def test_skill_route_passes_kwargs():
    reg = SkillRegistry()
    reg.register(Skill("echo", "echo back the payload value", run=lambda q, value=None: value))
    assert reg.route("echo the payload", value=42) == 42


def test_no_skill_match_raises():
    reg = SkillRegistry()
    reg.register(Skill("sim", "run a simulation", run=lambda q: "sim"))
    try:
        reg.route("xyzzy quux")
    except LookupError:
        pass
    else:
        raise AssertionError("expected LookupError")


def test_recipe_book_round_trip_and_find(tmp_path):
    book = RecipeBook(tmp_path / "recipes.jsonl")
    book.add(Recipe(task="tune a feedback loop", steps=["set the gain", "sweep the pole",
                                                        "check stability"], tags=["control"]))
    book.add(Recipe(task="render a report", steps=["collect data", "draw charts"], tags=["report"]))

    found = book.find("tune a feedback loop for stability", k=1)
    assert len(found) == 1
    assert found[0].steps[0] == "set the gain"
