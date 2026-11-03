import numpy as np, pandas as pd, engine as E

MODELS = {"std": dict(spread_mult=1.0, comm_mult=1.0, fin="A"), "cons": dict(spread_mult=1.5, comm_mult=1.5, fin="B"), "stress": dict(spread_mult=1.5, comm_mult=1.5, fin="A")}

class Ctx:
    def __init__(self, universe=None, nmin=E.NMIN):
        self.P = E.load_prices(universe); self.prep = E.Prep(self.P, nmin); self.cp = E.cost_params(); self.rates = E.load_rates(self.P.index)

def run(ctx, system, mult=1.0, literal=False, lag=0, models=MODELS, spread_mult=None, pos=None):
    if pos is None: pos, unit = E.positions(ctx.prep, system, mult=mult, literal=literal)
    res = {}
    for k, m in models.items():
        m = dict(m)
        if spread_mult is not None: m["spread_mult"] = m["spread_mult"] * spread_mult
        res[k] = E.pnl(ctx.prep, pos, ctx.cp, ctx.rates, lag=lag, **m)
    return pos, res

def port(res, k="cons"):
    return res[k]["net"].sum(axis=1)

def table(pos, res, w, boot=False):
    rows = {}
    idx = E.win(pos, w).index
    for k in res:
        net = port(res, k).loc[idx]; s = E.equity_stats(net)
        gross = res[k]["gross"].sum(axis=1).loc[idx]
        s.update(gross_sharpe=E.equity_stats(gross).get("sharpe"), cost_ann=res[k]["cost"].sum(axis=1).loc[idx].mean() * 252,
                 fin_ann=res[k]["fin"].sum(axis=1).loc[idx].mean() * 252, turnover=E.turnover(pos, idx))
        if boot:
            b = E.boot_sharpe(net); s.update({"boot_" + a: v for a, v in b.items()})
        rows[k] = s
    return pd.DataFrame(rows).T
