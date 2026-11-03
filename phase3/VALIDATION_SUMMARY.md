# MAFE-3 validation summary (2020–2022): **FAIL**

Only G2_dow_fri (long Friday, discovery direction) was validated; prereg hash verified, one read, no re-runs.

- n = 151; gross 3.88, cost 1.96, swap 1.17, **net +0.75 bps** (discovery: +6.93).
- t = 0.09; one-sided p = **0.463**; weekly block bootstrap p = 0.472.
- Net without swap: $0.20 → 2.75, $0.35 → 1.91, $0.60 → 0.51 bps.
- By year net: 2020 +2.81, 2021 −5.81, 2022 +5.15 (2 of 3 positive).
- Matched drift 1.52 (H) / 1.72 (24 h); gross − drift stays positive, so the drift gate passes.

Gate: p < 0.005 (K = 10) fails. The lenient K = 1 reading (p < 0.05, non-binding) also fails. Nothing advances; holdout stays sealed.
