# MAFE-2 Discovery Report (2020-2023, BTCUSDT; ETHUSDT sign check)

Pre-registration sha256: `85f65b98645554055a0a435d7cd4e6f8f68405c18efc52fc84299f213c5a18a2` (matches the registered value).  
Code parent commit: `e18a93ed70123e81d1d5e36249850bbe396571d3`; sha256 of each code file is in `results/discovery/advancement.json`.  
Run time of the discovery script: 12.5 s (feature building plus 139 hypotheses on two symbols).  
Only data < 2024-01-01 was read, through `mafe2.data`. All 139 hypotheses are listed in `results/discovery/hypotheses.csv`; episode-level parquet files are in `/home/ubuntu/mafe-data/episodes/discovery/<SYMBOL>/<id>.parquet` (not in git).

All figures are bps, round trip cost C = 12 bps (primary) unless stated; funding actually settled while held is included in net.

## Headline

- Hypotheses: 139. BH (q = 0.10) survivors on net > 0 (one-sided t-test): **0**. Smallest one-sided p = 0.00342; BH threshold for rank 1 = 0.00072.
- Informational screen, mean gross != 0 (two-sided, BH q = 0.05): 18 hypotheses pass (not a gate; see list below).
- Gate (1) mode: **NEAR_MISS**. Candidates entering gates 2-4: 5; passing gates 2-4: 4; K cap = 10.
- Advanced to validation (4): `F4_L4h_H24h_R` (NEAR_MISS), `F6_top_H24h_R` (NEAR_MISS), `F6_glob_H24h_R` (NEAR_MISS), `F4_L1h_H24h_R` (NEAR_MISS).

## Per-family summary (best and worst cell by net t-statistic)

| Family | cells | BH net survivors | gross-screen survivors | mean net > 0 | best cell | n | gross | net12 | t | worst cell | n | gross | net12 | t |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| F1 | 18 | 0 | 0 | 2 | `F1_L4h_H24h_C` | 714 | 23.5 | 11.5 | 0.77 | `F1_L1h_H1h_C` | 2635 | -2.0 | -14.0 | -6.58 |
| F2 | 18 | 0 | 0 | 2 | `F2_L1h_H24h_C` | 1054 | 19.6 | 7.6 | 0.72 | `F2_L1h_H1h_R` | 4051 | -0.8 | -12.8 | -12.14 |
| F3 | 6 | 0 | 0 | 2 | `F3_H24h_R` | 312 | 49.5 | 43.7 | 2.16 | `F3_H1h_C` | 2284 | -3.2 | -15.5 | -9.23 |
| F4 | 18 | 0 | 8 | 5 | `F4_L4h_H24h_R` | 533 | 48.5 | 41.3 | 2.72 | `F4_L1h_H1h_C` | 3320 | -4.8 | -17.1 | -11.06 |
| F5 | 18 | 0 | 2 | 3 | `F5_L4h_H4h_C` | 1046 | 18.7 | 6.6 | 1.22 | `F5_L24h_H1h_R` | 1830 | -5.4 | -17.3 | -7.71 |
| F6 | 12 | 0 | 8 | 3 | `F6_top_H24h_R` | 329 | 57.3 | 49.4 | 2.39 | `F6_glob_H1h_C` | 3579 | -4.6 | -16.8 | -13.61 |
| F7 | 31 | 0 | 0 | 4 | `F7_dow2` | 209 | 42.1 | 26.2 | 0.99 | `F7_hod05` | 1461 | 0.5 | -11.5 | -7.37 |
| F8 | 18 | 0 | 0 | 2 | `F8_L4h_H24h_R` | 179 | 34.3 | 22.3 | 1.21 | `F8_L1h_H1h_R` | 791 | -1.7 | -13.7 | -7.52 |

## Top 15 hypotheses by net t-statistic

