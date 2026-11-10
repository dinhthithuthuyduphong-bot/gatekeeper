import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("gskill_learn", Path("scripts/gskill_learn.py"))
gl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gl)


class _Result:
    def __init__(self, code, text):
        self.exit_code, self.output = code, text.encode()


class _Container:
    def __init__(self, result):
        self.result, self.calls = result, []

    def exec_run(self, cmd):
        self.calls.append(cmd)
        return self.result


def _harness(result):
    class H:
        def setup_task(self, task_instance=None):
            self.container = _Container(result)
            return "set up"

    return H


def test_rewrite_runs_after_setup_and_is_counted(tmp_path):
    gl._state.clear()
    gl._state.update(before=0.0, cap=1.0, ledger=str(tmp_path / "l.json"), argv=[])
    H = _harness(_Result(0, "noise\nOK LINE\n"))
    gl.install_leak_free(H, "the script", "OK LINE")
    h = H()
    assert h.setup_task(task_instance={}) == "set up"
    assert h.container.calls == [["bash", "-lc", "the script"]]
    assert gl._state["lf_ok"] == 1


@pytest.mark.parametrize("result", [_Result(1, "OK LINE"), _Result(0, "commits=2 refs=1")])
def test_failed_rewrite_stops_the_run(tmp_path, monkeypatch, result):
    gl._state.clear()
    gl._state.update(before=0.0, cap=1.0, ledger=str(tmp_path / "l.json"), argv=[])
    codes = []

    def fake_exit(code):
        codes.append(code)
        raise SystemExit(code)

    monkeypatch.setattr(gl.os, "_exit", fake_exit)
    H = _harness(result)
    gl.install_leak_free(H, "s", "OK LINE")
    with pytest.raises(SystemExit):
        H().setup_task(task_instance={})
    assert codes == [6]
    assert gl._state.get("lf_ok", 0) == 0
