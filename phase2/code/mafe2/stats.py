"""Per-hypothesis statistics, weekly block bootstrap, Benjamini-Hochberg."""
from __future__ import annotations
import numpy as np
from datetime import datetime, timedelta
from scipy import stats as sps

BOOT_B = 10_000
_T0 = datetime(2020, 1, 1)


def grid_calendar(ngrid: int):
    """per grid hour: year, quarter label (year*10+q), ISO week key (iso_year*100+week)."""
    yr = np.empty(ngrid, dtype=np.int32); q = np.empty(ngrid, dtype=np.int32); wk = np.empty(ngrid, dtype=np.int32)
    days = {}
    for g in range(0, ngrid, 24):
        d = (_T0 + timedelta(days=g // 24))
        iso = d.isocalendar()
        days[g // 24] = (d.year, d.year * 10 + (d.month - 1) // 3 + 1, iso[0] * 100 + iso[1])
    for g in range(ngrid):
        yr[g], q[g], wk[g] = days[g // 24]
    return yr, q, wk


def t_test(x: np.ndarray):
    """(mean, t, p_one_sided_greater, p_two_sided); ddof=1."""
    n = len(x)
    if n < 3:
        return (float(np.mean(x)) if n else np.nan), np.nan, 1.0, 1.0
    m, s = x.mean(), x.std(ddof=1)
    if s == 0:
        return float(m), np.nan, 1.0, 1.0
    t = m / (s / np.sqrt(n))
    return float(m), float(t), float(sps.t.sf(t, n - 1)), float(2 * sps.t.sf(abs(t), n - 1))


def block_bootstrap_p(x: np.ndarray, blocks: np.ndarray, B: int = BOOT_B, seed: int = 12345) -> float:
    """One-sided p for mean>0 by resampling ISO-week blocks with replacement, null-centred at zero.
    p = (1 + #{boot_mean - obs_mean >= obs_mean}) / (B + 1)."""
    if len(x) < 3:
        return 1.0
    ub, inv = np.unique(blocks, return_inverse=True)
    W = len(ub)
    s = np.bincount(inv, weights=x, minlength=W); c = np.bincount(inv, minlength=W).astype(float)
    obs = x.mean()
    rng = np.random.default_rng(seed)
    cnt = rng.multinomial(W, np.full(W, 1.0 / W), size=B).astype(float)
    den = cnt @ c
    bm = np.where(den > 0, (cnt @ s) / np.where(den > 0, den, 1), np.nan)
    ok = ~np.isnan(bm)
    return float((1 + np.sum((bm[ok] - obs) >= obs)) / (ok.sum() + 1))


def bh(p: np.ndarray, q: float) -> np.ndarray:
    """Benjamini-Hochberg step-up; returns boolean rejection array."""
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p, kind="stable")
    thr = (np.arange(1, m + 1) / m) * q
    below = p[order] <= thr
    rej = np.zeros(m, bool)
    if below.any():
        k = np.max(np.nonzero(below)[0])
        rej[order[: k + 1]] = True
    return rej


def summarize(gross, fund, g, cal, with_boot=True) -> dict:
    """Statistics for one hypothesis on one symbol. cal = (year, quarter, week) arrays on the grid."""
    yr, qt, wk = cal
    n = len(gross)
    n12, n8 = gross + fund - 12.0, gross + fund - 8.0
    out = {"n": n}
    if n == 0:
        out.update(mean_gross=np.nan, mean_funding=np.nan, mean_net12=np.nan, mean_net8=np.nan, median_net12=np.nan, hit_rate=np.nan,
                   t_net12=np.nan, p_net12_1s=1.0, p_net12_2s=1.0, p_boot=1.0, p_gross_2s=1.0, t_gross=np.nan)
    else:
        mn, t, p1, p2 = t_test(n12)
        mg, tg, _, p2g = t_test(gross)
        out.update(mean_gross=float(gross.mean()), mean_funding=float(fund.mean()), mean_net12=mn, mean_net8=float(n8.mean()),
                   median_net12=float(np.median(n12)), hit_rate=float((n12 > 0).mean()), t_net12=t, p_net12_1s=p1, p_net12_2s=p2,
                   p_boot=block_bootstrap_p(n12, wk[g]) if with_boot else np.nan, p_gross_2s=p2g, t_gross=tg)
    for y in (2020, 2021, 2022, 2023):
        mk = yr[g] == y if n else np.zeros(0, bool)
        out[f"n_{y}"] = int(mk.sum()); out[f"net12_{y}"] = float(n12[mk].mean()) if mk.any() else np.nan
    for y in (2020, 2021, 2022, 2023):
        for qq in (1, 2, 3, 4):
            mk = qt[g] == y * 10 + qq if n else np.zeros(0, bool)
            out[f"n_{y}Q{qq}"] = int(mk.sum()); out[f"net12_{y}Q{qq}"] = float(n12[mk].mean()) if mk.any() else np.nan
    return out
