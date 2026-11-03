"""MAFE-1C day pass (spot or futures sample). Resumable (per-day state pickles).
usage: c1_run.py spot OUTDIR START END RULES [FROZEN_JSON] [--anchors]
       c1_run.py fut  OUTDIR YEAR[,YEAR] RULES [FROZEN_JSON]
GUARD: any 2025 day requires the frozen-model file to be git-tracked (committed freeze) -> no 2025 outcome before the freeze commit."""
import sys, os, json, pickle, subprocess, datetime as dt
import numpy as np, polars as pl
sys.path.insert(0, os.path.dirname(__file__))
from c1_core import *
ROOT = "/home/ubuntu/mafe-data/mafe1"
REPO = "/home/ubuntu/mafe-research-archive"
def guard(dates, frozen_path):
    if any(d.year >= 2025 for d in dates):
        assert frozen_path, "2025 requires frozen models"
        r = subprocess.run(["git", "-C", REPO, "ls-files", "--error-unmatch", os.path.abspath(frozen_path)], capture_output=True)
        assert r.returncode == 0, "frozen model file is not committed -> refusing to touch 2025"
        st = subprocess.run(["git", "-C", REPO, "status", "--porcelain", os.path.abspath(frozen_path)], capture_output=True, text=True).stdout.strip()
        assert not st, "frozen model file modified since commit"
    assert all(d <= CUTOFF for d in dates), "governance cutoff 2025-12-31"
def load(kind, ds):
    base = ROOT if kind == "spot" else f"{ROOT}/futs"
    df = pl.read_parquet(f"{base}/parquet/{ds}.parquet", columns=["ts", "price", "qty", "buyer_is_maker"])
    return df["ts"].to_numpy(), df["price"].to_numpy(), df["qty"].to_numpy(), df["buyer_is_maker"].to_numpy()
def run_day(kind, out, d, rules, frozen, anchors, state):
    ds = d.isoformat(); day0 = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp() * 1000)
    ts, price, qty, bm = load(kind, ds); head = None
    if kind == "spot" and d < CUTOFF:
        nd = (d + dt.timedelta(1)).isoformat(); p = f"{ROOT}/parquet/{nd}.parquet"
        if os.path.exists(p):
            h = pl.scan_parquet(p).filter(pl.col("ts") < day0 + 86400_000 + 310_000).select("ts", "price").collect(); head = (h["ts"].to_numpy(), h["price"].to_numpy())
    tick = 0.01 if kind == "spot" else 0.10
    trs, A, new, daily = process_day(ts, price, qty, bm, day0, tick, head, state, rules, frozen, anchors)
    for r, df in trs.items():
        os.makedirs(f"{out}/trades_{r}", exist_ok=True); df.write_parquet(f"{out}/trades_{r}/{ds}.parquet", compression="zstd")
    if A is not None: os.makedirs(f"{out}/anchors", exist_ok=True); A.write_parquet(f"{out}/anchors/{ds}.parquet", compression="zstd")
    os.makedirs(f"{out}/daily", exist_ok=True); json.dump(daily, open(f"{out}/daily/{ds}.json", "w"))
    return new
if __name__ == "__main__":
    kind, out = sys.argv[1], sys.argv[2]; os.makedirs(f"{out}/state", exist_ok=True)
    if kind == "spot":
        a, b = dt.date.fromisoformat(sys.argv[3]), dt.date.fromisoformat(sys.argv[4]); rules = sys.argv[5].split(",")
        rest = [x for x in sys.argv[6:] if not x.startswith("--")]; anchors = "--anchors" in sys.argv
        days = [a + dt.timedelta(i) for i in range((b - a).days + 1)]
    else:
        ys = [int(y) for y in sys.argv[3].split(",")]; rules = sys.argv[4].split(","); rest = sys.argv[5:]; anchors = False
        days = []
        for y in ys:
            d = dt.date(y, 1, 1)
            while d.year == y: days.append(d); d += dt.timedelta(7)  # same pre-declared sample as m1_download.fut_days
    fpath = rest[0] if rest else None; guard(days, fpath)
    frozen = json.load(open(fpath)) if fpath else None
    prev = f"{out}/state/{(days[0] - dt.timedelta(1)).isoformat()}.pkl"
    state = pickle.load(open(prev, "rb")) if kind == "spot" and os.path.exists(prev) else {}
    for d in days:
        sp = f"{out}/state/{d}.pkl"
        if os.path.exists(sp): state = pickle.load(open(sp, "rb"))
        else:
            state = run_day(kind, out, d, rules, frozen, anchors, state if kind == "spot" else {})
            if kind == "spot": pickle.dump(state, open(sp, "wb"))
            else: open(sp, "wb").write(b"done")
        print(d, flush=True)
