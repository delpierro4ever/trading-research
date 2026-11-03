# MAFE-2 — Pre-registration (frozen before any outcome is computed)

Registered: 2026-10-14. Identity = sha256 of this file, recorded in the commit that adds it.
Any change after outcomes are computed must be a new, dated amendment section; nothing above it may change.

## Why MAFE-2 exists

MAFE (phase 1) found real BTC microstructure effects worth 0.1–1 bps against 2–21 bps round-trip cost,
and a clairvoyant bound that loses at ≤300 s. Cost is roughly fixed per trade while the size of price moves
grows with horizon, so phase 2 moves to **slower horizons (1 h, 4 h, 24 h)**. There, a typical move is tens to
hundreds of bps and a 12 bps round trip is no longer prohibitive by construction. Phase 2 also uses
**data classes phase 1 lacked**: funding, basis/premium, open interest, positioning ratios and order-book depth.

## Data

Binance USD-M perpetual futures, public archives (data.binance.vision), checksum-verified (see `DATA_MANIFEST.md`).
Primary instrument **BTCUSDT**; **ETHUSDT** is used only as a sign-replication check.
Datasets: 1 m klines (incl. taker-buy volume), settled funding rates, 1 m premium-index klines, 5 m metrics
(open interest, long/short ratios), bookDepth snapshots.

## Partitions (chronological; enforced in code by `mafe2.data`)

