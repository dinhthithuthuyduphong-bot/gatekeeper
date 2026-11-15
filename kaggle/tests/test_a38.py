import gzip
import hashlib
import json
import sys
import types
from itertools import combinations
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "kaggle" / "scripts"))
import a38_analyse as an  # noqa: E402
import a38_build as bd  # noqa: E402

DATA = ROOT / "kaggle" / "data" / "a38_prompts.jsonl.gz"
CELL = ROOT / "kaggle" / "notebooks" / "a38_run_cell.py"


def _cell_ns():
    ns = {"__name__": "cell_test"}
    exec(compile(CELL.read_text(), str(CELL), "exec"), ns)
    return ns


def _call(skills: str) -> dict:
    fp = (
        "intro\n" + bd.SKILL_BLOCK.format(skills) + "\n\n## Evaluation Results\n```\n"
        "a git log line in the data stays\n```\n"
    )
    return {"call_num": 1, "current_skills": skills, "full_prompt": fp}


def test_ablation_only_touches_the_parent_skill_block():
    c = _call("- keep me\n- Check Git History: run `git log`\n- keep too")
    new, drop = bd.ablated_prompt(c)
    assert drop == [2]
    assert "Check Git History" not in new
    assert "a git log line in the data stays" in new
    assert new == c["full_prompt"].replace("- Check Git History: run `git log`\n", "")


def test_empty_parent_keeps_gskill_placeholder():
    c = {"call_num": 1, "current_skills": "", "full_prompt": "x\n```\n(No skills learned yet)\n```"}
    assert bd.ablated_prompt(c) == (c["full_prompt"], [])


def test_cell_extract_skills_reproduces_gskill_on_saved_calls():
    ex = _cell_ns()["extract_skills"]
    calls = bd.calls_of(ROOT / "results" / "s30_learn_run.tar.gz")
    assert len(calls) == 14
    for c in calls:
        assert ex(c["llm_response"]) == c["new_skills"]


def test_data_file_cells_and_hashes():
    rows = [json.loads(x) for x in gzip.open(DATA, "rt")]
    cells = {}
    for r in rows:
        assert hashlib.sha256(r["prompt"].encode()).hexdigest() == r["sha256"]
        cells[f"{r['condition']}/{r['variant']}"] = (
            cells.get(f"{r['condition']}/{r['variant']}", 0) + 1
        )
    assert cells == {
        "leak/ablated": 6,
        "leak/original": 6,
        "noleak_leaky_env/ablated": 7,
        "clean/ablated": 14,
    }
    for r in rows:
        if r["variant"] == "ablated":
            block = r["prompt"].split("## Evaluation Results")[0]
            assert not bd.RULE.search(block.split("learned skills:")[-1]), r["pid"]
    # clean-run parents have no history line, so their prompts are the saved prompts verbatim
    clean = {r["call"]: r for r in rows if r["run"] == "clean"}
    for c in bd.calls_of(ROOT / "results" / "s30_learn_run.tar.gz"):
        assert clean[c["call_num"]]["prompt"] == c["full_prompt"]


def test_perm_p_matches_brute_force_and_holm():
    a, b = [1.0, 1.0, 2 / 3], [0.0, 1 / 3, 0.0, 0.0]
    pool = a + b
    obs = sum(a) / 3 - sum(b) / 4
    ds = [
        sum(pool[i] for i in s) / 3 - (sum(pool) - sum(pool[i] for i in s)) / 4
        for s in combinations(range(7), 3)
    ]
    assert an.perm_p(a, b) == pytest.approx(sum(d >= obs - 1e-12 for d in ds) / len(ds))
    assert an.perm_p(a, b) == pytest.approx(1 / 35)
    assert an.holm({"x": 0.001, "y": 0.02, "z": 0.3}, 0.025) == {"x": True, "y": False, "z": False}


def _mock_kbench(reply):
    calls = []

    class LLM:
        def __init__(self, name):
            self.name = name

        def prompt(self, text, temperature, seed):
            calls.append((self.name, seed, temperature))
            return reply(self.name, text, seed)

    mod = types.ModuleType("kaggle_benchmarks")
    mod.llms = {m: LLM(m) for m in ("m-a", "m-b")}
    return mod, calls


