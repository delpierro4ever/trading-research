"""M2 (2023-2024 only): variation of cost components and gross by month / hour / weekday / causal state; heterogeneity vs null; variance decomposition."""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from c1_common import *
rng = np.random.default_rng(SEED); B = 10000
df = load_trades()
edges = json.load(open("/home/ubuntu/mafe-research-archive/mafe1r/results/m4_bin_edges_2023.json"))
STATES = ["rate_300", "rv_300", "meansize_300", "chgfreq_300", "burst_300"]
for f in STATES: df[f"bin_{f}"] = np.where(df[f].isna(), -1, np.digitize(df[f].fillna(0), edges[f]))
df["hour8"] = df.hour // 8
OUTC = ["gross_bps", "gross0_bps", "lat100_bps", "lat250_bps", "lat500_bps", "spread_bps", "impact_small_bps", "impact_big_bps", "net_K1", "net_K2", "net_K3", "net_K4"]
SUMC = OUTC + ["cost_K1", "cost_K2", "cost_K3", "cost_K4"]
POST = pd.Timestamp("2023-03-22")
SCOPES = {"2023": df[df.year == 2023], "2023post": df[(df.year == 2023) & (df.day >= POST)], "2024": df[df.year == 2024]}

def table(d, key, scope):
    rows = []
    for k, g in d.groupby(key):
        if (isinstance(k, (int, np.integer)) and k < 0): continue
        da = day_agg(g, SUMC); r = dict(scope=scope, by=key, group=k, N=len(g), days=len(da))
        for c in SUMC: r[c] = da[c].sum() / da.N.sum()
        for c in ("gross_bps", "net_K2", "net_K1", "gross0_bps", "lat500_bps"):
            _, lo, hi, _ = boot_mean_ci(da, c, 2000, rng); r[c + "_lo"], r[c + "_hi"] = lo, hi
        r["spread_med"] = g.spread_bps.median(); r["spread_p95"] = g.spread_bps.quantile(.95); r["spread_max"] = g.spread_bps.max()
        r["lat500_sd"] = g.lat500_bps.std(); r["lat500_p95"] = g.lat500_bps.quantile(.95); r["lat500_p05"] = g.lat500_bps.quantile(.05)
        r["gross_sd"] = g.gross_bps.std()
        r["spread_pct_of_K2fee"] = 100 * r["spread_bps"] / 10.0; r["impact_small_pct_of_K2fee"] = 100 * r["impact_small_bps"] / 10.0
        rows.append(r)
    return rows
tabs = {k: [] for k in ("month", "hour", "dow", "hour8")}
state_rows = []
for sc, d in SCOPES.items():
    if sc == "2024" or sc == "2023": tabs["month"] += table(d, "month", sc)
    for k in ("hour", "dow", "hour8"): tabs[k] += table(d, k, sc)
    for f in STATES: state_rows += table(d, f"bin_{f}", sc)
pd.DataFrame(tabs["month"]).to_csv(f"{RES}/m2_by_month.csv", index=False)
pd.DataFrame(tabs["hour"]).to_csv(f"{RES}/m2_by_hour.csv", index=False)
pd.DataFrame(tabs["dow"]).to_csv(f"{RES}/m2_by_weekday.csv", index=False)
pd.DataFrame(tabs["hour8"]).to_csv(f"{RES}/m2_by_hour8.csv", index=False)
pd.DataFrame(state_rows).to_csv(f"{RES}/m2_by_state.csv", index=False)

# ---------- heterogeneity vs null (PREREG §4): month -> permute days over month labels; others -> permute labels within day
HC = ["gross_bps", "lat500_bps", "spread_bps", "impact_small_bps", "impact_big_bps"]
GROUPS = {"hour": "hour", "weekday": "dow", "hour8": "hour8", **{f: f"bin_{f}" for f in STATES}}
def Q(lab, k, N_, Smat):
    n = np.bincount(lab, N_, k); out = []
    for j in range(Smat.shape[1]):
        s = np.bincount(lab, Smat[:, j], k); ok = n > 0; m = s[ok] / n[ok]; mu = Smat[:, j].sum() / N_.sum()
        out.append((n[ok] * (m - mu) ** 2).sum())
    return np.array(out)