| id | n | gross | funding | net12 | net8 | median net12 | hit | t | p (1-sided t) | p (week bootstrap) | ETH n | ETH gross |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `F4_L4h_H24h_R` | 533 | 48.5 | 4.76 | 41.3 | 45.3 | 12.4 | 0.53 | 2.72 | 0.0034 | 0.0018 | 520 | 15.7 |
| `F6_top_H24h_R` | 329 | 57.3 | 4.16 | 49.4 | 53.4 | 8.1 | 0.52 | 2.39 | 0.0087 | 0.0036 | 127 | 20.8 |
| `F6_glob_H24h_R` | 432 | 52.7 | 2.70 | 43.4 | 47.4 | 10.1 | 0.52 | 2.34 | 0.0099 | 0.0049 | 221 | 27.6 |
| `F3_H24h_R` | 312 | 49.5 | 6.15 | 43.7 | 47.7 | 13.2 | 0.53 | 2.16 | 0.0157 | 0.0111 | 296 | -21.9 |
| `F4_L1h_H24h_R` | 651 | 37.6 | 4.24 | 29.8 | 33.8 | 17.2 | 0.54 | 2.12 | 0.0173 | 0.0059 | 630 | 14.7 |
| `F5_L4h_H4h_C` | 1046 | 18.7 | -0.12 | 6.6 | 10.6 | -3.7 | 0.48 | 1.22 | 0.1117 | 0.1232 | 661 | -0.7 |
| `F4_L4h_H4h_R` | 1500 | 16.3 | 1.08 | 5.4 | 9.4 | -6.2 | 0.47 | 1.22 | 0.1117 | 0.0847 | 1467 | 2.5 |
| `F8_L4h_H24h_R` | 179 | 34.3 | -0.04 | 22.3 | 26.3 | -14.7 | 0.45 | 1.21 | 0.1134 | 0.1448 | 173 | 31.5 |
| `F7_dow2` | 209 | 42.1 | -3.94 | 26.2 | 30.2 | 11.3 | 0.52 | 0.99 | 0.1606 | 0.1571 | 209 | 46.5 |
| `F4_L24h_H24h_R` | 379 | 23.8 | 4.78 | 16.5 | 20.5 | 5.6 | 0.51 | 0.90 | 0.1831 | 0.1603 | 385 | 27.1 |
| `F1_L4h_H24h_C` | 714 | 23.5 | -0.05 | 11.5 | 15.5 | -30.4 | 0.45 | 0.77 | 0.2198 | 0.1851 | 731 | 36.2 |
| `F5_L24h_H24h_C` | 386 | 26.4 | 0.24 | 14.6 | 18.6 | -4.7 | 0.49 | 0.75 | 0.2254 | 0.2287 | 227 | -12.3 |
| `F2_L1h_H24h_C` | 1054 | 19.6 | 0.04 | 7.6 | 11.6 | -18.7 | 0.45 | 0.72 | 0.2353 | 0.2427 | 1038 | 7.1 |
| `F4_L1h_H4h_R` | 1814 | 13.9 | 0.83 | 2.8 | 6.8 | -7.9 | 0.46 | 0.68 | 0.2481 | 0.2115 | 1760 | 8.4 |
| `F2_L24h_H24h_C` | 508 | 22.2 | 0.65 | 10.8 | 14.8 | -6.1 | 0.48 | 0.63 | 0.2631 | 0.2457 | 530 | 19.7 |

## Advancement decision, gate by gate

Gate (1) was evaluated first: no hypothesis is BH-significant on net > 0 at q = 0.10, so the best 5 by net t-statistic with mean net > 0 form the `NEAR_MISS` candidate set. Gates (2) n >= 100, (3) mean net > 0 in >= 3 of the counted discovery years (F5/F6: 2020 counts only if it has >= 100 episodes; F8: >= 75 % of the 4 quarters of 2023), and (4) same sign of mean gross on ETHUSDT were then applied; ranking by net t-statistic, cap K = 10.

| id | t | mean net12 | p (1-sided) | p (bootstrap) | (1) candidate | (2) n >= 100 | (3) years | (4) ETH sign | advanced |
|---|---:|---:|---:|---:|---|---|---|---|---|
| `F4_L4h_H24h_R` | 2.72 | 41.3 | 0.0034 | 0.0018 | NEAR_MISS | pass (n=533) | pass (4/4 years (need 3)) | pass (BTC 48.5, ETH 15.7) | YES (NEAR_MISS) |
| `F6_top_H24h_R` | 2.39 | 49.4 | 0.0087 | 0.0036 | NEAR_MISS | pass (n=329) | pass (3/3 years (need 3)) | pass (BTC 57.3, ETH 20.8) | YES (NEAR_MISS) |
| `F6_glob_H24h_R` | 2.34 | 43.4 | 0.0099 | 0.0049 | NEAR_MISS | pass (n=432) | pass (3/3 years (need 3)) | pass (BTC 52.7, ETH 27.6) | YES (NEAR_MISS) |
| `F3_H24h_R` | 2.16 | 43.7 | 0.0157 | 0.0111 | NEAR_MISS | pass (n=312) | pass (4/4 years (need 3)) | FAIL (BTC 49.5, ETH -21.9) | no |
| `F4_L1h_H24h_R` | 2.12 | 29.8 | 0.0173 | 0.0059 | NEAR_MISS | pass (n=651) | pass (4/4 years (need 3)) | pass (BTC 37.6, ETH 14.7) | YES (NEAR_MISS) |

Per-year net12 (n) of the candidates:

