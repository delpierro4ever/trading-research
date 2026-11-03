# MAFE-3 (gold) final summary

**Commits:** ingestion `a576f4b`, discovery `bbfcc3d`. Prereg sha256 `5f503bf8…0a234` (Amendment 2) verified at runtime.

**Data:** HistData M1 BID, XAUUSD and EURUSD, 52 zips, 0 failures, +5 h to UTC (weekly open 22:00/23:00 UTC, close 21:59 UTC, confirmed). ~345–355k XAU bars/year, 2009-03 → 2026-09.

**Dukascopy spread vs $0.35** (only 2009-11 → 2011-04 exists locally): median/p95 $ = 2009 0.49/0.59; 2010 0.51/0.70; 2011 0.41/0.70. The 2010-era median spread alone exceeds $0.35; the assumption fits modern ECN spreads only. Net at $0.20/$0.60 is in the report.

**Controls:** count 89 ✔; lookahead 0 mismatches (5 cutoffs); positive control gross 12.4 bps (t=140); negative control gross 0.02, net −2.70 ≈ −cost−swap; swap and weekend-rule checks ✔. Independent recomputation of 8 hypotheses' sampled episodes matched exactly.

**Best per family** (id; n; gross/cost/net bps; t). Swap adds to cost where stated:
- G1 L4h_H24h_C; 1108; 5.5/2.65+3.0 swap/−0.2; −0.06
- G2 dow_fri; 510; 10.9/2.64+1.3/+6.9; 1.58
- G3 H9h_R; 2563; 0.45/2.64/−2.2; −1.56
- G4 H4h_R; 2512; 0.79/2.64/−1.8; −1.75
- G5 short; 120; 3.7/2.64/+1.1; 0.15
- G6 H24h_R; 260; 8.6/2.66+3.0/+3.0; 0.53
- G7 L24h_H24h_R; 565; 4.8/2.63+3.3/−1.2; −0.28
- G8 H24h_R; 170; 4.2/2.59+2.0/−0.4; −0.05

**BH survivors (q=0.10, net>0): 0.** Gate 1 fell back to NEAR_MISS (only five hypotheses have positive net). Informational gross BH (q=0.05): G2_hod10, G2_hod14, G7_L4h_H1h C/R; their gross is 1–2.4 bps, below the ~2.6 bps cost.

**Advanced (K=10): 1** — `G2_dow_fri` (NEAR_MISS): n=510, net +6.9 bps, raw one-sided p=0.058, 7/10 positive years, drift gate passed. Failed gate 3 (4–6 of 10 positive years): G2_dow_mon, G5_short, G6_H4h_R, G6_H24h_R. The other 84 failed gate 1.

**Suspicious / caveats:**
- G2_dow_fri is long-only in a gold bull decade, not BH-significant. Treat it as probable drift or noise.
- Dukascopy minute offsets are seconds, not ms (the task text said ms).
- HistData 2023 has ~13% fewer bars (holdout only).
- XAUUSD has a daily 1 h gap from 2014. HistData has duplicate hours (60 timestamps per year from 2019); the first was kept.
- Gate 4 requires both the H-matched and the 24 h drift.
