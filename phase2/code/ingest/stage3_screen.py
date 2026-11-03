"""Stage 3 step 1a: outcome-blind universe screen. Only statistic computed: total 2023 quote_volume per symbol."""
import re, os, io, sys, json, zipfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import polars as pl
sys.path.insert(0, os.path.dirname(__file__))
import download as dl
OUTD = "/home/ubuntu/mafe-data/stage3"; os.makedirs(OUTD, exist_ok=True)
STABLE = {"USDC","BUSD","TUSD","FDUSD","USDP","DAI"}
EXCL = {"BTCUSDT","ETHUSDT"}

def prefixes(prefix):
    out=[]; marker=""
    while True:
        r=dl.sess.get(dl.S3,params={"delimiter":"/","prefix":prefix,"marker":marker},timeout=60); r.raise_for_status()
        root=ET.fromstring(r.content)
        out+=[c.find(dl.NS+"Prefix").text for c in root.findall(dl.NS+"CommonPrefixes")]
        if root.find(dl.NS+"IsTruncated").text=="true":
            nm=root.find(dl.NS+"NextMarker"); marker=nm.text if nm is not None else out[-1]
        else: break
    return out

def main():
    ps = prefixes("data/futures/um/monthly/klines/")
    syms = sorted(p.split("/")[-2] for p in ps)
    print("all symbols", len(syms), flush=True)
    usdt = [s for s in syms if re.fullmatch(r"[A-Z0-9]+USDT", s)]
    rows=[]
    for s in usdt:
        keys = dl.list_keys(f"data/futures/um/monthly/klines/{s}/1m/")
        months = sorted(re.search(r"-(\d{4}-\d{2})\.zip$",k).group(1) for k in keys)
        rows.append(dict(symbol=s, first_month=months[0] if months else None, last_month=months[-1] if months else None, n_months=len(months)))
    df = pl.DataFrame(rows, infer_schema_length=None)
    df = df.with_columns(base=pl.col("symbol").str.slice(0, pl.col("symbol").str.len_chars()-4))
    df = df.with_columns(
        has_hist=(pl.col("first_month").is_not_null() & (pl.col("first_month") <= "2021-12")),
        excluded=pl.col("symbol").is_in(list(EXCL)) | pl.col("base").is_in(list(STABLE)))
    df.write_csv(f"{OUTD}/listing.csv")
    cand = df.filter(pl.col("has_hist") & ~pl.col("excluded"))["symbol"].to_list()
    print("candidates", len(cand), flush=True)
    jobs=[f"data/futures/um/monthly/klines/{s}/1m/{s}-1m-2023-{m:02d}.zip" for s in cand for m in range(1,13)]
    avail=set()
    for s in cand:
        for k in dl.list_keys(f"data/futures/um/monthly/klines/{s}/1m/"): avail.add(k)
    jobs=[j for j in jobs if j in avail]
    # also first month file for listing timestamp
    first={r["symbol"]:r["first_month"] for r in rows}
    jobs+= [f"data/futures/um/monthly/klines/{s}/1m/{s}-1m-{first[s]}.zip" for s in cand]
    jobs = sorted(set(jobs))
    print("jobs", len(jobs), flush=True)
    fails=[]
    with ThreadPoolExecutor(4) as ex:
        for i,(k,st) in enumerate(ex.map(dl.job, jobs)):
            if st!="ok": fails.append((k,st)); print("REJECT",k,st,flush=True)
            if i%100==0: print(i,len(jobs),flush=True)
    json.dump(fails, open(f"{OUTD}/screen_rejects.json","w"))
    vol=[]
    for s in cand:
        tot=0.0; nm=0
        for m in range(1,13):
            z=f"{dl.RAW}/klines_1m/{s}/{s}-1m-2023-{m:02d}.zip"
            if not os.path.exists(z): continue
            raw=zipfile.ZipFile(z).read(zipfile.ZipFile(z).namelist()[0])
            hdr=not raw[:50].decode().startswith(tuple("0123456789"))
            d=pl.read_csv(io.BytesIO(raw),has_header=hdr,infer_schema_length=0)
            tot+=float(d[:,7].cast(pl.Float64).sum()); nm+=1
        # listing timestamp = first open_time of the first monthly file
        z=f"{dl.RAW}/klines_1m/{s}/{s}-1m-{first[s]}.zip"
        raw=zipfile.ZipFile(z).read(zipfile.ZipFile(z).namelist()[0])
        hdr=not raw[:50].decode().startswith(tuple("0123456789"))
        d=pl.read_csv(io.BytesIO(raw),has_header=hdr,infer_schema_length=0)
        t0=int(d[:,0].cast(pl.Int64).min())
        if t0>=10**14: t0//=1000
        vol.append(dict(symbol=s, vol2023=tot, months2023=nm, first_open_ms=t0))
    v=pl.DataFrame(vol).sort("vol2023",descending=True).with_columns(rank=pl.int_range(1,pl.len()+1))
    v.write_csv(f"{OUTD}/ranking.csv")
    print(v.head(60))
main()
