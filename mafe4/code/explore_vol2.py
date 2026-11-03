"""EXPLORATORY robustness of the top-vol-tercile F3 gate (discovery only): day-cluster and month-cluster bootstrap (cross-coin correlation), side split, distinct days."""
import json, numpy as np, pandas as pd, stats as S
from discover import load, R
ev = load(); fr = json.load(open(f"{R}/f4_frozen_models.json")); ve, ae = fr["vol_edges"], fr["act_edges"]; rows = []
for cid, tg, H, fam in (("F3|15|3|H240", "E|15|3", 240, "F3"), ("F3|15|4|H240", "E|15|4", 240, "F3"), ("F3|5|4|H240", "E|5|4", 240, "F3")):
    d = S.prep(ev[(ev.trig == tg) & (ev.H == H)], fam); d["vol"] = S.bins(d, ve, ae) // 9; x = d[d.vol == 2].copy()
    x["mon"] = pd.to_datetime(x.t * 60, unit="s").dt.strftime("%Y-%m")
    for lab, cl in (("coin-day (prereg)", x.cl), ("day (all coins)", x.day.astype(str)), ("month", x.mon)):
        m, lo, hi, p = S.boot(x.net.values, cl.values, B=3000)
        rows.append(dict(cell=cid, cluster=lab, n=len(x), n_clusters=cl.nunique(), net=m, ci_lo=lo, ci_hi=hi, p=p))
    for s, nm in ((1, "long(after down move)"), (-1, "short(after up move)")):
        y = x[x.side == s]
        if len(y): rows.append(dict(cell=cid, cluster=f"side={nm}", n=len(y), n_clusters=y.day.nunique(), net=y.net.mean(), ci_lo=np.nan, ci_hi=np.nan, p=np.nan))
    # also leave-top-3-months-out
    top = x.groupby("mon").net.sum().sort_values(ascending=False).index[:3]; y = x[~x.mon.isin(top)]
    rows.append(dict(cell=cid, cluster="drop 3 best months", n=len(y), n_clusters=y.mon.nunique(), net=y.net.mean(), ci_lo=np.nan, ci_hi=np.nan, p=np.nan))
o = pd.DataFrame(rows); o.to_csv(f"{R}/explore_vol_gate_robust.csv", index=False); print(o.round(3).to_string())