| id | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|
| `F4_L4h_H24h_R` | 41 (103) | 24 (157) | 77 (138) | 25 (135) |
| `F6_top_H24h_R` | 39 (46) | 58 (136) | 231 (5) | 38 (142) |
| `F6_glob_H24h_R` | 72 (43) | 76 (143) | 7 (117) | 31 (129) |
| `F3_H24h_R` | 87 (63) | 27 (71) | 29 (86) | 41 (92) |
| `F4_L1h_H24h_R` | 33 (118) | 41 (183) | 34 (186) | 10 (164) |

Informational gross screen (mean gross != 0, BH q = 0.05) survivors: `F4_L1h_H1h_C` (gross -4.8, p 1.7e-03), `F4_L1h_H1h_R` (gross 4.8, p 1.7e-03), `F4_L1h_H4h_C` (gross -13.9, p 5.8e-04), `F4_L1h_H4h_R` (gross 13.9, p 5.8e-04), `F4_L4h_H24h_C` (gross -48.5, p 1.5e-03), `F4_L4h_H24h_R` (gross 48.5, p 1.5e-03), `F4_L4h_H4h_C` (gross -16.3, p 2.5e-04), `F4_L4h_H4h_R` (gross 16.3, p 2.5e-04), `F5_L4h_H4h_C` (gross 18.7, p 5.5e-04), `F5_L4h_H4h_R` (gross -18.7, p 5.5e-04), `F6_glob_H1h_C` (gross -4.6, p 1.8e-04), `F6_glob_H1h_R` (gross 4.6, p 1.8e-04), `F6_glob_H24h_C` (gross -52.7, p 4.8e-03), `F6_glob_H24h_R` (gross 52.7, p 4.8e-03), `F6_glob_H4h_C` (gross -11.9, p 2.9e-03), `F6_glob_H4h_R` (gross 11.9, p 2.9e-03), `F6_top_H24h_C` (gross -57.3, p 6.1e-03), `F6_top_H24h_R` (gross 57.3, p 6.1e-03).

## Validation of the code

Run with `python -m tests.run_checks` from `phase2/code` (output in `results/discovery/controls.json`). Overall: **PASS**.

1. Hypothesis count: 139 (expected 139): pass.
2. Lookahead test BTCUSDT: 40 random grid points; at each, every dataset was replaced by random garbage after the allowed cutoff (klines after t-2min open time, metrics/bookDepth after t-10min, funding after t) and all 17 features plus their z-scores recomputed: 720 feature checks, 0 mismatches (pass). Sensitivity (cut tightened by 15 minutes must change the feature): 617/617.
2. Lookahead test ETHUSDT: 40 random grid points; at each, every dataset was replaced by random garbage after the allowed cutoff (klines after t-2min open time, metrics/bookDepth after t-10min, funding after t) and all 17 features plus their z-scores recomputed: 720 feature checks, 0 mismatches (pass). Sensitivity (cut tightened by 15 minutes must change the feature): 599/599.
3. Positive control (deliberate cheat: future 1 h return as feature, continuation, H = 1 h; not among the 139 and not written to outputs): n = 2585, mean gross 166.2 bps, mean net12 154.3 bps: pass.
4. Negative controls (20 seeds each; pooled episodes; expected net = mean funding - 12):
   - `noise_H1h`: n = 81983, mean gross 0.10 +/- 0.26 (s.e.), mean funding 0.001, mean net12 -11.90.
   - `noise_H4h`: n = 60497, mean gross 0.39 +/- 0.59 (s.e.), mean funding 0.003, mean net12 -11.61.
   - `noise_H24h`: n = 21978, mean gross -1.04 +/- 2.40 (s.e.), mean funding -0.043, mean net12 -13.08.
   - `random_sign_at_F1_1h_fire_times_H1h`: n = 52700, mean gross 0.41 +/- 0.48 (s.e.), mean funding 0.006, mean net12 -11.58.
   Firing rate: real F1 L=1h 0.091; iid noise feature 0.134 (the iid feature fires at the Gaussian rate 13.4 %; the real feature fires less often because returns are fat-tailed). Result: pass.

## Implementation decisions (ambiguities resolved; conservative reading where possible)

