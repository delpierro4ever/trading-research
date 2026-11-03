# MAFE-2 Validation Report (2024, one read)

Pre-registration sha256 (checked at runtime): `355c93a3184f03de55b652c44004acba9630781ffcd75f4ad572ded0e0413055` (equals the expected value, includes Amendment 1; the file was not edited).
Code parent commit at run time: `1c47bf5` (code sha256 per file in `results/validation/verdict.json`). Script: `code/mafe2/run_validation.py`, run once (`python -m mafe2.run_validation run`, 2.7 s). No rerun was made.
Window: entries in [2024-01-01, 2025-01-01) with exit < 2025-01-01. Data were requested with `end <= 2025-01-01` only; the holdout guard, `UNSEAL_TOKEN` and `MAFE2_UNSEAL` were not touched. Episode-level parquet: `/home/ubuntu/mafe-data/episodes/validation/<SYMBOL>/<id>.parquet` (not in git).
All figures in bps; C = 12 bps round trip is primary (net12), net8 is secondary; funding settled while held is included in net.

## Hypotheses (K = 6) and gate

Stage 1 (identical to discovery): `F4_L4h_H24h_R`, `F6_glob_H24h_R`, `F4_L1h_H24h_R`. Stage 2 (Amendment 1): `S2_LONG_F4_L4h`, `S2_LONG_F6_glob`, `S2_LONG_F4_L1h` = same feature, z-rule (|z| >= 1.5, reversal), H = 24 h and cost, trades only when direction = +1 (z <= -1.5); non-overlap is applied to the long-only stream.
Gate: PASS iff one-sided t-test p (mean net12 > 0) < 0.05/6 = 0.008333 AND mean net12 > 0 AND ETH 2024 mean gross has the same sign as BTC (positive).

## Results, BTCUSDT 2024

| id | n | gross | funding | net12 | net8 | median net12 | hit | t | p (1-sided t) | p (week bootstrap) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `F4_L4h_H24h_R` | 152 | 11.91 | 2.03 | 1.94 | 5.94 | 0.68 | 0.500 | 0.095 | 0.4622 | 0.4620 |
| `F6_glob_H24h_R` | 116 | 34.15 | 1.91 | 24.06 | 28.06 | -22.44 | 0.466 | 0.932 | 0.1766 | 0.1563 |
| `F4_L1h_H24h_R` | 181 | -4.28 | 1.83 | -14.45 | -10.45 | -10.44 | 0.481 | -0.818 | 0.7928 | 0.7714 |
| `S2_LONG_F4_L4h` | 72 | 67.39 | -1.50 | 53.89 | 57.89 | 21.97 | 0.597 | 1.966 | 0.0266 | 0.0312 |
| `S2_LONG_F6_glob` | 31 | 63.30 | -2.13 | 49.17 | 53.17 | 26.28 | 0.516 | 1.453 | 0.0783 | 0.0121 |
| `S2_LONG_F4_L1h` | 93 | 35.08 | -1.48 | 21.59 | 25.59 | 30.41 | 0.548 | 0.989 | 0.1626 | 0.2090 |

Quarterly (entry quarter) n / mean net12, BTC:

| id | Q1 | Q2 | Q3 | Q4 |
|---|---|---|---|---|
| `F4_L4h_H24h_R` | 35 / -41.1 | 39 / -3.6 | 35 / 113.6 | 43 / -48.9 |
| `F6_glob_H24h_R` | 33 / 29.6 | 31 / -11.0 | 27 / 106.6 | 25 / -28.9 |
| `F4_L1h_H24h_R` | 44 / -31.4 | 44 / -39.4 | 45 / 48.7 | 48 / -35.2 |
| `S2_LONG_F4_L4h` | 12 / 45.1 | 24 / 26.9 | 23 / 141.0 | 13 / -42.3 |
| `S2_LONG_F6_glob` | 9 / 88.5 | 4 / -13.2 | 13 / 78.8 | 5 / -48.8 |
| `S2_LONG_F4_L1h` | 18 / 68.3 | 27 / -4.3 | 32 / 47.9 | 16 / -39.9 |

Long / short split, BTC (n, mean gross, mean net12) for stage-1 cells:

| id | long | short |
|---|---|---|
| `F4_L4h_H24h_R` | 72, 67.39, 53.89 | 80, -38.03, -44.82 |
| `F6_glob_H24h_R` | 31, 63.30, 49.17 | 85, 23.52, 14.89 |
| `F4_L1h_H24h_R` | 87, 35.27, 21.74 | 94, -40.88, -47.94 |

