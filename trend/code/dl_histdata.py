"""Polite sequential HistData.com M1 (ASCII, bid) downloader for the TREND universe (adapted from phase3 downloader).
Usage: python -I dl_histdata.py OUTDIR SYM [SYM...]. Missing pages are recorded in OUTDIR/_missing.txt, not retried forever."""
import re, sys, time, zipfile, io, pathlib, datetime as dt
import requests
OUT = pathlib.Path(sys.argv[1]); SYMS = [s.lower() for s in sys.argv[2:]]
BASE = "https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}/{path}"
UA = {"User-Agent": "Mozilla/5.0 (research; trend)"}
PAUSE = 4

def fetch(s, pair, path):
    url = BASE.format(pair=pair, path=path)
    r = s.get(url, headers=UA, timeout=60)
    if r.status_code == 404: return None, None
    r.raise_for_status()
    m = re.search(r'<form id="file_down".*?</form>', r.text, re.S)
    if not m: return None, None
    fields = {x.group(1): x.group(2) for x in re.finditer(r'<input[^>]*name="(\w+)"[^>]*value="([^"]*)"', m.group(0))}
    r2 = s.post("https://www.histdata.com/get.php", data=fields, headers={**UA, "Referer": url}, timeout=300)
    r2.raise_for_status()
    return r2.content, fields

def get(s, pair, path, dest):
    if dest.exists(): return True
    for attempt in range(4):
        try:
            blob, fields = fetch(s, pair, path)
            if blob is None or blob[:2] != b'PK': return False
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                assert z.testzip() is None and z.namelist()
            dest.write_bytes(blob); print(dest.name, len(blob), flush=True); time.sleep(PAUSE); return True
        except Exception as e:
            print("FAIL", dest.name, attempt, repr(e)[:150], flush=True); time.sleep(20 * (attempt + 1))
    print("GIVING UP", dest.name, flush=True); return False

def main():
    OUT.mkdir(parents=True, exist_ok=True); s = requests.Session(); today = dt.date.today()
    for pair in SYMS:
        P = pair.upper()
        for y in range(int(__import__("os").environ.get("START_YEAR", 2009)), int(__import__("os").environ.get("END_YEAR", today.year))):
            if (OUT / f"{P}_{y}.zip").exists(): continue
            if not get(s, pair, str(y), OUT / f"{P}_{y}.zip"):
                # first/partial year: try months
                got = 0
                for m in range(1, 13):
                    got += get(s, pair, f"{y}/{m}", OUT / f"{P}_{y}{m:02d}.zip")
                    time.sleep(1)
                with open(OUT / "_missing.txt", "a") as f: f.write(f"{P} {y} yearpage-missing monthsgot={got}\n")
        for m in (range(1, today.month) if "END_YEAR" not in __import__("os").environ else []):
            get(s, pair, f"{today.year}/{m}", OUT / f"{P}_{today.year}{m:02d}.zip")
if __name__ == "__main__": main()
