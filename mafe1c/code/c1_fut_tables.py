"""Futures sample (every 7th day) take-all R5 replay: per-year cost/gross summary, and spot on the SAME dates for the proxy check. YEARS via argv (2025 only after the freeze)."""
import sys, os, glob
import numpy as np, pandas as pd, polars as pl
sys.path.insert(0, os.path.dirname(__file__))
from c1_common import *
rng = np.random.default_rng(SEED); years = [int(y) for y in sys.argv[1].split(",")]
def lf(path):
    fs = glob.glob(path)
    d = pl.concat([pl.read_parquet(f) for f in sorted(fs)], how='diagonal_relaxed').to_pandas(); d["day"] = pd.to_datetime(d["date"]); d["year"] = d.day.dt.year; d["month"] = d.day.dt.strftime("%Y-%m"); return costs(d)
fut = lf(f"{ROOT}/c1/fut/trades_ALL/*.parquet")
spot = load_trades(); 
if 2025 in years: spot = pd.concat([spot, lf(f"{ROOT}/c1/p2025/trades_ALL/*.parquet")])
sample_days = set(fut.day.unique())
rows = []
for nm, d in (("futures-sample", fut), ("spot-same-days", spot[spot.day.isin(sample_days)]), ("spot-all-days", spot)):
    for y in years:
        x = d[d.year == y]
        if not len(x): continue
        r = dict(venue=nm, year=y, N=len(x), days=x.day.nunique())
        for c in ("gross_bps", "gross0_bps", "net_K1", "net_K2", "net_K3"):
            da = day_agg(x, [c]); m, lo, hi, _ = boot_mean_ci(da, c, 10000, rng); r[c] = m; r[c + "_lo"] = lo; r[c + "_hi"] = hi
        for c in ("lat100_bps", "lat250_bps", "lat500_bps", "spread_bps", "impact_small_bps", "tick_bps", "cost_K1", "cost_K2", "cost_K3"): r[c] = x[c].mean()
        r["spread_med"] = x.spread_bps.median(); r["spread_p95"] = x.spread_bps.quantile(.95); r["gross_sd"] = x.gross_bps.std(); r["lat500_sd"] = x.lat500_bps.std()
        rows.append(r)
pd.DataFrame(rows).to_csv(f"{RES}/m2_futures_{'_'.join(map(str, years))}.csv", index=False)
print(pd.DataFrame(rows).round(4).T.to_string())
