# MAFE-1R STATUS — COMPLETE (awaiting review)
- M1 data: 731 spot daily archives downloaded, checksum-verified, converted to parquet (/home/ubuntu/mafe-data/mafe1, not in git); totals match ARCHIVE exactly. Futures aggTrades 2026-09-23/24 fetched; bookTicker not archived (404) -> spread PROXIED.
- M2 plan committed 475f306 before outcomes; reconstruction: L==5 reproduces ARCHIVE ladder; anchor counts within 0.01 %; futures replay checks in results/m2_futures_check.json.
- M3/M4: results/*.csv (code/m3_analyze.py, m5_*.py = post-hoc amendments A2-A5).
- M5: REPORT.md, SUMMARY.md written. STOPPED for review. Nothing pushed.
