# MAFE-3 discovery report (XAUUSD, 2010-01-01 .. 2020-01-01)

Pre-registration sha256 `5f503bf8636151b0e837d21586c018e21012a62be80d55c881fdb4643e40a234` (matches the frozen value). Code: `phase3/code/mafe3/`, parent commit `a576f4bf6b1fef7293f593a4ecb9cd6466760772`. All numbers below are in basis points (bps) per trade unless stated, from non-overlapping episodes, net of the primary cost convention (fixed $0.35/oz round trip converted at the entry price, Amendment 2, plus swap). Data: HistData.com 1-minute BID bars. Validation and holdout data were not read.

## Outcome

- Hypotheses evaluated: **89**. Gate-1 mode: **NEAR_MISS**.
- BH (q = 0.10) survivors on net > 0 (one-sided; G2 p doubled): **0**. Informational BH (q = 0.05) on gross != 0: **4**.
- Gate-1 candidates: 5; passing gates 2-4: 1; advanced to validation (K = 10): **1**.

| id | label | n | mean net | t | one-sided p |
|---|---|---:|---:|---:|---:|
| G2_dow_fri | NEAR_MISS | 510 | 6.93 | 1.58 | 0.0577 |

## Self-checks (controls.json)

- Hypothesis count: 89 (by family {'G1': 18, 'G2': 29, 'G3': 6, 'G4': 4, 'G5': 2, 'G6': 6, 'G7': 18, 'G8': 6}); pass = True. Controls are not part of the 89.
- Lookahead: bar values with label > t*-2 (bars whose close is after t*-1 min) replaced by random garbage at 5 random cutoffs; all log-returns, z-scores, breakout flags and every non-G2 candidate direction at decision times <= t* were identical (0 mismatches). Sensitivity: one extra bar of garbage changed the features at t* in 27/30 checks. pass = True.
- Positive control (feature = realised 1 h future return): n = 28435, mean gross 12.38 bps (t = 139.8), mean net 9.62 bps. pass = True.
- Negative control (random signs, 20 seeds, 1 h hold, ~9238 trades each): average gross 0.021 bps, share of seeds with |t| > 1.96 = 0.05, max |t| = 2.71; average cost 2.63 + swap 0.09 bps, average net -2.70 bps (= -cost -swap within noise). pass = True.
- Swap accounting: vectorised == brute force on 300 random holds, Tue->Thu 48 h hold = 8.0 bps (Tue 1 + Wed 3 rollovers x 2 bps); pass = True.
- Weekend rule (all minutes made available so only the rule can reject): Fri 20:30 UTC + 1 h hold accepted = False (must be False), Fri 19:00 + 1 h accepted = True, Mon 10:00 + 1 h accepted = True, waived weekend exit accepted = True.

## All 89 hypotheses

Columns: n episodes; mean gross, cost, swap, net (bps); t and one-sided p for net > 0 (G2 p shown raw; BH uses 2x); weekly block bootstrap p; net at a $0.20 and a $0.60 fixed round trip (+swap) and net without swap (primary = $0.35 + swap); positive years / eligible years (years with >= 10 episodes); share on one side.

