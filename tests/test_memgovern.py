import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import memgovern as mg  # noqa: E402

from gatekeeper.pilot import arm_config, deterministic_outputs, expand_env  # noqa: E402
from gatekeeper.skill import Skill  # noqa: E402

CARDS = {
    "a/x1": {"repo": "a/x", "bug_description": "b1", "fix_experience": "f1"},
    "b/y2": {"repo": "B/Y", "bug_description": "b2", "fix_experience": "f2"},
    "c/z3": {"repo": "c/z", "bug_description": "b3", "fix_experience": "f3"},
    "c/z4": {"repo": "c/z", "bug_description": "b4", "fix_experience": "f4"},
}
ORDER = ["b/y2", "a/x1", "unknown9", "c/z3", "c/z4"]  # ranking returned by the index


class FakeCollection:
    def __init__(self):
        self.asked = []

    def count(self):
        return len(ORDER)

    def query(self, query_texts, n_results):
        self.asked.append(n_results)
        ids = ORDER[:n_results]
        return {"ids": [ids], "distances": [[0.1] * len(ids)], "metadatas": [[{}] * len(ids)]}


def test_repo_of_instance():
    assert mg.repo_of_instance("B__Y-12") == "b/y"
    assert mg.repo_of_instance("owner__name-with-dash-7") == "owner/name-with-dash"
    with pytest.raises(ValueError):
        mg.repo_of_instance("nope")


def test_filter_removes_cell_repos_case_insensitive_and_keeps_count():
    kept = mg.filter_cards(CARDS, mg.excluded_repos(["b__y-1", "a__x-2"]))
    assert set(kept) == {"c/z3", "c/z4"}
    inner = FakeCollection()
    r = mg.FilteredCollection(inner, kept).query(query_texts=["q"], n_results=2)
    assert r["ids"] == [["c/z3", "c/z4"]]  # unknown ids dropped too
    assert len(r["distances"][0]) == 2 and inner.asked == [2, 5]  # widened until enough


def test_filter_returns_fewer_only_when_collection_exhausted():
    kept = mg.filter_cards(CARDS, mg.excluded_repos(["c__z-1"]))
    r = mg.FilteredCollection(FakeCollection(), kept).query(query_texts=["q"], n_results=5)
    assert r["ids"] == [["b/y2", "a/x1"]]


def test_check_static_flags_count_and_cell_repo():
    ids = ["c__z-1"]
    assert mg.check_static({"c__z-1": ["a/x1", "b/y2"]}, CARDS, ids, 2) == []
    bad = mg.check_static({"c__z-1": ["a/x1", "c/z3"]}, CARDS, ids, 2)
    assert any("repository of the cell" in b for b in bad)
    assert mg.check_static({"c__z-1": ["a/x1"]}, CARDS, ids, 2) == ["c__z-1: 1 cards"]


def test_expand_env_strict(monkeypatch):
    monkeypatch.setenv("MG_X", "/opt/t")
    assert expand_env({"a": ["-v", "${MG_X}:/t"]}) == {"a": ["-v", "/opt/t:/t"]}
    monkeypatch.delenv("MG_X")
    with pytest.raises(ValueError):
        expand_env("${MG_X}")


def test_skill_environment_and_dry_run_commands(monkeypatch):
    monkeypatch.setenv("MEMGOVERN_TOOLS", "/opt/mg/tools")
    sk = Skill.load("configs/skills/memgovern-orig.json")
    c = arm_config(
        sk, "deterministic", model_class="deterministic", outputs=deterministic_outputs()
    )
    env = c["environment"]
    assert "--add-host=host.docker.internal:host-gateway" in env["run_args"]
    assert "/opt/mg/tools:/mgtools:ro" in env["run_args"] and env["run_args"][0] == "--rm"
    assert env["env"]["GRAPH_EXP_SEARCH_URL"].startswith("http://host.docker.internal:")
    outs = c["model"]["outputs"]
    assert "exp_search" in outs[0]["extra"]["actions"][0]["command"]
    assert outs[-1] == deterministic_outputs()[-1]  # still submits at the end
    # paid arm: no scripted steps, same container settings
    paid = arm_config(sk, "vertex_ai/x", {"seed": 1})
    assert "outputs" not in paid["model"] and paid["environment"] == env
