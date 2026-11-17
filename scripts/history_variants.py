"""Git-history variants of a SWE-smith task for C10 (docs/todo_ease_revision.md section 7).

Every SWE-smith task ships with exactly three commits (section 41, level 1, 1,086 of 1,086 tasks):
HEAD~2 "Initial commit" (tree T0, the fixed code), HEAD~1 "Bug Patch" (T1, the bug inserted),
HEAD "Remove F2P Tests" (T2, the failing tests deleted). The agent works on T2 in every variant.
Each variant rebuilds the history with `git commit-tree`, keeping each original commit's author,
committer, dates and full message unless the variant changes it, then removes every other ref,
the remote, the mirror, reflogs and unreachable objects. The cleanup is the same in all four
variants, so the cells differ only in the factor of the design:

  A  T0 -> T1 "Bug Patch" -> T2          original messages; HEAD hash equals the shipped one
  B  T0 -> T1 <neutral message> -> T2    bug diff visible, message replaced
  C  T1 -> T1 "Bug Patch" -> T2          message kept, empty diff (initial commit holds T1)
  D  T1 -> T2                            no bug commit
"Remove F2P Tests" (T1 -> T2) is identical in all four variants.

The neutral message has no default: it is fixed by the registration of C10.
"""

from __future__ import annotations

import shlex

VARIANTS = ("A", "B", "C", "D")
EXPECTED_SUBJECTS = "Remove F2P Tests|Bug Patch|Initial commit|"


def history_variant_sh(variant: str, neutral_message: str | None, root: str, mirror: str) -> str:
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    if (variant == "B") != (neutral_message is not None):
        raise ValueError("neutral_message is required for B and only for B")
    if neutral_message is not None and (not neutral_message.strip() or "Bug" in neutral_message):
        raise ValueError("neutral_message must be non-empty and must not name the bug commit")
    msg_b = shlex.quote(neutral_message or "")
    plan = {
        # (tree, parent, metadata of original commit k, message source) per new commit
        "A": [("T0", "", 0, "orig"), ("T1", "c0", 1, "orig"), ("T2", "c1", 2, "orig")],
        "B": [("T0", "", 0, "orig"), ("T1", "c0", 1, "neutral"), ("T2", "c1", 2, "orig")],
        "C": [("T1", "", 0, "orig"), ("T1", "c0", 1, "orig"), ("T2", "c1", 2, "orig")],
        "D": [("T1", "", 0, "orig"), ("T2", "c0", 2, "orig")],
    }[variant]
    lines = [
        "set -e",
        f"cd {shlex.quote(root)}",
        "s=$(git log --format=%s HEAD | tr '\\n' '|')",
        f'[ "$s" = {shlex.quote(EXPECTED_SUBJECTS)} ] '
        '|| { echo "unexpected history: $s"; exit 3; }',
        "br=$(git symbolic-ref -q --short HEAD || true)",  # empty when HEAD is detached
        "W=$(mktemp -d)",
    ]
    for k, ref in enumerate(("HEAD~2", "HEAD~1", "HEAD")):
        lines += [
            f"T{k}=$(git rev-parse {ref}^{{tree}})",
            f"git log -1 --format=%B {ref} > $W/m{k}",
            # raw dates ("<epoch> <+hhmm>"): the original offset is kept on every git version
            "git log -1 --date=raw --format='%an%x00%ae%x00%ad%x00%cn%x00%ce%x00%cd' "
            f"{ref} > $W/a{k}",
        ]
    lines.append(f"printf '%s\\n' {msg_b} > $W/neutral")
    for i, (tree, parent, k, src) in enumerate(plan):
        msg = f"$W/m{k}" if src == "orig" else "$W/neutral"
        par = f"-p ${parent}" if parent else ""
        lines += [
            f"IFS=$(printf '\\001') read -r AN AE AD CN CE CD < <(tr '\\0' '\\001' < $W/a{k})",
            f'c{i}=$(GIT_AUTHOR_NAME="$AN" GIT_AUTHOR_EMAIL="$AE" GIT_AUTHOR_DATE="$AD" '
            f'GIT_COMMITTER_NAME="$CN" GIT_COMMITTER_EMAIL="$CE" GIT_COMMITTER_DATE="$CD" '
            f"git commit-tree ${tree} {par} -F <(sed -e :a -e '/^\\n*$/{{$d;N;ba' -e '}}' {msg}))",
        ]
    last = f"c{len(plan) - 1}"
    lines += [
        f'if [ -n "$br" ]; then git update-ref "refs/heads/$br" ${last}; keep="^refs/heads/$br$"; '
        f"else git update-ref --no-deref HEAD ${last}; keep='^$'; fi",
        '[ "$(git rev-parse HEAD^{tree})" = "$T2" ]',
        "for r in $(git for-each-ref --format='%(refname)' | grep -v \"$keep\"); "
        'do git update-ref -d "$r"; done',
        'want=0; [ -n "$br" ] && want=1; [ "$(git for-each-ref | wc -l)" = "$want" ]',
        "git remote remove origin 2>/dev/null || true",
        f"rm -rf {shlex.quote(mirror)}",
        "git reflog expire --expire=now --all",
        "git gc -q --prune=now",
        "t0=$(git cat-file -e $T0 2>/dev/null && echo 1 || echo 0)",
        "echo variant=" + variant + " commits=$(git rev-list --all | wc -l) "
        "remotes=$(git remote | wc -l) "
        "bug_msg=$(git log --all --format=%s | grep -c '^Bug Patch$' || true) "
        "tests_commit=$(git log --all --format=%s | grep -c '^Remove F2P Tests$' || true) "
        "t0_present=$t0",
        "rm -rf $W",
    ]
    return "\n".join(lines) + "\n"


def expected_check(variant: str) -> str:
    commits, bug, t0 = {"A": (3, 1, 1), "B": (3, 0, 1), "C": (3, 1, 0), "D": (2, 0, 0)}[variant]
    return (
        f"variant={variant} commits={commits} remotes=0 bug_msg={bug} tests_commit=1 "
        f"t0_present={t0}"
    )
