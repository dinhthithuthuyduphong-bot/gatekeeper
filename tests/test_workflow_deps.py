import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from preflight import check_workflow_deps  # noqa: E402


def test_litellm_without_mcp_is_flagged(tmp_path):
    (tmp_path / "a.yml").write_text('run: pip install -q "litellm==1.106.6" "google-auth"\n')
    (tmp_path / "b.yml").write_text('run: pip install -q "litellm==1.106.6" mcp  # note\n')
    (tmp_path / "c.yml").write_text('run: pip install "litellm==1.106.6" "mcp>=1.0"\n')
    bad = check_workflow_deps(tmp_path)
    assert len(bad) == 1 and "a.yml" in bad[0]


def test_repository_workflows_pass():
    assert check_workflow_deps() == []
