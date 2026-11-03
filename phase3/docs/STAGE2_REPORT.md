# MAFE-3 Stage 2 report — machine-native pattern search + combined model (XAUUSD)

Pre-registration: `docs/STAGE2_PREREGISTRATION.md` (sha256 `4adad97f739c04645fbb4bdca431594ec96789b44c29a7b8af2331c56ba6b080`, verified at run time), features frozen in
`docs/STAGE2_FEATURES.md`. Data: HistData M1 BID, discovery 2010–2019 only. **The validation window (2020–2022) and the holdout (2023+) were not read in stage 2:
neither track produced a candidate that reached validation.** All numbers are bps per trade, non-overlapping episodes, cost = $0.35/oz round trip (robustness $0.50) + swap.

## Step 0 — oracle exclusion (discovery, all valid 5-minute grid points)

Oracle = mean over grid points of max(MFE long, MFE short) over the hold, in bps; kept if oracle ≥ 4 × (cost $0.35 + mean swap).

| H_min | oracle_bps | cost35_bps | mean_swap_bps | threshold_bps | ratio | decision |
|---|---|---|---|---|---|---|
| 5 | 5.497 | 2.639 | 0.007 | 10.584 | 2.078 | excluded |
| 15 | 9.905 | 2.639 | 0.021 | 10.639 | 3.724 | excluded |
| 30 | 14.309 | 2.639 | 0.039 | 10.711 | 5.343 | kept |
| 60 | 20.647 | 2.638 | 0.078 | 10.865 | 7.601 | kept |
| 240 | 42.141 | 2.638 | 0.355 | 11.973 | 14.078 | kept |

Kept horizons: **30, 60, 240 min**. H = 5 and 15 are excluded (15 min narrowly: ratio 3.72 < 4).

## Section 6 — gross information: Spearman IC per concept (discovery 2010–2019)

IC between the z-scored feature and the long gross forward return (pooled, 5-minute grid with overlapping horizons, so naive significance is meaningless; stability is judged by
the sign across the 10 calendar years). Strongest |IC| per concept and H (full table: `results/stage2/ic.csv`):

| H | concept | feature | ic | mean_year_ic | t_years | years_same_sign |
|---|---|---|---|---|---|---|
| 30 | Absorption | a_rej | -0.0372 | -0.0357 | -9.3152 | 10 |
| 30 | Compression | c_loc60 | -0.0425 | -0.0422 | -11.4270 | 10 |
| 30 | Displacement | d_maxb60 | -0.0286 | -0.0282 | -10.6701 | 10 |
| 30 | Location | l_pdc | -0.0265 | -0.0262 | -6.7153 | 10 |
| 30 | Reversal | r_fail | 0.0212 | 0.0129 | 7.3183 | 10 |
| 30 | Speed | s_60 | -0.0449 | -0.0445 | -10.5933 | 10 |
| 30 | Time | t_hcos | 0.0111 | 0.0100 | 2.2672 | 8 |
| 30 | USD | u_s60 | -0.0164 | -0.0166 | -3.5272 | 10 |
| 60 | Absorption | a_rej | -0.0371 | -0.0348 | -6.6849 | 10 |
| 60 | Compression | c_loc60 | -0.0378 | -0.0375 | -10.0629 | 10 |
| 60 | Displacement | d_maxb60 | -0.0319 | -0.0313 | -10.6235 | 10 |
| 60 | Location | l_pdc | -0.0267 | -0.0265 | -5.4130 | 10 |
| 60 | Reversal | r_fail | 0.0237 | 0.0123 | 3.8808 | 9 |
| 60 | Speed | s_60 | -0.0439 | -0.0433 | -9.2226 | 10 |
| 60 | Time | t_hcos | 0.0146 | 0.0131 | 2.4303 | 7 |
| 60 | USD | u_s60 | -0.0175 | -0.0176 | -3.0271 | 10 |
| 240 | Absorption | a_th | -0.0242 | -0.0094 | -1.4806 | 7 |
| 240 | Compression | c_loc60 | -0.0177 | -0.0168 | -3.2843 | 9 |
| 240 | Displacement | d_maxb60 | -0.0190 | -0.0186 | -4.4969 | 9 |
| 240 | Location | l_pdc | -0.0236 | -0.0235 | -2.9727 | 8 |
| 240 | Reversal | r_fail | 0.0170 | -0.0024 | -0.3654 | 5 |
| 240 | Speed | s_60 | -0.0207 | -0.0196 | -3.2479 | 9 |
| 240 | Time | t_hcos | 0.0245 | 0.0229 | 2.4816 | 8 |
| 240 | USD | u_s60 | -0.0043 | -0.0040 | -0.7421 | 4 |

