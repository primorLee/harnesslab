"""Recall must rank by relevance and refuse to surface stale memories."""
from harnesslab.memory import Memory, MemoryStore


def test_write_read_round_trip(tmp_path):
    store = MemoryStore(tmp_path)
    store.write(Memory(name="ldo-trim", description="how the LDO trim works",
                       body="Set the 6-bit trim before measuring. See [[bandgap-startup]].",
                       refs=[]))
    (mem,) = store.read_all()
    assert mem.name == "ldo-trim"
    assert mem.description == "how the LDO trim works"
    assert mem.links == ["bandgap-startup"]


def test_anti_staleness(tmp_path):
    existing = tmp_path / "real_artifact.txt"
    existing.write_text("here", encoding="utf-8")

    store = MemoryStore(tmp_path)
    store.write(Memory(name="fresh", description="points at a live file",
                       body="valid", refs=[str(existing)]))
    store.write(Memory(name="stale", description="points at a deleted file",
                       body="valid", refs=[str(tmp_path / "gone.txt")]))

    names = {m.name for m in store.stale()}
    assert names == {"stale"}

    # drop_stale (default) hides the stale memory from recall
    recalled = {m.name for m in store.recall("valid", drop_stale=True)}
    assert recalled == {"fresh"}
    # opting out surfaces both
    assert {m.name for m in store.recall("valid", drop_stale=False)} == {"fresh", "stale"}


def test_custom_validator(tmp_path):
    # refs need not be files; a validator can resolve symbols, endpoints, anything.
    live = {"api.v2"}
    store = MemoryStore(tmp_path, validator=lambda ref: ref in live)
    store.write(Memory(name="ok", description="d", body="b", refs=["api.v2"]))
    store.write(Memory(name="dead", description="d", body="b", refs=["api.v1"]))
    assert {m.name for m in store.stale()} == {"dead"}
