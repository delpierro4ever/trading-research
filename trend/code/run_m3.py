"""M3 small-account reality: frozen best system with real min volumes / steps and integer rounding. USD account (EUR conversion noted).
Usage: python run_m3.py SYSTEM  (e.g. S2)"""
import sys, json, numpy as np, pandas as pd, engine as E, analysis as A
pd.set_option("display.width", 250); pd.set_option("display.float_format", "{:.3f}".format)
OUT = "/home/ubuntu/mafe-research-archive/trend/out"; BIG = "/home/ubuntu/mafe-data/trend/out"
SYSTEM = sys.argv[1]
INFO = json.load(open(E.INFO))["symbols"]
BASE_ASSET = {"EURJPY": "EUR", "EURGBP": "EUR", "EURCHF": "EUR", "GBPJPY": "GBP", "AUDJPY": "AUD"}

def usd_per_unit(c, P):
    """USD value of one broker volume unit at each date (Series), using the price frame P."""
    px = P[c].ffill()
    if c in ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"): return px
    if c in ("USDJPY", "USDCAD", "USDCHF"): return pd.Series(1.0, index=P.index)
    if c in BASE_ASSET: return P[BASE_ASSET[c] + "USD"].ffill()
    if c in ("XAUUSD", "XAGUSD", "XTIUSD", "XBRUSD", "US500", "USTEC", "BTCUSD", "ETHUSD"): return px
    if c == "DE40": return px * P["EURUSD"].ffill()
    if c == "UK100": return px * P["GBPUSD"].ffill()
    if c == "JP225": return px / P["USDJPY"].ffill()
    raise KeyError(c)

def simulate(ctx, pos, unit, eq0, lev, model, start="2009-01-01", end="2022-12-31", margin_cap=0.8):
    P, cp, cols = ctx.P, ctx.cp, ctx.prep.cols
    idx = P.loc[start:end].index; n = len(idx); pos_ = pos.loc[idx].to_numpy(); unit_ = unit.loc[idx].to_numpy()
    r = ctx.prep.r.loc[idx].fillna(0).to_numpy()
    upu = np.column_stack([usd_per_unit(c, P).loc[idx].to_numpy() for c in cols]); upu = np.nan_to_num(upu)      # USD per unit (0 before listing)
    vmin = np.array([INFO[c]["vol_min"] for c in cols]); step = np.array([INFO[c]["vol_step"] for c in cols])
    sm, cm = (1.0, 1.0) if model == "std" else (1.5, 1.5)
    hs = np.array([cp[c]["spread_frac"] / 2 * sm + cp[c]["comm_side"] * cm for c in cols])
    sl = np.array([cp[c]["swap_long_day"] for c in cols]); ss = np.array([cp[c]["swap_short_day"] for c in cols])
    days = pd.Series(idx, index=idx).diff().dt.days.fillna(1).to_numpy()
    fin_model = "A" if model == "std" else "B"
    rates = ctx.rates.loc[idx]
    cls = [E.CLS[c] for c in cols]
    E_t = eq0; held = np.zeros(len(cols)); out = []; stopouts = 0; maxmargin = 0.0; margins = []; notional_log = []
    for t in range(n):
        px_ok = upu[t]
        # P&L from yesterday's holdings
        notional_prev = held * upu[t - 1] if t > 0 else np.zeros(len(cols))
        gross = (notional_prev * r[t]).sum()
        if fin_model == "A": fin = (np.clip(notional_prev, 0, None) * sl + (-np.clip(notional_prev, None, 0)) * ss).sum() * days[t]
        else:
            f = 0.0
            for j, c in enumerate(cols):
                nl, ns = max(notional_prev[j], 0), max(-notional_prev[j], 0)
                if nl == 0 and ns == 0: continue
                if cls[j] == "FX":
                    d = rates[c[:3]].iloc[t] - rates[c[3:]].iloc[t]; f += (nl * (d - 0.01) + ns * (-d - 0.01)) / 365 * days[t]
                else:
                    rr = rates["USD"].iloc[t]; f += (-nl * (rr + 0.025) + ns * (rr - 0.025)) / 365 * days[t]
            fin = f
        E_t = E_t + gross + fin
        if E_t <= 0: out.append(0.0); E_t = 0.0; break      # ruin
        # target units
        ideal_notional = pos_[t] * E_t; ideal_units = ideal_notional / np.where(upu[t] > 0, upu[t], np.nan)
        ideal_units = np.nan_to_num(ideal_units)
        # margin scaling
        marg = (np.abs(ideal_units) * upu[t]).sum() / lev
        if marg > margin_cap * E_t and marg > 0: ideal_units = ideal_units * (margin_cap * E_t / marg)
        tgt = np.sign(ideal_units) * np.round(np.abs(ideal_units) / step) * step
        small = np.abs(tgt) < vmin
        tgt = np.where(small, np.where(np.abs(ideal_units) >= 0.5 * vmin, np.sign(ideal_units) * vmin, 0.0), tgt)
        un_units = np.abs(unit_[t] * E_t / np.where(upu[t] > 0, upu[t], np.nan)); un_units = np.nan_to_num(un_units)
        trade = (np.abs(tgt - held) > np.maximum(0.1 * un_units, 0.5 * step)) | (tgt * held < 0) | ((tgt == 0) & (held != 0))
        new = np.where(trade, tgt, held)
        cost = (np.abs(new - held) * upu[t] * hs).sum(); E_t -= cost; held = new
        # stop-out: equity < 50% of used margin
        used = (np.abs(held) * upu[t]).sum() / lev
        if used > 0 and E_t < 0.5 * used: stopouts += 1; E_t -= (np.abs(held) * upu[t] * hs).sum(); held[:] = 0; used = 0
        margins.append(used / E_t if E_t > 0 else np.nan); notional_log.append((np.abs(held) * upu[t]).sum() / E_t if E_t > 0 else np.nan)
        out.append(E_t)
    eq = pd.Series(out, index=idx[:len(out)])
    ret = eq.pct_change(); ret.iloc[0] = eq.iloc[0] / eq0 - 1
    return ret, dict(final=float(eq.iloc[-1]), stopouts=stopouts, max_margin_pct=float(np.nanmax(margins)) * 100, mean_margin_pct=float(np.nanmean(margins)) * 100,
                     mean_gross_lev=float(np.nanmean(notional_log)))

