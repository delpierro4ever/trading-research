"""EXPLORATORY descriptives on DISCOVERY data only (never evidence). Events: |r|>=4 sigma & same-sign |imb|>=0.6 (no OI condition), all 10 coins."""
import os, numpy as np, pandas as pd, engine as E
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"); FIG = os.path.join(R, "..", "docs"); os.makedirs(FIG, exist_ok=True)
K = np.arange(-60, 241)
G = {}; Fs = {}
ev = []
for c in E.COINS:
    g0 = E.load(c); F = E.features(g0); G[c] = {"o": g0["o"], "c": g0["c"]}; Fs[c] = {"sig": F["sig"]}
    with np.errstate(all="ignore"):
        z = np.abs(F["r"]) / F["sig"]; m = (z >= 4) & (np.sign(F["imb"]) == np.sign(F["r"])) & (np.abs(F["imb"]) >= 0.6)
    m[:1500] = False; m[E.DISC_END - 241:] = False
    for t in np.flatnonzero(m):
        cl = g0["c"][t + K]
        if np.isnan(cl).any(): continue
        ev.append(dict(coin=c, t=t, z=z[t], dir=np.sign(F["r"][t]), oi=F["oi"][t], path=np.log(cl / cl[60]) * 1e4 * np.sign(F["r"][t])))
    del g0, F
EV = pd.DataFrame(ev); EV["ts"] = pd.to_datetime((EV.t + E.T0) * 60, unit="s"); EV["hour"] = EV.ts.dt.hour; EV["wk"] = EV.ts.dt.dayofweek >= 5
EV["year"] = EV.ts.dt.year; EV["zb"] = pd.cut(EV.z, [4, 6, 8, 1e9], right=False, labels=["4-6", "6-8", "8+"])
EV["grp"] = EV.coin.map(lambda c: c if c in ("BTC", "ETH") else "alts")
EV["updown"] = np.where(EV.dir > 0, "up(short squeeze)", "down(long liq)")
EV["fund_slot"] = ((EV.ts.dt.hour % 8) * 60 + EV.ts.dt.minute) // 60   # hours since last funding time
P = np.vstack(EV.path.values)
rows = []
def summ(name, mask):
    n = int(mask.sum())
    if n < 20: return
    p = P[mask]; mu = p.mean(0); se = p.std(0, ddof=1) / np.sqrt(n)
    for k in (5, 15, 30, 60, 240):
        i = 60 + k; rows.append(dict(group=name, n=n, k=k, mean_bps=mu[i], se_bps=se[i], median_bps=np.median(p[:, i])))
    return mu, se
paths = {}
summ("ALL", np.ones(len(EV), bool)); paths["ALL"] = P.mean(0)
for col in ("grp", "zb", "updown", "wk", "year", "fund_slot"):
    for v in sorted(EV[col].astype(str).unique()): summ(f"{col}={v}", (EV[col].astype(str) == v).values)
for lo in (0, 6, 12, 18): summ(f"hour{lo:02d}-{lo+6:02d}", ((EV.hour >= lo) & (EV.hour < lo + 6)).values)
with_oi = EV.oi <= -0.005; summ("OIdrop>=0.5%", with_oi.values); summ("noOIdrop", (~with_oi & EV.oi.notna()).values)
pd.DataFrame(rows).to_csv(f"{R}/explore_event_study_summary.csv", index=False)
pd.DataFrame({"k": K, "mean_bps": P.mean(0), "se": P.std(0, ddof=1) / np.sqrt(len(P))}).to_csv(f"{R}/explore_event_study_all.csv", index=False)
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for nm, msk, col in (("all", np.ones(len(EV), bool), "#333"), ("down (long liq.)", (EV.dir < 0).values, "#c0392b"), ("up (short sq.)", (EV.dir > 0).values, "#2471a3")):
    mu = P[msk].mean(0); se = P[msk].std(0, ddof=1) / np.sqrt(msk.sum()); ax[0].plot(K, mu, color=col, label=f"{nm} n={msk.sum()}"); ax[0].fill_between(K, mu - 2 * se, mu + 2 * se, color=col, alpha=.12)
ax[0].axvline(0, color="grey", lw=.6); ax[0].axhline(0, color="grey", lw=.6); ax[0].set_xlabel("minutes from signal-minute close"); ax[0].set_ylabel("move-signed cum. return, bps (+ = continuation)"); ax[0].legend(frameon=False); ax[0].set_title("EXPLORATORY: avg path around cascades (discovery)")
for nm in ("4-6", "6-8", "8+"):
    msk = (EV.zb.astype(str) == nm).values
    if msk.sum() > 20: ax[1].plot(K, P[msk].mean(0), label=f"z {nm} n={msk.sum()}")
ax[1].axvline(0, color="grey", lw=.6); ax[1].axhline(0, color="grey", lw=.6); ax[1].legend(frameon=False); ax[1].set_xlabel("minutes"); ax[1].set_title("by size")
plt.tight_layout(); plt.savefig(f"{FIG}/explore_event_paths.png", dpi=110); plt.close()
# --- clustering
ts_all = np.sort(EV.t.values); EVs = EV.sort_values("t")
gap = np.diff(ts_all); cl = {}
cl["n_events"] = len(EV); cl["share_followed_by_another_event_within_60min_any_coin"] = float((gap <= 60).mean())
day = (EV.t + E.T0) // 1440; dc = day.value_counts(); cl["n_event_days"] = int(len(dc)); cl["share_events_on_top5pct_event_days"] = float(dc.sort_values(ascending=False).head(max(1, int(.05 * len(dc)))).sum() / len(EV))
cl["same_minute_multi_coin_share"] = float((EV.groupby("t").coin.nunique() > 1).mean())
# per-coin shares of events that are in a multi-coin burst (>=3 coins within 10 min)
bt = EV.sort_values("t"); burst = [(np.abs(EV.t.values - t) <= 10) for t in bt.t.values]
nb = np.array([len(set(EV.coin.values[b])) for b in burst]); cl["share_events_in_burst_ge3_coins_within10min"] = float((nb >= 3).mean())
# --- BTC-led spillover: alt reaction after BTC events, split by whether alt has already moved
btc = EV[EV.coin == "BTC"]; sp = []
for _, e in btc.iterrows():
    t = int(e.t)
    for c in E.COINS[1:]:
        c0 = G[c]["c"]; o0 = G[c]["o"]; F = Fs[c]
        if np.isnan(c0[t - 5:t + 31]).any() or np.isnan(F["sig"][t]): continue
        moved = np.log(c0[t] / o0[t]) * e.dir / F["sig"][t]       # alt's own signal-minute move in sigma units, signed with BTC
        r = {k: np.log(c0[t + k] / c0[t]) * e.dir * 1e4 for k in (1, 5, 15, 30)}
        sp.append(dict(coin=c, moved_sigma=moved, **{f"fwd{k}": v for k, v in r.items()}))
sp = pd.DataFrame(sp); sp["moved"] = pd.cut(sp.moved_sigma, [-1e9, 1, 3, 1e9], labels=["<1sig(laggard)", "1-3sig", ">3sig(already)"])
spt = sp.groupby("moved", observed=True)[["fwd1", "fwd5", "fwd15", "fwd30"]].agg(["mean", "count"]); spt.to_csv(f"{R}/explore_btc_spillover.csv")
pd.DataFrame([cl]).T.to_csv(f"{R}/explore_clustering.csv", header=False)
print(pd.DataFrame(rows).pivot_table(index="group", columns="k", values="mean_bps").round(1).to_string())
print(cl); print(spt.round(2).to_string())
