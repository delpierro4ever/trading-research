"""Build 22:00-UTC daily closes. HistData M1 zips (EST-no-DST -> UTC = EST+5h) and Binance 1h klines.
Writes /home/ubuntu/mafe-data/trend/daily/dev_val.parquet (dates <= 2022-12-31) and holdout.parquet (>= 2023-01-01; NEVER read by this study)
plus data_quality.json (computed on <=2022 only) and manifest.json (sha256). Usage: python -I build_daily.py"""
import io, json, glob, os, re, zipfile, hashlib, datetime as dt
import numpy as np, pandas as pd

RAW = "/home/ubuntu/mafe-data/trend/raw"; RAW_OLD = "/home/ubuntu/mafe-data/histdata/raw"; OUT = "/home/ubuntu/mafe-data/trend/daily"
SRC = {"EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "USDJPY": "USDJPY", "AUDUSD": "AUDUSD", "USDCAD": "USDCAD", "USDCHF": "USDCHF", "NZDUSD": "NZDUSD",
       "EURJPY": "EURJPY", "GBPJPY": "GBPJPY", "EURGBP": "EURGBP", "AUDJPY": "AUDJPY", "EURCHF": "EURCHF", "XAUUSD": "XAUUSD", "XAGUSD": "XAGUSD",
       "US500": "SPXUSD", "USTEC": "NSXUSD", "DE40": "GRXEUR", "UK100": "UKXGBP", "JP225": "JPXJPY", "XTIUSD": "WTIUSD", "XBRUSD": "BCOUSD"}
CUT = pd.Timedelta(hours=22); SPLIT = pd.Timestamp("2023-01-01")

def read_zip(p):
    z = zipfile.ZipFile(p); n = [x for x in z.namelist() if x.lower().endswith(".csv")]
    return pd.read_csv(io.BytesIO(z.read(n[0])), sep=";", header=None, names=["ts", "o", "h", "l", "c", "v"], dtype={"ts": str})

def daily_from_m1(d):
    t = pd.to_datetime(d["ts"], format="%Y%m%d %H%M%S") + pd.Timedelta(hours=5)      # UTC
    d = pd.DataFrame({"t": t, "c": d["c"].to_numpy()})
    d["date"] = d["t"].dt.normalize(); d = d[(d["t"] - d["date"]) < CUT]
    g = d.groupby("date"); out = pd.DataFrame({"close": g["c"].last(), "last_t": g["t"].last(), "nbars": g.size()})
    return out

def hist_files(name):
    fs = {}
    for base in (RAW_OLD, RAW):
        for f in glob.glob(f"{base}/{name}_*.zip"): fs[os.path.basename(f)] = f
    return [fs[k] for k in sorted(fs)]

series, quality, manifest = {}, {}, {}
for brk, src in SRC.items():
    files = hist_files(src); parts = []
    for f in files:
        manifest[os.path.basename(f)] = hashlib.sha256(open(f, "rb").read()).hexdigest()
        parts.append(daily_from_m1(read_zip(f)))
    if not parts: quality[brk] = {"error": "no files"}; continue
    d = pd.concat(parts).reset_index().sort_values(["date", "last_t"]).drop_duplicates("date", keep="last").set_index("date")
    d = d[d.index.dayofweek < 5]
    valid = (d["nbars"] >= 120) & ((d["last_t"] - d.index) >= pd.Timedelta(hours=16)) & (d["close"] > 0)
    series[brk] = d["close"].where(valid)
    dv = d[d.index < SPLIT]; vv = valid[valid.index < SPLIT]
    quality[brk] = {"src": src, "files": len(files), "first_valid": str(vv[vv].index.min().date()), "last_valid_dev_val": str(vv[vv].index.max().date()),
                    "n_valid_days_dev_val": int(vv.sum()), "n_weekdays_dev_val": int(len(dv)), "years_dev_val": round(float(vv.sum()) / 260.0, 2),
                    "invalid_days_dev_val": int((~vv).sum())}

# crypto from Binance 1h klines (open_time ms UTC; keep bars opening at 21:00 UTC -> close at 22:00)
for brk, fn in (("BTCUSD", "BTCUSDT_1h.json"), ("ETHUSD", "ETHUSDT_1h.json")):
    p = f"{RAW}/{fn}"; manifest[fn] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    k = pd.DataFrame(json.load(open(p)), columns=["t", "o", "h", "l", "c", "v"]); k["t"] = pd.to_datetime(k["t"], unit="ms"); k["c"] = k["c"].astype(float)
    k = k[k["t"].dt.hour == 21]; s = pd.Series(k["c"].to_numpy(), index=k["t"].dt.normalize()); s = s[s.index.dayofweek < 5]
    series[brk] = s; vv = s[s.index < SPLIT]
    quality[brk] = {"src": fn, "first_valid": str(vv.index.min().date()), "n_valid_days_dev_val": int(len(vv)), "years_dev_val": round(len(vv) / 260.0, 2)}

for f in sorted(glob.glob(f"{RAW}/FRED_*.csv")): manifest[os.path.basename(f)] = hashlib.sha256(open(f, "rb").read()).hexdigest()
df = pd.DataFrame(series).sort_index()
# data-integrity rule (fixed before any system result): a close-to-close |log return| > 0.5 in a non-crypto series is a feed splice -> series truncated the day before
trunc = {}
for c in df.columns:
    if c in ("BTCUSD", "ETHUSD"): continue
    lr = np.log(df[c].dropna()).diff().abs(); bad = lr[lr > 0.5]
    if len(bad):
        d0 = bad.index[0]; trunc[c] = f"series truncated from {d0.date()} (log return {float(np.log(df[c].dropna()).diff()[d0]):.3f}; HistData feed switched index)"
        df.loc[df.index >= d0, c] = np.nan
df = df[df.index >= pd.Timestamp("2008-01-01")]
os.makedirs(OUT, exist_ok=True)
df[df.index < SPLIT].to_parquet(f"{OUT}/dev_val.parquet")
ho = df[df.index >= SPLIT]; ho.to_parquet(f"{OUT}/holdout.parquet")
# outlier flags (dev/val only, flag not delete)
r = np.log(df[df.index < SPLIT]).diff()
for c in df.columns:
    x = r[c].dropna(); quality.setdefault(c, {})["abs_logret_gt_8pct"] = [(str(i.date()), round(float(v), 3)) for i, v in x[x.abs() > 0.08].items()]
    quality[c]["max_abs_logret"] = round(float(x.abs().max()), 4)
for c, m in trunc.items(): quality[c]['truncated'] = m
json.dump(quality, open(f"{OUT}/data_quality.json", "w"), indent=1)
manifest["_daily_dev_val.parquet"] = hashlib.sha256(open(f"{OUT}/dev_val.parquet", "rb").read()).hexdigest()
manifest["_daily_holdout.parquet_rows"] = int(len(ho))
json.dump(manifest, open(f"{OUT}/manifest.json", "w"), indent=1)
print(pd.DataFrame(quality).T.reindex(columns=["first_valid", "years_dev_val", "n_valid_days_dev_val", "invalid_days_dev_val"]).to_string())
