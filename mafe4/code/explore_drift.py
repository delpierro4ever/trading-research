"""EXPLORATORY: unconditional 240-min forward return (bps, entry open t+1, exit open t+241) in the top-vol tercile vs all minutes, by coin-pooled year; drift benchmark for the vol-gate hypothesis."""
import json, numpy as np, pandas as pd, engine as E
R = "../results"; ve = json.load(open(f"{R}/vol_edges.json")); rows = []
for c in E.COINS:
    g = E.load(c); F = E.features(g); o = g["o"]; N = len(o)
    fwd = np.full(N, np.nan); fwd[:N - 242] = (o[242:] / o[1:N - 241] - 1) * 1e4
    sg = F["sig"] * 1e4; ok = ~np.isnan(fwd) & ~np.isnan(sg); ok[E.DISC_END:] = False
    yr = pd.to_datetime((E.T0 + np.arange(N)) * 60, unit="s").year
    hi = ok & (sg > ve[c][1]); lo = ok & (sg <= ve[c][0])
    for y in (2020, 2021, 2022, 2023):
        for nm, m in (("all", ok), ("lowvol", lo), ("highvol", hi)):
            mm = m & (yr == y)
            if mm.sum() > 1000: rows.append(dict(coin=c, year=y, regime=nm, n_min=int(mm.sum()), fwd240=fwd[mm].mean()))
d = pd.DataFrame(rows); t = d.groupby(["regime", "year"]).apply(lambda x: pd.Series(dict(mean_fwd240_bps=np.average(x.fwd240, weights=x.n_min), minutes=x.n_min.sum()))).round(1)
t.to_csv(f"{R}/explore_drift_benchmark.csv"); print(t.to_string())
