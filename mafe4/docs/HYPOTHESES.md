# Hypothesis cards (EXPLORATORY — discovery data 2020-07..2023-12 only; none tested on validation; none is evidence)

Source files are in `results/explore_*.csv`, `results/f4_descriptive_bins.csv`; plot `docs/explore_event_paths.png`.

**H1 — High-volatility gate on the 15-min exhaustion fade, 4 h hold (the most interesting lead).**
What: F3 (w=15, zc 3 or 4) at H=240, only when the coin's 24 h vol is in its own top tercile (edges frozen from 2020-09..2022-12 minutes). Descriptive discovery result: gross +56/+77 bps, cost 23/28, net +32/+47 bps (n=1389/647), positive in all four year buckets, 8/10 coins; low-vol tercile is reliably about -20 bps. Why it might be real: gross grows faster with vol than cost does (cost 15 -> 22-28 bps while gross -6 -> +77).
Why to doubt: (i) it is entirely "long after a down move" (+58/+90) while "short after an up move" loses (-39/-91): the top-vol regime had positive drift (+17..+26 bps per 240 min unconditional in 2020/2021), so this may be beta, not reversal; (ii) dropping the 3 best months cuts net to +17/+8; (iii) day-cluster CIs are about twice as wide (4.8..58; 1.3..90) and the month-cluster CI for z=4 includes 0; (iv) it was found after looking, so the p-values mean nothing. The pre-registered 27-bin F4 model did not find it (2023 had only 21/9 such events).
Next test: a new PREREG with one rule (long only, vol-top-tercile, w=15, H=240, BTC-hedged and unhedged), day-cluster inference, drift-matched control (same coin-minutes, random signal), run once on 2024 validation by the lead researcher.

**H2 — Long liquidations revert, short squeezes do not (and it decays).** Event paths (move-signed, + = continuation): down-cascades -8 bps at 15 min, -18 at 60, -29 at 240; up-cascades +2/+5/+2. By year at 60 min: 2021 -29, 2022 -2, 2023 +2. Hypothesis: the reversal pays for forced selling of over-levered longs and has been arbitraged or leverage has fallen. Test: split by funding level and OI level at signal; check whether the decay tracks open-interest/leverage.

**H3 — Only OI-confirmed events revert.** OI drop >=0.5 % events: -12 bps at 15 min, -13 at 30; events without an OI drop: ~0 throughout. Suggests the OI filter is separating forced flow from informed flow. Test: continuous OI-drop size as a dose-response variable. Caveat: OI exists for alts only from 2021-12.

**H4 — Laggard-alt catch-up after BTC cascades.** After BTC events, alts that had moved <1 sigma in the signal minute continue in BTC's direction: +6 bps at 5 min, +9 at 30 (n=1004) vs ~+1 for 1-3 sigma movers and a reversal for alts that already moved >3 sigma (-2 at 30). Gross is below the 16+ bps cost, so only interesting with maker entry or as a filter. Test: lead-lag at 1-minute resolution with beta-adjustment.

**H5 — Cost is predictable, gross barely is.** Out-of-sample (2023) correlation between binned predicted and realized cost 0.25-0.43; for gross -0.10..0.13. State variables therefore help avoid expensive times but do not by themselves find profitable ones; the only state that moved gross a lot was volatility (H1), which also raises cost. Test: model net directly with vol as the single variable (H1).

**H6 — Events are clustered across coins.** 57 % of events are followed by another (any coin) within 60 min; 23 % sit in bursts of >=3 coins within 10 min; the top 5 % of event days hold 24 % of events. Cross-coin dependence means effective sample sizes are far below event counts; portfolio-level or day-cluster inference is needed, and "first event of a burst" could be a cleaner trigger.

**H7 — The one-minute bar is late.** In the 50-day aggTrades sample (121 event minutes) the median event has 54 % of its path in its largest 10 s and 90 % of the move done at ~53 s; 37 % of the path is in the last 10 s. A trade-level trigger could enter earlier with the move still unfinished. Needs tick data (aggTrades) at scale; cost of that data work is high.
