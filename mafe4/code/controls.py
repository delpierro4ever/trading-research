"""Controls: planted signal (BTC), lookahead/lag + cheat positive control, permuted-direction null."""
import os, sys, glob, numpy as np, pandas as pd, engine as E, stats as S
from discover import load
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
out = []
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); out.append(s)

def cellnet(ev, cid_list=None):
    rows = []
    for cid, fam, tg, H in S.cell_defs():
        d = S.prep(ev[(ev.trig == tg) & (ev.H == H)], fam)
        if len(d) == 0: continue
        se = d.groupby("cl").net.sum().std() * np.sqrt(d.cl.nunique()) / len(d) if d.cl.nunique() > 1 else np.nan
        rows.append(dict(cell=cid, n=len(d), gross=d.gross.mean(), net=d.net.mean(), se=se))
    return pd.DataFrame(rows).set_index("cell")

which = sys.argv[1]
if which == "planted":
    X = 20.0 / 1e4; H = 30
    g = E.load("BTC"); F = E.features(g)
    m, d = E.triggers(F, "C", 4, 0.6)
    base = E.run_trigger(g, F, m, d, H, 0, E.DISC_END, coin="BTC")
    N = len(g["c"]); delta = np.zeros(N)
    for t, dr in zip(base.t - E.T0, base.dir):
        e = t + 1; side = -dr
        delta[e:e + H + 1] += side * X * np.arange(H + 1) / H; delta[e + H + 1:] += side * X
    g2 = dict(g)
    for k in "ohlc": g2[k] = g[k] * np.exp(delta)
    ev2 = E.run_coin("BTC", 0, E.DISC_END, g=g2, kinds=["C"], hs=(30,))
    ev1 = E.run_coin("BTC", 0, E.DISC_END, g=g, kinds=["C"], hs=(30,))
    for nm, ev in (("baseline", ev1), ("planted+20bps", ev2)):
        dd = S.prep(ev[ev.trig == "C|4|0.6"], "F1")
        mm, lo, hi, p = S.boot(dd.gross.values, dd.cl.values)
        log(f"PLANTED {nm}: n={len(dd)} mean gross={mm:.2f} bps CI[{lo:.2f},{hi:.2f}] one-sided p(gross<=0)={p:.4f}")
elif which == "lookahead":
    b = cellnet(load("disc")); l = cellnet(load("lag1")); c = cellnet(load("cheat"))
    j = b.join(l, rsuffix="_lag", how="inner").join(c, rsuffix="_cheat", how="inner")
    z = (j.net_lag - j.net) / np.sqrt(j.se ** 2 + j.se_lag ** 2)
    zc = (j.net_cheat - j.net) / np.sqrt(j.se ** 2 + j.se_cheat ** 2)
    log(f"LOOKAHEAD cells compared={len(j)}  mean net baseline={j.net.mean():.2f} lag+1={j.net_lag.mean():.2f} cheat(entry at signal open)={j.net_cheat.mean():.2f}")
    log(f"  lag+1 improves by >1 SE in {(z>1).sum()} cells (>2 SE: {(z>2).sum()}); degrades by >1 SE in {(z<-1).sum()}")
    log(f"  cheat improves by >1 SE in {(zc>1).sum()} cells (>2 SE: {(zc>2).sum()}); mean gross base={j.gross.mean():.2f} lag={j.gross_lag.mean():.2f} cheat={j.gross_cheat.mean():.2f}")
    j.round(3).to_csv(f"{R}/control_lookahead.csv")
elif which == "perm":
    ev = load("disc"); P = []
    for seed in (1, 2, 3):
        rng = np.random.default_rng(seed); rows = []
        for cid, fam, tg, H in S.cell_defs():
            d = S.prep(ev[(ev.trig == tg) & (ev.H == H)], fam, perm_rng=rng)
            if len(d) == 0: rows.append((cid, 0, np.nan, 1.0)); continue
            mm, lo, hi, p = S.boot(d.net.values, d.cl.values, B=1000, seed=seed); rows.append((cid, len(d), d.gross.mean(), p))
        r = pd.DataFrame(rows, columns=["cell", "n", "gross", "p"]); adj, sig = S.bh(r.p.values)
        log(f"PERM seed={seed}: mean gross over cells={r.gross.mean():.3f} bps (max |cell gross|={r.gross.abs().max():.2f}); cells p<0.05: {(r.p<.05).sum()}/{len(r)}; BH q<=0.10 discoveries: {sig.sum()} (their n: {r.n[sig].tolist()}); among cells with n>=100: p<0.05 {((r.p<.05)&(r.n>=100)).sum()}/{(r.n>=100).sum()}, BH discoveries {(sig&(r.n>=100)).sum()}")
open(f"{R}/controls_{which}.txt", "w").write("\n".join(out))
