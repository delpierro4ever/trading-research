# TREND — summary for the user

**Question:** can slow trend following (buy what has been rising, sell what has been falling, across currencies, metals, indices and oil) earn money on a small IC Markets account?

**Answer: not demonstrated, and not with a USD 500 account.**

- I tested three classic, un-tuned systems on 2009–2022 data (the 2023–2026 period is sealed for the lead researcher). None passed the pre-set test on 2019–2022. Before costs the two best (S1 and S2) earned a small positive return in 2009–2018; after costs they earn about 0–3 % a year with 12–14 % volatility and drawdowns of 17–31 %.
- The cost that matters is **not** the spread (tiny: 0.2–0.4 % a year). It is the **overnight financing (swap)** on positions held for weeks: roughly 3–6 % a year of your equity. That removes most of the gross profit.
- Four validation years cannot separate a decent strategy from a useless one, so "failed" means "no evidence", not "proven worthless". Nothing in the robustness checks looked good.
- **Small account reality:** the smallest tradable position (e.g. 1 000 units of EURUSD ≈ USD 1 100; 1 oz of gold ≈ USD 4 100) is bigger than a USD 500 account's whole risk budget. At USD 500 the system either does nothing or becomes 1–3 concentrated currency bets (best case simulated: ~1.5 % a year, 12-month results from −14 % to +49 %, losing in more than half of the years). At USD 2 000 it starts to resemble the real thing; USD 10 000 follows it closely. Leverage is not the problem; lot size is.
- Nothing here should be traded live. I did not run the holdout, trade, or build a bot.

Files: `REPORT.md`, `PREREG.md`, `out/`, `holdout_test.py` (sealed; also refuses unless `TREND_RUN_FAILED=1`, since nothing passed).
