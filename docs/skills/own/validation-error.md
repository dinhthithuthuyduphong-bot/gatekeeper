# validation-error

- Nguồn: `configs/skills/validation-error.json` (hand-written from mined family raise_error)
- Loại: guidance
- I(x): `[{"kind": "issue_regex", "pattern": "\\binvalid\\b|\\bValueError\\b"}]`

```text
The issue may be about missing or wrong input validation. Find the public function that receives the bad input; validate it there and raise the most specific built-in exception (usually ValueError or TypeError) with a message naming the parameter and the accepted values; match the project's existing error-message style; do not change behaviour for valid inputs; test the new error.
```
