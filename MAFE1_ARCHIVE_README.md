# MAFE — Market Microstructure Research Archive

**Status: Research concluded / archived — not promoted to live trading.**

MAFE (market-anchored feature/event research) was a governed research programme that
looked for short-horizon, causally observable market microstructure states in BTC trade
data, and tested whether any of them could pay for execution costs. This repository is
the closing technical archive. It holds documentation and small summary tables only. It
does not contain raw market data, private infrastructure, or runnable trading code.

The programme is closed. No replacement strategy is being developed from it.

## One-paragraph result

One directional state, **0056 (Terminal Same-Side Run)**, was discovered on 2023 data
and replicated strongly on a separate 2024 holdout. At every economic stage, though, the
effect was a fraction of the cost of trading it. On the historical tape its mean
direction-normalised response was 0.004–0.083 bps at event 5, and it failed a 1 bps
friction gate in both years. On live Binance USD-M futures, a fixed 300-second paper
implementation had positive gross P&L on two of three branches, but **net P&L was
negative on all three**. Fees were about 95% of costs. A rule-based Position Manager
made the primary branch worse. The conclusion is that **no executable edge was
demonstrated from this evidence**.

## Contents

| Path | Content |
| --- | --- |
| `README.md` | Overview, data, partitioning, 0056, results, conclusion |
| `docs/EVIDENCE.md` | Stage-by-stage evidence with the exact figures |
| `docs/LIMITATIONS.md` | What the data did not contain, and what was not proven |
| `results/summary.json` | Machine-readable summary of the headline numbers |

## Historical dataset

| Property | Value |
| --- | --- |
| Venue / instrument | Binance Spot, `BTCUSDT` |
| Source | Official Binance public daily aggregate-trade (`aggTrades`) archives, checksum-verified |
| Coverage | 2023-01-01 → 2024-12-31 UTC, 731 daily archives |
| Accepted rows | **1,304,019,054** aggregate trades (2023: 752,974,771 / 365 archives; 2024: 551,044,283 / 366 archives) |
| Compressed size | 17,717,147,907 bytes |
| Rejected / duplicate / within-archive gaps | 0 / 0 / 0 |
| Timestamp resolution | milliseconds |
| Row fields | aggregate id, price, quantity, first/last trade id, timestamp, buyer-is-maker, best-match |

The dataset is **trades only**. It did NOT contain historical full depth/order-book state,
observed spread, queue position, replenishment, or receive latency. See
`docs/LIMITATIONS.md`.

The dataset is not published here and is not redistributed. It can be re-obtained from
Binance's public data portal (`data.binance.vision`, spot / daily / aggTrades / BTCUSDT).

## Partitioning, and why

| Role | Interval | Access rule |
| --- | --- | --- |
| Phase A: discovery | `[2023-01-01, 2024-01-01)` | Opened only after the hypotheses were registered; expanding chronological inner folds with purge/embargo |
| Phase B: validation | `[2024-01-01, 2025-01-01)` | Sealed until every phenomenon definition was frozen; one confirmatory read |
| Final strategy test | New, prospectively collected data | Never reached |

Why it was partitioned this way:

- **Leakage.** Splits were chronological, never random. Inner folds were purged and
  embargoed by at least the maximum feature lookback plus the outcome horizon, so a
  training anchor could never share an outcome window with an evaluation anchor. Every
  feature used only data available at the anchor.
- **Retrospective selection.** All 360 hypotheses (36 states × 10 coordinates) were
  registered, with identity hashes, before any outcome was computed. Phase B was allowed
  to read 2024 once, for exactly the nine frozen phenomena, with no redefinition. That
  stops the validation year from influencing which result is reported.
- **Overfitting.** Benjamini–Hochberg FDR control (q = 0.05) ran across the whole
  registered family. A redundancy rule and a simplest-representative rule kept
  near-duplicate states from being counted as independent discoveries. Advancement also
  required per-month, per-quarter and per-activity-band stability, not only pooled
  significance.

The 2024 interval was a holdout for the MAFE lineage only. Earlier projects had already
used the same tape, so it is not globally virgin data.

## 0056 — definition and source

- **Registry id:** `MAFE-PH-A-0056`, "Terminal Same-Side Run", family 006, coordinate event 5.
- **Definition:** at an anchor trade, the length of the run of same-aggressor-side
  trades that ends at the anchor, inside the causal inclusive five-event window. The
  response is the anchor-side-normalised price displacement to the fifth strictly
  subsequent aggregate trade. Aggressor side comes from `buyer_is_maker` (false =
  aggressive buy).
