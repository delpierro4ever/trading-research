# MAFE-3 (XAUUSD) — Pre-registration (frozen before any outcome is computed)

Registered: 2026-10-14. Identity = sha256 of this file, recorded in the commit that adds it.
Any change after outcomes are computed must be a new, dated amendment section; nothing above it may change.

## Why gold

MAFE (BTC, ≤ 300 s) and MAFE-2 (BTC/ETH/25 altcoins, 1–24 h) both found real effects that did not pay a
12–16 bps round trip. Spot gold (XAUUSD) on a retail ECN/cTrader account costs about $0.30/oz per round trip,
roughly **1–3 bps**, an order of magnitude cheaper. Its flows are also structurally different: the London
fixes/auctions, central banks, the USD, and session handovers. This is the user's own trading venue.

## Data

Dukascopy historical 1 m candles, **BID and ASK** separately, for XAUUSD (primary) and EURUSD (an explanatory
input for G7 only). Minutes with no ticks or zero volume (market closed) are dropped. Mid = (bid + ask) / 2.

## Partitions (chronological; enforced by the loader)

| Role | Interval |
| --- | --- |
| Discovery | 2010-01-01 → 2020-01-01 |
| Validation | 2020-01-01 → 2023-01-01 (one read, frozen definitions, advanced hypotheses only) |
| Holdout | 2023-01-01 → latest (sealed by token; one read, validation survivors only) |

## Execution and cost convention

- **Grid:** every full UTC hour while the market is open, except where a family defines its own anchor times.
  Features use only bars with close ≤ t − 1 min.
- **Entry:** at the bar opening at t + 1 min. **Exit:** at the bar opening at entry + H. A trade is not entered
  if its hold would span the weekend close (Fri 21:00 UTC → Sun 21:00 UTC), except in G9. A missing exit bar is
  replaced by the next available bar.
- **Gross** = direction × ln(exit mid / entry mid), in bps.
- **Cost (primary, used for every gate)** = observed half-spread at entry + observed half-spread at exit
  (from Dukascopy bid/ask) + commission $0.07/oz + slippage $0.05/oz, converted to bps at the entry price.
- **Swap:** 2.0 bps is charged to *both* longs and shorts for each 17:00 America/New_York rollover crossed, and
  ×3 for the Wednesday rollover (conservative: gold swaps are usually negative on at least one side).
- **Net** = gross − cost − swap.
- **Secondary costs (reported only):** a fixed $0.35/oz and $0.60/oz round trip (standard accounts), and net
  without swap.
- **Non-overlap:** greedy per hypothesis. Every statistic uses independent episodes.

## Signal rule (z families)

z = (x_t − mean) / std over the previous 720 grid points, needing ≥ 480. Fire when |z| ≥ 1.5. Direction is
d · sign(z), with d = +1 continuation and d = −1 reversal, both registered. L ∈ {1 h, 4 h, 24 h}; H ∈ {1 h, 4 h, 24 h}.

## Hypothesis families

| Family | Definition | Count |
| --- | --- | ---: |
| G1 Momentum | x = ln return over L | L × H × d = 18 |
| G2 Seasonality | hour-of-day h = 0..23 (UTC, entry at h:01, H = 1 h, every open day); weekday Mon–Fri (entry 00:01 UTC, H = 24 h, weekend rule waived for Friday by exiting at the Friday close). Direction = sign of the discovery mean. | 24 + 5 = 29 |
| G3 Asia → London | x = sign of the return 00:00 → 07:00 UTC; enter at 07:01 UTC in d · sign(x); H ∈ {1 h, 4 h, 9 h (to 16:00 UTC)} | 3 × d = 6 |
| G4 London PM fix | anchor = 15:00 Europe/London local each trading day; x = sign of the mid return over the 60 min before the anchor; enter at anchor + 1 min, d · sign(x); H ∈ {1 h, 4 h} | 2 × d = 4 |
| G5 Month-end | last trading day of each month: enter 00:01 UTC, exit at 16:00 Europe/London; long and short each registered | 2 |
| G6 Range breakout | at grid t, if the close is above the prior 24 h high (or below the low), trade d · breakout side; H ∈ {1 h, 4 h, 24 h} | 3 × d = 6 |
| G7 USD lead | x = ln return of EURUSD mid over L, z-scored; gold direction = d · sign(z) (d = +1 means gold follows EUR, i.e. moves against the USD) | L × H × d = 18 |
| G8 Weekend gap | x = Sunday reopen mid − Friday close mid; if \|x\| ≥ 0.1 % enter at reopen + 5 min, d · sign(x); H ∈ {1 h, 4 h, 24 h} | 3 × d = 6 |
| | **Total** | **89** |

G2 has no z-score: its direction is the sign of the discovery mean gross, and its test is two-sided. Every
other family has its direction fixed by d.

## Statistics

