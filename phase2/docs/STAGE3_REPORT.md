# STAGE 3 REPORT — cross-asset test of the capitulation-long (Amendment 2)

Hypothesis `S3_LONG_F4_L4h_XS`. Run once (`code/mafe2/run_stage3.py`, runtime 9.4 s), no reruns, no variants. Binding spec: `docs/PREREGISTRATION.md` Amendment 2 (sha256 checked at runtime and recorded in `results/stage3/verdict.json`: `ced06b5e5b10c9b44f1609b088035e714cd5ee92bfc8ae7ef1c51aa37d844712`). Data read: 2021-11-01 up to but excluding 2025-01-01 only; holdout files were never opened and no unseal token was used.

## Verdict: FAIL (only gate b met; a, c, d not met)

| Gate | Requirement | Value | Result |
|---|---|---|---|
| (a) | pooled mean net16 > 0 and one-sided p < 0.05 (calendar-week block bootstrap, 10 000 resamples, percentile method) | mean net16 = -16.16 bps; p = 0.7298 | not met |
| (b) | pooled mean (gross - matched drift) > 0 | +15.79 bps | met |
| (c) | >= 60 % of symbols with >= 10 episodes have mean net16 > 0 | 8 of 25 = 32 % | not met |
| (d) | pooled mean net16 > 0 in >= 2 of 2022/2023/2024 | 1 of 3 (2022 -55.78, 2023 +33.79, 2024 -8.01) | not met |

The capitulation-long line is closed under the pre-registered rule.

## Regression check (BTCUSDT 2024, before any altcoin was run)

The exact validation path (`Pipeline` + `run_validation.episodes_for`, long side of `F4_L4h_H24h_R`) and the light path used for the altcoins (`Features.premium(g, 240)` + `zscore`, no metrics) both give n = 72, mean net12 = +53.892 bps, identical episode sets, and equal to the committed `results/validation/hypotheses.csv` row for `S2_LONG_F4_L4h` (n = 72, +53.892). The run asserts this and stops otherwise.

## Universe (outcome-blind; full ranking in `results/stage3/universe.csv`)

- All 1 056 USD-M symbol prefixes were listed from the data.binance.vision S3 index; 138 `*USDT` symbols had a monthly 1m kline file for 2021-12 or earlier and were not BTC/ETH/stablecoin-base. For these the 2023 monthly 1m klines were downloaded (sha256 verified, 0 rejects) and total 2023 `quote_volume` was the only statistic computed (`universe.csv` lists every ranked symbol with its volume). `universe.csv` was written by `stage3_ingest.py` before `run_stage3.py` was executed, i.e. before any return was computed.
- Candidates were taken in rank order and checked against the >10 % rule over their window (premium-index 1m slots missing; funding-rate time not covered beyond 1.5 funding intervals). Two failed: **TRBUSDT (rank 11)**, funding missing 14.8 % of its window; **TOMOUSDT (rank 26)**, premium index missing 20.6 % of its window (window ends 2024-05-28, its last kline). Final list (25) = ranks 1-25 except TRB, plus rank 27 AXSUSDT (rank 26 TOMO also failed): SOL, XRP, DOGE, BNB, LTC, MATIC, BCH, LINK, AVAX, ADA, FIL, 1000SHIB, DYDX, MASK, FTM, GALA, ETC, LINA, DOT, NEAR, EOS, CRV, SAND, ATOM, AXS (all `USDT`).
- MATICUSDT (rank 6) was delisted (last kline 2024-09-11 09:42 UTC); it is included with window end at its last data point (survivorship control per the spec).
- Window per symbol: max(2022-01-01, listing + 30 d) to 2025-01-01; every chosen symbol listed before 2021-12, so every window starts 2022-01-01.

## Implementation decisions

