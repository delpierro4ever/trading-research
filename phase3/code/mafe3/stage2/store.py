"""Feature store: build and load the grid feature matrices (discovery now; validation only when a frozen validation read is run).
Usage (from phase3/code): python -m mafe3.stage2.store disc"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
import numpy as np
from . import features as Fz

STORE = "/home/ubuntu/mafe-data/stage2"
def utc(*a): return datetime(*a, tzinfo=timezone.utc)
SPANS = {"disc": (utc(2009, 12, 1), utc(2020, 1, 1)), "val": (utc(2019, 11, 1), utc(2023, 1, 1))}   # includes a z-score warm-up before the measured part

def build(which):
    s, e = SPANS[which]
    t, Xr, Z = Fz.build(s, e)
    np.savez(f"{STORE}/feat_{which}.npz", t=t, raw=Xr, z=Z, names=np.array(Fz.NAMES))
    return t, Xr, Z

def load(which):
    d = np.load(f"{STORE}/feat_{which}.npz")
    return d["t"], d["raw"], d["z"]

if __name__ == "__main__":
    t, Xr, Z = build(sys.argv[1])
    print(which := sys.argv[1], t.shape, Z.shape)
