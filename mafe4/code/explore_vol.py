"""EXPLORATORY: net by top-vol tercile and year (discovery only). Not evidence."""
import json, numpy as np, pandas as pd, stats as S
from discover import load, R
ev = load(); fr = json.load(open(f"{R}/f4_frozen_models.json")); ve, ae = fr["vol_edges"], fr["act_edges"]; rows = []
for cid, tg, H, fam in (("F1|4|0.6|H30", "C|4|0.6", 30, "F1"), ("F1|4|0.6|H240", "C|4|0.6", 240, "F1"), ("F3|5|3|H60", "E|5|3", 60, "F3"), ("F3|5|4|H240", "E|5|4", 240, "F3"), ("F3|15|3|H240", "E|15|3", 240, "F3"), ("F3|15|4|H240", "E|15|4", 240, "F3")):
    d = S.prep(ev[(ev.trig == tg) & (ev.H == H)], fam); d["vol"] = S.bins(d, ve, ae) // 9
    for v in (0, 2):
        x = d[d.vol == v]
        if len(x) < 10: continue
        m, lo, hi, p = S.boot(x.net.values, x.cl.values, B=2000)
        by = x.groupby("bucket").agg(n=("net", "size"), net=("net", "mean")).round(1)
        rows.append(dict(cell=cid, vol_tercile=v, n=len(x), gross=x.gross.mean(), cost=x.cost.mean(), net=m, ci_lo=lo, ci_hi=hi, p_one_sided=p,
                         by_year="; ".join(f"{b}: n={r.n} net={r.net}" for b, r in by.iterrows()), coins_pos=int((x.groupby("coin").net.mean() > 0).sum())))
o = pd.DataFrame(rows); o.to_csv(f"{R}/explore_vol_gate.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 200); print(o.round(2).to_string())
