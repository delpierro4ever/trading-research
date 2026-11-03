"""Binance 1h klines BTCUSDT/ETHUSDT (to build 22:00-UTC daily closes consistent with FX/HistData). Usage: python -I dl_binance_h1.py OUTDIR"""
import sys, json, time, pathlib, requests
OUT = pathlib.Path(sys.argv[1])
for sym in ("BTCUSDT", "ETHUSDT"):
    rows, start = [], 1502928000000   # 2017-08-17
    while True:
        r = requests.get("https://api.binance.com/api/v3/klines", params=dict(symbol=sym, interval="1h", startTime=start, limit=1000), timeout=60); r.raise_for_status()
        k = r.json()
        if not k: break
        rows += [x[:6] for x in k]; start = k[-1][0] + 3600000; time.sleep(0.25)
        if len(k) < 1000: break
    (OUT / f"{sym}_1h.json").write_text(json.dumps(rows)); print(sym, len(rows), flush=True)
