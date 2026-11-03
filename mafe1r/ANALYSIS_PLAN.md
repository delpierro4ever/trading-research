# MAFE-1R Analysis Plan (written and committed BEFORE any outcome/response is computed)

Scope: reconstruct the original MAFE study (frozen state 0056 "Terminal Same-Side Run") from surviving artifacts and
decompose why its economics looked positive in some periods and negative in others. Descriptive diagnosis only.
No optimisation, no new signals/thresholds/filters, no regime filter.

Labels used throughout: OBSERVED (computed now from re-downloaded data) / ARCHIVE (copied from surviving docs) /
ASSUMED (cost models) / PROXIED / INFERRED / UNKNOWN.

Status at time of writing: only data download + integrity statistics (row counts, id gaps, checksums, timestamps)
and a look at the futures file header/price level had been done. No anchor, response, P&L or regime statistic had
been computed.

## 0. Governance
- Discovery = 2023 (bin edges and any fitted constants come from 2023 only). Validation = 2024 (already read once in
  Phase B and again in Phase C; re-used here only for descriptive work on the SAME frozen 0056). Final test = prospective
  data, never reached.
- No Binance data dated after 2026-09-27 is downloaded or read (enforced in code: `CUTOFF`). Futures days used:
  2026-09-23, 2026-09-24 only.
- Only the frozen 0056 definition and its documented horizons may be evaluated. The readings below are interpretations of an
  UNKNOWN trigger, all pre-declared, ALL reported; none is selected by P&L.
- Anything needing a protected boundary is stopped and reported.

## 1. Data (M1)
- Spot BTCUSDT daily aggTrades 2023-01-01..2024-12-31 from data.binance.vision, SHA-256 checked against `.CHECKSUM`.
- Converted to parquet (agg_id, price, qty, first_id, last_id, ts_ms, buyer_is_maker). Timestamps in microseconds
  (if any) converted to ms. Per-day integrity: rows, duplicates, id gaps, monotonicity.
- Archive checks: 2023 rows 752,974,771; 2024 rows 551,044,283; 731 archives; compressed 17,717,147,907 B; 0 gaps/dups.
  Mismatches are reported, not corrected.
- Futures USD-M aggTrades 2026-09-23/24. bookTicker is not archived on data.binance.vision (404, checked) ->
  futures spread is PROXIED as 1 tick = 0.10 USDT (round trip, see costs).

## 2. Definitions (M2)
- Side: s = +1 if buyer_is_maker == false (aggressive buy), -1 otherwise.
- Run length L_i at event i: number of consecutive events ending at i with the same side as i, counted only inside the
  causal inclusive window {i-4..i}; so L in 1..5. The window cannot reach before the first event of the segment
  (window truncated; first 4 events of a segment have L computed on available events).
- Price reference = aggTrade price (spot has no quotes). The documented "mid" is PROXIED by trade price. UNKNOWN: the
  original mid reference.
- Event response at horizon h in {5,10,50,100,250}: R_h = s_i * (p_{i+h} - p_i)/p_i * 1e4 bps, defined if i+h is in the
  same segment. Clock response R_300s: p at the first trade with ts >= ts_i + 300,000 ms (next day's head is loaded for
  this; clock responses are not segment-limited).
- Continuity segment: UNKNOWN. Primary = one UTC-day archive (ids are checked for contiguity inside each file).
  Sensitivity S2 = ids contiguous across the whole calendar year (segment = year). Both anchor counts are reported as
  reconstruction checks, neither tuned.
- Anchors: event with 0-based index within segment % 250 == 0, union the first event of each 30 s UTC bucket
  (floor(ts/30000)). Anchor eligibility for a response at horizon h: the event i+h exists in-segment.
  Check: 2023 = 4,058,700 anchors; 2024 = 3,254,095 (ARCHIVE).
- Continuous coordinate: r = Pearson corr(L_i, R_5) over all anchors, per year (ARCHIVE: pooled r = 0.055, 2023). The
  original "effect 0.490/1.373" is UNKNOWN in unit; reported only as ARCHIVE, not reproduced (the measure is not defined
  in surviving docs). I will report mean R_5 by L and the standardised slope of R_5 on L (slope/sd(R_5)) as
  INFERRED-comparison, with no claim of equality.
- Readings of the trading trigger (UNKNOWN in archive). Pre-declared set, all evaluated:
  R1: every aggTrade is a signal (L>=1; direction = own side; baseline only)
  R2: L>=2   R3: L>=3   R4: L>=4   R5: L==5 (full run).
  Direction of a trade = side of the signal event (= run side).
  Additionally the anchor-level estimand is reported for all anchors by L (L=1..5) and for each reading's subset.
  Which reading (if any) reproduces the futures archive numbers is INFERENCE about the lost definition.
