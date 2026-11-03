"""Download Binance USD-M public data (klines 1m monthly, metrics daily, fundingRate monthly) with checksum verification.
Only dates <= 2024-12-31 are ever requested: the 2025+ holdout is never downloaded."""
import os, sys, hashlib, json, zipfile, io, urllib.request, urllib.error, datetime as dt
from concurrent.futures import ThreadPoolExecutor
BASE = "https://data.binance.vision/data/futures/um"
ROOT = "/home/ubuntu/mafe-data/mafe4/raw"
COINS = "BTC ETH SOL XRP DOGE BNB ADA AVAX LINK LTC".split()
LAST = dt.date(2024, 12, 31)
def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
        except Exception: pass
    raise RuntimeError(url)
def fetch(job):
    kind, sym, tag, url = job
    d = f"{ROOT}/{kind}/{sym}"; os.makedirs(d, exist_ok=True)
    out = f"{d}/{tag}.csv.gz"
    if os.path.exists(out): return (job[:3], "ok")
    z = get(url)
    if z is None: return (job[:3], "404")
    c = get(url + ".CHECKSUM")
    if c is not None:
        if hashlib.sha256(z).hexdigest() != c.decode().split()[0]: return (job[:3], "BADSUM")
        sumok = True
    else: sumok = False
    import gzip
    zf = zipfile.ZipFile(io.BytesIO(z)); data = zf.read(zf.namelist()[0])
    with gzip.open(out + ".tmp", "wb") as f: f.write(data)
    os.rename(out + ".tmp", out)
    return (job[:3], "ok" if sumok else "ok_nosum")
def months(a, b):
    y, m = a
    while (y, m) <= b:
        yield y, m; m += 1
        if m == 13: y += 1; m = 1
jobs = []
for c in COINS:
    s = c + "USDT"
    for y, m in months((2020, 7), (2024, 12)):
        jobs.append(("klines", s, f"{y}-{m:02d}", f"{BASE}/monthly/klines/{s}/1m/{s}-1m-{y}-{m:02d}.zip"))
        jobs.append(("funding", s, f"{y}-{m:02d}", f"{BASE}/monthly/fundingRate/{s}/{s}-fundingRate-{y}-{m:02d}.zip"))
    d = dt.date(2020, 9, 1)
    while d <= LAST:
        jobs.append(("metrics", s, d.isoformat(), f"{BASE}/daily/metrics/{s}/{s}-metrics-{d.isoformat()}.zip")); d += dt.timedelta(days=1)
kinds = sys.argv[1:] or ["klines", "funding", "metrics"]
jobs = [j for j in jobs if j[0] in kinds]
res = {}
with ThreadPoolExecutor(int(os.environ.get("WORKERS", 6))) as ex:
    for k, st in ex.map(fetch, jobs): res["|".join(k)] = st
man = f"{ROOT}/MANIFEST_{'_'.join(kinds)}.json"
json.dump(res, open(man, "w"), indent=0)
from collections import Counter
print(Counter(res.values()))
