import pytest


@pytest.fixture(autouse=True)
def _no_inherited_git_env(monkeypatch):
    """Tests that create temporary repositories must never act on the real one (A132): git sets
    GIT_DIR and GIT_INDEX_FILE for hooks, and a pre-commit run would pass them on to the tests."""
    for k in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX", "GIT_COMMON_DIR"):
        monkeypatch.delenv(k, raising=False)