- Matching archive: "0056 fired on ~65% of all aggTrades" -> share of futures events with L>=k is reported for each k.

## 3. Trading replay (M2 check, M3 base) — fixed 300 s, one position at a time, taker
- Signal at trade j (time t_j, ts ms). Entry at the first trade with ts >= t_j + d (d = entry delay; futures check d in
  {100,250,500}; spot decomposition uses d = 500 ms only, the archive's primary branch). Entry price = that trade's price.
- Exit signal at entry_ts + 300,000 ms; exit executes at the first trade with ts >= entry_ts + 300,000 + 100 ms; exit
  price = that trade's price.
- One position at a time: next signal considered is the first signal trade with ts >= exit execution ts (state carried
  across days; position may straddle midnight).
- Gross (bps) = s*(p_exit - p_entry)/p_entry*1e4. Gross USD (0.001 BTC) = s*(p_exit - p_entry)*0.001.
- Futures check (2026-09-23/24): signals from entry >= 2026-09-23T10:27:00Z (start second UNKNOWN; assumption), closed
  trades with exit <= 2026-09-24T01:51:59.999Z. Compare to ARCHIVE: 182 trades/branch, gross +2.2432 / +0.8027 /
  -0.2239 USD (500/250/100 ms), 374 distinct signals (union of entry signals over branches), per-trade cost ~ $0.0179,
  chronological thirds of 500 ms net/trade +0.00706/-0.01698/-0.00650 (thirds = consecutive blocks of 61/61/60
  trades). Pass/fail is reported; no tuning. Exact reproduction is NOT expected (live book/latency differ from a tape
  replay with trade-price fills): a "pass" requires the same order of magnitude of trades (within 10%) and the same sign
  structure; gross USD is reported with a bootstrap CI and a comparison, not a pass/fail on the point value.

## 4. Cost models (ASSUMED; none is an observed historical cost)
- c1 (archive futures paper model): fee 1.0 bps/side x2 + slippage 0.05 bps/side x2 + spread proxy (one tick round
  trip = tick/entry price*1e4; tick 0.10 futures / 0.01 spot) -> ~2.10 bps. PROXIED spread.
- c2 (undiscounted spot taker, ARCHIVE cost floor): 21.03 bps flat per round trip. (Sub-components of the 1.03 over the
  20.0 bps fee are UNKNOWN.)
- c3 (Phase C friction gate): 1.0 bps flat per round trip.
- Cost USD = cost_bps*1e-4 * entry_price * 0.001. Net = gross - cost. Because costs are constant in bps, cost per
  trade in bps is constant across periods; cost in USD scales with price level. The only c1 term that varies with market
  state is the spread proxy; its maximum movement is quantified. Hypothesis E therefore cannot be tested with an observed
  cost; it is evaluated only as "gross vs fixed assumed friction" plus the maximum possible movement of the proxy.

## 5. Periods and decomposition (M3)
- Periods: each month 2023-01..2024-12, quarters, years, and the futures thirds. Table per reading x cost model:
  trades N, gross P&L (bps-sum and USD), gross/trade, cost, cost/trade, net, net/trade; plus anchor-level (non-trading)
  estimand per month (mean R_5, R_10, R_50, R_100, R_250, R_300s; overall and by L).
- Shift-share between periods A -> B (consecutive quarters, 2023 -> 2024, and 2023H1 -> 2023H2): with nu = net/trade =
  g - c: dNet = dN*nu_A + N_A*dg - N_A*dc + dN*(dg - dc). Exact identity; terms reported separately (trade-count term,
  gross-per-trade term, cost-per-trade term, interaction). Answers brief §10.
- Hyp B (marginal trade, within the frozen rule only): (i) mean gross/trade of trades by run length of the entry signal
  (L=2..5 under R2); (ii) anchor-level mean R_300s by L per month; (iii) gross/trade of trades in the first vs last third
  of each day's trade sequence and in high-count vs low-count months (split at the median monthly trade count of the
  whole sample; reported but note that one-at-a-time at 300 s saturates counts at <= ~288/day, so the count range is
  narrow). No new thresholds.
- Statistics: day-block bootstrap (10,000 resamples, days resampled with replacement within the period) for CIs of
  gross/trade and net/trade by period; heterogeneity across months: Q = sum_m n_m*(mean_m - mean)^2 and the best/worst
  month, null distribution by permuting whole days across month labels (10,000 permutations, preserving month sizes) -
  tests whether "positive periods" exceed what noise generates. Same by quarter.
