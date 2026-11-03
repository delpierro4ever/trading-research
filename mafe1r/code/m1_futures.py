"""M1b: futures USD-M aggTrades 2026-09-23/24 (+ bookTicker if archived)."""
import urllib.request, hashlib, shutil, sys
ROOT="/home/ubuntu/mafe-data/mafe1/fut"
for d in ["2026-09-23","2026-09-24"]:
    for kind in ["aggTrades","bookTicker"]:
        n=f"BTCUSDT-{kind}-{d}.zip"; u=f"https://data.binance.vision/data/futures/um/daily/{kind}/BTCUSDT/{n}"
        for ext in ["",".CHECKSUM"]:
            try:
                with urllib.request.urlopen(u+ext,timeout=120) as r, open(f"{ROOT}/{n}{ext}","wb") as f: shutil.copyfileobj(r,f)
                print("ok",n+ext)
            except Exception as e: print("MISSING",n+ext,e)
        try:
            h=hashlib.sha256(open(f"{ROOT}/{n}","rb").read()).hexdigest(); print(n,h,open(f"{ROOT}/{n}.CHECKSUM").read().split()[0]==h)
        except Exception as e: print(e)
