# MAFE-1C summary (plain language)

**Question:** can we tell when the 0056 trade is expensive or profitable?

**Answer: no.** Trading costs hardly change over time. On Binance the fee is a fixed percentage (about 10 bps for a round trip on futures with the assumed public tier, 20 on spot). The parts that could vary with market conditions (spread, size impact) are measured at about 0.01–0.15 bps, under 2% of the fee. The one varying cost that is not negligible is the price move during our 0.5-second delay (0.2–0.4 bps), about as big as the signal itself.

**The signal is real but tiny.** In 2025 (read once, after everything was frozen) the 0056 effect persisted: about 0.32 bps gross per trade, in line with 2023–2024 (0.42–0.43). Costs are 2.1 bps (archive model) to 20 bps (spot): 6–60 times too big. No month, hour, weekday or market-state bucket was ever net positive.

**Prediction failed.** We built simple models on 2023 data. None predicted a profitable state even before 2025, so the rule made zero trades and the pre-registered 2025 test failed (it needs ≥100 trades). Weekly ranking of good vs bad periods was wrong-signed in 2025; the cells predicted best did worse than those predicted worst.

**Open ideas (untested):** a zero-fee pair or tier (break-even is ≈0.15 bps per side), using 0056 only to time orders you must place anyway, and checking the futures venue with all days instead of every 7th.

**Caveat:** spread and impact are proxies; fees are assumed.
