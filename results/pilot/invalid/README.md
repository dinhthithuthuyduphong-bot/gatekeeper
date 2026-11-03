# Invalid pilot runs (kept for the record, excluded from every analysis)

- `g1-a-lite.json` (02/11/2026): 3 of 8 agent runs failed to start their container
  (`docker run` exit 125: the task image was not pulled yet). The old pipeline scored those runs as
  "not solved" (loss 0.667), which biased the no-skill arm. Fixed in `scripts/run_pilot.py`
  (images pre-pulled; infrastructure failures excluded and reported). Re-run as `g1-a-lite2`.

- `g1-b/` (02/11/2026, 3.95 USD, 38 tasks): **seeding confound**. Vertex AI treats `seed=0` as
  *unset* (proto3 default is dropped): two seed-0 calls on the same prompt differ, two seed-1 calls
  are byte-identical (tested 02/11/2026). The no-skill arm and the positive control ran with
  seed 0 (unseeded sampling) while the noise control ran with seed 1 (deterministic sampling), so
  the noise control differed from the no-skill arm in *how* it sampled, not only in its seed. The
  pre-registered G1 rule fired correctly: noise control mean Z = −0.104, 90% CI
  [−0.19, −0.02] → STOP (`g1-b/g1_decision.json`). Discordant pairs split 8 vs 2 (sign test
  p ≈ 0.11), so chance alone is also plausible, but the run is not interpretable either way.
  No other defect found: identical overlays apart from the seed, 0 infra failures except one
  (xarray-6461), similar timeout and rate-limit counts per arm. Fixed: seeds start at 1 in
  `configs/models/vertex_gemini.json`, `arm_config` rejects seed 0
  (`tests/test_pilot.py::test_seed_zero_is_rejected`). Re-run as `g1-b2`.
  Spend still counts towards the cumulative pilot cap.
