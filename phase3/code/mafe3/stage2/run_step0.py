"""Stage-2 step 0: oracle exclusion of horizons on discovery (section 1). Usage (from phase3/code): python -m mafe3.stage2.run_step0"""
from __future__ import annotations
import json, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from ..market import Market, O, D0
from . import store
from .trades import Outcomes, HS

ROOT = Path(__file__).resolve().parents[3]
PREREG2 = ROOT / "docs" / "STAGE2_PREREGISTRATION.md"
SHA2 = "4adad97f739c04645fbb4bdca431594ec96789b44c29a7b8af2331c56ba6b080"
OUT = ROOT / "results" / "stage2"

def main():
    assert hashlib.sha256(PREREG2.read_bytes()).hexdigest() == SHA2, "stage-2 prereg hash mismatch"
    M = Market.from_loader("2009-11-01", "2020-01-01")
    t_abs, _, _ = store.load("disc")
    td = t_abs - O
    m = td >= D0
    td = td[m]
    oc = Outcomes(M, td, oracle=True)
    rows = []
    for H in HS:
        r = oc.by[H]; v = r["valid"]
        orc, cost, swap = float(r["mfe"][v].mean()), float(r["cost35"][v].mean()), float(r["swap"][v].mean())
        rows.append(dict(H_min=H, n_grid=int(v.sum()), oracle_bps=orc, cost35_bps=cost, mean_swap_bps=swap, threshold_bps=4 * (cost + swap),
                         ratio=orc / (cost + swap), kept=bool(orc >= 4 * (cost + swap))))
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "oracle.csv", index=False)
    kept = [int(h) for h in df[df.kept].H_min]
    (OUT / "kept_H.json").write_text(json.dumps({"kept_H_min": kept, "prereg_sha256": SHA2}, indent=1))
    print(df.round(3).to_string()); print("kept", kept)

if __name__ == "__main__":
    main()