| id | n | gross | cost | swap | net | t | p (1s) | p boot | net $0.20 | net $0.60 | net no swap | pos yrs | one-side | BH | gate-1 cand |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|---|
| G1_L1h_H1h_C | 4200 | -0.32 | 2.64 | 0.10 | -3.05 | -6.71 | 1.000 | 1.000 | -1.92 | -4.94 | -2.96 | 0/10 | 0.51 |  |  |
| G1_L1h_H1h_R | 4200 | 0.32 | 2.64 | 0.10 | -2.42 | -5.32 | 1.000 | 1.000 | -1.29 | -4.31 | -2.33 | 0/10 | 0.51 |  |  |
| G1_L1h_H4h_C | 3140 | -0.97 | 2.65 | 0.41 | -4.03 | -4.54 | 1.000 | 1.000 | -2.89 | -5.92 | -3.62 | 1/10 | 0.52 |  |  |
| G1_L1h_H4h_R | 3140 | 0.97 | 2.65 | 0.41 | -2.09 | -2.35 | 0.991 | 0.992 | -0.96 | -3.98 | -1.68 | 2/10 | 0.52 |  |  |
| G1_L1h_H24h_C | 1381 | 0.26 | 2.64 | 2.98 | -5.37 | -2.04 | 0.979 | 0.974 | -4.23 | -7.25 | -2.38 | 2/10 | 0.52 |  |  |
| G1_L1h_H24h_R | 1381 | -0.26 | 2.64 | 2.98 | -5.89 | -2.24 | 0.987 | 0.986 | -4.76 | -7.78 | -2.91 | 2/10 | 0.52 |  |  |
| G1_L4h_H1h_C | 3491 | -0.61 | 2.63 | 0.13 | -3.38 | -7.22 | 1.000 | 1.000 | -2.25 | -5.26 | -3.25 | 0/10 | 0.51 |  |  |
| G1_L4h_H1h_R | 3491 | 0.61 | 2.63 | 0.13 | -2.15 | -4.60 | 1.000 | 1.000 | -1.02 | -4.03 | -2.02 | 0/10 | 0.51 |  |  |
| G1_L4h_H4h_C | 2165 | -1.26 | 2.64 | 0.65 | -4.55 | -4.24 | 1.000 | 1.000 | -3.42 | -6.44 | -3.90 | 0/10 | 0.52 |  |  |
| G1_L4h_H4h_R | 2165 | 1.26 | 2.64 | 0.65 | -2.03 | -1.89 | 0.970 | 0.980 | -0.90 | -3.92 | -1.38 | 1/10 | 0.52 |  |  |
| G1_L4h_H24h_C | 1108 | 5.47 | 2.65 | 2.99 | -0.18 | -0.06 | 0.524 | 0.518 | 0.96 | -2.07 | 2.82 | 4/10 | 0.53 |  |  |
| G1_L4h_H24h_R | 1108 | -5.47 | 2.65 | 2.99 | -11.11 | -3.86 | 1.000 | 1.000 | -9.97 | -13.00 | -8.12 | 0/10 | 0.53 |  |  |
| G1_L24h_H1h_C | 3332 | -0.06 | 2.65 | 0.09 | -2.80 | -6.52 | 1.000 | 1.000 | -1.67 | -4.69 | -2.71 | 0/10 | 0.53 |  |  |
| G1_L24h_H1h_R | 3332 | 0.06 | 2.65 | 0.09 | -2.67 | -6.22 | 1.000 | 1.000 | -1.54 | -4.56 | -2.58 | 0/10 | 0.53 |  |  |
| G1_L24h_H4h_C | 1679 | 0.01 | 2.65 | 0.44 | -3.08 | -2.75 | 0.997 | 0.998 | -1.94 | -4.97 | -2.64 | 1/10 | 0.52 |  |  |
| G1_L24h_H4h_R | 1679 | -0.01 | 2.65 | 0.44 | -3.10 | -2.77 | 0.997 | 0.999 | -1.96 | -4.99 | -2.66 | 1/10 | 0.52 |  |  |
| G1_L24h_H24h_C | 537 | -1.92 | 2.65 | 3.17 | -7.75 | -1.99 | 0.976 | 0.980 | -6.61 | -9.64 | -4.58 | 3/10 | 0.51 |  |  |
| G1_L24h_H24h_R | 537 | 1.92 | 2.65 | 3.17 | -3.90 | -1.00 | 0.841 | 0.844 | -2.76 | -5.80 | -0.73 | 3/10 | 0.51 |  |  |
| G2_hod00 | 2567 | 0.46 | 2.64 | 0.00 | -2.17 | -8.38 | 1.000 | 1.000 | -1.04 | -4.06 | -2.17 | 0/10 | 1.00 |  |  |
| G2_hod01 | 2571 | 0.28 | 2.64 | 0.00 | -2.36 | -6.92 | 1.000 | 1.000 | -1.22 | -4.24 | -2.36 | 0/10 | 1.00 |  |  |
| G2_hod02 | 2575 | 0.63 | 2.64 | 0.00 | -2.01 | -5.75 | 1.000 | 1.000 | -0.88 | -3.90 | -2.01 | 1/10 | 1.00 |  |  |
| G2_hod03 | 2575 | 0.12 | 2.64 | 0.00 | -2.52 | -9.53 | 1.000 | 1.000 | -1.39 | -4.41 | -2.52 | 1/10 | 1.00 |  |  |
| G2_hod04 | 2576 | 0.11 | 2.64 | 0.00 | -2.53 | -11.03 | 1.000 | 1.000 | -1.40 | -4.42 | -2.53 | 0/10 | 1.00 |  |  |
| G2_hod05 | 2575 | 0.40 | 2.64 | 0.00 | -2.24 | -9.73 | 1.000 | 1.000 | -1.11 | -4.13 | -2.24 | 0/10 | 1.00 |  |  |
| G2_hod06 | 2575 | 0.42 | 2.64 | 0.00 | -2.22 | -7.44 | 1.000 | 1.000 | -1.09 | -4.10 | -2.22 | 0/10 | 1.00 |  |  |
| G2_hod07 | 2574 | 0.95 | 2.64 | 0.00 | -1.69 | -5.06 | 1.000 | 1.000 | -0.56 | -3.57 | -1.69 | 1/10 | 1.00 |  |  |
| G2_hod08 | 2578 | 0.17 | 2.64 | 0.00 | -2.47 | -6.05 | 1.000 | 1.000 | -1.34 | -4.36 | -2.47 | 1/10 | 1.00 |  |  |
| G2_hod09 | 2578 | 0.61 | 2.64 | 0.00 | -2.03 | -5.98 | 1.000 | 1.000 | -0.90 | -3.92 | -2.03 | 1/10 | 1.00 |  |  |
| G2_hod10 | 2576 | 1.12 | 2.64 | 0.00 | -1.52 | -4.64 | 1.000 | 1.000 | -0.39 | -3.40 | -1.52 | 3/10 | 1.00 |  |  |
| G2_hod11 | 2576 | 0.12 | 2.64 | 0.00 | -2.52 | -7.70 | 1.000 | 1.000 | -1.39 | -4.40 | -2.52 | 1/10 | 1.00 |  |  |
| G2_hod12 | 2580 | 0.56 | 2.64 | 0.00 | -2.08 | -5.47 | 1.000 | 1.000 | -0.94 | -3.96 | -2.08 | 0/10 | 1.00 |  |  |
| G2_hod13 | 2577 | 0.62 | 2.64 | 0.00 | -2.02 | -3.10 | 0.999 | 0.999 | -0.89 | -3.91 | -2.02 | 1/10 | 1.00 |  |  |
| G2_hod14 | 2577 | 2.44 | 2.64 | 0.00 | -0.20 | -0.33 | 0.628 | 0.631 | 0.93 | -2.08 | -0.20 | 4/10 | 1.00 |  |  |
| G2_hod15 | 2578 | 1.67 | 2.64 | 0.00 | -0.97 | -1.59 | 0.944 | 0.949 | 0.16 | -2.86 | -0.97 | 4/10 | 1.00 |  |  |
| G2_hod16 | 2578 | 0.63 | 2.64 | 0.00 | -2.01 | -4.22 | 1.000 | 1.000 | -0.88 | -3.90 | -2.01 | 0/10 | 1.00 |  |  |
| G2_hod17 | 2546 | 0.15 | 2.64 | 0.00 | -2.49 | -5.83 | 1.000 | 1.000 | -1.36 | -4.37 | -2.49 | 0/10 | 1.00 |  |  |
| G2_hod18 | 2510 | 0.32 | 2.64 | 0.00 | -2.32 | -5.62 | 1.000 | 1.000 | -1.19 | -4.20 | -2.32 | 0/10 | 1.00 |  |  |
| G2_hod19 | 2503 | 0.23 | 2.64 | 0.00 | -2.41 | -6.00 | 1.000 | 1.000 | -1.28 | -4.29 | -2.41 | 0/10 | 1.00 |  |  |
| G2_hod20 | 1989 | 0.30 | 2.64 | 1.99 | -4.33 | -11.60 | 1.000 | 1.000 | -3.20 | -6.22 | -2.34 | 0/10 | 1.00 |  |  |
| G2_hod21 | 837 | 1.07 | 2.48 | 1.03 | -2.44 | -5.74 | 1.000 | 1.000 | -1.38 | -4.21 | -1.41 | 0/5 | 1.00 |  |  |
| G2_hod22 | 818 | 0.02 | 2.47 | 0.00 | -2.45 | -8.23 | 1.000 | 1.000 | -1.39 | -4.21 | -2.45 | 0/5 | 1.00 |  |  |
| G2_hod23 | 73 | 0.25 | 2.55 | 0.00 | -2.29 | -2.34 | 0.989 | 0.994 | -1.20 | -4.11 | -2.29 | 0/5 | 1.00 |  |  |
| G2_dow_mon | 506 | 4.79 | 2.64 | 2.00 | 0.15 | 0.04 | 0.486 | 0.476 | 1.28 | -1.74 | 2.15 | 4/10 | 1.00 |  | Y |
| G2_dow_tue | 510 | 1.16 | 2.64 | 2.00 | -3.48 | -0.89 | 0.813 | 0.812 | -2.35 | -5.37 | -1.48 | 3/10 | 1.00 |  |  |
| G2_dow_wed | 513 | 2.07 | 2.64 | 6.00 | -6.56 | -1.58 | 0.943 | 0.944 | -5.43 | -8.45 | -0.56 | 4/10 | 1.00 |  |  |
| G2_dow_thu | 507 | 2.49 | 2.64 | 2.00 | -2.15 | -0.49 | 0.688 | 0.687 | -1.02 | -4.03 | -0.15 | 4/10 | 1.00 |  |  |
| G2_dow_fri | 510 | 10.86 | 2.64 | 1.29 | 6.93 | 1.58 | 0.058 | 0.056 | 8.06 | 5.04 | 8.22 | 7/10 | 1.00 |  | Y |
| G3_H1h_C | 2563 | 0.28 | 2.64 | 0.00 | -2.36 | -7.03 | 1.000 | 1.000 | -1.23 | -4.24 | -2.36 | 0/10 | 0.54 |  |  |
| G3_H1h_R | 2563 | -0.28 | 2.64 | 0.00 | -2.92 | -8.71 | 1.000 | 1.000 | -1.79 | -4.80 | -2.92 | 0/10 | 0.54 |  |  |
| G3_H4h_C | 2563 | 0.39 | 2.64 | 0.00 | -2.25 | -3.12 | 0.999 | 0.999 | -1.12 | -4.14 | -2.25 | 1/10 | 0.54 |  |  |
| G3_H4h_R | 2563 | -0.39 | 2.64 | 0.00 | -3.02 | -4.18 | 1.000 | 1.000 | -1.89 | -4.91 | -3.02 | 1/10 | 0.54 |  |  |
| G3_H9h_C | 2563 | -0.45 | 2.64 | 0.00 | -3.09 | -2.21 | 0.986 | 0.986 | -1.96 | -4.98 | -3.09 | 1/10 | 0.54 |  |  |
| G3_H9h_R | 2563 | 0.45 | 2.64 | 0.00 | -2.18 | -1.56 | 0.941 | 0.943 | -1.05 | -4.07 | -2.18 | 3/10 | 0.54 |  |  |
| G4_H1h_C | 2568 | 0.14 | 2.64 | 0.00 | -2.50 | -4.12 | 1.000 | 1.000 | -1.37 | -4.38 | -2.50 | 1/10 | 0.52 |  |  |
| G4_H1h_R | 2568 | -0.14 | 2.64 | 0.00 | -2.78 | -4.59 | 1.000 | 1.000 | -1.65 | -4.67 | -2.78 | 0/10 | 0.52 |  |  |
| G4_H4h_C | 2512 | -0.79 | 2.64 | 0.00 | -3.43 | -3.25 | 0.999 | 0.999 | -2.30 | -5.32 | -3.43 | 1/10 | 0.52 |  |  |
| G4_H4h_R | 2512 | 0.79 | 2.64 | 0.00 | -1.84 | -1.75 | 0.960 | 0.952 | -0.71 | -3.73 | -1.84 | 4/10 | 0.52 |  |  |
| G5_long | 120 | -3.72 | 2.64 | 0.00 | -6.36 | -0.86 | 0.804 | 0.805 | -5.23 | -8.25 | -6.36 | 5/10 | 1.00 |  |  |
| G5_short | 120 | 3.72 | 2.64 | 0.00 | 1.08 | 0.15 | 0.442 | 0.435 | 2.21 | -0.81 | 1.08 | 4/10 | 1.00 |  | Y |
| G6_H1h_C | 368 | -1.18 | 2.65 | 0.11 | -3.94 | -3.25 | 0.999 | 1.000 | -2.80 | -5.83 | -3.82 | 2/10 | 0.51 |  |  |
| G6_H1h_R | 368 | 1.18 | 2.65 | 0.11 | -1.58 | -1.30 | 0.903 | 0.910 | -0.45 | -3.47 | -1.47 | 4/10 | 0.51 |  |  |
| G6_H4h_C | 342 | -4.05 | 2.65 | 0.33 | -7.03 | -2.80 | 0.997 | 0.996 | -5.89 | -8.92 | -6.70 | 2/10 | 0.51 |  |  |
| G6_H4h_R | 342 | 4.05 | 2.65 | 0.33 | 1.07 | 0.42 | 0.336 | 0.330 | 2.20 | -0.83 | 1.39 | 6/10 | 0.51 |  | Y |
| G6_H24h_C | 260 | -8.59 | 2.66 | 2.95 | -14.20 | -2.55 | 0.994 | 0.993 | -13.06 | -16.10 | -11.25 | 2/10 | 0.50 |  |  |
| G6_H24h_R | 260 | 8.59 | 2.66 | 2.95 | 2.97 | 0.53 | 0.297 | 0.306 | 4.11 | 1.07 | 5.93 | 4/10 | 0.50 |  | Y |
| G7_L1h_H1h_C | 4758 | -0.94 | 2.63 | 0.09 | -3.66 | -10.08 | 1.000 | 1.000 | -2.53 | -5.54 | -3.57 | 0/10 | 0.51 |  |  |
| G7_L1h_H1h_R | 4758 | 0.94 | 2.63 | 0.09 | -1.78 | -4.89 | 1.000 | 1.000 | -0.65 | -3.65 | -1.69 | 1/10 | 0.51 |  |  |
| G7_L1h_H4h_C | 3486 | -0.82 | 2.63 | 0.33 | -3.78 | -4.77 | 1.000 | 1.000 | -2.66 | -5.66 | -3.45 | 0/10 | 0.51 |  |  |
| G7_L1h_H4h_R | 3486 | 0.82 | 2.63 | 0.33 | -2.14 | -2.70 | 0.997 | 0.997 | -1.02 | -4.02 | -1.81 | 1/10 | 0.51 |  |  |
| G7_L1h_H24h_C | 1464 | -0.64 | 2.64 | 2.97 | -6.25 | -2.54 | 0.994 | 0.992 | -5.12 | -8.14 | -3.28 | 2/10 | 0.51 |  |  |
| G7_L1h_H24h_R | 1464 | 0.64 | 2.64 | 2.97 | -4.96 | -2.02 | 0.978 | 0.972 | -3.83 | -6.85 | -1.99 | 3/10 | 0.51 |  |  |
| G7_L4h_H1h_C | 4008 | -1.22 | 2.62 | 0.11 | -3.95 | -10.04 | 1.000 | 1.000 | -2.83 | -5.83 | -3.84 | 0/10 | 0.51 |  |  |
| G7_L4h_H1h_R | 4008 | 1.22 | 2.62 | 0.11 | -1.52 | -3.84 | 1.000 | 1.000 | -0.39 | -3.39 | -1.40 | 1/10 | 0.51 |  |  |
| G7_L4h_H4h_C | 2523 | -1.20 | 2.63 | 0.57 | -4.40 | -4.45 | 1.000 | 1.000 | -3.27 | -6.28 | -3.83 | 0/10 | 0.50 |  |  |
| G7_L4h_H4h_R | 2523 | 1.20 | 2.63 | 0.57 | -2.00 | -2.02 | 0.978 | 0.985 | -0.87 | -3.87 | -1.43 | 2/10 | 0.50 |  |  |
| G7_L4h_H24h_C | 1219 | -3.26 | 2.63 | 2.93 | -8.82 | -3.30 | 0.999 | 1.000 | -7.69 | -10.70 | -5.89 | 0/10 | 0.50 |  |  |
| G7_L4h_H24h_R | 1219 | 3.26 | 2.63 | 2.93 | -2.30 | -0.86 | 0.804 | 0.808 | -1.17 | -4.17 | 0.63 | 4/10 | 0.50 |  |  |
| G7_L24h_H1h_C | 3333 | -0.49 | 2.63 | 0.11 | -3.23 | -8.07 | 1.000 | 1.000 | -2.10 | -5.11 | -3.12 | 0/10 | 0.52 |  |  |
| G7_L24h_H1h_R | 3333 | 0.49 | 2.63 | 0.11 | -2.25 | -5.59 | 1.000 | 1.000 | -1.12 | -4.12 | -2.13 | 0/10 | 0.52 |  |  |
| G7_L24h_H4h_C | 1726 | -0.25 | 2.63 | 0.44 | -3.32 | -2.98 | 0.999 | 0.999 | -2.19 | -5.20 | -2.88 | 1/10 | 0.51 |  |  |
| G7_L24h_H4h_R | 1726 | 0.25 | 2.63 | 0.44 | -2.82 | -2.54 | 0.994 | 0.994 | -1.69 | -4.70 | -2.39 | 3/10 | 0.51 |  |  |
| G7_L24h_H24h_C | 565 | -4.80 | 2.63 | 3.34 | -10.77 | -2.58 | 0.995 | 0.996 | -9.64 | -12.64 | -7.43 | 1/10 | 0.52 |  |  |
| G7_L24h_H24h_R | 565 | 4.80 | 2.63 | 3.34 | -1.16 | -0.28 | 0.609 | 0.606 | -0.04 | -3.04 | 2.17 | 5/10 | 0.52 |  |  |
| G8_H1h_C | 171 | 0.91 | 2.59 | 0.01 | -1.69 | -0.80 | 0.786 | 0.786 | -0.58 | -3.54 | -1.68 | 5/10 | 0.58 |  |  |
| G8_H1h_R | 171 | -0.91 | 2.59 | 0.01 | -3.52 | -1.65 | 0.950 | 0.954 | -2.41 | -5.37 | -3.50 | 1/10 | 0.58 |  |  |
| G8_H4h_C | 171 | 0.55 | 2.59 | 0.01 | -2.05 | -0.56 | 0.711 | 0.704 | -0.94 | -3.90 | -2.04 | 5/10 | 0.58 |  |  |
| G8_H4h_R | 171 | -0.55 | 2.59 | 0.01 | -3.16 | -0.86 | 0.804 | 0.808 | -2.05 | -5.01 | -3.14 | 5/10 | 0.58 |  |  |
| G8_H24h_C | 170 | -4.15 | 2.59 | 2.00 | -8.74 | -0.99 | 0.839 | 0.841 | -7.63 | -10.59 | -6.74 | 4/10 | 0.58 |  |  |
| G8_H24h_R | 170 | 4.15 | 2.59 | 2.00 | -0.44 | -0.05 | 0.520 | 0.527 | 0.67 | -2.29 | 1.56 | 4/10 | 0.58 |  |  |

