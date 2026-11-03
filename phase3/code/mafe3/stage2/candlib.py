"""Track A machinery (section 3): candidate generation, thresholds, non-overlapping episodes, statistics. Shared by discovery and validation runs."""
from __future__ import annotations
from itertools import combinations
import numpy as np
from scipy import stats as sps
from . import features as Fz
from .trades import greedy
from ..engine import block_bootstrap_p

TAILS = {"lo10": (0.10, "le"), "hi10": (0.90, "ge"), "lo20": (0.20, "le"), "hi20": (0.80, "ge")}
SINGLE_TAILS = ("lo10", "hi10"); PAIR_TAILS = ("lo20", "hi20")
FEATS = Fz.NONTIME                                      # 34 features; time features only as session context
SESS = (0, 1, 2, 3)

def fit_thresholds(Z, rows):
    """Percentile cut-offs of each non-time z-feature on the given rows (discovery-A only)."""
    ix = {n: i for i, n in enumerate(Fz.NAMES)}
    thr = {}
    for f in FEATS:
        v = Z[rows, ix[f]].astype(np.float64); v = v[~np.isnan(v)]
        thr[f] = {q: float(np.quantile(v, p)) for q, p in (("q10", .10), ("q20", .20), ("q80", .80), ("q90", .90))}
    return thr

def tail_mask(Z, thr, f, tail):
    z = Z[:, Fz.NAMES.index(f)]
    return (z <= thr[f]["q10" if tail == "lo10" else "q20"]) if tail.startswith("lo") else (z >= thr[f]["q90" if tail == "hi10" else "q80"])

def mask_specs():
    """All signal definitions (before horizon and direction). A spec is a tuple: ("S", f, tail) | ("P", f1, t1, f2, t2) | ("C", sess, f, tail)."""
    specs = [("S", f, t) for f in FEATS for t in SINGLE_TAILS]
    for f1, f2 in combinations(FEATS, 2):
        if Fz.CONCEPT_OF[f1] == Fz.CONCEPT_OF[f2]: continue
        specs += [("P", f1, t1, f2, t2) for t1 in PAIR_TAILS for t2 in PAIR_TAILS]
    specs += [("C", s, f, t) for s in SESS for f in FEATS for t in PAIR_TAILS]
    return specs

def spec_id(s): return "|".join(str(v) for v in s)
def complexity(s): return 1 if s[0] == "S" else 2

class Masks:
    def __init__(self, Z, thr):
        self.Z, self.thr = Z, thr
        self.cache = {}
        self.sess = Z[:, Fz.NAMES.index("t_sess")]
    def tail(self, f, t):
        k = (f, t)
        if k not in self.cache: self.cache[k] = tail_mask(self.Z, self.thr, f, t)
        return self.cache[k]
    def get(self, s):
        if s[0] == "S": return self.tail(s[1], s[2])
        if s[0] == "P": return self.tail(s[1], s[2]) & self.tail(s[3], s[4])
        return (self.sess == s[1]) & self.tail(s[2], s[3])

def episodes(mask, oc, H, td, period):
    """Greedy non-overlapping episodes (positions into the grid) for a signal mask at horizon H inside a boolean period mask."""
    r = oc.by[H]
    pos = np.nonzero(mask & r["valid"] & period)[0]
    if len(pos) == 0: return pos
    return pos[greedy(td[pos], r["x"][pos])]

def nets(oc, H, pos, d):
    r = oc.by[H]
    g = d * r["gross"][pos]
    return g, g - r["cost35"][pos] - r["swap"][pos], g - r["cost50"][pos] - r["swap"][pos]

def tstat(x):
    n = len(x)
    if n < 3: return np.nan, 1.0
    s = x.std(ddof=1)
    if s == 0: return np.nan, 1.0
    t = x.mean() / (s / np.sqrt(n))
    return float(t), float(sps.t.sf(t, n - 1))

def summarize_ep(oc, H, pos, d, boot=False):
    g, n35, n50 = nets(oc, H, pos, d)
    n = len(pos)
    out = dict(n=n)
    if n == 0:
        return out | dict(gross=np.nan, cost=np.nan, swap=np.nan, net35=np.nan, net50=np.nan, t=np.nan, p=1.0, p_boot=np.nan, days=0, pos_years=0, years="")
    r = oc.by[H]
    t, p = tstat(n35)
    out |= dict(gross=float(g.mean()), cost=float(r["cost35"][pos].mean()), swap=float(r["swap"][pos].mean()), net35=float(n35.mean()), net50=float(n50.mean()),
                t=t, p=p, days=int(len(np.unique(oc.day[pos]))))
    out["p_boot"] = float(block_bootstrap_p(n35, oc.week[pos])) if boot else np.nan
    yrs = oc.year[pos]
    ys = sorted(set(yrs.tolist()))
    out["years"] = ";".join(f"{y}:{n35[yrs == y].mean():.2f}({int((yrs == y).sum())})" for y in ys)
    out["_year_net"] = {y: float(n35[yrs == y].mean()) for y in ys}
    out["pos_years"] = int(sum(v > 0 for v in out["_year_net"].values()))
    return out

def overlap_frac(e_i, x_i, e_j, x_j):
    """share of episodes i whose [e, x) interval intersects an interval of j. Both sorted, each non-overlapping."""
    if len(e_i) == 0 or len(e_j) == 0: return 0.0
    a = np.searchsorted(e_j, x_i, "left"); b = np.searchsorted(x_j, e_i, "right")
    return float((a > b).mean())
