"""M4: one-shot 2025 evaluation with the FROZEN models (PREREG §6). Reads c1/p2025 (produced by c1_run.py with frozen_models.json committed). Outputs results/m4_*.csv/json."""
import sys, os, json, glob
import numpy as np, pandas as pd, polars as pl
sys.path.insert(0, os.path.dirname(__file__))
from c1_common import *
from scipy.stats import spearmanr
rng = np.random.default_rng(SEED); B = 10000
P25 = os.environ.get("MAFE_P25", f"{ROOT}/c1/p2025")  # env override only for the 2024 dry-run of this script
RES_IN = RES
RES = os.environ.get("MAFE_RES", RES)
RULES = ["ALL", "B1_K2", "B1_K1", "B1_K3", "B1_K4", "R1_K2", "B0_K2", "B2_K2"]
def load(rule):
    fs = glob.glob(f"{P25}/trades_{rule}/*.parquet")
    if not fs: return None
    d = pl.read_parquet(fs).to_pandas(); d["day"] = pd.to_datetime(d["date"]); d["month"] = d.day.dt.strftime("%Y-%m")
    return costs(d)
def stat(d, col):
    """mean + day-block bootstrap one-sided p(mean<=0) and 95% CI"""
    da = day_agg(d, [col]); m, lo, hi, bs = boot_mean_ci(da, col, B, rng)
    return dict(N=len(d), days=len(da), mean=m, lo=lo, hi=hi, p_one_sided_gt0=float((bs <= 0).mean()))
out = {}
# ---------- durability: anchors
an = pl.scan_parquet(f"{P25}/anchors/*.parquet").collect().to_pandas()
HC = ["R5", "R10", "R50", "R100", "R250", "R300s"]
lad = []
for sub, m in (("all anchors", an.L >= 1), ("L>=2", an.L >= 2), ("L>=3", an.L >= 3), ("L>=4", an.L >= 4), ("L==5", an.L == 5)) + tuple((f"L=={k}", an.L == k) for k in range(1, 5)):
    x = an[m]; r = dict(year=2025, subset=sub, n=len(x))
    for h in HC: r[h] = x[h].mean()
    lad.append(r)
L5 = an[an.L == 5].copy(); L5["day"] = pd.to_datetime(L5.date)
for h in HC:
    v = L5[h].notna(); d = L5[v]; da = d.groupby("day")[h].agg(["sum", "size"]).rename(columns={"sum": "S", "size": "N"})
    idx = rng.integers(0, len(da), (B, len(da))); m = da.S.values[idx].sum(1) / da.N.values[idx].sum(1)
    lad.append(dict(year=2025, subset=f"L==5 CI95 {h}", n=int(v.sum()), **{h: da.S.sum() / da.N.sum(), "lo": np.quantile(m, .025), "hi": np.quantile(m, .975)}))
pd.DataFrame(lad).to_csv(f"{RES}/m4_ladder_2025.csv", index=False)
l5 = [r for r in lad if r["subset"] == "L==5"][0]
monotone = all(l5[a] <= l5[b] for a, b in (("R5", "R10"), ("R10", "R50"), ("R50", "R100"), ("R100", "R250")))
all_ = load("ALL"); st_all = stat(all_, "gross_bps")
out["durability"] = dict(r5_gross_per_trade=st_all, ladder_L5=l5, ladder_monotone_5_to_250=bool(monotone), durable=bool(st_all["lo"] > 0 and monotone))
# monthly gross 2025 take-all
mt = []
for m_, g in all_.groupby("month"):
    s = stat(g, "gross_bps"); s.update(month=m_, lat500=g.lat500_bps.mean(), spread=g.spread_bps.mean(), impact=g.impact_small_bps.mean(), net_K1=g.net_K1.mean(), net_K2=g.net_K2.mean(), net_K3=g.net_K3.mean(), net_K4=g.net_K4.mean()); mt.append(s)
