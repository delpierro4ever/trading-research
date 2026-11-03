# TREND — diversified daily trend following on IC Markets CFDs (REPORT)

All numbers: 2009–2022 only (development 2009–2018, validation 2019–2022). The 2023-01 → 2026-09 holdout was **not touched**; `holdout_test.py` is written and sealed. Definitions: `PREREG.md` (+ two dated amendments). Code: `code/`, results: `out/`.

## Verdict
**None of the three pre-registered systems passes the validation gate**, so none goes to the holdout (per PREREG). Gross of costs the systems earn a modest positive Sharpe in development (S1 0.53, S2 0.51; S3 0.10), but financing and costs consume most of it, and 2019–2022 is too short to distinguish any of them from zero. For a small account the larger obstacle is minimum contract size (below).

## 1. Broker facts (M1; a broker demo account, queried 2026-10-15 by the `SymbolInfo` cBot; `out/broker_symbolinfo.json`)
Account currency EUR, account leverage 1:500. Commission USD 30 per million USD per side (0.3 bp) on FX and metals, none on indices/energy/crypto (spread only). Spreads are single snapshots.

| Instrument | min vol (units) | min notional USD | spread (bp of price) | swap long / short (points/day) |
|---|---|---|---|---|
| EURUSD | 1 000 | 1 122 | 0.09 | −0.80 / +0.13 |
| USDJPY | 1 000 | 1 000 | 0.06 | +0.82 / −1.70 |
| EURCHF | 1 000 | 1 122 | 0.54 | +0.36 / −1.08 |
| XAUUSD | 1 oz | 4 147 | 0.29 | −57 / +40 |
| XAGUSD | 10 oz | 561 | 0.89 | −0.82 / +0.57 |
| US500 | 0.1 | 770 | 0.65 | −18.5 / −0.23 |
| USTEC | 0.1 | 2 975 | 0.34 | −73 / −0.93 |
| UK100 | 0.1 | 1 418 | 2.3 | −25 / −0.8 |
| JP225 | 1 | 410 | 0.31 | −109 / −57 |
| XTIUSD | 50 bbl | 4 706 | 2.1 | +13 / −21 |
| BTCUSD | 0.01 | 815 | 0.61 | −20 %/yr / 0 |

Full table for all 23 symbols: `out/m3_minsize_facts.csv`. Margin per the broker: FX/metals 1:500, indices 1:200, energy 1:100, BTC ≈ 1:2 (!). Not on the broker's list or without a usable data source: US30 (broker yes, data no), XNGUSD, bonds (none offered).

## 2. Data (M2)
HistData M1 bid → daily close at 22:00 UTC; Binance 1h for crypto; FRED rates. Manifest with sha256: `/home/ubuntu/mafe-data/trend/daily/manifest.json` (559 files). Stooq was unusable (JavaScript proof-of-work wall; not circumvented). Coverage (through 2022-12-30, valid daily closes):

| Group | Instruments | First close | Years |
|---|---|---|---|
| FX (12) | all 12 pairs | 2008-01-02 | 14.0–15.0 |
| Metals | XAUUSD / XAGUSD | 2009-03 / 2009-05 | 13.7 / 13.6 |
| Indices | US500 USTEC UK100 JP225 | 2010-11-15 | 11.7–12.0 |
| Indices | DE40 | 2010-11-15, **ends 2020-06-12** | 9.3 |
| Energy | XTIUSD XBRUSD | 2010-11-15 | 12.0 |
| Crypto | BTCUSD ETHUSD | 2017-08-17 | 5.4 (fails the 8-year rule → supplementary only) |

Data issues: (a) HistData's GRXEUR switches to a Euro-Stoxx-like level on 2020-06-15 (log return −1.33); under the pre-set splice rule (Amendment 2) DE40 is truncated there. (b) WTI cannot go negative in this feed (2020-04-21 −0.485 log). (c) All other >8 % days are known events. (d) HistData WTI for 2024–25 is missing (matters only for the holdout; DE40 will also be missing there). (e) Index CFD series are price returns; dividends are not credited to longs.

