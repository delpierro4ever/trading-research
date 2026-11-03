# MAFE-1R — Reconstruction and positive→negative investigation

Tags: **[OBS]** computed now from re-downloaded Binance data · **[ARCH]** copied from the surviving docs (README/EVIDENCE/LIMITATIONS/summary.json) · **[ASSUM]** assumed cost model · **[PROX]** proxy · **[INF]** inference · **[UNK]** unknown/lost.
Pre-registration: `ANALYSIS_PLAN.md`, commit `475f306df208f5294088b4224f7dd14fa13935a0` (before any outcome was computed). Post-hoc extensions A2–A5 are listed in its Amendments section and are exploratory. Data: 731 spot daily archives re-downloaded, all SHA-256 checksums verified; rows 2023 = 752,974,771 and 2024 = 551,044,283, compressed bytes 17,717,147,907, 0 duplicates, 0 id gaps, ids contiguous across day boundaries, ms timestamps — **all identical to the archive [OBS vs ARCH]**. Code and CSVs: `code/`, `results/`. Governance: no data after 2026-09-27 touched; futures days used = 2026-09-23/24 only.

## 1. Reconstructed MAFE strategy
- **What it measures [ARCH]:** aggregate-trade flow on Binance spot BTCUSDT; side = `buyer_is_maker` (false = aggressive buy). Trades only: no depth, spread, queue or latency.
- **Signal 0056 [ARCH]:** run length (1–5) of same-side trades ending at the anchor within the causal inclusive 5-event window; response = side-normalised price change to the 5th subsequent aggTrade; horizons 5/10/50/100/250 events; anchors = every 250th event + first event of each 30 s bucket.
- **Reconstruction evidence [OBS]:** my implementation reproduces the archive ladder when the state is **run length = 5** (L==5): 2023 0.004/0.028/0.146/0.204/0.264 bps vs ARCHIVE 0.004/0.029/0.145/0.203/0.260; 2024 0.083/0.154/0.495/0.687/0.881 vs 0.083/0.155/0.495/0.687/0.882. Correlation of run length with the event-5 response: 0.054 (2023) vs ARCHIVE 0.055. **[INF]** this strongly suggests the "0056 signal" for the ladder and (consistently) for entries is the full 5-run; the lower readings (L≥2…4) give clearly different ladders. Anchor counts: 2023 4,058,441 (day segments) / 4,058,633 (year segments) vs 4,058,700; 2024 3,253,772 / 3,254,037 vs 3,254,095 — within 0.002–0.010 %, **not exact** (segment definition [UNK]).
- **Trading rule [ARCH]:** enter in run direction on 0056, hold fixed 300 s, one position at a time, taker, 0.001 BTC, fee 1.0 bps/side, slippage 0.05 bps, spread at touch (USD-M futures paper). **[UNK]:** exact trigger, mid reference, continuity-segment definition, purge/embargo, 4 pooled cohorts' dates, any trade-level rows. I evaluated five pre-declared readings (R1 every trade; R2…R4 L≥k; R5 L==5), reported all, selected none by P&L; R5 is singled out only because of the reconstruction match above.
- **Futures tape check [OBS vs ARCH]** (2026-09-23/24; trade-price fills, 1-tick spread [PROX]; bookTicker is not archived → 404): R5 replay gives **182 trades per branch (ARCH 182)** and cost **$3.2518–3.2519 per branch (ARCH 3.2518)**; L==5 fires on 66.7 % of aggTrades (ARCH "about 65 %"). Gross 100/250/500 ms = +0.42/+2.41/+1.42 USD vs ARCH −0.22/+0.80/+2.24; iid CI of each total ≈ ±3 USD, so the gross is not distinguishable from the archive's. Distinct signals 469 vs ARCH 374 (fail); chronological thirds of net/trade at 500 ms −0.0168/−0.0115/−0.0017 vs ARCH +0.0071/−0.0170/−0.0065 (not reproduced). Live latency/book effects are absent from a tape replay, so exact gross reproduction was not expected.
- **Cause of economic rejection [ARCH]:** gross ≲1 bps vs 2.1 bps (futures) to 21 bps (spot taker) round trip; fees ≈95 % of cost.

## 2. Recovered historical results (ARCH only)
Phase A: 4,058,700 anchors, 0056 effect 0.490, r=0.055, positive 365/365 days. Phase B (2024): effect 1.373, 12/12 months. Phase C ladder and 1 bps gate failed in both years; "magnitude changed ~20-fold" and 2023 failed the quarter-stability gate. Futures paper: 182 trades/branch, gross −0.22/+0.80/+2.24 USD, net −3.49/−2.45/−1.01 USD; thirds (500 ms) +0.00706/−0.01698/−0.00650 USD/trade; SE of net/trade ≈ $0.0073 (n=182). Pooled four cohorts: gross ≈0.92 bps, cost ≈2.14 (scripts lost, secondary). **[UNK]** all trade-level rows, Phase A registry, per-month spot P&L (none ever existed in the surviving files).

