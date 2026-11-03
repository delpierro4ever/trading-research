"""M3: fit conditional models on 2023(-2024) take-all R5 trades (PREREG §5); write frozen_models.json. No 2025."""
import sys, os, json, hashlib
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from c1_common import *
from c1_core import cell_index, ridge_X, predict
edges = json.load(open("/home/ubuntu/mafe-research-archive/mafe1r/results/m4_bin_edges_2023.json"))
E = {k: edges[k] for k in ("rv_300", "rate_300", "chgfreq_300")}
df = load_trades(); df = df.dropna(subset=["rv_300", "rate_300", "chgfreq_300"])
POST = pd.Timestamp("2023-03-22")
SAMPLES = {"B1": df[(df.day >= POST) & (df.year == 2023)], "B0": df[df.year == 2023], "R1": df[(df.day >= POST) & (df.year == 2023)], "B2": df[df.day >= POST]}
MINCELL = 200; ALPHA_FRAC = 0.1
models = {}; info = []
for name, d in SAMPLES.items():
    yg, yv = d.gross_bps.values, d.var_bps.values
    if name != "R1":
        c = cell_index(E, d.rv_300.values, d.rate_300.values, d.chgfreq_300.values)
        pg, pv, nn = np.full(27, yg.mean()), np.full(27, yv.mean()), np.zeros(27, int)
        for k in range(27):
            m = c == k; nn[k] = m.sum()
            if m.sum() >= MINCELL: pg[k], pv[k] = yg[m].mean(), yv[m].mean()
        models[name] = dict(type="bin", pg=pg.tolist(), pv=pv.tolist(), n=nn.tolist(), fit_trades=int(len(d)), fit_from=str(d.day.min().date()), fit_to=str(d.day.max().date()), overall_g=float(yg.mean()), overall_v=float(yv.mean()), min_cell=MINCELL)
    else:
        X = ridge_X(d.rv_300.values, d.rate_300.values, d.chgfreq_300.values); mu, sd = X.mean(0), X.std(0); Z = np.column_stack([np.ones(len(X)), (X - mu) / sd])
        P = np.eye(4) * ALPHA_FRAC * len(X); P[0, 0] = 0
        bg = np.linalg.solve(Z.T @ Z + P, Z.T @ yg); bv = np.linalg.solve(Z.T @ Z + P, Z.T @ yv)
        models[name] = dict(type="ridge", mu=mu.tolist(), sd=sd.tolist(), bg=bg.tolist(), bv=bv.tolist(), alpha=ALPHA_FRAC * len(X), fit_trades=int(len(d)), fit_from=str(d.day.min().date()), fit_to=str(d.day.max().date()))
frozen = dict(edges=E, models=models, note="MAFE-1C frozen models, PREREG §5. Fit data 2023(-2024) only.")
json.dump(frozen, open(f"{RES}/frozen_models.json", "w"), indent=1)
open(f"{RES}/frozen_models.sha256", "w").write(hashlib.sha256(open(f"{RES}/frozen_models.json", "rb").read()).hexdigest() + "  frozen_models.json\n")

# ---- training summary + check on 2024 (take-all trades; the rule replays are run separately with c1_run)
rows = []; d24 = df[df.year == 2024]
cell24 = cell_index(E, d24.rv_300.values, d24.rate_300.values, d24.chgfreq_300.values)
for name, M in models.items():
    for scope, d in (("train", SAMPLES[name]), ("2024check" if name != "B2" else "2024(in-sample)", d24)):
        pg, pv = predict(M, E, d.rv_300.values, d.rate_300.values, d.chgfreq_300.values)
        r = dict(model=name, scope=scope, N=len(d), mean_pred_gross=float(np.nanmean(pg)), mean_real_gross=float(d.gross_bps.mean()),
                 corr_pred_real_gross=float(np.corrcoef(pg, d.gross_bps)[0, 1]), max_pred_gross=float(np.nanmax(pg)), min_pred_gross=float(np.nanmin(pg)),
                 corr_pred_real_var=float(np.corrcoef(pv, d.var_bps)[0, 1]) if np.std(pv) > 0 else np.nan)
        for K, fixed, vs in (("K1", None, 0), ("K2", 10.0, 1.0), ("K3", 7.65, .5), ("K4", 20.0, 1.0)):
            pn = pg - ((2.1 + d.tick_bps.values) if K == "K1" else fixed + vs * pv)
            r[f"max_pred_net_{K}"] = float(np.nanmax(pn)); r[f"share_trades_pred_net_gt0_{K}"] = float(np.nanmean(pn > 0))
            r[f"realised_net_{K}_of_selected"] = float(d[f"net_{K}"].values[pn > 0].mean()) if (pn > 0).any() else np.nan
            r[f"n_selected_{K}"] = int((pn > 0).sum())
        rows.append(r)
pd.DataFrame(rows).to_csv(f"{RES}/m3_fit_summary.csv", index=False)
# cell tables: training n, mean gross, SE; and 2024 realised per cell (B1 cells)
b1 = models["B1"]; tr = SAMPLES["B1"]; ctr = cell_index(E, tr.rv_300.values, tr.rate_300.values, tr.chgfreq_300.values)
cr = []
for k in range(27):
    m = ctr == k; m2 = cell24 == k; g = tr.gross_bps.values[m]; g2 = d24.gross_bps.values[m2]
    cr.append(dict(cell=k, rv_bin=k // 9, rate_bin=(k // 3) % 3, chg_bin=k % 3, n_train=int(m.sum()), train_gross=float(g.mean()) if m.sum() else np.nan, train_se=float(g.std() / np.sqrt(m.sum())) if m.sum() > 1 else np.nan,
                   used=bool(m.sum() >= MINCELL), pred_gross=b1["pg"][k], pred_var=b1["pv"][k], n_2024=int(m2.sum()), gross_2024=float(g2.mean()) if m2.sum() else np.nan,
                   se_2024=float(g2.std() / np.sqrt(m2.sum())) if m2.sum() > 1 else np.nan))
C = pd.DataFrame(cr); C.to_csv(f"{RES}/m3_b1_cells.csv", index=False)
ok = C[(C.n_2024 >= 100) & C.used]
from scipy.stats import spearmanr
print("B1 cell rank corr pred vs 2024 realised gross (cells n>=100):", spearmanr(ok.pred_gross, ok.gross_2024), len(ok))
print(pd.DataFrame(rows).T.to_string())
