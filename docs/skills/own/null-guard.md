# null-guard

- Nguồn: `configs/skills/null-guard.json` (hand-written from mined family null_guard)
- Loại: guidance
- I(x): `[{"kind": "issue_regex", "pattern": "\\bis None\\b|\\bNone\\b.*(passed|given|returned)|returns? None"}]`

```text
The issue may involve a value that can be None (or missing). Before changing logic: find where the value is produced and every place it is used on the failing path; decide what None should mean there (default, skip, or a clear error); add an explicit `is None` check at the boundary where the value enters, not deep inside callers; keep behaviour for non-None inputs unchanged; add or run a test that passes None.
```