(The stage-2 cells are the long sides; for the first two the long-only episode set is identical to the long side of the stage-1 run, for `F4_L1h` it has 93 vs 87 episodes because skipped shorts no longer block later grid points.)

## ETHUSDT 2024 (sign replication)

| id | ETH n | ETH gross | ETH net12 | ETH t | ETH p (1-sided) | ETH long gross (n) | ETH short gross (n) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `F4_L4h_H24h_R` | 155 | -3.63 | -13.92 | -0.546 | 0.7071 | 49.92 (72) | -50.08 (83) |
| `F6_glob_H24h_R` | 126 | 47.31 | 37.54 | 1.117 | 0.1331 | 103.27 (46) | 15.13 (80) |
| `F4_L1h_H24h_R` | 182 | 1.88 | -8.37 | -0.349 | 0.6364 | 22.77 (89) | -18.11 (93) |
| `S2_LONG_F4_L4h` | 74 | 45.17 | 31.28 | 0.763 | 0.2240 | | |
| `S2_LONG_F6_glob` | 46 | 103.27 | 88.85 | 2.152 | 0.0184 | | |
| `S2_LONG_F4_L1h` | 93 | 33.84 | 20.03 | 0.513 | 0.3046 | | |

## Verdict

| id | p < 0.00833 | net12 > 0 | ETH gross same (positive) sign as BTC | verdict |
|---|---|---|---|---|
| `F4_L4h_H24h_R` | no (0.4622) | yes (1.94) | no (BTC 11.91, ETH -3.63) | **FAIL** |
| `F6_glob_H24h_R` | no (0.1766) | yes (24.06) | yes (34.15 / 47.31) | **FAIL** |
| `F4_L1h_H24h_R` | no (0.7928) | no (-14.45) | no (BTC -4.28, ETH 1.88) | **FAIL** |
| `S2_LONG_F4_L4h` | no (0.0266) | yes (53.89) | yes (67.39 / 45.17) | **FAIL** |
| `S2_LONG_F6_glob` | no (0.0783) | yes (49.17) | yes (63.30 / 103.27) | **FAIL** |
| `S2_LONG_F4_L1h` | no (0.1626) | yes (21.59) | yes (35.08 / 33.84) | **FAIL** |

No hypothesis passes; none advances to the sealed holdout. For reference, the best p (`S2_LONG_F4_L4h`, 0.0266) would not clear 0.05/6 and would also not clear 0.05/3.

## Drift benchmark (reporting only, not a gate)

Mean 24 h gross (bps) of a long entered at every grid hour (entry = open at t+1 min, exit = open 24 h later; overlapping, so only the mean is meaningful):

| Period | BTCUSDT | ETHUSDT |
|---|---:|---:|
| Validation 2024 (8,760 grid points) | 21.46 | 10.37 |
| Discovery 2020-2023 (35,040 grid points) | 12.14 | 19.62 |

Long-only 2024 mean gross against that benchmark (BTC): `S2_LONG_F4_L4h` 67.39 (excess 45.9), `S2_LONG_F6_glob` 63.30 (excess 41.8), `S2_LONG_F4_L1h` 35.08 (excess 13.6). ETH: 45.17 (excess 34.8), 103.27 (excess 92.9), 33.84 (excess 23.5).

## Stage-2 discovery stats (descriptive only; `results/validation/stage2_discovery_descriptive.csv`)

Computed on 2020-2023 before the validation read, with the discovery code and ETH F5/F6 suppression convention. They were not used for selection or tuning.

| id | symbol | n | gross | funding | net12 | net8 | median net12 | hit | t | p (1-sided) | p (bootstrap) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `S2_LONG_F4_L4h` | BTC | 238 | 82.96 | -0.49 | 70.46 | 74.46 | 16.27 | 0.563 | 2.76 | 0.0031 | 0.0015 |
| `S2_LONG_F6_glob` | BTC | 152 | 96.95 | -2.50 | 82.45 | 86.45 | 40.09 | 0.599 | 2.45 | 0.0077 | 0.0042 |
| `S2_LONG_F4_L1h` | BTC | 334 | 54.62 | -0.81 | 41.81 | 45.81 | 26.65 | 0.560 | 2.07 | 0.0197 | 0.0088 |
| `S2_LONG_F4_L4h` | ETH | 224 | 52.18 | -0.37 | 39.81 | 43.81 | 49.73 | 0.567 | 1.12 | 0.1313 | 0.1153 |
| `S2_LONG_F6_glob` | ETH | 91 | 68.10 | -1.48 | 54.62 | 58.62 | -8.62 | 0.473 | 1.13 | 0.1299 | 0.0762 |
| `S2_LONG_F4_L1h` | ETH | 312 | 44.91 | -0.91 | 32.00 | 36.00 | 44.30 | 0.567 | 1.13 | 0.1304 | 0.0910 |

