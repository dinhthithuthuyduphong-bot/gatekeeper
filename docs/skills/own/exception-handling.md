# exception-handling

- Nguồn: `configs/skills/exception-handling.json` (hand-written from mined family exception_handling)
- Loại: guidance
- I(x): `[{"kind": "issue_regex", "pattern": "\\braises?\\b.*\\b(should|instead|unexpected)\\b|\\bcatch\\b|\\bexcept\\b"}]`

```text
The issue may involve an exception that escapes or is swallowed. Reproduce it and read the full traceback; catch only the specific exception type at the level that can actually handle it; never use a bare `except:` or silently pass; re-raise with context (`raise ... from err`) when translating errors; make sure retries or fallbacks cannot hide a real failure; test both the error path and the normal path.
```
