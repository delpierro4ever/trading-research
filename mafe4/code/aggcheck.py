"""aggTrades sample check: 50 BTC discovery days with largest max |r|/sigma among minutes meeting F1 z>=4 & |imb|>=0.6 (OI ignored).
Streams each day zip, keeps only event minutes (+ next minute), deletes the zip. Output results/aggtrades_check.csv"""
import os, sys, io, zipfile, hashlib, urllib.request, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); import engine as E
RES = os.path.join(os.path.dirname(__file__), "..", "results"); TMP = "/home/ubuntu/mafe-data/mafe4/raw/agg"; os.makedirs(TMP, exist_ok=True)
g = E.load("BTC"); F = E.features(g)
with np.errstate(all="ignore"):
    z = np.abs(F["r"]) / F["sig"]
    m = (z >= 4) & (np.sign(F["imb"]) == np.sign(F["r"])) & (np.abs(F["imb"]) >= 0.6)
m[E.DISC_END:] = False
idx = np.flatnonzero(m); days = (E.T0 + idx) // 1440
dfm = pd.DataFrame({"day": days, "t": idx, "z": z[idx]})
top = dfm.groupby("day").z.max().sort_values(ascending=False).head(50)
sample = dfm[dfm.day.isin(top.index)]
sample.assign(date=lambda d: pd.to_datetime(d.day * 86400, unit="s").dt.date).to_csv(f"{RES}/aggtrades_sample_events.csv", index=False)
def get(url):
    with urllib.request.urlopen(url, timeout=120) as r: return r.read()
rows = []
for day in sorted(top.index):
    date = pd.to_datetime(day * 86400, unit="s").strftime("%Y-%m-%d")
    url = f"https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{date}.zip"
    try:
        zb = get(url); ck = get(url + ".CHECKSUM").decode().split()[0]
        if hashlib.sha256(zb).hexdigest() != ck: print("BADSUM", date); continue
    except Exception as ex: print("FAIL", date, ex); continue
    ev = sample[sample.day == day]; mins = {int(t + E.T0) for t in ev.t}; need = mins | {x + 1 for x in mins}
    zf = zipfile.ZipFile(io.BytesIO(zb)); parts = []
    with zf.open(zf.namelist()[0]) as f:
        for ch in pd.read_csv(f, header=None, names=["id", "price", "quantity", "f", "l", "transact_time", "is_buyer_maker"], usecols=["price", "quantity", "transact_time", "is_buyer_maker"], chunksize=2_000_000, dtype=str):
            ch = ch[pd.to_numeric(ch.transact_time, errors="coerce").notna()].copy()
            ch["price"] = ch.price.astype(float); ch["quantity"] = ch.quantity.astype(float); ch["transact_time"] = ch.transact_time.astype("int64")
            mm = (ch.transact_time.astype("int64") // 60000)
            parts.append(ch[mm.isin(need)].assign(mm=mm[mm.isin(need)]))
    tr = pd.concat(parts); tr["is_buyer_maker"] = tr.is_buyer_maker.astype(str).str.lower().eq("true")
    for t in ev.t:
        mn = int(t + E.T0); a = tr[tr.mm == mn]; b = tr[tr.mm == mn + 1]
        if len(a) < 5: continue
        p0, p1 = a.price.iloc[0], a.price.iloc[-1]; mv = np.log(p1 / p0)
        sec = ((a.transact_time.astype("int64") % 60000) // 10000).values
        lp = a.price.values; bins = []; prev = p0
        for s in range(6):
            q = lp[sec == s]
            if len(q): bins.append(np.log(q[-1] / prev)); prev = q[-1]
            else: bins.append(0.0)
        bins = np.array(bins)
        cum = np.cumsum(np.log(lp / p0)) if False else np.log(lp / p0)
        tsec = (a.transact_time.astype("int64").values % 60000) / 1000
        k = np.argmax(np.abs(cum) >= 0.9 * abs(mv)) if abs(mv) > 0 else 0
        buy = a.quantity[~a.is_buyer_maker].sum(); tot = a.quantity.sum()
        rows.append(dict(date=date, t=int(t), kline_r_bps=F["r"][t] * 1e4, trade_r_bps=mv * 1e4, kline_imb=F["imb"][t], trade_imb=2 * buy / tot - 1,
                         max10s_share=np.abs(bins).max() / max(np.abs(bins).sum(), 1e-12), last10s_share=abs(bins[-1]) / max(np.abs(bins).sum(), 1e-12),
                         t90_sec=tsec[k], n_trades=len(a), gap_next_open_bps=(np.log(b.price.iloc[0] / p1) * 1e4 if len(b) else np.nan),
                         next_min_r_bps=(np.log(b.price.iloc[-1] / b.price.iloc[0]) * 1e4 if len(b) else np.nan)))
    print(date, len(ev), flush=True)
pd.DataFrame(rows).to_csv(f"{RES}/aggtrades_check.csv", index=False)
