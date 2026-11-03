"""Formats results/stage3/{validation.csv,verdict.json} into docs/STAGE3_REPORT.md. Usage (from phase3/code): python -m mafe3.stage3.make_report"""
import json
import pandas as pd
from .train import OUT, OUT as _O

def md(d):
    d = d.round(2)
    return "| " + " | ".join(d.columns) + " |\n|" + "---|" * len(d.columns) + "\n" + "\n".join("| " + " | ".join(str(x) for x in r) + " |" for r in d.values)

def main():
    df = pd.read_csv(OUT / "validation.csv"); v = json.loads((OUT / "verdict.json").read_text())["models"]
    cols = ["model", "period", "n", "gross", "cost", "swap", "net", "net60", "net38", "long_share", "price"]
    s = f"""# MAFE-3 Stage 3 report — frozen ridge M30 / M60, validation read (2020-01-01 → 2023-01-01)

Prereg sha256 354d2c17… (verified). Models trained once on 2010–2019 (hashes in `results/stage3/models.json`; identical to the stage-2 final ridge models).
Rule: c_t = $0.45 / entry price (bps); trade only if |pred| > c_t + expected swap; greedy non-overlap; weekend/swap as stage 1. One read, no variants.
`net60` / `net38` = net at $0.60 / $0.38 on the same trades (threshold fixed at $0.45). All figures bps; `price` = mean entry price, USD/oz.
Gate: weekly-block-bootstrap one-sided p < 0.025, net > 0 in ≥ 2 of 3 years (a year without trades does not count), ≥ 30 distinct days, n ≥ 100.

## Verdict
| model | n | gross | cost | swap | net $0.45 | p | years net>0 | days | gates p/years/days/n | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
"""
    for k, x in v.items():
        g = x["gates"]
        s += f"| {k} | {int(x['n'])} | {x['gross']:.2f} | {x['cost']:.2f} | {x['swap']:.2f} | {x['net']:.2f} | {x['p_boot']:.3f} | {int(x['pos_years'])} | {int(x['days'])} | {g['p']}/{g['years']}/{g['days']}/{g['n']} | {'PASS' if x['PASS'] else 'FAIL'} |\n"
    s += "\n## Per-year table\n\n" + md(df[cols]) + f"""

## Reading
- M30 trades rarely (n={int(v['M30']['n'])}; the ≈2.5 bps hurdle exceeds nearly every prediction): fails n ≥ 100, days ≥ 30 and p.
- M60: n={int(v['M60']['n'])}, gross {v['M60']['gross']:.2f} bps (negative in 2020, ≈0 in 2021–22), net negative in every year at all three cost levels, including the $0.38 spread-only level. The cost did fall (≈2.5 bps against ≈3.1 bps in 2017–19) but the gross edge did not hold: the pattern weakened, it is not only a cost effect.
- Correlation of prediction with the long gross return over the whole 2020–22 grid: M30 {v['M30']['pred_ic_all_grid']:.3f}, M60 {v['M60']['pred_ic_all_grid']:.3f} (same sign as learned, small).
- Both models FAIL. Holdout untouched: no data ≥ 2023-01-01 read; MAFE3_UNSEAL and the token file never used.
"""
    (OUT.parents[1] / "docs" / "STAGE3_REPORT.md").write_text(s)

if __name__ == "__main__":
    main()
