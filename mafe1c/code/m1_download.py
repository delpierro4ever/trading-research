"""MAFE-1C M1: download Binance daily aggTrades BTCUSDT (spot or USD-M futures), verify SHA-256, convert to parquet, per-day integrity stats.
Only integrity statistics are computed here (no price/outcome statistic).  Hard cutoff 2025-12-31 (governance: 2026 untouched).
usage: m1_download.py spot START END            (every day, inclusive)
       m1_download.py fut  YEAR [YEAR ...]      (pre-declared sample: day-of-year 1,8,15,... i.e. every 7th day of the year)"""
import sys, os, io, json, zipfile, hashlib, time, datetime as dt, urllib.request, shutil
import polars as pl
ROOT = "/home/ubuntu/mafe-data/mafe1"
CUTOFF = dt.date(2025, 12, 31)
CFG = {"spot": (f"https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/", f"{ROOT}", ["agg_id","price","qty","first_id","last_id","ts","buyer_is_maker","best_match"]),
       "fut": (f"https://data.binance.vision/data/futures/um/daily/aggTrades/BTCUSDT/", f"{ROOT}/futs", ["agg_id","price","qty","first_id","last_id","ts","buyer_is_maker"])}
def fetch(url, dst, tries=6):
    err = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r, open(dst, "wb") as f: shutil.copyfileobj(r, f, 1 << 20)
            return
        except Exception as e:
            time.sleep(2 * (i + 1)); err = e
    raise RuntimeError(f"fetch failed {url}: {err}")
def day(kind, d):
    base, root, cols = CFG[kind]
    s = d.isoformat(); assert d <= CUTOFF, "governance cutoff"
    os.makedirs(f"{root}/raw", exist_ok=True); os.makedirs(f"{root}/parquet", exist_ok=True)
    st = f"{root}/parquet/{s}.stats.json"
    if os.path.exists(st): return
    name = f"BTCUSDT-aggTrades-{s}"; zp = f"{root}/raw/{name}.zip"; cp = zp + ".CHECKSUM"
    fetch(base + name + ".zip.CHECKSUM", cp); fetch(base + name + ".zip", zp)
    h = hashlib.sha256(open(zp, "rb").read()).hexdigest(); exp = open(cp).read().split()[0]
    assert h == exp, f"checksum mismatch {s}"
    with zipfile.ZipFile(zp) as z: raw = z.read(z.namelist()[0])
    hdr = raw[:20].decode("ascii", "ignore")[:1].isalpha()  # header row present (futures; spot 2025?)
    df = pl.read_csv(io.BytesIO(raw), has_header=hdr, new_columns=cols, schema_overrides={"price": pl.Float64, "qty": pl.Float64}); del raw
    bm = df["buyer_is_maker"]
    if bm.dtype == pl.String: bm = bm.str.to_lowercase() == "true"
    df = df.select(pl.col("agg_id").cast(pl.Int64), "price", "qty", pl.col("first_id").cast(pl.Int64), pl.col("last_id").cast(pl.Int64), pl.col("ts").cast(pl.Int64), bm.alias("buyer_is_maker"))
    unit = "us" if df["ts"].max() > 10**14 else "ms"
    if unit == "us": df = df.with_columns(pl.col("ts") // 1000)
    ids = df["agg_id"]; n = len(df); dups = n - ids.n_unique(); span = int(ids.max() - ids.min() + 1)
    srt = bool((ids.diff().drop_nulls() > 0).all()); tsm = bool((df["ts"].diff().drop_nulls() >= 0).all())
    day0 = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)
    in_day = bool(((df["ts"] >= day0) & (df["ts"] < day0 + 86400000)).all())
    df.write_parquet(f"{root}/parquet/{s}.parquet", compression="zstd")
    json.dump(dict(kind=kind, date=s, rows=n, dups=dups, gaps=span - n + dups, id_min=int(ids.min()), id_max=int(ids.max()), sorted=srt, ts_monotone=tsm, ts_in_utc_day=in_day,
                   ts_unit_in_file=unit, ts_min=int(df["ts"].min()), ts_max=int(df["ts"].max()), zip_bytes=os.path.getsize(zp), sha256=h, checksum_ok=True), open(st, "w"))
    if kind == "fut" or shutil.disk_usage(ROOT).free < 60e9: os.remove(zp)
def fut_days(year):
    d = dt.date(year, 1, 1)
    while d.year == year: yield d; d += dt.timedelta(7)
if __name__ == "__main__":
    kind = sys.argv[1]
    if kind == "spot":
        d = dt.date.fromisoformat(sys.argv[2]); b = dt.date.fromisoformat(sys.argv[3])
        while d <= b: day("spot", d); print("spot", d, flush=True); d += dt.timedelta(1); time.sleep(0.3)
    else:
        for y in map(int, sys.argv[2:]):
            for d in fut_days(y): day("fut", d); print("fut", d, flush=True); time.sleep(0.3)
