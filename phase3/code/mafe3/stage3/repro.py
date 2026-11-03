"""Behaviour-preservation check: re-run the stage-2 Track B ridge walk-forward (discovery only) and compare with the committed rows.
Usage (from phase3/code): python -m mafe3.stage3.repro"""
from __future__ import annotations
import json, tempfile
from pathlib import Path
import numpy as np, pandas as pd
from ..stage2 import track_b as TB
from .train import OUT

def main():
    tmp = Path(tempfile.mkdtemp(dir=OUT)); TB.OUT = tmp
    S = TB.run(tag="repro", models=("ridge",), save_models=False)
    res = {}
    for nm, key in (("summary", ["model", "H"]), ("walkforward", ["model", "H", "year"])):
        new = pd.read_csv(tmp / f"repro_{nm}.csv")
        old = pd.read_csv(OUT.parent / "stage2" / f"trackB_{nm}.csv")
        old = old[old.model == "ridge"]
        cols = [c for c in new.columns if c not in ("gate_p", "pass")]       # gate_p/pass depend on the number of models (K) in the run
        a = new[cols].sort_values(key).reset_index(drop=True); b = old[cols].sort_values(key).reset_index(drop=True)
        res[nm] = dict(rows=len(a), exact_equal=bool(a.equals(b)), max_abs_diff=float(np.nanmax(np.abs(a.select_dtypes("number").to_numpy() - b.select_dtypes("number").to_numpy()))))
    (OUT / "repro.json").write_text(json.dumps(res, indent=1)); print(res)
    import shutil; shutil.rmtree(tmp)

if __name__ == "__main__":
    main()