- Rule reused unchanged: `Features.premium(g, 240)` (mean premium-index close over the last 4 h, NaN if any of the 240 bars is missing), `features.zscore` (720-hour causal window, >= 480 valid), `z_direction` with d = -1 and long-only (z <= -1.5), `run_episodes` (entry open of the bar at t + 1 min, exit open 24 h later, greedy non-overlap by first grid hour >= exit, funding events in (entry, exit]), signals only from the window start, exit strictly before 2025-01-01. Shared modules were not edited; the time base was re-bound exactly as in `run_validation.py`.
- Cost: net16 = gross + funding - 16; net12 reported too. Funding is the per-symbol actual rate (some alts have only 8 h intervals in this window).
- Matched drift: per symbol, per calendar quarter (by entry grid hour), mean 24 h gross of a long entered at every grid hour from the symbol's window start (entry open t + 1 min, exit open +24 h, valid bars only, exit inside the loaded period). Excess = episode gross - drift of the episode's symbol-quarter. The drift pool includes the episode hours themselves.
- Bootstrap: percentile method. The pooled panel's episodes are grouped by ISO week of the entry time (157 weeks contain at least one episode); 157 weeks are resampled with replacement 10 000 times (seed 20241); each resampled mean is total net16 / total episodes; p = share of resampled means <= 0. Weeks without episodes are not in the resampling population (same convention as `stats.block_bootstrap_p`). The existing null-centred function from `stats.py` is reported for comparison only: p = 0.7563.
- Breadth gate uses all 25 symbols (each has >= 10 episodes). Year gate uses the calendar year of the entry time.
- Top-3 "contributing" symbols = three largest sums of net16 across their episodes (1000SHIBUSDT, CRVUSDT, DOGEUSDT).
- Ambiguity choices: coverage for the replacement rule is measured against the window up to the symbol's last kline (or 2025-01-01); data requests were always bounded with end <= 2025-01-01. The 25 final symbols' per-symbol coverage fractions are in `universe.csv`.

## Pooled results (n = 5 789 episodes, 25 symbols, 928 distinct entry days)

| Quantity | bps |
|---|---|
| mean gross | -3.43 |
| mean funding (long side, received positive) | +3.28 |
| mean net16 | -16.16 |
| mean net12 | -12.16 |
| mean matched drift (24 h long, same symbol-quarter) | -19.22 |
| mean excess (gross - drift) | +15.79 |

Inference: naive t (net16) = -2.02 (naive one-sided p = 0.978); bootstrap percentile p = 0.7298; bootstrap 95 % interval of the pooled mean net16 = [-67.7, +32.4] bps; null-centred bootstrap p = 0.756.

### Per year (entry year)

| Year | n | gross | net16 | net12 | excess |
|---|---|---|---|---|---|
| 2022 | 2 298 | -46.14 | -55.78 | -51.78 | +9.02 |
| 2023 | 1 498 | +46.33 | +33.79 | +37.79 | +30.54 |
| 2024 | 1 993 | +8.40 | -8.01 | -4.01 | +12.50 |

### Other reported diagnostics

- Excluding the top-3 contributing symbols (1000SHIB, CRV, DOGE): n = 5 077, mean net16 = -22.96 bps, bootstrap p = 0.8182.
- Equal-weight-per-week mean of weekly mean net16 (157 weeks): +35.51 bps. This differs in sign from the pooled episode mean (-16.16); weeks with many simultaneous entries (market-wide capitulations) have lower mean net16 and carry most of the episodes.
- Concentration: the 20 days with the most simultaneous entries (max 25 symbols entering on one day) hold 457 episodes = 7.9 % of all episodes; their mean net16 = -46.08 bps versus -13.59 bps on all other days. Those days: 2024-01-03/04/05/08, 2024-04-12/13/14/19/20/21, 2023-06-10/11, 2022-05-09, 2022-08-19/21, 2023-02-13, 2023-08-15, 2024-12-11/14/15.

### Per symbol (`results/stage3/symbols.csv`; bps)

