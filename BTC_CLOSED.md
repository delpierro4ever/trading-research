# BTC research line — CLOSED (2026-10-15)

Decision by the user after review: the BTC/crypto short-horizon research line is retired. This note is the single entry point for anyone reopening it.

## What was tested
| Phase | Question | Data | Verdict |
|---|---|---|---|
| MAFE (archive, root README) | Aggressive-flow microstructure states, ≤ 300 s | Binance spot BTCUSDT aggTrades 2023–24 + live futures paper | Real effect (0056), gross ≲ 1 bps vs 2–21 bps cost. No edge. |
| MAFE-2 (`phase2/`) | 1h/4h/24h futures positioning, funding, premium, OI | Binance USD-M BTC/ETH 2020–24, 25 alts | 0 BH survivors; 24 h capitulation-long failed 2024 validation and the alt replication. |
| MAFE-1R (`mafe1r/`) | Rebuild MAFE; why did economics go positive → negative? | 1,304,019,054 spot trades re-downloaded (exact match) | Gross +0.4 bps/trade, net negative every month under every cost model. The one regime change is the 2023-03-22 tape break (end of zero-fee BTCUSDT; gross ≈ 0 before). Trade count and cost regime do not explain anything. |
| MAFE-1C (`mafe1c/`) | Can profitable times be told in advance? One-shot 2025 test | 441.6 M spot trades 2025 + futures sample | Cost is ~99 % fixed fee; its variable parts are predictable but tiny. Gross is not predictable (2025 ranking reversed). Primary gate FAIL (0 trades). 0056 gross is durable in 2025 (0.32 bps) but 6–60× below cost. |
| MAFE-4 (`mafe4/`) | Liquidation cascades, 5–60 min flow reversal, 10 perps | 1-min klines + OI + funding 2020–23 | 0 of 128 cells survive; cascade fade gross 12–24 bps vs 16–20 bps cost. Cost predictable (r 0.25–0.43), gross not (≈ 0.03). |

## The lesson
Every phase found real but small effects whose gross is below a mostly fixed fee. The edges belong to participants with exchange-side latency and rebate-level fees, not to a small taker account. Being able to predict expensive times does not create profitable times.

## Untested leads (recorded, NOT evidence)
- MAFE-4 H1 (`mafe4/docs/HYPOTHESES.md`): long after down-moves in top-volatility tercile, 4 h hold — likely bull-market drift; would need a single-rule prereg with a drift-matched control on 2024.
- Zero-fee promotional pairs (MAFE-1C §5): the only cost class under which 0056's ~0.3 bps could pay.
- BTC as one market inside a daily, diversified trend-following study (costs negligible at that horizon) — a different line, not a reopening of this one.

## Holdouts and data
- MAFE-2 BTC holdout 2025+ and MAFE-4 holdout 2025-01…2026-08 were never read (MAFE-1C read 2025 spot once, for 0056 only). Tokens kept in /home/ubuntu/mafe-data/.
- All raw crypto data deleted from the server on 2026-10-15 to free space; everything is re-downloadable from data.binance.vision, and every phase's code, manifests (SHA-256) and results remain in this repository.
