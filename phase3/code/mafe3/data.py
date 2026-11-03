"""MAFE3 data loader (HistData.com XAUUSD/EURUSD 1-minute BID bars, Amendment 2) with sealed-holdout enforcement.

load(symbol, start, end) -> polars DataFrame: time (UTC datetime[ms]), open, high, low, close, volume (BID prices).
Interval is half-open [start, end). Any request that could touch timestamps >= 2023-01-01T00:00Z (including end=None)
raises HoldoutSealedError unless env MAFE3_UNSEAL equals the contents of /home/ubuntu/mafe-data/UNSEAL_TOKEN_MAFE3.
Sealed year files (>= 2023) are never opened.
"""
from __future__ import annotations
import os
from datetime import datetime, timezone
from pathlib import Path
import polars as pl

DATA_ROOT = Path(os.environ.get("MAFE3_DATA", "/home/ubuntu/mafe-data"))
PARQUET = DATA_ROOT / "histdata" / "parquet"
TOKEN_FILE = DATA_ROOT / "UNSEAL_TOKEN_MAFE3"

def _utc(s): return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
DISCOVERY = (_utc("2010-01-01"), _utc("2020-01-01"))
VALIDATION = (_utc("2020-01-01"), _utc("2023-01-01"))
HOLDOUT = (_utc("2023-01-01"), None)
HOLDOUT_START = HOLDOUT[0]

class HoldoutSealedError(RuntimeError):
    pass

def _to_dt(x, name):
    if x is None: return None
    if isinstance(x, str): x = datetime.fromisoformat(x.replace("Z", "+00:00"))
    if isinstance(x, datetime):
        return x.replace(tzinfo=timezone.utc) if x.tzinfo is None else x.astimezone(timezone.utc)
    raise TypeError(f"{name} must be None, ISO string or datetime")

def _unsealed() -> bool:
    tok = os.environ.get("MAFE3_UNSEAL")
    if not tok: return False
    try: real = TOKEN_FILE.read_text().strip()
    except OSError: return False
    return bool(real) and tok.strip() == real

def _guard(end):
    if (end is None or end > HOLDOUT_START) and not _unsealed():
        raise HoldoutSealedError("Request touches timestamps >= 2023-01-01T00:00Z (holdout sealed). "
                                 "Use end<=2023-01-01 or set MAFE3_UNSEAL to the unseal token.")

def partition(name):
    return {"discovery": DISCOVERY, "validation": VALIDATION, "holdout": HOLDOUT}[name.lower()]

def _year_files(symbol, start, end):
    """Yearly parquet files YYYY.parquet (UTC years) overlapping [start, end)."""
    sel = []
    for f in sorted((PARQUET / symbol).glob("*.parquet")):
        y = int(f.stem)
        f0 = datetime(y, 1, 1, tzinfo=timezone.utc); f1 = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
        if end is not None and f0 >= end: continue
        if start is not None and f1 <= start: continue
        if not _unsealed() and f0 >= HOLDOUT_START: continue
        sel.append(str(f))
    return sel

def load(symbol, start=None, end=None) -> pl.DataFrame:
    start, end = _to_dt(start, "start"), _to_dt(end, "end")
    _guard(end)
    sel = _year_files(symbol, start, end)
    if not sel: return pl.DataFrame()
    lf = pl.scan_parquet(sel)
    if start is not None: lf = lf.filter(pl.col("time") >= start)
    if end is not None: lf = lf.filter(pl.col("time") < end)
    if not _unsealed(): lf = lf.filter(pl.col("time") < HOLDOUT_START)
    return lf.unique(subset=["time"], keep="first").sort("time").collect()

def load_partition(symbol, name):
    s, e = partition(name)
    return load(symbol, s, e)
