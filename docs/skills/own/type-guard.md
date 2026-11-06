# type-guard

- Nguồn: `configs/skills/type-guard.json` (hand-written from mined family type_guard)
- Loại: guidance
- I(x): `[{"kind": "issue_regex", "pattern": "TypeError|isinstance|not supported between|unsupported operand"}]`

```text
The issue may involve an input of an unexpected type. Identify the accepted types from the documentation and existing callers; normalise inputs once at the public entry point (convert, or raise TypeError with a clear message) using isinstance checks; avoid sprinkling type checks through internal helpers; preserve existing accepted types; test each accepted and one rejected type.
```
