"""Reporting-only spread sanity check: Dukascopy XAUUSD daily minute files (BID/ASK .bi5, LZMA, 24-byte big-endian records:
int32 seconds-from-day-start (NOT ms; verified), int32 open, close, low, high, float32 volume; price/1000). Prints/stores median & p95 of (ask open - bid open) in $
by year. Also cross-checks the Dukascopy BID open against HistData BID open for the same UTC minute (timestamp/format sanity)."""
import glob, json, lzma, os, re, datetime as dt
import numpy as np, pandas as pd, polars as pl

RAW = "/home/ubuntu/mafe-data/dukascopy/raw/XAUUSD"
OUT = "/home/ubuntu/mafe-data/histdata/spread_check.json"
REC = np.dtype([("t", ">i4"), ("o", ">i4"), ("c", ">i4"), ("l", ">i4"), ("h", ">i4"), ("v", ">f4")])

def read(p, day):
    b = open(p, "rb").read()
    if not b: return None
    a = np.frombuffer(lzma.decompress(b), REC)
    t = (np.datetime64(day, "s") + a["t"].astype("int64")).astype("datetime64[ms]")   # offset is SECONDS (verified: multiples of 60, 1440 rows/day)
    return pd.DataFrame({"time": t, "open": a["o"] / 1000.0, "close": a["c"] / 1000.0, "low": a["l"] / 1000.0, "high": a["h"] / 1000.0, "vol": a["v"].astype("float64")})

rows, fmt_bad, nday, empty = [], 0, 0, 0
for pb in sorted(glob.glob(f"{RAW}/*/*/*_BID.bi5")):
    pa = pb.replace("_BID", "_ASK")
    if not os.path.exists(pa): continue
    y, m, d = re.search(r"/(\d{4})/(\d{2})/(\d{2})_BID", pb).groups()
    day = dt.date(int(y), int(m), int(d))
    b, a = read(pb, day), read(pa, day)
    if b is None or a is None: empty += 1; continue
    nday += 1
    for df in (b, a):   # format verification: low <= open,close <= high on every record
        fmt_bad += int(((df["low"] > df[["open", "close"]].min(axis=1) + 1e-9) | (df["high"] < df[["open", "close"]].max(axis=1) - 1e-9)).sum())
    j = b.merge(a, on="time", suffixes=("_b", "_a"))
    j = j[(j["vol_b"] > 0) & (j["vol_a"] > 0)]
    j["spread"] = j["open_a"] - j["open_b"]; rows.append(j[["time", "open_b", "spread"]])
df = pd.concat(rows, ignore_index=True)
df["year"] = df["time"].dt.year
res = {"day_files_paired": nday, "empty_pairs": empty, "format_violations": fmt_bad, "first": str(df["time"].min()), "last": str(df["time"].max()), "by_year": {}}
for y, g in df.groupby("year"):
    s = g["spread"].to_numpy()
    res["by_year"][int(y)] = {"minutes": int(len(s)), "days": int(g["time"].dt.date.nunique()), "median_usd": float(np.median(s)), "p95_usd": float(np.quantile(s, 0.95)),
                              "mean_usd": float(s.mean()), "share_negative": float((s < 0).mean()), "mean_price": float(g["open_b"].mean())}
# cross-check against HistData bid open (same UTC minute), only for Dukascopy dates (all < 2012)
hd = pl.read_parquet([f for f in [f"/home/ubuntu/mafe-data/histdata/parquet/XAUUSD/{y}.parquet" for y in (2009, 2010, 2011)]]).to_pandas()
hd["time"] = hd["time"].dt.tz_localize(None).astype("datetime64[ms]")
m = df.merge(hd[["time", "open"]], on="time")
if len(m):
    diff = (m["open_b"] - m["open"]).to_numpy()
    res["histdata_crosscheck"] = {"matched_minutes": int(len(m)), "median_abs_diff_usd": float(np.median(np.abs(diff))), "p95_abs_diff_usd": float(np.quantile(np.abs(diff), .95)),
                                  "median_signed_diff_usd": float(np.median(diff))}
json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps(res, indent=1))
