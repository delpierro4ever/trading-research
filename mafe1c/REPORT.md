# MAFE-1C — When is the 0056 trade profitable? Conditional economics + one-shot 2025 test

Labels: **[OBS]** measured on the Binance tape · **[ASSUM]** assumed (fees, adverse-selection constant) · **[PROX]** proxy (spread = Roll estimator on aggTrades, impact = Kyle-lambda; no order book exists for these dates) · **[INF]** inference · **[SPEC]** speculation.
Pre-registration: `PREREG.md` (commit efdd5e6, before any 2025 outcome and any fit; amendment A1 and the model freeze `results/frozen_models.json`, sha256 `e937568…b7474`, in f04b46c, before the 2025 run). 0056 is reused exactly from `mafe1r/code/mafe_core.py` (reading R5: run of 5 same-side trades, 500 ms entry, 300 s hold, one position, 0.001 BTC). My replay reproduces mafe1r's 208,043 trades and gross exactly, plus one extra 2024-12-31 trade (exit read from 2025-01-01) that I drop from 2024.
Data **[OBS]**: spot BTCUSDT 2025, 365 days, 441.6 M trades, all SHA-256 checksums verified, 0 duplicates, 0 id gaps, ids contiguous across days; USD-M futures sample = every 7th day of 2023/24/25 (53 days each, 213.8 M trades), same checks. 2026 never read. 2025 was read once, after the freeze.

## Answers in one paragraph
Cost is almost constant: the fixed fee is 98.5–99.9 % of K2 (and more of K4); the time-varying parts (spread proxy, impact) are 0.01–0.15 bps against a 10 bps fee. The one varying quantity that is not negligible is latency slippage (0.18–0.36 bps), which is of the same size as the gross. Gross varies, but not detectably beyond noise. A model that tells in advance when expected net > 0 does not exist in this data: under every cost model the best state-cell is below break-even, so the frozen rule traded **zero** times in 2025 and the primary gate failed. The 0056 gross effect itself is durable in 2025 (0.32 bps/trade), but it is 6.5× (K1) to 60× (K4) smaller than the cost models. "Positive periods" were gross-positive periods, never net-positive.

## 1. Does cost vary over time, by how much, which component?
Spot tape, R5 take-all trades, bps of notional per round trip, means **[OBS]** except spread/impact **[PROX]**:

| sample | trades | gross₅₀₀ | latency slip 500 ms (inside gross) | spread (Roll) | impact 0.001 BTC | K2 cost | var. share of K2 cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 pre-break (Jan 1–Mar 21) | 22,970 | −0.065 | 0.005 | 0.154 | 0.0003 | 10.154 | 1.5 % |
| 2023-03-22→12-31 | 80,861 | 0.430 | 0.231 | 0.0144 | 0.0004 | 10.015 | 0.15 % |
| 2024 | 104,212 | 0.422 | 0.358 | 0.0119 | 0.0008 | 10.013 | 0.13 % |
| 2025 | 103,632 | 0.321 | 0.354 | 0.0076 | 0.0010 | 10.009 | 0.09 % |

- Monthly mean spread proxy ranges 0.005–0.15 bps (30×), but the 30× is the tape break plus the price level (tick/price fell from 0.0036 to 0.0010 bps); 57–82 % of trades sit at the 1-tick floor, so the proxy is mostly its floor. Largest single-trade spread proxy 3.7 bps. Impact at 0.001/0.01 BTC: ≤0.001/0.01 bps — negligible at this size. The only fee-side variation is the tier (assumed constant) — **cost "expensive at some times" is, within what the tape can show, a < 0.2 bps effect on a 10 bps fee.**
- Heterogeneity (day-block/within-day permutations, 10,000; 45 tests per scope; Holm): latency slippage varies strongly by month, hour, weekday and volatility/activity tercile (Holm p = 0.0045, all scopes); spread varies with state and month (Holm < 0.05); impact trivially. Latency slippage is higher in high-volatility states (rv tercile 0.15→0.57 bps in 2023-post), 12–20 UTC, and on weekdays (0.26–0.42) vs weekends (0.13–0.26) **[OBS]**. Roll is a crude estimator; part of the spread-proxy variation may be estimator noise **[PROX]**.
- Net by month, 2023-04…2024-12 (K1/K2/K3/K4 means): K1 −1.39…−1.98, K2 −9.30…−9.90, K3 −6.94…−7.54, K4 −19.30…−19.90; **no month, hour, weekday or state bin has positive net under any model** (see `m2_by_*.csv`).
- Variance of period net under K2 (22 post-break months / 94 weeks, `m2_variance_decomposition.csv`): gross₀ 86 % / 92 % [CI 63–105 / 86–99], latency 12 % / 7 %, spread 2 % / 0.4 %, impact 0 %. **Variation of net is gross-driven (plus the part of it that latency slippage removes); variable fee-side cost is ≲2 %.** (Including the pre-break months the spread share is 15 % — a tape-regime artefact.)