## 3. What was previously rejected [ARCH]
Economic proof at every stage: Phase C gate (1 bps), forward spot probe (0 executions; 21 bps cost vs 0.745 bps gross), oracle ceiling (15.25 bps < 21.03 bps at 300 s), 14,652 candidates → 0 survivors, passive execution (adverse selection), futures paper (net negative on all branches), Position Manager (worse). Not rejected: the existence of a small gross directional effect.

## 4. Positive-versus-negative decomposition
Spot tape, R5, fixed 300 s, one position, 500 ms entry delay, trade-price fills **[OBS]**; costs **[ASSUM]**; gross USD per 0.001 BTC.

| Period | Trades | Gross P&L (USD, 0.001 BTC) | Gross/trade bps [95% CI] | Cost c1 (USD) | Cost/trade c1 bps (USD) | Net c1 (USD) | Net/trade c1 bps | Net/trade c2 bps | Net/trade c3 bps |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|
| 2023Q1 | 25,793 | -3.4 | -0.059 [-0.28, 0.17] | 123.7 | 2.104 (0.0048) | -127.0 | -2.163 | -21.09 | -1.059 |
| 2023Q2 | 25,851 | 31.4 | 0.431 [0.28, 0.57] | 152.2 | 2.104 (0.0059) | -120.8 | -1.672 | -20.60 | -0.569 |
| 2023Q3 | 26,021 | 34.2 | 0.466 [0.33, 0.62] | 153.9 | 2.104 (0.0059) | -119.7 | -1.637 | -20.56 | -0.534 |
| 2023Q4 | 26,166 | 40.7 | 0.439 [0.30, 0.57] | 199.1 | 2.103 (0.0076) | -158.4 | -1.664 | -20.59 | -0.561 |
| 2024Q1 | 25,937 | 69.8 | 0.483 [0.29, 0.68] | 291.2 | 2.102 (0.0112) | -221.4 | -1.619 | -20.55 | -0.517 |
| 2024Q2 | 25,886 | 87.8 | 0.509 [0.30, 0.71] | 357.4 | 2.102 (0.0138) | -269.6 | -1.593 | -20.52 | -0.491 |
| 2024Q3 | 26,171 | 65.3 | 0.409 [0.19, 0.63] | 335.5 | 2.102 (0.0128) | -270.3 | -1.693 | -20.62 | -0.591 |
| 2024Q4 | 26,218 | 65.1 | 0.291 [0.11, 0.47] | 459.4 | 2.101 (0.0175) | -394.3 | -1.810 | -20.74 | -0.709 |
| 2023 | 103,831 | 103.0 | 0.320 [0.23, 0.41] | 628.9 | 2.104 (0.0061) | -525.9 | -1.783 | -20.71 | -0.680 |
| 2024 | 104,212 | 288.0 | 0.422 [0.32, 0.52] | 1443.5 | 2.102 (0.0139) | -1155.5 | -1.679 | -20.61 | -0.578 |

Reading: gross per trade is positive in 21 of 24 months (negative only Jan–Mar 2023) yet **net is negative in every month, quarter and year under every assumed cost model** (best month: −1.39 bps under c1, −0.29 bps under c3 [OBS]). R1–R4 give the same picture (`results/m3_period_table.csv`). Any "positive" period therefore means gross-positive (or, for the futures thirds, a noisy net-positive third of 61 trades). The USD cost per trade grows 3.6× over the sample (0.0048→0.0175) only because BTC's price rose; gross USD grows with it, so bps ratios are unchanged.

## 5. Trade-count analysis (Hyp A) **[OBS]**
Under a fixed 300 s, one-position rule the count is capped at ≈288/day: R5 trades per month range 8,039–8,900; yearly 103,831 vs 104,212. Exact shift-share identity ΔNet = ΔN·ν_A + N_A·Δg − N_A·Δc + ΔN·Δν (bps·trades, c1):

