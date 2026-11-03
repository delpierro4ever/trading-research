"""Self-checks for the MAFE3 discovery code: hypothesis count, lookahead, positive/negative controls, swap accounting."""
from __future__ import annotations
import numpy as np
from collections import Counter
from .market import Market, O, L, D0, epoch_min, NY, abs_min
from .engine import Cands, run, resolve, summarize, net
from .signals import Signals, registry, Hyp


def count_check():
    hs = registry()
    ids = [h.id for h in hs]
    fam = Counter(h.family for h in hs)
    exp = {"G1": 18, "G2": 29, "G3": 6, "G4": 4, "G5": 2, "G6": 6, "G7": 18, "G8": 6}
    return {"n_hypotheses": len(hs), "unique_ids": len(set(ids)), "by_family": dict(fam), "expected_by_family": exp,
            "pass": len(hs) == 89 and len(set(ids)) == 89 and dict(fam) == exp}


def lookahead_test(M: Market, S: Signals, n_cut=5, seed=11):
    """Replace every bar value with label > t*-2 (bars whose close is after t*-1 min) by garbage; every feature/signal at decision times <= t*
    must be identical. Sensitivity: cutting one bar earlier (label > t*-3) must change the features at t*."""
    rng = np.random.default_rng(seed)
    g = S.grid
    cand_t = g[(g > D0 + 1440 * 400) & (g < L - 6000)]
    stars = rng.choice(cand_t, n_cut, replace=False)
    hs = [h for h in registry() if h.family != "G2"]
    base = {h.id: S.cands(h) for h in hs}
    out = {"cutoffs_checked": [], "mismatches": [], "sensitivity_changed": 0, "sensitivity_total": 0}
    for ts in stars:
        ts = int(ts)
        Mc = M.corrupt_after(ts - 2, seed=ts)
        Sc = Signals(Mc)
        pos = int(np.searchsorted(g, ts))
        assert g[pos] == ts and np.array_equal(Sc.grid[: pos + 1], g[: pos + 1])
        for nm in ("x_gold", "x_eur", "z_gold", "z_eur"):
            for Lm in (1, 4, 24):
                a, b = getattr(S, nm)[Lm][: pos + 1], getattr(Sc, nm)[Lm][: pos + 1]
                if not np.array_equal(a, b, equal_nan=True): out["mismatches"].append((ts, nm, Lm))
        if not np.array_equal(S.g6[: pos + 1], Sc.g6[: pos + 1]): out["mismatches"].append((ts, "g6"))
        for h in hs:
            a, b = base[h.id], Sc.cands(h)
            ma, mb = a.t <= ts, b.t <= ts
            if not (np.array_equal(a.t[ma], b.t[mb]) and np.array_equal(a.d[ma], b.d[mb])): out["mismatches"].append((ts, h.id))
        del Mc, Sc
        # sensitivity: one more bar of garbage must change something at ts
        Mt = M.corrupt_after(ts - 3, seed=ts)
        St = Signals(Mt)
        ch = sum(not np.array_equal(S.x_gold[Lm][pos:pos + 1], St.x_gold[Lm][pos:pos + 1], equal_nan=True) for Lm in (1, 4, 24))
        ch += sum(not np.array_equal(S.x_eur[Lm][pos:pos + 1], St.x_eur[Lm][pos:pos + 1], equal_nan=True) for Lm in (1, 4, 24))
        out["sensitivity_changed"] += ch; out["sensitivity_total"] += 6
        del Mt, St
        out["cutoffs_checked"].append(int((ts + O) * 60))
    out["pass"] = (len(out["mismatches"]) == 0) and out["sensitivity_changed"] >= 0.8 * out["sensitivity_total"]
    return out


def positive_control(M: Market, S: Signals):
    """Feature = the realised future 1h return from entry (t) to exit (t+1): must show a huge gross."""
    t = S.grid
    e, x, ok = resolve(M, t + 1, np.full(len(t), -1), hold=np.full(len(t), 60))
    fut = np.where(ok, np.log(M.o[np.clip(x, 0, L - 1)] / M.o[np.clip(e, 0, L - 1)]), 0.0)
    c = Cands(t, t + 1, None, np.sign(fut).astype(np.int8), hold=60)
    ep = run(M, c)
    s = summarize(ep, M, {}, boot=False)
    mabs = float(np.abs(fut[ok]).mean() * 1e4)
    return {"n": s["n"], "mean_gross_bps": s["mean_gross"], "mean_abs_1h_return_bps": mabs, "mean_net_bps": s["mean_net"], "t_gross": s["t_gross"],
            "pass": bool(s["mean_gross"] > 0.5 * mabs and s["t_gross"] > 20)}