| rank | symbol | n | gross | funding | net16 | matched drift | excess | hit rate (net16>0) |
|---|---|---|---|---|---|---|---|---|
| 1 | SOLUSDT | 215 | -23.3 | 13.3 | -25.9 | -13.6 | -9.7 | 0.460 |
| 2 | XRPUSDT | 241 | 31.7 | 0.5 | 16.2 | -0.1 | 31.8 | 0.531 |
| 3 | DOGEUSDT | 233 | 35.7 | -0.2 | 19.5 | 4.9 | 30.8 | 0.545 |
| 4 | BNBUSDT | 222 | 7.2 | 9.3 | 0.5 | 0.9 | 6.3 | 0.545 |
| 5 | LTCUSDT | 204 | 24.1 | -0.4 | 7.7 | -8.9 | 33.0 | 0.578 |
| 6 | MATICUSDT | 184 | 1.9 | 2.2 | -11.9 | -34.3 | 36.2 | 0.478 |
| 7 | BCHUSDT | 251 | 15.5 | 5.6 | 5.1 | -8.0 | 23.5 | 0.518 |
| 8 | LINKUSDT | 208 | 5.0 | -0.8 | -11.8 | -11.3 | 16.2 | 0.481 |
| 9 | AVAXUSDT | 224 | -62.9 | 2.7 | -76.2 | -21.5 | -41.4 | 0.464 |
| 10 | ADAUSDT | 232 | 12.8 | 0.9 | -2.3 | -13.7 | 26.5 | 0.491 |
| 12 | FILUSDT | 208 | 3.9 | 0.4 | -11.8 | -29.6 | 33.4 | 0.514 |
| 13 | 1000SHIBUSDT | 215 | 58.8 | 1.3 | 44.1 | -18.6 | 77.4 | 0.553 |
| 14 | DYDXUSDT | 255 | -25.9 | 1.1 | -40.8 | -29.5 | 3.6 | 0.471 |
| 15 | MASKUSDT | 229 | 7.8 | 2.5 | -5.6 | -33.4 | 41.2 | 0.476 |
| 16 | FTMUSDT | 226 | -18.9 | 0.5 | -34.4 | -15.0 | -3.9 | 0.509 |
| 17 | GALAUSDT | 252 | -24.8 | 1.8 | -38.9 | -29.6 | 4.8 | 0.484 |
| 18 | ETCUSDT | 224 | 21.0 | 2.1 | 7.1 | -8.5 | 29.5 | 0.500 |
| 19 | LINAUSDT | 267 | -32.4 | 8.2 | -40.3 | -40.8 | 8.3 | 0.524 |
| 20 | DOTUSDT | 220 | -16.0 | 4.1 | -27.9 | -23.0 | 7.0 | 0.505 |
| 21 | NEARUSDT | 234 | -16.1 | 2.5 | -29.6 | -18.5 | 2.3 | 0.500 |
| 22 | EOSUSDT | 273 | 1.8 | 0.1 | -14.1 | -23.3 | 25.1 | 0.480 |
| 23 | CRVUSDT | 264 | 46.6 | 3.5 | 34.1 | -32.8 | 79.4 | 0.545 |
| 24 | SANDUSDT | 225 | -20.1 | 1.2 | -34.8 | -27.2 | 7.1 | 0.493 |
| 25 | ATOMUSDT | 224 | -33.2 | 3.3 | -45.9 | -11.0 | -22.2 | 0.496 |
| 27 | AXSUSDT | 259 | -74.1 | 14.2 | -76.0 | -28.2 | -45.9 | 0.429 |

## Notes

- Mean matched drift is negative (-19.2 bps per 24 h) over 2022-2024 for this alt panel, so the positive excess in gate (b) is mostly that the signal avoids hours when the unconditional long loses, not that the signal itself earns after costs: mean gross is -3.4 bps.
- Per-symbol results are widely dispersed (net16 from -76 to +44 bps); eight symbols are positive.
- Funding contributes +3.3 bps on average (the signal enters when premiums are negative, i.e. funding tends to be paid to longs), concentrated in SOL, AXS, LINA, BNB.
- The data manifest has a stage-3 section (`docs/DATA_MANIFEST.md`): 0 checksum failures, premium-index gaps of up to 1 440 slots on 2022-10-02 / 2023-02-24 for several symbols, as in BTC/ETH.
- Per the pre-registration, a FAIL closes the capitulation-long line; the BTC 2025+ holdout test is not triggered.
