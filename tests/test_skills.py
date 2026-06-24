from harnesslab.skills import Recipe, RecipeBook, Skill, SkillRegistry


def test_skill_routing_picks_best_match():
    reg = SkillRegistry()
    reg.register(Skill("sim", "run a spectre simulation of a circuit", run=lambda q: "sim"))
    reg.register(Skill("plot", "draw a waveform chart from results", run=lambda q: "plot"))
    assert reg.route("please simulate this circuit") == "sim"
    assert reg.route("chart the waveform") == "plot"


def test_skill_route_passes_kwargs():
    reg = SkillRegistry()
    reg.register(Skill("echo", "echo back the payload value", run=lambda q, value=None: value))
    assert reg.route("echo the payload", value=42) == 42


def test_no_skill_match_raises():
    reg = SkillRegistry()
    reg.register(Skill("sim", "simulate a circuit", run=lambda q: "sim"))
    try:
        reg.route("xyzzy quux")
    except LookupError:
        pass
    else:
        raise AssertionError("expected LookupError")


def test_recipe_book_round_trip_and_find(tmp_path):
    book = RecipeBook(tmp_path / "recipes.jsonl")
    book.add(Recipe(task="size an OTA", steps=["set bias", "sweep W/L", "check gain"],
                    tags=["analog"]))
    book.add(Recipe(task="lay out a pad ring", steps=["place pads", "route"], tags=["layout"]))

    found = book.find("size an OTA for high gain", k=1)
    assert len(found) == 1
    assert found[0].steps[0] == "set bias"