Net12 by discovery year (BTC): `S2_LONG_F4_L4h` 146.9 / 50.2 / 69.6 / 58.2 (2020-23); `S2_LONG_F6_glob` 253.6 / 137.7 / -19.6 / 82.6; `S2_LONG_F4_L1h` 129.2 / 49.4 / 7.0 / 44.1. Drift benchmark in discovery: BTC 12.14, ETH 19.62.

## Implementation decisions

- **Shared code unchanged.** `features.py`, `engine.py`, `stats.py`, `pipeline.py`, `run_discovery.py` are byte-identical to the discovery commit. They hard-code the discovery time base (`NMIN`/`NGRID`, 2020-01-01..2024-01-01). `run_validation.py` re-binds those module globals at run time (`features.NMIN/NGRID`, `engine.NMIN/NGRID`, `pipeline.NGRID`) to the 2020-01-01..2025-01-01 base; T0 stays 2020-01-01, so grid indices are identical to discovery. `run_episodes` then drops episodes whose exit is >= 2025-01-01 (asserted).
- **Loader.** `features.load_market` has a hard-coded end of 2024-01-01 and a bookDepth step, so `load_market_validation` repeats its dataset/column loading with end = 2025-01-01 and without bookDepth (F8 is not among the six hypotheses). Data from 2020-2023 is loaded as the causal history for z-scores (a superset of the 2023 warm-up allowed); signals are zeroed outside 2024 grid points, so the greedy non-overlap starts fresh at 2024-01-01 and entries are only in 2024.
- **Gate details.** p is the one-sided t-test p of net12 (as in discovery); the weekly block bootstrap (10,000, seed 12345, ISO-week blocks of entry time) is reported as a cross-check and is not part of the gate. The sign condition is implemented as BTC gross > 0 and ETH gross > 0. ETH stage-1 and stage-2 use the same rule on ETH data (no ETH F6 signal suppression in 2024, i.e. `g_start = 0`; ETH metrics exist from 2021-12 and the 30-day z-history is available long before 2024).
- **Discovery reproduction check.** `python -m mafe2.run_validation repro` re-ran `run_discovery.main()` unchanged into a temporary directory (the pinned pre-registration hash `85f65b...` in `run_discovery.py` was re-bound to the current hash for this check only, because Amendment 1 changed the file). The resulting `hypotheses.csv` is byte-identical to the committed `results/discovery/hypotheses.csv` (sha256 `94483aa1666ebf52fb572359a6dc378194d2e7618e7fa551a019d5fd8632e084`), so all stage-1 rows are reproduced exactly. The stage-1 validation cells use the same functions and the same z-score and signal code.
- Drift benchmark uses exits strictly inside the loaded period (2024: 8,784 grid hours minus the last 24 whose exit would fall on 2025-01-01).

## Observations (neutral)

- The 2024 stage-1 results are far below discovery (e.g. `F4_L4h_H24h_R` gross 11.9 vs 48.5; net12 +1.9 vs +41.3). The long side of each reversal cell stays positive and the short side is negative in 2024 for `F4_L4h` and `F4_L1h`; for `F6_glob` both sides are positive.
- The long-only cells have positive mean gross in both symbols, but their BTC gross is partly the long-biased 2024 drift (21.5 bps per 24 h on BTC) and episode counts are small (31 to 93); none reaches the registered threshold.
- On BTC all six hypotheses have negative mean net12 in 2024 Q4 and positive mean net12 in Q3 (Q3 means 48.7 to 141.0), so a single quarter carries much of each sum.
- `S2_LONG_F6_glob` has only 31 BTC episodes (4 and 5 in Q2 and Q4); its bootstrap p (0.0121) and t-test p (0.0783) disagree, consistent with a small, skewed sample. ETH `S2_LONG_F6_glob` (46 episodes) has p = 0.0184 but ETH p is not a gate.
