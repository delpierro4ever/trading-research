"""Glue: Market -> features -> z -> signals -> episodes, for every registered hypothesis."""
from __future__ import annotations
import numpy as np
from .features import Features, NGRID, zscore
from .engine import Hyp, z_direction, run_episodes, f7_grid_mask, flip, G_2022


class Pipeline:
    def __init__(self, mk):
        self.mk = mk
        self.g = np.arange(NGRID)
        self.feats = Features(mk).all(self.g)
        self.z = {k: zscore(v) for k, v in self.feats.items()}

    def g_start(self, h: Hyp) -> int:
        # ETHUSDT F5/F6: discovery sign-check uses 2022-2023 only (amendment notes)
        return G_2022 if (self.mk.symbol == "ETHUSDT" and h.family in ("F5", "F6")) else 0

    def episodes(self, h: Hyp, f7_sign: int | None = None):
        """Return (episodes, f7_sign). For F7 the direction is the sign of the mean gross of the long (+1) episodes,
        unless f7_sign is supplied (used to carry BTC's direction to ETH)."""
        if h.kind == "z":
            return run_episodes(self.mk, z_direction(self.z[h.feat], h.d, self.g_start(h)), h.H), None
        dir_ = np.zeros(NGRID, dtype=np.int8)
        dir_[f7_grid_mask(h)] = 1
        ep = run_episodes(self.mk, dir_, h.H)
        if f7_sign is None:
            m = ep["gross"].mean() if len(ep["gross"]) else 0.0
            f7_sign = 1 if m >= 0 else -1
        return (flip(ep) if f7_sign < 0 else ep), f7_sign
