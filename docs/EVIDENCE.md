# MAFE — Evidence by stage

All figures are copied from the programme's frozen reports and audited artifacts. Units
are basis points (bps) of price unless stated. "Gross" means mid-to-mid P&L before costs.
"Net" means after spread, slippage and both fees.

## 1. Phase A — discovery (Binance Spot BTCUSDT, 2023)

- 365 archives, 752,974,771 events, 4,058,700 unique causal anchors. The anchor design
  was outcome-independent: every 250th event per continuity segment, plus the first
  event in each 30 s UTC bucket.
- 360 registered hypotheses, 357 eligible for inference. BH at q = 0.05 rejected 246.
- Status counts: PROMISING 44, OBSERVED 17, REDUNDANT 30, UNSTABLE 108, WEAK 161.
- Unconditional mean absolute displacement: 0.74 / 1.02 / 1.62 / 2.29 / 3.93 bps at
  1 / 2 / 5 / 10 / 30 s. Signed means were near zero.
- 0056: effect 0.490, pooled full-population r = 0.055, positive on 365 of 365 days.
- Nine simplest representatives were promoted: 0056, 0073, 0093, 0113, 0133, 0278,
  0285, 0292, 0325. Only 0056 (continuation) and 0278 (reversal) are directional.
- Phase A tested no economics, P&L, models or signals.

## 2. Phase B — independent validation (2024 holdout)

- 366 archives, 551,044,283 events, 3,254,095 anchors. A primary run and an independent
  replication produced the same scientific result identity.
- 8 of 9 advanced: REPLICATED_STRONG 6, REPLICATED_MODERATE 2, FAILED_REPLICATION 0.
  0278 was not advanced because it was unstable in event time.
- 0056: REPLICATED_STRONG. 2024 effect 1.373 against 0.490 in 2023 (it strengthened).
  It held in 12/12 months, 4/4 quarters, and both sides.
- The report states that Phase B "establishes no profitability, executability, or
  strategy".

## 3. Phase C — natural response and economic headroom (both years)

Only 0056 has a defined direction, so it is the only state with a friction ladder.

| 0056, event horizon | 5 | 10 | 50 | 100 | 250 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 mean direction-normalised response (bps) | 0.004 | 0.029 | 0.145 | 0.203 | 0.260 |
| 2024 mean direction-normalised response (bps) | 0.083 | 0.155 | 0.495 | 0.687 | 0.882 |

- It passed the zero-friction gate and **failed at 1 bps** in both years. 2023 also
  failed the quarter-stability gate, and the magnitude changed about 20-fold between years.
- Classification: `ECONOMIC_HEADROOM_UNCLEAR` / hold, non-advancing. Zero of the nine
  phenomena advanced.
- The movement-magnitude states (0073, 0093, 0113, 0133, 0285, 0292, 0325) predict how
  far the price moves, not which way, and showed high-activity reversals.

## 4. Forward economic probe (live Binance Spot BTCUSDT, prospective)

- Prospective segment: 2026-09-02 → 2026-09-11, 85,492,520 records. The pre-declared
  evaluation window was the first 24.19 h.
- Four frozen taker policies P0–P3 produced 27,846 raw opportunity episodes and **zero
  executions**. Every eligible episode was rejected by the cost gate: estimated cost was
  about 21.0 bps (20.0 bps of it round-trip taker fee at the undiscounted 10 bps/side
  tier), against a best expected gross of 0.745 bps.

## 5. Machine-native search and oracle ceiling (same 24 h window)

- 14,652 candidates, **0 economic survivors**.
- The oracle ceiling is the mean maximum absolute mid excursion over the holding path,
  meaning perfect direction and perfect exit timing: 0.22 bps at 0.25 s, 1.30 at 5 s,
  6.25 at 60 s, and **15.25 bps at 300 s, against a 21.03 bps cost floor**. A
  clairvoyant loses at every searched horizon. Oracle numbers were used only to exclude
  horizons, never to rank candidates.
- The median half-spread was 0.00065 bps (one tick). The total possible spread saving was
  0.026 bps, so cost is about 95% fee, which does not depend on market state.
- An overlap trap: the best candidate appeared to have "8,847 episodes". Reduced to
  non-overlapping 300 s episodes it had n = 2, and it inverted under a small parameter change.