def test_run_cell_resumes_caps_and_never_resends(tmp_path, monkeypatch):
    ns = _cell_ns()
    work, inp = tmp_path / "w", tmp_path / "i"
    work.mkdir()
    (inp / "d").mkdir(parents=True)
    (inp / "d" / "a38_prompts.jsonl.gz").write_bytes(DATA.read_bytes())
    sha = hashlib.sha256(DATA.read_bytes()).hexdigest()
    mod, calls = _mock_kbench(lambda m, t, s: "text\n```\n- run `git log -n 5`\n```")
    monkeypatch.setitem(sys.modules, "kaggle_benchmarks", mod)
    ns.update(
        WORK=str(work),
        INPUT=str(inp),
        COMMIT="c0ffee",
        SHA256=sha,
        MODELS={"m-a": 0.01, "m-b": 0.01},
        OUT=str(work / "a38_results_1.jsonl"),
        DAY_CAP_USD=1.0,
        ITEM_CAP_USD=5.0,
    )
    ns["main"]()
    n1 = len(calls)
    assert 0 < n1 < 2 * 32 * 3  # the day cap stopped it
    rows = [json.loads(x) for x in (work / "a38_results_1.jsonl").read_text().splitlines()]
    assert sum(r["est_usd"] for r in rows) <= 1.0
    assert all(r["temperature"] is None for r in rows)
    ns["OUT"] = str(work / "a38_results_2.jsonl")
    ns["main"]()
    sent = [(c[0], c[1]) for c in calls]
    keys = [(r["sha256"], r["model"], r["seed"]) for r in rows]
    rows2 = [json.loads(x) for x in (work / "a38_results_2.jsonl").read_text().splitlines()]
    keys2 = [(r["sha256"], r["model"], r["seed"]) for r in rows2]
    assert not set(keys) & set(keys2)  # nothing sent twice
    assert len(sent) == len(keys) + len(keys2)


def test_run_cell_refuses_unfilled_config(monkeypatch, capsys):
    ns = _cell_ns()
    ns["MODELS"] = {}
    mod, calls = _mock_kbench(lambda m, t, s: "")
    monkeypatch.setitem(sys.modules, "kaggle_benchmarks", mod)
    ns["main"]()  # prints and returns, so a later cell of a batch run still runs
    assert not calls and "nothing sent" in capsys.readouterr().out


def test_run_cell_reads_an_unpacked_upload_and_never_raises_on_missing_data(
    tmp_path, monkeypatch, capsys
):
    ns = _cell_ns()
    work, inp = tmp_path / "w", tmp_path / "i"
    work.mkdir()
    (inp / "d").mkdir(parents=True)
    mod, calls = _mock_kbench(lambda m, t, s: "x")
    monkeypatch.setitem(sys.modules, "kaggle_benchmarks", mod)
    ns.update(WORK=str(work), INPUT=str(inp), COMMIT="not-in-repo")
    assert ns["load_prompts"]() is None  # nothing attached: printed, not raised
    assert "not attached" in capsys.readouterr().out
    (inp / "d" / "a38_prompts.jsonl").write_bytes(gzip.decompress(DATA.read_bytes()))
    rows = ns["load_prompts"]()
    assert len(rows) == 33
    (inp / "d" / "a38_prompts.jsonl").write_bytes(b"{}\n")
    assert ns["load_prompts"]() is None and "does not match" in capsys.readouterr().out


def test_analysis_on_mock_results():
    rows = [json.loads(x) for x in gzip.open(DATA, "rt")]
    res = []
    for r in rows:
        for s in (1, 2, 3):
            hist = r["condition"] == "leak"
            skill = "- run `git log`" if hist else "- run tests"
            res.append(
                {"sha256": r["sha256"], "model": "x", "seed": s, "ok": True, "new_skills": skill}
            )
            res.append(
                {"sha256": r["sha256"], "model": "ref", "seed": s, "ok": True, "new_skills": skill}
            )
    out = an.analyse(rows, res, "ref", 0.025)
    h = out["models"]["x"]["H"]
    key = "leak/ablated - noleak_leaky_env/ablated"
    assert h[key]["diff"] == 1.0
    assert h[key]["p_one_sided"] == pytest.approx(1 / 1716)  # C(13, 6)
    assert out["holm_primary_H"] == {"x": True}


def test_run_cell_charges_the_cost_kaggle_reports(tmp_path, monkeypatch):
    ns = _cell_ns()
    work, inp = tmp_path / "w", tmp_path / "i"
    work.mkdir()
    (inp / "d").mkdir(parents=True)
    (inp / "d" / "a38_prompts.jsonl.gz").write_bytes(DATA.read_bytes())
    reply = "x\n```\n- run tests\n```"
    mod, calls = _mock_kbench(lambda m, t, s: reply)
    last = types.SimpleNamespace(
        content=reply,
        usage=types.SimpleNamespace(
            input_tokens=20000, output_tokens=900, total_cost_nanodollars=50_000_000
        ),
    )
    mod.chats = types.SimpleNamespace(
        get_current_chat=lambda: types.SimpleNamespace(messages=[last])
    )
    monkeypatch.setitem(sys.modules, "kaggle_benchmarks", mod)
    ns.update(
        WORK=str(work),
        INPUT=str(inp),
        COMMIT="c0ffee",
        SHA256=hashlib.sha256(DATA.read_bytes()).hexdigest(),
        MODELS={"m-a": 0.001},  # estimate far below the reported 0.05 USD per call
        OUT=str(work / "a38_results_1.jsonl"),
        DAY_CAP_USD=0.5,
        ITEM_CAP_USD=5.0,
    )
    ns["main"]()
    rows = [json.loads(x) for x in (work / "a38_results_1.jsonl").read_text().splitlines()]
    assert all(r["charged_usd"] == 0.05 and r["tokens_in"] == 20000 for r in rows)
    assert sum(r["charged_usd"] for r in rows) <= 0.5 + 1e-9
    assert len(rows) == 10  # 10 x 0.05 = 0.5; the 11th would pass the day cap
