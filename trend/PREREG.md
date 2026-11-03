# TREND — pre-registration (written 2026-10-15, before any backtest outcome was computed)

Status of the data at the time of writing: broker facts (M1) were read; raw price downloads were started; **no return, signal or P&L statistic has been computed on any series**.

## Hypothesis
Time-series momentum / trend following, in three classic fixed-parameter forms, applied to a diversified daily universe of IC Markets CFDs, earns a positive net Sharpe after realistic costs at a 12 % vol target.

## Universe and data
- Daily closes at **22:00 UTC** (17:00 New York, FX roll). HistData M1 bid (timestamps EST-no-DST, +5 h → UTC): last M1 close with bar time < 22:00 UTC of each UTC date; a day is valid only if ≥ 120 M1 bars before 22:00 and the last bar is ≥ 16:00 UTC, otherwise the day is a holiday (price carried forward, zero return). Crypto: Binance spot 1h klines (close of the 21:00–22:00 bar). Stooq was not usable (JavaScript proof-of-work wall; not circumvented) — documented; HistData covers all index/energy needs.
- Mapping (broker name ← source): FX EURUSD GBPUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD EURJPY GBPJPY EURGBP AUDJPY EURCHF ← same HistData names; XAUUSD, XAGUSD ← same; US500 ← SPXUSD; USTEC ← NSXUSD; DE40 ← GRXEUR; UK100 ← UKXGBP; JP225 ← JPXJPY; XTIUSD ← WTIUSD; XBRUSD ← BCOUSD; BTCUSD/ETHUSD ← Binance BTCUSDT/ETHUSDT. **Not available** (no source, excluded and listed): US30, XNGUSD, bond CFDs.
- Classes: FX (12), Metals (2), Indices (5), Energy (2) = **main universe**. Crypto (2) has < 8 years of history through the end of validation (Binance starts 2017-08) so it fails the ≥ 8-year rule and is **supplementary only** (robustness variant). The ≥ 8-year rule is evaluated on data up to 2022-12-31.
- An instrument becomes tradable once it has ≥ 260 valid daily closes. Warm-up data before 2009-01-01 (2008 where HistData has it) is used only to initialise signals; P&L evaluation starts 2009-01-01.
- Risk shares b_i: equal across classes that currently have ≥ 1 tradable instrument, equal within class (sum b_i = 1). Fixed ex ante.
- Returns: close-to-close simple returns in the instrument's quote currency; P&L is treated as a fraction of equity = position (notional / equity) × return. Quote-currency → account-currency conversion of P&L is ignored in the main backtest (second-order); position sizing in M3 does use conversion.

## Partitions
Development 2009-01-01 → 2018-12-31 (report only, no tuning) · Validation 2019-01-01 → 2022-12-31 (one read, frozen systems) · **HOLDOUT 2023-01-01 → 2026-09-30 sealed**: the loader physically excludes it (holdout rows are written to a separate file never opened by this study); `holdout_test.py` refuses to run unless `TREND_UNSEAL=1`; the lead researcher runs it once. Record: the 2023+ period was a sealed period for earlier *gold-intraday* studies; this study consumes it for a different hypothesis family (daily diversified trend following).

## Common machinery (all three systems)
- σ_i,t: EWMA (α = 2/(25+1)) of squared daily returns, annualised ×√252, **floored at 50 % of its own trailing 252-day mean**.
- Raw position (fraction of equity) w_i,t = f_i,t · b_i / σ_i,t (S1: f = ±1; S2: f = forecast/10; S3: f = ±1 and σ replaced by the 20-day ATR proxy, see below).
- Portfolio scaling: w ← m_t · w where m_t = 12 % / sqrt(w′Σ_t w), Σ_t = trailing 250-day sample covariance (annualised); m_t capped at 6. (This is the portfolio-level vol target, i.e. an implicit diversification multiplier, fixed by construction, not fitted.)
- Position buffering: define the unit u_i,t = |position at |f| = 1| ; trade (move fully to target) only if |target − current| > 0.10 · u_i,t; always trade when the sign flips.
- Timing: signals use closes through day t; the position is set at the close of day t (idealised same-close execution) and earns the return t→t+1.
- **S1 TSMOM**: f = sign(P_t / P_{t−252} − 1).
- **S2 EWMAC**: for (fast, slow) ∈ {(16,64),(32,128),(64,256)}: forecast_k = scalar_k · (EMA_fast − EMA_slow) / (P · σ_daily), σ_daily = σ_i,t/√252; Carver's published scalars 3.75, 2.65, 1.87 (so average |forecast| ≈ 10); each capped ±20; average of the three (FDM = 1, none applied), capped ±20; f = forecast/10.
- **S3 Donchian** (close-based, since only closes are kept): long when close > max of prior 55 closes, short when close < min of prior 55 closes; long exits (to flat) when close < min of prior 20 closes, short exits when close > max of prior 20 closes (exits are processed before entries on each day). Sizing by ATR proxy A = mean of |ΔClose| over 20 days, as % of price: raw w = ±b_i / (A%·√252·1.2533) (the 1.2533 converts mean-abs to σ); then the same portfolio vol scaling to 12 %. (A literal "0.5 % equity per ATR per unit, no portfolio scaling" version is run as a robustness variant only.)

