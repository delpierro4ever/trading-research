# MAFE-3 Stage 2 summary (prereg sha256 4adad97f… verified)

**Commits:** features 40c5f64 · oracle 94a1865 · IC bb15e03 · Track A count 66f046c · Track A be46221 · Track B 02c6800 · report beb1c4e.

**Kept horizons** (oracle ÷ (cost+swap) ≥ 4): 5 min 2.1 ✗, 15 min 3.7 ✗, **30 min 5.3, 60 min 7.6, 240 min 14.1 ✓**.

**Top IC per concept** (30/60 min; sign stable 9–10 of 10 years): Speed s_60 −0.045; Compression c_loc60 −0.043; Absorption a_rej −0.037; Displacement d_maxb60 −0.03; Location l_pdc −0.027; Reversal r_fail +0.02; USD u_s60 −0.017; Time t_hcos +0.012. Small, mostly mean-reversion; weaker at 240 min.

**Track A:** 13 656 candidates → 13 604 with n ≥ 100 → 128 net>0 → **0 BH survivors** (min p 0.011: London short at 240 min, n 1 577, net +2.7/+1.6 bps at \$0.35/\$0.50). No B stage, no validation read.

**Track B** (walk-forward 2013–19, pooled; bps; net at \$0.35/\$0.50; bootstrap p; years positive):

| model H | n | gross | net | net50 | p | yrs+ |
|---|---|---|---|---|---|---|
| ridge 30 | 185 | 1.74 | −0.84 | −1.94 | 0.80 | 3/7 |
| LGBM 30 | 2570 | 0.76 | −1.89 | −3.03 | 1.0 | 1/7 |
| ridge 60 | 1721 | 1.58 | −1.01 | −2.12 | 0.99 | 2/7 |
| LGBM 60 | 7530 | 0.79 | −1.91 | −3.07 | 1.0 | 0/7 |
| ridge 240 | 6892 | 1.11 | −1.67 | −2.84 | 1.0 | 0/7 |
| LGBM 240 | 8308 | 0.88 | −2.03 | −3.20 | 1.0 | 0/7 |

0 of 6 pass; no validation read.

**Top 10 LightGBM features:** c_loc60c, a_th, t_hcos, t_hsin, r_fail, l_pdl, a_tl, l_pdh, c_rng, l_twap.

**Verdict:** a small, stable gross short-horizon reversal exists (≈ +1–2 bps per trade), below the ≈ 2.7 bps cost. Nothing survives discovery. 2020–2022 validation and 2023+ holdout were never read; no paper trading.

**Controls:** planted-signal and permuted-feature controls pass for both tracks; lookahead test 0 mismatches.

**Suspicious / caveats:** BID-only prices; best Track A candidates are one repeated pattern (likely 2010–14 gold weakness); LightGBM importance favours spiky count/location features and hour-of-day (possible volatility fitting); 38 features (45 after one-hot), not "≈45"; only crash/control-criterion fixes were re-run (see report).