| A → B | ΔNet (bps·trades) | trade-count term | gross/trade term | cost/trade term | interaction |
|---|---:|---:|---:|---:|---:|
| 2023Q1 → 2023Q2 | 12,560 | -125 | 12,634 | 23 | 28 |
| 2023Q2 → 2023Q3 | 626 | -284 | 904 | 0 | 6 |
| 2023Q3 → 2023Q4 | -932 | -237 | -709 | 19 | -4 |
| 2023Q4 → 2024Q1 | 1,553 | 381 | 1,159 | 23 | -10 |
| 2024Q1 → 2024Q2 | 748 | 83 | 656 | 11 | -1 |
| 2024Q2 → 2024Q3 | -3,062 | -454 | -2,577 | -3 | -28 |
| 2024Q3 → 2024Q4 | -3,164 | -80 | -3,090 | 11 | -6 |
| 2023 → 2024 | 10,186 | -679 | 10,616 | 210 | 40 |
| 2023H1 → 2023H2 | 12,881 | -1,041 | 13,734 | 43 | 145 |
| 2024H1 → 2024H2 | -8,540 | -909 | -7,564 | 15 | -82 |
| 2023H2 → 2024H1 | 2,923 | 601 | 2,262 | 76 | -16 |

In all 11 transitions the gross/trade term is larger in magnitude than the trade-count term (trade-count term 1–45 % of |ΔNet|, median ≈15 %; 2023→2024: −679 vs gross +10,616); the cost-per-trade term is ≈0 (cost in bps is constant by construction). **A is unsupported for this rule.** [UNK] whether the original "more trades" referred to cohorts with different counts; the archive gives only 182/branch.

## 6. Gross-edge analysis (Hyp C, B) **[OBS]**
- Gross is **statistically positive but small** outside the first quarter: 2023 0.320 [0.23, 0.41], 2024 0.422 [0.32, 0.52] bps/trade (day-block bootstrap, 10,000). Pooled 208,043 R5 trades: 0.371 bps.
- **Discrete break.** The tape changes abruptly on 2023-03-22 (daily rows ~10.3 M → 2.7 M → 0.8 M; −88 % over the 28-day windows, CI excludes 0; price-change frequency 0.885→0.578; mean size +38 %, median size −40 %; L==5 share 60.5 %→46.7 %). This matches the outside-the-archive claim that zero-fee BTCUSDT trading ended in March 2023; the tape shows the break, the cause is **[INF]**.
- **Era split (post hoc A3):** anchors L==5, mean response by event horizon 5/10/50/100/250/300 s — 2023 pre-break (Jan 1–Mar 21): −0.037/−0.038/−0.034/−0.037/−0.030/−0.052; 2023 post-break: 0.100/0.184/0.571/0.772/0.959/1.050; 2024: 0.083/0.154/0.495/0.687/0.881/0.943. Replay gross/trade (R5): pre-break −0.065 [−0.30, 0.20], post-break 0.430 [0.35, 0.51], 2024 0.422 [0.32, 0.53]. So the "20-fold change between years" in the archive (0.004 vs 0.083 at event 5) is mostly a pooling artefact: **2023 averages an effectively zero-response first 80 days with a 2024-like remainder** **[INF]**.
- **No further heterogeneity:** pre-declared permutation test, R5 gross/trade across months: 2023 p=0.002 (driven by Jan–Mar), 2024 p=0.67 (quarters 0.44); restricted to 2023-04…2024-12 (A5): months p=0.81, quarters p=0.73; best/worst month are inside the no-heterogeneity null (p=0.58/0.39). The late-2024 decline (Q4 0.29 vs ≈0.45) is not distinguishable from noise. **Positive-then-weaker periods are within what noise produces**, except the pre-break quarter.
- **Marginal trades (Hyp B, within the frozen rule, R2):** entries with run length 5 have higher gross than those with 2–4 (2023: 0.454 vs 0.135/0.243/0.119; 2024: 0.335 vs 0.061/0.057/−0.123; CIs wide), and the anchor ladder rises broadly with L. Weaker marginal signals exist but are a cross-sectional gradient; high-count vs low-count months show no difference (R5 0.370 vs 0.373). B explains **which** signals are weaker, not why periods differ over time.
- Anchor vs replay: event-driven anchors (i%250==0) have R300s ≈1.0–1.2 bps (post-break), time-driven ≈0.49, replay 0.42–0.43 bps. The headline anchor estimand is ≈2× the clock-sampled one (A2, descriptive) **[OBS]**; reason **[INF]**: event-count sampling over-weights busy times.

## 7. Cost analysis (Hyp E) **[ASSUM/PROX]**
Under c1/c2/c3 cost in bps is constant per trade (≈2.10 / 21.03 / 1.00), so cost cannot change across periods except through the spread proxy: 1 tick/price = 0.0010–0.0051 bps (0.05–0.24 % of c1). Gross/cost ratio (R5, post-break) ≈0.20 (c1), ≈0.02 (c2), ≈0.43 (c3); it moves only through gross. Break-even would need total round-trip friction below ≈0.4 bps (c1: 5×; c3: 2.4× too high). No historical spread, depth or slippage exists in the data, so "friction relatively larger" is **untestable with observed costs**; "the signal never covered the assumed friction in any period" is what the data support. **E: unsupported/unresolved.**

