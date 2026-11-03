"""Track B on discovery (section 4): walk-forward ridge + LightGBM, 2013-2019, 1-day purge. Usage (from phase3/code): python -m mafe3.stage2.track_b run | controls"""
from __future__ import annotations
import json, pickle, sys, time
import numpy as np, pandas as pd
from ..market import Market, O, D0, epoch_min
from . import store, features as Fz, modelslib as ML
from .trades import Outcomes
from .track_a import setup
from .run_step0 import OUT

MODELS = ("ridge", "lgbm")
YEARS = list(range(2013, 2020))
PURGE = 1440
MODEL_DIR = "/home/ubuntu/mafe-data/stage2/models"

def ymin(y): return epoch_min(y, 1, 1) - O

def fit_predict(kind, Z, Xr, y, tr, te):
    """fit on rows tr (positions), predict rows te."""
    if kind == "ridge":
        m = ML.fit_ridge(Xr[tr], y[tr]); return ML.predict_ridge(m, Xr[te]), m
    m = ML.fit_lgb(Z[tr], y[tr]); return m.predict(Z[te]).astype(np.float64), m

def walk_forward(kind, H, Z, Xr, oc, td, quiet=True):
    r = oc.by[H]; y = np.where(r["valid"], r["gross"], 0.0).astype(np.float64); ok = r["valid"]
    preds_pos, preds_d, imp = [], [], []
    per_year = {}
    for yv in YEARS:
        te = np.nonzero(ok & (td >= ymin(yv)) & (td < ymin(yv + 1)))[0]
        tr = np.nonzero(ok & (td < ymin(yv) - PURGE))[0]
        pred, m = fit_predict(kind, Z, Xr, y, tr, te)
        pos, d = ML.trade_rule(pred, r, td, te)
        preds_pos.append(pos); preds_d.append(d)
        if kind == "lgbm": imp.append(m.feature_importance("gain"))
        else: imp.append(np.abs(m["beta"]))
        per_year[yv] = (int(len(tr)), int(len(te)), float(np.corrcoef(pred, y[te])[0, 1]))
    pos = np.concatenate(preds_pos); d = np.concatenate(preds_d)
    o = np.argsort(td[pos], kind="stable"); pos, d = pos[o], d[o]
    # global greedy across year boundaries (a trade entered at the end of a year blocks the first decisions of the next)
    keep = np.array(__import__("mafe3.stage2.trades", fromlist=["greedy"]).greedy(td[pos], r["x"][pos]), dtype=np.int64)
    pos, d = pos[keep], d[keep]
    return pos, d, imp, per_year

def run(Zin=None, tag="trackB", Hs=None, models=MODELS, save_models=True, boot=True):
    t0 = time.time()
    kept, td, Z = setup()
    if Zin is not None: Z = Zin
    M = Market.from_loader("2009-11-01", "2020-01-01")
    oc = Outcomes(M, td)
    Xr = ML.design_ridge(Z)
    rows, imps, wf_rows = [], [], []
    Hs = Hs or kept
    for H in Hs:
        for kind in models:
            pos, d, imp, per_year = walk_forward(kind, H, Z, Xr, oc, td)
            s = ML.trade_stats(oc, H, pos, d, YEARS)
            yn = s.pop("year_net")
            row = dict(model=kind, H=H, **s, years_net=";".join(f"{y}:{v:.2f}" for y, v in yn.items()))
            n_models = len(models) * len(Hs)
            row["gate_p"] = 0.05 / n_models
            row["pass"] = bool(s["n"] >= 200 and s["net35"] > 0 and s["net50"] > 0 and s["p_boot"] < 0.05 / n_models and s["pos_years"] >= 5)
            rows.append(row)
            for y in YEARS:
                mk = oc.year[pos] == y
                ys = ML.trade_stats(oc, H, pos[mk], d[mk], [y]) if mk.any() else dict(n=0)
                ys.pop("year_net", None)
                wf_rows.append(dict(model=kind, H=H, year=y, n_train=per_year[y][0], n_test=per_year[y][1], pred_corr=per_year[y][2], **{k: ys.get(k, np.nan) for k in ("n", "gross", "net35", "net50")}))
            names = Fz.NAMES if kind == "lgbm" else ML.ridge_names()
            imp = np.array(imp)
            if kind == "lgbm": imp = imp / imp.sum(1, keepdims=True)
            imps.append(pd.DataFrame(dict(model=kind, H=H, feature=names, importance=imp.mean(0))))
            print(f"[{time.time()-t0:.0f}s] {kind} H={H}: n={s['n']} gross={s['gross']:.2f} net35={s['net35']:.2f} net50={s['net50']:.2f} p_boot={s['p_boot']:.4f} pos_years={s['pos_years']}", flush=True)
    S = pd.DataFrame(rows)
    S.to_csv(OUT / f"{tag}_summary.csv", index=False)
    pd.DataFrame(wf_rows).to_csv(OUT / f"{tag}_walkforward.csv", index=False)
    pd.concat(imps).to_csv(OUT / f"{tag}_importance.csv", index=False)
    if save_models:       # final models on 2010..2019 (1-day purge before 2020-01-01); only gate survivors are ever applied to validation
        import os; os.makedirs(MODEL_DIR, exist_ok=True)
        for H in Hs:
            r = oc.by[H]; y = np.where(r["valid"], r["gross"], 0.0).astype(np.float64)
            tr = np.nonzero(r["valid"] & (td < epoch_min(2020, 1, 1) - O - PURGE))[0]
            for kind in models:
                _, m = fit_predict(kind, Z, Xr, y, tr, tr[:10])
                if kind == "lgbm":
                    m.save_model(f"{MODEL_DIR}/lgbm_H{H}.txt")
                    pd.DataFrame(dict(feature=Fz.NAMES, gain=m.feature_importance("gain"))).to_csv(OUT / f"final_lgbm_importance_H{H}.csv", index=False)
                else:
                    pickle.dump(m, open(f"{MODEL_DIR}/ridge_H{H}.pkl", "wb"))
                    pd.DataFrame(dict(feature=ML.ridge_names(), coef_std=m["beta"])).to_csv(OUT / f"final_ridge_coef_H{H}.csv", index=False)
    return S

def controls():
    """positive: planted feature (noisy realised return) in place of d_body1; negative: rows of Z permuted. H = 60, both models."""
    kept, td, Z = setup()
    M = Market.from_loader("2009-11-01", "2020-01-01")
    oc = Outcomes(M, td)
    r = oc.by[60]; y = np.where(r["valid"], r["gross"], np.nan)
    plant = (y - np.nanmean(y)) / np.nanstd(y) + np.random.default_rng(1).normal(0, 3.0, len(y))
    Zp = Z.copy(); Zp[:, Fz.NAMES.index("d_body1")] = plant
    res = {}
    for nm, Zc in (("positive", Zp), ("negative", Z[np.random.default_rng(2).permutation(len(Z))])):
        S = run(Zin=Zc, tag=f"ctrl_{nm}", Hs=[60], save_models=False, boot=False)
        res[nm] = S.drop(columns=["years_net"]).to_dict("records")
    res["positive_pass"] = all(v["net35"] > 0 and v["gross"] > 3 for v in res["positive"])
    res["negative_pass"] = all((not v["pass"]) and v["net35"] < 0 and v["p_boot"] > 0.05 for v in res["negative"])      # permuted inputs: nothing may pass or look significant
    (OUT / "trackB_controls.json").write_text(json.dumps(res, indent=1, default=str)); print(json.dumps(res, indent=1, default=str))

if __name__ == "__main__":
    {"run": run, "controls": controls}[sys.argv[1]]()
