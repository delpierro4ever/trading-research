"""Execution engine and statistics for MAFE3 (see phase3/docs/PREREGISTRATION.md incl. Amendment 2). Prices are BID."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "phase2" / "code"))
from mafe2.stats import t_test, block_bootstrap_p, bh      # reused phase-2 statistics (t-test, weekly block bootstrap, BH)
from .market import Market, O, L, D0, TOL, BIG, in_closure, week_idx, abs_min

COST_USD = {"primary": 0.35, "c20": 0.20, "c60": 0.60}      # $/oz round trip; primary = Amendment 2 fixed cost


class Cands:
    """Candidate trades. t: decision minute (dense idx); entry: target minute of the entry bar; exit_: absolute target minute of the exit
    bar, used where hold == 0; hold: minutes after the ACTUAL entry bar (exit = entry + H); d in {-1,0,+1}; waive: skip weekend rule."""
    def __init__(self, t, entry, exit_, d, waive=None, hold=None):
        self.t = np.asarray(t, np.int64); self.entry = np.asarray(entry, np.int64)
        n = len(self.t)
        self.exit = np.full(n, -1, np.int64) if exit_ is None else np.asarray(exit_, np.int64)
        self.hold = np.zeros(n, np.int64) if hold is None else np.broadcast_to(np.asarray(hold, np.int64), (n,)).copy()
        self.d = np.asarray(d, np.int8)
        self.waive = np.zeros(n, bool) if waive is None else np.asarray(waive, bool)
    def __len__(self): return len(self.t)
    def with_d(self, d): return Cands(self.t, self.entry, self.exit, d, self.waive, self.hold)


def resolve(M: Market, entry, exit_, hold=None, waive=None):
    """Resolve targets to actual bars (first bar with label >= target within TOL minutes). Returns (e_bar, x_bar, valid)."""
    entry = np.asarray(entry); exit_ = np.asarray(exit_)
    inr = (entry >= 0) & (entry < L)
    e = np.where(inr, M.nxt[np.clip(entry, 0, L - 1)], BIG)
    ok = inr & (e < L) & (e - entry <= TOL)
    xt = exit_ if hold is None else np.where(np.asarray(hold) > 0, e + np.asarray(hold), exit_)
    inx = ok & (xt >= 0) & (xt < L)
    x = np.where(inx, M.nxt[np.clip(xt, 0, L - 1)], BIG)
    ok = inx & (x < L) & (x - xt <= TOL) & (x > e)
    eC, xC = np.clip(e, 0, L - 1), np.clip(x, 0, L - 1)
    span = in_closure(abs_min(eC)) | in_closure(abs_min(xC) - 1) | (week_idx(abs_min(eC)) != week_idx(abs_min(xC) - 1))
    if waive is not None: span = span & ~np.asarray(waive, bool)
    return e, x, ok & ~span


def trade_numbers(M: Market, e, x, d):
    pe = M.o[e]; px = M.o[x]
    gross = d * np.log(px / pe) * 1e4
    return gross, {k: v / pe * 1e4 for k, v in COST_USD.items()}, M.swap_bps(e, x)


def run(M: Market, c: Cands, start=D0) -> dict:
    """Greedy non-overlapping execution. A decision at t is admissible if t >= exit bar of the previous accepted trade."""
    live = (c.d != 0) & (c.t >= start)
    idx = np.nonzero(live)[0]
    idx = idx[np.argsort(c.t[idx], kind="stable")]
    e, x, ok = resolve(M, c.entry[idx], c.exit[idx], c.hold[idx], c.waive[idx])
    keep, nxt_free = [], -1
    for k in np.nonzero(ok)[0]:
        if c.t[idx[k]] < nxt_free: continue
        keep.append(k); nxt_free = x[k]
    keep = np.array(keep, dtype=np.int64)
    sel = idx[keep]; e, x = e[keep], x[keep]; d = c.d[sel].astype(np.int64)
    g, co, sw = trade_numbers(M, e, x, d)
    return dict(t=c.t[sel], e=e, x=x, d=d, gross=g, cost=co["primary"], c20=co["c20"], c60=co["c60"], swap=sw)


def flip(ep):
    return {**ep, "d": -ep["d"], "gross": -ep["gross"]}


def net(ep, kind="primary"):
    base = {"primary": ep["cost"], "c20": ep["c20"], "c60": ep["c60"], "noswap": ep["cost"]}[kind]
    return ep["gross"] - base - (0.0 if kind == "noswap" else ep["swap"])


def episode_calendar(e):
    """year, quarter label (year*10+q), ISO-week key of the entry bar."""
    ts = (e + O).astype("datetime64[m]") if len(e) else np.array([], "datetime64[m]")
    idx = pd.DatetimeIndex(ts)
    iso = idx.isocalendar()
    return idx.year.to_numpy(), (idx.year * 10 + (idx.month - 1) // 3 + 1).to_numpy(), (iso.year.to_numpy() * 100 + iso.week.to_numpy()).astype(int)


def forward_drift(M: Market, grid, H_min):
    """Mean H gross of a LONG at every grid hour, by quarter (same execution rules incl. weekend rule, no non-overlap)."""
    g = grid[grid >= D0]
    e, x, ok = resolve(M, g + 1, np.full(len(g), -1), hold=np.full(len(g), H_min))
    e, x = e[ok], x[ok]
    gr = np.log(M.o[x] / M.o[e]) * 1e4
    _, q, _ = episode_calendar(e)
    return pd.Series(gr).groupby(q).mean().to_dict()


def summarize(ep: dict, M: Market, drift: dict, years=range(2010, 2020), boot=True) -> dict:
    n = len(ep["gross"]); out = {"n": n}
    for y in years: out[f"n_{y}"] = 0; out[f"net_{y}"] = np.nan
    nt = net(ep) if n else np.array([])
    if n == 0:
        return out | dict(n_long=0, n_short=0, gross_long=np.nan, gross_short=np.nan, share_one_side=np.nan, mean_net_c20=np.nan, mean_net_c60=np.nan,
                          mean_net_noswap=np.nan, median_hold_h=np.nan, mean_gross=np.nan, mean_cost=np.nan, mean_swap=np.nan, mean_net=np.nan, median_net=np.nan, hit_rate=np.nan,
                          t_net=np.nan, p_net_1s=1.0, p_boot=1.0, p_gross_2s=1.0, t_gross=np.nan)
    yr, qt, wk = episode_calendar(ep["e"])
    mn, t, p1, p2 = t_test(nt); mg, tg, _, p2g = t_test(ep["gross"])
    out |= dict(mean_gross=float(mg), mean_cost=float(ep["cost"].mean()), mean_swap=float(ep["swap"].mean()), mean_net=float(mn),
                median_net=float(np.median(nt)), hit_rate=float((nt > 0).mean()), t_net=float(t), p_net_1s=float(p1),
                p_boot=float(block_bootstrap_p(nt, wk)) if boot else np.nan, p_gross_2s=float(p2g), t_gross=float(tg),
                mean_net_c20=float(net(ep, "c20").mean()), mean_net_c60=float(net(ep, "c60").mean()),
                mean_net_noswap=float(net(ep, "noswap").mean()),
                median_hold_h=float(np.median(ep["x"] - ep["e"]) / 60))
    for y in years:
        mk = yr == y
        out[f"n_{y}"] = int(mk.sum()); out[f"net_{y}"] = float(nt[mk].mean()) if mk.any() else np.nan
    lo, sh = ep["d"] > 0, ep["d"] < 0
    out |= dict(n_long=int(lo.sum()), n_short=int(sh.sum()),
                gross_long=float(ep["gross"][lo].mean()) if lo.any() else np.nan,
                gross_short=float(ep["gross"][sh].mean()) if sh.any() else np.nan,
                share_one_side=float(max(lo.mean(), sh.mean())))
    return out
