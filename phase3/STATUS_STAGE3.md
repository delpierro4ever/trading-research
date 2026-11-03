# MAFE-3 Stage 3 STATUS
- Prereg sha256 verified = 354d2c17... (at start).
- [done] Step 1: M30/M60 trained on discovery; coefficients identical to stage-2 final ridge pickles. Committed before any 2020+ read.
- [done] Reproduction: stage-2 Track B ridge walk-forward re-run reproduces committed summary (3 rows) and walkforward (21 rows) exactly (max abs diff 0.0). results/stage3/repro.json.
- [done] Validation script written and dry-run on discovery data (smoke mode); no 2020+ data read yet.
- [done] Step 2: single validation read. Both M30 and M60 FAIL. Report: docs/STAGE3_REPORT.md. Holdout untouched.
