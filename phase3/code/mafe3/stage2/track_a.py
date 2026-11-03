"""Track A on discovery (section 3). Phases (from phase3/code): python -m mafe3.stage2.track_a count | run
 count: record the candidate count (committed before any evaluation).  run: A search -> BH -> B replication -> collapse -> frozen list."""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np, pandas as pd
from ..market import Market, O, D0, epoch_min
from ..engine import block_bootstrap_p, bh
from . import store, features as Fz, candlib as C
from .trades import Outcomes
from .run_step0 import OUT, SHA2, PREREG2
import hashlib

A_END = epoch_min(2015, 1, 1) - O          # dense index of 2015-01-01 (A: decisions before; B: from)

def setup(Z_override=None):
    assert hashlib.sha256(PREREG2.read_bytes()).hexdigest() == SHA2
    kept = json.loads((OUT / "kept_H.json").read_text())["kept_H_min"]
    t_abs, _, Z = store.load("disc")
    td = t_abs - O; m = td >= D0
    td, Z = td[m], Z[m]
    return kept, td, Z

def count():
    kept, td, Z = setup()
    specs = C.mask_specs()
    n = len(specs) * len(kept) * 2
    by = {k: sum(1 for s in specs if s[0] == k) for k in "SPC"}
    res = dict(kept_H=kept, n_signal_masks=len(specs), by_kind=by, n_horizons=len(kept), n_directions=2, n_candidates=n)
    (OUT / "trackA_candidate_count.json").write_text(json.dumps(res, indent=1)); print(res)

def run(Zin=None, tag="trackA", verbose=True):
    t0 = time.time()
    kept, td, Z = setup()
    if Zin is not None: Z = Zin
    M = Market.from_loader("2009-11-01", "2020-01-01")
    oc = Outcomes(M, td)
    inA, inB = td < A_END, td >= A_END
    rowsA = np.nonzero(inA)[0]
    thr = C.fit_thresholds(Z, rowsA)
    masks = C.Masks(Z, thr)
    specs = C.mask_specs()
    recs = []
    for s in specs:
        mk = masks.get(s)
        for H in kept:
            pos = C.episodes(mk, oc, H, td, inA)
            for d in (1, -1):
                r = C.summarize_ep(oc, H, pos, d)
                r.pop("_year_net", None)
                recs.append(dict(spec=C.spec_id(s), kind=s[0], H=H, d=d, **r))
    A = pd.DataFrame(recs)
    if verbose: print(f"[{time.time()-t0:.0f}s] A evaluated: {len(A)} candidates", flush=True)
    rej = bh(A["p"].to_numpy(), 0.10)
    A["bh"] = rej
    A["pass_A"] = rej & (A["n"] >= 100) & (A["net50"] > 0) & (A["days"] >= 30)
    A.drop(columns=["years"]).to_csv(OUT / f"{tag}_discA.csv", index=False)
    funnel = dict(n_candidates=len(A), n_with_n_ge_100=int((A.n >= 100).sum()), n_net35_pos=int((A.net35 > 0).sum()), min_p=float(A.p.min()), n_bh=int(rej.sum()),
                  n_bh_n100=int((rej & (A.n >= 100)).sum()), n_bh_n100_net50=int((rej & (A.n >= 100) & (A.net50 > 0)).sum()), m_A=int(A.pass_A.sum()))
    if verbose: print(funnel, flush=True)
    surv = A[A.pass_A].copy()
    mA = len(surv)
    recB = []
    byspec = {C.spec_id(s): s for s in specs}
    for _, r in surv.iterrows():
        s = byspec[r.spec]
        pos = C.episodes(masks.get(s), oc, int(r.H), td, inB)
        o = C.summarize_ep(oc, int(r.H), pos, int(r.d), boot=True)
        yn = o.pop("_year_net", {})
        recB.append(dict(spec=r.spec, kind=r.kind, H=int(r.H), d=int(r.d), pos=pos, **o, year_net=yn))
    B = pd.DataFrame(recB)
    funnel["B_threshold_p"] = 0.05 / mA if mA else None
    if mA:
        B["p_used"] = np.maximum(B.p, B.p_boot)
        B["pass_B"] = (B.p_used < 0.05 / mA) & (B.net35 > 0) & (B.net50 > 0) & (B.pos_years >= 3) & (B.days >= 30)
        funnel |= dict(B_p_ok=int((B.p_used < 0.05 / mA).sum()), B_net_ok=int(((B.net35 > 0) & (B.net50 > 0)).sum()), B_years_ok=int((B.pos_years >= 3).sum()), n_pass_B=int(B.pass_B.sum()))
        B.drop(columns=["pos", "year_net"]).to_csv(OUT / f"{tag}_discB.csv", index=False)
    else:
        funnel["n_pass_B"] = 0
    # collapse near-duplicates among B-survivors (episode overlap > 50 %, either direction of the comparison), simplest definition first, then B t
    final = []
    if mA and funnel["n_pass_B"]:
        cand = B[B.pass_B].copy()
        cand["cx"] = cand.spec.map(lambda sp: C.complexity(byspec[sp]))
        cand = cand.sort_values(["cx", "t"], ascending=[True, False])
        reps = []
        for _, r in cand.iterrows():
            ei = oc.by[int(r.H)]["e"][r.pos]; xi = oc.by[int(r.H)]["x"][r.pos]
            dup = False
            for q in reps:
                ej, xj = q["e"], q["x"]
                if max(C.overlap_frac(ei, xi, ej, xj), C.overlap_frac(ej, xj, ei, xi)) > 0.5: dup = True; break
            if not dup: reps.append(dict(row=r, e=ei, x=xi))
        funnel["n_after_collapse"] = len(reps)
        for q in reps[:10]:
            r = q["row"]
            final.append(dict(spec=r.spec, H=int(r.H), d=int(r.d), B_n=int(r.n), B_net35=r.net35, B_net50=r.net50, B_p=float(r.p_used), B_t=r.t, B_days=int(r.days), cx=int(r.cx)))
        funnel["n_to_validation"] = len(final)
    else:
        funnel["n_after_collapse"] = 0; funnel["n_to_validation"] = 0
    if verbose: print(funnel, flush=True)
    if tag == "trackA":
        (OUT / "trackA_funnel.json").write_text(json.dumps(funnel, indent=1, default=str))
        (OUT / "trackA_frozen.json").write_text(json.dumps(dict(thresholds=thr, finalists=final, kept_H=kept, A_end="2015-01-01"), indent=1))
    return A, funnel, final

if __name__ == "__main__":
    {"count": count, "run": run}[sys.argv[1]]()
