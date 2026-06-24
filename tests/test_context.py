from harnesslab.context import Block, assemble, estimate_tokens, reground, window


def test_estimate_tokens_roughly_chars_over_four():
    assert estimate_tokens("a" * 40) == 10
    assert estimate_tokens("") == 1  # never zero


def test_pinned_always_survives_even_over_budget():
    blocks = [Block("KEEP ME", pinned=True), Block("x" * 400, priority=9)]
    out = assemble(blocks, budget=1)  # budget too small for anything but the pin
    assert "KEEP ME" in out
    assert "xxxx" not in out


def test_priority_admission_and_order_preserved():
    blocks = [
        Block("pinned", pinned=True),
        Block("a" * 400, priority=5),  # ~100 tokens
        Block("b" * 400, priority=1),  # ~100 tokens, dropped under budget
    ]
    out = assemble(blocks, budget=110)
    assert "pinned" in out and "aaaa" in out and "bbbb" not in out
    # output keeps original order: pinned block comes before the 'a' block
    assert out.index("pinned") < out.index("aaaa")


def test_compactor_rescues_an_overflowing_block():
    blocks = [Block("pinned", pinned=True), Block("a" * 400, priority=5),
              Block("b" * 400, priority=1)]
    out = assemble(blocks, budget=110, compactor=lambda t: t[:20])
    assert "bbbb" in out  # compacted to fit instead of dropped


def test_reground_is_pinned():
    b = reground("ship the harness", "no secrets leave the repo")
    assert b.pinned and "ship the harness" in b.text and "no secrets" in b.text


def test_window_folds_old_turns():
    turns = [f"turn{i}" for i in range(10)]
    blocks = window(turns, keep_recent=3, compactor=lambda s: "SUMMARY")
    assert len(blocks) == 4  # one summary + 3 recent
    assert blocks[0].text == "SUMMARY"
    assert blocks[-1].text == "turn9"
