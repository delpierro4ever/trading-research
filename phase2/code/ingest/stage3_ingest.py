"""Stage 3 step 1b+2: coverage/replacement rule, universe.csv, ingest (klines 1m, premium 1m, funding) 2021-11..2024-12, manifest section.
Reuses download.job (sha256 checksum verified) and convert.read/SPEC. No returns are computed here."""
import os, re, sys, json, glob, shutil, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import numpy as np, polars as pl, duckdb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import download as dl, convert as cv
D = "/home/ubuntu/mafe-data"; OUTD = f"{D}/stage3"
ROOT = "/home/ubuntu/mafe-research-archive/phase2"
M0, M1 = "2021-11", "2024-12"
WE = dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc)
DS = {"klines_1m": ("klines", "/1m/"), "premiumIndexKlines_1m": ("premiumIndexKlines", "/1m/"), "fundingRate": ("fundingRate", "/")}


def keys_for(sym, ds):
    nm, sub = DS[ds]
    ks = dl.list_keys(f"data/futures/um/monthly/{nm}/{sym}{sub}")
    out = []
    for k in ks:
        ym = re.search(r"-(\d{4}-\d{2})\.zip$", k).group(1)
        if M0 <= ym <= M1:
            out.append(k)
    return out


def convert_symbol(sym, ds):
    spec = cv.SPEC[ds]; sd = f"{dl.RAW}/{ds}/{sym}"; od = f"{D}/parquet/{ds}/{sym}"; os.makedirs(od, exist_ok=True)
    for f in sorted(glob.glob(sd + "/*.zip")):
        ym = re.search(r"(\d{4}-\d{2})\.zip$", f).group(1)
        if not (M0 <= ym <= M1):
            continue
        df = cv.read(f, spec).unique(subset=spec["key"], keep="first", maintain_order=True).sort(spec["key"])
        df.write_parquet(f"{od}/{ym}.parquet", compression="zstd")


def load_ts(sym, ds, col):
    fs = sorted(glob.glob(f"{D}/parquet/{ds}/{sym}/*.parquet"))
    if not fs:
        return np.array([], dtype="datetime64[ms]")
    return pl.scan_parquet(fs).select(col).unique().sort(col).collect()[col].to_numpy().astype("datetime64[ms]")


