"""Binance daily klines (BTCUSDT, ETHUSDT spot) and FRED DTB3 (US 3m bill). Raw -> OUTDIR. Usage: python -I dl_other.py OUTDIR"""
import sys, json, time, pathlib, requests
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
for sym in ("BTCUSDT", "ETHUSDT"):
    rows, start = [], 1483228800000   # 2017-01-01
    while True:
        r = requests.get("https://api.binance.com/api/v3/klines", params=dict(symbol=sym, interval="1d", startTime=start, limit=1000), timeout=60); r.raise_for_status()
        k = r.json()
        if not k: break
        rows += k; start = k[-1][0] + 86400000; time.sleep(0.3)
        if len(k) < 1000: break
    (OUT / f"{sym}_1d.json").write_text(json.dumps(rows)); print(sym, len(rows))
for sid in ("DTB3", "DGS3MO", "DEXUSEU"):
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv", params=dict(id=sid), timeout=60); r.raise_for_status()
    (OUT / f"FRED_{sid}.csv").write_text(r.text); print(sid, len(r.text))