## 3. Results (net of costs; Sharpe uses no risk-free subtraction)
"cons" = ×1.5 spread/commission + financing Model B (T-bill ± 2.5 %, FX differential − 1 %) — the pre-registered gate model. "std" = ×1.0 + Model A (today's swap points held constant). "stress" = ×1.5 + Model A (Amendment 1).

| System | Window | Gross Sharpe | Net Sharpe std / cons / stress | CAGR cons | Vol | Max DD cons | Worst 12m cons | Boot 5th–95th pct (cons) | Turnover /yr |
|---|---|---|---|---|---|---|---|---|---|
| S1 TSMOM | DEV | 0.53 | 0.05 / 0.24 / 0.04 | 2.3 % | 12.8 % | −31 % | −24 % | −0.34 … 0.78 | 50 |
| S1 | VAL | 0.44 | −0.01 / 0.18 / −0.02 | 1.5 % | 13.4 % | −17 % | −6 % | **−0.59** … 0.88 | 55 |
| S2 EWMAC | DEV | 0.51 | 0.12 / 0.30 / 0.11 | 3.3 % | 14.3 % | −30 % | −23 % | −0.23 … 0.78 | 26 |
| S2 | VAL | 0.16 | −0.19 / −0.07 / −0.20 | −2.0 % | 14.5 % | −19 % | −14 % | **−0.77** … 0.60 | 30 |
| S3 Donchian | DEV | 0.10 | −0.36 / −0.15 / −0.37 | −2.5 % | 12.3 % | −37 % | −23 % | −0.66 … 0.36 | 54 |
| S3 | VAL | 0.06 | −0.22 / −0.15 / −0.23 | −3.2 % | 14.3 % | −26 % | −17 % | **−1.02** … 0.59 | 48 |

**Gates (validation):** S1 net Sharpe +0.18 but 5th percentile −0.59 < −0.2 → FAIL; S2 −0.07 → FAIL; S3 −0.15 → FAIL. The verdicts are the same under the stress model. The bootstrap interval is about ±0.7 Sharpe wide for 4 years: **the test cannot distinguish a true Sharpe of 0.5 from 0** — "fail" here means "not demonstrated", not "disproved". Realised vol runs 12–14.5 % against the 12 % target. Positive months 48–57 %. Correlation of gross returns with equal-risk buy-and-hold: −0.08 to −0.30 (B&H of the same universe: Sharpe 0.01 DEV, 0.32 VAL, max DD −50 %/−35 %, gross).

Per-year net returns, cons (`out/per_year_*.csv`, chart `out/per_year.png`):
S1: 2009 −6, 10 +18, 11 −5, 12 −5, 13 +16, 14 +16, 15 +28, 16 −22, 17 +13, 18 −18, 19 −2, 20 +12, 21 +1, 22 −4 (%).
S2: −9, +23, +5, −14, +20, +16, +23, −17, 0, −2, −13, +7, 0, −1. S3: −7, +9, −14, 0, +15, −2, −3, −9, −12, 0, −9, +19, −15, −5.
The universe has no bonds or short-rate futures, which supplied much of trend following's 2014 and 2022 gains in the literature; 2022 gross was ≈0 here.

Equity curves: `out/equity_curves.png`.

## 4. Costs anatomy (annualised % of equity, VAL/DEV; `out/attr_*.csv`)
Trading costs (spread + commission) are small: 0.2–0.4 %/yr cons (0.1–0.3 % std), even at 50 round-trip-equivalents of turnover, because FX/index spreads are 0.1–2 bp. **Financing is the dominant cost: −3 %/yr under Model B and −5 to −6 %/yr under Model A**, i.e. 1.5–3 % per unit of gross exposure (average gross exposure 1.6–1.9× equity). Model A applies today's swap points (embedding ~4 % rates plus broker markup) to 2009–2015, when rates were ~0, so it overstates history; Model B charges ±2.5 % on both long and short sides in ZIRP years, which also bites. Reality for a live account today is closer to Model A. By class (S1 DEV gross → net cons): metals +2.7 → +1.7, energy +1.8 → +1.1, indices +1.4 → +0.4, FX +0.9 → −0.2. Spread levels are today's constants applied back to 2008 (ASSUMED; earlier spreads were wider). Doubling spread changes Sharpe by only 0.01–0.02; the gap to the verdict is financing, not spread.

## 5. Controls
- **Look-ahead:** positions at date T are identical when recomputed from data truncated at T (three dates, all systems). One- and two-day extra lag never improves Sharpe by > 0.15 (S1 DEV: 0.24 → 0.38 at lag 1, +0.14, VAL −0.02; this is within noise but near the threshold and is flagged here).
- **Placebo (random sign per hold episode, same sizing, 200 draws, cons):** placebo mean Sharpe −0.29 to −0.47 (costs/financing drag). Real-system percentile: S1 DEV 96 %, VAL 92 %; S2 DEV 96 %, VAL 72 %; S3 68 %/68 %. So S1/S2 show gross signal in development; S3 does not.
- **Cost accounting:** engine cost total equals an independent recomputation exactly (0.054 / 0.028 / 0.054 summed fractions); financing is charged on every one of the 3 643 days with a position; synthetic unit tests with known answers pass (`code/tests.py`). An independent minimal re-implementation of S1 gross gives Sharpe 0.55 / 0.41 vs the engine's 0.53 / 0.44.

## 6. Small account (M3; S1 only, because it is the least bad validated-score system — **illustrative, not recommended**)
Simulation uses real minimum volume/step, nearest-step rounding, USD account (the demo is EUR 670 ≈ USD 750; EUR/USD conversion not modelled), 2009–2022 from the stated equity, `code/run_m3.py`, `run_m3b.py`.
- **Minimum position vs target.** One minimum FX position (1 000 units, ≈ USD 1 000–1 300) has stand-alone annual vol ≈ 11–39 % of a USD 500 account (≈ 3–10 % of USD 2 000, ≈ 1–2 % of USD 10 000). One minimum gold position (1 oz ≈ USD 4 147) is 116 % of USD 500 equity; USTEC 155 %; WTI/Brent 290–350 %. The whole 12 % vol target is therefore used up by a single minimum lot at USD 500.
- **Main 21-instrument book:** USD 500 → average gross exposure 0.10× (nearly all positions round to zero), achieved vol 3.9 % vs 13 % unconstrained, correlation with the unconstrained portfolio 0.22: effectively not trading. USD 2 000 → vol 8.7 %, corr 0.72, tracking error 9 %; USD 10 000 → vol 12.9 %, corr 0.90, tracking error 6 %. Tradable instruments: at USD 2 000 FX majors, silver, JP225/US500; at USD 10 000 everything except oil and USTEC/gold at full size.
- **Smallest sensible USD 500 universe**, chosen from min-lot facts only: the six FX pairs with the smallest min-lot risk (EURCHF, NZDUSD, USDCAD, EURGBP, USDCHF, EURUSD), 1 000-unit lots. Result (cons): CAGR 1.5 %, vol 14 %, Sharpe 0.16, max DD −24 %, 12-month return: empirical 5/50/95th pct −14 % / −1 % / +49 %, bootstrap −11 % / −1 % / +44 %, negative in 53–56 % of years. Over 2009–2022 USD 500 → ≈ USD 620. It is 1–3 concentrated FX bets, not diversified trend following; it also did not remove the failure to clear the validation gate.
- **Margin:** peak margin use ≤ 20 % of equity even at 1:30 (≤ 6 % at 1:100, ≤ 1.2 % at 1:500); no stop-outs. 1:500 applies to this international IC account (shown on the demo); 1:30 would apply only under EU/ESMA rules. Leverage is not the constraint — lot size is.
- **Expected outcomes** (USD 2 000, main book, cons): median 12-month +1 %, 5–95 % range −10 % … +29 %, negative 39–52 % of years; USD 10 000: −19 % … +27 %.

## 7. Robustness (M4; reported, not used to choose; Sharpe cons, DEV / VAL; `out/robustness.csv`)
| Variant | S1 | S2 | S3 |
|---|---|---|---|
| base | 0.24 / 0.18 | 0.30 / −0.07 | −0.15 / −0.15 |
| lookbacks ×0.5 | 0.32 / −0.44 | 0.18 / −0.19 | 0.03 / 0.06 |
| lookbacks ×1.5 | 0.00 / −0.17 | 0.29 / −0.13 | 0.24 / −0.15 |
| spread ×2 | 0.22 / 0.16 | 0.29 / −0.07 | −0.16 / −0.17 |
| one day later | 0.38 / −0.02 | 0.30 / −0.08 | −0.26 / −0.03 |
| drop FX | 0.31 / 0.06 | 0.35 / −0.11 | 0.11 / 0.04 |
| drop metals | 0.18 / 0.14 | 0.34 / −0.03 | −0.23 / −0.34 |
| drop indices | 0.14 / 0.29 | 0.12 / 0.10 | 0.02 / 0.05 |
| drop energy | 0.11 / 0.16 | 0.24 / −0.34 | −0.38 / −0.20 |
| add crypto (suppl.) | 0.30 / 0.35 | 0.35 / −0.11 | −0.11 / 0.24 |
Start-date sensitivity (S1, cons, to 2022): from 2009 0.22, 2011 0.18, 2013 0.27, 2015 0.06, 2017 0.06 — the Sharpe depends heavily on whether the early 2010s are included. S3 literal ATR sizing: DEV −0.22, VAL −0.06. Nothing flips the picture: small positive-or-zero, unstable signs, no variant is robustly good.

## 8. What could go wrong / limits
- Low power: 4 validation years (SE ≈ 0.5 Sharpe); a true 0.3–0.5 Sharpe strategy fails this gate most of the time.
- Cost model is extrapolated: constant spreads, swap points and commission; Model A and B bracket financing but neither is the broker's historic truth. Financing assumptions drive the result; a lower-markup broker or fewer gross-leveraged positions would change it.
- Universe: no bonds/rates, a single US-dollar-heavy FX block (12 correlated pairs), 4 clear classes; index series lack dividends and DE40 is truncated; HistData quotes are one broker-like feed, not IC Markets'.
- Close-to-close idealised execution at 22:00 UTC; P&L currency conversion ignored in the backtest; sizing drifts with equity between rebalances.
- Backtest-only: no live fills, rollover of index CFDs, weekend gaps, margin changes, or leverage caps by regulator.
- The 2023–2026 holdout shares its period with earlier gold-intraday studies (different hypothesis family, recorded in PREREG).

## 9. Deviations from the brief / PREREG
Amendment 1 (stress model added), Amendment 2 (DE40 splice rule). The 10-day stale-feed rule (instrument leaves the book when its feed ends) and the M3 handling of unlisted-instrument prices were implemented while building and before/without affecting any gate decision. US30, XNGUSD and bonds could not be sourced. Next-day-open execution is implemented as a one-day delay (the 22:00 UTC close equals the next session's open for FX). Gate-model results were read once; no parameter was changed afterwards.