pd.DataFrame(mt).to_csv(f"{RES}/m4_monthly_all_2025.csv", index=False)
# ---------- rules table (own trades), all K
rows = []
for r in RULES:
    d = load(r)
    if d is None:
        rows.append(dict(rule=r, N=0)); continue
    row = dict(rule=r, N=len(d), gate_trades_ok=len(d) >= 100)
    for K in ("gross", "K1", "K2", "K3", "K4"):
        col = "gross_bps" if K == "gross" else f"net_{K}"; s = stat(d, col)
        row.update({f"{K}_mean": s["mean"], f"{K}_lo": s["lo"], f"{K}_hi": s["hi"], f"{K}_p": s["p_one_sided_gt0"]})
    rows.append(row)
R = pd.DataFrame(rows)
# Holm over secondary (rule x K, excluding the primary cell B1_K2/K2)
sec = [(i, K) for i, r in R.iterrows() for K in ("K1", "K2", "K3", "K4") if r.N > 0 and not (r.rule == "B1_K2" and K == "K2")]
ps = np.array([R.loc[i, f"{K}_p"] for i, K in sec]); o = np.argsort(ps); n = len(ps); run = 0
for rk, j in enumerate(o):
    run = max(run, (n - rk) * ps[j]); R.loc[sec[j][0], f"{sec[j][1]}_p_holm"] = min(run, 1)
R.to_csv(f"{RES}/m4_rules_2025.csv", index=False)
b1 = R[R.rule == "B1_K2"].iloc[0]
out["primary_gate"] = dict(rule="B1 under K2", trades=int(b1.N), trades_ge_100=bool(b1.N >= 100), mean_net_K2=None if b1.N == 0 else float(b1.K2_mean),
                           p_one_sided=None if b1.N == 0 else float(b1.K2_p), CI95=None if b1.N == 0 else [float(b1.K2_lo), float(b1.K2_hi)],
                           PASS=bool(b1.N >= 100 and b1.K2_mean > 0 and b1.K2_p < 0.05))
# ---------- ranking: weekly Spearman, predicted vs realised (take-all trades)
all_["week"] = all_.day.dt.strftime("%G-W%V"); rk = []
for mn in ("B1", "B0", "R1", "B2"):
    all_[f"prednet_{mn}"] = all_[f"pg_{mn}"] - (10.0 + all_[f"pv_{mn}"])
    g = all_.groupby("week"); w = pd.DataFrame(dict(n=g.size(), pg=g[f"pg_{mn}"].mean(), pn=g[f"prednet_{mn}"].mean(), real_g=g.gross_bps.mean(), real_n=g.net_K2.mean()))
    w = w[w.n >= 20]
    for tgt, a, b in (("net_K2", "pn", "real_n"), ("gross", "pg", "real_g")):
        rho = spearmanr(w[a], w[b]).statistic if w[a].std() > 0 else np.nan
        pv = np.mean([(spearmanr(w[a], rng.permutation(w[b].values)).statistic >= rho) for _ in range(B)]) if np.isfinite(rho) else np.nan
        rk.append(dict(model=mn, target=tgt, weeks=len(w), spearman=rho, p_perm_one_sided=pv, pred_sd=float(w[a].std())))
