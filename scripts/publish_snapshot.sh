#!/usr/bin/env bash
# Append data files to a snapshot branch without ever carrying workflow files.
# GITHUB_TOKEN may not create or update .github/workflows/*, so a snapshot branch must not be
# re-created from main (whose workflows change); we add data-only commits on top of the branch.
# Usage: scripts/publish_snapshot.sh <branch> <message> <file-or-dir>...
set -euo pipefail
branch="$1"; msg="$2"; shift 2
stage="$(mktemp -d)"
for f in "$@"; do
  if [ -e "$f" ]; then mkdir -p "$stage/$(dirname "$f")"; cp -r "$f" "$stage/$f"; fi
done
git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git reset -q --hard
git clean -qfdx -e "$stage"
if git fetch -q origin "$branch" 2>/dev/null; then
  git checkout -q -B "$branch" "origin/$branch"
else
  git checkout -q --orphan "$branch"
  git rm -rq --cached . >/dev/null 2>&1 || true
  git clean -qfdx
fi
cp -r "$stage"/. .
git add -f -- "$@"
if git diff --cached --quiet; then echo "nothing new to publish"; exit 0; fi
git commit -q -m "$msg"
git push origin "$branch"
echo "published to $branch"
