# MAFE-3 Stage 3 — Cost-regime test of the frozen mean-reversion model (XAUUSD)

Registered 2026-10-14, before any 2020+ data is read for this purpose. Identity = sha256 of this file.

## Motivation (mechanical, not outcome-driven)

Stage 2 found a stable short-horizon mean-reversion signal. Its information coefficient was ≈ −0.03 to −0.045
with the same sign in 9–10 of 10 years. Its gross value was ≈ 1.1–1.7 bps per trade, below a cost of ≈ 2.7 bps
at 2010s prices. Retail gold cost is roughly fixed **in dollars**, while the gold price rose from ≈ $1 200 to
≈ $4 000. The user's live cTrader quote on 2026-10-14 (≈ 14:25 UTC) was bid 4094.62 / ask 4095.00, a $0.38 spread.
With commission assumed, the all-in cost is **$0.45/oz round trip**: ≈ 1.1 bps today against ≈ 3.7 bps at
$1 200. The cost hurdle therefore falls mechanically in the later periods. This stage asks whether the frozen
model clears it.

## Models (frozen; no tuning)

- **M30:** the stage-2 ridge model (α = 10, standardised inputs, the same frozen feature list
  `STAGE2_FEATURES.md`), target the 30-min forward log return.
- **M60:** the same model with a 60-min target.
- Ridge was chosen over LightGBM and over 240 min because of its higher discovery walk-forward *gross* (1.74 and
  1.58 bps, against ≤ 1.11). This choice uses discovery information only. **K = 2.**
- Each model is trained **once** on all discovery data (2010-01-01 → 2020-01-01) and then frozen: coefficients,
  scaler and feature code. Their hashes are recorded in the training commit, which happens before any 2020+
  prediction.

## Trading rule and cost

- Decision grid every 5 min. Entry is at the bar opening at t + 1 min; exit at entry + H. Greedy non-overlap; the
  weekend rule and swap model are the same as stage 1.
- Cost per trade c_t = 0.45 / entry_price × 1e4 bps. **Trade only if |prediction| > c_t + expected swap**, in the
  sign of the prediction. Expected swap is 0 unless the hold crosses the 17:00 New York rollover.
- Net = gross − c_t − swap. Also reported: net at $0.60/oz and at $0.38/oz (spread only).

## Validation (2020-01-01 → 2023-01-01, exits < 2023-01-01) — one read

PASS for a model requires **all** of: one-sided weekly-block-bootstrap p < 0.05/2 = 0.025 for mean net > 0
(at $0.45); mean net > 0 in ≥ 2 of 3 years; ≥ 30 distinct trading days; n ≥ 100.

## Holdout (2023-01-01 → latest) — one read, only for validation passers

The holdout is unsealed by the lead researcher only after a validation PASS. PASS requires one-sided p < 0.05
for mean net > 0 at $0.45, mean net > 0 in more than half of the calendar years, and net > 0 at $0.60
reported (not a gate). Only a holdout PASS goes to cTrader demo paper trading, with the same frozen model,
H and rule.

## Always reported

Per year: n, gross, cost in bps (it varies with price), net, the share of trades that are long, and the gold
price level. This separates "the pattern weakened" from "the cost changed".
