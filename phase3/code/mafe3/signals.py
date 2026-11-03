"""Hypothesis registry (89) and candidate construction for MAFE3 (1-minute BID bars, Amendment 2). Decision time t (a full UTC hour
unless a family has its own anchor) uses only bars with label <= t-2 (close <= t-1 min); entry is the open of the bar at t+1 min;
exit at entry + H. All L/H in the registry are in HOURS; Cands use minutes."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import numpy as np
import pandas as pd
from .market import Market, O, L, D0, TOL, local_to_utc_min, LON
from .engine import Cands

Z_THRESH, Z_WIN, Z_MIN = 1.5, 720, 480
LS = {"1h": 1, "4h": 4, "24h": 24}
HS = {"1h": 1, "4h": 4, "24h": 24}
DN = {1: "C", -1: "R"}


@dataclass(frozen=True)
class Hyp:
    id: str
    family: str
    d: int = 0
    L: int = 0
    H: int = 0
    param: int = -1
    kind: str = "z"


def registry() -> list[Hyp]:
    h = []
    for ln, Lm in LS.items():
        for hn, Hm in HS.items():
            for d in (1, -1):
                h.append(Hyp(f"G1_L{ln}_H{hn}_{DN[d]}", "G1", d, Lm, Hm))
    for k in range(24):
        h.append(Hyp(f"G2_hod{k:02d}", "G2", 0, 0, 1, k, "hod"))
    for w, nm in enumerate(("mon", "tue", "wed", "thu", "fri")):
        h.append(Hyp(f"G2_dow_{nm}", "G2", 0, 0, 24, w, "dow"))
    for hn, Hm in (("1h", 1), ("4h", 4), ("9h", 9)):
        for d in (1, -1):
            h.append(Hyp(f"G3_H{hn}_{DN[d]}", "G3", d, 0, Hm, kind="g3"))
    for hn, Hm in (("1h", 1), ("4h", 4)):
        for d in (1, -1):
            h.append(Hyp(f"G4_H{hn}_{DN[d]}", "G4", d, 0, Hm, kind="g4"))
    for d, nm in ((1, "long"), (-1, "short")):
        h.append(Hyp(f"G5_{nm}", "G5", d, 0, 0, kind="g5"))
    for hn, Hm in HS.items():
        for d in (1, -1):
            h.append(Hyp(f"G6_H{hn}_{DN[d]}", "G6", d, 0, Hm, kind="g6"))
    for ln, Lm in LS.items():
        for hn, Hm in HS.items():
            for d in (1, -1):
                h.append(Hyp(f"G7_L{ln}_H{hn}_{DN[d]}", "G7", d, Lm, Hm, kind="g7"))
    for hn, Hm in HS.items():
        for d in (1, -1):
            h.append(Hyp(f"G8_H{hn}_{DN[d]}", "G8", d, 0, Hm, kind="g8"))
    return h


def zscore(x: np.ndarray) -> np.ndarray:
    """z over the previous 720 grid points (excluding the current one); needs >= 480 non-null."""
    s = pd.Series(x)
    r = s.rolling(Z_WIN, min_periods=Z_MIN)
    m, sd = r.mean().shift(1), r.std(ddof=1).shift(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (s - m) / sd
    z[(sd <= 0) | sd.isna()] = np.nan
    return z.to_numpy()


def log_ret(M: Market, close, prv, t, Lm):
    """ln return over Lm hours ending at t-1 min: close of the last bar with label <= t-2 vs close of the last bar with label <= t-2-60*Lm."""
    a = M.asof(close, prv, t - 2)
    b = M.asof(close, prv, t - 2 - 60 * Lm)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.log(a / b)


class Signals:
    """Builds all features once; hypothesis -> Cands."""

    def __init__(self, M: Market):
        self.M = M
        self.grid = M.grid()
        t = self.grid
        self.x_gold = {Lm: log_ret(M, M.c, M.prv, t, Lm) for Lm in LS.values()}
        self.x_eur = {Lm: log_ret(M, M.eur_c, M.eur_prv, t, Lm) for Lm in LS.values()}
        self.z_gold = {Lm: zscore(x) for Lm, x in self.x_gold.items()}
        self.z_eur = {Lm: zscore(x) for Lm, x in self.x_eur.items()}
        # G6: close of the latest closed bar (label <= t-2) vs the prior-24h high/low of bars labelled t-1442 .. t-3 (>= 200 bars present)
        W = 1440
        hi = pd.Series(M.h).rolling(W, min_periods=200).max().to_numpy()
        lo = pd.Series(M.l).rolling(W, min_periods=200).min().to_numpy()
        c = M.asof(M.c, M.prv, t - 2)
        H24, L24 = hi[t - 3], lo[t - 3]
        with np.errstate(invalid="ignore"):
            self.g6 = np.where(c > H24, 1, np.where(c < L24, -1, 0)).astype(np.int8)
        self._build_days()

    def _build_days(self):
        M = self.M
        n = L // 1440
        d00 = datetime.fromtimestamp(O * 60, timezone.utc).date()      # discovery: 2009-11-01
        days = [d00 + timedelta(days=i) for i in range(n)]
        self.days = days
        self.mid0 = np.arange(n, dtype=np.int64) * 1440          # dense idx of 00:00 UTC of each date
        self.wd = np.array([d.weekday() for d in days])
        hours_with_bars = M.has[: n * 1440].reshape(n, 24, 60).any(axis=2).sum(axis=1)
        self.day_hours = hours_with_bars
        self.lon15 = np.array([local_to_utc_min(d.year, d.month, d.day, 15, LON) for d in days], dtype=np.int64)
        self.lon16 = np.array([local_to_utc_min(d.year, d.month, d.day, 16, LON) for d in days], dtype=np.int64)

    def _near(self, idx):
        """True where a bar with label in [idx, idx+TOL] exists."""
        M = self.M; ok = (idx >= 0) & (idx < L)
        return ok & (M.nxt[np.clip(idx, 0, L - 1)] <= idx + TOL)

    def cands(self, h: Hyp) -> Cands:
        M, t, k = self.M, self.grid, h.kind
        if h.family in ("G1", "G7"):
            z = (self.z_gold if h.family == "G1" else self.z_eur)[h.L]
            with np.errstate(invalid="ignore"):
                fire = np.abs(z) >= Z_THRESH
            d = np.where(fire, h.d * np.sign(np.nan_to_num(z)), 0).astype(np.int8)
            return Cands(t, t + 1, None, d, hold=h.H * 60)
        if k == "g6":
            return Cands(t, t + 1, None, (h.d * self.g6).astype(np.int8), hold=h.H * 60)
        if k == "hod":
            tt = t[(t + O) // 60 % 24 == h.param]
            return Cands(tt, tt + 1, None, np.ones(len(tt), np.int8), hold=60)
        if k == "dow":
            ds = np.nonzero(self.wd == h.param)[0]
            tt = self.mid0[ds]
            if h.param == 4:       # Friday: exit at the open of the last bar of the trading week (Friday close); weekend rule waived
                ex = M.prv[np.minimum(tt + 1439, L - 1)]
                ok = ex > tt + 1
                return Cands(tt[ok], tt[ok] + 1, ex[ok], np.ones(ok.sum(), np.int8), waive=np.ones(ok.sum(), bool))
            return Cands(tt, tt + 1, None, np.ones(len(tt), np.int8), hold=1440)
        if k == "g3":
            ds = np.nonzero(self.wd < 5)[0]
            t7 = self.mid0[ds] + 420
            s0 = self.mid0[ds]
            okk = self._near(s0) & (M.prv[t7 - 2] >= t7 - 2 - TOL) & (t7 < L)
            ds, t7, s0 = ds[okk], t7[okk], s0[okk]
            start = M.o[M.nxt[s0]]                          # open of the first bar at/after 00:00
            end = M.asof(M.c, M.prv, t7 - 2)                # close of the last bar closed by 06:59
            with np.errstate(invalid="ignore", divide="ignore"):
                x = np.log(end / start)
            return Cands(t7, t7 + 1, None, (h.d * np.sign(np.nan_to_num(x))).astype(np.int8), hold=h.H * 60)
        if k == "g4":
            ds = np.nonzero(self.wd < 5)[0]
            a = self.lon15[ds]                              # 15:00 Europe/London on this date, in UTC minutes
            a = a[(a > 60 * 2) & (a < L - 1)]
            c1 = M.asof(M.c, M.prv, a - 2); c0 = M.asof(M.c, M.prv, a - 2 - 60)
            with np.errstate(invalid="ignore", divide="ignore"):
                x = np.log(c1 / c0)                         # return over the 60 min before the anchor
            return Cands(a, a + 1, None, (h.d * np.sign(np.nan_to_num(x))).astype(np.int8), hold=h.H * 60)
        if k == "g5":
            ym = np.array([d.year * 12 + d.month for d in self.days])
            trading = (self.day_hours >= 6) & self._near(self.mid0 + 1) & self._near(self.lon16)
            sel = []
            for key in np.unique(ym):
                ix = np.nonzero((ym == key) & trading)[0]
                if len(ix): sel.append(ix[-1])
            sel = np.array(sel, dtype=np.int64)
            tt = self.mid0[sel]
            return Cands(tt, tt + 1, self.lon16[sel], np.full(len(tt), h.d, np.int8))
        if k == "g8":
            B = np.nonzero(M.has)[0]
            gi = np.nonzero(np.diff(B) >= 36 * 60)[0]       # closure >= 36 h
            last, reo = B[gi], B[gi + 1]
            wd_last = ((last + O) // 1440 + 3) % 7          # epoch day 0 is a Thursday -> Monday=0
            wd_reo = ((reo + O) // 1440 + 3) % 7
            f = (wd_last == 4) & np.isin(wd_reo, (6, 0)) & (reo + 4 < L)
            last, reo = last[f], reo[f]
            with np.errstate(invalid="ignore", divide="ignore"):
                x = M.o[reo] / M.c[last] - 1                # reopen open vs Friday close (both bid)
            sg = np.where(np.abs(x) >= 0.001, np.sign(x), 0)
            return Cands(reo + 4, reo + 5, None, (h.d * sg).astype(np.int8), hold=h.H * 60)
        raise ValueError(h)