Per hypothesis on discovery: n, mean gross, mean cost, mean swap, mean net, median net, hit rate, t and
one-sided p for mean net > 0, weekly block bootstrap p (10 000 resamples), per-year net, long/short split, and
the matched drift (mean 24 h gross of a long at every grid hour in the same quarter) for directionally biased
hypotheses. **Benjamini–Hochberg runs at q = 0.10** across all 89 on the net p-values. An informational screen
of gross ≠ 0 (BH q = 0.05) is reported. Every hypothesis is reported.

## Advancement gates

**Discovery → Validation.** All must hold: (1) BH-significant on net > 0, or, if none is, the best ≤ 5 by net t
with mean net > 0 (`NEAR_MISS`); (2) n ≥ 100; (3) mean net > 0 in ≥ 7 of the 10 discovery years, counting only
years with ≥ 10 episodes; (4) if ≥ 70 % of a hypothesis's trades are on one side, its mean (gross − matched
drift) must have the same sign as its mean gross, so the signal beats simply holding. At most **K = 10** advance.

**Validation (2020–2022).** One-sided p < 0.05/K for mean net > 0, mean net > 0 in ≥ 2 of 3 years, and gate (4).

**Holdout (2023 → latest).** One-sided p < 0.05 for mean net > 0, and gate (4). Only a holdout survivor goes to
paper trading on the user's cTrader demo account.

## Out of scope

Multi-signal or ML models (a possible later stage that would be registered separately), stops/targets/position
managers, leverage and sizing, news/economic-calendar events (no point-in-time calendar data), and other
instruments.

## Amendment 1 — 2026-10-14, data resolution (before any outcome is computed)

Reason: Dukascopy began throttling its free datafeed (HTTP 429, about 200 files per hour) after about 1 600
daily minute files. The full minute set (~21 000 files) would take about 4 days. The study switches to
**Dukascopy hourly candles**: one file per month per side, ~800 files in total. No price outcome has been computed.
The minute files fetched so far are not used.

1. **Data:** hourly BID and ASK candles (`{SYM}/{YYYY}/{MM0}/{BID|ASK}_candles_hour_1.bi5`) for XAUUSD and
   EURUSD. Hours with zero volume are dropped. Mid = (bid + ask) / 2.
2. **Decision timing:** a decision at full hour *t* uses only bars that closed at or before *t*. **Entry** is the
   open of the bar starting at *t* (a bot acting within seconds of *t*). **Exit** is the open of the bar starting at
   entry + H. To pay for the lost one-minute buffer, **slippage is raised from $0.05 to $0.10/oz** per round trip, so
   the fixed part becomes $0.07 commission + $0.10 slippage. Half-spreads come from the BID/ASK opens of the entry
   and exit bars, as before.
3. **Family anchors map to hour boundaries:**
   - G3 enters at 07:00 UTC; its 9 h horizon exits at 16:00 UTC.
   - G4's anchor is the hour that is 15:00 Europe/London; x = the mid return of the preceding hourly bar.
   - G5 enters at 00:00 UTC and exits at the hour that is 16:00 Europe/London.
   - G2 hour-of-day enters at h:00 UTC.
   - G8 measures the gap as the mid open of the first bar after the weekend closure minus the mid close of the
     last bar before it. **Entry is the open of the second bar after reopen**, which replaces "+5 min" and is
     conservative because it avoids the reopen spike. H counts from that entry.
4. Everything else is unchanged, including the hypothesis count (89), statistics, gates, partitions and swap.
   Secondary fixed costs stay at $0.35 and $0.60.

## Amendment 2 — 2026-10-14, data source HistData.com (before any outcome is computed)

Reason: the Dukascopy datafeed then throttled even the hourly files (1 file in 30 min, 1 800 s penalties). Its
paid bulk route (AWS requester-pays) was not available to the user. No price outcome has been computed on any
source. **This amendment supersedes Amendment 1**, which stays here only as a record.

1. **Data:** HistData.com free ASCII **1-minute bars** (BID only) for XAUUSD and EURUSD. These come as yearly
   files for past years and monthly files for the current year. HistData timestamps are EST *without* DST (fixed
   UTC−5) and are converted to UTC by adding 5 h; this is verified against the known weekly open and close times.
   Gross returns use BID prices, because no mid price is available.
2. **Timing:** the conventions of the original spec are restored: features use bars with close ≤ t − 1 min, entry
   is at the bar opening at t + 1 min, exit at entry + H, and G8 enters at reopen + 5 min.
3. **Cost (primary, used for every gate):** a **fixed $0.35/oz round trip**, covering spread, commission and
   slippage, converted to bps at the entry price. Swap is unchanged: 2.0 bps per 17:00 New York rollover, ×3 on
   Wednesday, charged to both directions. **Secondary (reported only):** $0.20/oz (a good ECN account), $0.60/oz,
   and net without swap.
4. **Spread sanity check (reporting only, never a gate):** the median and p95 Dukascopy ask − bid spread by
   year, from the ~1 700 daily minute files already downloaded (2009–2014), are reported next to the $0.35
   assumption.
5. Unchanged: the 89 hypotheses, statistics, gates, partitions, and the sealed holdout from 2023-01-01.
