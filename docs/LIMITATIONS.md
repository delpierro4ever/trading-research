# MAFE — Limitations and scope of the conclusion

## What the historical dataset did not contain

The 1,304,019,054-row Binance Spot BTCUSDT dataset for 2023–2024 is **aggregate trades
only**. It did NOT contain:

- historical full-depth or order-book state;
- observed bid/ask spread;
- queue position;
- order-book replenishment or cancellations;
- local receive latency (the replay convention sets availability equal to exchange time).

It also has millisecond resolution only. An aggregate trade groups several fills and
does not expose each one. For those reasons, claims about sub-millisecond reactions and
queue dynamics were ruled out from the start.

The live futures paper tests recorded top-of-book (`bookTicker`) and `aggTrade` only. They
had no depth stream, and queue position, cancellations and partial fills could not be
observed. The local book was often stale relative to trades: about 61% of trades printed
beyond the locally known touch when they arrived.

## What was not proven

- **No executable edge was demonstrated.** That is not a proof that none exists. The
  oracle-ceiling result (§5 of `EVIDENCE.md`) is a proof only for taker execution at the
  stated fee, on that venue, over that window.
- Paper results are simulations: taker fills at the observed delayed touch, with modelled
  slippage and no funding. They are not exchange fills.
- The modelled futures fee (1.0 bps per side) was not the user's verified fee tier. The
  maker fee was never available, so the maker results are expressed as a function of an
  unknown fee *m*.
- The 300 s paper evidence covers about 15 h (audited) and about 58 h (pooled), on one
  instrument and one venue, in one market regime. The standard error of per-trade net
  (about $0.0073 for n = 182) is larger than the effect sizes of practical interest.
- The 2024 holdout was a holdout for MAFE only. Earlier projects had used the same tape.
- The Position Manager was a hand-written rule set. No learned manager was trained or
  tested.
- The win rates reported are sample descriptions and are not forecasts.
- Signal-conditioned passive execution, and venues or instruments other than Binance
  BTCUSDT, were not tested.

## Validation the result survived

- Pre-registered hypotheses with frozen identity hashes before any outcome was computed.
- A chronological partition with a sealed, read-once 2024 holdout.
- BH FDR control, plus redundancy and simplest-representative rules.
- An independent deterministic replication of Phase B with the same result identity.
- Month, quarter, activity-band and side stability gates.
- Exact Decimal reconciliation of all 546 audited paper trades from their fills.
- Reduction to non-overlapping episodes, block bootstrap, and trimmed, winsorised and
  drop-top/drop-bottom robustness checks.
- An independent audit of the paper-trading conclusions, including a cross-branch census
  proof of the selection mechanism.

## Scope

The conclusion applies to **this experiment and this evidence**. This is a research
archive, not investment advice.
