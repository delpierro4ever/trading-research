"""SEALED HOLDOUT TEST (2023-01-01 -> 2026-09-30). Refuses to run unless TREND_UNSEAL=1. To be run ONCE by the lead researcher.
Runs the frozen best-validated system (out/best_system.json) exactly as specified in PREREG.md, plus the other systems for reference, and prints the gate verdict:
net Sharpe > 0 under the conservative model (x1.5 spread/commission + financing Model B) and max drawdown < 30 %."""
import os, sys, json
if os.environ.get("TREND_UNSEAL") != "1":
    sys.exit("HOLDOUT IS SEALED. Set TREND_UNSEAL=1 to run (once).")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "code"))
import numpy as np, pandas as pd, engine as E, analysis as A
HO = "/home/ubuntu/mafe-data/trend/daily/holdout.parquet"
E.SEAL = pd.Timestamp("2026-09-30")
full = pd.concat([pd.read_parquet(E.DAILY), pd.read_parquet(HO)]).sort_index()
full = full.loc[:"2026-09-30", E.MAIN].astype(float)
class Ctx(A.Ctx):
    def __init__(self):
        self.P = full; self.prep = E.Prep(full); self.cp = E.cost_params(); self.rates = E.load_rates(full.index, end="2026-09-30").ffill()
ctx = Ctx(); best = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "best_system.json")))["best"]
if best is None and os.environ.get("TREND_RUN_FAILED") != "1":
    sys.exit("No system passed the validation gate (out/gates.json); per PREREG none goes to the holdout. Set TREND_RUN_FAILED=1 to run all three for reference only (lead decision).")
idx = ctx.P.loc["2023-01-01":"2026-09-30"].index
for s in ([best] if best else []) + [x for x in ("S1", "S2", "S3") if x != best]:
    pos, res = A.run(ctx, s)
    for k in ("std", "cons", "stress"):
        net = res[k]["net"].sum(axis=1).loc[idx]; st = E.equity_stats(net); b = E.boot_sharpe(net)
        print(s, "(FROZEN BEST)" if s == best else "(reference)", k, {a: round(float(v), 3) for a, v in st.items()}, "boot p05/p95", round(b["p05"], 3), round(b["p95"], 3))
    st = E.equity_stats(res["cons"]["net"].sum(axis=1).loc[idx])
    print(s, "HOLDOUT GATE (cons):", "PASS" if st["sharpe"] > 0 and st["maxdd"] > -0.30 else "FAIL", flush=True)
