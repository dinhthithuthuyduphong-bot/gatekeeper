"""paper/refs.bib for the keys cited in paper/main.tex, from the saved originals (0 USD).

  python scripts/make_bib.py

A key is a source id of configs/sources.json. Title: taken from the snapshot on the
`sources-snapshots` branch (data/sources/<id>.json, field `head`) by a rule per page type
(GitHub issue/PR, arXiv abs/html, blog); authors only from data/citations.json (checked against
arXiv) when the arXiv id matches. Nothing is typed by hand: an entry whose title or authors cannot
be taken from these files gets note = {VERIFY ...} and is listed on stdout. A cited key without a
source id stops the script.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

# text of arXiv page chrome that must never end up in a title (A113m)
CHROME = ("Skip to main content", "Report GitHub Issue", "Back to arXiv")


def snapshot(key: str) -> dict | None:
    r = subprocess.run(
        ["git", "show", f"origin/sources-snapshots:data/sources/{key}.json"],
        capture_output=True,
        text=True,
    )
    return json.loads(r.stdout) if r.returncode == 0 else None


def title_from(url: str, head: str) -> str | None:
    h = " ".join(head.split())
    m = re.match(
        r"https://raw\.githubusercontent\.com/([^/]+/[^/]+)/([0-9a-f]{7})[0-9a-f]*/(.+)", url
    )
    if m:  # a source file pinned to a commit: the citation is the file itself
        return f"{m.group(1)}: {m.group(3)} (commit {m.group(2)})"
    if "github.com" in url and " · " in h:
        parts = h.split(" · ")
        if len(parts) >= 3 and re.match(r"(Issue|Pull Request) #\d+", parts[1]):
            return f"{parts[0]} ({parts[1]}, {parts[2]})"
        return parts[0]
    if "arxiv.org/html" in url and " Report GitHub Issue" in h:
        return h.split(" Report GitHub Issue")[0].strip()
    if "arxiv.org/abs" in url:
        m = re.match(r"\[[\d.v]+\]\s*(.+?)\s+Skip to main content", h)
        return m.group(1) if m else None
    if "gepa-ai.github.io" in url and " - GEPA" in h:
        return h.split(" - GEPA")[0].strip()
    return None


def arxiv_id(url: str) -> str | None:
    m = re.search(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", url)
    return m.group(1) if m else None


MONTHS = "Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
DATED = re.compile(
    rf"(?:opened|commented|merged|created)[^.]{{0,40}}?(?:{MONTHS})[a-z]* \d{{1,2}}, (20\d\d)"
)


def year_of(url: str, snap: dict, commits: dict) -> str | None:
    """Year from the saved originals only (ACM's style breaks on two year-less entries that share a
    label: "[n. d.]" plus a suffix letter):
    * arXiv: the identifier YYMM.NNNNN encodes the year of first submission;
    * a file pinned to a commit: the committer date of that commit (data/commit_dates.json,
      scripts/commit_dates.py);
    * a GitHub issue or pull request: the earliest dated event on the saved page."""
    ax = arxiv_id(url)
    if ax:
        return str(2000 + int(ax[:2]))
    m = re.match(r"https://raw\.githubusercontent\.com/[^/]+/[^/]+/([0-9a-f]{40})/", url)
    if m and m.group(1) in commits:
        return commits[m.group(1)]["committer_date"][:4]
    if re.match(r"https://github\.com/[^/]+/[^/]+/(issues|pull)/\d+", url):
        text = (snap.get("head") or "") + " " + json.dumps(snap.get("excerpts") or {})
        years = DATED.findall(" ".join(text.split()))
        return min(years) if years else None
    return None


def bib_escape(s: str) -> str:
    """Escape a title so LaTeX prints it as written (A162): `~` would print a space, `--` an en
    dash and a backtick a curly quote, which changes commands such as `git checkout HEAD~1 -- .`."""
    s = s.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
    s = s.replace("~", r"\textasciitilde{}").replace("`", r"\textasciigrave{}")
    while "--" in s:
        s = s.replace("--", "-{}-")
    return s


def main() -> int:
    tex = Path("paper/main.tex").read_text()
    keys = sorted({k.strip() for g in re.findall(r"\\cite\{([^}]*)\}", tex) for k in g.split(",")})
    src = json.loads(Path("configs/sources.json").read_text())
    ids = {s["id"] for s in (src if isinstance(src, list) else src["sources"])}
    r = subprocess.run(
        ["git", "show", "origin/data-snapshots:data/citations.json"], capture_output=True, text=True
    )
    cit = json.loads(r.stdout if r.returncode == 0 else Path("data/citations.json").read_text())
    cit = cit.get("arxiv", [])
    by_arxiv = {c["arxiv_id"].split("v")[0]: c for c in cit if c.get("exists_on_arxiv")}
    ov_path = Path("configs/bib_overrides.json")
    overrides = json.loads(ov_path.read_text()) if ov_path.exists() else {}
    cp = Path("data/commit_dates.json")
    commits = json.loads(cp.read_text()) if cp.exists() else {}
    out, verify, yearless = [], [], {}
    for k in keys:
        if k not in ids:
            # sources declared only on branch `trial` are allowed until the merge
            snap = snapshot(k)
            if snap is None:
                raise SystemExit(f"cited key {k} is not a source id and has no snapshot")
        snap = snapshot(k) or {}
        url = snap.get("url") or ""
        title = title_from(url, snap.get("head") or "")
        ax = arxiv_id(url)
        authors = None
        if ax and ax in by_arxiv:
            authors = " and ".join(by_arxiv[ax]["authors"])
            # arXiv's own title (checked by check_citations.py) over text cut from the page head,
            # which can carry page chrome ("Skip to main content") or lost spaces (A113m)
            title = " ".join(by_arxiv[ax]["title"].split()) or title
        ov = overrides.get(k, {})
        if ov:
            # every override must be read off the saved original: each author name and the title
            # must occur verbatim in the snapshot's text, or the script stops
            # only the source's own text: the snapshot's `claim` is our wording (A110m)
            text = " ".join(
                (
                    snap.get("head", "")
                    + " "
                    + json.dumps(snap.get("excerpts", {}), ensure_ascii=False)
                ).split()
            )
            names = [n.strip("{} ") for n in ov.get("author", "").split(" and ") if n.strip()]
            # `verify`: verbatim strings of the source when its spelling differs from BibTeX form
            need = ov.get("verify") or (names + [ov.get("title", "")])
            missing = [n for n in need if n and n not in text]
            if missing:
                raise SystemExit(f"{k}: override not found in the saved original: {missing}")
            authors = ov.get("author") or authors
            title = ov.get("title") or title
        chrome = [w for w in CHROME if w in (title or "")]
        if chrome:
            raise SystemExit(f"{k}: title carries page chrome {chrome}: {title}")  # A113m
        fields = {"title": "{" + bib_escape(title) + "}" if title else "{VERIFY: title}"}
        if authors:
            fields["author"] = "{" + authors + "}"
        year = ov.get("year") or year_of(url, snap, commits)
        if year:
            fields["year"] = "{" + year + "}"
        else:
            # the label ACM's style builds for an entry without author: first letters of the key
            label = (authors or "").split(" and ")[0].split()[-1] if authors else k[:3]
            yearless.setdefault(label, []).append(k)
        if ov.get("no_url"):
            # the saved original is a secondary source (Holm via Shaffer 1986, A155): print the
            # bibliographic data only, never the secondary source's URL as if it were the work
            fields["howpublished"] = "{" + ov["howpublished"] + "}"
        else:
            fields["howpublished"] = "{" + (
                ov["howpublished"] + ", " if ov.get("howpublished") else ""
            )
            fields["howpublished"] += "\\url{" + url + "}}"
        if snap.get("fetched_utc") and not ov.get("no_url"):
            fields["note"] = "{Accessed " + snap["fetched_utc"][:10] + "}"
        if not title or (
            not authors and not re.match(r"https://(github\.com|raw\.githubusercontent\.com)/", url)
        ):
            verify.append(k)
            fields["note"] = "{VERIFY title/authors from the saved original}"
        body = ",\n".join(f"  {f} = {v}" for f, v in fields.items())
        out.append(f"@misc{{{k},\n{body}\n}}")
    clash = {lab: ks for lab, ks in yearless.items() if len(ks) > 1}
    if clash:
        raise SystemExit(f"year-less entries sharing a label break the ACM style: {clash}")
    Path("paper/refs.bib").write_text(
        "% Generated by scripts/make_bib.py from sources-snapshots. Do not edit by hand.\n\n"
        + "\n\n".join(out)
        + "\n"
    )
    print(f"{len(keys)} entries; VERIFY: {verify}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