Reading: the information is small (|IC| ≤ 0.045) but its sign is stable in all 10 years at 30–60 min, and it is dominated by *mean reversion* (negative IC for speed, displacement, location in the range, signed rejection). At 240 min ICs are smaller and
less stable. The time-of-day cosine reflects the intraday drift profile.

## Track A — mechanical search

Candidates: 2276 signal definitions (68 single-feature tails, 1936 cross-concept pair signals (484 pairs × 4 quintile-tail combinations), 272 session × feature) × 3 horizons × 2 directions = **13656**
(recorded in the commit before any evaluation). Thresholds were fitted on discovery-A (2010–2014) only.

| step | count |
|---|---:|
| candidates | 13656 |
| with n ≥ 100 non-overlapping episodes in A | 13604 |
| net($0.35) > 0 in A | 128 |
| smallest one-sided p | 0.0107 |
| BH q = 0.10 survivors (m_A) | 0 |
| after n ≥ 100, net($0.50) > 0, ≥ 30 days | 0 |
| B replication / collapse / validation | not run (no A-survivor) |

Ten most significant candidates in A (none survives BH; t-test p; note the repeated "C|1|·|hi20, d = −1, H = 240" pattern = short in the London session after a strong up-move, i.e. the same underlying 2010–2014 gold weakness):

| spec | H | d | n | gross | cost | swap | net35 | net50 | t | p | days |
|---|---|---|---|---|---|---|---|---|---|---|---|
| C|1|u_s60|hi20 | 240 | -1 | 1577 | 5.209 | 2.495 | 0.000 | 2.714 | 1.645 | 2.304 | 0.011 | 1265 |
| C|1|s_up60|hi20 | 240 | -1 | 1550 | 5.267 | 2.499 | 0.000 | 2.768 | 1.697 | 2.211 | 0.014 | 1229 |
| C|1|s_30|hi20 | 240 | -1 | 1810 | 4.997 | 2.500 | 0.000 | 2.497 | 1.426 | 2.160 | 0.015 | 1286 |
| C|1|u_s15|hi20 | 240 | -1 | 2019 | 4.628 | 2.498 | 0.000 | 2.131 | 1.060 | 1.986 | 0.024 | 1289 |
| C|1|r_v|hi20 | 240 | -1 | 1867 | 4.660 | 2.492 | 0.000 | 2.168 | 1.100 | 1.858 | 0.032 | 1288 |
| C|1|c_loc60|hi20 | 240 | -1 | 1751 | 4.643 | 2.497 | 0.000 | 2.146 | 1.076 | 1.850 | 0.032 | 1281 |
| C|1|s_up15|hi20 | 240 | -1 | 1946 | 4.407 | 2.504 | 0.000 | 1.904 | 0.831 | 1.640 | 0.051 | 1288 |
| C|1|d_maxb15|hi20 | 240 | -1 | 1800 | 4.220 | 2.494 | 0.000 | 1.727 | 0.658 | 1.617 | 0.053 | 1278 |
| C|1|a_tl|lo20 | 240 | -1 | 636 | 6.028 | 2.529 | 0.000 | 3.499 | 2.416 | 1.612 | 0.054 | 402 |
| C|1|l_pdl|lo20 | 240 | -1 | 640 | 6.056 | 2.488 | 0.000 | 3.568 | 2.501 | 1.566 | 0.059 | 437 |

Controls (`trackA_controls.json`): positive (planted feature = noisy realised 30 min return) n ≈ 20 600, gross +6.4 bps, net +3.9, p < 1e-200, pass = True;
negative (rows of the feature matrix permuted, the full 13656 candidates re-searched): mean gross 0.000 bps, mean net -2.67, BH survivors 0, pass = True.

