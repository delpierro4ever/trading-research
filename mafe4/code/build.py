"""Raw csv.gz -> per-coin minute-grid npz (2020-07-01..2024-12-31). Usage: build.py [COIN ...]"""
import os, sys, glob, gzip, numpy as np, pandas as pd
RAW = "/home/ubuntu/mafe-data/mafe4/raw"; OUT = "/home/ubuntu/mafe-data/mafe4/grid"; os.makedirs(OUT, exist_ok=True)
T0 = int(pd.Timestamp("2020-07-01", tz="UTC").timestamp()) // 60
T1 = int(pd.Timestamp("2025-01-01", tz="UTC").timestamp()) // 60   # exclusive
N = T1 - T0
def num(a): return pd.to_numeric(a, errors="coerce")
def build(coin):
    s = coin + "USDT"; g = {k: np.full(N, np.nan) for k in "ohlcv"}; g["nt"] = np.full(N, np.nan); g["tb"] = np.full(N, np.nan)
    for f in sorted(glob.glob(f"{RAW}/klines/{s}/*.csv.gz")):
        d = pd.read_csv(f, header=None, dtype=str)
        d = d[num(d[0]).notna()]
        ts = num(d[0]).astype("int64").values
        if ts.max() > 1e14: ts = ts // 1000          # microsecond stamps (safety)
        i = ts // 60000 - T0; ok = (i >= 0) & (i < N); i = i[ok]
        for k, c in zip("ohlcv", (1, 2, 3, 4, 5)): g[k][i] = num(d[c]).values[ok]
        g["nt"][i] = num(d[8]).values[ok]; g["tb"][i] = num(d[9]).values[ok]
    # funding
    fr = []
    for f in sorted(glob.glob(f"{RAW}/funding/{s}/*.csv.gz")):
        d = pd.read_csv(f, dtype=str); d = d[num(d.iloc[:, 0]).notna()]
        fr.append(np.c_[num(d.iloc[:, 0]).values, num(d.iloc[:, 2]).values])
    fr = np.vstack(fr) if fr else np.zeros((0, 2))
    fr = fr[np.argsort(fr[:, 0])]; fts = np.round(fr[:, 0] / 60000).astype("int64") - T0  # funding minute index (calc_time ~ +2ms)
    # open interest 5-min -> 15-min change at latest stamp <= signal close
    oi = np.full(N // 5 + 2, np.nan)
    for f in sorted(glob.glob(f"{RAW}/metrics/{s}/*.csv.gz")):
        d = pd.read_csv(f, dtype=str)
        t = d.iloc[:, 0]
        tt = (pd.to_datetime(num(t), unit="ms", utc=True) if num(t).notna().all() else pd.to_datetime(t, utc=True))
        m = (tt.astype("int64") // 10**9 // 60).values - T0   # minutes; datetime64 resolution agnostic below
        m = (tt.map(lambda x: int(x.timestamp())).values // 60) - T0
        si = m // 5; ok = (si >= 0) & (si < len(oi)) & (m % 5 == 0)
        oi[si[ok]] = num(d["sum_open_interest"]).values[ok]
    stamp = (np.arange(1, N + 1)) // 5          # boundary = t+1 minute; latest stamp index
    chg = oi[stamp] / oi[np.maximum(stamp - 3, 0)] - 1
    np.savez_compressed(f"{OUT}/{coin}.npz", **g, fund_t=fts, fund_r=fr[:, 1], oi_chg=chg.astype("float32"), has_oi=(~np.isnan(oi)).sum())
    print(coin, "minutes", int((~np.isnan(g['c'])).sum()), "of", N, "first", np.argmax(~np.isnan(g['c'])), "funding", len(fts), "oi stamps", int((~np.isnan(oi)).sum()), flush=True)
if __name__ == "__main__":
    for c in (sys.argv[1:] or "BTC ETH SOL XRP DOGE BNB ADA AVAX LINK LTC".split()): build(c)
