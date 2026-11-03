"""MAFE-3 stage-2 feature library (phase3/docs/STAGE2_PREREGISTRATION.md section 2). Causal, price-only, 5-minute decision grid.

Convention (same as stage 1): the decision time is t (absolute epoch minute, multiple of 5). Features use bars with close <= t-1 min,
i.e. bars with label <= t-2 (a bar's label is its open minute). Every per-minute quantity below is evaluated at the dense minute j = t-2
and uses only bars with label <= j (trailing windows only). No forward return is computed anywhere in this module.
Frozen list and formulas: phase3/docs/STAGE2_FEATURES.md.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from numba import njit
from .. import data as D

NY = ZoneInfo("America/New_York")
PREROLL_DAYS = 15                # per-year chunks are computed with this much history before the chunk start
ZWIN, ZMIN = 5760, 1440          # trailing 20 trading days = 20 * 288 grid points; need >= 5 days
CONCEPT = {
    "Displacement": ["d_body1", "d_maxb15", "d_maxb60", "d_r5s60"],
    "Speed": ["s_5", "s_15", "s_30", "s_60", "s_acc", "s_up15", "s_up60"],
    "Compression": ["c_rng", "c_volr", "c_inside30", "c_loc60", "c_loc60c"],
    "Absorption": ["a_uw15", "a_lw15", "a_uw60", "a_lw60", "a_th", "a_tl", "a_rej"],
    "Reversal": ["r_fail", "r_v"],
    "Location": ["l_pdh", "l_pdl", "l_pdc", "l_open", "l_twap", "l_round"],
    "Time": ["t_hsin", "t_hcos", "t_sess", "t_dow"],
    "USD": ["u_s15", "u_s60", "u_disp"],
}
NAMES = [n for v in CONCEPT.values() for n in v]
TIME = CONCEPT["Time"]
NONTIME = [n for n in NAMES if n not in TIME]
CONCEPT_OF = {n: c for c, v in CONCEPT.items() for n in v}
NF = len(NAMES)
SESSIONS = {0: (0, 7), 1: (7, 12), 2: (12, 16), 3: (16, 21)}      # Asia, London, overlap, NY (UTC hours); 21-24 UTC = no session (-1)


@njit(cache=True)
def _max_abs_signed(x, k, minp):
    n = len(x); out = np.full(n, np.nan)
    for i in range(n):
        lo = max(0, i - k + 1); cnt = 0; bv = np.nan
        for j in range(lo, i + 1):
            b = x[j]
            if b == b:
                cnt += 1
                if bv != bv or abs(b) > abs(bv): bv = b
        if cnt >= minp: out[i] = bv
    return out


def _S(x): return pd.Series(x)
def rsum(x, k, mp): return _S(x).rolling(k, min_periods=mp).sum().to_numpy()
def rmean(x, k, mp): return _S(x).rolling(k, min_periods=mp).mean().to_numpy()
def rmax(x, k, mp): return _S(x).rolling(k, min_periods=mp).max().to_numpy()
def rmin(x, k, mp): return _S(x).rolling(k, min_periods=mp).min().to_numpy()
def shift(x, k):
    out = np.full(len(x), np.nan)
    if k > 0: out[k:] = x[:-k]
    else: out[:] = x
    return out
def ffill(x, limit): return _S(x).ffill(limit=limit).to_numpy()
def mp(k, frac=0.6): return int(np.ceil(frac * k))


def prims(o, h, l, c):
    """Per-minute primitives on a dense array (NaN = no bar)."""
    cp = shift(c, 1)
    ret1 = np.log(c / cp)                                   # NaN unless two consecutive minute bars
    body = c - o
    tr = np.fmax(h - l, np.fmax(np.abs(h - cp), np.abs(l - cp)))
    atr = rmean(tr, 60, 36)
    cf = ffill(c, 3)                                        # last close, stale by at most 3 minutes
    r2 = ret1 ** 2
    sig = {k: np.sqrt(rmean(r2, k, mp(k, 0.5))) for k in (30, 60, 240)}      # per-minute rms of 1 m log returns
    return dict(cp=cp, ret1=ret1, body=body, tr=tr, atr=atr, cf=cf, sig=sig)


def R(cf, k): return np.log(cf / shift(cf, k))


def speed(P, k): return R(P["cf"], k) / (P["sig"][240] * np.sqrt(k))


def rollover_days(a0, a1):
    """epoch minutes of 17:00 America/New_York for every calendar date around [a0, a1) (epoch minutes)."""
    d0 = datetime.fromtimestamp(a0 * 60, timezone.utc).date() - timedelta(days=3)
    d1 = datetime.fromtimestamp(a1 * 60, timezone.utc).date() + timedelta(days=3)
    out, d = [], d0
    while d <= d1:
        out.append(int(datetime(d.year, d.month, d.day, 17, tzinfo=NY).astimezone(timezone.utc).timestamp() // 60)); d += timedelta(days=1)
    return np.array(out, dtype=np.int64)


def minute_features(A: dict, a0: int) -> dict:
    """A: dense arrays o,h,l,c (gold) and eo,eh,el,ec (EURUSD) from absolute epoch minute a0. Returns per-minute feature arrays (except
    time features and c_loc60c, which are built on the grid)."""
    o, h, l, c = A["o"], A["h"], A["l"], A["c"]
    n = len(o)
    P = prims(o, h, l, c)
    atr, cf, body = P["atr"], P["cf"], P["body"]
    F = {}
    # --- Displacement
    F["d_body1"] = ffill(body, 5) / atr
    mb15 = _max_abs_signed(body, 15, 9); mb60 = _max_abs_signed(body, 60, 36)
    F["d_maxb15"] = mb15 / atr; F["d_maxb60"] = mb60 / atr
    F["d_r5s60"] = R(cf, 5) / (P["sig"][60] * np.sqrt(5))
    # --- Speed
    for k in (5, 15, 30, 60): F[f"s_{k}"] = speed(P, k)
    F["s_acc"] = F["s_5"] - F["s_30"]
    up = np.where(np.isnan(body), np.nan, (body > 0).astype(float))
    F["s_up15"] = rmean(up, 15, 9); F["s_up60"] = rmean(up, 60, 36)
    # --- Compression / accumulation
    hi60, lo60 = rmax(h, 60, 36), rmin(l, 60, 36)
    rng1440 = rmax(h, 1440, 240) - rmin(l, 1440, 240)
    F["c_rng"] = (hi60 - lo60) / rng1440
    F["c_volr"] = P["sig"][30] / P["sig"][240]
    hp, lp = shift(h, 1), shift(l, 1)
    inside = np.where(np.isnan(h) | np.isnan(hp) | np.isnan(lp) | np.isnan(l), np.nan, ((h <= hp) & (l >= lp)).astype(float))
    F["c_inside30"] = rsum(inside, 30, 18)
    F["c_loc60"] = (cf - lo60) / (hi60 - lo60)
    # --- Absorption / rejection
    upw = h - np.fmax(o, c); low = np.fmin(o, c) - l; rg = h - l
    for k in (15, 60):
        sr = rsum(rg, k, mp(k))
        sr = np.where(sr > 0, sr, np.nan)
        F[f"a_uw{k}"] = rsum(upw, k, mp(k)) / sr; F[f"a_lw{k}"] = rsum(low, k, mp(k)) / sr
    Hm = shift(rmax(h, 120, 72), 1); Lm = shift(rmin(l, 120, 72), 1)                 # prior 120 m high / low (excludes the bar itself)
    th = np.where(np.isnan(Hm) | np.isnan(h) | np.isnan(atr), np.nan, ((h >= Hm - 0.25 * atr) & (h <= Hm)).astype(float))
    tl = np.where(np.isnan(Lm) | np.isnan(l) | np.isnan(atr), np.nan, ((l <= Lm + 0.25 * atr) & (l >= Lm)).astype(float))
    F["a_th"] = rsum(th, 60, 36); F["a_tl"] = rsum(tl, 60, 36); F["a_rej"] = F["a_th"] - F["a_tl"]
    # --- Reversal / failed break
    lvl_up = rmin(np.where(h > Hm, Hm, np.nan), 15, 1)         # lowest 120 m high broken in the last 15 min
    lvl_dn = rmax(np.where(l < Lm, Lm, np.nan), 15, 1)         # highest 120 m low broken in the last 15 min
    ok = ~np.isnan(cf) & ~np.isnan(Hm) & ~np.isnan(Lm) & (rsum(np.where(np.isnan(h), 0.0, 1.0), 15, 1) >= 9)
    fail_up = (~np.isnan(lvl_up)) & (cf <= lvl_up)
    fail_dn = (~np.isnan(lvl_dn)) & (cf >= lvl_dn)
    F["r_fail"] = np.where(ok, fail_dn.astype(float) - fail_up.astype(float), np.nan)        # +1 failed break of the low (bullish), -1 failed break of the high
    r15 = R(cf, 15); r60p = shift(R(cf, 60), 15)               # R_60 ending 15 min before j
    opp = (r15 * r60p) < 0
    with np.errstate(all="ignore"):
        rv = np.where(opp, np.clip(r15 / np.abs(r60p), -2, 2), 0.0)
    F["r_v"] = np.where(np.isnan(r15) | np.isnan(r60p), np.nan, rv)
    # --- Location (ATR units, signed: price minus level)
    am = a0 + np.arange(n, dtype=np.int64)
    R_ = rollover_days(a0, a0 + n)
    dayid = np.searchsorted(R_, am, "right")
    has = ~np.isnan(o)
    df = pd.DataFrame({"d": dayid, "h": h, "l": l, "c": c})
    g = df.groupby("d")
    agg = pd.DataFrame({"H": g["h"].max(), "L": g["l"].min(), "C": g["c"].last()}).dropna(how="all")
    prev = agg.shift(1)                                         # previous trading day with bars
    pos = np.searchsorted(agg.index.to_numpy(), dayid)
    pdh, pdl, pdc = (prev[k].to_numpy()[np.clip(pos, 0, len(agg) - 1)] for k in ("H", "L", "C"))
    idx = np.nonzero(has)[0]
    firstflag = np.r_[True, np.diff(dayid[idx]) != 0] if len(idx) else np.array([], bool)
    first_open = np.full(n, np.nan); first_open[idx[firstflag]] = o[idx[firstflag]]
    d_open = pd.Series(first_open).groupby(dayid).ffill().to_numpy()      # causal: open of the first bar of the day, known once seen
    twap = rmean(c, 1440, 240)
    F["l_pdh"] = (cf - pdh) / atr; F["l_pdl"] = (cf - pdl) / atr; F["l_pdc"] = (cf - pdc) / atr
    F["l_open"] = (cf - d_open) / atr; F["l_twap"] = (cf - twap) / atr
    F["l_round"] = (cf - np.round(cf / 10.0) * 10.0) / atr
    # --- USD (EURUSD)
    E = prims(A["eo"], A["eh"], A["el"], A["ec"])
    F["u_s15"] = speed(E, 15); F["u_s60"] = speed(E, 60)
    F["u_disp"] = _max_abs_signed(E["body"], 15, 9) / E["atr"]
    F["_has_recent"] = rsum(has.astype(float), 6, 1)            # a bar exists in the 6 minutes ending at j (grid availability)
    return F


def time_features(t_abs):
    """Time features at the decision time t (UTC)."""
    tm = np.asarray(t_abs, dtype=np.int64)
    hod = (tm % 1440) / 60.0
    ang = 2 * np.pi * hod / 24.0
    hh = np.floor(hod)
    sess = np.full(len(tm), -1.0)
    for s, (a, b) in SESSIONS.items(): sess[(hh >= a) & (hh < b)] = s
    dow = ((tm // 1440 + 3) % 7).astype(float)                   # 1970-01-01 was a Thursday; 0 = Monday
    return dict(t_hsin=np.sin(ang), t_hcos=np.cos(ang), t_sess=sess, t_dow=dow)


def load_dense(start, end, pre_days=PREROLL_DAYS):
    """Dense float64 arrays for [start - pre_days, end) (datetimes, UTC) for gold and EURUSD. Returns (A, a0). Goes through the
    sealed-holdout guard in data.load."""
    s0 = start - timedelta(days=pre_days)
    a0 = int(s0.timestamp() // 60); a1 = int(end.timestamp() // 60)
    A = {}
    for sym, pre in (("XAUUSD", ""), ("EURUSD", "e")):
        df = D.load(sym, s0, end)
        for col, k in zip(("open", "high", "low", "close"), ("o", "h", "l", "c")):
            arr = np.full(a1 - a0, np.nan)
            if len(df):
                tt = df["time"].to_numpy().astype("datetime64[m]").astype("int64") - a0
                arr[tt] = df[col].to_numpy()
            A[pre + k] = arr
    return A, a0


def grid_times(start, end):
    """Absolute epoch minutes t in [start, end) that are multiples of 5."""
    a = int(start.timestamp() // 60); b = int(end.timestamp() // 60)
    return np.arange(a - a % 5 + (5 if a % 5 else 0), b, 5, dtype=np.int64)


def raw_features(start, end, patch=None):
    """Raw (un-normalised) features at every 5-minute decision time in [start, end) with a bar available shortly before t-2.
    Returns (t_abs int64 [n], X float32 [n, NF] in NAMES order with c_loc60c = NaN placeholder). patch(A, a0) may corrupt the dense arrays (tests)."""
    ts_all, Xs = [], []
    y = start.year
    while True:
        c0 = max(start, datetime(y, 1, 1, tzinfo=timezone.utc)); c1 = min(end, datetime(y + 1, 1, 1, tzinfo=timezone.utc))
        if c0 >= end: break
        A, a0 = load_dense(c0, c1)
        if patch is not None: patch(A, a0)
        F = minute_features(A, a0)
        t = grid_times(c0, c1)
        j = t - 2 - a0
        keep = F["_has_recent"][j] >= 1
        t, j = t[keep], j[keep]
        T = time_features(t)
        X = np.full((len(t), NF), np.nan, dtype=np.float32)
        for k, nme in enumerate(NAMES):
            if nme in T: X[:, k] = T[nme]
            elif nme in F: X[:, k] = F[nme][j]
        ts_all.append(t); Xs.append(X)
        del A, F
        y += 1
    return np.concatenate(ts_all), np.concatenate(Xs)


def normalise(t, X):
    """Grid-level stage: c_loc60c = c_loc60 x 1[c_rng < trailing 20th percentile of c_rng]; z-score (trailing 20 trading days = 5760 grid
    points incl. the current one, >= 1440 valid) of every non-time feature. Returns (Xraw, Z) float32; Z keeps the raw time features."""
    X = X.copy()
    ix = {n: i for i, n in enumerate(NAMES)}
    rng = pd.Series(X[:, ix["c_rng"]].astype(np.float64))
    q20 = rng.rolling(ZWIN, min_periods=ZMIN).quantile(0.2).to_numpy()
    loc = X[:, ix["c_loc60"]]
    X[:, ix["c_loc60c"]] = np.where(np.isnan(q20) | np.isnan(rng.to_numpy()) | np.isnan(loc), np.nan, loc * (rng.to_numpy() < q20))
    Z = X.copy()
    for n in NONTIME:
        s = pd.Series(X[:, ix[n]].astype(np.float64))
        r = s.rolling(ZWIN, min_periods=ZMIN)
        sd = r.std().to_numpy()
        Z[:, ix[n]] = np.where(sd > 0, (s.to_numpy() - r.mean().to_numpy()) / sd, np.nan)
    return X, Z


def build(start, end, patch=None):
    t, X = raw_features(start, end, patch)
    Xr, Z = normalise(t, X)
    return t, Xr, Z