## Track B — combined model (walk-forward 2013–2019, train on 2010…y−1, 1-day purge)

Pooled 2013–2019. Gate: n ≥ 200, net($0.35) > 0 and net($0.50) > 0, weekly-block-bootstrap one-sided p < 0.05/6 = 0.0083, ≥ 5 of 7 years positive.

| model | H | n | gross | cost | swap | net35 | net50 | t | p_boot | pos_years | days | pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ridge | 30 | 185 | 1.739 | 2.574 | 0.000 | -0.835 | -1.938 | -0.773 | 0.796 | 3 | 176 | False |
| lgbm | 30 | 2570 | 0.756 | 2.649 | 0.000 | -1.893 | -3.028 | -4.369 | 1.000 | 1 | 1056 | False |
| ridge | 60 | 1721 | 1.576 | 2.587 | 0.000 | -1.011 | -2.120 | -2.092 | 0.986 | 2 | 816 | False |
| lgbm | 60 | 7530 | 0.792 | 2.697 | 0.005 | -1.910 | -3.066 | -6.855 | 1.000 | 0 | 1696 | False |
| ridge | 240 | 6892 | 1.113 | 2.726 | 0.062 | -1.674 | -2.842 | -3.734 | 1.000 | 0 | 1902 | False |
| lgbm | 240 | 8308 | 0.876 | 2.735 | 0.168 | -2.027 | -3.199 | -4.939 | 1.000 | 0 | 1857 | False |

Per-year net($0.35) of the traded episodes:

| model | H | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 |
|---|---|---|---|---|---|---|---|---|
| lgbm | 30 | -0.43 | -3.11 | -4.45 | -2.90 | -3.45 | -1.95 | 0.66 |
| lgbm | 60 | -0.97 | -2.68 | -3.72 | -1.39 | -1.46 | -2.13 | -1.70 |
| lgbm | 240 | -1.44 | -2.40 | -3.19 | -0.45 | -2.14 | -2.74 | -1.86 |
| ridge | 30 | -0.89 | -3.28 | 0.70 | 3.05 | -2.99 | -0.24 | 4.97 |
| ridge | 60 | -0.61 | -1.51 | -1.51 | -2.02 | 0.19 | -3.24 | 0.24 |
| ridge | 240 | -2.35 | -1.31 | -1.23 | -1.66 | -1.75 | -1.54 | -1.72 |

Number of trades per year:

| model | H | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 |
|---|---|---|---|---|---|---|---|---|
| lgbm | 30 | 1045 | 606 | 229 | 222 | 161 | 199 | 108 |
| lgbm | 60 | 2151 | 1374 | 940 | 865 | 812 | 852 | 536 |
| lgbm | 240 | 1332 | 1265 | 1182 | 1163 | 1146 | 1135 | 1085 |
| ridge | 30 | 94 | 38 | 4 | 15 | 18 | 4 | 12 |
| ridge | 60 | 882 | 334 | 135 | 151 | 98 | 68 | 53 |
| ridge | 240 | 1243 | 1098 | 959 | 958 | 938 | 852 | 844 |

Mean out-of-sample correlation of the prediction with the realised H-return (all grid points, per year, averaged over 2013–2019):

| model | H | pred_corr |
|---|---|---|
| lgbm | 30 | 0.0160 |
| lgbm | 60 | 0.0189 |
| lgbm | 240 | 0.0175 |
| ridge | 30 | 0.0157 |
| ridge | 60 | 0.0180 |
| ridge | 240 | 0.0169 |

The models carry a small positive amount of information (corr ≈ 0.016–0.019) and the trades they select earn a positive **gross** edge of +0.8 to +1.7 bps, which is below the 2.6 bps cost. **No model × H passes (0 of 6).**
Controls (`trackB_controls.json`): planted feature (H = 60): ridge net +1.63, LightGBM net +2.14, pass = True; permuted inputs: nothing passes and nothing is significant, pass = True.

### Importances

LightGBM gain (normalised, mean over the 7 walk-forward fits), top 10 over the three horizons:

