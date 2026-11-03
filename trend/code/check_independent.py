"""Independent minimal re-implementation of S1 gross returns (no covariance scaling, no buffer, plain class-equal weights) as a bug check on the engine."""
import numpy as np, pandas as pd, engine as E
P = E.load_prices(); Pf = P.ffill(); r = Pf.pct_change(fill_method=None)
vol = np.sqrt((r ** 2).ewm(span=25, adjust=False).mean() * 252)
sig = np.sign(Pf / Pf.shift(252) - 1)
ok = (P.notna().cumsum() >= 260) & (P.notna().rolling(10, min_periods=1).max() > 0)
w = (sig / vol).where(ok)
cl = pd.Series({c: E.CLS[c] for c in P.columns})
wt = pd.DataFrame(0.0, index=P.index, columns=P.columns)
for k in cl.unique():
    cols = cl[cl == k].index; wt[cols] = w[cols].div(ok[cols].sum(axis=1).replace(0, np.nan), axis=0)
ncls = pd.DataFrame({k: ok[cl[cl == k].index].any(axis=1) for k in cl.unique()}).sum(axis=1)
wt = wt.div(ncls.replace(0, np.nan), axis=0).fillna(0.0)
g = (wt.shift(1) * r.fillna(0)).sum(axis=1)
for name, (a, b) in E.WINDOWS.items():
    x = g.loc[a:b]; print(name, "independent S1 gross Sharpe (unscaled, unbuffered):", round(float(x.mean() / x.std() * np.sqrt(252)), 3))