## 8. Market-regime analysis (Hyp D) **[OBS]**
Features (trailing 300 s/3600 s, causal): arrival rate, volume, realised vol, change frequency, events/price change, mean size, burstiness; hour, weekday; terciles from 2023 applied unchanged to 2024 (`m4_regime_bins.csv`).
- Full-sample 2023 shows steep gradients (e.g. anchors L≥5: rate_300 low→high tercile 0.99→−0.05 bps, change-freq 1.14→−0.04) — but **these are the pre-break era in disguise**: high-activity days are the pre-break days with ≈0 response. Restricting to post-break days (A4) the 2023 gradients vanish (every computable span CI includes 0; e.g. rate_300 −0.01 [−3.0, 3.2]).
- 2024 retains some negatives in the top-activity bins (anchors L≥5: volume_300 top bin −2.0 bps, n=50 k; rate_300 −0.45; span CI excludes 0) but small bins, not seen in 2023-post, and trade-level (R5) spans mostly include 0; e.g. change-frequency span +0.07 [−0.24, 0.37] (2023-post) vs −0.60 [−1.06, −0.19] (2024) — **inconsistent sign/size across years**. Hour-of-day (8 h blocks): trades +0.24 [0.06, 0.45] (2023) vs +0.08 [−0.18, 0.33] (2024), while the 2024 anchor estimand has the opposite sign (−0.29 [−0.53, −0.06]); weekday/weekend ~0.
- 2024 occupies almost only the lower two 2023 terciles of activity (e.g. 0 % in top change-frequency tercile), so 2023 edges cannot span 2024 conditions.
**Regime dependence beyond the 2023-03-22 break is not established**; it is neither excluded (small bins, wide CIs).

## 9. Strongest explanation (ranked)
1. **Strongest supported — gross-per-trade variation (C) concentrated in one discrete tape regime break (D, 2023-03-22), against a fixed friction that the gross never approached.** the gross/trade term dominates Δnet in every transition (75–144 % of ΔNet in the 7 quarter transitions; shift-share); outside Jan–Mar 2023 gross/trade is stable (0.29–0.51, heterogeneity p≈0.7–0.8). On the spot tape there never was a net-positive period under any cost model.
2. **Secondary:** B (cross-sectional: shorter runs are weaker) and sampling noise — the futures thirds swing (≈ +0.025 → +0.001 → +0.011 USD gross/trade, derived from ARCH net + ARCH mean cost [INF]) is ≈1.3 SE of the difference (SE(third) ≈ 0.0127 from ARCH SE 0.0073·√3); consistent with noise.
3. **Unsupported:** A (trade count; count is capped; term smaller than the gross term in all 11 transitions); E as an observed-cost effect (cost in bps constant by construction).
4. **Unresolved:** within-era regime dependence (D beyond the break); live futures behaviour (not reproducible: no rows, no book); whether "positive/encouraging" meant gross or net (no per-period historical P&L survives). Verdict among A–G: **F-like (C+D-by-break), with G for the original futures path.**

## 10. What remains unknown
Exact trigger/mid/segment/purge definitions; historical spread, depth, slippage, queue, latency; the dates of the 4 cohorts and all trade rows; whether futures behaved like spot in 2023–24; whether the zero-fee-era explanation (outside the archive) is the true cause of the break; whether the anchor-vs-replay 2× gap is weighting or something else; any regime effect hidden in small high-activity bins.

## 11. Research decision (§17 answer)
**Core question: neither of the two extremes is supported.** A small, statistically real gross directional effect exists on the post-break tape (≈0.4 bps at 300 s per trade, stable across 2023-Apr…2024-Dec within noise; absent in Jan–Mar 2023). It is **not** a phenomenon whose economic value "sometimes" clears friction: under every assumed cost model its net value was negative in every period, and the periods that looked positive are explained by gross-positivity or noise (insufficient evidence for any genuine regime-driven sign flip; G for the original futures sequence). The evidence does **not** justify further MAFE economic investigation of this signal at 300 s taker execution; the archive's conclusion stands. No optimisation, filter or strategy is proposed. Stop for review.

Limitations of this reconstruction: trade-price fills (no spread) overstate/understate gross by unknown bounce; 500 ms entry delay is the archive's primary branch only; many exploratory tests uncorrected; segment definition unknown; pre-declared regime bins poorly suited to 2024 occupancy.
