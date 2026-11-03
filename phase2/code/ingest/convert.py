"""Convert raw Binance zips -> monthly parquet. Writes per-file stats to /home/ubuntu/mafe-data/convert_stats.json"""
import re, io, os, sys, json, glob, zipfile, collections
import polars as pl
RAW="/home/ubuntu/mafe-data/raw"; OUT="/home/ubuntu/mafe-data/parquet"
KL=["open_time","open","high","low","close","volume","close_time","quote_volume","count","taker_buy_volume","taker_buy_quote_volume","ignore"]
SPEC={
 "klines_1m":dict(cols=KL,key=["open_time"],tcols=["open_time","close_time"],ints=["count"],drop=["ignore"],sort="open_time"),
 "premiumIndexKlines_1m":dict(cols=KL,key=["open_time"],tcols=["open_time","close_time"],ints=["count"],drop=["ignore"],sort="open_time"),
 "fundingRate":dict(cols=["calc_time","funding_interval_hours","last_funding_rate"],key=["calc_time"],tcols=["calc_time"],ints=["funding_interval_hours"],drop=[],sort="calc_time"),
 "metrics":dict(cols=["create_time","symbol","sum_open_interest","sum_open_interest_value","count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio","count_long_short_ratio","sum_taker_long_short_vol_ratio"],key=["create_time"],tcols=["create_time"],ints=[],strs=["symbol"],drop=[],sort="create_time"),
 "bookDepth":dict(cols=["timestamp","percentage","depth","notional"],key=["timestamp","percentage"],tcols=["timestamp"],ints=[],drop=[],sort="timestamp"),
}
def read(zb,spec):
    z=zipfile.ZipFile(zb); raw=z.read(z.namelist()[0])
    first=raw[:200].split(b"\n")[0].decode()
    hdr=not first[:1].isdigit()
    df=pl.read_csv(io.BytesIO(raw),has_header=hdr,infer_schema_length=0)
    if hdr:
        got=[c.strip() for c in df.columns]; assert got==spec["cols"],(got,spec["cols"]); df.columns=got
    else:
        assert df.width==len(spec["cols"]); df.columns=spec["cols"]
    exprs=[]
    for c in spec["cols"]:
        if c in spec["tcols"]:
            s=pl.col(c)
            if c in ("timestamp","create_time"):
                exprs.append(s.str.strptime(pl.Datetime("ms"),"%Y-%m-%d %H:%M:%S").dt.replace_time_zone("UTC").alias(c))
            else:
                i=s.cast(pl.Int64)
                i=pl.when(i>=10**14).then(i//1000).otherwise(i)   # microseconds -> ms
                exprs.append(pl.from_epoch(i,time_unit="ms").dt.replace_time_zone("UTC").cast(pl.Datetime("ms","UTC")).alias(c))
        elif c in spec["ints"]: exprs.append(pl.col(c).cast(pl.Int64))
        elif c in spec.get("strs",[]): pass
        else: exprs.append(pl.when(pl.col(c).str.strip_chars()=="").then(None).otherwise(pl.col(c)).cast(pl.Float64).alias(c))   # empty field -> null; other junk still raises
    df=df.with_columns(exprs)
    return df.drop(spec["drop"])
def main():
    stats=[]
    for ds,spec in SPEC.items():
        for sd in sorted(glob.glob(f"{RAW}/{ds}/*")):
            sym=os.path.basename(sd); months=collections.defaultdict(list)
            for f in sorted(glob.glob(sd+"/*.zip")):
                ym=re.search(r"(\d{4}-\d{2})(-\d{2})?\.zip$",f).group(1); months[ym].append(f)
            od=f"{OUT}/{ds}/{sym}"; os.makedirs(od,exist_ok=True)
            for ym,fs in sorted(months.items()):
                parts=[]
                for f in fs:
                    d=read(f,spec); parts.append(d)
                    stats.append(dict(dataset=ds,symbol=sym,file=os.path.basename(f),rows=d.height,
                       first=str(d[spec["sort"]].min()),last=str(d[spec["sort"]].max())))
                df=pl.concat(parts); n0=df.height
                df=df.unique(subset=spec["key"],keep="first",maintain_order=True).sort(spec["key"])
                if n0-df.height: stats.append(dict(dataset=ds,symbol=sym,file=ym,dups_removed=n0-df.height))
                df.write_parquet(f"{od}/{ym}.parquet",compression="zstd")
            print(ds,sym,len(months),flush=True)
    json.dump(stats,open("/home/ubuntu/mafe-data/convert_stats.json","w"))
if __name__=="__main__":
    main()
