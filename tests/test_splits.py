import csv

from gatekeeper.splits import load_tasks, make_split


def write(path, rows):
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["instance_id", "repo", "version"])
        w.writeheader()
        w.writerows(rows)


def test_split_is_disjoint_by_repo(tmp_path):
    write(
        tmp_path / "swe-gym.csv",
        [{"instance_id": f"g{i}", "repo": "org/gymrepo", "version": "1"} for i in range(5)]
        + [{"instance_id": "g9", "repo": "org/shared", "version": "1"}],
    )
    write(
        tmp_path / "swe-bench.csv",
        [
            {"instance_id": f"d{i}", "repo": "django/django", "version": v}
            for i, v in enumerate(["4.0"] * 60 + ["4.1"] * 40)
        ]
        + [{"instance_id": "s1", "repo": "org/shared", "version": "1"}],
    )
    write(  # Verified is a subset of SWE-bench: duplicates must be counted once
        tmp_path / "swe-bench-verified.csv",
        [{"instance_id": "d0", "repo": "django/django", "version": "4.0"}],
    )
    sp = make_split(load_tasks(tmp_path), thresholds=(50, 100))
    assert sp["train_repos"] == ["org/gymrepo", "org/shared"]
    assert sp["repos_removed_from_test_for_overlap"] == ["org/shared"]
    assert sp["test_repos"] == ["django/django"]
    assert sp["n_test_tasks"] == 100
    assert sp["tasks_per_scope"] == {"django/django@4.0": 60, "django/django@4.1": 40}
    assert sp["scopes_with_at_least"] == {50: 1, 100: 0}
    assert sp["repos_with_at_least"] == {50: 1, 100: 1}
    assert sp["regime_A_candidates"] == ["django/django"]
    assert not set(sp["test_instance_ids"]) & {"s1", "g9"}
