"""MAFE-1C core: cost components (Roll spread proxy, latency slippage, Kyle-lambda impact), frozen-model rules, one-day pass.
Reuses mafe1r/code/mafe_core.py unchanged (0056 definition, replay, feature bars)."""
import sys, os, json, datetime as dt
import numpy as np, polars as pl
sys.path.insert(0, "/home/ubuntu/mafe-research-archive/mafe1r/code")
from mafe_core import side_of, run_length, anchor_mask, event_response, clock_response, replay, bars_for_day, FeatureState, HS, FEAT_W

D_MS = 500
LAT_MS = (100, 250, 500)
ROLL_W, ROLL_MIN = 1000, 200
T_IMP = 300
CUTOFF = dt.date(2025, 12, 31)
FEATS = [f"{f}_{w}" for w in (300, 3600) for f in ("rate", "vol", "rv", "chgfreq", "evperchg", "meansize", "burst")]
EDGES_FILE = "/home/ubuntu/mafe-research-archive/mafe1r/results/m4_bin_edges_2023.json"
Q_SMALL, Q_BIG = 0.001, 0.01

def roll_at(price, idx, tick, W=ROLL_W, nmin=ROLL_MIN):
    """Roll (1926) spread proxy in price units at event indices idx, trailing W aggTrade price changes inside the supplied array.
    S = 2*sqrt(max(-cov(dp_t, dp_{t-1}),0)); max(S, tick); fewer than nmin changes -> tick."""
    dp = np.diff(price, prepend=price[0]); dpl = np.r_[0.0, dp[:-1]]
    z = lambda a: np.r_[0.0, np.cumsum(a)]
    Sx, Sy, Sxy = z(dp), z(dpl), z(dp * dpl)
    a = np.maximum(idx - W + 1, 2); n = idx - a + 1
    nn = np.maximum(n, 1)
    sx = (Sx[idx + 1] - Sx[a]) / nn; sy = (Sy[idx + 1] - Sy[a]) / nn; sxy = (Sxy[idx + 1] - Sxy[a]) / nn
    cov = sxy - sx * sy
    S = 2 * np.sqrt(np.maximum(-cov, 0))
    return np.where(n >= nmin, np.maximum(S, tick), tick)

