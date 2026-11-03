"""Feature construction for MAFE-2 discovery. Everything is indexed on the hourly UTC decision grid.

Time base: T0 = 2020-01-01T00:00Z. Minute index m = minutes since T0. Grid hour g -> t = g*60 minutes.
All feature functions take an array of grid indices `g` and return one value per index (NaN = unavailable).
Only data with index <= t-2min (klines) or timestamp <= t-10min (metrics/bookDepth) or funding time <= t is read.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np
import polars as pl
from . import data

T0 = datetime(2020, 1, 1, tzinfo=timezone.utc)
T_END = datetime(2024, 1, 1, tzinfo=timezone.utc)          # discovery end (exclusive)
NMIN = int((T_END - T0).total_seconds() // 60)               # 2,103,840 minutes
NGRID = NMIN // 60                                           # 35,064 hours
LS = {"1h": 60, "4h": 240, "24h": 1440}                      # lookbacks in minutes
HS = {"1h": 60, "4h": 240, "24h": 1440}
STALE_METRICS_S = 300            # a 5m row may be used at most one sampling interval stale
BOOK_MIN_COVER = 0.8             # bookDepth window needs >=80% of expected snapshots (~30.5 s cadence)
BOOK_EXPECT_S = 30.5
BOOK_END_STALE_S = 60            # last snapshot must be within 60 s of the window end

_T0_MS = int(np.datetime64(T0.replace(tzinfo=None), "ms").astype("int64"))


def to_min(ts: np.ndarray) -> np.ndarray:
    """datetime64 array -> float minutes since T0."""
    return (ts.astype("datetime64[ms]").astype("int64") - _T0_MS) / 60000.0


def _kline_arrays(df: pl.DataFrame, cols: list[str]) -> dict[str, np.ndarray]:
    idx = np.rint(to_min(df["open_time"].to_numpy())).astype(np.int64)
    ok = (idx >= 0) & (idx < NMIN)
    out = {}
    for c in cols:
        a = np.full(NMIN, np.nan)
        a[idx[ok]] = df[c].to_numpy()[ok]
        out[c] = a
    return out


@dataclass
class Market:
    symbol: str
    open: np.ndarray = None
    close: np.ndarray = None
    vol: np.ndarray = None
    tbv: np.ndarray = None
    prem: np.ndarray = None
    fund_min: np.ndarray = None      # funding time, minutes since T0 (float)
    fund_rate: np.ndarray = None
    met_s: np.ndarray = None         # metrics create_time, seconds since T0
    oi_val: np.ndarray = None
    top_ratio: np.ndarray = None     # count_toptrader_long_short_ratio
    glob_ratio: np.ndarray = None    # count_long_short_ratio
    book_s: np.ndarray = None        # snapshot time, seconds since T0
    book_imb: np.ndarray = None

    def copy(self) -> "Market":
        import copy
        m = copy.copy(self)
        for k, v in list(m.__dict__.items()):
            if isinstance(v, np.ndarray):
                setattr(m, k, v.copy())
        return m


def load_market(symbol: str, books: bool = True) -> Market:
    """Load discovery data (< 2024-01-01) through mafe2.data only."""
    s, e = "2020-01-01", "2024-01-01"
    k = data.load("klines_1m", symbol, s, e, ["open", "close", "volume", "taker_buy_volume"])
    ka = _kline_arrays(k, ["open", "close", "volume", "taker_buy_volume"])
    p = data.load("premiumIndexKlines_1m", symbol, s, e, ["close"])
    pa = _kline_arrays(p, ["close"])
    f = data.load("fundingRate", symbol, s, e, ["last_funding_rate"])
    m = data.load("metrics", symbol, s, e, ["sum_open_interest_value", "count_toptrader_long_short_ratio", "count_long_short_ratio"])
    mk = Market(symbol, open=ka["open"], close=ka["close"], vol=ka["volume"], tbv=ka["taker_buy_volume"], prem=pa["close"],
                fund_min=to_min(f["calc_time"].to_numpy()), fund_rate=f["last_funding_rate"].to_numpy().astype(float),
                met_s=to_min(m["create_time"].to_numpy()) * 60.0,
                oi_val=m["sum_open_interest_value"].to_numpy().astype(float),
                top_ratio=m["count_toptrader_long_short_ratio"].to_numpy().astype(float),
                glob_ratio=m["count_long_short_ratio"].to_numpy().astype(float))
    if books:
        ts_l, im_l = [], []
        for mo in range(1, 13):            # month by month, bookDepth is large
            a = datetime(2023, mo, 1, tzinfo=timezone.utc)
            b = datetime(2023 + (mo == 12), mo % 12 + 1, 1, tzinfo=timezone.utc)
            d = data.load("bookDepth", symbol, a, b, ["percentage", "notional"])
            d = d.filter(pl.col("percentage").abs() == 1.0)
            sn = d.group_by("timestamp").agg(
                bid=pl.col("notional").filter(pl.col("percentage") == -1.0).first(),
                ask=pl.col("notional").filter(pl.col("percentage") == 1.0).first()).drop_nulls().sort("timestamp")
            ts_l.append(to_min(sn["timestamp"].to_numpy()) * 60.0)
            im_l.append(((sn["bid"] - sn["ask"]) / (sn["bid"] + sn["ask"])).to_numpy())
            del d, sn
        mk.book_s = np.concatenate(ts_l)
        mk.book_imb = np.concatenate(im_l)
    return mk


# ---------------------------------------------------------------- window helpers
def _cum(a: np.ndarray):
    """cumulative sum with NaN->0 plus cumulative count of valid entries (length n+1)."""
    ok = ~np.isnan(a)
    return np.concatenate([[0.0], np.cumsum(np.where(ok, a, 0.0))]), np.concatenate([[0], np.cumsum(ok)])


def _window_sum(cs, cc, last, L):
    """sum over bars last-L+1..last ; NaN if any bar missing or window out of range."""
    lo = last - L + 1
    valid = (lo >= 0) & (last < len(cs) - 1)
    lo_c, hi_c = np.clip(lo, 0, None), np.clip(last + 1, 0, len(cs) - 1)
    s = cs[hi_c] - cs[lo_c]
    n = cc[hi_c] - cc[lo_c]
    return np.where(valid & (n == L), s, np.nan)


def _last_row(ts, T):
    """index of last row with ts <= T, plus staleness check (T - ts <= one 5m interval)."""
    j = np.searchsorted(ts, T, side="right") - 1
    jj = np.clip(j, 0, len(ts) - 1)
    ok = (j >= 0) & ((T - ts[jj]) <= STALE_METRICS_S)
    return jj, ok


class Features:
    """Vectorised, causal feature extractor on a Market."""
    def __init__(self, mk: Market):
        self.mk = mk
        self.cum_tbv = _cum(mk.tbv)
        self.cum_vol = _cum(mk.vol)
        self.cum_prem = _cum(mk.prem)
        self.book_cum = None if mk.book_imb is None else np.concatenate([[0.0], np.cumsum(mk.book_imb)])

    def ret(self, g, L):
        c = self.mk.close
        m = g * 60 - 2
        a = m - L
        ok = a >= 0
        ca, cb = c[np.clip(a, 0, None)], c[np.clip(m, 0, None)]
        with np.errstate(all="ignore"):
            return np.where(ok, np.log(cb / ca), np.nan)

    def taker(self, g, L):
        last = g * 60 - 2
        tb = _window_sum(*self.cum_tbv, last, L)
        v = _window_sum(*self.cum_vol, last, L)
        with np.errstate(all="ignore"):
            return np.where(v > 0, (2 * tb - v) / v, np.nan)

    def funding(self, g):
        t = g * 60.0
        mk = self.mk
        j = np.searchsorted(mk.fund_min, t, side="right") - 1
        return np.where(j >= 0, mk.fund_rate[np.clip(j, 0, None)], np.nan)

    def premium(self, g, L):
        last = g * 60 - 2
        return _window_sum(*self.cum_prem, last, L) / L

    def oi_confirmed(self, g, L):
        mk = self.mk
        T1 = g * 3600.0 - 600.0
        j1, ok1 = _last_row(mk.met_s, T1)
        j0, ok0 = _last_row(mk.met_s, T1 - L * 60.0)
        with np.errstate(all="ignore"):
            chg = mk.oi_val[j1] / mk.oi_val[j0] - 1.0
            x = chg * np.sign(self.ret(g, L))
        return np.where(ok1 & ok0, x, np.nan)

    def level(self, g, which):
        mk = self.mk
        arr = mk.top_ratio if which == "top" else mk.glob_ratio
        j, ok = _last_row(mk.met_s, g * 3600.0 - 600.0)
        return np.where(ok, arr[j], np.nan)

    def book(self, g, L):
        mk = self.mk
        if mk.book_s is None:
            return np.full(len(g), np.nan)
        hi = g * 3600.0 - 600.0
        lo = hi - L * 60.0
        i1 = np.searchsorted(mk.book_s, hi, side="right")          # ts <= hi
        i0 = np.searchsorted(mk.book_s, lo, side="right")          # ts > lo
        cnt = i1 - i0
        last_ts = mk.book_s[np.clip(i1 - 1, 0, len(mk.book_s) - 1)]
        ok = (cnt >= BOOK_MIN_COVER * L * 60.0 / BOOK_EXPECT_S) & (i1 > 0) & ((hi - last_ts) <= BOOK_END_STALE_S)
        with np.errstate(all="ignore"):
            x = (self.book_cum[i1] - self.book_cum[i0]) / np.maximum(cnt, 1)
        return np.where(ok, x, np.nan)

    def all(self, g) -> dict[str, np.ndarray]:
        out = {}
        for ln, L in LS.items():
            out[f"F1_{ln}"] = self.ret(g, L)
            out[f"F2_{ln}"] = self.taker(g, L)
            out[f"F4_{ln}"] = self.premium(g, L)
            out[f"F5_{ln}"] = self.oi_confirmed(g, L)
            out[f"F8_{ln}"] = self.book(g, L)
        out["F3"] = self.funding(g)
        out["F6_top"] = self.level(g, "top")
        out["F6_glob"] = self.level(g, "glob")
        return out


# ---------------------------------------------------------------- z-score
Z_WIN, Z_MIN = 720, 480

def zscore(x: np.ndarray) -> np.ndarray:
    """z_t = (x_t - mean)/std over the previous 720 grid points (t-720..t-1, excluding t); >=480 non-null; ddof=1."""
    import pandas as pd
    r = pd.Series(x).rolling(Z_WIN, min_periods=Z_MIN)
    mu, sd = r.mean().shift(1).to_numpy(), r.std(ddof=1).shift(1).to_numpy()
    with np.errstate(all="ignore"):
        z = (x - mu) / sd
    z[~np.isfinite(z) | (sd <= 1e-9 * np.abs(mu))] = np.nan     # constant window -> z undefined (guards float noise)
    return z
