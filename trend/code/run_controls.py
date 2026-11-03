"""Controls: (1) lag test, (2) prefix invariance on real data, (3) random-sign placebo, (4) cost/financing accounting on real positions."""
import json, numpy as np, pandas as pd, engine as E, analysis as A
pd.set_option("display.width", 250); pd.set_option("display.float_format", "{:.3f}".format)
OUT = "/home/ubuntu/mafe-research-archive/trend/out"; BIG = "/home/ubuntu/mafe-data/trend/out"
ctx = A.Ctx(); rng = np.random.default_rng(20261015); rows = []; plac = []
cons = {"cons": A.MODELS["cons"]}
def sh(res, w, pos): return E.equity_stats(res["cons"]["net"].sum(axis=1).loc[E.win(pos, w).index]).get("sharpe")
for s in ("S1", "S2", "S3"):
    pos, _ = A.run(ctx, s, models=cons)
    r = {"system": s}
    for lag in (0, 1, 2):
        _, res = A.run(ctx, s, lag=lag, models=cons, pos=pos)
        for w in ("DEV", "VAL"): r[f"{w}_lag{lag}"] = sh(res, w, pos)
    r["lag1_improves_by_gt_0.15"] = bool((r["DEV_lag1"] - r["DEV_lag0"] > 0.15) or (r["VAL_lag1"] - r["VAL_lag0"] > 0.15))
    # prefix invariance with real data
    ok = []
    for d in ("2012-06-29", "2016-03-31", "2020-06-30"):
        sub = E.Prep(ctx.P.loc[:d]); ps, _ = E.positions(sub, s)
        ok.append(bool(np.allclose(pos.loc[:d].to_numpy(), ps.to_numpy(), atol=1e-9)))
    r["prefix_invariant"] = all(ok)
    # accounting on real positions: independent recomputation
    res = E.pnl(ctx.prep, pos, ctx.cp, ctx.rates, spread_mult=1.5, comm_mult=1.5, fin="B")
    hs = np.array([ctx.cp[c]["spread_frac"] / 2 * 1.5 + ctx.cp[c]["comm_side"] * 1.5 for c in ctx.prep.cols])
    X = pos.to_numpy(); d = np.abs(np.diff(np.vstack([np.zeros(X.shape[1]), X]), axis=0)); indep = float((d * hs).sum())
    r["cost_total_engine"] = float(res["cost"].sum().sum()); r["cost_total_indep"] = indep; r["cost_match"] = abs(indep - r["cost_total_engine"]) < 1e-9
    nz_days = int(((pos.shift(1).fillna(0) != 0).any(axis=1)).sum()); fin_days = int((res["fin"].abs().sum(axis=1) > 0).sum())
    r["days_with_position"] = nz_days; r["days_with_financing"] = fin_days
    # placebo: random sign per hold episode, 200 draws, DEV and VAL
    sg = np.sign(X); ep = np.zeros_like(X, dtype=int); cnt = 0
    for j in range(X.shape[1]):
        prev = 0
        for t in range(X.shape[0]):
            if sg[t, j] != 0 and sg[t, j] != prev: cnt += 1
            ep[t, j] = cnt if sg[t, j] != 0 else 0; prev = sg[t, j]
    ps_d, ps_v = [], []
    for k in range(200):
        flip = rng.choice([-1.0, 1.0], cnt + 1); flip[0] = 1.0
        pp = pd.DataFrame(X * flip[ep], index=pos.index, columns=pos.columns)
        _, rs = A.run(ctx, s, models=cons, pos=pp)
        ps_d.append(sh(rs, "DEV", pp)); ps_v.append(sh(rs, "VAL", pp))
    for w, arr in (("DEV", ps_d), ("VAL", ps_v)):
        arr = np.array(arr); real = r[f"{w}_lag0"]
        r[f"placebo_{w}_mean"] = float(arr.mean()); r[f"placebo_{w}_p05"] = float(np.percentile(arr, 5)); r[f"placebo_{w}_p95"] = float(np.percentile(arr, 95))
        r[f"real_{w}_pct_rank_vs_placebo"] = float((arr < real).mean())
    rows.append(r); print(pd.Series(r))
pd.DataFrame(rows).to_csv(f"{OUT}/controls.csv", index=False)
