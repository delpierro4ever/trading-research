# MAFE-3 Stage 3 report — frozen ridge M30 / M60, validation read (2020-01-01 → 2023-01-01)

Prereg sha256 354d2c17… (verified). Models trained once on 2010–2019 (hashes in `results/stage3/models.json`; identical to the stage-2 final ridge models).
Rule: c_t = $0.45 / entry price (bps); trade only if |pred| > c_t + expected swap; greedy non-overlap; weekend/swap as stage 1. One read, no variants.
`net60` / `net38` = net at $0.60 / $0.38 on the same trades (threshold fixed at $0.45). All figures bps; `price` = mean entry price, USD/oz.
Gate: weekly-block-bootstrap one-sided p < 0.025, net > 0 in ≥ 2 of 3 years (a year without trades does not count), ≥ 30 distinct days, n ≥ 100.

## Verdict
| model | n | gross | cost | swap | net $0.45 | p | years net>0 | days | gates p/years/days/n | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| M30 | 19 | 1.56 | 2.52 | 0.00 | -0.96 | 0.657 | 2 | 19 | False/True/False/False | FAIL |
| M60 | 140 | -2.70 | 2.49 | 0.00 | -5.18 | 0.944 | 0 | 128 | False/False/True/True | FAIL |

## Per-year table

| model | period | n | gross | cost | swap | net | net60 | net38 | long_share | price |
|---|---|---|---|---|---|---|---|---|---|---|
| M30 | ALL | 19 | 1.56 | 2.52 | 0.0 | -0.96 | -1.8 | -0.57 | 0.42 | 1796.23 |
| M30 | 2020 | 14 | 0.6 | 2.54 | 0.0 | -1.94 | -2.79 | -1.55 | 0.36 | 1783.48 |
| M30 | 2021 | 3 | 4.92 | 2.45 | 0.0 | 2.47 | 1.65 | 2.85 | 0.33 | 1839.34 |
| M30 | 2022 | 2 | 3.18 | 2.47 | 0.0 | 0.71 | -0.11 | 1.1 | 1.0 | 1820.81 |
| M60 | ALL | 140 | -2.7 | 2.49 | 0.0 | -5.18 | -6.01 | -4.8 | 0.64 | 1814.16 |
| M60 | 2020 | 54 | -6.18 | 2.51 | 0.0 | -8.7 | -9.54 | -8.31 | 0.46 | 1801.42 |
| M60 | 2021 | 47 | 0.02 | 2.48 | 0.0 | -2.46 | -3.29 | -2.08 | 0.77 | 1816.5 |
| M60 | 2022 | 39 | -1.13 | 2.47 | 0.0 | -3.6 | -4.42 | -3.21 | 0.72 | 1828.98 |

## Reading
- M30 trades rarely (n=19; the ≈2.5 bps hurdle exceeds nearly every prediction): fails n ≥ 100, days ≥ 30 and p.
- M60: n=140, gross -2.70 bps (negative in 2020, ≈0 in 2021–22), net negative in every year at all three cost levels, including the $0.38 spread-only level. The cost did fall (≈2.5 bps against ≈3.1 bps in 2017–19) but the gross edge did not hold: the pattern weakened, it is not only a cost effect.
- Correlation of prediction with the long gross return over the whole 2020–22 grid: M30 0.012, M60 0.009 (same sign as learned, small).
- Both models FAIL. Holdout untouched: no data ≥ 2023-01-01 read; MAFE3_UNSEAL and the token file never used.
