import importlib.util
import math
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "c10_analysis", Path(__file__).parents[1] / "scripts" / "c10_analysis.py"
)
c10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c10)


def runs_with(solve):  # solve[(variant, arm)] = set of solved task indices
    ids = [f"t{k}" for k in range(20)]
    runs = {
        (v, s): {i: {"S": {"resolved": k in solve.get((v, s), set())}} for k, i in enumerate(ids)}
        for v in c10.VARIANTS
        for s in ("none", "skill")
    }
    return runs, ids


def test_main_contrast_rejects_when_gain_needs_the_leaked_code():
    runs, ids = runs_with({("A", "skill"): set(range(20)), ("B", "skill"): set(range(20))})
    out = c10.analyse(runs, ids, lam=0.5, theta=0.0, threshold=40.0, reps=200, seed=1)
    m = out["contrasts"]["main A-C"]
    assert m["n"] == 20 and m["n_negative"] == 20 and m["mean_D"] == -0.5
    assert math.isclose(m["E"], 1.25**20) and m["reject_at_threshold"]
    assert out["contrasts"]["A-B"]["E"] == 1.0  # no message effect
    assert out["solved"]["A_skill"] == [20, 20]


def test_no_rejection_when_c_gains_as_much_as_a_and_missing_tasks_dropped():
    runs, ids = runs_with({("A", "skill"): set(range(20)), ("C", "skill"): set(range(20))})
    del runs[("C", "none")]["t3"]
    runs[("A", "none")]["t4"]["infra_error"] = "x"
    m = c10.analyse(runs, ids, lam=0.5, theta=0.0, threshold=40.0, reps=200, seed=1)["contrasts"][
        "main A-C"
    ]
    assert m["n"] == 18 and m["E"] == 1.0 and not m["reject_at_threshold"]
