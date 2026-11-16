import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import local_shim as ls  # noqa: E402


@pytest.fixture
def box(tmp_path, monkeypatch):
    """The module's fixed paths, moved under tmp_path; a base clone with one file."""
    state = tmp_path / "state"
    (state / "testbed").mkdir(parents=True)
    (state / "testbed" / "a.py").write_text("x = 1\n")
    monkeypatch.setattr(ls, "STATE", state)
    monkeypatch.setattr(ls, "WORKDIR", tmp_path / "testbed")
    return tmp_path


def test_each_container_sees_its_own_testbed_at_the_fixed_path(box):
    c1 = ls.Client().containers.create(image="img", name="c1")
    c2 = ls.Client().containers.create(image="img", name="c2")
    wd = str(ls.WORKDIR)
    assert (
        c1.exec_run("bash -c 'echo one > a.py; pwd -P'", workdir=wd).output.decode().strip() == wd
    )
    assert c2.exec_run("cat a.py", workdir=wd).output == b"x = 1\n"  # untouched by c1
    assert c1.exec_run("cat a.py", workdir=wd).output == b"one\n"
    c1.remove()
    c2.remove()
    assert (ls.WORKDIR / "a.py").read_text() == "x = 1\n"  # the base clone is back and unchanged
    assert sorted(p.name for p in ls.STATE.iterdir()) == ["active", "containers"]
    assert not list((ls.STATE / "containers").iterdir())


def test_exec_result_and_missing_command(box):
    c = ls.Client().containers.create(image="img", name="c")
    code, out = c.exec_run("bash -c 'echo hi; exit 3'")
    assert (code, out) == (3, b"hi\n")
    assert c.exec_run("no-such-command-xyz").exit_code == 127
    c.remove()


def test_swap_refuses_a_testbed_it_did_not_make(box):
    ls.WORKDIR.mkdir()
    with pytest.raises(RuntimeError):
        ls._swap(ls.STATE / "testbed")


def test_put_archive_writes_to_the_real_path(box, tmp_path):
    import io
    import tarfile

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        info = tarfile.TarInfo("eval.sh")
        info.size = 3
        t.addfile(info, io.BytesIO(b"ok\n"))
    c = ls.Client().containers.create(image="img", name="c")
    c.put_archive(str(tmp_path / "dest"), buf.getvalue())
    assert (tmp_path / "dest" / "eval.sh").read_text() == "ok\n"
    c.remove()
