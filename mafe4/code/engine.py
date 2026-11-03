"""Event engine for MAFE-4. Causal signal at minute t close, entry at open of t+1(+lag), fixed-time exit, non-overlap per coin per trigger/H.
Guard: refuses signals >= 2024-01-01 unless validate=True (requires a frozen candidate file, checked by the caller)."""
import os, json, numpy as np, pandas as pd
GRID = "/home/ubuntu/mafe-data/mafe4/grid"
T0 = int(pd.Timestamp("2020-07-01", tz="UTC").timestamp()) // 60
COINS = "BTC ETH SOL XRP DOGE BNB ADA AVAX LINK LTC".split()
HS = (15, 30, 60, 240)
DISC_END = int(pd.Timestamp("2024-01-01", tz="UTC").timestamp()) // 60 - T0     # exclusive, grid index
VAL_END = int(pd.Timestamp("2025-01-01", tz="UTC").timestamp()) // 60 - T0
ZS, QS = (4, 6, 8), (0.6, 0.75)
WS, ZCS = (5, 15), (3, 4)
IMBW = 0.25; OI_THR = -0.005

def load(coin):
    z = np.load(f"{GRID}/{coin}.npz"); return {k: z[k] for k in z.files}

def csum(x):
    return np.cumsum(np.where(np.isnan(x), 0.0, x)), np.cumsum(~np.isnan(x))

def wsum(x, w):
    """sum and count over [t-w+1, t] (NaN as 0)."""
    s, n = csum(x); s = np.r_[0.0, s]; n = np.r_[0, n]
    i = np.arange(len(x)) + 1; lo = np.maximum(i - w, 0)
    return s[i] - s[lo], n[i] - n[lo]

def features(g, shift=0):
    o, h, l, c, v, nt, tb = (g[k] for k in ("o", "h", "l", "c", "v", "nt", "tb"))
    N = len(c); F = {}
    r = np.log(c / o); F["r"] = r
    s1, n1 = csum(r); s2, _ = csum(r * r)
    def lag(a, k): return np.r_[np.zeros(k + 1), a][:N] if False else None
    # sigma over previous 1440 minutes: [t-1440, t-1]
    S = np.r_[0.0, s1]; S2 = np.r_[0.0, s2]; Nn = np.r_[0, n1]
    t = np.arange(N); lo = np.maximum(t - 1440, 0)
    cnt = Nn[t] - Nn[lo]; sm = S[t] - S[lo]; sm2 = S2[t] - S2[lo]
    with np.errstate(all="ignore"):
        var = (sm2 - sm * sm / cnt) / (cnt - 1)
        sig = np.where(cnt >= 720, np.sqrt(np.maximum(var, 0)), np.nan)
        F["sig"] = sig
        F["imb"] = np.where(v > 0, (2 * tb - v) / v, np.nan)
        ntS = np.r_[0.0, np.cumsum(np.where(np.isnan(nt), 0, nt))]
        F["act"] = nt / ((ntS[t] - ntS[lo]) / np.maximum(cnt, 1))
        F["rng"] = (h - l) / o
        for w in (5, 15):
            _, cn = wsum(o, w)
            o_w = np.r_[np.full(w - 1, np.nan), o[:N - w + 1]]
            cum = np.log(c / o_w); cum[cn < w] = np.nan
            tbs, _ = wsum(tb, w); vs, vn = wsum(v, w)
            F[f"cum{w}"] = cum; F[f"imb{w}"] = np.where((vs > 0) & (vn == w), (2 * tbs - vs) / vs, np.nan)
        # ATR60: mean (h-l) over [t-59, t]
        rs, rn = wsum(h - l, 60); F["atr60"] = np.where(rn == 60, rs / 60, np.nan)
    F["oi"] = g["oi_chg"].astype(float)
    if shift:   # lookahead/lag control: features known `shift` minutes later (signal delayed)
        for k in list(F): F[k] = np.r_[np.full(shift, np.nan), F[k][:N - shift]]
    return F

def triggers(F, kind, a, b):
    """boolean signal mask and direction (+1 up move)."""
    if kind == "C":
        z, q = a, b; r, sig, imb = F["r"], F["sig"], F["imb"]
        with np.errstate(all="ignore"):
            m = (np.abs(r) >= z * sig) & (np.sign(imb) == np.sign(r)) & (np.abs(imb) >= q) & (F["oi"] <= OI_THR)
        return np.where(np.isnan(m.astype(float)), False, m), np.sign(r)
    w, zc = a, b; cum, sig, imb = F[f"cum{w}"], F["sig"], F[f"imb{w}"]
    with np.errstate(all="ignore"):
        m = (np.abs(cum) >= zc * sig * np.sqrt(w)) & (np.sign(imb) == np.sign(cum)) & (np.abs(imb) >= IMBW)
    return m, np.sign(cum)

