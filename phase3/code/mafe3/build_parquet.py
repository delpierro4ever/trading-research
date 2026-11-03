"""HistData raw M1 zips -> UTC yearly parquet + ingest_stats.json (data-quality only; no return statistics).
HistData timestamps are EST without DST (UTC-5): UTC = EST + 5 h. Rows are re-partitioned by UTC year."""
import io, json, zipfile, glob, os, re
import numpy as np, pandas as pd, polars as pl

RAW = "/home/ubuntu/mafe-data/histdata/raw"; OUT = "/home/ubuntu/mafe-data/histdata/parquet"
STATS = "/home/ubuntu/mafe-data/histdata/ingest_stats.json"
BAND = {"XAUUSD": (300.0, 6000.0), "EURUSD": (0.3, 3.0)}      # wide plausibility band; flag only
stats = {}

def read_zip(p):
    z = zipfile.ZipFile(p)
    assert z.testzip() is None
    n = [x for x in z.namelist() if x.lower().endswith(".csv")]; assert len(n) == 1, z.namelist()
    return pd.read_csv(io.BytesIO(z.read(n[0])), sep=";", header=None, names=["ts", "open", "high", "low", "close", "volume"],
                       dtype={"ts": str})

for sym in ("XAUUSD", "EURUSD"):
    files = sorted(glob.glob(f"{RAW}/{sym}_*.zip")); parts = []; st = {"files": len(files), "raw_rows": 0}
    for f in files:
        d = read_zip(f); st["raw_rows"] += len(d); d["src"] = os.path.basename(f); parts.append(d)
    d = pd.concat(parts, ignore_index=True)
    est = pd.to_datetime(d["ts"], format="%Y%m%d %H%M%S")
    d["time"] = (est + pd.Timedelta(hours=5)).astype("datetime64[ms]")
    st["not_whole_minute"] = int((d["time"].dt.second != 0).sum())
    st["dup_times"] = int(d.duplicated("time").sum())
    dd = d[d.duplicated("time", keep=False)]
    st["dup_conflicting_timestamps"] = int((dd.groupby("time")[["open", "high", "low", "close"]].nunique().max(axis=1) > 1).sum())
    st["dup_by_utc_year"] = {str(k): int(v) for k, v in dd.drop_duplicates("time").groupby(dd.drop_duplicates("time")["time"].dt.year).size().items()}
    d = d.drop_duplicates("time", keep="first").sort_values("time").reset_index(drop=True)
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    bad = (h < np.maximum(o, c) - 1e-9) | (l > np.minimum(o, c) + 1e-9) | (h < l) | (np.minimum.reduce([o, h, l, c]) <= 0) | np.isnan(o + h + l + c)
    lo, hi = BAND[sym]
    out_band = (np.maximum.reduce([o, h, l, c]) > hi) | (np.minimum.reduce([o, h, l, c]) < lo)
    st["bad_ohlc"] = int(bad.sum()); st["outside_wide_band"] = int(out_band.sum()); st["volume_nonzero"] = int((d["volume"] > 0).sum())
    d = d.loc[~bad].reset_index(drop=True)          # structurally invalid bars are dropped (counted above)
    st["rows"] = len(d)
    tm = d["time"]; yr = tm.dt.year.to_numpy()
    st["per_year_rows"] = {str(y): int((yr == y).sum()) for y in sorted(set(yr))}
    # timezone verification (timestamps only): first/last bar of each trading week, as UTC hour:minute
    wk = ((tm - pd.Timestamp("2009-01-04 21:00")) // pd.Timedelta(days=7)).to_numpy()      # weeks cut at Sun 21:00 UTC
    g = d.groupby(wk)["time"].agg(["min", "max"])
    st["week_open_hour"] = {}; st["week_close_hour"] = {}
    for y in sorted(set(g["min"].dt.year)):
        mo = g["min"][g["min"].dt.year == y]; mc = g["max"][g["max"].dt.year == y]
        mo = mo[mo.dt.dayofweek == 6]; mc = mc[mc.dt.dayofweek == 4]
        st["week_open_hour"][str(y)] = {"n": int(len(mo)), "median_utc_hhmm": mo.dt.strftime("%H:%M").sort_values().iloc[len(mo) // 2] if len(mo) else None,
                                        "hour_counts": {k: int(v) for k, v in mo.dt.hour.value_counts().sort_index().items()}}
        st["week_close_hour"][str(y)] = {"n": int(len(mc)), "median_utc_hhmm": mc.dt.strftime("%H:%M").sort_values().iloc[len(mc) // 2] if len(mc) else None,
                                         "hour_counts": {k: int(v) for k, v in mc.dt.hour.value_counts().sort_index().items()}}
    # gaps beyond normal weekend closures: consecutive-bar gaps, excluding weekly closures (Fri->Sun)
    dt_min = (tm.diff().dt.total_seconds() / 60).to_numpy()
    prev = tm.shift(1)
    weekend = ((prev.dt.dayofweek == 4) & tm.dt.dayofweek.isin([6, 0])).to_numpy() & (dt_min >= 24 * 60)
    big = np.nonzero((dt_min >= 60) & ~weekend)[0]
    st["gaps_ge_60min_nonweekend"] = {str(y): int((yr[big] == y).sum()) for y in sorted(set(yr))}
    mid = big[dt_min[big] < 24 * 60]
    st["gap_ge60_start_hour_by_year"] = {str(y): {int(h): int(n) for h, n in prev.iloc[mid][yr[mid] == y].dt.hour.value_counts().sort_index().items()} for y in sorted(set(yr[mid]))}
    st["gaps_ge_6h_nonweekend"] = [f"{prev[i]} -> {tm[i]} ({dt_min[i]/60:.1f}h)" for i in big if dt_min[i] >= 360]
    st["weekend_gap_max_h"] = float(np.nanmax(np.where(weekend, dt_min, np.nan)) / 60)
    st["first_bar_utc"] = str(tm.iloc[0]); st["last_bar_utc"] = str(tm.iloc[-1])
    j10 = d[(d["time"] >= "2010-01-04")].iloc[0]
    st["jan2010_first_open"] = float(j10["open"]); st["jan2010_first_time"] = str(j10["time"])
    os.makedirs(f"{OUT}/{sym}", exist_ok=True)
    for y in sorted(set(yr)):
        x = d.loc[yr == y, ["time", "open", "high", "low", "close", "volume"]]
        pl.from_pandas(x).with_columns(pl.col("time").cast(pl.Datetime("ms")).dt.replace_time_zone("UTC")).write_parquet(f"{OUT}/{sym}/{y}.parquet")
    stats[sym] = st; print(sym, st["rows"], st["bad_ohlc"], st["dup_times"], flush=True)
json.dump(stats, open(STATS, "w"), indent=1, default=str)
