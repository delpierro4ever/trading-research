# Stage 3 summary
**Result: both models FAIL validation. No model goes to the holdout; it stays sealed (no data ≥ 2023-01-01 read, token untouched).**

Commits: dde3f3e (frozen models, before any 2020+ read) · ca7ea48 (repro + script, dry-run on discovery only) · 0024d2b (validation, report). Prereg sha256 verified.

**Reproduction:** stage-2 ridge Track B walk-forward re-run matches the committed summary (3 rows) and walk-forward (21 rows) exactly, max abs diff 0.0. The retrained M30/M60 coefficients are bit-identical to the stage-2 final ridge pickles.

**Model sha256:** M30 cb87bbcf…fd7cc · M60 9f285bea…e459c (full in results/stage3/models.json).

| | n | gross | cost | swap | net .45 | net .60 | net .38 | p | verdict |
|---|---|---|---|---|---|---|---|---|---|
| M30 | 19 | 1.56 | 2.52 | 0 | −0.96 | −1.80 | −0.57 | 0.657 | FAIL |
| M60 | 140 | −2.70 | 2.49 | 0 | −5.18 | −6.01 | −4.80 | 0.944 | FAIL |

Per-year net / cost (bps): M30 2020 −1.94/2.54, 2021 +2.47/2.45, 2022 +0.71/2.47 (n=14/3/2). M60 2020 −8.70/2.51, 2021 −2.46/2.48, 2022 −3.60/2.47 (n=54/47/39).

**Notes:** M30 fails n≥100 and days≥30 (the hurdle exceeds nearly every prediction). M60's gross edge vanished (negative in 2020, ≈0 later), so it is not a cost effect. Gold averaged ≈ 800 in 2020–22, so the cost fell only to ≈2.5 bps; the ≈1.1 bps regime lives mainly in the sealed 2023+ period. Nothing suspicious found. The ridge pipeline was unchanged.