def coverage(sym, listing_ms):
    ws = max(dt.datetime(2022, 1, 1, tzinfo=dt.timezone.utc), dt.datetime.fromtimestamp(listing_ms / 1000, dt.timezone.utc) + dt.timedelta(days=30))
    kt = load_ts(sym, "klines_1m", "open_time")
    last = int(kt.max().astype("int64")) if len(kt) else 0
    we = min(WE, dt.datetime.fromtimestamp(last / 1000, dt.timezone.utc) + dt.timedelta(minutes=1))
    w0 = np.datetime64(ws.replace(tzinfo=None), "ms"); w1 = np.datetime64(we.replace(tzinfo=None), "ms")
    exp = int((w1 - w0) / np.timedelta64(1, "m"))
    pt = load_ts(sym, "premiumIndexKlines_1m", "open_time"); pt = pt[(pt >= w0) & (pt < w1)]
    kk = kt[(kt >= w0) & (kt < w1)]
    pm = 1 - len(pt) / exp if exp > 0 else 1.0
    km = 1 - len(kk) / exp if exp > 0 else 1.0
    ft = load_ts(sym, "fundingRate", "calc_time")
    if len(ft) and exp > 0:
        fd = pl.scan_parquet(sorted(glob.glob(f"{D}/parquet/fundingRate/{sym}/*.parquet"))).select("funding_interval_hours").collect()
        iv = np.timedelta64(int(np.median(fd["funding_interval_hours"].to_numpy())), "h")
        f_in = ft[(ft >= w0) & (ft <= w1)]
        pts = np.concatenate([np.array([w0]), f_in, np.array([w1])])
        gaps = np.diff(pts)
        unc = np.maximum(gaps - iv * 3 // 2, np.timedelta64(0, "ms")).sum()
        fm = float(unc / (w1 - w0))
    else:
        fm = 1.0
    return dict(window_start=str(ws), window_end=str(we), prem_missing_frac=pm, kline_missing_frac=km, fund_missing_frac=fm,
                n_prem=int(len(pt)), expected_minutes=exp)


def fetch_symbol(sym):
    res = []
    for ds in DS:
        for k in keys_for(sym, ds):
            res.append(dl.job(k))
    return sym, res


def main():
    rk = pl.read_csv(f"{OUTD}/ranking.csv")
    syms = rk["symbol"].to_list(); listing = dict(zip(rk["symbol"], rk["first_open_ms"]))
    chosen = []; info = {}; fails = []; pos = 0
    while len(chosen) < 25 and pos < len(syms):
        need = 25 - len(chosen)
        batch = syms[pos:pos + need]; pos += len(batch)
        with ThreadPoolExecutor(4) as ex:
            for sym, res in ex.map(fetch_symbol, batch):
                bad = [r for r in res if r[1] != "ok"]; fails += bad
                for ds in DS:
                    convert_symbol(sym, ds)
                info[sym] = coverage(sym, listing[sym]); info[sym]["n_rejects"] = len(bad)
                print(sym, info[sym], flush=True)
        for s in batch:
            c = info[s]
            if c["prem_missing_frac"] <= 0.10 and c["fund_missing_frac"] <= 0.10:
                chosen.append(s)
    json.dump(fails, open(f"{OUTD}/ingest_rejects.json", "w"))
    # universe.csv is written BEFORE any outcome is computed
    rows = []
    for r in rk.iter_rows(named=True):
        s = r["symbol"]
        row = dict(rank=r["rank"], symbol=s, vol2023_quote=r["vol2023"], months2023=r["months2023"],
                   listing_utc=str(dt.datetime.fromtimestamp(r["first_open_ms"] / 1000, dt.timezone.utc)))
        if s in info:
            c = info[s]
            row.update(window_start=c["window_start"], window_end=c["window_end"], prem_missing_frac=round(c["prem_missing_frac"], 5),
                       fund_missing_frac=round(c["fund_missing_frac"], 5), kline_missing_frac=round(c["kline_missing_frac"], 5))
            if s in chosen:
                row["status"] = "chosen"
                row["reason"] = "top-25 by 2023 quote volume" if r["rank"] <= 25 else "replacement for a higher-ranked symbol failing the >10% missing rule"
            else:
                row["status"] = "excluded"
                row["reason"] = f"premium missing {c['prem_missing_frac']:.3f} / funding missing {c['fund_missing_frac']:.3f}; >0.10 over window"
        else:
            row["status"] = "not_needed"; row["reason"] = "ranked below the 25 chosen"
        rows.append(row)
    os.makedirs(f"{ROOT}/results/stage3", exist_ok=True)
    pl.DataFrame(rows, infer_schema_length=None).write_csv(f"{ROOT}/results/stage3/universe.csv")
    json.dump(chosen, open(f"{OUTD}/chosen.json", "w"))
    print("CHOSEN", chosen, flush=True)
    for s in rk["symbol"].to_list():
        if s in chosen or s in ("BTCUSDT", "ETHUSDT"):
            continue
        for ds in DS:
            for base in (dl.RAW, f"{D}/parquet"):
                shutil.rmtree(f"{base}/{ds}/{s}", ignore_errors=True)
    manifest(chosen, fails)


def manifest(chosen, fails):
    con = duckdb.connect(); con.execute("PRAGMA threads=2; PRAGMA memory_limit='2GB'")
    TC = {"klines_1m": "open_time", "premiumIndexKlines_1m": "open_time", "fundingRate": "calc_time"}

    def ep(x): return dt.datetime.fromtimestamp(x / 1000, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    out = ["", "", "# Stage 3 ingestion (Amendment 2 cross-asset universe)", "",
           f"Generated {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC by `phase2/code/ingest/stage3_screen.py` + `stage3_ingest.py`. Months {M0} through {M1} only (monthly files); nothing from 2025+ was downloaded. Same checksum policy (sha256 vs sibling .CHECKSUM, 5 retries) and parquet conventions as above. Row counts and coverage only.", "",
           f"Chosen symbols ({len(chosen)}): {', '.join(chosen)}", "",
           f"Checksum failures / rejected files after 5 retries in the stage-3 ingest: **{len(fails)}**"]
    for k, st in fails:
        out.append(f"- REJECT {k} {st}")
    out.append("")
    for s in chosen:
        for ds, t in TC.items():
            g = f"read_parquet('{D}/parquet/{ds}/{s}/*.parquet')"
            try:
                n, mn, mx = con.execute(f"select count(*),epoch_ms(min({t})),epoch_ms(max({t})) from {g}").fetchone()
            except Exception as e:
                out.append(f"- {ds}/{s}: NO DATA ({e})"); continue
            nz = len(glob.glob(f"{dl.RAW}/{ds}/{s}/*.zip"))
            line = f"- **{ds} / {s}**: zips {nz}; rows {n:,}; first {ep(mn)}; last {ep(mx)}"
            if ds != "fundingRate":
                gaps = con.execute(f"""with q as (select epoch_ms({t}) t from {g}), l as (select t, lag(t) over (order by t) p from q)
                  select p+60000, t-60000, (t-p)//60000-1 from l where p is not null and t-p>60000 order by 3 desc""").fetchall()
                miss = sum(x[2] for x in gaps)
                line += f"; missing 1m slots inside span {miss:,} in {len(gaps)} gap range(s)"
                if gaps:
                    line += "; largest: " + ", ".join(f"{ep(a)}..{ep(b)} ({m:,})" for a, b, m in gaps[:3])
            else:
                iv = con.execute(f"select funding_interval_hours,count(*) from {g} group by 1 order by 1").fetchall()
                line += "; interval_hours counts " + ", ".join(f"{a}:{b}" for a, b in iv)
            out.append(line)
    out += ["", "Window coverage used for the >10 % replacement rule is recorded per ranked symbol in `results/stage3/universe.csv`.", ""]
    with open(f"{ROOT}/docs/DATA_MANIFEST.md", "a") as f:
        f.write("\n".join(out))


if __name__ == "__main__":
    main()
