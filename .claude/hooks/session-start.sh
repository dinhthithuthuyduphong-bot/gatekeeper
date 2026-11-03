#!/bin/bash
# SessionStart hook (every start, resume, clear and compact): makes the project rules apply in
# every session without relying on memory (CLAUDE.md, docs/research_rules.md R1-R6, lesson L14).
set -euo pipefail
cd "${CLAUDE_PROJECT_DIR:-.}"

# 1. Dependencies (cloud sessions only), skipped when nothing that decides them has changed.
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  hashes=.venv/.session-start.sha256
  if ! sha256sum --check --status "$hashes" 2>/dev/null; then
    rm -f "$hashes"
    if command -v uv >/dev/null 2>&1; then  # the existing .venv was created by uv (no pip inside)
      [ -x .venv/bin/python ] || uv venv -q .venv
      uv pip install -q --python .venv/bin/python -e ".[dev]"
    else
      [ -x .venv/bin/python ] || python3 -m venv .venv
      .venv/bin/python -m pip install -q -e ".[dev]"
    fi
    sha256sum .claude/hooks/session-start.sh pyproject.toml > "$hashes" || rm -f "$hashes"
  fi
  if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo "export PATH=\"$PWD/.venv/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  fi
fi

# Everything below only informs or installs the commit gate: it must never fail the session start.
set +e

# 2. Git pre-commit hook: preflight must pass, or git itself refuses the commit (L15).
if [ -d .git/hooks ]; then
  cp scripts/git-hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
fi

# 3. Reminder of the rules and of the latest records (read them before acting).
last() { grep -oE "$2" "$1" 2>/dev/null | tail -1 | grep -oE "[A-Z]-?[0-9]+"; }
echo "=== Gatekeeper: quy tắc bắt buộc của phiên này (CLAUDE.md) ==="
echo "R1 nguồn công bố, đã đọc bản gốc | R2 mọi con số có nhóm và căn cứ | R3 review trước khi chạy"
echo "R4 ghi mọi lỗi (audit + bài học) | R5 không đổi quy tắc sau khi thấy dữ liệu | R6 ký hiệu, ngưỡng rõ nghĩa"
echo "Danh sách review: docs/research_rules.md §4. Review song song: §3b."
echo "Mới nhất: lỗi $(last docs/audit_pilot.md '^\| A[0-9]+'), bài học $(last docs/lessons_learned.md '^## L[0-9]+'), review $(last docs/review_log.md 'R-[0-9]+')"
echo "Commit sẽ bị git chặn nếu preflight không đạt (.git/hooks/pre-commit)."

# 4. Long-running experiments: a worker restart kills background jobs and Docker (A50).
if command -v docker >/dev/null 2>&1; then
  docker info >/dev/null 2>&1 && echo "Docker: đang chạy" || echo "Docker: KHÔNG chạy (khởi động: dockerd &)"
fi
PY=python3
[ -x .venv/bin/python ] && PY=.venv/bin/python
for stage in "g1-e1-s41:e1_selected" "g1-e1-s51:e1_selected" "g1-e1-s61:e1_selected" \
             "g1-e1x-s41:e1x_selected" "g1-e1x-s51:e1x_selected" "g1-e1x-s61:e1x_selected" \
             "g2-e2-s41:e2_selected" "g2-e2-s51:e2_selected" "g2-e2-s61:e2_selected"; do
  name=${stage%%:*}; pool=configs/pools/${stage##*:}.json
  [ -f "$pool" ] || continue
  ls results/pilot/"$name"-p[0-9][0-9].json >/dev/null 2>&1 || continue
  left=$("$PY" scripts/missing_tasks.py "$name" "$pool" 2>/dev/null)
  [ -n "$left" ] && [ "$left" != "0" ] && echo "Dở dang: $name còn $left task (chạy tiếp bằng script của thí nghiệm, đi qua cổng preflight)"
done

# 5. Preflight once (report only: the gates block commits and paid runs).
if "$PY" scripts/preflight.py --ci > /tmp/gatekeeper-preflight-session.log 2>&1; then
  echo "Preflight: PASS"
else
  echo "Preflight: FAIL — xem /tmp/gatekeeper-preflight-session.log trước khi làm bất cứ việc gì"
fi
exit 0
