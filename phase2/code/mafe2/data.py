"""MAFE2 data loader with sealed-holdout enforcement.

load(dataset, symbol, start, end) -> polars DataFrame sorted by time and de-duplicated.
Interval is half-open [start, end). Any request that could touch timestamps >= 2025-01-01T00:00Z
(including end=None, i.e. open-ended) raises HoldoutSealedError unless env MAFE2_UNSEAL equals the
contents of /home/ubuntu/mafe-data/UNSEAL_TOKEN.
"""
from __future__ import annotations
import os, re
from datetime import datetime, timezone
from pathlib import Path
import polars as pl

DATA_ROOT = Path(os.environ.get("MAFE2_DATA", "/home/ubuntu/mafe-data"))
PARQUET = DATA_ROOT / "parquet"
TOKEN_FILE = DATA_ROOT / "UNSEAL_TOKEN"

def _utc(s): return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
DISCOVERY = (_utc("2020-01-01"), _utc("2024-01-01"))
VALIDATION = (_utc("2024-01-01"), _utc("2025-01-01"))
HOLDOUT = (_utc("2025-01-01"), None)
HOLDOUT_START = HOLDOUT[0]

TIME_COL = {"klines_1m": "open_time", "premiumIndexKlines_1m": "open_time", "fundingRate": "calc_time",
            "metrics": "create_time", "bookDepth": "timestamp"}
KEY = {"bookDepth": ["timestamp", "percentage"]}

class HoldoutSealedError(RuntimeError):
    pass

def _to_dt(x, name):
    if x is None: return None
    if isinstance(x, str): x = datetime.fromisoformat(x.replace("Z", "+00:00"))
    if isinstance(x, datetime):
        return x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x.astimezone(timezone.utc)
    raise TypeError(f"{name} must be None, ISO string or datetime")

def _unsealed() -> bool:
    tok = os.environ.get("MAFE2_UNSEAL")
    if not tok: return False
    try: real = TOKEN_FILE.read_text().strip()
    except OSError: return False
    return bool(real) and tok.strip() == real

def _guard(start, end):
    touches = end is None or end > HOLDOUT_START
    if touches and not _unsealed():
        raise HoldoutSealedError(
            "Request touches timestamps >= 2025-01-01T00:00Z (holdout is sealed). "
            "Use end<=2025-01-01 or set MAFE2_UNSEAL to the unseal token.")

def partition(name):
    return {"discovery": DISCOVERY, "validation": VALIDATION, "holdout": HOLDOUT}[name.lower()]

def load_partition(dataset, symbol, name, columns=None):
    s, e = partition(name)
    return load(dataset, symbol, s, e, columns)

def load(dataset: str, symbol: str, start=None, end=None, columns=None) -> pl.DataFrame:
    if dataset not in TIME_COL: raise ValueError(f"unknown dataset {dataset}; choose from {list(TIME_COL)}")
    start, end = _to_dt(start, "start"), _to_dt(end, "end")
    _guard(start, end)                       # enforced BEFORE any file is opened
    tcol = TIME_COL[dataset]
    files = sorted((PARQUET / dataset / symbol).glob("*.parquet"))
    if not files: raise FileNotFoundError(f"no parquet for {dataset}/{symbol}")
    sel = []
    for f in files:                          # month files named YYYY-MM.parquet; prune by month
        y, m = map(int, re.match(r"(\d{4})-(\d{2})", f.stem).groups())
        f0 = datetime(y, m, 1, tzinfo=timezone.utc)
        f1 = datetime(y + (m == 12), m % 12 + 1, 1, tzinfo=timezone.utc)
        if end is not None and f0 >= end: continue
        if start is not None and f1 <= start: continue
        if not _unsealed() and f0 >= HOLDOUT_START: continue   # never even open holdout files when sealed
        sel.append(str(f))
    if not sel: return pl.DataFrame()
    lf = pl.scan_parquet(sel)
    if start is not None: lf = lf.filter(pl.col(tcol) >= start)
    if end is not None: lf = lf.filter(pl.col(tcol) < end)
    if not _unsealed():                      # defence in depth
        lf = lf.filter(pl.col(tcol) < HOLDOUT_START)
    lf = lf.unique(subset=KEY.get(dataset, [tcol]), keep="first").sort(KEY.get(dataset, [tcol]))
    if columns: lf = lf.select(list(dict.fromkeys([tcol] + list(columns))))
    return lf.collect()
