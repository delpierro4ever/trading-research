"""Engine controls for Track A (run before looking at the real search): positive control (planted feature = noisy realised 30 min return)
and negative control (rows of Z permuted at random; full 13 656-candidate search). Usage: python -m mafe3.stage2.controls_a"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from ..market import Market, O
from . import track_a as TA, candlib as C, features as Fz
from .trades import Outcomes
from .run_step0 import OUT

def main():
    kept, td, Z = TA.setup()
    M = Market.from_loader("2009-11-01", "2020-01-01")
    oc = Outcomes(M, td)
    inA = td < TA.A_END
    res = {}
    # positive control: replace d_body1 with fwd30 gross / sd + noise; trade the top decile long, bottom decile short
    r = oc.by[30]; y = np.where(r["valid"], r["gross"], np.nan)
    rng = np.random.default_rng(1)
    plant = (y - np.nanmean(y)) / np.nanstd(y) + rng.normal(0, 3.0, len(y))
    Zp = Z.copy(); Zp[:, Fz.NAMES.index("d_body1")] = plant
    thr = C.fit_thresholds(Zp, np.nonzero(inA)[0]); mk = C.Masks(Zp, thr)
    out = {}
    for tail, d in (("hi10", 1), ("lo10", -1)):
        pos = C.episodes(mk.get(("S", "d_body1", tail)), oc, 30, td, inA)
        s = C.summarize_ep(oc, 30, pos, d); s.pop("_year_net", None); s.pop("years", None); out[f"{tail}_d{d}"] = s
    res["positive"] = out | {"pass": all(v["gross"] > 3 and v["net35"] > 0 and v["p"] < 1e-6 for v in out.values())}
    # negative control: permute rows of Z (kills every relation to returns, keeps marginals/cross-feature structure)
    perm = np.random.default_rng(2).permutation(len(Z))
    A, fun, fin = TA.run(Zin=Z[perm], tag="ctrl_neg", verbose=False)
    res["negative"] = dict(funnel=fun, mean_gross=float(A.gross.mean()), share_p_lt_05=float((A.p < 0.05).mean()), min_p=float(A.p.min()), mean_net35=float(A.net35.mean()),
                           n_bh=int(A.bh.sum()), pass_=bool(A.bh.sum() == 0 and abs(A.gross.mean()) < 0.3))
    res["negative"]["pass"] = res["negative"].pop("pass_")
    (OUT / "trackA_controls.json").write_text(json.dumps(res, indent=1, default=str)); print(json.dumps(res, indent=1, default=str))

if __name__ == "__main__":
    main()
