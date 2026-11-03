"""Dense one-minute market arrays for the MAFE3 discovery (XAUUSD bid, EURUSD bid close) and calendar helpers (Amendment 2).

Index convention: dense index i <-> epoch minute O + i, O = 2009-11-01T00:00Z (warm-up for z-scores; the discovery partition
starts 2010-01-01). A HistData bar's *label* is its open minute; it covers [label, label+1 min) and its close is observed at
label+1 min. "Features use bars with close <= t-1 min" therefore means bars with label <= t-2. Entry is the open of the bar
with label t+1 (first available bar with label in [t+1, t+6]). All prices are BID.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import os
import numpy as np
from . import data as D

def epoch_min(y, m, d, hh=0, mm=0): return int(datetime(y, m, d, hh, mm, tzinfo=timezone.utc).timestamp() // 60)

def _env_min(name, default):
    y, m, d = (int(v) for v in os.environ.get(name, default).split("-"))
    return epoch_min(y, m, d)

# Window (defaults = discovery). run_validation sets these env vars BEFORE importing mafe3: warm-up start / exclusive end / first measured day.
O = _env_min("MAFE3_WIN_START", "2009-11-01")
END = _env_min("MAFE3_WIN_END", "2020-01-01")             # exclusive end of the partition
L = END - O
D0 = _env_min("MAFE3_PART_START", "2010-01-01") - O       # first dense index of the measured partition
F0 = epoch_min(2010, 1, 1, 21)          # a Friday 21:00 UTC (weekend-closure origin), in epoch minutes
WEEK, CLOSURE = 10080, 2880             # minutes; closure = [Fri 21:00, Sun 21:00)
TOL = 5                                 # minutes: nearest-bar tolerance
NY, LON = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
BIG = 2**40
assert O % 60 == 0 and L % 1440 == 0

def abs_min(i): return np.asarray(i, dtype=np.int64) + O
def in_closure(am): return np.mod(am - F0, WEEK) < CLOSURE
def week_idx(am): return np.floor_divide(am - F0, WEEK)

def local_to_utc_min(y, m, d, hh, tz):
    """dense index of a local wall-clock whole hour on a calendar date."""
    return int(datetime(y, m, d, hh, 0, tzinfo=tz).astimezone(timezone.utc).timestamp() // 60) - O

def rollovers():
    """(epoch minutes of 17:00 America/New_York for every calendar day, weight 1 or 3 (Wednesday rollover))."""
    R, W = [], []
    d = date(2009, 10, 25)
    e = datetime.fromtimestamp(END * 60, timezone.utc).date() + timedelta(days=2)     # discovery: 2020-01-03
    while d <= e:
        R.append(int(datetime(d.year, d.month, d.day, 17, tzinfo=NY).astimezone(timezone.utc).timestamp() // 60)); W.append(3 if d.weekday() == 2 else 1)
        d += timedelta(days=1)
    return np.array(R, dtype=np.int64), np.array(W, dtype=np.int64)

KEYS = ("o", "h", "l", "c")

class Market:
    def __init__(self, g: dict, eur_close: np.ndarray):
        self.__dict__.update(g)
        self.eur_c = eur_close
        self.has = ~np.isnan(self.o)
        ar = np.arange(L, dtype=np.int64)
        self.nxt = np.minimum.accumulate(np.where(self.has, ar, BIG)[::-1])[::-1]       # first bar with label >= i
        self.prv = np.maximum.accumulate(np.where(self.has, ar, -1))                     # last bar with label <= i
        self.eur_has = ~np.isnan(self.eur_c)
        self.eur_prv = np.maximum.accumulate(np.where(self.eur_has, ar, -1))
        self.R, self.W = rollovers()
        self.cumW = np.concatenate([[0], np.cumsum(self.W)])

    @staticmethod
    def from_loader(start="2009-11-01", end="2020-01-01"):
        gd = D.load("XAUUSD", start, end)
        ed = D.load("EURUSD", start, end)
        def dense(df, col):
            a = np.full(L, np.nan)
            t = df["time"].to_numpy().astype("datetime64[m]").astype("int64") - O
            assert t.min() >= 0 and t.max() < L, "data outside the discovery window"
            a[t] = df[col].to_numpy(); return a
        g = {k: dense(gd, n) for k, n in zip(KEYS, ("open", "high", "low", "close"))}
        return Market(g, dense(ed, "close"))

    def corrupt_after(self, label_cut: int, seed=0):
        """New Market where all bar VALUES with dense label index > label_cut are replaced by random garbage (availability kept)."""
        rng = np.random.default_rng(seed)
        def garb(a):
            a = a.copy(); tail = a[label_cut + 1:]; med = np.nanmedian(a[:label_cut + 1])
            a[label_cut + 1:] = np.where(np.isnan(tail), np.nan, rng.uniform(0.5, 2.0, len(tail)) * med)
            return a
        return Market({k: garb(getattr(self, k)) for k in KEYS}, garb(self.eur_c))

    def asof(self, arr, prv, m, tol=TOL):
        """value of the last bar with label <= m, if not older than tol minutes (else NaN). m: int array of dense indices."""
        m = np.asarray(m); ok = (m >= 0) & (m < L)
        j = np.where(ok, prv[np.clip(m, 0, L - 1)], -1)
        good = ok & (j >= 0) & (m - j <= tol)
        return np.where(good, arr[np.clip(j, 0, L - 1)], np.nan)

    def grid(self):
        """Decision hours t (full UTC hours): a bar with label in [t-2-5, t-2] (features) and one in [t+1, t+6] (entry) both exist."""
        t = np.arange(60, L - 60, 60, dtype=np.int64)
        f = self.prv[t - 2] >= t - 2 - TOL
        e = self.nxt[t + 1] <= t + 1 + TOL
        return t[f & e]

    def swap_bps(self, e_bar, x_bar):
        """2 bps per 17:00 NY rollover r with entry < r <= exit (epoch minutes of the bar opens), x3 for the Wednesday rollover."""
        ea, xa = abs_min(e_bar), abs_min(x_bar)
        return 2.0 * (self.cumW[np.searchsorted(self.R, xa, "right")] - self.cumW[np.searchsorted(self.R, ea, "right")])
