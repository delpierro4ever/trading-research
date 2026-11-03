"""Stage-2 feature tests: lookahead (garbage after t-1 min => identical features), sensitivity, shape/NaN report.
Run (from phase3/code): python -m mafe3.stage2.test_features   -> prints a JSON report; exit 1 on failure. Features only; no returns."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
import numpy as np
from . import features as Fz

def utc(*a): return datetime(*a, tzinfo=timezone.utc)

def make_patch(cut_label_abs, seed):
    """Replace values of every bar with label (abs epoch minute) > cut by garbage; availability kept."""
    def patch(A, a0):
        rng = np.random.default_rng(seed)
        k = cut_label_abs - a0
        for key in list(A):
            a = A[key]; tail = a[k + 1:]
            med = np.nanmedian(a[:k + 1])
            a[k + 1:] = np.where(np.isnan(tail), np.nan, rng.uniform(0.5, 2.0, len(tail)) * med)
    return patch

def lookahead(n_cut=8):
    start, end = utc(2013, 12, 1), utc(2014, 2, 15)          # spans a year-chunk boundary
    
    tt, Xr, Z = Fz.build(start, end)
    rng = np.random.default_rng(3)
    cands = tt[(tt > tt[0] + 1440 * 30)]
    stars = list(rng.choice(cands, n_cut - 2, replace=False))
    # targeted: right after a NY rollover (~21:00/22:00 UTC) and the first grid point after a Sunday reopen
    stars += [int(cands[(cands % 1440 >= 21 * 60 + 30) & (cands % 1440 < 22 * 60 + 30)][40])]
    stars += [int(cands[((cands // 1440 + 3) % 7 == 6) & (cands % 1440 >= 22 * 60 + 10)][3])]
    out = {"cutoffs": [], "mismatch": [], "sens_changed": 0, "sens_total": 0}
    for ts in stars:
        ts = int(ts)
        t1, Xr1, Z1 = Fz.build(start, end, patch=make_patch(ts - 2, ts))
        assert np.array_equal(tt, t1)
        m = tt <= ts
        for name, a, b in (("raw", Xr, Xr1), ("z", Z, Z1)):
            same = (a[m] == b[m]) | (np.isnan(a[m]) & np.isnan(b[m]))
            bad = np.nonzero(~same.all(axis=0))[0]
            for k in bad: out["mismatch"].append((ts, name, Fz.NAMES[k], int((~same[:, k]).sum())))
        # sensitivity: one more bar (label ts-2) garbage must change non-time features at ts
        t2, Xr2, Z2 = Fz.build(start, end, patch=make_patch(ts - 3, ts))
        i = int(np.searchsorted(tt, ts))
        diff = [Fz.NAMES[k] for k in range(Fz.NF) if Fz.NAMES[k] not in Fz.TIME and not (Xr[i, k] == Xr2[i, k] or (np.isnan(Xr[i, k]) and np.isnan(Xr2[i, k])))]
        out["sens_changed"] += len(diff); out["sens_total"] += len(Fz.NONTIME)
        out["cutoffs"].append(ts * 60)
    out["pass"] = (len(out["mismatch"]) == 0) and out["sens_changed"] > 0.5 * out["sens_total"]
    return out

def shape_nan(start=utc(2010, 1, 1), end=utc(2011, 1, 1)):
    t, Xr, Z = Fz.build(utc(2009, 12, 1), end)
    m = t >= int(start.timestamp() // 60)
    t, Xr, Z = t[m], Xr[m], Z[m]
    rep = {"n_rows": int(len(t)), "n_features": int(Z.shape[1]), "n_nontime": len(Fz.NONTIME), "window": [str(start), str(end)], "per_feature": {}}
    for k, n in enumerate(Fz.NAMES):
        z = Z[:, k]
        rep["per_feature"][n] = dict(concept=Fz.CONCEPT_OF[n], nan_frac=round(float(np.isnan(z).mean()), 4), raw_mean=round(float(np.nanmean(Xr[:, k])), 4),
                                     z_mean=round(float(np.nanmean(z)), 3), z_std=round(float(np.nanstd(z)), 3), z_min=round(float(np.nanmin(z)), 2), z_max=round(float(np.nanmax(z)), 2),
                                     inf=int(np.isinf(Xr[:, k]).sum()))
    rep["pass"] = all(v["inf"] == 0 for v in rep["per_feature"].values()) and rep["n_features"] == Fz.NF
    return rep

if __name__ == "__main__":
    r = {"lookahead": lookahead(), "shape_nan_2010": shape_nan()}
    print(json.dumps(r, indent=1, default=str))
    sys.exit(0 if r["lookahead"]["pass"] and r["shape_nan_2010"]["pass"] else 1)