def run_trigger(g, F, mask, dirn, H, lo, hi, lag=0, cheat=False, coin=""):
    o, h, l, c = g["o"], g["h"], g["l"], g["c"]
    nanc = np.r_[0, np.cumsum(np.isnan(o) | np.isnan(h) | np.isnan(l))]
    cr = np.r_[0.0, np.cumsum(np.where(np.isnan(g["fund_r"]), 0, g["fund_r"]))]
    ft = g["fund_t"]
    idx = np.flatnonzero(mask & ~np.isnan(F["sig"]))
    idx = idx[(idx >= lo) & (idx < hi)]
    rows = []; last_exit = -10**9
    for t in idx:
        e = t + (0 if cheat else 1 + lag); x = e + H
        if t < 60 or x > hi: continue
        if nanc[x + 1] - nanc[t - 59] != 0: continue          # any missing bar from signal-59 to exit
        if e < last_exit: continue
        last_exit = x
        oe = o[e]; ox = o[x]
        mup = max(h[e:x].max(), ox) / oe - 1; mdn = 1 - min(l[e:x].min(), ox) / oe
        i0 = np.searchsorted(ft, e, "right"); i1 = np.searchsorted(ft, x, "right")
        frate = (cr[i1] - cr[i0]) * 1e4
        slin = max(1.0, 0.10 * (h[e] - l[e]) / oe * 1e4); slout = max(1.0, 0.10 * (h[x] - l[x]) / ox * 1e4)
        d = 2 * F["atr60"][t] if not np.isnan(F["atr60"][t]) else np.nan
        st = []
        for side in (1, -1):
            res = (np.nan, np.nan, np.nan, np.nan)
            if not np.isnan(d):
                stop = oe - side * d
                hit = np.flatnonzero((l[e:x] <= stop) if side == 1 else (h[e:x] >= stop))
                if len(hit):
                    j = e + hit[0]; fill = o[j] if ((o[j] <= stop) if side == 1 else (o[j] >= stop)) else stop
                    sl = max(1.0, 0.10 * (h[j] - l[j]) / o[j] * 1e4)
                    f2 = (cr[np.searchsorted(ft, j, "right")] - cr[i0]) * 1e4
                    res = (side * (fill / oe - 1) * 1e4, sl, f2, j - e)
                else: res = (side * (ox / oe - 1) * 1e4, slout, frate, H)
            st.append(res)
        f = lambda k: F[k][t]
        hour = ((T0 + t) // 60) % 24; dow = ((T0 + t) // 1440 + 3) % 7   # 0=Mon (1970-01-01 Thu)
        fl = ft[:np.searchsorted(ft, t, "right")]; lastf = g["fund_r"][len(fl) - 1] * 1e4 if len(fl) else np.nan
        rows.append((coin, T0 + t, dirn[t], H, (ox / oe - 1) * 1e4, frate, slin, slout, mup * 1e4, mdn * 1e4,
                     *st[0], *st[1], f("r") * 1e4, f("sig") * 1e4, f("act"), f("imb"), f("oi"), f("rng") * 1e4, hour, dow, lastf))
    cols = ["coin", "t", "dir", "H", "ret", "fundraw", "slin", "slout", "mfe_up", "mfe_dn",
            "sl_ret", "sl_slip", "sl_fund", "sl_j", "ss_ret", "ss_slip", "ss_fund", "ss_j",
            "r_bps", "sig_bps", "act", "imb", "oi", "rng_bps", "hour", "dow", "lastfund"]
    return pd.DataFrame(rows, columns=cols)

def trigger_list():
    L = [("C", z, q) for z in ZS for q in QS] + [("E", w, zc) for w in WS for zc in ZCS]
    return L

def run_coin(coin, lo, hi, g=None, lag=0, cheat=False, kinds=None, hs=HS, Fshift=0, validate=False):
    if hi > DISC_END and not validate:
        raise RuntimeError("holdout/validation guard: signals >= 2024-01-01 need validate=True")
    g = g or load(coin); F = features(g, Fshift); out = []
    for (k, a, b) in trigger_list():
        if kinds and k not in kinds: continue
        m, d = triggers(F, k, a, b)
        for H in hs:
            df = run_trigger(g, F, m, d, H, lo, hi, lag, cheat, coin)
            df.insert(0, "trig", f"{k}|{a}|{b}"); out.append(df)
    return pd.concat(out, ignore_index=True)

def vol_edges(coin):
    g = load(coin); F = features(g); sg = F["sig"]
    a = int(pd.Timestamp("2020-09-01", tz="UTC").timestamp()) // 60 - T0
    b = int(pd.Timestamp("2023-01-01", tz="UTC").timestamp()) // 60 - T0
    x = sg[a:b]; x = x[~np.isnan(x)] * 1e4
    return [float(np.quantile(x, 1 / 3)), float(np.quantile(x, 2 / 3))]
