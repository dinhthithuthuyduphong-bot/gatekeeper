"""kaggle/scripts/c4p_analyse.py on a hand-made C4' output (note 40-5)."""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import c4p_analyse  # noqa: E402


def write(d: Path, arm: str, k: int, solved: dict):
    runs = [{"instance_id": i, "S": {"resolved": s}} for i, s in solved.items()]
    (d / f"t_{arm}_c{k:02d}.json").write_text(json.dumps({"runs": runs}))


def test_contrast_signs_and_pool(tmp_path):
    # test chunk 0: a (no description), b (has one); extra chunk 1: c
    write(tmp_path, "none", 0, {"a": False, "b": False})
    write(tmp_path, "skill", 0, {"a": True, "b": True})
    write(tmp_path, "lf_none", 0, {"a": False, "b": False})
    write(tmp_path, "lf_skill", 0, {"a": False, "b": True})
    for arm, s in (("none", False), ("skill", True), ("lf_none", False), ("lf_skill", False)):
        write(tmp_path, arm, 1, {"c": s})
    runs, chunk = c4p_analyse.load(tmp_path, "t")
    ids = sorted({"a"} | {i for i, k in chunk.items() if k >= 1})
    r = c4p_analyse.contrast(runs, ids, 0.5, 0.0, 120)
    # a and c: skill gain 1 shipped, 0 single commit -> D = (-1 - 0)/2 = -0.5
    assert r["n"] == 2 and r["mean_D"] == -0.5 and r["neg_pos"] == [2, 0]
    assert abs(r["E"] - 1.25**2) < 1e-12 and not r["reject"]
    assert math.isclose(r["solved"]["skill"], 2)


def test_download_pattern_is_the_registered_one():
    assert c4p_analyse.DOWNLOAD.search("pip download jinja2==3.1.6")
    assert not c4p_analyse.DOWNLOAD.search("env = Environment()")


def test_traces_take_the_longest_copy(tmp_path):
    import gzip

    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    rows = [{"instance_id": f"t{k}", "messages": []} for k in range(3)]
    with gzip.open(a / "m_none_c00.traces.jsonl.gz", "wt") as f:
        f.write("".join(json.dumps(r) + "\n" for r in rows))
    (b / "m_none_c00.traces.jsonl").write_text(json.dumps(rows[0]) + "\n")  # truncated copy
    got = c4p_analyse.traces([b, a], "m")
    assert len(got) == 1 and len(got[0]) == 3