| feature | importance |
|---|---|
| c_loc60c | 0.0916 |
| a_th | 0.0777 |
| t_hcos | 0.0765 |
| t_hsin | 0.0686 |
| r_fail | 0.0660 |
| l_pdl | 0.0630 |
| a_tl | 0.0622 |
| l_pdh | 0.0491 |
| c_rng | 0.0468 |
| l_twap | 0.0468 |

By horizon (top 10, gain share): 
- H = 30: t_hsin 0.082, t_hcos 0.075, c_rng 0.055, l_pdl 0.055, a_th 0.055, c_loc60c 0.054, a_tl 0.050, r_fail 0.047, a_rej 0.045, l_pdh 0.040
- H = 60: c_loc60c 0.081, t_hsin 0.077, a_th 0.074, t_hcos 0.068, r_fail 0.064, l_pdl 0.064, a_tl 0.058, c_rng 0.055, l_twap 0.051, l_pdh 0.050
- H = 240: c_loc60c 0.140, a_th 0.104, t_hcos 0.087, r_fail 0.087, a_tl 0.079, l_pdl 0.071, l_pdh 0.057, l_twap 0.050, t_dow 0.050, t_hsin 0.047

Ridge (mean |standardised coefficient| over the 7 fits, bps per 1 sd), top 6:
- H = 30: s_5 1.11, s_acc 0.99, s_30 0.92, a_rej 0.83, a_tl 0.69, a_th 0.66
- H = 60: s_5 1.47, s_acc 1.41, s_30 1.31, a_rej 1.06, a_tl 0.93, a_th 0.83
- H = 240: s_acc 2.58, s_30 2.29, s_5 2.26, dow4 1.79, a_rej 1.76, t_hsin 1.52

The final 2010–2019 models (frozen, saved outside the repo; importances in `results/stage2/final_lgbm_importance_H*.csv`, `final_ridge_coef_H*.csv`) were fitted but **not applied to any later data**.
LightGBM spends its splits mostly on spiky range/touch/location features (c_loc60c, a_th, a_tl, l_pdl, l_pdh, r_fail) and on the time of day; ridge puts its weight on the short-term speed
contrast (s_5, s_acc, s_30), i.e. the same short-horizon mean reversion visible in the IC table.

## Validation and holdout

Not run. Track A had no discovery-A survivor; Track B had no model passing the discovery gate. Section 5 therefore leaves the holdout sealed. `phase3/results/stage2/` contains no validation output.

## Implementation decisions (all made before outcomes unless noted; conservative reading)

1. Features: see `STAGE2_FEATURES.md` (38 columns; ridge inputs = 45 after one-hot encoding of session and weekday). σ_k = per-minute rms of 1 m returns; "its 20th percentile" of the compression ratio = trailing 20 trading days, so it is causal; time features are not z-scored; sessions: 21–24 UTC belongs to none.
2. Grid: 5-minute grid points with a gold bar in the 6 minutes ending at t−2; entries/exits/weekend rule/swap through the stage-1 engine (`resolve`, `swap_bps`); the oracle uses BID highs/lows over [entry, entry+H).
3. Track A: both tails of each single feature (≤ p10, ≥ p90) and the quintile tails for pairs/context; direction is a separate candidate; BH on the t-test one-sided p of net($0.35) > 0 in A; the A gate also required ≥ 30 distinct days; for B and validation the p used would have been max(t-test, weekly block bootstrap) (conservative; never reached). Near-duplicate collapse: overlap = share of one candidate's episodes that intersect the other's, collapse if either direction exceeds 50 %.
4. Track B: ridge intercept unpenalised, inputs z-clipped at ±5 and missing → 0; LightGBM native API, `bagging_freq = 1` (needed to activate bagging), NaN native; the "expected swap" in the trading rule is the deterministic rollover charge of the planned hold; greedy non-overlap pooled across years; year positive = mean net($0.35) > 0 among years with ≥ 1 trade.
5. Bug fixes unrelated to outcomes: LightGBM's sklearn wrapper needed scikit-learn, so the native `lgb.train` API was used (before any real Track B run); the negative-control criterion of Track B was rewritten after the first control run (the first criterion mis-specified noise tolerance for n = 87 trades); the real discovery runs were executed once each.
