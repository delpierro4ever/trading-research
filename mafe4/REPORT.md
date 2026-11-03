# MAFE-4 REPORT — forced-flow cascades and 5–60 min flow reversal on Binance USD-M perpetuals

Status: discovery complete, **zero survivors**, 2024 validation not read (K=0), holdout never touched. Costs are assumed (Binance USD-M VIP0, assumption date 2026-10-14). All numbers are bps per trade, pooled over 10 coins, at 1.0× cost unless stated. Everything is in `results/`; the plan is `PREREG.md` (committed before any outcome).

## 1. Data coverage
- 1-min klines (with taker-buy volume and trade count) for BTC ETH SOL XRP DOGE BNB ADA AVAX LINK LTC, 2020-07-01 → 2024-12-31, SHA-256 verified. Late listings: DOGE from 2020-07-10, SOL ~2020-09-14, AVAX ~2020-09-23 (8 pre-listing monthly files 404). Only ≤2024 files were ever requested; 2025+ was not downloaded, so the holdout cannot leak.
- **`liquidationSnapshot` is not archived** (empty listing, monthly and daily). Forced flow is therefore proxied by a ≥4σ one-minute move + same-sign taker imbalance + open-interest drop. That is a proxy, not observed liquidations.
- `metrics` (5-min OI): BTC from 2020-09-01, **all other coins only from 2021-12-01**. Because F1/F2 require the OI drop, they cover alts only from 2021-12. Event counts per year below mostly reflect this, not cascades becoming rarer or commoner.
- Funding rates: complete (monthly files). aggTrades: 50 BTC days only (§6).

## 2. Event counts (F1/F2 triggers, H=15; counts per calendar year)
| trigger (z, q) | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|
| 4σ, 0.6 | 18 | 27 | 179 | 128 |
| 4σ, 0.75 | 3 | 0 | 26 | 21 |
| 6σ, 0.6 | 4 | 11 | 50 | 36 |
| 6σ, 0.75 | 0 | 0 | 4 | 4 |
| 8σ, 0.6 | 0 | 3 | 26 | 11 |
| 8σ, 0.75 | 0 | 0 | 1 | 2 |

F3 (no OI condition) is common: roughly 1.3k–13k events a year per cell. Imbalance ≥0.75 almost never occurs in a one-minute bar; two of the six F1/F2 triggers (6σ/0.75 and 8σ/0.75) have fewer than 10 events in total.

## 3. Discovery table (selected rows of 64; full file `results/discovery_cells.csv`)
Net = gross − fees (10) − slippage − funding. CI = coin-day cluster bootstrap (B=4000). p one-sided; q = BH over all 128 registered cells.

| cell | n | gross | fees | slip | cost+fund | net | 95% CI | p | q | yrs+ /4 | coins+ /10 | net 1.5× | net maker-exit | net stop var. | oracle MFE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 4σ,.6 H15 | 352 | 12.5 | 10 | 6.2 | 16.2 | −3.7 | −11.8…4.7 | .81 | 1 | 1 | 3 | −11.8 | 1.4 | −12.7 | 51 |
| F1 4σ,.6 H30 | 350 | 13.6 | 10 | 6.0 | 16.0 | −2.3 | −11.2…7.1 | .69 | 1 | 2 | 3 | −10.3 | 2.5 | −13.4 | 66 |
| F1 4σ,.6 H240 | 346 | 7.8 | 10 | 5.7 | 15.8 | −8.0 | −28…13 | .75 | 1 | 2 | 2 | −15.8 | −3.4 | −10.6 | 136 |
| F1 6σ,.6 H30 (best n≥100) | 101 | 24.2 | 10 | 9.6 | 19.6 | +4.6 | −17…26 | .35 | 1 | 2 | 6 | −5.2 | 9.9 | −20.6 | 87 |
| F2 4σ,.6 H30 | 350 | −13.6 | 10 | 6.0 | 16.0 | −29.6 | −39…−21 | 1.0 | 1 | 0 | 0 | | | −22.3 | 69 |
| F3 5/3 H60 | 35267 | 2.5 | 10 | 6.6 | 16.6 | −14.2 | −15.8…−12.5 | 1.0 | 1 | 0 | 0 | | | −19.0 | 93 |
| F3 15/4 H60 | 5345 | 9.9 | 10 | 10.1 | 20.1 | −10.3 | −15.9…−5.1 | 1.0 | 1 | 1 | 2 | | | −21.6 | 115 |
| F3 15/4 H240 | 4830 | 11.6 | 10 | 9.5 | 19.5 | −8.2 | −15.9…−0.7 | .98 | 1 | 1 | 2 | | | −23.3 | 174 |

Summary of the 32 cells with n≥100: **24 have positive gross, 1 has positive net** (F1 6σ,.6 H30, +4.6, CI spanning zero, p=.35). F3 grows gross with horizon and window (1.5 bps → 11.6) but never reaches cost. The F2 mirror cells lose by construction (F2 gross = −F1 gross). Two cells are BH-significant (F2 8σ,.75 H60/H240) but have **n=3**: a cluster bootstrap with three events is meaningless, and they fail the n≥100 rule. The stop variant (2×ATR60, a very tight stop) is worse everywhere. The oracle ceiling (50–180 bps) exceeds cost in every cell, so it excludes no horizon; it only shows that perfect timing would pay.

