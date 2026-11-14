import io
import sys
import tarfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import udocker_shim as us  # noqa: E402


def _container(tmp_path, monkeypatch):
    root = tmp_path / "root"
    (root / "testbed").mkdir(parents=True)
    (root / "testbed" / "a.py").write_text("x = 1\n")
    monkeypatch.setattr(us, "base_container", lambda image: "base")
    monkeypatch.setattr(us, "_root", lambda name: root)
    return us.Client().containers.create(image="img", name="c"), root


def _tar(name: str, text: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        data = text.encode()
        info = tarfile.TarInfo(name)
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_each_container_gets_its_own_copy_of_testbed(tmp_path, monkeypatch):
    c1, root = _container(tmp_path, monkeypatch)
    c2 = us.Client().containers.create(image="img", name="d")
    (c1.testbed / "a.py").write_text("x = 2\n")
    assert (c2.testbed / "a.py").read_text() == "x = 1\n"
    assert (root / "testbed" / "a.py").read_text() == "x = 1\n"  # the base image is never edited
    c1.remove()
    assert not c1.testbed.exists() and c2.testbed.exists()


def test_put_archive_goes_to_the_copy_inside_testbed_and_to_the_root_outside(tmp_path, monkeypatch):
    c, root = _container(tmp_path, monkeypatch)
    c.put_archive("/testbed/sub", _tar("f.txt", "in testbed"))
    c.put_archive("/tmp", _tar("patch.diff", "outside"))
    assert (c.testbed / "sub" / "f.txt").read_text() == "in testbed"
    assert not (root / "testbed" / "sub").exists()
    assert (root / "tmp" / "patch.diff").read_text() == "outside"


def test_command_line_mounts_the_copy_and_splits_like_docker_exec(tmp_path, monkeypatch):
    c, _ = _container(tmp_path, monkeypatch)
    seen = {}

    class P:
        returncode = 0

        def communicate(self):
            return b"ok", None

    monkeypatch.setattr(us.subprocess, "Popen", lambda argv, **kw: seen.update(argv=argv) or P())
    r = c.exec_run("git checkout -- 'a b.py'", workdir="/testbed", environment={"K": "v"})
    argv = seen["argv"]
    assert (r.exit_code, r.output) == (0, b"ok")
    assert f"--volume={c.testbed}:/testbed" in argv and "--workdir=/testbed" in argv
    assert "--env=K=v" in argv and argv[-4:] == ["git", "checkout", "--", "a b.py"]
