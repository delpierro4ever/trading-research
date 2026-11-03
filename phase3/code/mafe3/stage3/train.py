"""Stage 3 step 1: train M30 / M60 once on all discovery data (entries < 2020-01-01 minus the stage-2 1-day purge) with the stage-2 ridge
(alpha = 10, same design/scaler). Saves coefficients + scaler and hashes. Reads no data >= 2020-01-01.
Usage (from phase3/code): python -m mafe3.stage3.train"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
from ..market import Market, O, epoch_min
from ..stage2 import modelslib as ML, features as Fz
from ..stage2.trades import Outcomes
from ..stage2.track_a import setup
from ..stage2.track_b import PURGE

ROOT = Path(__file__).resolve().parents[3]
PREREG3 = ROOT / "docs" / "STAGE3_PREREGISTRATION.md"
SHA3 = "354d2c1755eaccb66eb8943c21c39761b3ce06d70ba94798f529c4ffc913d929"
OUT = ROOT / "results" / "stage3"
MODELS = {"M30": 30, "M60": 60}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert sha(PREREG3) == SHA3, "stage-3 prereg hash mismatch"
    _, td, Z = setup()
    M = Market.from_loader("2009-11-01", "2020-01-01")
    oc = Outcomes(M, td)
    Xr = ML.design_ridge(Z)
    (OUT / "models").mkdir(parents=True, exist_ok=True)
    info = {"prereg_sha256": SHA3, "alpha": ML.ALPHA, "train": "entries 2010-01-01 .. 2020-01-01 minus 1-day purge (as stage-2 final models)", "feature_names": ML.ridge_names(), "models": {}}
    for name, H in MODELS.items():
        r = oc.by[H]; y = np.where(r["valid"], r["gross"], 0.0).astype(np.float64)
        tr = np.nonzero(r["valid"] & (td < epoch_min(2020, 1, 1) - O - PURGE))[0]
        m = ML.fit_ridge(Xr[tr], y[tr])
        f = OUT / "models" / f"{name}.npz"
        np.savez(f, mu=m["mu"], sd=m["sd"], beta=m["beta"], b0=np.array(m["b0"]), H=np.array(H))
        info["models"][name] = dict(H=H, n_train=int(len(tr)), file=f"models/{name}.npz", sha256=sha(f))
        print(name, len(tr), info["models"][name]["sha256"])
    (OUT / "models.json").write_text(json.dumps(info, indent=1))

if __name__ == "__main__":
    main()
