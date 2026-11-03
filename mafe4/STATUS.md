# MAFE-4 STATUS (final for this stage)
- DONE: PREREG committed before outcomes; data downloaded (<=2024-12-31 only, checksums verified); engine; discovery run; controls; aggTrades check; exploration; REPORT.md, SUMMARY.md, docs/HYPOTHESES.md.
- RESULT: 0 survivors of 128 registered cells (64 primary + 64 F4). K=0, so the 2024 validation was NOT read. Holdout never downloaded or computed. UNSEAL_TOKEN_MAFE4 in /home/ubuntu/mafe-data.
- Re-run: `code/dl.py`, `code/build.py`, `code/run_events.py disc|lag1 1|cheat 0 cheat`, `code/discover.py`, `code/controls.py planted|lookahead|perm`, `code/aggcheck.py`, `code/explore*.py`, `code/f4_desc.py` (venv at /home/ubuntu/mafe-data/mafe4/venv).
- Open for the lead researcher: whether to pre-register a fresh single-rule test of the exploratory H1 vol-gate (docs/HYPOTHESES.md) on 2024 validation.
