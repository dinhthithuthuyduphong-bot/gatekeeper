import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_net_kwargs(monkeypatch):
    import harness_net as hn

    monkeypatch.setenv("HTTPS_PROXY", "http://p:1")
    k = hn.net_kwargs()
    assert k["network_mode"] == "host"
    assert k["environment"]["HTTPS_PROXY"] == "http://p:1"
    assert k["environment"]["REQUESTS_CA_BUNDLE"] == hn.CA_IN
    assert k["volumes"][hn.CA] == {"bind": hn.CA_IN, "mode": "ro"}


def test_run_harness_uses_wrapper_only_when_asked(monkeypatch):
    from gatekeeper import harness

    seen = []
    monkeypatch.setattr(
        harness.subprocess,
        "run",
        lambda cmd, check: seen.append(cmd) or type("R", (), {"returncode": 0})(),
    )
    harness.run_harness("p.json", ["a"], "r", 1, dataset="d")
    harness.run_harness("p.json", ["a"], "r", 1, dataset="d", net=True)
    assert seen[0][1:3] == ["-m", "swebench.harness.run_evaluation"]
    assert seen[1][1].endswith("scripts/harness_net.py")
