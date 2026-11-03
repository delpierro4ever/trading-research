"""M2/M3/M4 single pass over spot days: anchors (with responses + regime features), 500 ms replay trades per reading, daily summary.
usage: m2_pass.py START END   (sequential; resumable via state files)."""
import sys, os, json, datetime as dt, pickle
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(__file__))
from mafe_core import *
ROOT = "/home/ubuntu/mafe-data/mafe1"
OUT = os.environ.get("MAFE_OUT", f"{ROOT}/out"); os.makedirs(f"{OUT}/anchors", exist_ok=True); os.makedirs(f"{OUT}/trades", exist_ok=True); os.makedirs(f"{OUT}/state", exist_ok=True); os.makedirs(f"{OUT}/daily", exist_ok=True)
D_MS = 500
READINGS = (1, 2, 3, 4, 5)

def pq(d): return f"{ROOT}/parquet/{d}.parquet"
def load(d):
    df = pl.read_parquet(pq(d), columns=["ts", "price", "qty", "buyer_is_maker"])
    return df["ts"].to_numpy(), df["price"].to_numpy(), df["qty"].to_numpy(), df["buyer_is_maker"].to_numpy()
def load_head(d, lim):
    if not os.path.exists(pq(d)): return np.array([], np.int64), np.array([])
    df = pl.scan_parquet(pq(d)).filter(pl.col("ts") < lim).select("ts", "price").collect()
    return df["ts"].to_numpy(), df["price"].to_numpy()

def year_offsets(year):
    offs = {}; c = 0; d = dt.date(year, 1, 1)
    while d.year == year:
        offs[d.isoformat()] = c
        f = f"{ROOT}/parquet/{d}.stats.json"
        if not os.path.exists(f): break
        c += json.load(open(f))["rows"]; d += dt.timedelta(1)
    return offs
OFFS = {y: year_offsets(y) for y in (2023, 2024)}

def process(d, state):
    ds = d.isoformat(); day0 = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)
    ts, price, qty, bm = load(ds); n = len(ts)
    nts, nprice = load_head((d + dt.timedelta(1)).isoformat(), day0 + 86400_000 + 310_000)
    ts_e = np.r_[ts, nts]; price_e = np.r_[price, nprice]
    s = side_of(bm); L = run_length(s)
    # features
    cnt, vol, chg, Pf = bars_for_day(ts, price, qty, day0, state.get("last_price"))
    fs = FeatureState(state.get("tail")); fs.build(cnt, vol, chg, Pf)
    # anchors
    am = anchor_mask(ts); aidx = np.flatnonzero(am)
    am2 = anchor_mask(ts, OFFS[d.year][ds]); n_anch_S2 = int(am2.sum())
    A = dict(date=np.full(len(aidx), ds), i=aidx, ts=ts[aidx], price=price[aidx], side=s[aidx], L=L[aidx])
    for h in HS: A[f"R{h}"] = event_response(price, s, aidx, h)
    A["R300s"] = clock_response(ts_e, price_e, s, aidx)
    A.update(fs.feats(ts[aidx], day0))
    A["hour"] = ((ts[aidx] - day0) // 3600000).astype(np.int8)
    pl.DataFrame(A).write_parquet(f"{OUT}/anchors/{ds}.parquet", compression="zstd")
    # trades
    rows = []
    free = state.get("free", {k: 0 for k in READINGS})
    for k in READINGS:
        sig = np.flatnonzero(L >= k)
        tr, free[k] = replay(ts_e, price_e, sig, s, D_MS, free[k])
        if not tr: continue
        tr = np.array(tr); si, ei, xi = tr[:, 0], tr[:, 1], tr[:, 2]
        sd = s[si].astype(np.float64)
        f = fs.feats(ts[si], day0)
        T = dict(reading=np.full(len(si), k, np.int8), date=np.full(len(si), ds), seq=np.arange(len(si)), sig_ts=ts[si], entry_ts=ts_e[ei], exit_ts=ts_e[xi],
                 side=s[si], L=L[si], p_entry=price_e[ei], p_exit=price_e[xi], gross_bps=sd * (price_e[xi] - price_e[ei]) / price_e[ei] * 1e4,
                 gross_usd=sd * (price_e[xi] - price_e[ei]) * 0.001, hour=((ts[si] - day0) // 3600000).astype(np.int8))
        T.update(f)
        rows.append(pl.DataFrame(T))
    if rows: pl.concat(rows).write_parquet(f"{OUT}/trades/{ds}.parquet", compression="zstd")
    # daily summary
    r1 = np.diff(np.log(Pf)); 
    daily = dict(date=ds, rows=n, n_buy=int((s > 0).sum()), mean_qty=float(qty.mean()), med_qty=float(np.median(qty)), p90_qty=float(np.quantile(qty, .9)),
                 vol_btc=float(qty.sum()), open=float(price[0]), close=float(price[-1]), high=float(price.max()), low=float(price.min()),
                 rv_day_bps=float(np.sqrt((r1 ** 2).sum()) * 1e4), chgfreq=float((np.diff(price) != 0).mean()),
                 n_anch_S1=int(len(aidx)), n_anch_S2=n_anch_S2, n_anch_eff5=int(np.isfinite(A["R5"]).sum()),
                 nL=[int((L == j).sum()) for j in range(1, 6)])
    daily["n_trades"] = {int(r["reading"][0]): int(len(r)) for r in rows}
    json.dump(daily, open(f"{OUT}/daily/{ds}.json", "w"))
    state = dict(last_price=float(price[-1]), tail=fs.newtail, free=free)
    pickle.dump(state, open(f"{OUT}/state/{ds}.pkl", "wb"))
    return state

if __name__ == "__main__":
    a = dt.date.fromisoformat(sys.argv[1]); b = dt.date.fromisoformat(sys.argv[2])
    prev = f"{OUT}/state/{(a - dt.timedelta(1)).isoformat()}.pkl"
    state = pickle.load(open(prev, "rb")) if os.path.exists(prev) else {}
    d = a
    while d <= b:
        if os.path.exists(f"{OUT}/state/{d}.pkl"): state = pickle.load(open(f"{OUT}/state/{d}.pkl", "rb"))
        else: state = process(d, state)
        print(d, flush=True); d += dt.timedelta(1)
