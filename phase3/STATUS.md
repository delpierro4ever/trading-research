# MAFE-3 STATUS
- Prereg sha256 = 5f503bf8... (Amendment 2 version) verified at runtime (recorded in results/discovery/advancement.json).
- [done] Part 1: HistData M1 BID XAUUSD+EURUSD, 52 zips, 0 failures; parquet; spread sanity; DATA_MANIFEST (commit a576f4b).
- [done] Part 2: discovery run (24 s). All controls pass; 89 hypotheses; BH(q=0.10) survivors 0; NEAR_MISS fallback; 1 advanced (G2_dow_fri). Independent spot-check of 8 hypotheses' episodes against raw bars: 0 mismatches.
- [running] commit discovery, write FINAL_SUMMARY.
- Notes: Dukascopy minute offsets are SECONDS (not ms). 2023 HistData files look incomplete (holdout, not used). No re-runs were needed.
- [done] Part 3: validation run (2020-2022), one read. G2_dow_fri FAILS (n=151, net +0.75 bps, t=0.09, one-sided p=0.463; 2 of 3 years positive; drift gate ok). Fails under K=10 and lenient K=1. Nothing advances; holdout (2023+) stays sealed. Discovery hypotheses.csv reproduces byte-identically after the window edits. See docs/VALIDATION_REPORT.md.
