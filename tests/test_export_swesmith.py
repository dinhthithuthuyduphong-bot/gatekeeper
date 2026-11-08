import importlib.util
import random
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "export_swesmith", Path(__file__).resolve().parents[1] / "scripts" / "export_swesmith.py"
)
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)


def _gskill_reference(all_data, train_size, val_size, test_size, seed):
    # verbatim arithmetic of gepa@8c7b697 load_and_split_data after the load loop
    random.seed(seed)
    random.shuffle(all_data)
    total_needed = train_size + val_size + test_size
    if len(all_data) < total_needed:
        ratio = len(all_data) / total_needed
        train_size = int(train_size * ratio)
        val_size = int(val_size * ratio)
        test_size = len(all_data) - train_size - val_size
    tr = all_data[:train_size]
    va = all_data[train_size : train_size + val_size]
    te = all_data[train_size + val_size : train_size + val_size + test_size]
    return tr, va, te


def test_split_matches_gskill_full_and_scaled():
    for n in (350, 120):
        rows = [{"instance_id": f"i{k}"} for k in range(n)]
        ref = _gskill_reference([dict(r) for r in rows], 200, 50, 100, 42)
        got = ex.gskill_split(rows, 200, 50, 100, 42)
        for name, part in zip(("train", "val", "test"), ref, strict=True):
            assert [r["instance_id"] for r in got if r["_gskill_split"] == name] == [
                r["instance_id"] for r in part
            ]