def roll12(ret):
    eq = (1 + ret).cumprod(); r12 = (eq / eq.shift(252) - 1).dropna(); return r12

if __name__ == "__main__":
    rows = []; allr = {}
    for label, uni in (("main21", E.MAIN),):
        ctx = A.Ctx(uni); pos, unit = E.positions(ctx.prep, SYSTEM)
        base = {k: A.run(ctx, SYSTEM, pos=pos)[1][k]["net"].sum(axis=1) for k in ("std", "cons")}
        for eq0 in (500, 2000, 10000):
            for lev in (30, 100, 500):
                for model in ("std", "cons"):
                    ret, info = simulate(ctx, pos, unit, eq0, lev, model)
                    ub = base[model].loc[ret.index]
                    st = E.equity_stats(ret); te = (ret - ub).std() * np.sqrt(252)
                    r12 = roll12(ret)
                    rows.append(dict(universe=label, eq0=eq0, lev=lev, model=model, **info, cagr=st["cagr"], vol=st["vol"], sharpe=st["sharpe"], maxdd=st["maxdd"],
                                     tracking_error=te, corr_unconstrained=ret.corr(ub), r12_p05=r12.quantile(.05), r12_p25=r12.quantile(.25), r12_p50=r12.median(), r12_p75=r12.quantile(.75), r12_p95=r12.quantile(.95),
                                     r12_neg_share=(r12 < 0).mean(), unconstrained_vol=E.equity_stats(ub)["vol"], unconstrained_sharpe=E.equity_stats(ub)["sharpe"]))
                    print(rows[-1]["eq0"], lev, model, {k: round(v, 3) for k, v in rows[-1].items() if isinstance(v, float)}, flush=True)
                    allr[(eq0, lev, model)] = ret
        pd.DataFrame(rows).to_csv(f"{OUT}/m3_{SYSTEM}_{label}.csv", index=False)
        pd.DataFrame({f"{a}_{b}_{c}": v for (a, b, c), v in allr.items()}).to_parquet(f"{BIG}/m3_returns_{SYSTEM}_{label}.parquet")