## 2. Does gross vary?
Per-trade gross has SD 12–17 bps around a mean of 0.3–0.4 bps, so any month has a ±0.3 bps CI. Monthly gross₅₀₀ (post-break) 0.12–0.71 (2024) and 0.10–0.45 (2025). Permutation tests of heterogeneity: months p = 0.39 (2023-post), 0.67 (2024); weekday, hour, rate/vol/size/burst terciles all non-significant after Holm; the exceptions are 2023 months (raw p = 0.003, Holm 0.057, driven by Jan–Mar 2023), and change-frequency in 2024 (raw 0.005, Holm 0.08, gross −0.13 vs +0.47 bps). Variation in gross is therefore **not distinguishable from noise except the 2023-03-22 break** (mafe1r). The state-dependence of *cost* (latency slip, spread) is real and measurable; that of *gross* is not.

## 3. Can profitable times be told in advance? — 2025 verdict
**Model (frozen before 2025).** State variables fixed in advance: rv₃₀₀, rate₃₀₀, chgfreq₃₀₀ (mafe1r definitions, 2023 tercile edges → 27 cells); primary B1 = cell means of gross and of variable cost fitted on 2023-03-22→12-31 (80,860 trades; cells < 200 trades → overall mean); secondary B0 (all 2023), R1 (ridge), B2 (B1 + 2024). Rule: trade iff predicted gross − (K + predicted variable cost) > 0. *Disclosure:* I had seen mafe1r's regime tables, so the choice of chgfreq and of excluding the pre-break era is not blind.

**Check on 2024 (not virgin).** The best cell predicts 1.78 bps gross (n = 500, SE 0.83), the best predicted net is **−0.32 bps even under the cheap K1** (K2 −8.26, K3 −5.89, K4 −18.26): the rules take **0 trades** in 2024. Trade-level correlation of predicted vs realised gross: 0.005 (B1), 0.008 (B0), −0.003 (R1). Weekly Spearman of predicted vs realised net (B1, out of sample, 53 weeks): +0.19 (one-sided p = 0.09).

**One-shot 2025 test (spot, B1 under K2).**

| gate item | result |
|---|---|
| ≥ 100 non-overlapping trades | **0 trades → FAIL** (all seven rules B1/B0/R1/B2 × K1–K4 took 0 trades; this was announced in amendment A1 before the run) |
| mean net/trade > 0, p < 0.05 | not evaluable (no trades) |
| **Primary gate** | **FAIL** |

What the rule would have been up against, take-all 2025 trades **[OBS/ASSUM]**: net/trade K1 −1.78 [−1.86, −1.70], K2 −9.69 [−9.77, −9.61], K3 −7.33, K4 −19.69 bps. Break-even round-trip cost = gross = 0.32 [0.24, 0.40] bps, i.e. K1 is 6.5×, K3 24×, K2 31× too high.

