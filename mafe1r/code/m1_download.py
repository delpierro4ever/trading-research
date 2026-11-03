"""M1: download Binance spot daily aggTrades BTCUSDT, verify checksum, convert to parquet, per-day integrity stats.
Resumable: skips days with an existing stats json. Usage: m1_download.py START END (YYYY-MM-DD, inclusive)"""
import sys, os, io, json, zipfile, hashlib, time, datetime as dt, urllib.request, shutil
import polars as pl
BASE="https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/"
ROOT="/home/ubuntu/mafe-data/mafe1"
CUTOFF=dt.date(2026,9,27)
def fetch(url,dst,tries=6):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url,timeout=120) as r, open(dst,"wb") as f: shutil.copyfileobj(r,f,1<<20)
            return
        except Exception as e:
            time.sleep(2*(i+1)); err=e
    raise RuntimeError(f"fetch failed {url}: {err}")
def day(d):
    s=d.isoformat(); assert d<=CUTOFF
    st=f"{ROOT}/parquet/{s}.stats.json"
    if os.path.exists(st): return
    name=f"BTCUSDT-aggTrades-{s}"; zp=f"{ROOT}/raw/{name}.zip"; cp=zp+".CHECKSUM"
    fetch(BASE+name+".zip.CHECKSUM",cp); fetch(BASE+name+".zip",zp)
    h=hashlib.sha256(open(zp,"rb").read()).hexdigest()
    exp=open(cp).read().split()[0]
    assert h==exp, f"checksum mismatch {s}"
    with zipfile.ZipFile(zp) as z:
        raw=z.read(z.namelist()[0])
    cols=["agg_id","price","qty","first_id","last_id","ts","buyer_is_maker","best_match"]
    df=pl.read_csv(io.BytesIO(raw),has_header=False,new_columns=cols,schema_overrides={"price":pl.Float64,"qty":pl.Float64})
    del raw
    if df["agg_id"][0] is None or isinstance(df["agg_id"][0],str):  # header row present
        df=df.filter(pl.col("agg_id")!="agg_trade_id")
    bm=df["buyer_is_maker"]
    if bm.dtype==pl.String: bm=bm.str.to_lowercase()=="true"
    df=df.select(pl.col("agg_id").cast(pl.Int64),"price","qty",pl.col("first_id").cast(pl.Int64),pl.col("last_id").cast(pl.Int64),
                 pl.col("ts").cast(pl.Int64),bm.alias("buyer_is_maker"))
    tmax=df["ts"].max(); unit="us" if tmax>10**14 else "ms"
    if unit=="us": df=df.with_columns(pl.col("ts")//1000)
    ids=df["agg_id"]; n=len(df)
    dups=n-ids.n_unique(); span=int(ids.max()-ids.min()+1)
    srt=bool((ids.diff().drop_nulls()>0).all()); tsmono=bool((df["ts"].diff().drop_nulls()>=0).all())
    df.write_parquet(f"{ROOT}/parquet/{s}.parquet",compression="zstd")
    stats=dict(date=s,rows=n,dups=dups,gaps=span-n+dups,id_min=int(ids.min()),id_max=int(ids.max()),sorted=srt,ts_monotone=tsmono,ts_unit_in_file=unit,
               ts_min=int(df["ts"].min()),ts_max=int(df["ts"].max()),zip_bytes=os.path.getsize(zp),sha256=h,checksum_ok=True)
    json.dump(stats,open(st,"w"))
    if shutil.disk_usage(ROOT).free<60e9: os.remove(zp)
if __name__=="__main__":
    a=dt.date.fromisoformat(sys.argv[1]); b=dt.date.fromisoformat(sys.argv[2]); d=a
    while d<=b:
        day(d); print(d,flush=True); d+=dt.timedelta(1); time.sleep(0.3)