het = []
for sc, d in SCOPES.items():
    d = d.sort_values(['day', 'sig_ts']).reset_index(drop=True); y = d[HC].values
    # months (day-level)
    da = day_agg(d, HC); da["month"] = da.index.strftime("%Y-%m"); lab = pd.factorize(da.month)[0]; k = lab.max() + 1
    Nd = da.N.values.astype(float); Sd = da[HC].values
    obs = Q(lab, k, Nd, Sd); cnt = np.zeros(len(HC))
    for _ in range(B): cnt += Q(rng.permutation(lab), k, Nd, Sd) >= obs
    for j, c in enumerate(HC): het.append(dict(scope=sc, by="month", outcome=c, groups=int(k), Q=obs[j], p=(1 + cnt[j]) / (B + 1)))
    # within-day label permutation for trade-level groupings
    dayid = pd.factorize(d.day)[0]; labs = {g: d[col].values.astype(int) for g, col in GROUPS.items()}
    labs = {g: np.where(l < 0, 0, l) for g, l in labs.items()}
    ks = {g: l.max() + 1 for g, l in labs.items()}
    N1 = np.ones(len(d)); obs = {g: Q(labs[g], ks[g], N1, y) for g in labs}; cnt = {g: np.zeros(len(HC)) for g in labs}
    for _ in range(B):
        shuf = np.lexsort((rng.random(len(d)), dayid))  # rows are sorted by day, so this shuffles row order inside each day block
        for g in labs:
            cnt[g] += Q(labs[g][shuf], ks[g], N1, y) >= obs[g]
    for g in labs:
        for j, c in enumerate(HC): het.append(dict(scope=sc, by=g, outcome=c, groups=int(ks[g]), Q=obs[g][j], p=(1 + cnt[g][j]) / (B + 1)))
H = pd.DataFrame(het)
# Holm across all tests within scope
H["p_holm"] = np.nan
for sc in H.scope.unique():
    m = H.scope == sc; p = H.loc[m, "p"].values; o = np.argsort(p); n = len(p); adj = np.empty(n); run = 0
    for r, i in enumerate(o): run = max(run, (n - r) * p[i]); adj[i] = min(run, 1)
    H.loc[m, "p_holm"] = adj
H["n_tests_in_scope"] = H.groupby("scope").p.transform("size")
H.to_csv(f"{RES}/m2_heterogeneity.csv", index=False)

# ---------- variance decomposition of period net_K2 (months, weeks)
def vardecomp(d, per, label):
    g = d.groupby(per); m = g[["gross0_bps", "lat500_bps", "spread_bps", "impact_small_bps", "net_K2", "gross_bps"]].mean(); n = g.size()
    m = m[n >= 20]
    def shares(mm):
        v = np.var(mm.net_K2.values, ddof=1)
        if v == 0: return [np.nan] * 4
        c = lambda a, b: np.cov(a, b, ddof=1)[0, 1]
        return [c(mm.net_K2, mm.gross0_bps) / v, -c(mm.net_K2, mm.lat500_bps) / v, -c(mm.net_K2, mm.spread_bps) / v, -c(mm.net_K2, mm.impact_small_bps) / v]
    obs = shares(m); bs = np.array([shares(m.iloc[rng.integers(0, len(m), len(m))]) for _ in range(2000)])
    r = dict(sample=label, period=per, n_periods=len(m), var_net=float(np.var(m.net_K2, ddof=1)), sd_net=float(np.std(m.net_K2, ddof=1)))
    for i, nm in enumerate(["share_gross0", "share_latency", "share_spread", "share_impact"]):
        r[nm] = obs[i]; r[nm + "_lo"] = np.nanquantile(bs[:, i], .025); r[nm + "_hi"] = np.nanquantile(bs[:, i], .975)
    r["share_var_cost_total"] = obs[1] + obs[2] + obs[3]
    # variance of gross_500-only (latency inside gross): share if lat is treated as part of gross
    v = np.var(m.net_K2, ddof=1); r["share_gross500_incl_latency"] = np.cov(m.net_K2, m.gross_bps, ddof=1)[0, 1] / v
    r["share_spread_impact_only"] = obs[2] + obs[3]
    return r
dd = df.copy(); dd["week"] = dd.day.dt.strftime("%G-W%V")
vr = []
for lab, d in (("2023-2024", dd), ("2023post+2024", dd[dd.day >= POST]), ("2024", dd[dd.year == 2024])):
    vr.append(vardecomp(d, "month", lab)); vr.append(vardecomp(d, "week", lab))
pd.DataFrame(vr).to_csv(f"{RES}/m2_variance_decomposition.csv", index=False)
# overall component summary vs fixed fee
rows = []
for sc, d in SCOPES.items():
    r = dict(scope=sc, N=len(d))
    for c in ("gross_bps", "gross0_bps", "lat100_bps", "lat250_bps", "lat500_bps", "spread_bps", "impact_small_bps", "impact_big_bps", "var_bps", "cost_K1", "cost_K2", "cost_K3", "cost_K4", "net_K1", "net_K2", "net_K3", "net_K4"):
        r[c + "_mean"] = d[c].mean(); r[c + "_sd"] = d[c].std()
    r["spread_p99"] = d.spread_bps.quantile(.99); r["spread_max"] = d.spread_bps.max(); r["share_spread_at_tick"] = float((d.spread_bps <= d.tick_bps * 1.0001).mean())
    r["K2_variable_share_of_cost_pct"] = 100 * d.var_bps.mean() / d.cost_K2.mean()
    rows.append(r)
pd.DataFrame(rows).to_csv(f"{RES}/m2_component_summary.csv", index=False)
print("m2 done")
