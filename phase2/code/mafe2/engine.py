"""Hypothesis registry, signal construction and the greedy non-overlapping execution engine (MAFE-2 discovery)."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .features import NGRID, NMIN, LS, HS, zscore

COST12, COST8 = 12.0, 8.0
Z_THRESH = 1.5
# grid hour index of 2022-01-01 (2020 is a leap year): 366 + 365 days
G_2022 = (366 + 365) * 24


@dataclass(frozen=True)
class Hyp:
    id: str
    family: str
    feat: str            # key in Features.all() ("" for F7)
    d: int               # +1 continuation / -1 reversal (0 for F7)
    H: int               # horizon in minutes
    kind: str = "z"      # "z" | "hod" | "dow"
    param: int = -1      # hour-of-day or weekday for F7


def build_registry() -> list[Hyp]:
    hyps: list[Hyp] = []
    dn = {1: "C", -1: "R"}
    for fam, feats in (("F1", "F1"), ("F2", "F2"), ("F4", "F4"), ("F5", "F5"), ("F8", "F8")):
        for ln in LS:
            for hn, H in HS.items():
                for d in (1, -1):
                    hyps.append(Hyp(f"{fam}_L{ln}_H{hn}_{dn[d]}", fam, f"{feats}_{ln}", d, H))
    for hn, H in HS.items():
        for d in (1, -1):
            hyps.append(Hyp(f"F3_H{hn}_{dn[d]}", "F3", "F3", d, H))
    for which in ("top", "glob"):
        for hn, H in HS.items():
            for d in (1, -1):
                hyps.append(Hyp(f"F6_{which}_H{hn}_{dn[d]}", "F6", f"F6_{which}", d, H))
    for h in range(24):
        hyps.append(Hyp(f"F7_hod{h:02d}", "F7", "", 0, 60, "hod", h))
    for w in range(7):
        hyps.append(Hyp(f"F7_dow{w}", "F7", "", 0, 1440, "dow", w))
    # order by family number for readability
    hyps.sort(key=lambda h: (h.family, h.id))
    return hyps


def z_direction(z: np.ndarray, d: int, g_start: int = 0) -> np.ndarray:
    """direction array on the grid from a z-score array: d*sign(z) where |z|>=1.5, else 0; no signals before grid index g_start."""
    dir_ = np.zeros(len(z), dtype=np.int8)
    with np.errstate(invalid="ignore"):
        fire = np.abs(z) >= Z_THRESH
    dir_[fire] = (d * np.sign(z[fire])).astype(np.int8)
    dir_[:g_start] = 0
    return dir_


def f7_grid_mask(h: Hyp) -> np.ndarray:
    g = np.arange(NGRID)
    if h.kind == "hod":
        return (g % 24) == h.param
    # day of week: weekday of 2020-01-01 (Wednesday) = 2 with Monday=0
    day = g // 24
    return ((day + 2) % 7 == h.param) & (g % 24 == 0)


def run_episodes(mk, dir_: np.ndarray, H: int, cost_free: bool = False) -> dict:
    """Greedy non-overlapping episodes.

    t = g*60 min; entry = open of 1m bar at t+1; exit = open of bar at entry+H. Next admissible grid point is the first
    with t' >= exit time (literal reading => g' = g + H/60 + 1). Episodes whose exit would be >= 2024-01-01 are dropped.
    Returns arrays: g, d, gross (bps), fund (bps).
    """
    cand = np.nonzero(dir_)[0]
    op = mk.open
    nxt = 0
    G, D, GR = [], [], []
    for g in cand:
        if g < nxt:
            continue
        e = g * 60 + 1
        x = e + H
        if x >= NMIN:                      # exit not inside discovery -> drop (and every later one)
            break
        pe, px = op[e], op[x]
        if not (pe > 0 and px > 0):
            continue                        # missing bar -> skip, position never opened
        d = int(dir_[g])
        G.append(g); D.append(d); GR.append(d * np.log(px / pe) * 1e4)
        nxt = -(-x // 60)                   # ceil(exit/60): first grid hour >= exit
    G = np.array(G, dtype=np.int64); D = np.array(D, dtype=np.int8); GR = np.array(GR, dtype=float)
    return {"g": G, "d": D, "gross": GR, "fund": funding_bps(mk, G, D, H), "H": H}


def funding_bps(mk, G, D, H):
    """sum over funding events with time in (entry, exit] of -direction*rate*1e4."""
    if len(G) == 0:
        return np.zeros(0)
    cs = np.concatenate([[0.0], np.cumsum(mk.fund_rate)])
    e = G * 60.0 + 1.0
    ia = np.searchsorted(mk.fund_min, e, side="right")
    ib = np.searchsorted(mk.fund_min, e + H, side="right")
    return -D * (cs[ib] - cs[ia]) * 1e4


def flip(ep: dict) -> dict:
    """Reverse the direction of every episode (gross and funding both change sign)."""
    return {**ep, "d": -ep["d"], "gross": -ep["gross"], "fund": -ep["fund"]}


def net(ep: dict, cost: float = COST12) -> np.ndarray:
    return ep["gross"] + ep["fund"] - cost