class ImpactState:
    """Kyle-type lambda (bps per BTC) on trailing 300 completed 1-s bars: sum(dp_bps*v)/sum(v^2), v signed volume."""
    def __init__(self, tail=None): self.tail = tail
    def build(self, ts, qty, s, day0, Pf, last_price_prev):
        sec = ((ts - day0) // 1000).astype(np.int64)
        v = np.bincount(sec, weights=qty * s, minlength=86400)
        prev = np.r_[last_price_prev if last_price_prev is not None else Pf[0], Pf[:-1]]
        d = 1e4 * (Pf - prev) / prev
        if self.tail is not None: dd = np.r_[self.tail["d"], d]; vv = np.r_[self.tail["v"], v]; self.valid0 = 0
        else: dd = np.r_[np.zeros(T_IMP), d]; vv = np.r_[np.zeros(T_IMP), v]; self.valid0 = T_IMP
        z = lambda a: np.r_[0.0, np.cumsum(a)]
        self.cxy, self.cxx = z(dd * vv), z(vv * vv)
        self.newtail = dict(d=d[-T_IMP:], v=v[-T_IMP:])
    def lam(self, t_ms, day0):
        k = ((t_ms - day0) // 1000).astype(np.int64) + T_IMP; a = k - T_IMP
        ok = a >= self.valid0; a = np.maximum(a, 0)
        sxy = self.cxy[k] - self.cxy[a]; sxx = self.cxx[k] - self.cxx[a]
        with np.errstate(divide="ignore", invalid="ignore"):
            lam = np.where(sxx > 0, sxy / sxx, 0.0)
        return np.where(ok, np.maximum(lam, 0.0), np.nan)

# ---------------- frozen models
def cell_index(edges, rv, rate, chg):
    return np.digitize(rv, edges["rv_300"]) * 9 + np.digitize(rate, edges["rate_300"]) * 3 + np.digitize(chg, edges["chgfreq_300"])
def ridge_X(rv, rate, chg): return np.column_stack([np.log(np.maximum(rv, 1e-9)), np.log(np.maximum(rate, 1e-9)), chg])
def predict(M, edges, rv, rate, chg):
    """returns (pred gross_500 bps, pred variable cost bps = spread+impact(0.001)); NaN where a state variable is NaN."""
    bad = np.isnan(rv) | np.isnan(rate) | np.isnan(chg)
    rv0, rate0, chg0 = np.where(bad, 1.0, rv), np.where(bad, 1.0, rate), np.where(bad, 0.5, chg)
    if M["type"] == "bin":
        c = cell_index(edges, rv0, rate0, chg0); pg = np.array(M["pg"])[c]; pv = np.array(M["pv"])[c]
    else:
        X = (ridge_X(rv0, rate0, chg0) - np.array(M["mu"])) / np.array(M["sd"]); X1 = np.column_stack([np.ones(len(X)), X])
        pg = X1 @ np.array(M["bg"]); pv = X1 @ np.array(M["bv"])
    return np.where(bad, np.nan, pg), np.where(bad, np.nan, pv)
K_FIXED = {"K2": 10.0, "K3": 2.0 + 5.0 + 0.65, "K4": 20.0}
K_VARSHARE = {"K2": 1.0, "K3": 0.5, "K4": 1.0}
def rule_net_pred(K, pg, pv, price, tick):
    if K == "K1": return pg - (2.1 + tick / price * 1e4)
    return pg - (K_FIXED[K] + K_VARSHARE[K] * pv)

def parse_rule(r):
    """'ALL' or '<MODEL>_<K>' -> (model, K)"""
    return (None, None) if r == "ALL" else tuple(r.split("_"))

def process_day(ts, price, qty, bm, day0, tick, head, state, rules, frozen=None, anchors=False):
    """One day. head=(ts,price) of the next 310 s (or None). state: dict(last_price, tail, itail, free{rule}) or {}.
    Returns (dict rule -> polars trades, anchors df or None, new state, daily dict)."""
    n = len(ts)
    if head is not None and len(head[0]): ts_e = np.r_[ts, head[0]]; price_e = np.r_[price, head[1]]
    else: ts_e, price_e = ts, price
    s = side_of(bm); L = run_length(s)
    cnt, vol, chg, Pf = bars_for_day(ts, price, qty, day0, state.get("last_price"))
    fs = FeatureState(state.get("tail")); fs.build(cnt, vol, chg, Pf)
    im = ImpactState(state.get("itail")); im.build(ts, qty, s, day0, Pf, state.get("last_price"))
    sig = np.flatnonzero(L >= 5)
    edges = frozen["edges"] if frozen else None
    models = frozen["models"] if frozen else {}
    pre = None
    if any(r != "ALL" for r in rules):
        f = fs.feats(ts[sig], day0)
        pre = {}
        for mn, M in models.items(): pre[mn] = predict(M, edges, f["rv_300"], f["rate_300"], f["chgfreq_300"])
    free = dict(state.get("free", {}))
    out = {}
    for r in rules:
        mn, K = parse_rule(r)
        if r == "ALL": sg = sig
        else:
            pg, pv = pre[mn]; np_ = rule_net_pred(K, pg, pv, price[sig], tick); sg = sig[np_ > 0]
        tr, free[r] = replay(ts_e, price_e, sg, s, D_MS, free.get(r, 0))
        if not tr: continue
        a = np.array(tr); si, ei, xi = a[:, 0], a[:, 1], a[:, 2]
        sd = s[si].astype(np.float64)
        psig, pen, pex = price_e[si], price_e[ei], price_e[xi]
        T = dict(rule=np.full(len(si), r), date=np.full(len(si), dt.datetime.fromtimestamp(day0 / 1000, dt.timezone.utc).date().isoformat()),
                 sig_ts=ts_e[si], entry_ts=ts_e[ei], exit_ts=ts_e[xi], side=s[si], p_sig=psig, p_entry=pen, p_exit=pex,
                 gross_bps=sd * (pex - pen) / pen * 1e4, hour=((ts_e[si] - day0) // 3600000).astype(np.int8))
        for d in LAT_MS:
            j = np.minimum(np.searchsorted(ts_e, ts_e[si] + d, side="left"), len(ts_e) - 1)
            T[f"lat{d}_bps"] = sd * (price_e[j] - psig) / psig * 1e4
        S_sig, S_exit = roll_at(price_e, si, tick), roll_at(price_e, xi, tick)
        T["roll_sig_usd"], T["roll_exit_usd"] = S_sig, S_exit
        T["spread_bps"] = 0.5 * (S_sig + S_exit) / pen * 1e4
        lam = im.lam(ts_e[si], day0); T["lam_bps_per_btc"] = lam
        T["impact_small_bps"] = np.nan_to_num(2 * lam * Q_SMALL); T["impact_big_bps"] = np.nan_to_num(2 * lam * Q_BIG)
        T["tick_bps"] = tick / pen * 1e4
        T.update(fs.feats(ts_e[si], day0) if True else {})
        if frozen:
            rv, rate, chg = T["rv_300"], T["rate_300"], T["chgfreq_300"]
            for mn, M in models.items():
                pg, pv = predict(M, edges, rv, rate, chg); T[f"pg_{mn}"] = pg; T[f"pv_{mn}"] = pv
        out[r] = pl.DataFrame(T)
    A = None
    if anchors:
        am = anchor_mask(ts); aidx = np.flatnonzero(am)
        Ad = dict(date=np.full(len(aidx), dt.datetime.fromtimestamp(day0 / 1000, dt.timezone.utc).date().isoformat()), ts=ts[aidx], L=L[aidx])
        for h in HS: Ad[f"R{h}"] = event_response(price, s, aidx, h)
        Ad["R300s"] = clock_response(ts_e, price_e, s, aidx)
        A = pl.DataFrame(Ad)
    r1 = np.diff(np.log(Pf))
    daily = dict(date=dt.datetime.fromtimestamp(day0 / 1000, dt.timezone.utc).date().isoformat(), rows=int(n), n_buy=int((s > 0).sum()), mean_qty=float(qty.mean()), med_qty=float(np.median(qty)),
                 vol_btc=float(qty.sum()), open=float(price[0]), close=float(price[-1]), rv_day_bps=float(np.sqrt((r1 ** 2).sum()) * 1e4), chgfreq=float((np.diff(price) != 0).mean()),
                 n_L5=int(len(sig)), n_anchors=int(0 if A is None else len(A)), roll_med_usd=float(np.median(roll_at(price, np.arange(1000, n, 997), tick))) if n > 2000 else None,
                 n_trades={r: int(len(df)) for r, df in out.items()})
    new = dict(last_price=float(price[-1]), tail=fs.newtail, itail=im.newtail, free=free)
    return out, A, new, daily
