# MAFE-3 Stage 2 — Machine-native pattern search + combined model (XAUUSD)

Registered 2026-10-14, after the MAFE-3 stage 1 validation failed. Identity = sha256 of this file, recorded in
its commit. Changes require dated amendments. Data and partitions are the same as stage 1 (HistData M1 BID;
discovery 2010–2019; validation 2020–2022; holdout 2023+ sealed by token). The 2020–2022 window was read once in
stage 1, for `G2_dow_fri` only. It is used here again only for the frozen stage-2 finalists below.

## 0. Why

Stage 1 tested 89 hand-written ideas at 1–24 h. Stage 2 asks the data directly. It builds a price-only library
of **market-behaviour features** (displacement, speed, compression/accumulation, absorption/rejection,
reversal, location, session, USD) and (A) searches it mechanically, then (B) combines everything in one model.
Gold's low cost (~2.6 bps) also makes **shorter horizons** worth testing for the first time.

## 1. Execution, cost, horizons

- **Decision grid:** every 5 minutes with an open market. Features use bars with close ≤ t − 1 min. Entry is at the
  bar opening at t + 1 min; exit at entry + H. The weekend rule and the swap model are the same as stage 1 (2.0 bps
  per 17:00 New York rollover, ×3 on Wednesday, both directions). Episodes never overlap within a candidate.
- **Cost (primary): $0.35/oz round trip. Robustness gate:** net must also be > 0 at **$0.50/oz**, because the real
  2009–2011 spreads were $0.41–0.51.
- **Candidate horizons:** H ∈ {5, 15, 30, 60, 240} min.
- **Step 0, oracle exclusion.** On discovery, compute the oracle ceiling per H: the mean maximum favourable
  excursion over the hold with perfect direction. Keep only H whose oracle is ≥ 4 × (cost at $0.35 + mean swap).
  This step only excludes horizons and never ranks anything.

## 2. Feature library (causal, price-only; z-scored over a trailing 20 trading days)

Definitions: ATR = mean true range over 60 one-minute bars; R_k = ln return over k minutes; σ_k = realised
volatility over k minutes.

| Concept | Features |
| --- | --- |
| Displacement | last-bar body / ATR (signed); largest signed 1 m body in the last 15 and 60 min / ATR; R_5 / σ_60·√5 |
| Speed | R_k / (σ_240·√k) for k ∈ {5, 15, 30, 60}; acceleration = speed_5 − speed_30; share of up-bars in the last 15 and 60 min |
| Compression / accumulation | range_60 / range_1440; σ_30/σ_240; count of inside bars in the last 30 min; close location in the 60 m range (0–1) during compression (that location × 1[range_60/range_1440 < its 20th percentile]) |
| Absorption / rejection | upper and lower wick share of the total range over the last 15 and 60 bars; touches of the 120 m high (low) within 0.25·ATR without a break in the last 60 min; signed rejection = (touches_high − touches_low) |
| Reversal / failed break | 1 if price traded above the prior 120 m high in the last 15 min but the close is back inside (and the mirror case, signed); V-score = R_15 after R_60 of opposite sign, as a fraction retraced |
| Location | distance (in ATR) to prior-day high, low and close, today's open, the 24 h TWAP, and the nearest $10 round number |
| Time | hour-of-day (cyclic sin/cos), session (Asia 00–07, London 07–12, overlap 12–16, NY 16–21 UTC), day of week |
| USD | EURUSD speed_15 and speed_60; EURUSD displacement (largest 1 m body in the last 15 min / its ATR) |

The total is about 45 features. The exact list and code are frozen in the commit that implements them, and
**that implementation commit is made before any return is computed.**

## 3. Track A — mechanical pattern search, internally replicated

- **Candidates:** (i) every feature × tail (≤ 10th or ≥ 90th percentile, thresholds fitted on discovery-A only)
  × kept H × direction (long/short); (ii) pairs of features from different concept rows, both in their tails
  (quintiles: ≤ 20th or ≥ 80th), × kept H × direction. Time features enter only as context in pairs (session ×
  another concept). The candidate count is recorded before evaluation.
- **Discovery-A (2010–2014): search.** BH at q = 0.10 on one-sided net > 0 across all candidates. Survivors
  also need n ≥ 100 non-overlapping episodes and net > 0 at $0.50.
- **Discovery-B (2015–2019): internal replication** of the A-survivors only, using A's thresholds. They need
  one-sided p < 0.05 / m_A (m_A = number of A-survivors), net > 0 at $0.35 and $0.50, and ≥ 3 of 5 years positive.
  Ties are broken toward the simplest definition (single feature before pairs). Near-duplicates (episode overlap
  > 50 %) are collapsed to one representative.
- **Validation (2020–2022), one read:** at most 10 B-survivors. They need p < 0.05/K, net > 0 at $0.50, and
  ≥ 2 of 3 years positive.
- **Overlap trap (MAFE lesson):** every statistic is computed on non-overlapping episodes and weekly block
  bootstrap p-values are reported. A candidate whose evidence comes from fewer than 30 distinct trading days
  is rejected.

## 4. Track B — combined model

- **Inputs:** all section-2 features at each grid point. **Target:** the H-ahead log return (one model per kept H).
- **Models, hyper-parameters fixed now (no tuning):** (B1) ridge regression, α = 10, standardised inputs;
  (B2) LightGBM regression with 300 trees, learning_rate 0.03, num_leaves 15, min_data_in_leaf 2 000,
  feature_fraction 0.7, bagging 0.7, and seed 7.
- **Trading rule:** long if the prediction > cost_bps($0.35) + expected swap; short if the prediction < −(the
  same); otherwise flat. Greedy non-overlap.
- **Out-of-sample within discovery (walk-forward):** train on 2010 … y−1, predict year y for y = 2013 … 2019,
  with a 1-day purge at each boundary.
- **Discovery gate:** pooled walk-forward net > 0 with weekly-block-bootstrap one-sided p < 0.05 / (number of
  models × kept H). It also needs net > 0 at $0.50, ≥ 5 of 7 years positive, and n ≥ 200.
- **Validation (one read):** surviving models are retrained once on 2010–2019, frozen, and applied to
  2020–2022. They need p < 0.05 / (number of survivors), net > 0 at $0.50, and ≥ 2 of 3 years positive.
- **Reported:** feature importances (LightGBM gain; ridge coefficients), so we can see *which* market
  behaviours carry information, even when nothing pays for costs.

## 5. Holdout

Only something that passes validation in track A or B may be tested once on the 2023+ holdout (one-sided
p < 0.05, net > 0 at $0.50). Only a holdout survivor goes to cTrader demo paper trading.

## 6. Diagnostics that are always reported (not gates)

The gross predictive content per concept, measured as the information coefficient (Spearman) between each
feature and the forward return per H on discovery, with its yearly stability. This answers "is there *any*
pattern?" separately from "does it pay?".