## 6. Passive execution feasibility (same window)

- Round-trip cost at a maker fee *m* bps per side: taker/taker 20.0; maker/maker
  3.37 + 1.66m. With measured adverse selection added, maker/maker is about 4.5 + 1.66m.
- Passive fills were adversely selected on both sides: the mid moved against the fill by
  0.32 bps at 100 ms, rising to 0.99 bps at 10 s.
- The verdict was INCONCLUSIVE because no authoritative maker fee was available. At a low
  enough *m*, the oracle impossibility result stops holding at 120–300 s. That removes an
  exclusion; it is not evidence of an edge.

## 7. Fixed-300 s 0056 paper trading (live Binance USD-M futures BTCUSDT)

The audited cohort, reconciled exactly from fills:

| Branch (entry delay) | Closed trades | Gross USD | Net USD | Mean net USD | Net win rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| 100 ms | 182 | −0.22385 | −3.48569 | −0.019152 | 39.6% |
| 250 ms | 182 | +0.80265 | −2.44919 | −0.013457 | 45.6% |
| 500 ms | 182 | +2.24320 | −1.00864 | −0.005542 | 47.8% |

- Window: 2026-09-23T10:27Z → 2026-09-24T01:51Z (≈15.4 h).
- Cost assumptions: commission 1.0 bps per side, slippage 0.05 bps, spread cost at the
  touch, 0.001 BTC per trade, no funding. Mean cost per trade (500 ms) was $0.017867,
  94.7% of it fees.
- The apparent 500 ms advantage over 250 ms is mostly path-dependent selection. On the
  131 signals both branches traded, 500 ms was $0.057 *worse* in total. Three
  opposite-direction trades account for $1.41 of the aggregate difference.
- Robustness (500 ms mean net per trade): median −0.00358, 10% trimmed −0.00694,
  chronological thirds +0.00706 / −0.01698 / −0.00650.
- A post-hoc "5 ms processing" entry filter showed +$0.0114 per trade on 43 trades. It
  was not pre-registered, it was less than one standard error from zero, and it weakened
  over time. It was not adopted.
- A later pooled analysis across four cohorts (1,221 unique signals, 641 non-overlapping
  episodes, about 58 clock hours) found mean gross ≈ 0.92 bps (hour-clustered 95% CI
  roughly +0.24 to +1.60 bps) against about 2.14 bps cost. Net was negative on every
  UTC day. Entry-selection and exit-policy predictability were about zero out of sample.
  *These analysis scripts were not preserved, so this pooled figure is secondary to the
  audited cohort above.*

## 8. Position Manager

See the README table. On the 500 ms branch: 135 eligible pairs, manager − baseline =
−$2.036. The median paired delta was −$0.0054, and dropping the three worst deltas still
leaves a mean of −$0.0090. Exit timing accounts for the whole loss (−$2.037); entry fills
contributed +$0.0015. 65 of 472 joined pairs were censored, and including them does not
reverse any branch's sign. The learned-manager design was specified but judged not
trainable: 193 independent entries on the primary branch and zero verified
counterfactual exit labels.

## 9. Re-examination on futures and other follow-ups

- All 44 Phase A PROMISING states were re-implemented on about 97 h of USD-M futures
  data (three disjoint periods). 43 of 44 replicated their estimand; **none was
  economically material**. The best replicated conditional signed response was about
  0.3–0.7 bps.
- 0056 on futures: +0.24 to +0.63 bps direction effect, complete by 5 s and flat out to
  300 s. It was symmetric long and short. It fired on about 65% of all aggTrades, so it
  is not a rare event on futures.
- Direction × magnitude interactions: 0 of 12 pre-registered pairs improved in all three
  periods, with 0 BH discoveries.
- 0056 as a quote-pull or adverse-selection filter for passive quotes: falsified, with an
  effect of 0.07 bps or less and an unstable sign.
- 2023 slow-directional search, 10–300 s (610,327,996 events): 341 of 960 cells were
  statistically significant, and none reached the 3.165 bps economic screen (best
  1.054 bps).
- Cross-venue (Binance/Bybit) feasibility, 5 discovery days: crossed-arbitrage
  −10.4 bps per trade, and lead–lag gross of 0.2–2.1 bps against 10–11 bps of fees.
  Killed.