## Best hypothesis per family (by net t)

| family | id | n | gross | cost | swap | net | t |
|---|---|---:|---:|---:|---:|---:|---:|
| G1 | G1_L4h_H24h_C | 1108 | 5.47 | 2.65 | 2.99 | -0.18 | -0.06 |
| G2 | G2_dow_fri | 510 | 10.86 | 2.64 | 1.29 | 6.93 | 1.58 |
| G3 | G3_H9h_R | 2563 | 0.45 | 2.64 | 0.00 | -2.18 | -1.56 |
| G4 | G4_H4h_R | 2512 | 0.79 | 2.64 | 0.00 | -1.84 | -1.75 |
| G5 | G5_short | 120 | 3.72 | 2.64 | 0.00 | 1.08 | 0.15 |
| G6 | G6_H24h_R | 260 | 8.59 | 2.66 | 2.95 | 2.97 | 0.53 |
| G7 | G7_L24h_H24h_R | 565 | 4.80 | 2.63 | 3.34 | -1.16 | -0.28 |
| G8 | G8_H24h_R | 170 | 4.15 | 2.59 | 2.00 | -0.44 | -0.05 |

## Gate-by-gate advancement

Gate 1: BH-significant on net > 0 or, when none, the best <= 5 by net t with mean net > 0 (`NEAR_MISS`). Gate 2: n >= 100. Gate 3: mean net > 0 in >= 7 of the 10 years (a year counts only with >= 10 episodes). Gate 4: if >= 70 % of trades are on one side, mean(gross - matched drift) must have the sign of the mean gross, for both the hold-matched drift and the literal 24 h drift.