## Costs (broker facts M1; **ASSUMED** where extrapolated back in time)
- Spread: current quoted spread in price units divided by current price = constant fraction applied to all history (ASSUMED; early-period spreads were wider — see robustness for 2× spread). Cost on each position change = |Δw| × spread_frac / 2 per side. Commission: USD 30 per million USD per side (FX and metals; 0 on indices/energy/crypto) = 0.3 bp per side, treated as per side (ASSUMED reading of the field).
- **Standard cost model**: spread + commission ×1.0 and financing Model A. **Conservative model**: spread + commission **×1.5** and financing Model B.
- Financing Model A (broker constant, ASSUMED constant over time): current swap points converted to a fraction of current price per calendar day (swap_points × pip_size / price; crypto: −20 %/yr "percentage" long, 0 short); positive = credit. Accrued on every calendar day a position is held (weekend and triple-swap days are included by accruing calendar days between consecutive closes).
- Financing Model B (conservative): US 3-month T-bill (FRED DTB3) r_t. Indices, commodities, metals, crypto: long pays r_t + 2.5 %, short receives r_t − 2.5 % p.a. (a negative receipt is a cost). FX: long pays (r_quote − r_base) + 1 %, short pays (r_base − r_quote) + 1 %, with 3-month interbank rates from FRED (OECD monthly series, forward-filled; USD from DTB3), i.e. rate differential minus 1 % markup on either side. (Index longs are not credited with dividends in this model — conservative, noted.)
- Sharpe is computed on net returns with **no risk-free subtraction** (an unfunded CFD account earns no interest on the balance).

## Metrics (net of all costs)
Annual return (CAGR), annual vol, Sharpe (mean/std·√252), max drawdown, worst rolling 12 months, % positive months, one-way turnover (Σ|Δw|/yr); per instrument / asset class / year attribution (gross, costs, financing); correlation with equal-risk buy-and-hold (long every instrument, same b_i/σ_i sizing and the same 12 % scaling, gross). Sharpe CI: stationary block bootstrap, mean block 20 days, 10 000 resamples, seed 20261015; "lower 90 % CI" = 5th percentile.

## Decision gates
- Development: report only.
- Validation, per system: net Sharpe > 0 under the **conservative** model AND bootstrap 5th percentile of net Sharpe > −0.2. Failing systems are dropped before the holdout. 2019–2022 is 4 years, so power is low (SE of a Sharpe estimate ≈ 0.5); this will be stated in the report.
- "Best validated system" (frozen for M3/M4/holdout): the passing system with the highest conservative validation net Sharpe. If none passes, the holdout is not recommended and M3 is run on the least-bad system for illustration only (labelled).
- Holdout (lead runs): net Sharpe > 0 under conservative costs and max drawdown < 30 % at the 12 % target.

## Controls (reported)
1. Lookahead: positions lagged one and two extra days must not improve Sharpe materially (> 0.15 would be flagged); plus a prefix-invariance test (positions at date T computed from data truncated at T equal those from the full data).
2. Placebo: same sizing/turnover, random sign per hold episode, 200 draws; the real system is compared to the placebo distribution.
3. Cost accounting: independent recomputation that costs are charged on every position change and financing on every calendar day held (synthetic test with known answers).

## M3 small account (frozen best system)
Simulate with the broker's real minimum volume/step and integer-lot rounding (nearest step; below half of the minimum → 0) for USD 500 / 2 000 / 10 000 starting equity (USD used as account currency; the demo is EUR — conversion noted). Rebalance rule: trade only if the integer target differs from the held size by more than max(10 % of the ideal unit, half a step). Margin: leverage scenarios 1:30, 1:100, 1:500 flat; positions are scaled down pro rata when required margin would exceed 80 % of equity. Report instruments held, achieved vs intended vol, tracking error vs the unconstrained portfolio, return/Sharpe/drawdown, margin usage; a smallest sensible universe for USD 500 is proposed *from instrument minimum-size facts* (not from performance), and 12-month outcome ranges come from bootstrap of the simulated daily returns.

## M4 robustness (dev + validation only; reported, not used to choose)
Lookbacks ×0.5 and ×1.5 (all systems); drop each asset class; start-date sensitivity; slippage 2× spread; execution one day later; crypto added (supplementary); S3 literal ATR sizing.

## Deviations
Any change after the first outcome is computed will be listed in REPORT.md under "Deviations", with the reason.

## Amendment 1 (2026-10-15, after a development-only smoke test on 6 instruments, **before** any validation number was seen)
In the low-rate development years the "conservative" financing Model B (T-bill ± 2.5 %, FX differential − 1 %) is *cheaper* than Model A (today's broker swap points held constant, which embed ~4 % rates), so ×1.5 costs + Model B is not the harshest combination. The gates stay exactly as pre-registered (conservative = ×1.5 + Model B), but a third model **"stress" = ×1.5 costs + Model A** is also computed and reported for every table, and the report states explicitly whether any gate verdict would change under it.

## Amendment 2 (2026-10-15, data cleaning, before any system result)
HistData GRXEUR (DE40) changes level on 2020-06-15 (≈12 000 → ≈3 200, i.e. the feed switches to a Euro-Stoxx-50-like series). Rule fixed before any backtest result: in non-crypto series, a close-to-close |log return| > 0.5 marks a feed splice and the series is **truncated the day before** (NaN afterwards, the instrument leaves the portfolio). This affects DE40 only (from 2020-06-15). The WTI 2020-04-21 move (−0.485 log, CFD feed floors prices above zero) stays. All the other > 8 % moves in `data_quality.json` correspond to known events (SNB 2015-01-15, Brexit 2016-06-24, Mar 2020, …) and are kept. HistData WTIUSD pages for 2024–2025 and Jan–May 2026 were not available, which only matters for the sealed holdout.
