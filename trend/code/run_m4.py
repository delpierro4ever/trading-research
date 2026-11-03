"""M4 robustness (DEV + VAL only; reported, not used to choose)."""
import numpy as np, pandas as pd, engine as E, analysis as A
pd.set_option("display.width", 250); pd.set_option("display.float_format", "{:.3f}".format)
OUT = "/home/ubuntu/mafe-research-archive/trend/out"
rows = []
def rec(variant, s, pos, res):
    for w in ("DEV", "VAL"):
        idx = E.win(pos, w).index
        for k in ("std", "cons", "stress"):
            st = E.equity_stats(res[k]["net"].sum(axis=1).loc[idx])
            rows.append(dict(variant=variant, system=s, window=w, model=k, sharpe=st.get("sharpe"), cagr=st.get("cagr"), maxdd=st.get("maxdd")))
base = A.Ctx()
for s in ("S1", "S2", "S3"):
    pos, res = A.run(base, s); rec("base", s, pos, res)
    for m in (0.5, 1.5):
        c = base if m == 0.5 else A.Ctx(nmin=400)
        p2, r2 = A.run(c, s, mult=m); rec(f"lookback x{m}", s, p2, r2)
    _, r2 = A.run(base, s, pos=pos, spread_mult=2.0); rec("spread x2 (slippage)", s, pos, r2)
    _, r2 = A.run(base, s, pos=pos, lag=1); rec("execute one day later", s, pos, r2)
    # start-date sensitivity (cons model): Sharpe from start to 2018-12-31 and to 2022-12-31
    net = res["cons"]["net"].sum(axis=1)
    for st in ("2009-01-01", "2011-01-01", "2013-01-01", "2015-01-01", "2017-01-01"):
        for end in ("2018-12-31", "2022-12-31"):
            x = net.loc[st:end]; rows.append(dict(variant=f"start {st[:4]} to {end[:4]}", system=s, window="n/a", model="cons", sharpe=E.equity_stats(x).get("sharpe"), cagr=E.equity_stats(x).get("cagr"), maxdd=E.equity_stats(x).get("maxdd")))
    if s == "S3":
        p2, r2 = A.run(base, s, literal=True); rec("S3 literal 0.5% ATR sizing, unscaled", s, p2, r2)
for cl in ("FX", "METALS", "INDICES", "ENERGY"):
    c = A.Ctx([i for i in E.MAIN if E.CLS[i] != cl])
    for s in ("S1", "S2", "S3"):
        p2, r2 = A.run(c, s); rec(f"drop {cl}", s, p2, r2)
cc = A.Ctx(E.MAIN + E.CLASSES["CRYPTO"])
for s in ("S1", "S2", "S3"):
    p2, r2 = A.run(cc, s); rec("add crypto (supplementary)", s, p2, r2)
d = pd.DataFrame(rows); d.to_csv(f"{OUT}/robustness.csv", index=False)
pv = d[(d.model == "cons")].pivot_table(index=["variant", "window"], columns="system", values="sharpe", sort=False)
print(pv)
