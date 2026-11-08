"""Section 25 step 2: run gskill's own training script (gepa@8c7b697) under a hard spend cap.

gskill's train_optimize_anything.main() is called unmodified with the given argv. LiteLLM's
per-call response_cost is summed in a success callback; when spent_before + spent exceeds the
cap the ledger is written and the process exits with code 5 (the cap is not a stopping rule on
outcomes; it bounds money). The ledger is also written on normal exit.

  PYTHONPATH=<gepa>/src/gepa/gskill <venv>/bin/python scripts/gskill_learn.py \
      --cap 23.0 --spent-before 0 --ledger results/s25_learn_ledger_h1.json \
      --registry /tmp/registry.json -- --repo pallets__jinja ... (gskill's own arguments)
"""

from __future__ import annotations

import argparse
import atexit
import gzip
import json
import os
import sys
import threading
from collections import defaultdict
from pathlib import Path

_by_model: dict[str, float] = defaultdict(float)
_calls: dict[str, int] = defaultdict(int)
_lock = threading.Lock()
_state: dict = {}


def _write() -> None:
    led = {
        "spent_before": _state["before"],
        "spent_this_run": sum(_by_model.values()),
        "spent_total": _state["before"] + sum(_by_model.values()),
        "cap": _state["cap"],
        "by_model_usd": dict(_by_model),
        "calls_by_model": dict(_calls),
        "argv": _state["argv"],
    }
    Path(_state["ledger"]).write_text(json.dumps(led, indent=1) + "\n")


def _over() -> bool:
    return _state["before"] + sum(_by_model.values()) > _state["cap"]


def _stop() -> None:
    _write()
    total = _state["before"] + sum(_by_model.values())
    print(f"[cap] spent {total:.4f} > {_state['cap']}", flush=True)
    os._exit(5)


def install_meter(litellm, mock: str | None = None) -> None:
    """Wrap litellm.completion. gskill's cost_tracker assigns litellm.success_callback, which
    would silently drop a callback-based meter (the A84 failure mode), so the meter wraps the
    call itself: check the cap before each call, add completion_cost(response) after it."""
    original = litellm.completion

    def metered(*args, **kwargs):
        if _over():
            _stop()
        if mock is not None:
            kwargs["mock_response"] = mock
        r = original(*args, **kwargs)
        m = kwargs.get("model") or (args[0] if args else "?")
        c = float(litellm.completion_cost(completion_response=r) or 0.0)
        with _lock:
            _by_model[m] += c
            _calls[m] += 1
        if c <= 0.0:
            print(f"[meter] zero cost for {m}: cap would be blind (A84)", flush=True)
            _stop()
        if _over():
            _stop()
        return r

    litellm.completion = metered

    def unmetered(*args, **kwargs):  # batch_completion calls litellm.main.completion directly
        print("[meter] batch_completion is not metered; stopping", flush=True)
        _stop()

    litellm.batch_completion = unmetered


def main() -> int:
    if "--" not in sys.argv:
        raise SystemExit("usage: gskill_learn.py <own args> -- <gskill args>")
    i = sys.argv.index("--")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=float, required=True)
    ap.add_argument("--spent-before", type=float, required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--registry", required=True)
    ap.add_argument("--mock-response", help="free dry run: every LiteLLM call returns this text")
    ap.add_argument("--local-rows", help="dry run without HuggingFace: serve these exported rows")
    a = ap.parse_args(sys.argv[1:i])
    _state.update(before=a.spent_before, cap=a.cap, ledger=a.ledger, argv=sys.argv[i + 1 :])

    import litellm

    litellm.register_model(json.loads(Path(a.registry).read_text()))
    install_meter(litellm, a.mock_response)
    atexit.register(_write)

    from gskill import train_optimize_anything as t

    if a.local_rows:  # dry run only: exported rows are in gskill's shuffled order, so the split
        # of a dry run differs from the real one; the real run loads HuggingFace as gskill does
        raw = Path(a.local_rows).read_bytes()
        text = (gzip.decompress(raw) if a.local_rows.endswith(".gz") else raw).decode("utf-8")
        rows = [
            {k: v for k, v in json.loads(x).items() if not k.startswith("_gskill")}
            for x in text.splitlines()
            if x.strip()
        ]
        t.load_dataset = lambda *args, **kwargs: rows

    sys.argv = ["train_optimize_anything.py", *sys.argv[i + 1 :]]
    t.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
