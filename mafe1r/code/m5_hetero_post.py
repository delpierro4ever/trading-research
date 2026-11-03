"""Amendment A5 (post hoc): day-label permutation heterogeneity test of replay gross/trade across calendar months/quarters, restricted to 2023-04..2024-12 (full months after the 2023-03-22 tape break)."""
import os, numpy as np, polars as pl, pandas as pd, datetime as dt
ROOT = "/home/ubuntu/mafe-data/mafe1/out"; RES = os.path.join(os.path.dirname(__file__), "..", "results"); rng = np.random.default_rng(11)
tr = pl.read_parquet(f"{ROOT}/trades/*.parquet", columns=["reading", "date", "gross_bps"]).with_columns(pl.col("date").str.to_date().alias("d")).filter(pl.col("d") >= dt.date(2023, 4, 1))
g = tr.group_by(["reading", "d"]).agg(pl.len().alias("N"), pl.col("gross_bps").sum().alias("G")).sort(["reading", "d"]).to_pandas()
g["d"] = pd.to_datetime(g.d); g["month"] = g.d.dt.strftime("%Y-%m"); g["quarter"] = g.d.dt.year.astype(str) + "Q" + g.d.dt.quarter.astype(str)
rows = []
for rd in range(1, 6):
    x = g[g.reading == rd]
    for key in ("month", "quarter"):
        lab = pd.factorize(x[key])[0]; k = lab.max() + 1; N = x.N.values.astype(float); G = x.G.values; mu = G.sum() / N.sum()
        def st(l):
            n = np.bincount(l, N, k); s = np.bincount(l, G, k); m = s / n; return (n * (m - mu) ** 2).sum(), m.max(), m.min()
        Q, mx, mn = st(lab); nul = np.array([st(rng.permutation(lab)) for _ in range(10000)])
        rows.append(dict(reading=rd, by=key, periods=int(k), Q=Q, p_Q=(nul[:, 0] >= Q).mean(), best=mx, worst=mn, p_best=(nul[:, 1] >= mx).mean(), p_worst=(nul[:, 2] <= mn).mean(), null_best95=np.quantile(nul[:, 1], .95), null_worst5=np.quantile(nul[:, 2], .05)))
pd.DataFrame(rows).to_csv(f"{RES}/m5_heterogeneity_postbreak.csv", index=False); print(pd.DataFrame(rows).to_string())
