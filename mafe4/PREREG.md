# MAFE-4 PREREGISTRATION (written 2026-10-14, before any discovery outcome was computed)

Only data-availability checks and downloads had been done when this was committed. No return, event, or P&L has been computed.

## Data
Binance USD-M public archive (data.binance.vision), SHA-256 checksums verified at download.
Coins: BTC ETH SOL XRP DOGE BNB ADA AVAX LINK LTC (USDT). 1-min klines (monthly files), `metrics` (daily files: 5-min open interest, long/short ratios), `fundingRate` (monthly).
**liquidationSnapshot is NOT archived** (empty listing for monthly and daily) -> no direct liquidation data; forced flow is proxied by price/imbalance/OI-drop. Metrics only exist from 2020-09 (and later for some coins).
Only files dated <= 2024-12-31 are ever downloaded (code cap in `code/dl.py`). The holdout (2025-01-01 -> 2026-08-31) is never downloaded or touched. `UNSEAL_TOKEN_MAFE4` created.

## Partitions
Discovery 2020-07-01 -> 2023-12-31. Validation 2024 (one read, frozen candidates). Holdout sealed. A trade belongs to the partition of its *signal* minute and must also exit inside the partition (else dropped). Features (trailing windows) may use earlier data.
Code guard: the analysis script refuses to produce outcomes for signals >= 2024-01-01 unless run in validation mode with a frozen candidate file.

## Mechanics
Signal minute t (kline open time). Features use only klines up to and including t's close. Entry = open of minute t+1 (fill at open; slippage proxy below). Exit = open of minute t+1+H (fixed time), H in {15, 30, 60, 240}. Non-overlapping per coin *per cell*: an event is skipped if its entry is before the exit of the previous accepted event of that cell/coin. Events with any missing minute between signal-60 and exit are dropped. Side: against (fade) or with the move.
r = log(close/open) of a minute. sigma = std of r over the preceding 1440 minutes (excludes the signal minute; min 720 obs). imb = (2*taker_buy_base - volume)/volume. Signal needs sign(imb) = sign(r) (flow in the direction of the move).
Cost (ASSUMED, Binance USD-M VIP0, assumption date 2026-10-14): per side taker 5 bps + slip = max(1 bp, 10% of that minute's (high-low)/open in bps), applied to the entry minute and to the exit minute (symmetric choice). Round trip = 2*5 + slip_in + slip_out. Funding: if (entry_ts, exit_ts] contains a funding time, net -= side*rate*1e4 per crossing (actual rate; long pays positive rate). Reported gross, fees, slippage, funding separately. Sensitivity (report only): taker in, maker out 2 bps (no exit slippage). Stress: fees+slippage x 1.5 (funding unscaled). Headline = 1.0x.

## Registered cells (64 primary + 64 F4-conditional = 128 = BH family)
- F1 cascade fade: |r| >= z*sigma, z in {4,6,8}; |imb| >= q, q in {0.6,0.75}; OI condition: latest 5-min metrics stamp <= signal close vs the stamp 15 min earlier, OI change <= -0.5% (events on coin-days lacking metrics are EXCLUDED from F1/F2). Trade against. 3x2x4 H = 24 cells.
- F2 cascade continuation: same triggers, trade with the move. 24 cells.
- F3 exhaustion fade, no OI condition: window w in {5,15} min; cumulative r over the window / (sigma*sqrt(w)) >= zc in {3,4} (absolute value), window imbalance (volume-weighted) |imb_w| >= 0.25 with the same sign as the move; first qualifying minute triggers; trade against. 2x2x4 H = 16 cells.
- F4 conditional policy: one per F1-F3 cell (64). State variables (exactly three, causal at signal close): (a) vol regime = tercile of sigma(24h), per coin, edges from all minutes 2020-09..2022-12; (b) activity regime = signal-minute trade count / mean trade count of previous 1440 min, terciles with edges from the pooled set of all F1/F2/F3 events (any cell, dedup by coin-minute) in 2020-2022; (c) UTC hour bucket {0-8, 8-16, 16-24}. 27 bins. Binned-mean models of gross and of cost (1.0x) fit on 2020-2022 events of the cell; bins with n<10 use the cell mean. Policy: trade only in bins where predicted gross - predicted cost > 0. Evaluated on 2023 events only (out-of-sample inside discovery). Funding level, weekday, coin rank are descriptive only (not in the model).
Pooled cells = all 10 coins.

## Statistics
Per cell: mean net bps, bootstrap over coin-day clusters (B=4000, seed 20261014); one-sided p = P*(mean* <= 0) with +1 smoothing; 95% CI percentile. BH q=0.10 across all 128 cells.
Primary pass to validation: BH-significant AND net>0 in >= 3 of 4 calendar-year buckets (2020H2, 2021, 2022, 2023; a bucket with no events counts as not positive) AND net>0 on >= 6 of 10 coins (a coin with no events counts as not positive) AND >= 100 events.
F4 pass: BH-significant on 2023 policy-selected events AND >= 60 selected events AND net>0 in >= 3 of 4 quarters of 2023. (Looser event minimum because only one year is available; this is declared now.) Frozen artefact = bin edges + selected bins from the 2020-2022 fit.
Also reported: gross, cost parts, event counts per year, maker-exit and 1.5x columns, an oracle ceiling (mean max favourable excursion over the hold, in bps; used only to flag horizons where ceiling < mean cost, never to rank), and the stop variant (stop at 2 x trailing ATR60 = mean of the preceding 60 1-min (high-low), as a price distance from entry; checked on each minute bar from the entry minute; gap-through fills at open; stop fill pays the usual cost with that minute's range). The stop variant is a separate report, not in the BH family.

## Validation (2024, one read)
Frozen survivors only; K = number of survivors. Pass iff one-sided p < 0.05/K, mean net > 0 at 1.0x, and mean net >= 0 at 1.5x.

## Controls
(1) Planted signal: inject a known +20 bps reversal over 30 min after each F1(z=4,q=0.6) event in a copy of BTC prices; engine must recover ~20 bps gross and a tiny p. (2) Lookahead: delay the signal by +1 minute (entry t+2); a genuine causal edge may not improve (flag if improved by >1 SE); plus a positive control that cheats (entry at signal-minute open) which must look better, showing the engine can see leakage. (3) Permuted-direction null: random sign per event, seeded; mean gross ~0 and BH discoveries expected ~0.

## aggTrades check
Pre-declared sample: the 50 BTC days in discovery with the largest max single-minute |r|/sigma among minutes meeting F1 z>=4 & |imb|>=0.6 (OI condition ignored). For these day files we compare kline vs trade-level minute return, how concentrated the move is within the minute (largest 10-s share), and trade-level imbalance. Raw zips deleted after streaming conversion.

## Exploration (EXPLORATORY, never evidence, discovery data only)
Event-study paths -60..+240 by coin/size/direction/hour; clustering; BTC-led spillover into alts at minute lags; weekend vs weekday; funding-time effects. Written as hypothesis cards; none tested on validation.

## Deliverables / stop rule
REPORT.md (<=2000 words), SUMMARY.md (<=250 words), STATUS.md. Do not open the holdout, do not paper-trade.
