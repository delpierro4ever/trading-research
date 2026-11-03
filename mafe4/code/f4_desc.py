"""Descriptive F4 tables (discovery, not tested): cost/gross by vol tercile, activity tercile, hour bucket."""
import json, numpy as np, pandas as pd, stats as S
from discover import load, R
ev = load(); fr = json.load(open(f"{R}/f4_frozen_models.json")); ve, ae = fr["vol_edges"], fr["act_edges"]
out = []
for cid, tg, H, fam in (("F1|4|0.6|H30", "C|4|0.6", 30, "F1"), ("F3|5|3|H60", "E|5|3", 60, "F3"), ("F3|15|4|H240", "E|15|4", 240, "F3")):
    d = S.prep(ev[(ev.trig == tg) & (ev.H == H)], fam); b = S.bins(d, ve, ae); d["vol"] = b // 9; d["act"] = (b // 3) % 3; d["hb"] = b % 3
    for col in ("vol", "act", "hb"):
        t = d.groupby(col).agg(n=("net", "size"), gross=("gross", "mean"), cost=("cost", "mean"), net=("net", "mean"), net_med=("net", "median"), mfe=("mfe", "mean")).round(2); t.insert(0, "cell", cid); t.insert(1, "by", col); out.append(t.reset_index().rename(columns={col: "bin"}))
o = pd.concat(out); o.to_csv(f"{R}/f4_descriptive_bins.csv", index=False); print(o.to_string())
