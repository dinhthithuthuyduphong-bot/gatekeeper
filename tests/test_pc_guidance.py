import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "build_pc_guidance", Path(__file__).parents[1] / "scripts" / "build_pc_guidance.py"
)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

PATCH = """diff --git a/src/pkg/a.py b/src/pkg/a.py
--- a/src/pkg/a.py
+++ b/src/pkg/a.py
@@ -1 +1 @@
-x
+y
diff --git a/src/pkg/b.py b/src/pkg/b.py
new file mode 100644
diff --git a/src/pkg/a.py b/src/pkg/a.py
"""


def test_lists_each_modified_file_once_in_patch_order():
    assert m.files_of(PATCH) == ["src/pkg/a.py", "src/pkg/b.py"]
    g = m.guidance(PATCH)
    head = "The fix for this issue modifies the following file(s):\n"
    assert g == head + "- src/pkg/a.py\n- src/pkg/b.py\n"


def test_a_patch_without_files_is_an_error():
    with pytest.raises(ValueError):
        m.guidance("no diff here")
