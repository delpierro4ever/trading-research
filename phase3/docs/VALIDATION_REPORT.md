# MAFE-3 Validation report (2020-01-01 → 2023-01-01)

Pre-registration sha256 `5f503bf8…0a234` verified at runtime. One read, no variants, no re-runs, no crash fixes needed.
Runner: `code/mafe3/run_validation.py`. Outputs: `results/validation/{hypotheses.csv, verdict.json}`.

## Verdict: **FAIL** — G2_dow_fri does not validate. Nothing advances to the holdout.

## Setup
- Advanced hypotheses (from `results/discovery/advancement.json`): `G2_dow_fri` only (NEAR_MISS).
- Window: entries in [2020-01-01, 2023-01-01) with exit < 2023-01-01; warm-up bars from 2019-11-01. Data ≥ 2023-01-01 were never loaded;
  `UNSEAL_TOKEN_MAFE3` was never read and `MAFE3_UNSEAL` never set.
- Direction: the discovery direction (long, `g2_direction = +1`) was read from `results/discovery/hypotheses.csv`, not re-estimated.
- Cost: fixed $0.35/oz round trip at entry price, plus swap (2 bps per 17:00 NY rollover, ×3 Wednesday). Prices are BID (Amendment 2).
- Gate (conservative reading, binding): one-sided p < 0.05/K with K = 10 (p < 0.005) for mean net > 0, AND mean net > 0 in ≥ 2 of 3 years, AND drift gate (4).
  Lenient reading K = 1 (p < 0.05) is shown for information only and is **non-binding**.

## Code reuse and discovery reproducibility
The discovery modules are reused unchanged in behaviour. Two behaviour-preserving edits were needed so the dense market window is not hard-coded:
`market.py` reads the window (`O`, `END`, `D0`) from `MAFE3_WIN_START/WIN_END/PART_START` env vars (defaults = the discovery constants), and its rollover
table end date derives from `END`; `signals.py` derives the calendar base date from `O` instead of the literal 2009-11-01.
Proof: after the edits, `run_discovery` (output redirected via `MAFE3_TEST_OUT`) produced a `hypotheses.csv` that is **byte-identical** (`cmp`) to the
committed `results/discovery/hypotheses.csv`. The engine, statistics, gates and registry are untouched. The hypothesis-independent controls (count, positive, negative)
were re-run on the validation market and pass; the date-specific discovery controls (swap, weekend rule, look-ahead) were not repeated (they hard-code 2015 dates).

## Results: G2_dow_fri (long, enter Fri 00:01 UTC, exit at Friday close)

| Quantity | Validation | Discovery (ref.) |
| --- | ---: | ---: |
| n | 151 | 510 |
| mean gross (bps) | 3.88 | 10.86 |
| mean cost (bps) | 1.96 | 2.64 |
| mean swap (bps) | 1.17 | 1.29 |
| **mean net (bps)** | **0.75** | 6.93 |
| t (net) | 0.093 | 1.58 |
| one-sided p (net > 0) | **0.463** | 0.058 |
| weekly block bootstrap p | 0.472 | 0.056 |

Net at other costs, **no swap**: $0.20 → 2.75 bps; $0.35 → 1.91 bps; $0.60 → 0.51 bps.

| Year | n | gross | net |
| --- | ---: | ---: | ---: |
| 2020 | 50 | 5.92 | +2.81 |
| 2021 | 50 | −2.66 | −5.81 |
| 2022 | 51 | 8.28 | +5.15 |

Matched drift (long at every grid hour, same quarter): H-matched 1.52 bps, 24 h 1.72 bps. Gross − drift = 2.36 / 2.15 bps, same sign as gross, so gate (4) holds
(100 % of trades are long, so the gate applies).

## Gates

| Gate | Result |
| --- | --- |
| p < 0.005 (K = 10), mean net > 0 | **FAIL** (p = 0.463) |
| mean net > 0 in ≥ 2 of 3 years | pass (2 of 3: 2020, 2022) |
| drift gate (4) | pass |
| **Binding verdict** | **FAIL** |
| *Lenient K = 1, p < 0.05 (non-binding)* | *also fail (p = 0.463)* |

The result fails under either reading, so the K ambiguity does not matter. Net is barely positive (0.75 bps) and statistically indistinguishable from zero;
it was driven by 2020 and 2022, with 2021 clearly negative. The discovery gross (10.9 bps) shrank to 3.9 bps out of sample, consistent with a
NEAR_MISS selected from 89 hypotheses.
