"""Fetch the primary sources in configs/sources.json and store short excerpts around keywords.

Runs in GitHub Actions (the development container cannot reach these hosts). Only excerpts are
kept (quotation for verification), never the documents. Writes data/sources/<id>.json.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

OUT = Path("data/sources")
UA = "Mozilla/5.0 (research verification; gatekeeper)"
WINDOW = 600  # characters on each side of a keyword hit, enough to read the full sentence
MAX_HITS = 4  # per keyword


def get(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read(), r.headers.get("Content-Type", "")


def to_text(raw: bytes, ctype: str) -> str:
    if raw[:4] == b"%PDF" or "pdf" in ctype:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(raw))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    html = raw.decode("utf-8", errors="replace")
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    return unescape(re.sub(r"(?s)<[^>]+>", " ", html))


def excerpts(text: str, keywords: list[str]) -> dict[str, list[str]]:
    flat = re.sub(r"\s+", " ", text)
    out = {}
    for k in keywords:
        hits = [m.start() for m in re.finditer(re.escape(k), flat)][:MAX_HITS]
        out[k] = [flat[max(0, i - WINDOW) : i + len(k) + WINDOW] for i in hits]
    return out


def previous_good(sid: str) -> dict | None:
    """Latest SUCCESSFUL snapshot of a source in the history of the sources-snapshots branch
    (audit A44: a failed re-fetch used to overwrite a good snapshot, e.g. nosek_2018)."""
    import subprocess

    path = f"data/sources/{sid}.json"
    try:
        shas = subprocess.check_output(
            ["git", "log", "--format=%H", "origin/sources-snapshots", "--", path], text=True
        ).split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    for sha in shas:
        try:
            d = json.loads(subprocess.check_output(["git", "show", f"{sha}:{path}"]))
        except (subprocess.CalledProcessError, ValueError):
            continue
        if d.get("url") and any((d.get("excerpts") or {}).values()):
            d["snapshot_commit"] = sha
            return d
    return None


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(Path("configs/sources.json").read_text())
    summary = {}
    for s in cfg["sources"]:
        rec = {"id": s["id"], "claim": s["claim"], "attempts": []}
        for url in s["urls"]:
            try:
                raw, ctype = get(url)
                text = to_text(raw, ctype)
                if len(text) < 2000:  # an interstitial/redirect page, not the document
                    raise ValueError(f"only {len(text)} characters: not the document")
                rec.update(
                    url=url,
                    sha256=hashlib.sha256(raw).hexdigest(),
                    n_chars=len(text),
                    head=re.sub(r"\s+", " ", text[:1500]),
                    excerpts=excerpts(text, s["keywords"]),
                )
                rec["attempts"].append({"url": url, "ok": True})
                break
            except Exception as exc:  # noqa: BLE001 - record and try the next mirror
                rec["attempts"].append({"url": url, "ok": False, "error": str(exc)[:200]})
        rec["fetched_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        if "url" not in rec:  # keep the last good snapshot, and say that the re-fetch failed
            old = previous_good(s["id"])
            if old is not None:
                old["refetch_failed"] = {"utc": rec["fetched_utc"], "attempts": rec["attempts"]}
                rec = old
        (OUT / f"{s['id']}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
        summary[s["id"]] = {
            "ok": "url" in rec,
            "url": rec.get("url"),
            "n_chars": rec.get("n_chars"),
        }
        print(s["id"], "OK" if "url" in rec else "FAILED", rec.get("url"))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