| id | n | net | t | G1 cand | G2 n>=100 | G3 years | G3 detail | one-sided >=70% | G4 drift | advanced |
|---|---:|---:|---:|---|---|---|---|---|---|---|
| G2_dow_mon | 506 | 0.15 | 0.04 | Y | True | False | 4 positive of 10 eligible years | True | True | False |
| G2_dow_fri | 510 | 6.93 | 1.58 | Y | True | True | 7 positive of 10 eligible years | True | True | True |
| G5_short | 120 | 1.08 | 0.15 | Y | True | False | 4 positive of 10 eligible years | True | True | False |
| G6_H4h_R | 342 | 1.07 | 0.42 | Y | True | False | 6 positive of 10 eligible years | False | True | False |
| G6_H24h_R | 260 | 2.97 | 0.53 | Y | True | False | 4 positive of 10 eligible years | False | True | False |

Hypotheses not in the gate-1 candidate set failed gate 1 (not BH-significant and not among the best five by net t with positive mean net). For reference, the gate status of the ten hypotheses with the highest net t:

| id | n | net | t | p (1s) | G1 | G2 | G3 | G4 |
|---|---:|---:|---:|---:|---|---|---|---|
| G2_dow_fri | 510 | 6.93 | 1.58 | 0.058 | True | True | True | True |
| G6_H24h_R | 260 | 2.97 | 0.53 | 0.297 | True | True | False | True |
| G6_H4h_R | 342 | 1.07 | 0.42 | 0.336 | True | True | False | True |
| G5_short | 120 | 1.08 | 0.15 | 0.442 | True | True | False | True |
| G2_dow_mon | 506 | 0.15 | 0.04 | 0.486 | True | True | False | True |
| G8_H24h_R | 170 | -0.44 | -0.05 | 0.520 | False | True | False | True |
| G1_L4h_H24h_C | 1108 | -0.18 | -0.06 | 0.524 | False | True | False | True |
| G7_L24h_H24h_R | 565 | -1.16 | -0.28 | 0.609 | False | True | False | True |
| G2_hod14 | 2577 | -0.20 | -0.33 | 0.628 | False | True | False | True |
| G2_dow_thu | 507 | -2.15 | -0.49 | 0.688 | False | True | False | True |