**Does the model rank periods?** 2025 weekly Spearman (53 weeks), predicted vs realised: B1 net −0.19 (one-sided p = 0.92), gross −0.21; B0 −0.07/−0.14; R1 −0.12/−0.11; B2 +0.10/+0.09 (p = 0.24/0.27); persistence (last week's gross) −0.21. Top-5 vs bottom-5 predicted-gross cells in 2025 (descriptive): gross 0.12 [−0.05, 0.30] vs 0.40 [0.33, 0.47]; difference −0.28 [−0.48, −0.08] — the ordering **reversed** (2024: +0.09 [−0.10, 0.28]). **No: nothing in this state set predicts which times are better, and out of sample it ranks the wrong way.** 2025 also left the fitted state space: 47.5 % of trades in the mid change-frequency tercile vs 7–14 % in the fit years.

## 4. Is 0056 durable in 2025?
Pre-registered test: lower 95 % CI of R5 gross/trade > 0 and the L==5 ladder non-decreasing in horizon. **Passed.**

| L==5 anchors (event horizon / 300 s) | 5 | 10 | 50 | 100 | 250 | 300 s | R5 replay gross/trade [95 % CI] |
|---|---:|---:|---:|---:|---:|---:|---|
| 2023 post-break (mafe1r) | 0.100 | 0.184 | 0.571 | 0.772 | 0.959 | 1.050 | 0.430 [0.35, 0.51] |
| 2024 | 0.083 | 0.154 | 0.495 | 0.687 | 0.881 | 0.943 | 0.422 [0.32, 0.52] |
| **2025** | 0.092 | 0.175 | 0.576 | 0.787 | 0.973 | 0.978 | **0.321 [0.24, 0.40]** |

The effect persisted (ladder CIs e.g. event 250: 0.97 [0.91, 1.01]); the replay gross is 0.10 bps below 2024 with overlapping CIs. Latency slippage is ≈ half of the zero-latency response (gross₀ 0.68 in 2025, of which 0.35 is lost in the 500 ms delay). **Futures sample (53 days/yr, secondary, [OBS]):** R5 gross₅₀₀ 0.09 [−0.05, 0.24] (2023), 0.06 [−0.26, 0.48] (2024), 0.50 [0.25, 0.76] (2025); spot on the same days 0.51 / 0.56 / 0.20. Futures K2 net −9.96 / −9.99 / −9.53, K1 −2.04 / −2.05 / −1.61: negative every year. The sample is too small (SE 0.12–0.25) to say whether futures and spot differ in gross; durability on the futures venue is **not established**, though it is not contradicted.

## 5. Open possibilities (listed, not tested beyond the by-products above)
**Observed in the data, cause unknown:**
1. Latency slippage doubled 2023→2024 (0.18→0.36 bps) and is stable in 2025; it halves on weekends and rises with volatility. *Test:* order-book/bookTicker + own timestamps; vary delay 0–2 s on the tape.
2. Futures vs spot gross differ in sign of the difference between years (2023–24 lower, 2025 higher). *Test:* all futures days, not every 7th.
3. 2025 state distribution shifted (price-change frequency much higher). *Test:* is it a tick-size-in-bps effect (tick/price fell 3.6×)? Compare with BTC-quoted-in-other-pair tapes.
4. The March-2023 break (mafe1r) — zero-fee end [INF]; pre-break gross ≈ 0.

**Speculation [SPEC]:**
- *Zero/low-fee pairs or tiers.* The take-all gross (0.32–0.43 bps) is the maximum round-trip cost that breaks even; only a ≈ 0.15 bps/side all-in cost could pay. Zero-fee promotional pairs (user's recollection, not verified here, e.g. BTC vs FDUSD) are the one class that could be tested: download that pair's aggTrades and replay with its actual spread. VIP/maker-rebate tiers need volume far beyond 0.001 BTC trades. *Data:* that pair's tape + fee-schedule history.
- *Use 0056 as execution timing for orders that must be traded anyway* (no extra round trip): value ≈ gross₀ 0.7 bps minus latency — needs the user's real order flow.
- *Funding-time (00/08/16 UTC) and exchange-event effects on futures;* BNB discounts (K4b 15 bps still 24× too high).
- *Passive entry (K3):* needs queue/fill data; the archive's adverse-selection 0.32–0.99 bps is itself as large as the gross.

## 6. Caveats
- Spread, impact are proxies; true spread/depth unknown. Fees (5/10 bps, VIP0) are assumed as of 2026-10-15, not re-verified, assumed constant 2023–25. The K2 fee is a futures fee applied to the spot tape; the futures sample is only a coarse check.
- The primary gate is a trivially failed gate (zero trades) because the cost level exceeds any state-conditional gross — the informative results are the break-even gap, the failed ranking and the durable gross.
- Corrections made in-flight (documented): the first weekday heterogeneity test was vacuous (within-day permutation of a day label) and was re-run at day level (`c1_m2_weekday.py`); the 2024-12-31 extra trade; schema fix in the futures table script. None touched a 2025 number.
- Exploratory p-values: 45 tests per scope; claims require Holm < 0.05.

Code `mafe1c/code/`, results `mafe1c/results/`, data (not in git) `/home/ubuntu/mafe-data/mafe1/`.
