# MAFE-1C PRE-REGISTRATION (written 2026-10-15; committed BEFORE any 2025 outcome and BEFORE any model is fitted)

Question (user): can we tell, from causal information, WHEN the 0056 trade is expensive or profitable? Net per trade = gross response − cost. The explicit
Binance fee is a fixed percentage; time variation of cost can only come from spread, latency slippage, size impact, fee-tier changes; gross may vary with state.
Test = whether the SIGN of expected net is predictable in advance, not whether some past period was positive. Open to other explanations (M5).

Labels: OBSERVED (computed from tape) / ASSUMED (fee schedule, adverse-selection constant) / PROXIED (spread, impact; no order book exists on data.binance.vision for these dates).

## 0. State of knowledge at the time of writing (what has and has not been read)
- 2023 and 2024 spot: read by MAFE and by mafe1r (incl. regime tables). Not virgin. Therefore the choice of state variables below is a-priori economic reasoning, but
  the author had seen mafe1r's regime tables (that price-change frequency had the sharpest 2024 contrast, that 2023-01-01..03-21 is a different tape regime with ≈0 response).
  This is disclosed; both facts influenced the choices in §5 (change-frequency as a state variable; exclusion of the pre-break era from the primary fit).
- 2025 spot and the futures sample (every 7th day of 2023/24/25): downloaded; only integrity statistics (rows, id gaps/duplicates, monotonicity, checksum, timestamp unit) have been computed.
  NO price, response, gross, cost or P&L statistic of any 2025 day has been computed. 2026 data are never read (code asserts date ≤ 2025-12-31).
- No cost-component statistic (Roll, slippage, impact) of any year has been computed yet.

## 1. Data
- Spot BTCUSDT daily aggTrades 2023-01-01..2025-12-31 (2023/24 from mafe1r, 2025 new), SHA-256 verified, parquet (µs timestamps converted to ms).
- USD-M futures BTCUSDT daily aggTrades, pre-declared systematic sample: day-of-year 1, 8, 15, … (every 7th day from Jan 1) of 2023, 2024, 2025 (53 days each). Each sampled day is
  processed in isolation (no carry-over; trades whose exit would fall after the day end are dropped; state windows are valid after 300 s / 3600 s into the day).
- Futures is **secondary** (descriptive: cost/gross variation, 2025 durability on the venue the paper trades used). The primary gate is on full-year spot 2025.

## 2. Frozen 0056 rule (reused from mafe1r code `mafe_core.py`, not redefined)
- Side from `buyer_is_maker`; run length L ≤ 5; signal = L==5 ("reading R5", the reading that reproduced the archive ladder); anchors every 250th event + first event of each 30 s bucket (segment = UTC day);
  event-response horizons 5/10/50/100/250 events and clock response 300 s.
- Trade replay: entry at first trade ≥ signal ts + 500 ms; exit at first trade ≥ entry ts + 300,100 ms; one position at a time; trade-price fills; 0.001 BTC. Gross_500 (bps) = s·(p_exit − p_entry)/p_entry·1e4.
- Replay carries state across midnight on spot (as mafe1r); spot 2025 starts from the mafe1r state of 2024-12-31 (R5 free time).

## 3. Cost models (all ASSUMED unless stated). Round-trip, bps of entry price, 0.001 BTC unless stated
Components computed causally from the tape at the SIGNAL event (state) and, for the realised cost, also at the exit event:
- **Spread proxy (PROXIED)**: Roll estimator on trailing 1000 aggTrade price changes within the UTC day: S = 2·sqrt(max(−cov(Δp_t, Δp_{t−1}), 0)); spread_proxy = max(S, 1 tick); windows with <200 events → 1 tick.
  tick = 0.01 (spot) / 0.10 (futures). Realised spread cost of a trade = (S_signal + S_exit)/2 / p_entry·1e4 (each leg pays half a spread). No real spread is observed. Roll on aggTrades is a crude estimator; its variability may be partly estimator noise — stated in the report.
- **Latency slippage (OBSERVED)**: L_d = s·(P(first trade with ts ≥ ts_sig + d) − P_sig)/P_sig·1e4 for d ∈ {100, 250, 500} ms. The trade enters at d = 500 ms, so L_500 is already INSIDE gross_500 (net = gross_500 − fee − spread − impact).
  Accounting identity used in variance decomposition: gross_0 := gross_500 + L_500 (response from the signal price), net = gross_0 − L_500 − fee − spread − impact.