## Implementation decisions and ambiguities

- **Data.** HistData.com ASCII M1 BID bars (EST without DST, +5 h to UTC); a bar is labelled by its open minute and its close is observed one minute later. Bars exist only for minutes with ticks; no zero-volume filtering is possible (volume is 0 in the files). Structurally invalid bars are dropped at ingestion (counts in DATA_MANIFEST.md). Features and z-scores may use bars from 2009-11-01 (warm-up for the 720-point history); no trade is entered before 2010-01-01 and every exit is before 2020-01-01 (episodes whose exit would be later cannot be formed).
- **Timing.** Decision time t uses only bars with close <= t-1 min, i.e. label <= t-2. Entry = open of the bar labelled t+1 (first available bar with label in [t+1, t+6], i.e. nearest-bar tolerance 5 min); exit = open of the first bar with label in [entry+H, entry+H+5 min] (H counted from the ACTUAL entry bar), else the episode is skipped and does not block the next one. Look-back closes use the last bar at or before the target label, accepted only if at most 5 min older; the bar at t-2 (or up to 5 min earlier) must exist.
- **Grid.** Full UTC hours t for which a bar exists in [t-7, t-2] and one in [t+1, t+6] (market open). The first hour after a weekend/holiday reopening is therefore usually not a grid point.
- **Non-overlap.** A decision at t is admissible when t >= the exit bar of the previous accepted episode.
- **Weekend rule.** An episode is skipped if the entry bar lies in the closure Fri 21:00 -> Sun 21:00 UTC, the exit-bar open (minus 1 min) lies in it, or entry and exit are in different weeks. Exempt: G2 Friday (exit at the open of the last bar of the trading week, i.e. the Friday close; waived) and G8 by construction. The closure is fixed at Fri 21:00 UTC all year as in the spec (the real winter close is 22:00 UTC, so Fri 21:00-22:00 winter trades are excluded: conservative).
- **Costs.** Gross from BID opens at entry and exit. Primary cost = $0.35 / entry bid open x 1e4 bps (fixed, Amendment 2); also $0.20 and $0.60 variants. Swap = 2 bps per 17:00 America/New_York rollover r with entry < r <= exit (instants of the bar opens), x3 for the Wednesday rollover, same for longs and shorts. Net = gross - cost - swap; "net without swap" = gross - cost.
- **z families (G1, G7).** x = ln of BID close (last bar label <= t-2) / BID close at t-1 min-L hours (last bar at or before, within 5 min) (gold for G1, EURUSD for G7); z over the previous 720 grid points (current excluded), >= 480 non-null, std ddof=1; |z| >= 1.5; d = +1 trades sign(z), d = -1 the opposite. G7 d = +1: gold follows EURUSD. A 24 h look-back that lands in a market closure gives no signal.
- **G2.** hod: decision at the full hour h (grid hours only), entry at h:01, H = 1 h. dow: entry 00:01 UTC of the weekday (day must have a bar within 5 min), Mon-Thu hold 24 h, Friday exit at the open of the last bar of the week. Direction = sign of the discovery mean gross (zero -> long). Because the direction is selected on the same data, the net p-value used for BH and the gates is min(1, 2 x one-sided p); the raw one-sided p is also reported.
- **G3.** x = sign of ln(close of the last bar closed by 06:59 / open of the first bar at/after 00:00) (bid); decision 07:00, entry 07:01; 9 h exits 16:01 UTC. Monday-Friday dates.
- **G4.** Anchor = 15:00 Europe/London (zoneinfo) Monday-Friday, in UTC; x = sign of the bid return between the close at anchor-61 min and the close at anchor-1 min (the 60 min before the anchor); entry anchor+1 min.
- **G5.** Last trading day of a month = last UTC date in the month with bars in >= 6 distinct hours and with bars near 00:01 UTC and near 16:00 Europe/London; entry 00:01 UTC, exit at the first bar at/after 16:00 Europe/London (15:00 or 16:00 UTC); long and short each registered.
- **G6.** Close of the last closed bar (label <= t-2) vs the max high / min low of the 1440 bar labels ending at t-3 (>= 200 bars present); d = +1 trades the breakout side. No z-score.
- **G8.** Closure = gap >= 36 h between consecutive bars, earlier bar on a Friday (UTC date), reopen bar on a Sunday or Monday; x = bid open of the first reopen bar / bid close of the last bar before the closure - 1; |x| >= 0.1 %; entry = first bar at/after reopen + 5 min; H counted from there.
- **Matched drift (gate 4).** Mean gross of a LONG held H at every grid hour of the same quarter (same execution rules, no non-overlap), averaged over the episodes' quarters and signed by their direction. Two versions: H = hypothesis median hold (rounded to whole hours) and the literal 24 h. The gate requires both to have the sign of the mean gross (conservative). Applied only to hypotheses with >= 70 % of trades on one side.
- **Gate 3.** "Positive years" is an absolute count >= 7; years with < 10 episodes are never counted as positive.
- **Bootstrap.** ISO-week block bootstrap (10 000 resamples, null-centred) from phase-2 code; reported, not used in a gate.
