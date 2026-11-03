"""M2 reconstruction check on USD-M futures 2026-09-23/24 (tape replay, trade-price fills)."""
import sys, os, io, zipfile, json, datetime as dt
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(__file__))
from mafe_core import *
F = "/home/ubuntu/mafe-data/mafe1/fut"
frames = []
for d in ["2026-09-23", "2026-09-24"]:
    z = zipfile.ZipFile(f"{F}/BTCUSDT-aggTrades-{d}.zip"); frames.append(pl.read_csv(io.BytesIO(z.read(z.namelist()[0]))))
df = pl.concat(frames)
ts = df["transact_time"].to_numpy(); price = df["price"].to_numpy(); qty = df["quantity"].to_numpy(); bm = df["is_buyer_maker"].to_numpy()
ids = df["agg_trade_id"].to_numpy(); gaps = int(ids[-1] - ids[0] + 1 - len(ids))
s = side_of(bm); L = run_length(s)
t0 = int(dt.datetime(2026, 9, 23, 10, 27, tzinfo=dt.timezone.utc).timestamp() * 1000)
t1 = int(dt.datetime(2026, 9, 24, 1, 51, 59, 999000, tzinfo=dt.timezone.utc).timestamp() * 1000)
res = dict(rows=len(ts), id_gaps=gaps, share_L_ge={str(k): float((L >= k).mean()) for k in range(1, 6)},
           share_L_ge_window={str(k): float((L[(ts >= t0) & (ts <= t1)] >= k).mean()) for k in range(1, 6)}, readings={})
rng = np.random.default_rng(1)
TICK = 0.10
for k in range(1, 6):
    sig = np.flatnonzero((L >= k) & (ts >= t0) & (ts <= t1))
    rk = {}; sigsets = {}
    for dly in (100, 250, 500):
        tr, _ = replay(ts, price, sig, s, dly, t0)
        tr = [t for t in tr if ts[t[2]] <= t1]
        if not tr: continue
        a = np.array(tr); si, ei, xi = a[:, 0], a[:, 1], a[:, 2]
        sd = s[si].astype(float)
        g_usd = sd * (price[xi] - price[ei]) * 0.001
        cost_bps = 2 * 1.0 + 2 * 0.05 + TICK / price[ei] * 1e4
        cost_usd = cost_bps * 1e-4 * price[ei] * 0.001
        net = g_usd - cost_usd
        boot = [rng.choice(g_usd, len(g_usd)).mean() for _ in range(2000)]
        th = np.array_split(net, 3)
        rk[str(dly)] = dict(trades=len(tr), gross_usd=float(g_usd.sum()), cost_usd=float(cost_usd.sum()), net_usd=float(net.sum()),
                            cost_per_trade_usd=float(cost_usd.mean()), cost_bps_mean=float(cost_bps.mean()), net_win=float((net > 0).mean()), gross_win=float((g_usd > 0).mean()),
                            gross_per_trade_ci_iid=[float(np.quantile(boot, .025)), float(np.quantile(boot, .975))],
                            net_thirds_mean=[float(x.mean()) for x in th], first_entry=int(ts[ei[0]]))
        sigsets[dly] = set(int(x) for x in si)
    rk["distinct_signals_union"] = len(set().union(*sigsets.values())) if sigsets else 0
    res["readings"][f"R{k}"] = rk
json.dump(res, open(os.path.join(os.path.dirname(__file__), "..", "results", "m2_futures_check.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
