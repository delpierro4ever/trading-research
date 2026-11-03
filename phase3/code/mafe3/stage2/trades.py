"""Forward outcomes for stage 2 (first module that touches returns). Reuses stage-1 execution: entry = bar opening at t+1 (first bar with
label in [t+1, t+6]); exit = bar opening at entry + H (first bar within 5 min after, strictly after entry); no trade if the hold spans the
weekend closure; swap 2 bps per 17:00 NY rollover, x3 Wednesday; BID prices. Cost in bps = USD/oz round trip / entry price * 1e4.
The window (discovery or validation) is chosen by the MAFE3_WIN_* env vars read by mafe3.market BEFORE import (see run scripts)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..market import Market, O, L, D0, TOL
from ..engine import resolve, episode_calendar

HS = (5, 15, 30, 60, 240)
USD_PRIMARY, USD_ROBUST = 0.35, 0.50

def fwd_max(a, H, fn):
    """result[i] = fn over a[i .. i+H-1] (NaN skipped)."""
    s = pd.Series(a[::-1]).rolling(H, min_periods=1)
    return (s.max() if fn == "max" else s.min()).to_numpy()[::-1]

class Outcomes:
    """For a decision-time array td (dense Market indices), per horizon H: valid, e, x (bar indices), long gross bps, cost bps (0.35/0.50), swap bps."""
    def __init__(self, M: Market, td: np.ndarray, oracle=False):
        self.M, self.td = M, td
        self.by = {}
        for H in HS:
            e, x, ok = resolve(M, td + 1, np.full(len(td), -1), hold=np.full(len(td), H))
            ok &= td >= D0
            eC, xC = np.clip(e, 0, L - 1), np.clip(x, 0, L - 1)
            pe, px = M.o[eC], M.o[xC]
            with np.errstate(all="ignore"):
                g = np.log(px / pe) * 1e4
            ok &= np.isfinite(g)
            r = dict(valid=ok, e=eC, x=xC, gross=np.where(ok, g, np.nan), cost35=USD_PRIMARY / pe * 1e4, cost50=USD_ROBUST / pe * 1e4,
                     swap=np.where(ok, M.swap_bps(eC, xC), np.nan))
            if oracle:
                hi = fwd_max(M.h, H, "max")[eC]; lo = fwd_max(M.l, H, "min")[eC]
                with np.errstate(all="ignore"):
                    r["mfe"] = np.where(ok, np.maximum(np.log(hi / pe), np.log(pe / lo)) * 1e4, np.nan)
            self.by[H] = r
        yr, qt, wk = episode_calendar(np.arange(0))      # placeholder to keep import used
        # calendar of the decision time (year, ISO week, day) for statistics
        ts = (td + O).astype("datetime64[m]")
        idx = pd.DatetimeIndex(ts)
        iso = idx.isocalendar()
        self.year = idx.year.to_numpy()
        self.week = (iso.year.to_numpy() * 100 + iso.week.to_numpy()).astype(int)
        self.day = (td + O) // 1440

def greedy(tt, xs):
    """Greedy non-overlap: tt sorted decision times of candidate entries, xs their exit bars; a decision at t is admissible if t >= exit of the previous
    accepted trade (same rule as engine.run). Returns positions into tt."""
    keep, i, n = [], 0, len(tt)
    while i < n:
        keep.append(i)
        i = int(np.searchsorted(tt, xs[i], "left"))
    return np.array(keep, dtype=np.int64)