- **Source:** the Phase A discovery registry (2023). It was the only *directional*
  representative among the 44 `PROMISING` states that also replicated. The other
  promoted states predict movement magnitude, not direction.
- **Selection note:** 0056 was chosen over its sibling states 0057–0060 in report prose,
  matching the highest IQR-standardised effect. That criterion mechanically favours the
  shortest coordinate, and the frozen redundancy rule would not have removed the
  siblings. On futures, the siblings behave almost identically.

## Final 300-second evidence (live paper trading)

| Item | Value |
| --- | --- |
| Venue / instrument | Binance USD-M perpetual futures, `BTCUSDT` |
| Feed | Public WebSocket `bookTicker` (L1) + `aggTrade` |
| Execution model | Paper; taker, top-of-book, no funding, 0.001 BTC per trade |
| Rule | Enter on 0056 in the run direction, exit at a fixed 300 s; one position at a time |
| Branches | Entry delay 100 / 250 / 500 ms (exit delay 100 ms) |
| Audited window | 2026-09-23 10:27 → 2026-09-24 01:51 UTC (≈15.4 h, two partial UTC days) |
| Trades | 182 closed per branch (546 total, 374 distinct signals) |

| Branch | Gross USD | Total cost USD | Net USD | Mean net / trade | Win rate (net > 0) | Win rate (gross > 0) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 100 ms | −0.2239 | 3.2618 | **−3.4857** | −0.01915 | 72/182 = 39.6% | 52.2% |
| 250 ms | +0.8027 | 3.2518 | **−2.4492** | −0.01346 | 83/182 = 45.6% | 54.4% |
| 500 ms | +2.2432 | 3.2518 | **−1.0086** | −0.00554 | 87/182 = 47.8% | 58.8% |

All 546 trades reconciled exactly from their fills (commission, modelled slippage, spread
and P&L). The win rates come from those audited rows. They describe this 15-hour sample
only and are not an expected hit rate.

Cost per round trip was about $0.0179, or roughly 2.1 bps, and **fees were 94.7% of
it**. Even the best branch (500 ms) had gross of 1.23¢ per trade against 1.79¢ of cost.
The modelled fee of 1.0 bps per side is below standard public taker tiers, so real costs
would probably have been higher.

## Position Manager result

A rule-based manager (`UNVALIDATED_RESEARCH_POLICY_V1`) was run in paper alongside the
fixed-300 s baseline. It had cost-scaled stop and trailing rules, break-even protection,
and conditional extension to a 900 s maximum. Results on the same signals, eligible
pairs only:

| Branch | Eligible pairs | Baseline net | Manager net | Manager − baseline |
| --- | ---: | ---: | ---: | ---: |
| 100 ms | 140 | −3.8363 | −3.0562 | +0.7801 |
| 250 ms | 132 | −1.1142 | −2.6188 | −1.5047 |
| 500 ms | 135 | −0.8549 | −2.8907 | **−2.0358** |

On the primary 500 ms branch the manager exited early (median hold 75 s). It turned 41
baseline winners into losses, and essentially all of the damage came from exits
(−$2.037), not from entries (+$0.0015). The 100 ms improvement still left the manager's
net negative. A design for a learned manager was written, but it was never trained:
there were too few independent episodes and no verified counterfactual exit labels.

## Final economic conclusion

On this data and this evidence:

- 0056 is a **real but economically immaterial** directional microstructure effect.
  Its gross continuation is a fraction of a basis point to about 1 bps, while a
  round-trip taker trade costs about 2–21 bps depending on the fee assumption.
- A clairvoyant bound (perfect direction and perfect exit timing) on Binance spot
  earned 15.25 bps at 300 s, against a 21.03 bps round-trip cost at undiscounted taker
  fees. No strategy on that horizon and cost can be profitable.
- Passive (maker) execution removes most of the fee but not the problem. Spread capture
  on BTCUSDT is about 0.001 bps, and passive fills were adversely selected on both sides.
- Exit management, entry filtering, combining states, cross-venue lead–lag, and
  regime conditioning were each tested and none closed the gap.

**Net expectancy was negative in every executable test. MAFE was not promoted to live
trading.** The conclusion applies to this experiment and this evidence. It does not claim
that no microstructure edge exists for other data, venues, fee levels or execution
infrastructure.

This archive is a research record and not investment advice.
