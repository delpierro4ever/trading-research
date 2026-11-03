"""Section 6 diagnostics: Spearman IC of each feature (z-scored; time features raw) vs the long gross forward return per kept H on
discovery, pooled and per year, with sign stability. Not a gate. Usage (from phase3/code): python -m mafe3.stage2.run_ic"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd
from ..market import Market, O, D0
from . import store, features as Fz
from .trades import Outcomes

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results" / "stage2"
YEARS = list(range(2010, 2020))

def spearman(x, y):
    m = ~(np.isnan(x) | np.isnan(y))
    if m.sum() < 100: return np.nan, int(m.sum())
    rx = pd.Series(x[m]).rank().to_numpy(); ry = pd.Series(y[m]).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1]), int(m.sum())

def main():
    kept = json.loads((OUT / "kept_H.json").read_text())["kept_H_min"]
    M = Market.from_loader("2009-11-01", "2020-01-01")
    t_abs, _, Z = store.load("disc")
    td = t_abs - O; m = td >= D0
    td, Z = td[m], Z[m]
    oc = Outcomes(M, td)
    rows = []
    for H in kept:
        r = oc.by[H]; y = np.where(r["valid"], r["gross"], np.nan)
        for k, nme in enumerate(Fz.NAMES):
            ic, n = spearman(Z[:, k].astype(float), y)
            row = dict(H=H, feature=nme, concept=Fz.CONCEPT_OF[nme], ic=ic, n=n)
            ys = []
            for yr in YEARS:
                mk = oc.year == yr
                v, _ = spearman(Z[mk, k].astype(float), y[mk]); row[f"ic_{yr}"] = v; ys.append(v)
            ys = np.array(ys, float)
            row["mean_year_ic"] = float(np.nanmean(ys)); row["t_years"] = float(np.nanmean(ys) / (np.nanstd(ys, ddof=1) / np.sqrt(np.sum(~np.isnan(ys)))))
            row["years_same_sign"] = int(np.sum(np.sign(ys) == np.sign(ic)))
            rows.append(row)
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "ic.csv", index=False)
    top = df.loc[df.groupby(["H", "concept"])["ic"].apply(lambda s: s.abs().idxmax())].sort_values(["H", "concept"])
    top.to_csv(OUT / "ic_top_by_concept.csv", index=False)
    pd.set_option("display.width", 250)
    print(top[["H", "concept", "feature", "ic", "mean_year_ic", "t_years", "years_same_sign", "n"]].round(4).to_string())

if __name__ == "__main__":
    main()
