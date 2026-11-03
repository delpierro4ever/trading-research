"""Correction to c1_m2.py: the weekday label is constant within a day, so the within-day permutation used there is vacuous (p=1). Weekday heterogeneity is re-tested here with the
day-level permutation (whole days permuted over weekday labels, same as the month test), and m2_heterogeneity.csv weekday rows + Holm values are replaced. 2023-2024 only."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from c1_common import *
rng = np.random.default_rng(SEED + 1); B = 10000
df = load_trades(); HC = ["gross_bps", "lat500_bps", "spread_bps", "impact_small_bps", "impact_big_bps"]; POST = pd.Timestamp("2023-03-22")
SC = {"2023": df[df.year == 2023], "2023post": df[(df.year == 2023) & (df.day >= POST)], "2024": df[df.year == 2024]}
def Q(lab, k, N_, S):
    n = np.bincount(lab, N_, k); out = []
    for j in range(S.shape[1]):
        s = np.bincount(lab, S[:, j], k); ok = n > 0; m = s[ok] / n[ok]; mu = S[:, j].sum() / N_.sum(); out.append((n[ok] * (m - mu) ** 2).sum())
    return np.array(out)
H = pd.read_csv(f"{RES}/m2_heterogeneity.csv"); H = H[H.by != "weekday"]; new = []
for sc, d in SC.items():
    da = day_agg(d, HC); lab = da.index.dayofweek.values; Nd = da.N.values.astype(float); Sd = da[HC].values; k = 7
    obs = Q(lab, k, Nd, Sd); cnt = np.zeros(len(HC))
    for _ in range(B): cnt += Q(rng.permutation(lab), k, Nd, Sd) >= obs
    for j, c in enumerate(HC): new.append(dict(scope=sc, by="weekday", outcome=c, groups=7, Q=obs[j], p=(1 + cnt[j]) / (B + 1)))
H = pd.concat([H[["scope", "by", "outcome", "groups", "Q", "p"]], pd.DataFrame(new)], ignore_index=True)
H["p_holm"] = np.nan
for sc in H.scope.unique():
    m = (H.scope == sc).values; p = H.loc[m, "p"].values; o = np.argsort(p); n = len(p); adj = np.empty(n); run = 0
    for r, i in enumerate(o): run = max(run, (n - r) * p[i]); adj[i] = min(run, 1)
    H.loc[m, "p_holm"] = adj
H["n_tests_in_scope"] = H.groupby("scope").p.transform("size")
H.to_csv(f"{RES}/m2_heterogeneity.csv", index=False)
print(H[H.by == "weekday"].round(4).to_string())
