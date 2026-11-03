"""Core definitions for MAFE-1R (see ANALYSIS_PLAN.md). Pure functions; no I/O."""
import numpy as np
HS = (5, 10, 50, 100, 250)
HOLD_MS = 300_000
EXIT_DELAY_MS = 100
FEAT_W = (300, 3600)

def side_of(buyer_is_maker):
    return np.where(buyer_is_maker, -1, 1).astype(np.int8)

def run_length(s):
    """Causal run length of same-side events ending at i, capped at 5 (inclusive window {i-4..i}); window truncated at segment start."""
    n = len(s)
    chg = np.empty(n, bool); chg[0] = True; chg[1:] = s[1:] != s[:-1]
    start = np.maximum.accumulate(np.where(chg, np.arange(n), 0))
    return np.minimum(np.arange(n) - start + 1, 5).astype(np.int8)

def anchor_mask(ts, offset=0):
    """every 250th event of the segment (global index = offset+i) + first event of each 30 s UTC bucket."""
    n = len(ts); i = np.arange(n)
    m = ((i + offset) % 250) == 0
    b = ts // 30000
    f = np.empty(n, bool); f[0] = True; f[1:] = b[1:] != b[:-1]
    return m | f

def event_response(price, s, idx, h):
    n = len(price); j = idx + h
    ok = j < n
    r = np.full(len(idx), np.nan)
    r[ok] = s[idx[ok]] * (price[j[ok]] - price[idx[ok]]) / price[idx[ok]] * 1e4
    return r

def clock_response(ts_ext, price_ext, s, idx, ms=HOLD_MS):
    j = np.searchsorted(ts_ext, ts_ext[idx] + ms, side="left")
    ok = j < len(ts_ext)
    r = np.full(len(idx), np.nan)
    r[ok] = s[idx[ok]] * (price_ext[j[ok]] - price_ext[idx[ok]]) / price_ext[idx[ok]] * 1e4
    return r

def replay(ts_ext, price_ext, sig_idx, s, d_ms, free_ts):
    """Fixed-300 s one-position-at-a-time taker replay.
    sig_idx: sorted indices (into ext arrays, restricted to the current day) of signal events; s: side array (ext length).
    Returns list of (sig_i, entry_i, exit_i) and the new free_ts."""
    out = []
    sig_ts = ts_ext[sig_idx]
    n = len(ts_ext)
    while True:
        k = np.searchsorted(sig_ts, free_ts, side="left")
        if k >= len(sig_idx): break
        si = sig_idx[k]
        ei = np.searchsorted(ts_ext, ts_ext[si] + d_ms, side="left")
        if ei >= n: break
        xi = np.searchsorted(ts_ext, ts_ext[ei] + HOLD_MS + EXIT_DELAY_MS, side="left")
        if xi >= n: break
        out.append((si, ei, xi))
        free_ts = ts_ext[xi]
    return out, free_ts

def bars_for_day(ts, price, qty, day0_ms, last_price_prev):
    """1-second bars for one UTC day (86400 s)."""
    sec = ((ts - day0_ms) // 1000).astype(np.int64)
    cnt = np.bincount(sec, minlength=86400).astype(np.float64)
    vol = np.bincount(sec, weights=qty, minlength=86400)
    prev = np.empty(len(price)); prev[0] = last_price_prev if last_price_prev is not None else price[0]; prev[1:] = price[:-1]
    chg = np.bincount(sec, weights=(price != prev).astype(np.float64), minlength=86400)
    P = np.full(86400, np.nan)
    last = np.flatnonzero(np.r_[sec[1:] != sec[:-1], True])
    P[sec[last]] = price[last]
    # forward fill
    idx = np.where(~np.isnan(P), np.arange(86400), -1)
    idx = np.maximum.accumulate(idx)
    first_valid = idx >= 0
    Pf = np.where(first_valid, P[np.maximum(idx, 0)], np.nan)
    if last_price_prev is not None:
        Pf = np.where(first_valid, Pf, last_price_prev)
    else:
        Pf = np.where(first_valid, Pf, price[0])
    return cnt, vol, chg, Pf

class FeatureState:
    """Holds trailing 3600 s of bars; builds cumulative sums for causal window features."""
    def __init__(self, tail=None):
        self.tail = tail  # dict of arrays len 3600 or None (first day)
    def build(self, cnt, vol, chg, Pf):
        T = 3600
        has = self.tail is not None
        if has:
            c = np.r_[self.tail["cnt"], cnt]; v = np.r_[self.tail["vol"], vol]; g = np.r_[self.tail["chg"], chg]; P = np.r_[self.tail["P"], Pf]
        else:
            c = np.r_[np.zeros(T), cnt]; v = np.r_[np.zeros(T), vol]; g = np.r_[np.zeros(T), chg]; P = np.r_[np.full(T, Pf[0]), Pf]
        r = np.zeros(len(P)); r[1:] = np.log(P[1:] / P[:-1])
        z = lambda a: np.r_[0.0, np.cumsum(a)]
        self.cum = dict(c=z(c), v=z(v), g=z(g), r2=z(r * r), c2=z(c * c))
        self.valid0 = 0 if has else T
        self.newtail = dict(cnt=cnt[-T:], vol=vol[-T:], chg=chg[-T:], P=Pf[-T:])
    def feats(self, t_ms, day0_ms):
        T = 3600
        k = ((t_ms - day0_ms) // 1000).astype(np.int64) + T  # index of current (incomplete) second; window = [k-W, k-1]
        out = {}
        cu = self.cum
        for W in FEAT_W:
            a = k - W
            ok = a >= self.valid0
            a = np.maximum(a, 0)
            n = cu["c"][k] - cu["c"][a]; vol = cu["v"][k] - cu["v"][a]; g = cu["g"][k] - cu["g"][a]
            r2 = cu["r2"][k] - cu["r2"][a]; c2 = cu["c2"][k] - cu["c2"][a]
            mu = n / W; sd = np.sqrt(np.maximum(c2 / W - mu * mu, 0))
            with np.errstate(divide="ignore", invalid="ignore"):
                out[f"rate_{W}"] = np.where(ok, mu, np.nan)
                out[f"vol_{W}"] = np.where(ok, vol, np.nan)
                out[f"rv_{W}"] = np.where(ok, np.sqrt(r2) * 1e4, np.nan)
                out[f"chgfreq_{W}"] = np.where(ok & (n > 0), g / n, np.nan)
                out[f"evperchg_{W}"] = np.where(ok & (g > 0), n / g, np.nan)
                out[f"meansize_{W}"] = np.where(ok & (n > 0), vol / n, np.nan)
                out[f"burst_{W}"] = np.where(ok & (mu + sd > 0), (sd - mu) / (sd + mu), np.nan)
        return out