- Decision language: "supported" requires the effect/shift-share term to dominate (>50% of |dNet|) AND a CI/permutation
  p-value (two-sided, alpha 0.05 uncorrected, reported with the number of tests) pointing the same way in both years;
  "unsupported" if the term is small (<20%) or CI spans 0 and sign inconsistent; otherwise "unresolved". Hypothesis
  verdicts: A trade-count; B marginal deterioration; C gross-edge deterioration (gross/trade or anchor response falls
  between periods beyond CI); D regime dependence (§6); E cost-regime (cost/g ratio moves because g moves; cost per trade
  in bps constant -> E collapses into C unless spread proxy matters); F combination if >=2 supported; G if evidence
  not decisive. Ranking: strongest supported / secondary / unsupported / unresolved.

## 6. Regimes (M4)
- Causal features at the anchor (and at trade entry) from completed 1-second bars strictly before the current
  second, trailing windows W in {300 s, 3600 s}: trade count (arrival rate), volume (BTC), realised volatility
  (sqrt of sum of squared 1-s last-trade-price log returns, bps), price-change frequency (share of events where price
  != previous event price), events per price change, mean trade size (BTC), burstiness (Goh-Barabasi
  (sigma-mu)/(sigma+mu) of 1-s counts). MEDIAN trade size is omitted (not cheaply causal-incremental); stated deviation.
  Calendar: hour UTC, weekday, month.
- Bin edges: terciles (33.3/66.7 percentiles) of each feature over 2023 anchors, fixed, applied unchanged to 2024.
  Hour UTC bins: 8-hour blocks (00-08, 08-16, 16-24); weekday: weekday/weekend.
- Outputs per bin: anchor-level mean R_300s (direction-normalised, per reading subset) and trade-level gross/trade and
  net/trade (c1,c2,c3) with day-block bootstrap CIs; heterogeneity test across the 3 bins (day-block bootstrap of the
  max-min bin difference + Spearman monotonic trend of bin index) separately for 2023 and 2024.
  Sign consistency across years is the stability criterion. No regime filter is created; results are descriptive.
- Compute: all days, all anchors (no sampling needed unless runtime forces; if sampling is used it is every 3rd day
  and stated).
- Structural-break check (context from outside the archive, to be CHECKED not assumed): Binance ended zero-fee BTCUSDT
  spot trading in March 2023. Daily series of row counts, mean trade size, share of L>=2, share L==5 and price-change
  frequency are examined around 2023-03-22 (before/after 28-day windows; difference in mean with day-block bootstrap).
  Reported as what the tape shows; causal attribution is INFERRED at most.

## 7. Report (M5)
REPORT.md in the 11-section structure of brief §16, each number tagged. Core question (brief §17) answered plainly;
"insufficient evidence" allowed. SUMMARY.md <= 250 words. Results CSVs in results/.

## 8. Amendments / deviations
Plan committed as 475f306df208f5294088b4224f7dd14fa13935a0 before any outcome was computed (verified: file unchanged until this section was edited).
After that commit the following were added or deviated from; items A2-A5 are POST HOC and EXPLORATORY (designed after seeing the tape
break and the weak 2023 Q1; not part of the pre-declared tests; counts of tests are large, p-values uncorrected).
- A1 (implementation deviations): (a) regime features are evaluated at the SIGNAL trade time, not the entry time (causal, <=0.5 s earlier);
  (b) the 2024 pass started with an empty carry state (a position open across 2023-12-31/2024-01-01 is not carried: at most one
  trade differs); (c) anchors near a day end lack a response only for event horizons (segment = day), 300 s clock responses use the next day's head;
  (d) median trade size only as a daily statistic (not a trailing-window feature) - as pre-declared; (e) bootstrap/permutation seeds fixed in code;
  (f) spot spread proxy tick = 0.01 USDT; (g) trade-level regime tests use 2,000 day-block resamples (anchors/trades), other bootstraps 10,000 / 3,000 for Hyp-B strata, as noted in code;
  (h) the bin-edge rule produced very uneven bin occupancy in 2024 (2023 terciles; e.g. 0% of 2024 anchors in the top change-frequency tercile) - reported as is.
- A2 (post hoc): `m5_diag.py` - anchors split into event-driven (i%250==0) vs time-driven (first-in-30s only), motivated by the gap between anchor-level
  and replay gross. Descriptive.
- A3 (post hoc): era split at 2023-03-22 (the date was named in plan §6 as a context check, but splitting the replay, the ladder and the regime tables by era is an
  extension chosen after seeing the daily series and 2023 Q1). `m5_diag.py` -> m5_replay_by_era.csv, m5_ladder_by_era.csv, m5_anchor_sampling_and_era.csv.
- A4 (post hoc): `m5_regime_postbreak.py` - the §6 regime bins re-run on days >= 2023-03-22 only, edges unchanged (all-2023 terciles).
- A5 (post hoc): `m5_hetero_post.py` - permutation heterogeneity test restricted to 2023-04..2024-12.
- No cost model, threshold, horizon, entry or exit rule was changed at any point. The reading set R1-R5 was fixed in advance; all five are reported.