- **Size impact (PROXIED)**: Kyle-type lambda from trailing 300 s of 1-s bars: λ = Σ(Δp_bps·v)/Σ v², v = signed volume (BTC, buyer aggressor +), λ⁺ = max(λ,0) in bps/BTC; impact_bps(q) = 2·λ⁺·q (two legs), q ∈ {0.001, 0.01}.
  Expected to be negligible at these sizes (reported, not hidden). Trade size relative to market = `meansize_300` (state variable).
- **K1** (archive paper model, continuity only): 2.0 + 0.10 + tick/p_entry·1e4.
- **K2** (primary): USD-M VIP0 taker 5.0 bps/side (public schedule as I understand it on 2026-10-15; NOT re-verified, assumed constant 2023–2025) → 10.0 + spread_bps + impact_bps(0.001).
- **K3** (sensitivity, fills not guaranteed): maker entry 2.0 + taker exit 5.0 + ½·spread_bps (exit leg only) + ½·impact + adverse selection 0.65 bps (archive §6 range 0.32–0.99; those two bounds as sensitivity).
- **K4** (spot continuity): spot VIP0 taker 10 bps/side → 20.0 + spread_bps + impact_bps(0.001); variant with BNB 7.5 bps/side → 15.0 + ….
- Note: K2 is a futures fee schedule applied to the spot tape for the primary gate (spot tape = price series proxy); the futures sample is the consistency check of that proxy.

## 4. M2 variation analysis (2023–2024 only; no 2025)
- Unit: R5 take-all replay trades (spot). Per month, per UTC hour, per weekday, and per causal-state tercile (rate_300, rv_300, meansize_300, chgfreq_300, burst_300; edges = `mafe1r/results/m4_bin_edges_2023.json`, frozen): gross_500, gross_0, L_100/250/500, spread bps, impact bps (both q), K1–K4 net (mean, day-block bootstrap 95% CI).
- "Is cost expensive at some times": distribution of each variable cost component relative to the fixed fee (component / K2 fee 10 bps) by month and state.
- Heterogeneity tests vs no-heterogeneity null, 10,000 permutations (seed 20261015): months → permute whole days over month labels; hour / state terciles → permute labels among trades WITHIN day (tests structure beyond day effects). Statistic Q = Σ n_k(mean_k − mean)²; also best/worst bin.
- Variance decomposition of monthly (and weekly) net_K2: Var(net) = Cov(net, gross_0) − Cov(net, V) where V = L_500 + spread_bps + impact_bps, fee constant ⇒ Cov(net, fee)=0; shares = Cov(net,gross_0)/Var(net) and −Cov(net,V)/Var(net) (sum to 1); 95% CI by resampling months/weeks.

## 5. M3 conditional model (fit on 2023-03-22..2023-12-31, check on 2024, freeze)
- State variables (≤3, fixed now): `rv_300` (realised volatility, bps, trailing 300 s), `rate_300` (trades/s), `chgfreq_300` (price-change frequency); mafe1r causal definitions (completed 1-s bars strictly before the signal second); terciles with the frozen 2023 edges → 27 cells. Reason: volatility scales both gross moves and slippage; activity ~ liquidity/spread; change frequency measures tick-level granularity, the variable the run signal itself is built on.
- Targets per trade: Y_g = gross_500; Y_v = spread_bps + impact_bps(0.001) (variable part of K2/K4); K1's variable part (tick/p) is known at signal time.
- **B1 (PRIMARY)**: binned cell means of Y_g and Y_v on R5 take-all trades 2023-03-22..2023-12-31. Cells with <200 training trades → training overall mean (no extrapolation). Rule(K) = take a signal iff Ŷ_g(cell) − (K_fixed + Ŷ_v(cell)) > 0 (K2: K_fixed=10.0; K1: 2.1 + tick bps; K3, K4 analogous).
  The rule is evaluated at every L==5 event; the replay (one position, same entry/exit rules) is run on the events that pass.
- Secondary models, same rule form, reported but never used for a claim: **B0** binned on ALL of 2023 (literal reading of the brief); **R1** ridge on [log rv_300, log rate_300, chgfreq_300] standardised with training moments, penalty α = 0.1·n_train, no tuning; **B2** B1 refit on 2023-03-22..2024-12-31.
- No thresholds are searched; no other variables or cell counts are tried. "Check on 2024": report, for B1/R1, the rule's 2024 trade count and net (not virgin; labelled), the cell-level rank correlation of Ŷ_g vs realised 2024 gross, and the trade count the rule would take. If B1 takes ZERO trades on 2024 (expected whenever max cell gross < fixed fee) this is reported as the result; the model is NOT modified.
- Freeze: model JSON (cell tables, ridge coefficients, edges) written to `mafe1c/results/frozen_models.json`; its SHA-256 is committed before the 2025 run.

