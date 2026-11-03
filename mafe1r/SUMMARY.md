# MAFE-1R — plain-language summary

**What we did.** The original MAFE code and trade logs were lost. We re-downloaded the same two years of Binance BTC spot trades (2023–24; row counts match the archive exactly) and rebuilt the study's one promising signal: five same-direction trades in a row. Our rebuild reproduces the archive's price-response numbers almost exactly.

**What we found.**
- The signal is a small but real continuation effect: about 0.4 basis points (0.004 %) per trade over five minutes.
- Trading it costs 1 to 21 basis points depending on assumptions. In no month, quarter or year, under any assumed cost, did it make money.
- The "positive then negative" pattern is mostly noise plus one real event: on 22 March 2023 trading volume fell about 88 % (consistent with Binance ending zero-fee trading; inferred, not proven). Before that date the effect was about zero; afterwards it was stable through 2024.
- More trades did not explain the decline: the one-position-at-a-time rule holds the count near 290 a day.
- Market conditions (activity, volatility, time of day) showed no consistent effect once the March 2023 break was removed, though small samples leave this open.

**Answer.** MAFE did not fail because the phenomenon vanished, nor because it sometimes beat costs and sometimes did not. A small phenomenon existed but was always several times too small for the costs. We do not recommend further work on this signal as a trading strategy.

**Limits.** There is no order-book or spread data, so costs are assumptions, and the futures results could not be reproduced exactly.