def negative_control(M: Market, S: Signals, n_seeds=20):
    t = S.grid
    res = []
    for seed in range(n_seeds):
        rng = np.random.default_rng(1000 + seed)
        d = np.where(rng.random(len(t)) < 0.2, rng.choice([-1, 1], len(t)), 0).astype(np.int8)
        ep = run(M, Cands(t, t + 1, None, d, hold=60))
        s = summarize(ep, M, {}, boot=False)
        res.append((s["n"], s["mean_gross"], s["t_gross"], s["mean_cost"], s["mean_swap"], s["mean_net"]))
    r = np.array(res)
    dev = r[:, 5] - (-r[:, 3] - r[:, 4])         # mean_net - (-cost - swap) == mean_gross exactly
    return {"seeds": n_seeds, "mean_n": float(r[:, 0].mean()), "mean_gross_bps_avg": float(r[:, 1].mean()),
            "t_gross_per_seed": [round(float(v), 2) for v in r[:, 2]], "frac_abs_t_gt_1.96": float((np.abs(r[:, 2]) > 1.96).mean()),
            "mean_cost_bps": float(r[:, 3].mean()), "mean_swap_bps": float(r[:, 4].mean()), "mean_net_bps_avg": float(r[:, 5].mean()),
            "max_abs_dev_net_vs_minus_cost_swap": float(np.abs(dev).max()),
            "pass": bool(np.abs(r[:, 2]).max() < 3.5 and abs(r[:, 1].mean()) < 0.3 and abs(r[:, 5].mean() + r[:, 3].mean() + r[:, 4].mean()) < 0.3)}


def swap_check(M: Market):
    """Vectorised swap vs brute force on random holds, and an explicit Tue->Thu case."""
    rng = np.random.default_rng(5)
    e = np.sort(rng.integers(D0, L - 6000, 300)); x = e + rng.integers(1, 3000, 300)
    fast = M.swap_bps(e, x)
    slow = np.array([2.0 * sum(w for r, w in zip(M.R, M.W) if abs_min(a) < r <= abs_min(b)) for a, b in zip(e, x)])
    # explicit: Tue 2015-03-03 12:00 UTC -> Thu 2015-03-05 12:00 UTC crosses Tue(1), Wed(3) rollovers = 4 -> 8 bps
    a = epoch_min(2015, 3, 3, 12) - O
    ex = float(M.swap_bps(np.array([a]), np.array([a + 2880]))[0])
    return {"vectorised_equals_bruteforce": bool(np.allclose(fast, slow)), "tue_to_thu_swap_bps": ex, "pass": bool(np.allclose(fast, slow) and ex == 8.0)}


def weekend_rule_check(M: Market):
    """Synthetic availability: Fri 20:30 entry with 1h hold must be rejected (exit after the 21:00 close); Fri 19:00 and Mon 10:00 1h holds accepted."""
    def idx(y, m, d, hh, mm=0): return epoch_min(y, m, d, hh, mm) - O
    f2030, f19, mon = idx(2015, 3, 6, 20, 30), idx(2015, 3, 6, 19), idx(2015, 3, 9, 10)
    has0 = M.has; nxt0 = M.nxt
    try:                                  # make every minute of these probes "available" so only the weekend rule can reject
        M.has = np.ones(L, bool); M.nxt = np.arange(L, dtype=np.int64)
        r = {}
        for nm, a in (("fri_2030_1h", f2030), ("fri_1900_1h", f19), ("mon_1000_1h", mon)):
            _, _, ok = resolve(M, np.array([a]), np.array([-1]), hold=np.array([60])); r[nm] = bool(ok[0])
        _, _, okw = resolve(M, np.array([f2030]), np.array([f2030 + 600]), waive=np.array([True])); r["waived_ok"] = bool(okw[0])
    finally:
        M.has, M.nxt = has0, nxt0
    r["pass"] = (not r["fri_2030_1h"]) and r["fri_1900_1h"] and r["mon_1000_1h"] and r["waived_ok"]
    return r