| Role | Interval | Rule |
| --- | --- | --- |
| Discovery | 2020-01-01 → 2024-01-01 (each family from its data's first date) | Free use, only for hypotheses registered here |
| Validation | 2024-01-01 → 2025-01-01 | One read, frozen definitions, only for advanced hypotheses |
| Holdout | 2025-01-01 → latest | Sealed by token; one read, only for validation survivors. **Never touched by MAFE phase 1.** |

Family F8 (bookDepth) and F5/F6 (metrics) start when their data does. If a family's discovery span is under
12 months, its discovery is that span and the gates below are applied per quarter instead of per year.

## Execution and cost convention (identical for every hypothesis)

- **Decision grid:** every full UTC hour. The features at decision time *t* use only data whose timestamp is
  ≤ *t* − 1 min for klines and ≤ *t* − 10 min for 5 m metrics/bookDepth, because their publication lag is unknown.
  Funding uses only rates already settled.
- **Entry:** open of the 1 m bar starting at *t* + 1 min. **Exit:** open of the bar at entry + *H*. No stops,
  no targets.
- **Overlap:** greedy and non-overlapping. While a position is open, later signals are ignored. Every statistic is
  computed on these independent episodes (the MAFE overlap lesson).
- **Cost (primary, used for every gate): C = 12 bps round trip** = 2 × (5 bps taker fee + 1 bps slippage).
  Funding actually settled while the position is held is added as P&L (sign-correct).
- **Secondary costs, reported only (never used for selection):** 8 bps (maker entry 2 + taker exit 5 + 1 slip),
  and the user's verified fee tier when supplied.
- **Gross** = direction × log(exit/entry) in bps. **Net** = gross + funding − C.

## Signal rule (all z-score families)

Feature *x_t* → *z_t* = (x_t − mean) / std over the trailing 30 days of grid points (causal; needs ≥ 20 days of
history). A trade fires when |z| ≥ 1.5, with direction = *d* · sign(z), where *d* = +1 is continuation and
*d* = −1 is reversal. **Both d are registered as separate hypotheses.**

Lookbacks L ∈ {1 h, 4 h, 24 h}. Horizons H ∈ {1 h, 4 h, 24 h}.

## Hypothesis families (per symbol)

| Family | Feature *x* | Grid | Count |
| --- | --- | --- | ---: |
| F1 Momentum | log return over L | L × H × d | 18 |
| F2 Taker-flow imbalance | Σ(2·taker_buy_vol − vol) / Σ vol over L | L × H × d | 18 |
| F3 Funding | last settled funding rate | H × d | 6 |
| F4 Premium / basis | mean premium-index close over L | L × H × d | 18 |
| F5 OI-confirmed move | (OI_value_t / OI_value_{t−L} − 1) · sign(return over L) | L × H × d | 18 |
| F6 Positioning | top-trader count L/S ratio; global account L/S ratio (levels) | 2 × H × d | 12 |
| F7 Seasonality | hour-of-day (H = 1 h, trade every day at that hour) and day-of-week (H = 24 h from 00:00) | 24 + 7 | 31 |
| F8 Book-depth imbalance | (bid − ask)/(bid + ask) depth within ±1 %, mean over L | L × H × d | 18 |
| | | **Total** | **139** |

F7 has no z-score. Its direction is fixed to the sign of the discovery-period mean, and its test is two-sided.

## Statistics

For each hypothesis on discovery: n episodes; mean gross; mean net; median net; hit rate. The test is a
one-sided t-test of **mean net > 0**, with a weekly block bootstrap (10 000 resamples) as a cross-check.
Benjamini–Hochberg runs at **q = 0.10** across all 139 BTCUSDT hypotheses. An informational screen of
**mean gross ≠ 0** (BH q = 0.05) is reported but is not a gate. Every hypothesis is reported, including the failures.

## Advancement gates

**Discovery → Validation.** All of the following must hold: (1) BH-significant on net > 0, or, if none are, the
best ≤ 5 by net t-statistic with mean net > 0 (labelled `NEAR_MISS`); (2) n ≥ 100 episodes; (3) mean net > 0 in
≥ 3 of 4 discovery years (or ≥ 75 % of quarters for short families); (4) same sign of mean gross on ETHUSDT
discovery. At most **K = 10** advance.

**Validation (2024) → Holdout.** Mean net > 0 at C = 12 with one-sided p < 0.05 / K, and the same gross sign on
ETHUSDT 2024.

**Holdout.** Mean net > 0 with one-sided p < 0.05. Only a holdout survivor may go to live paper trading. A
`NEAR_MISS` that passes validation is treated the same as any other.

## Explicitly out of scope for this registration

Multi-signal models and ML combinations. A separate registration (MAFE-2 stage 2) may be written after stage-1
discovery, using only discovery data. Other also out of scope: leverage and position sizing, stop/target exit
management (phase 1 showed hand-written managers destroyed value), other venues, and cTrader instruments
(a candidate stage 3).

## Data notes recorded before any outcome (2026-10-14, from DATA_MANIFEST.md)

- Metrics start 2020-09-01 (BTC) and 2021-12-01 (ETH). F5/F6 BTC discovery = 2020-09 → 2023-12; the year gate
  counts 2020 as a year only if it has ≥ 100 episodes, otherwise ≥ 3 of the 3 full years is required. The ETH
  sign check for F5/F6 uses 2022–2023.
- bookDepth starts 2023-01-01, so F8 discovery is 2023 only and uses the quarter gate. The ±1 % depth uses
  bands −1 (bid) and +1 (ask) of `notional`.
- Missing data (premium gaps, metrics holes): a grid point whose feature window lacks data is skipped, never
  filled forward beyond one sampling interval.

## Amendment 1 — 2026-10-14, after discovery outcomes, before any validation read

Written after reading `DISCOVERY_REPORT.md`. It may only **remove** candidates or **add** hypotheses with their
own correction, never loosen a gate. Validation data (2024) has not been read by any code at this point.

1. **Year-gate data sufficiency (tightening).** A discovery year counts toward gate (3) only if the hypothesis
   has ≥ 100 episodes in it. This is the same rule already applied to 2020 for F5/F6, now applied uniformly. Effect:
   `F6_top_H24h_R` had only 5 episodes in 2022 (`count_toptrader_long_short_ratio` is mostly null that year), so it
   has only 2 qualifying years and **is removed**. Advanced from stage 1: `F4_L4h_H24h_R`, `F6_glob_H24h_R`,
   `F4_L1h_H24h_R` (all `NEAR_MISS`; none survived BH on net).
2. **Stage-2 hypotheses (new, derived from discovery only).** In discovery, the profit of every advanced
   reversal cell comes mainly from its *long* side, i.e. buying when premium or crowd positioning is extremely
   negative. This holds on BTC and on ETH. On ETH the short side is negative. Registered as three new hypotheses with
   the identical feature, z-rule, H = 24 h and cost, but **trades taken only when direction = +1** (z ≤ −1.5):
   `S2_LONG_F4_L4h`, `S2_LONG_F6_glob`, `S2_LONG_F4_L1h`. Discovery figures for these are descriptive only.
   Stage-2 hypotheses must not be selected or tuned on 2024.
3. **Validation family size.** K = 6 (three stage-1 + three stage-2). The validation gate is one-sided
   p < 0.05/6 for mean net(12) > 0, plus the same gross sign on ETHUSDT 2024.
4. **Drift benchmark (reporting only).** Every long-biased result is reported next to the unconditional mean
   24 h return of a long entered at every grid hour in the same period, because a bull market inflates long-only
   results. This is not a gate.

## Amendment 2 — 2026-10-14, cross-asset test of the capitulation-long (stage 3)

Context: validation (2024) failed all six hypotheses. `S2_LONG_F4_L4h` came closest (BTC net12 +53.9 bps, n = 72,
p = 0.027). Its weakness is sample size, not effect size. Stage 3 tests the **same pre-defined rule on other
assets**, which no MAFE code has ever read. Written before any altcoin data is downloaded.

**Universe (mechanical, outcome-blind).** Binance USD-M USDT-margined perpetuals with a 1 m kline history that
starts on or before 2021-12-01. Excluded: BTCUSDT, ETHUSDT, and stablecoin bases (USDC, BUSD, TUSD, FDUSD, USDP,
DAI). Rank by total 2023 `quote_volume` and take the **top 25**. A symbol whose premiumIndexKlines or fundingRate
history is missing for more than 10 % of its window is replaced by the next in rank. Delisted symbols that meet
the rule are included (survivorship control).

**Window.** From 2022-01-01 (or listing + 30 days) to 2025-01-01. 2025+ stays sealed for every asset.

**Rule (identical to `S2_LONG_F4_L4h`).** Feature = mean premium-index close over the last 4 h. Causal 30-day z
on the hourly grid. Go long at z ≤ −1.5. Hold 24 h, entry at t + 1 min. Greedy non-overlap per symbol. Funding is
included.

**Cost.** Altcoins get **C = 16 bps** round trip (5 bps taker + 3 bps slippage per side). 12 bps is reported too.

**Single primary hypothesis `S3_LONG_F4_L4h_XS`. PASS iff all hold:**
(a) pooled mean net16 > 0 with one-sided p < 0.05, inference by **calendar-week block bootstrap of the pooled
    panel** (10 000 resamples; whole weeks resampled with every symbol's episodes, because capitulations are
    market-wide and simultaneous);
(b) pooled mean of (gross − matched drift) > 0, where matched drift = that symbol's mean 24 h gross of a long
    entered at every grid hour in the same calendar quarter (the signal must beat simply being long);
(c) breadth: mean net16 > 0 on ≥ 60 % of symbols with ≥ 10 episodes;
(d) pooled mean net16 > 0 in at least 2 of 2022, 2023, 2024.

Reported but not gates: per-symbol table, per-year, results excluding the top-3 contributing symbols,
equal-weight-per-week means, and the count of distinct calendar days.
**If stage 3 PASSES**, the next step is the one-time BTC holdout test of `S2_LONG_F4_L4h`
(2025-01-01 → latest, one-sided p < 0.05, K = 1), then live paper trading. **If it FAILS**, the capitulation-long
line is closed.
