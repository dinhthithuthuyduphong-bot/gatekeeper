import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kaggle" / "scripts"))
import a38p_analyse as pa  # noqa: E402
import a38p_build as pb  # noqa: E402


def test_rename_is_exactly_reversible():
    s = 'see "Bug Patch" and the bug patch, bug-patch; Bug_Patch.'
    new, hits = pb.rename(s, "Merge branch 'stable'")
    assert len(hits) == 4 and not pb.RENAME.search(new)
    assert pb.restore(new, hits, "Merge branch 'stable'") == s


def test_signflip_exact_values():
    assert pa.signflip_p([1, 1, 1, 1, 1, 1]) == 1 / 64
    assert pa.signflip_p([1, 1, 1, 1, 1, 0]) == 2 / 64
    assert pa.signflip_p([0, 0, 0, 0, 0, 0]) == 1.0


def test_data_file_pairs_and_hashes():
    rows = [json.loads(x) for x in gzip.open(ROOT / "kaggle/data/a38p_prompts.jsonl.gz", "rt")]
    allp = [json.loads(x) for x in gzip.open(ROOT / "kaggle/data/a38_prompts.jsonl.gz", "rt")]
    orig = {p["sha256"]: p for p in allp if (p["condition"], p["variant"]) == ("leak", "ablated")}
    assert len(rows) == 6
    for r in rows:
        o = orig[r["pair_of"]]
        assert not pb.RENAME.search(r["prompt"])
        assert len(r["prompt"]) - len(o["prompt"]) == sum(
            len("Merge branch 'stable'") - len(t)
            for t in [m.group(0) for m in pb.RENAME.finditer(o["prompt"])]
        )
