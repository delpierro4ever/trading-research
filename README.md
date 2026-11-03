# Trading research: pre-registered tests that came back negative

Between September and October 2026 I ran a series of studies looking for a trading edge in
Bitcoin, gold and classic trend-following, each one able to pay for real trading costs.
**None passed.** This repository holds the pre-registrations, code, reports and summary results,
so anyone can check how each conclusion was reached.

I'm publishing negative results on purpose. Most backtests that "work" were tuned until they did.
The point of this work was to set the rules before looking at the data, and then accept the answer.

## How every study was run

1. **Pre-register first.** Hypotheses, cost assumptions and pass/fail gates were written and
   committed *before* the data for that stage was opened (see each `PREREGISTRATION.md` / `PREREG.md`).
2. **Split time three ways.** Discovery → validation → a sealed holdout. The holdout loader refuses
   to read those dates unless an unseal token is supplied, and the token is used only after a
   validation pass. No study here reached that point, so **every holdout is still unused**.
3. **Correct for multiple testing.** Benjamini–Hochberg across the hypothesis family in discovery;
   a strict, pre-set p-value gate (Bonferroni over the survivors) in validation.
4. **Judge on net, not gross.** Every result is after spread, fees, slippage and overnight swap,
   using costs measured from real exchange and broker quotes where possible.
5. **Amend in writing.** When a data source failed or a plan changed, the change was committed as a
   numbered amendment before any new results were looked at.

## Results

| Study | Market and data | What was tested | Verdict |
| --- | --- | --- | --- |
| [MAFE-1](MAFE1_ARCHIVE_README.md) | BTCUSDT spot, 1.3 billion aggregate trades, 2023–24 | Short-horizon order-flow states | Real effect (state 0056 replicated on 2024), but 0.004–0.4 bps vs 2–21 bps cost. Net negative on live paper trading. **Closed** |
| [MAFE-1R / 1C](mafe1r/) | Same, rebuilt from scratch, plus 2025 | Why it failed, and whether "when to trade" can be predicted | Gross edge appeared only after Binance's zero-fee period ended (March 2023) and stayed 6–60× below cost. One-shot 2025 test: **fail** |
| [MAFE-2](phase2/) | BTC/ETH USD-M futures, 1 h – 24 h | 139 hypotheses: momentum, taker flow, funding, premium, open interest, positioning, seasonality | 0 survivors in discovery; 6 near-misses all **failed** validation; an altcoin breadth test (25 coins) **failed** |
| [MAFE-3](phase3/) | Gold (XAUUSD), 1-min bars 2010–2022 | 89 calendar/session/breakout hypotheses, then ~45 machine-searched price features with ridge and LightGBM | A real, stable 30–60 min mean-reversion signal (9–10 of 10 years) but worth 1–2 bps vs ≈ 2.7 bps cost; frozen model **failed** 2020–22 validation |
| [MAFE-4](mafe4/) | 10 crypto perpetuals, 1-min, 2020–2024 | Liquidation cascades and short-term flow reversal (128 cells) | 0 survivors. Notable: **cost was predictable** out of sample (r 0.25–0.43) but **gross return was not** (r ≈ 0.03) |
| [Trend](trend/) | 23 broker CFDs (FX, metals, indices, energy, crypto), daily, 2009–2022 | Time-series momentum, EWMAC, Donchian, all at 12% volatility target | All three **failed** 2019–22 validation (≈ 0–3% a year net). Main cost was overnight swap, not spread. Small accounts can't hold the minimum lot within the risk budget |

## What I took from it

- **Costs decide everything at short horizons.** Several effects were real and repeatable, and still
  lost money, because the edge was smaller than the fee.
- **Finding that something is real and finding that it pays are different questions.** The
  pre-registered gates kept the two apart.
- **A sealed holdout is only useful if you're willing not to open it.** Every holdout here is still
  unused for future ideas.

## What's not here

Raw market data is not included (it is large and re-downloadable from the original public
sources named in each data manifest). Separate studies of a third-party trader's paid course and
private signal channel are left out on purpose, because that material isn't mine to publish.
Paths such as `/home/ubuntu/mafe-data` refer to the private server the jobs ran on.

Most of the code was written with AI coding agents (Claude) working under my direction. I designed
the studies, set the gates and made the calls to close each line.
