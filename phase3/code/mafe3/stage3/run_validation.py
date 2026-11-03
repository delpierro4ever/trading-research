"""Stage 3 step 2: ONE validation read of the frozen M30 / M60 (entries 2020-01-01 .. 2023-01-01, exits < 2023-01-01).
Usage (from phase3/code): python -m mafe3.stage3.run_validation
Never touches data >= 2023-01-01 (loader refuses; MAFE3_UNSEAL / the token file are never used).
MAFE3_S3_SMOKE=1 runs the same code path on DISCOVERY data into a temp dir (dry run; writes nothing in results/)."""
from __future__ import annotations
import os
SMOKE = os.environ.get("MAFE3_S3_SMOKE") == "1"
if not SMOKE:
    os.environ["MAFE3_WIN_START"] = "2019-11-01"; os.environ["MAFE3_WIN_END"] = "2023-01-01"; os.environ["MAFE3_PART_START"] = "2020-01-01"
assert "MAFE3_UNSEAL" not in os.environ
import json, tempfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np, pandas as pd
from ..market import Market, O, D0
from ..stage2 import modelslib as ML, features as Fz
from ..stage2.trades import Outcomes
from ..engine import block_bootstrap_p
from .train import OUT, PREREG3, SHA3, sha

USD, USD_HI, USD_LO = 0.45, 0.60, 0.38
GATE_P, MIN_N, MIN_DAYS, MIN_POS_YEARS = 0.025, 100, 30, 2
YEARS = [2020, 2021, 2022] if not SMOKE else [2017, 2018, 2019]

def load_model(name):
    info = json.loads((OUT / "models.json").read_text())["models"][name]
    f = OUT / info["file"]; assert sha(f) == info["sha256"], f"model hash mismatch {name}"
    z = np.load(f); return dict(mu=z["mu"], sd=z["sd"], beta=z["beta"], b0=float(z["b0"])), info["H"]

def features():
    if SMOKE:
        from ..stage2 import store
        t, _, Z = store.load("disc"); return t, Z
    t, _, Z = Fz.build(datetime(2019, 11, 1, tzinfo=timezone.utc), datetime(2023, 1, 1, tzinfo=timezone.utc))
    return t, Z

def stats(oc, M, H, pos, d):
    r = oc.by[H]; n = len(pos)
    if n == 0: return dict(n=0, gross=np.nan, cost=np.nan, swap=np.nan, net=np.nan, net60=np.nan, net38=np.nan, long_share=np.nan, price=np.nan)
    pe = M.o[r["e"][pos]]; g = d * r["gross"][pos]; sw = r["swap"][pos]
    c = lambda usd: usd / pe * 1e4
    return dict(n=n, gross=g.mean(), cost=c(USD).mean(), swap=sw.mean(), net=(g - c(USD) - sw).mean(), net60=(g - c(USD_HI) - sw).mean(),
                net38=(g - c(USD_LO) - sw).mean(), long_share=(d > 0).mean(), price=pe.mean())

def main():
    assert sha(PREREG3) == SHA3, "stage-3 prereg hash mismatch"
    out = Path(tempfile.mkdtemp(dir="/home/ubuntu/mafe-data")) if SMOKE else OUT
    t_abs, Z = features(); td = t_abs - O; m = td >= D0; td, Z = td[m], Z[m]
    M = Market.from_loader("2009-11-01" if SMOKE else "2019-11-01", "2020-01-01" if SMOKE else "2023-01-01")
    oc = Outcomes(M, td); Xr = ML.design_ridge(Z)
    rows, verdict = [], {}
    for name in ("M30", "M60"):
        mdl, H = load_model(name)
        pred = ML.predict_ridge(mdl, Xr)
        r = dict(oc.by[H]); pe_all = M.o[r["e"]]
        r["cost35"] = USD / pe_all * 1e4                       # trade_rule's threshold column: c_t at $0.45 (+ expected swap)
        ok = np.nonzero(r["valid"])[0]
        pos, d = ML.trade_rule(pred[ok], r, td, ok)
        o = np.argsort(td[pos], kind="stable"); pos, d = pos[o], d[o]
        pred_ic = float(np.corrcoef(pred[ok], np.where(r["valid"], r["gross"], 0)[ok])[0, 1])
        s = stats(oc, M, H, pos, d)
        net = d * r["gross"][pos] - r["cost35"][pos] - r["swap"][pos]
        yr = oc.year[pos]
        s["p_boot"] = float(block_bootstrap_p(net, oc.week[pos])); s["days"] = int(len(np.unique(oc.day[pos])))
        ynet = {y: (float(net[yr == y].mean()) if (yr == y).any() else float("nan")) for y in YEARS}
        s["pos_years"] = int(sum(v > 0 for v in ynet.values()))        # a year without trades does not count as positive
        gate = dict(p=bool(s["p_boot"] < GATE_P), years=bool(s["pos_years"] >= MIN_POS_YEARS), days=bool(s["days"] >= MIN_DAYS), n=bool(s["n"] >= MIN_N))
        passed = all(gate.values()) and bool(s["net"] > 0)
        verdict[name] = dict(H=H, PASS=passed, gates=gate, pred_ic_all_grid=pred_ic, **{k: (None if isinstance(v, float) and np.isnan(v) else float(v)) for k, v in s.items()},
                             year_net=ynet)
        rows.append(dict(model=name, period="ALL", **s))
        for y in YEARS:
            mk = yr == y
            rows.append(dict(model=name, period=y, **stats(oc, M, H, pos[mk], d[mk])))
        print(name, json.dumps(verdict[name], default=str), flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / "validation.csv", index=False)
    (out / "verdict.json").write_text(json.dumps(dict(prereg_sha256=SHA3, window="entries 2020-01-01..2023-01-01" if not SMOKE else "SMOKE (discovery)", K=2, gate_p=GATE_P, models=verdict), indent=1, default=str))
    print(df.round(3).to_string())

if __name__ == "__main__":
    main()
