"""M1 manifest: integrity statistics of the 2025 spot files and the futures sample (no price/outcome statistic)."""
import glob, json, datetime as dt, os
R = "/home/ubuntu/mafe-data/mafe1"; out = {}
def summ(files):
    st = [json.load(open(f)) for f in sorted(files)]
    return dict(files=len(st), first=st[0]["date"], last=st[-1]["date"], rows=sum(x["rows"] for x in st), zip_bytes=sum(x["zip_bytes"] for x in st), dups=sum(x["dups"] for x in st), id_gaps=sum(x["gaps"] for x in st),
                unsorted_or_nonmono=sum((not x["sorted"]) or (not x["ts_monotone"]) for x in st), ts_outside_utc_day=sum(not x.get("ts_in_utc_day", True) for x in st),
                us_timestamp_files=sum(x["ts_unit_in_file"] == "us" for x in st), checksum_ok=all(x["checksum_ok"] for x in st), min_rows=min(x["rows"] for x in st), max_rows=max(x["rows"] for x in st),
                days=[x["date"] for x in st] if st[0].get("kind") == "fut" else None)
out["spot_2025"] = summ(glob.glob(f"{R}/parquet/2025-*.stats.json"))
exp = [dt.date(2025, 1, 1) + dt.timedelta(i) for i in range(365)]; have = {os.path.basename(f)[:10] for f in glob.glob(f"{R}/parquet/2025-*.stats.json")}
out["spot_2025"]["missing_days"] = [d.isoformat() for d in exp if d.isoformat() not in have]
# id continuity across day boundaries
st = {os.path.basename(f)[:10]: json.load(open(f)) for f in glob.glob(f"{R}/parquet/2025-*.stats.json")}
out["spot_2025"]["cross_day_id_breaks"] = sum(1 for i in range(364) if exp[i].isoformat() in st and exp[i + 1].isoformat() in st and st[exp[i + 1].isoformat()]["id_min"] != st[exp[i].isoformat()]["id_max"] + 1)
for y in (2023, 2024, 2025):
    out[f"fut_{y}"] = summ(glob.glob(f"{R}/futs/parquet/{y}-*.stats.json"))
sp = {y: summ(glob.glob(f"{R}/parquet/{y}-*.stats.json")) for y in (2023, 2024)}
out["spot_2023_2024_from_mafe1r"] = {y: {k: v for k, v in s.items() if k != "days"} for y, s in sp.items()}
json.dump(out, open("/home/ubuntu/mafe-research-archive/mafe1c/results/MANIFEST_data.json", "w"), indent=1)
print(json.dumps({k: {a: b for a, b in v.items() if a != "days"} for k, v in out.items() if k != "spot_2023_2024_from_mafe1r"}, indent=1))
