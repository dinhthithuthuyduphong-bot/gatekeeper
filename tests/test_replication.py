import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "analyze_replication", Path(__file__).parents[1] / "scripts" / "analyze_replication.py"
)
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)


def _run(zs):
    return {
        "skills": {
            "s": {
                "pairs": [
                    {
                        "instance_id": f"t{i}",
                        "loss_with": max(0.0, 0.667 + z),
                        "loss_without": 0.667,
                    }
                    for i, z in enumerate(zs)
                ]
            }
        }
    }


def test_replicated_effect_passes_and_unreplicated_does_not():
    strong = [-0.667] * 12 + [0.0] * 18
    runs = [_run(strong)] * 3
    assert ar.verdict(ar.pooled_z(runs, "s"))["pass"]
    lucky = [_run(strong), _run([0.0] * 30), _run([0.0] * 30)]  # one lucky seed only
    v = ar.verdict(ar.pooled_z(lucky, "s"))
    assert not v["pass"] and abs(v["mean_z"] + 0.0889) < 1e-3


def test_incomplete_tasks_are_excluded():
    runs = [_run([-0.667] * 10), _run([-0.667] * 10), _run([-0.667] * 8)]
    v = ar.verdict(ar.pooled_z(runs, "s"))
    assert v["n_tasks"] == 8 and v["n_incomplete"] == 2
