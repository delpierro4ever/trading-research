"""Polite sequential HistData.com M1 (ASCII, BID) downloader. Usage: python download_histdata.py [outdir]"""
import re, sys, time, zipfile, io, pathlib, datetime as dt
import requests

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/mafe-data/histdata/raw")
BASE = "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}/{path}"
UA = {"User-Agent": "Mozilla/5.0 (research; mafe3)"}
PAUSE = 6


def jobs():
    today = dt.date.today()
    for pair in ("xauusd", "eurusd"):
        for y in range(2009, today.year):
            yield pair, str(y), f"{pair.upper()}_{y}.zip"
        for m in range(1, today.month):  # complete months of the current year only
            yield pair, f"{today.year}/{m}", f"{pair.upper()}_{today.year}{m:02d}.zip"


def fetch(s, pair, path):
    url = BASE.format(pair=pair, path=path)
    r = s.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    html = r.text
    form = re.search(r'<form id="file_down".*?</form>', html, re.S).group(0)
    fields = {m.group(1): m.group(2) for m in re.finditer(r'<input[^>]*name="(\w+)"[^>]*value="([^"]*)"', form)}
    r2 = s.post("https://www.histdata.com/get.php", data=fields, headers={**UA, "Referer": url}, timeout=300)
    r2.raise_for_status()
    return r2.content, fields


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = requests.Session()
    for pair, path, fn in jobs():
        dest = OUT / fn
        if dest.exists():
            continue
        for attempt in range(6):
            try:
                blob, fields = fetch(s, pair, path)
                with zipfile.ZipFile(io.BytesIO(blob)) as z:
                    assert z.testzip() is None and z.namelist()
                dest.write_bytes(blob)
                print(fn, len(blob), fields.get("date"), fields.get("datemonth"), flush=True)
                break
            except Exception as e:
                print("FAIL", fn, attempt, repr(e)[:200], flush=True)
                time.sleep(30 * (attempt + 1))
        else:
            print("GIVING UP", fn, flush=True)
        time.sleep(PAUSE)


if __name__ == "__main__":
    main()