Cost anatomy: fees are fixed at 10 bps; the slippage proxy adds 6–10 bps (the entry/exit minute of a cascade is wide); funding is ≈0 over ≤4 h. **Typical round trip 16–20 bps against a typical gross of 2–25 bps.**

## 4. Pass rule outcome
Primary pass requires BH-significance, ≥3/4 positive year-buckets, ≥6/10 positive coins, n≥100: **0 of 64 pass**. Validation gate (p<0.05/K) is undefined for K=0; **the 2024 validation file was not read.**

## 5. F4 — can we tell in advance when trading pays?
Pre-declared model: 3 variables (per-coin 24 h-vol tercile, trade-count-surge tercile, UTC 8 h bucket), 27 bins, fit on 2020–2022, tested on 2023 (`results/f4_cells.csv`).
- **Cost is predictable; gross essentially is not.** Out-of-sample 2023 correlation of predicted vs realized cost: 0.25–0.43 across cells; of predicted vs realized gross: −0.10…0.13 (typical 0.03).
- Policy cells (trade only in bins with predicted gross > predicted cost): **0 of 64 pass**. One cell is BH-significant (F3 5/4 H15, q=.011) but with only 25 selected events (rule: ≥60), so it is not a survivor; the other 63 are unremarkable (many select 0 events).
- Descriptive (not tested; full discovery sample, `results/f4_descriptive_bins.csv`): gross rises steeply with volatility while cost rises slowly (F1 4σ H30: gross 3 → 33 → 64, cost 15 → 17 → 22 across vol terciles). This is the one state variable that matters, and the pre-registered 27-bin model failed to exploit it: in 2023 there were almost no high-vol events, so the fit/test split could not see it. See H1 in `docs/HYPOTHESES.md`; it is a **lead, not a result**.

## 6. Controls and checks
- **Planted signal** (+20 bps reversal injected after each BTC F1 4σ event, 30 min): gross 6.7 → 26.7 bps (exactly +20.0), p 0.17 → 0.0007. Engine detects what is there.
- **Lookahead**: delaying the signal one minute leaves mean net at −16.4 vs −17.4 baseline; 1 of 64 cells improves by >1 SE, none by >2 SE (`controls_lookahead.txt`). A deliberate cheat (entry at the signal-minute open) moves F2 gross from +4.7 to +74.8 and F1 from −4.7 to −74.8 — the engine sees leakage when it exists.
- **Permuted direction** (3 seeds): mean gross over cells +0.6, −0.3, +3.1; among cells with n≥100, 0 of 32 reach p<.05 in each seed. BH "discoveries" appear only in cells with n=3–8 (1, 0, 2 of them), the same small-n artefact as the two F2 cells above. Note for the future: p-values from clusters-of-few-events must not be trusted without the size floor.
- **aggTrades (50 BTC days, 121 event minutes)**: kline 1-min return equals the trade-level return (median abs. difference 0.00 bps; imbalance correlation 0.99999), so the 1-min detection is faithful. The move is late and bursty within the minute: median 54 % of the path lies in the largest 10 s; the 90 % point is reached at ~53 s; mean 37 % of the path is in the last 10 s. Signal at the minute close, entry at the next open, is therefore early enough to see the event but late for the sharpest part of it.

## 7. Exploration (EXPLORATORY; hypothesis cards in `docs/HYPOTHESES.md`; plot `docs/explore_event_paths.png`)
9,423 events (≥4σ, same-sign imbalance ≥0.6, no OI condition), discovery only. Move-signed average path (+ = continuation): +60 min −8, +240 min −15 bps. Asymmetric: down-cascades revert (−18 at 60 min, −29 at 240); up-squeezes drift slightly with the move (+5 at 60). Reversal is concentrated in 2021 (−29 at 60) and gone in 2023 (+2). OI-drop events revert (−12 at 15 min) while non-OI events do not. Alts revert more than BTC/ETH. Clustering is strong (57 % of events followed by another within an hour; 23 % in ≥3-coin bursts). Alts that had not yet moved when BTC cascaded drift with BTC (+6 at 5 min, +9 at 30). The vol-gated F3 lead (H1) is robustness-checked in `results/explore_vol_gate*.csv` and `explore_drift_benchmark.csv`: it is all long-after-down-move, sits on a positive-drift regime, and shrinks to +8…+17 bps without the three best months.

## 8. Limitations
- Coin-day clusters ignore cross-coin correlation within a day; day-cluster intervals are about twice as wide in the one case checked. This could only make real findings look better, so it does not rescue the null.
- Fills are at the next open plus a slippage proxy; real cascade fills could be worse. Fee level (5 bps taker) is a 2026 assumption applied to 2020–23 and ignores VIP tiers/BNB discounts.
- OI is a 5-minute snapshot; the signal uses the latest stamp ≤ the signal close, so a fast OI drop inside the signal minute may not yet be visible.
- A third of the F1/F2 grid (the 0.75-imbalance triggers at 6σ and 8σ) has too few events to test.

## 9. Bottom line
Rare large forced-flow events do show a gross fade effect (12–24 bps at 4–6σ, 15–60 min) and 5–60 min exhaustion fades show 1.5–10 bps, but the round-trip cost is 16–20 bps and no pre-registered cell, conditional or not, clears it. Same pattern as MAFE, MAFE-2 and MAFE-3: gross < cost. The new information is that the gap is smallest, and gross grows faster than cost, in high-volatility regimes — a hypothesis that needs its own pre-registered test, with a drift-matched control, before anyone believes it.