# persistence baseline (descriptive extra, PREREG amendment A1): prior-week realised gross as predictor
g = all_.groupby("week"); w = pd.DataFrame(dict(n=g.size(), real_g=g.gross_bps.mean())); w = w[w.n >= 20]; prev = w.real_g.shift(1).dropna()
rho = spearmanr(prev, w.real_g.loc[prev.index]).statistic
rk.append(dict(model="persistence(prev-week gross)", target="gross", weeks=len(prev), spearman=rho, p_perm_one_sided=np.mean([(spearmanr(prev, rng.permutation(w.real_g.loc[prev.index].values)).statistic >= rho) for _ in range(B)])))
pd.DataFrame(rk).to_csv(f"{RES}/m4_ranking_weekly.csv", index=False)
w.to_csv(f"{RES}/m4_weekly_gross_2025.csv")
# ---------- state occupancy 2025 vs 2023post / 2024 (descriptive)
edges = json.load(open("/home/ubuntu/mafe-research-archive/mafe1r/results/m4_bin_edges_2023.json")); occ = []
ref = load_trades()
for nm, d in (("2023post", ref[(ref.year == 2023) & (ref.day >= "2023-03-22")]), ("2024", ref[ref.year == 2024]), ("2025", all_)):
    for f in ("rv_300", "rate_300", "chgfreq_300"):
        b = np.digitize(d[f].dropna(), edges[f]); occ.append(dict(sample=nm, var=f, **{f"share_bin{k}": float((b == k).mean()) for k in range(3)}))
pd.DataFrame(occ).to_csv(f"{RES}/m4_state_occupancy.csv", index=False)
# comparison of take-all gross/cost components across years
cmp = []
for nm, d in (("2023post", ref[(ref.year == 2023) & (ref.day >= "2023-03-22")]), ("2024", ref[ref.year == 2024]), ("2025", all_)):
    s = stat(d, "gross_bps"); cmp.append(dict(sample=nm, N=len(d), gross=s["mean"], lo=s["lo"], hi=s["hi"], lat500=d.lat500_bps.mean(), spread=d.spread_bps.mean(), impact_small=d.impact_small_bps.mean(), K2_cost=d.cost_K2.mean(),
                                               net_K1=d.net_K1.mean(), net_K2=d.net_K2.mean(), net_K3=d.net_K3.mean(), net_K4=d.net_K4.mean(), gross_sd=d.gross_bps.std()))
pd.DataFrame(cmp).to_csv(f"{RES}/m4_takeall_by_year.csv", index=False)

# ---------- A1(c)(1): top vs bottom predicted-gross cells (descriptive, no gate)
cells = pd.read_csv(f"{RES_IN}/m3_b1_cells.csv"); order = cells.sort_values(["pred_gross", "cell"], ascending=[False, True]).cell.values
top, bot = set(order[:5]), set(order[-5:])
from c1_core import cell_index
cid = cell_index(edges, all_.rv_300.values, all_.rate_300.values, all_.chgfreq_300.values)
tb = []
for nm, sel in (("top5 cells", np.isin(cid, list(top))), ("bottom5 cells", np.isin(cid, list(bot))), ("other 17", ~np.isin(cid, list(top | bot)))):
    d = all_[sel]
    for col in ("gross_bps", "net_K1", "net_K2", "net_K3", "net_K4"):
        s = stat(d, col); tb.append(dict(group=nm, outcome=col, N=s["N"], mean=s["mean"], lo=s["lo"], hi=s["hi"]))
da = day_agg(all_.assign(g_top=np.where(np.isin(cid, list(top)), all_.gross_bps, 0.0), g_bot=np.where(np.isin(cid, list(bot)), all_.gross_bps, 0.0), n_top=np.isin(cid, list(top)).astype(float), n_bot=np.isin(cid, list(bot)).astype(float)), ["g_top", "g_bot", "n_top", "n_bot"])
idx = rng.integers(0, len(da), (B, len(da))); dif = da.g_top.values[idx].sum(1) / da.n_top.values[idx].sum(1) - da.g_bot.values[idx].sum(1) / da.n_bot.values[idx].sum(1)
tb.append(dict(group="top5 - bottom5", outcome="gross_bps", N=int(da.n_top.sum() + da.n_bot.sum()), mean=da.g_top.sum() / da.n_top.sum() - da.g_bot.sum() / da.n_bot.sum(), lo=np.quantile(dif, .025), hi=np.quantile(dif, .975)))
pd.DataFrame(tb).to_csv(f"{RES}/m4_top_bottom_cells.csv", index=False)
json.dump(out, open(f"{RES}/m4_verdicts.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
