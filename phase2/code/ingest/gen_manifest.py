import json, os, glob, duckdb, datetime as dt
D="/home/ubuntu/mafe-data"; PQ=f"{D}/parquet"; RAW=f"{D}/raw"
TC={"klines_1m":"open_time","premiumIndexKlines_1m":"open_time","fundingRate":"calc_time","metrics":"create_time","bookDepth":"timestamp"}
STEP={"klines_1m":60_000,"premiumIndexKlines_1m":60_000,"metrics":300_000}
stats=json.load(open(f"{D}/convert_stats.json")); rej=json.load(open(f"{D}/rejects.json"))
keys=json.load(open(f"{D}/keys.json"))
con=duckdb.connect(); con.execute("PRAGMA threads=2; PRAGMA memory_limit='2GB'")
def du(p): return sum(os.path.getsize(f) for f in glob.glob(p+"/**",recursive=True) if os.path.isfile(f))
def h(n):
    for u in "B KB MB GB".split():
        if n<1024: return f"{n:.1f} {u}"
        n/=1024
    return f"{n:.1f} TB"
def ep(x): return dt.datetime.fromtimestamp(x/1000,dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
out=["# DATA MANIFEST — Binance USD-M futures (phase 2 ingestion)","",
f"Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC by `phase2/code/ingest/gen_manifest.py`. Source: https://data.binance.vision/data/futures/um/. "
"All timestamps UTC, normalised to `datetime[ms, UTC]`. Contains only row counts and timestamp coverage (no price/outcome statistics).","",
f"Checksum policy: every zip verified against its sibling `.CHECKSUM` (sha256). Files in scope per S3 listing: {len(keys)}. Rejected after 5 retries: **{len(rej)}**.",""]
for r in rej: out.append(f"- REJECT {r}")
out+=["","## Layouts and cadence notes","",
"- **klines_1m / premiumIndexKlines_1m**: 12 CSV columns; `ignore` (always 0) dropped. Kept: open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume. Header row present in some files only (detected per file). Timestamps ms; values >=1e14 (µs) are divided by 1000.",
"- **fundingRate**: calc_time, funding_interval_hours, last_funding_rate (one row per funding event).",
"- **metrics**: create_time (string UTC, parsed), symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio. Header always present. Nominal cadence 5 min.",
"- **bookDepth**: timestamp (string UTC, parsed), percentage (signed depth band, -5..-1 and 1..5), depth (base-asset quantity within band), notional (quote value within band). 10 rows per snapshot; dedup key (timestamp, percentage).",
"- Duplicates: only metrics/BTCUSDT 2020-09..2021-05 (9 months, 75,255 rows) — those daily files list every 5-min row twice with byte-identical values (verified for 2020-09: distinct rows == distinct timestamps); first occurrence kept. No other dataset had duplicates.",
"- metrics note: some CSV fields are empty strings (e.g. top-trader ratios in early files) and are stored as null.",
"- Parquet layout: `/home/ubuntu/mafe-data/parquet/<dataset>/<SYM>/<YYYY-MM>.parquet` (zstd); daily files merged into their month. Raw: `/home/ubuntu/mafe-data/raw/<dataset>/<SYM>/` (monthly and daily zips share a directory).",
"","## Per dataset / symbol",""]
tot_raw=tot_pq=0
for ds in TC:
  for sym in ("BTCUSDT","ETHUSDT"):
    rp=f"{RAW}/{ds}/{sym}"; pp=f"{PQ}/{ds}/{sym}"
    if not os.path.isdir(pp): continue
    t=TC[ds]; nz=len(glob.glob(rp+"/*.zip"))
    rawb=du(rp); pqb=du(pp); tot_raw+=rawb; tot_pq+=pqb
    nrej=sum(1 for k,_ in rej if f"/{sym}/" in k and k.split("/")[4]+("_1m" if "/1m/" in k else "")==ds)
    dups=sum(s["dups_removed"] for s in stats if s["dataset"]==ds and s["symbol"]==sym and "dups_removed" in s)
    rows_in=sum(s["rows"] for s in stats if s["dataset"]==ds and s["symbol"]==sym and "rows" in s)
    g=f"read_parquet('{pp}/*.parquet')"
    n,mn,mx=con.execute(f"select count(*),epoch_ms(min({t})),epoch_ms(max({t})) from {g}").fetchone()
    cols=con.execute(f"describe select * from {g}").fetchall()
    out+=[f"### {ds} / {sym}","",f"- raw zip files: {nz}; checksum failures/rejects: {nrej}",
          f"- rows in parquet: {n:,} (raw rows read {rows_in:,}; duplicates removed {dups:,})",
          f"- first / last timestamp: {ep(mn)} / {ep(mx)}",
          f"- bytes: raw {h(rawb)}, parquet {h(pqb)}",
          "- schema: "+", ".join(f"`{c[0]}` {c[1]}" for c in cols)]
    if ds in STEP:
        st=STEP[ds]
        gaps=con.execute(f"""with s as (select epoch_ms({t}) t from {g}), l as (select t, lag(t) over (order by t) p from s)
          select p+{st} as a, t-{st} as b, (t-p)//{st}-1 as miss from l where p is not null and t-p>{st} order by a""").fetchall()
        exp=(mx-mn)//st+1
        out.append(f"- expected grid slots in span at {st//1000}s: {exp:,}; present {n:,}; missing slots {exp-n:,}; gap ranges {len(gaps)}")
        dist=con.execute(f"""with s as (select epoch_ms({t}) t from {g}), l as (select t-lag(t) over (order by t) d from s) select d/1000 sec,count(*) from l where d is not null group by 1 order by 2 desc limit 6""").fetchall()
        out.append("- observed spacing (seconds: count), top: "+", ".join(f"{a:g}: {b:,}" for a,b in dist))
        if gaps:
            out.append(f"- largest gaps (up to 15 of {len(gaps)}):")
            for a,b,m in sorted(gaps,key=lambda x:-x[2])[:15]: out.append(f"  - {ep(a)} .. {ep(b)} ({m:,} slots)")
    elif ds=="bookDepth":
        dist=con.execute(f"""with s as (select distinct epoch_ms({t}) t from {g}), l as (select t-lag(t) over (order by t) d from s) select d/1000 sec,count(*) from l where d is not null group by 1 order by 2 desc limit 8""").fetchall()
        ns=con.execute(f"select count(distinct {t}) from {g}").fetchone()[0]
        lv=con.execute(f"select list(distinct percentage order by percentage) from {g}").fetchone()[0]
        pr=con.execute(f"select min(c),max(c) from (select count(*) c from {g} group by {t})").fetchone()
        out+=[f"- distinct snapshots: {ns:,}; rows per snapshot min/max: {pr[0]}/{pr[1]}; levels: {lv}",
              "- spacing between consecutive snapshots (seconds: count), top: "+", ".join(f"{a:g}: {b:,}" for a,b in dist)]
        yr=con.execute(f"""with s as (select distinct {t} t from {g}) select year(t), count(*), round(86400.0*count(distinct date_trunc('day',t))/count(*),1) from s group by 1 order by 1""").fetchall()
        out.append("- per year (snapshots / avg seconds per snapshot over days present): "+"; ".join(f"{a}: {b:,} / {c}s" for a,b,c in yr))
    elif ds=="fundingRate":
        dist=con.execute(f"select funding_interval_hours,count(*) from {g} group by 1 order by 1").fetchall()
        out.append("- funding_interval_hours counts: "+", ".join(f"{a}: {b:,}" for a,b in dist))
    days=con.execute(f"select distinct cast({t} as date)::varchar from {g} order by 1").fetchall()
    days=[dt.date.fromisoformat(d[0]) for d in days]
    miss=[(a+dt.timedelta(1),b-dt.timedelta(1)) for a,b in zip(days,days[1:]) if (b-a).days>1]
    md=sum((b-a).days+1 for a,b in miss)
    out.append(f"- calendar days with data: {len(days):,} (first {days[0]}, last {days[-1]}); missing days inside span: {md} in {len(miss)} range(s)")
    for a,b in miss[:25]: out.append(f"  - {a} .. {b}")
    if len(miss)>25: out.append(f"  - ... {len(miss)-25} more ranges")
    out.append("")
out+=["## Totals","",f"- raw: {h(tot_raw)}; parquet: {h(tot_pq)}",""]
open("/home/ubuntu/mafe-research-archive/phase2/docs/DATA_MANIFEST.md","w").write("\n".join(out))
print("ok")
