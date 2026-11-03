"""Main run: S1/S2/S3 on the main universe; DEV (report) and VAL (gate) tables, attribution, bootstrap, gates, equity curves data.
Single pass. Output -> ../out/ and /home/ubuntu/mafe-data/trend/out/. Usage: python run_main.py"""
import json, os, numpy as np, pandas as pd, engine as E, analysis as A
pd.set_option("display.width", 250); pd.set_option("display.float_format", "{:.3f}".format)
OUT = "/home/ubuntu/mafe-research-archive/trend/out"; BIG = "/home/ubuntu/mafe-data/trend/out"; os.makedirs(BIG, exist_ok=True)
ctx = A.Ctx(); P = ctx.P
print("universe:", list(P.columns))
bh = E.bh_positions(ctx.prep); bh_ret = (bh.shift(1).fillna(0) * ctx.prep.r.fillna(0)).sum(axis=1)
tabs, gates, nets = [], {}, {}
for s in ("S1", "S2", "S3"):
    pos, res = A.run(ctx, s); pos.to_parquet(f"{BIG}/pos_{s}.parquet")
    for w in ("DEV", "VAL"):
        t = A.table(pos, res, w, boot=True); t.insert(0, "window", w); t.insert(0, "system", s); tabs.append(t.reset_index(names="model"))
        print(s, w); print(t[["cagr", "vol", "sharpe", "gross_sharpe", "maxdd", "worst12m", "pct_pos_months", "cost_ann", "fin_ann", "turnover", "boot_p05", "boot_p95"]])
    for k in res: nets[(s, k)] = res[k]["net"].sum(axis=1)
    v = tabs[-1].set_index("model")   # VAL
    gates[s] = {"cons_sharpe": float(v.loc["cons", "sharpe"]), "cons_p05": float(v.loc["cons", "boot_p05"]),
                "pass": bool(v.loc["cons", "sharpe"] > 0 and v.loc["cons", "boot_p05"] > -0.2),
                "stress_sharpe": float(v.loc["stress", "sharpe"]), "stress_p05": float(v.loc["stress", "boot_p05"]),
                "pass_if_stress": bool(v.loc["stress", "sharpe"] > 0 and v.loc["stress", "boot_p05"] > -0.2)}
    # attribution (cons net, plus gross/cost/fin), per instrument / class / year
    for w in ("DEV", "VAL"):
        idx = E.win(pos, w).index; rows = []
        for c in ctx.prep.cols:
            rows.append(dict(instrument=c, cls=E.CLS[c], gross=res["cons"]["gross"][c].loc[idx].sum() / (len(idx) / 252), cost=-res["cons"]["cost"][c].loc[idx].sum() / (len(idx) / 252),
                             fin=res["cons"]["fin"][c].loc[idx].sum() / (len(idx) / 252), net=res["cons"]["net"][c].loc[idx].sum() / (len(idx) / 252),
                             net_stress=res["stress"]["net"][c].loc[idx].sum() / (len(idx) / 252), avg_abs_pos=pos[c].loc[idx].abs().mean()))
        a = pd.DataFrame(rows); a.to_csv(f"{OUT}/attr_instrument_{s}_{w}.csv", index=False)
        a.groupby("cls")[["gross", "cost", "fin", "net", "net_stress"]].sum().to_csv(f"{OUT}/attr_class_{s}_{w}.csv")
    allidx = pos.loc["2009-01-01":"2022-12-31"].index; net = res["cons"]["net"].sum(axis=1).loc[allidx]
    yr = pd.DataFrame({"net_cons": (1 + net).groupby(net.index.year).prod() - 1,
                       "net_std": (1 + res["std"]["net"].sum(axis=1).loc[allidx]).groupby(net.index.year).prod() - 1,
                       "net_stress": (1 + res["stress"]["net"].sum(axis=1).loc[allidx]).groupby(net.index.year).prod() - 1,
                       "gross": (1 + res["cons"]["gross"].sum(axis=1).loc[allidx]).groupby(net.index.year).prod() - 1})
    yr.to_csv(f"{OUT}/per_year_{s}.csv"); print(yr)
    for w in ("DEV", "VAL"):
        idx = E.win(pos, w).index
        gc = res["cons"]["gross"].sum(axis=1).loc[idx]; print(s, w, "corr(gross, equal-risk B&H gross) =", round(float(gc.corr(bh_ret.loc[idx])), 3))
        tabs[-1 if w == "VAL" else -2]["corr_bh"] = float(gc.corr(bh_ret.loc[idx]))
    # average |net exposure|
    print(s, "avg gross leverage (sum|pos|):", float(pos.loc["2009":"2022"].abs().sum(axis=1).mean()), " avg active instruments:", float((pos.loc["2009":"2022"] != 0).sum(axis=1).mean()))
bhs = {w: E.equity_stats(E.win(bh_ret.to_frame()[0] if False else bh_ret, w)) for w in ("DEV", "VAL")}
print("B&H (gross, no costs) :", {w: {k: round(v, 3) for k, v in d.items()} for w, d in bhs.items()})
full = pd.concat(tabs); full.to_csv(f"{OUT}/main_results.csv", index=False)
pd.DataFrame(nets).to_parquet(f"{BIG}/net_returns.parquet"); bh_ret.to_frame("bh").to_parquet(f"{BIG}/bh_gross.parquet")
json.dump(dict(gates=gates, bh=bhs), open(f"{OUT}/gates.json", "w"), indent=1, default=float)
print(json.dumps(gates, indent=1))
passers = {k: v["cons_sharpe"] for k, v in gates.items() if v["pass"]}
best = max(passers, key=passers.get) if passers else None
print("best validated:", best); json.dump({"best": best, "passers": passers}, open(f"{OUT}/best_system.json", "w"))