## 6. M4 one-shot 2025 test (exactly once, after the freeze commit)
- **Primary gate (spot 2025, B1 under K2)**: trades = R5 replay of events passing Rule(K2); net/trade = gross_500 − K2 realised. PASS iff (i) ≥100 non-overlapping trades, AND (ii) mean net/trade > 0, AND (iii) one-sided p<0.05 by day-block bootstrap (10,000 resamples of days; ratio of sums; p = share of resamples with mean ≤ 0). If fewer than 100 trades pass the rule, the gate FAILS by (i); mean net of whatever trades exist is still reported.
- **Durability of 0056 (take-all, spot 2025)**: anchor ladder (L==5 and L≥2…): mean response at 5/10/50/100/250 events and 300 s; R5 replay gross_500/trade with day-block 95% CI. Durable iff the lower CI of R5 gross/trade > 0 AND the L==5 ladder is non-decreasing from event-5 to event-250. Compared to 2023-post-break and 2024 descriptively.
- Secondary (no claim, Holm across them): the take-all rule and B1/B0/R1/B2 rules under K1/K2/K3/K4; B1-K1, B1-K3, B1-K4 own-rule net.
- **Ranking**: weekly (ISO week, ≥20 take-all trades) Spearman between model-predicted mean net (B1, K2) and realised mean net of the take-all trades (K2), with permutation p (10,000); the same for gross alone. Reported with the number of weeks.
- Futures sample 2025 (secondary): R5 take-all replay on each sampled day, gross, L_d, K1/K2/K3 net.
- Everything is run once; code is frozen at the commit that contains `frozen_models.json`. No post-hoc 2025 look before the final run's output is saved.

## 7. Multiplicity
One primary test (§6, B1/K2 gate) at α=0.05 one-sided. Durability is a second pre-declared decision, a different question (two-sided CI, no multiplicity adjustment with the primary; stated). All other 2025 numbers are descriptive.
M2 heterogeneity tests are exploratory, ~ (months, hour, weekday, 5 states) × (≈9 outcomes) tests: p-values are reported with the count and a Holm-adjusted value; nothing from M2 is a claim of "regime exists" unless Holm p<0.05 AND the same sign in 2023-post and 2024.

## 8. Other
- Seeds: 20261015 everywhere. Bootstrap/permutation counts as stated.
- M5 (open possibilities) lists ideas and the data that would test them; none is tested except where a result above is already a by-product.
- Deviations → amendments below, each committed before the thing it changes is used.

## Amendments
- **A1 (committed with the model freeze, before any 2025 outcome; 2025 spot/futures outcomes still not computed).**
  (a) Implementation notes: the 2023–24 replay reproduces mafe1r's R5 trades exactly (208,043 trades, identical gross) except one extra trade on 2024-12-31 whose exit price is read from 2025-01-01; that trade is dropped from all 2024 analyses (exit_ts < 2025-01-01) to keep 2024 a 2024-only sample. 2025 spot starts from the 2024-12-31 carry state of this pipeline for the ALL rule (rule replays start flat).
  Impact λ and Roll are NaN/tick during the first 300 s / 200 events of a day without carry-over (impact set to 0 there). Latency slippage L_d uses the first trade at or after ts_sig+d.
  (b) Result of the 2024 check (reported in the report; model not modified): no model (B1, B0, R1, B2) predicts a positive net under any of K1–K4 for any 2023-fit or 2024 trade (max predicted net: K1 −0.32, K2 −8.26, K3 −5.89, K4 −18.26 bps), so every frozen rule will take ZERO trades in 2025 unless the 2025 state distribution leaves the fitted cells (in which case cells with <200 training trades use the training mean, so it cannot exceed it). The primary gate therefore fails condition (i) by construction; this was known before the 2025 run and is stated here.
  (c) Because the rules are empty, the following DESCRIPTIVE additions are pre-declared for the single 2025 read (no gate, no claim of profitability): (1) *top vs bottom predicted-gross cells*: among take-all 2025 trades, those whose B1 predicted gross is in the 5 highest-ranked cells vs the 5 lowest (ties by cell id), mean gross and K1–K4 net with day-block CIs and the day-block bootstrap CI of the difference — does the gross ranking replicate out of sample, regardless of cost? (2) *persistence baseline* for the weekly ranking: previous-week realised gross as the predictor. (3) 2025 state-bin occupancy vs 2023-post/2024.
