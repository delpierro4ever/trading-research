"""Track B machinery (section 4): design matrices, ridge (alpha = 10) and LightGBM (fixed hyper-parameters), trading rule, statistics."""
from __future__ import annotations
import numpy as np
import lightgbm as lgb
from . import features as Fz
from .trades import greedy
from .candlib import tstat
from ..engine import block_bootstrap_p

ALPHA = 10.0
LGB_PARAMS = dict(objective="regression", learning_rate=0.03, num_leaves=15, min_data_in_leaf=2000, feature_fraction=0.7, bagging_fraction=0.7,
                  bagging_freq=1, seed=7, num_threads=3, verbose=-1)      # bagging needs bagging_freq >= 1 (decision: 1); everything else LightGBM default
LGB_ROUNDS = 300
IX = {n: i for i, n in enumerate(Fz.NAMES)}
ZCLIP = 5.0

def design_ridge(Z):
    """45 inputs: 34 non-time z-features (clipped to +-5, NaN -> 0 = training mean), hour sin/cos, session one-hot (4), weekday one-hot (Mon-Fri)."""
    cols = [np.nan_to_num(np.clip(Z[:, IX[n]], -ZCLIP, ZCLIP), nan=0.0) for n in Fz.NONTIME]
    cols += [Z[:, IX["t_hsin"]], Z[:, IX["t_hcos"]]]
    cols += [(Z[:, IX["t_sess"]] == s).astype(np.float32) for s in range(4)]
    cols += [(Z[:, IX["t_dow"]] == d).astype(np.float32) for d in range(5)]
    return np.column_stack(cols).astype(np.float32)

def ridge_names():
    return list(Fz.NONTIME) + ["t_hsin", "t_hcos"] + [f"sess{s}" for s in range(4)] + [f"dow{d}" for d in range(5)]

def fit_ridge(X, y):
    mu, sd = X.mean(0, dtype=np.float64), X.std(0, dtype=np.float64)
    sd = np.where(sd > 0, sd, 1.0)
    Xs = (X - mu) / sd
    yb = y.mean(dtype=np.float64)
    G = Xs.T.astype(np.float64) @ Xs.astype(np.float64)
    beta = np.linalg.solve(G + ALPHA * np.eye(X.shape[1]), Xs.T.astype(np.float64) @ (y - yb))
    return dict(mu=mu, sd=sd, beta=beta, b0=yb)

def predict_ridge(m, X): return (((X - m["mu"]) / m["sd"]) @ m["beta"] + m["b0"]).astype(np.float64)

def fit_lgb(Z, y):
    return lgb.train(LGB_PARAMS, lgb.Dataset(Z, label=y), num_boost_round=LGB_ROUNDS)

def trade_rule(pred, r, td, rows):
    """pred for `rows` (positions into the grid, sorted by time). long if pred > cost35 + swap, short if pred < -(same). Greedy non-overlap.
    Returns positions (into the grid) and directions."""
    thr = r["cost35"][rows] + r["swap"][rows]
    d = np.where(pred > thr, 1, np.where(pred < -thr, -1, 0))
    sel = np.nonzero(d != 0)[0]
    if len(sel) == 0: return rows[:0], d[:0]
    pos = rows[sel]
    keep = greedy(td[pos], r["x"][pos])
    return pos[keep], d[sel][keep]

def trade_stats(oc, H, pos, d, years):
    r = oc.by[H]; n = len(pos)
    out = dict(n=n)
    if n == 0: return out | dict(gross=np.nan, cost=np.nan, swap=np.nan, net35=np.nan, net50=np.nan, t=np.nan, p_t=1.0, p_boot=1.0, days=0, pos_years=0, year_net={}, n_long=0)
    g = d * r["gross"][pos]; n35 = g - r["cost35"][pos] - r["swap"][pos]; n50 = g - r["cost50"][pos] - r["swap"][pos]
    t, p = tstat(n35)
    yr = oc.year[pos]
    yn = {int(y): float(n35[yr == y].mean()) for y in years if (yr == y).any()}
    return dict(n=n, gross=float(g.mean()), cost=float(r["cost35"][pos].mean()), swap=float(r["swap"][pos].mean()), net35=float(n35.mean()), net50=float(n50.mean()),
                t=t, p_t=p, p_boot=float(block_bootstrap_p(n35, oc.week[pos])), days=int(len(np.unique(oc.day[pos]))),
                pos_years=int(sum(v > 0 for v in yn.values())), year_net=yn, n_long=int((d > 0).sum()))
