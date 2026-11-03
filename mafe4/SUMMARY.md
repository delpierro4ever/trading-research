# MAFE-4 summary (plain language)

We looked in two places in ten Binance crypto perpetuals (2020–2023): rare violent "forced selling/buying" spikes, and the 5–60 minute reversal after one-sided trading.

**Result: nothing survives costs.** Of 128 pre-registered tests (64 strategies plus 64 "trade only in favourable conditions" versions), none passed the rules. Fading a cascade does earn something before costs (about 12–24 bps), and exhaustion fades earn 1–10 bps. But one round trip costs about 16–20 bps (10 bps in fees plus 6–10 bps of slippage in fast markets), so the best realistic cell is about −2 bps, and the only positive cell is statistically indistinguishable from zero. Nothing passed, so the 2024 validation data was not read; the 2025–2026 holdout was never downloaded.

**Can we tell in advance when trading pays?** Cost is fairly predictable (it rises with volatility); the gross edge is not. One exploratory lead: in each coin's most volatile third of the time, the 4-hour fade looked much better (+30 to +50 bps net) in the discovery data. But it comes almost entirely from buying dips in an upward-drifting period and a few months, and was found after the fact. It needs its own pre-registered test before anyone relies on it.

Checks passed: a planted 20 bps signal was recovered exactly, a one-minute delay did not help, randomised directions found nothing, and minute data matched trade-level data. The public archive has no liquidation feed, so "forced flow" is inferred from price, order-flow imbalance and open-interest drops.
