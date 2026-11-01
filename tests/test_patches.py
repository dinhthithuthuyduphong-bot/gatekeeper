from gatekeeper.patches import composition_candidates, edit_patterns, parse_patch

PATCH = """diff --git a/pkg/io.py b/pkg/io.py
--- a/pkg/io.py
+++ b/pkg/io.py
@@ -10,6 +10,9 @@ def read_config(path, encoding=None):
     data = open(path).read()
+    if data is None:
+        raise ValueError("empty config")
+    data = data.decode("utf-8")
     return data
@@ -40,3 +43,8 @@ class Loader:
+    def load(self, x):
+        try:
+            return x.copy()
+        except AttributeError:
+            return x
diff --git a/tests/test_io.py b/tests/test_io.py
--- a/tests/test_io.py
+++ b/tests/test_io.py
@@ -1,2 +1,3 @@
+    assert x is None
"""


def test_parse_patch_excludes_tests():
    p = parse_patch(PATCH)
    assert p.files == ["pkg/io.py"]
    assert p.functions == {"pkg/io.py::read_config", "pkg/io.py::Loader", "pkg/io.py::load"}
    assert len(p.added) == 8 and p.removed == []
    assert len(parse_patch(PATCH, include_tests=True).added) == 9


def test_edit_patterns():
    pats = edit_patterns(parse_patch(PATCH))
    assert {"null_guard", "raise_error", "encoding", "exception_handling", "defensive_copy"} <= pats
    assert "dtype_cast" not in pats
    assert edit_patterns(parse_patch("")) == set()


def test_composition_candidates():
    tasks = [
        {"instance_id": "r-1", "repo": "r", "functions": ["a.py::f", "a.py::g"]},
        {"instance_id": "r-2", "repo": "r", "functions": ["a.py::f"]},
        {"instance_id": "r-3", "repo": "r", "functions": ["b.py::h"]},
        {"instance_id": "s-1", "repo": "s", "functions": ["a.py::f"]},
    ]
    assert composition_candidates(tasks) == [
        {"a": "r-1", "b": "r-2", "shared_functions": ["a.py::f"]}
    ]
