"""M3b: min-size facts table, small-universe simulations and bootstrap of 12-month outcomes. Usage: python run_m3b.py SYSTEM"""
import sys, json, numpy as np, pandas as pd
sys.argv = sys.argv[:2] if len(sys.argv) > 1 else ["x", "S1"]
import engine as E, analysis as A, run_m3 as M
pd.set_option("display.width", 250); pd.set_option("display.float_format", "{:.3f}".format); pd.set_option("display.max_columns", 40)
OUT = M.OUT; SYSTEM = M.SYSTEM; INFO = M.INFO
ctx = A.Ctx(); sig_end = ctx.prep.sig.loc["2022-12-30"]
spot = {k: (v["bid"] + v["ask"]) / 2 for k, v in INFO.items()}
def usd_now(c):
    p = spot[c]
    if c in ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"): return p
    if c in ("USDJPY", "USDCAD", "USDCHF"): return 1.0
    if c in M.BASE_ASSET: return spot[M.BASE_ASSET[c] + "USD"]
    if c in ("XAUUSD", "XAGUSD", "XTIUSD", "XBRUSD", "US500", "USTEC", "BTCUSD", "ETHUSD"): return p
    if c == "DE40": return p * spot["EURUSD"]
    if c == "UK100": return p * spot["GBPUSD"]
    if c == "JP225": return p / spot["USDJPY"]
rows = []
for c in E.MAIN + E.CLASSES["CRYPTO"]:
    i = INFO[c]; mn = i["vol_min"] * usd_now(c)
    sg = sig_end.get(c, np.nan) if c in sig_end.index else np.nan
    rows.append(dict(instrument=c, cls=E.CLS[c], min_units=i["vol_min"], step=i["vol_step"], min_notional_usd=mn, min_notional_eur=mn / spot["EURUSD"],
                     margin_min_eur_broker=i.get("margin_1lot_units"), margin_1to30_usd=mn / 30, margin_1to100_usd=mn / 100, margin_1to500_usd=mn / 500, sigma_2022=sg,
                     minlot_vol_pct_of_500=mn * sg / 500 * 100 if sg == sg else np.nan, minlot_vol_pct_of_2000=mn * sg / 2000 * 100 if sg == sg else np.nan,
                     minlot_vol_pct_of_10000=mn * sg / 10000 * 100 if sg == sg else np.nan, spread_bp=ctx.cp[c]["spread_frac"] * 1e4))
facts = pd.DataFrame(rows); facts.to_csv(f"{OUT}/m3_minsize_facts.csv", index=False); print(facts[["instrument", "min_notional_usd", "sigma_2022", "minlot_vol_pct_of_500", "minlot_vol_pct_of_2000", "minlot_vol_pct_of_10000", "spread_bp"]])

# smallest sensible universe for USD 500, chosen from the min-size facts only (lowest annual vol of one minimum position, FX only, 6 instruments)
fx = facts[facts.cls == "FX"].sort_values("minlot_vol_pct_of_500")
SMALL = list(fx.instrument.head(6)); MID = list(fx.instrument.head(8)) + ["XAGUSD"]
print("SMALL universe (6 lowest min-lot-risk FX):", SMALL)
def boot12(ret, n=5000, block=20, seed=1):
    x = np.asarray(ret.dropna()); T = len(x); rng = np.random.default_rng(seed); idx = np.empty((n, 252), dtype=np.int32); idx[:, 0] = rng.integers(0, T, n)
    new = rng.random((n, 252)) < 1 / block; rs = rng.integers(0, T, (n, 252))
    for t in range(1, 252): idx[:, t] = np.where(new[:, t], rs[:, t], (idx[:, t - 1] + 1) % T)
    r = np.prod(1 + x[idx], axis=1) - 1
    return {f"boot12_p{q}": float(np.percentile(r, q)) for q in (5, 25, 50, 75, 95)} | {"boot12_neg": float((r < 0).mean())}
res = []
for label, uni, eqs in (("main21", E.MAIN, (500, 2000, 10000)), ("MID9", MID, (2000,)), ("SMALL6", SMALL, (500, 2000))):
    c = A.Ctx(uni) if label != "main21" else ctx
    pos, unit = E.positions(c.prep, SYSTEM)
    base = {k: A.run(c, SYSTEM, pos=pos)[1][k]["net"].sum(axis=1) for k in ("std", "cons")}
    for eq0 in eqs:
        for model in ("std", "cons"):
            ret, info = M.simulate(c, pos, unit, eq0, 500, model); ub = base[model].loc[ret.index]
            st = E.equity_stats(ret); r12 = M.roll12(ret)
            held = (pd.DataFrame(0.0, index=ret.index, columns=[]))
            res.append(dict(universe=label, n_instr=len(uni), eq0=eq0, model=model, **info, cagr=st["cagr"], vol=st["vol"], sharpe=st["sharpe"], maxdd=st["maxdd"],
                            tracking_error=(ret - ub).std() * np.sqrt(252), corr_unconstrained=ret.corr(ub), unconstr_vol=E.equity_stats(ub)["vol"], unconstr_sharpe=E.equity_stats(ub)["sharpe"],
                            emp12_p05=r12.quantile(.05), emp12_p50=r12.median(), emp12_p95=r12.quantile(.95), emp12_neg=(r12 < 0).mean(), **boot12(ret)))
            print(res[-1]["universe"], eq0, model, {k: round(float(v), 3) for k, v in res[-1].items() if isinstance(v, (float, np.floating))}, flush=True)
pd.DataFrame(res).to_csv(f"{OUT}/m3_{SYSTEM}_universes.csv", index=False)
json.dump(dict(SMALL=SMALL, MID=MID), open(f"{OUT}/m3_universes.json", "w"))