- Signal rule follows the task clarification (previous 720 hourly grid points, >= 480 non-null, |z| >= 1.5), not the 30-day / 20-day wording of the pre-registration; the two agree in length (30 d = 720 h). Sample standard deviation (ddof = 1). A window with (numerically) zero variance gives no signal.
- Greedy non-overlap taken literally: after entering at t+1min with horizon H, the next admissible grid point is the first t' >= exit time, i.e. t + H + 1 h. For H = 1 h the signal can therefore trade at most every second hour (the grid point t+1h is before the exit at t+1h01).
- Episodes whose exit would fall at or after 2024-01-01 are dropped (a few at most per hypothesis, last days of December 2023).
- Return over L = ln(close of the last usable 1m bar / close of the usable bar L minutes earlier); the last usable bar is the one opening at t-2min. Taker-flow and premium windows are the L bars ending at that bar.
- Premium (F4) window must contain all L bars (any missing minute gives no signal). Premium gaps are the dates listed in the manifest; the strict rule drops windows touching them.
- Metrics (F5, F6): last row with create_time <= t-10min, and that row (and the comparison row L earlier for F5) may be at most 5 minutes (one sampling interval) older than its target time, otherwise no signal. A null value gives no signal.
- bookDepth (F8): snapshot imbalance = (notional at -1 % minus notional at +1 %) / sum; snapshots lacking either band are discarded; the feature is the mean over snapshots in (t-L-10min, t-10min], required to hold >= 80 % of the expected number (L / 30.5 s) and the last snapshot within 60 s of the window end. These two thresholds are my choices (the spec only says 'skip, never fill beyond one sampling interval').
- Funding feature: most recent funding row with calc_time <= t. Note some calc_time stamps carry a +2 ms offset (e.g. 00:00:00.002), so the rate for the 00:00 settlement becomes usable from the 01:00 grid point. Funding P&L uses events with time in (entry, exit].
- F7 direction = sign of the BTC discovery mean gross of the always-long episodes (ties to +1); the ETH check for F7 reuses the BTC direction. Day-of-week uses UTC, Monday = 0. Because direction is chosen in-sample, mean gross >= 0 by construction, so F7's gross screen is not informative.
- F7 p-value for net > 0: the standard one-sided t-test p (equal to the two-sided p halved when mean net > 0; for mean net <= 0 it is >= 0.5, so such cells can never be significant). The two-sided p is also in the CSV (`p_net12_2s`). A hypothesis counts as BH-significant only if mean net > 0 as well.
- Bootstrap: ISO-week blocks of the entry time resampled with replacement, 10,000 resamples, null-centred, one-sided p = (1 + #{boot mean - observed mean >= observed mean}) / (B + 1). Seed 12345.
- ETH F5/F6 signals are suppressed before 2022-01-01 (amendment notes); ETH F8 uses 2023 (its data start). ETH statistics are mean gross, mean net and n only.
- NEAR_MISS fallback is used only if no hypothesis is BH-significant (literal reading); the best 5 are taken before gates (2)-(4) are applied, as gate (1) is defined as the candidate set.
- Gate (3) counts a year with zero episodes as not positive; for F5/F6, 2020 (Sept-Dec) counts only if it has >= 100 episodes, otherwise 3 of 3 full years is required. Years/quarters are by entry time.

## Observations worth a second look (neutral)

- BTC `count_toptrader_long_short_ratio` is null for most of 2022 (Jan-Apr, Jul-Nov entirely; the Binance archive has a hole) and `count_long_short_ratio` is partly repeated/stale in Jan 2022. F6-top therefore has almost no 2022 signals (5 episodes at H = 24 h, 13 at 4 h, 27 at 1 h). `F6_top_H24h_R` is counted as positive in 2022 on those 5 episodes (net +231 bps), which is how it meets gate (3); on a more demanding reading (years with a minimum number of episodes) it would not. ETH top-ratio has the same hole.
- Every surviving near-miss is a 24 h reversal against the premium / positioning level (F4 premium over 1 h and 4 h; F6 top-trader and global ratios), i.e. one economic signal (extreme crowding / premium followed by reversal) seen through correlated features. They are not 4 independent confirmations. Their mean gross (38-57 bps) is larger than the 12 bps cost, and funding contributes about +2.7 to +4.8 bps because the reversal side is the side that receives funding.
- None of the 139 reach BH significance on net at q = 0.10; the best one-sided t-test p is 0.0034 against a rank-1 threshold of 0.00072. Of 139 one-sided tests about 14 would fall below 0.10 by chance alone; observed number with p < 0.10: 5, with p < 0.05: 5.
- Continuation and reversal cells of the same feature are exact mirrors in gross (same episodes, opposite sign), so the 18 gross-screen survivors are 9 distinct signals; net differs only through the 12 bps cost and the sign of funding.
- Most short-horizon (H = 1 h) cells are close to gross 0 (|gross| < 5 bps) and net about -12 bps, consistent with the negative controls.
- Among F4 and F6 reversal cells, only the H = 24 h ones reach t > 2 (n of 329-651); H = 4 h cells are about 0 to +5 bps net with t <= 1.2. Episode counts are modest and 2020-2021 vs 2022-2023 regimes are mixed; per-year numbers are in the CSV.
