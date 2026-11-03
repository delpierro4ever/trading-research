"""Cell construction, cluster bootstrap, BH, pass rules, F4 binned model. Shared by discovery and validation."""
import numpy as np, pandas as pd
EV = "/home/ubuntu/mafe-data/mafe4/events"
B_BOOT = 4000; SEED = 20261014

def cell_defs():
    """(cell_id, family, trig, H) for the 64 primary cells."""
    out = []
    for fam, trigs in (("F1", [f"C|{z}|{q}" for z in (4, 6, 8) for q in (0.6, 0.75)]), ("F2", [f"C|{z}|{q}" for z in (4, 6, 8) for q in (0.6, 0.75)]),
                       ("F3", [f"E|{w}|{zc}" for w in (5, 15) for zc in (3, 4)])):
        for tg in trigs:
            for H in (15, 30, 60, 240): out.append((f"{fam}|{tg.split('|',1)[1]}|H{H}", fam, tg, H))
    return out

def prep(ev, fam, perm_rng=None):
    d = ev.copy()
    d["side"] = -d["dir"] if fam in ("F1", "F3") else d["dir"]
    if perm_rng is not None: d["side"] = perm_rng.choice([-1, 1], len(d))
    d["gross"] = d.side * d.ret; d["fund"] = d.side * d.fundraw
    d["fees"] = 10.0; d["slip"] = d.slin + d.slout
    d["cost"] = d.fees + d.slip
    d["net"] = d.gross - d.cost - d.fund
    d["net15"] = d.gross - 1.5 * d.cost - d.fund
    d["netm"] = d.gross - (5 + d.slin + 2) - d.fund
    d["mfe"] = np.where(d.side == 1, d.mfe_up, d.mfe_dn)
    long = d.side == 1
    sret = np.where(long, d.sl_ret, d.ss_ret); sslip = np.where(long, d.sl_slip, d.ss_slip); sf = np.where(long, d.sl_fund, d.ss_fund)
    d["net_stop"] = sret - 5 - 5 - d.slin - sslip - d.side * sf
    d["day"] = (d.t // 1440).astype(int)
    d["cl"] = d.coin + "_" + d.day.astype(str)
    ts = pd.to_datetime(d.t * 60, unit="s")
    d["year"] = ts.dt.year; d["bucket"] = np.where(d.year == 2020, "2020H2", d.year.astype(str)); d["q"] = ts.dt.quarter
    return d

def boot(vals, cl, B=B_BOOT, seed=SEED, side="greater"):
    """coin-day cluster bootstrap of the mean. returns mean, lo, hi, p (one-sided: P*(mean*<=0))."""
    vals = np.asarray(vals, float); n = len(vals)
    if n == 0: return (np.nan,) * 3 + (1.0,)
    codes, uniq = pd.factorize(cl); nc = len(uniq)
    s = np.bincount(codes, vals, nc); c = np.bincount(codes, minlength=nc).astype(float)
    rng = np.random.default_rng(seed); means = np.empty(B); ch = max(1, int(2e7 // nc))
    for i in range(0, B, ch):
        k = min(ch, B - i); ix = rng.integers(0, nc, (k, nc))
        means[i:i + k] = s[ix].sum(1) / c[ix].sum(1)
    p = (1 + (means <= 0).sum()) / (B + 1)
    return vals.mean(), np.quantile(means, .025), np.quantile(means, .975), p

def bh(p, q=0.10):
    p = np.asarray(p, float); m = len(p); o = np.argsort(p); adj = np.empty(m)
    ranked = p[o] * m / np.arange(1, m + 1); adj[o] = np.minimum.accumulate(ranked[::-1])[::-1]
    return np.minimum(adj, 1.0), adj <= q

def cell_stats(d):
    n = len(d); r = dict(n=n)
    if n == 0: return r
    for k in ("gross", "fees", "slip", "fund", "cost", "net", "net15", "netm", "mfe", "net_stop"): r[k] = d[k].mean()
    r["net_med"] = d.net.median(); r["win"] = (d.net > 0).mean()
    for b in ("2020H2", "2021", "2022", "2023", "2024"): r[f"n_{b}"] = int((d.bucket == b).sum())
    return r

def pass_flags(d, bucket_list=("2020H2", "2021", "2022", "2023")):
    bm = d.groupby("bucket").net.mean().reindex(bucket_list)
    cm = d.groupby("coin").net.mean().reindex("BTC ETH SOL XRP DOGE BNB ADA AVAX LINK LTC".split())
    return int((bm > 0).sum()), int((cm > 0).sum())

# ---- F4
def act_edges(evs_fit):
    u = evs_fit.drop_duplicates(["coin", "t"]).act.dropna()
    return [float(u.quantile(1 / 3)), float(u.quantile(2 / 3))]
def bins(d, vol_edges, act_e):
    vb = np.zeros(len(d), int)
    for c, e in vol_edges.items():
        m = (d.coin == c).values; vb[m] = (d.sig_bps.values[m] > e[0]).astype(int) + (d.sig_bps.values[m] > e[1])
    ab = (d.act.values > act_e[0]).astype(int) + (d.act.values > act_e[1])
    hb = (d.hour.values // 8).astype(int)
    return vb * 9 + ab * 3 + hb
def fit_model(fit, minn=10):
    fit = fit.assign(bin=fit.bin, c2=fit.cost + fit.fund)
    g0, c0 = fit.gross.mean(), fit.c2.mean(); gm = np.full(27, g0); cm = np.full(27, c0); nn = np.zeros(27, int)
    for b, x in fit.groupby("bin"):
        nn[b] = len(x)
        if len(x) >= minn: gm[b] = x.gross.mean(); cm[b] = x.c2.mean()
    return gm, cm, nn
