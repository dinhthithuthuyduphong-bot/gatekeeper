import io
import json
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import split_identity as si  # noqa: E402

A = "pallets__jinja.ada0a9a6.func_basic__aaaaaaaa"
B = "pallets__jinja.ada0a9a6.func_basic__bbbbbbbb"
C = "pallets__jinja.ada0a9a6.combine_file__cccccccc"


def _archive(tmp_path, text: str) -> Path:
    p = tmp_path / "run.tar.gz"
    data = text.encode()
    with tarfile.open(p, "w:gz") as t:
        info = tarfile.TarInfo("logs/run_x/training.log")
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))
    return p


def test_same_split_only_when_every_logged_id_is_train_or_val(tmp_path):
    split = {A: "train", B: "val", C: "test"}
    ok = si.check(split, si.ids_in_logs(_archive(tmp_path, f"task {A} then {B}")))
    assert ok["same_split"] and ok["by_split"] == {"train": 1, "val": 1}
    bad = si.check(split, {A, C})
    assert not bad["same_split"]
    missing = si.check(split, {A, "pallets__jinja.ada0a9a6.func_basic__zzzzzzzz"})
    assert not missing["same_split"]
    assert not si.check(split, set())["same_split"]


def test_split_of_reads_plain_and_gz(tmp_path):
    import gzip

    rows = "\n".join(json.dumps({"instance_id": i, "_gskill_split": s}) for i, s in [(A, "train")])
    (tmp_path / "r.jsonl").write_text(rows)
    (tmp_path / "r.jsonl.gz").write_bytes(gzip.compress(rows.encode()))
    assert si.split_of(tmp_path / "r.jsonl") == si.split_of(tmp_path / "r.jsonl.gz") == {A: "train"}
