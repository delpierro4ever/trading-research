"""Validation checks for the MAFE-2 discovery code. Run from phase2/code:  python -m tests.run_checks"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from mafe2.features import load_market, Features, zscore, NGRID, NMIN
from mafe2.engine import build_registry, z_direction, run_episodes, net
from mafe2.pipeline import Pipeline

OUT = Path(__file__).resolve().parents[2] / "results" / "discovery" / "controls.json"


def garbage_after(mk, g, extra_back_min=0):
    """Copy of market where everything not allowed at decision time t=g*60min is replaced with random garbage.
    extra_back_min>0 makes the cut tighter (also destroys the last usable data) - used to prove the test is sensitive."""
    rng = np.random.default_rng(g)
    m = g * 60
    x = mk.copy()
    cut = m - 1 - extra_back_min                       # klines: open_time <= m-2 usable -> garbage from index m-1
    for name in ("open", "close", "vol", "tbv", "prem"):
        a = getattr(x, name)
        a[cut:] = rng.uniform(0.5, 2.0, len(a) - cut) * np.nanmedian(a[:cut])
    tcut = g * 3600.0 - 600.0 - extra_back_min * 60.0   # metrics / book: ts <= t-10min usable
    j = np.searchsorted(x.met_s, tcut, side="right")
    for name in ("oi_val", "top_ratio", "glob_ratio"):
        a = getattr(x, name); a[j:] = rng.uniform(0.5, 2.0, len(a) - j) * np.nanmedian(a[:max(j, 1)])
    if x.book_s is not None:
        k = np.searchsorted(x.book_s, tcut, side="right")
        x.book_imb[k:] = rng.uniform(-1, 1, len(x.book_imb) - k)
    fj = np.searchsorted(x.fund_min, g * 60.0, side="right")
    x.fund_rate[fj:] = rng.uniform(-0.01, 0.01, len(x.fund_rate) - fj)
    return x


def lookahead_test(mk, n_samples=40, seed=7):
    rng = np.random.default_rng(seed)
    base = Pipeline(mk)
    # sample from the whole span (needs history for z) with extra weight on 2023 so bookDepth is exercised
    gs = np.concatenate([rng.integers(900, NGRID - 100, n_samples // 2), rng.integers(26500, NGRID - 100, n_samples - n_samples // 2)])
    bad, sens_hit, sens_tot, checked = [], 0, 0, 0
    for g in gs:
        lo = g - 800
        idx = np.arange(lo, g + 1)
        for tight, store in ((0, "ok"), (1, "sens")):
            x = garbage_after(mk, int(g), extra_back_min=0 if tight == 0 else 15)
            f = Features(x).all(idx)
            if tight == 0:
                for k, v in f.items():
                    ref = base.feats[k][g]
                    a = v[-1]
                    checked += 1
                    if not ((np.isnan(a) and np.isnan(ref)) or a == ref):
                        bad.append((int(g), k, "feature", float(a), float(ref)))
                    zi = zscore(v)[-1]; zr = base.z[k][g]
                    if not ((np.isnan(zi) and np.isnan(zr)) or abs(zi - zr) <= 1e-9 * max(1.0, abs(zr))):
                        bad.append((int(g), k, "z", float(zi), float(zr)))
            else:   # tighter cut must change features that were available (proves garbage is really read if used)
                for k, v in f.items():
                    ref = base.feats[k][g]
                    if np.isnan(ref) or k == "F3":
                        continue
                    sens_tot += 1
                    if v[-1] != ref:
                        sens_hit += 1
    return {"n_points": int(len(gs)), "feature_checks": checked, "mismatches": bad[:10], "n_mismatches": len(bad),
            "sensitivity_changed_when_cut_tightened": f"{sens_hit}/{sens_tot}", "pass": len(bad) == 0 and sens_hit / max(sens_tot, 1) > 0.9}


def positive_control(pipe):
    mk = pipe.mk
    g = np.arange(NGRID)
    e, x = g * 60 + 1, g * 60 + 61
    ok = x < NMIN
    cheat = np.full(NGRID, np.nan)
    cheat[ok] = np.log(mk.open[x[ok]] / mk.open[e[ok]])      # FUTURE 1h return (deliberate lookahead)
    d = z_direction(zscore(cheat), +1)
    ep = run_episodes(mk, d, 60)
    return {"n": int(len(ep["gross"])), "mean_gross_bps": float(ep["gross"].mean()), "mean_net12_bps": float(net(ep).mean()),
            "pass": bool(ep["gross"].mean() > 50)}


def negative_controls(pipe, n_seeds=20):
    mk = pipe.mk
    res = {}
    # (a) iid noise feature through the same z / threshold / non-overlap pipeline
    for hn, H in (("1h", 60), ("4h", 240), ("24h", 1440)):
        gr, fu, nn = [], [], []
        for s in range(n_seeds):
            x = np.random.default_rng(100 + s).normal(size=NGRID)
            ep = run_episodes(mk, z_direction(zscore(x), +1), H)
            gr.append(ep["gross"]); fu.append(ep["fund"]); nn.append(len(ep["gross"]))
        gr, fu = np.concatenate(gr), np.concatenate(fu)
        res[f"noise_H{hn}"] = {"n_total": int(len(gr)), "mean_gross": float(gr.mean()), "se_gross": float(gr.std(ddof=1) / np.sqrt(len(gr))),
                               "mean_funding": float(fu.mean()), "mean_net12": float((gr + fu - 12).mean()),
                               "expected_net_if_gross_zero": float(fu.mean() - 12)}
    # (b) real F1_L1h_H1h firing times, random directions
    d0 = z_direction(pipe.z["F1_1h"], +1)
    gr, fu = [], []
    for s in range(n_seeds):
        rng = np.random.default_rng(500 + s)
        d = np.where(d0 != 0, rng.choice([-1, 1], size=len(d0)), 0).astype(np.int8)
        ep = run_episodes(mk, d, 60); gr.append(ep["gross"]); fu.append(ep["fund"])
    gr, fu = np.concatenate(gr), np.concatenate(fu)
    res["random_sign_at_F1_1h_fire_times_H1h"] = {"n_total": int(len(gr)), "mean_gross": float(gr.mean()),
                                                  "se_gross": float(gr.std(ddof=1) / np.sqrt(len(gr))), "mean_funding": float(fu.mean()),
                                                  "mean_net12": float((gr + fu - 12).mean())}
    res["firing_rate_F1_1h_real"] = float((d0 != 0).mean())
    res["firing_rate_noise"] = float((z_direction(zscore(np.random.default_rng(1).normal(size=NGRID)), 1) != 0).mean())
    res["pass"] = all(abs(v["mean_gross"]) < 3 * v["se_gross"] + 1e-9 and abs(v["mean_net12"] - (v.get("mean_funding", 0) - 12)) < 3 * v["se_gross"] + 1e-6
                      for k, v in res.items() if isinstance(v, dict))
    return res


def main():
    out = {}
    out["hypothesis_count"] = len(build_registry()); out["hypothesis_count_pass"] = out["hypothesis_count"] == 139
    for sym in ("BTCUSDT", "ETHUSDT"):
        mk = load_market(sym)
        out[f"lookahead_{sym}"] = lookahead_test(mk, 40)
        print(sym, out[f"lookahead_{sym}"], flush=True)
        if sym == "BTCUSDT":
            pipe = Pipeline(mk)
            out["positive_control"] = positive_control(pipe)
            out["negative_controls"] = negative_controls(pipe)
            print(out["positive_control"], json.dumps(out["negative_controls"], indent=1), flush=True)
    out["all_pass"] = bool(out["hypothesis_count_pass"] and out["lookahead_BTCUSDT"]["pass"] and out["lookahead_ETHUSDT"]["pass"]
                           and out["positive_control"]["pass"] and out["negative_controls"]["pass"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print("ALL PASS" if out["all_pass"] else "FAILURES", flush=True)
    sys.exit(0 if out["all_pass"] else 1)


if __name__ == "__main__":
    main()
