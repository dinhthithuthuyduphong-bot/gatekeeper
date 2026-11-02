# Invalid pilot runs (kept for the record, excluded from every analysis)

- `g1-a-lite.json` (02/11/2026): 3 of 8 agent runs failed to start their container
  (`docker run` exit 125: the task image was not pulled yet). The old pipeline scored those runs as
  "not solved" (loss 0.667), which biased the no-skill arm. Fixed in `scripts/run_pilot.py`
  (images pre-pulled; infrastructure failures excluded and reported). Re-run as `g1-a-lite2`.
