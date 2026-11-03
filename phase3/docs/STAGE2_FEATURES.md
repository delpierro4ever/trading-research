# MAFE-3 Stage 2 — frozen feature list (implementation of STAGE2_PREREGISTRATION.md section 2)

Frozen by the commit "phase3 s2: feature library (frozen before outcomes)", made before any forward return was computed.
Code: `phase3/code/mafe3/stage2/features.py`. Tests: `test_features.py` (results in `results/stage2/feature_tests.json`).

## Conventions (implementation decisions where section 2 is ambiguous; conservative reading)

- **Grid.** Every epoch minute t that is a multiple of 5, with a gold bar among the 6 minutes ending at t−2. Features use bars with label ≤ t−2
  (close ≤ t−1 min), exactly as in stage 1. All windows are trailing, in calendar minutes, evaluated at j = t−2; missing minutes are NaN and
  skipped; a window needs a minimum number of present bars (`min` below), otherwise the feature is NaN.
- **Primitives (1-minute bars, BID).** `body = c − o`; `TR = max(h−l, |h−c₋₁|, |l−c₋₁|)` (just `h−l` if the previous minute has no bar);
  `ATR = mean TR over 60 min` (min 36); `ret1 = ln(c/c₋₁)` only between consecutive minutes; `σ_k` = per-minute root-mean-square of ret1 over
  the last k min (min 0.5k) — a per-minute volatility, so `R_k/(σ·√k)` is a k-minute z-return; `cf` = last close (stale ≤ 3 min); `R_k = ln(cf_j/cf_{j−k})`.
- **Normalisation.** Every non-time feature is z-scored over the trailing 20 trading days (5 760 grid points including the current one, ≥ 1 440 valid,
  mean/std) at grid level. Time features are not z-scored. Z-scores are not clipped (Track A is percentile based; ridge clips at ±5, see report).
- **Daily features** use the FX trading day that ends at 17:00 America/New_York (same rollover as the swap model).
- **Session** uses the decision time t (UTC): Asia 0–7, London 7–12, overlap 12–16, NY 16–21; 21–24 UTC = −1 (no session).
- **Sign conventions.** Signed features are positive when bullish for gold (up).

## Features (38 columns; 34 non-time + 4 time. The model input for ridge expands session and weekday to one-hot: 2 + 4 + 5 + 34 = 45)

| # | name | concept | formula (j = t−2) |
|---|---|---|---|
| 1 | d_body1 | Displacement | (c−o of the last bar, ≤ 5 min stale) / ATR |
| 2 | d_maxb15 | Displacement | signed body with the largest |body| among the last 15 min (min 9) / ATR |
| 3 | d_maxb60 | Displacement | same over 60 min (min 36) / ATR |
| 4 | d_r5s60 | Displacement | R_5 / (σ_60·√5) |
| 5–8 | s_5, s_15, s_30, s_60 | Speed | R_k / (σ_240·√k) |
| 9 | s_acc | Speed | s_5 − s_30 |
| 10–11 | s_up15, s_up60 | Speed | share of up bars (c > o) among present bars of the last 15 / 60 min |
| 12 | c_rng | Compression | (max h − min l over 60 min) / (same over 1 440 min, min 240 bars) |
| 13 | c_volr | Compression | σ_30 / σ_240 |
| 14 | c_inside30 | Compression | number of inside bars (h ≤ h₋₁ and l ≥ l₋₁) in the last 30 min |
| 15 | c_loc60 | Compression | (cf − min l₆₀)/(max h₆₀ − min l₆₀) |
| 16 | c_loc60c | Compression | c_loc60 × 1[c_rng < trailing 20th percentile of c_rng over the 5 760 previous grid points] (built at grid level) |
| 17–18 | a_uw15, a_lw15 | Absorption | Σ upper wick / Σ range (upper wick = h − max(o,c); lower = min(o,c) − l; range = h − l) over the last 15 bars |
| 19–20 | a_uw60, a_lw60 | Absorption | same over 60 bars |
| 21 | a_th | Absorption | in the last 60 min, count of bars whose high is within 0.25·ATR *below* the prior 120 m high (excluding that bar) without exceeding it |
| 22 | a_tl | Absorption | mirror: low within 0.25·ATR above the prior 120 m low without breaking it |
| 23 | a_rej | Absorption | a_th − a_tl |
| 24 | r_fail | Reversal | +1 if in the last 15 min a bar's low broke the prior 120 m low and cf ≥ the highest broken low level; −1 if a bar's high broke the prior 120 m high and cf ≤ the lowest broken high level (both ⇒ 0) |
| 25 | r_v | Reversal | if R_15 and R_60 (the 60 min ending 15 min before j) have opposite signs: R_15/|R_60| clipped to [−2, 2] (signed by R_15; the retraced fraction), else 0 |
| 26–28 | l_pdh, l_pdl, l_pdc | Location | (cf − prior-day high / low / close) / ATR |
| 29 | l_open | Location | (cf − today's open) / ATR |
| 30 | l_twap | Location | (cf − mean close over 1 440 min, min 240) / ATR |
| 31 | l_round | Location | (cf − nearest multiple of $10) / ATR |
| 32–33 | t_hsin, t_hcos | Time | sin / cos of 2π·(UTC time of day of t in hours)/24 |
| 34 | t_sess | Time | session code 0..3 (−1 = none) |
| 35 | t_dow | Time | weekday of t (UTC), Monday = 0 |
| 36–37 | u_s15, u_s60 | USD | EURUSD R_k/(σ_240·√k) (EURUSD's own σ) for k = 15, 60 |
| 38 | u_disp | USD | EURUSD signed largest 1 m body in the last 15 min / EURUSD ATR |

Concept rows for Track A pairs: Displacement (4), Speed (7), Compression (5), Absorption (7), Reversal (2), Location (6), USD (3); Time only as session context.

## Tests

See `results/stage2/feature_tests.json`: (1) lookahead — bar values with label > t*−2 replaced by garbage (kept availability), at 8 random cutoffs
(including right after a rollover and right after a Sunday reopen, across a year boundary) ⇒ raw and z-scored features at all decision times ≤ t*
identical (0 mismatches); sensitivity — garbage from one bar earlier changes the features at t* (174 of 272 feature checks). (2) 2010 shape/NaN report:
72 124 grid rows, 38 columns, no infinities; NaN fractions 0–8 % (largest: a_th/a_tl/a_rej 7.9 %, c_rng/c_loc60c/l_twap ≈ 6 %, caused by the minimum-bars rules after reopen).
