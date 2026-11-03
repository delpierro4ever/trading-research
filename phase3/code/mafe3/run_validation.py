"""MAFE-3 one-time VALIDATION run (entries 2020-01-01 .. 2023-01-01, exit < 2023-01-01). Reuses the discovery code unchanged
(window via env vars read by mafe3.market). Usage (from phase3/code): python -m mafe3.run_validation
Never touches data >= 2023-01-01 (loader refuses; MAFE3_UNSEAL is not used and the token file is never read)."""
from __future__ import annotations
import os
os.environ["MAFE3_WIN_START"] = "2019-11-01"      # warm-up (z-scores, rolling windows) from late 2019 only
os.environ["MAFE3_WIN_END"] = "2023-01-01"        # exclusive end: nothing at/after the sealed holdout is loaded
os.environ["MAFE3_PART_START"] = "2020-01-01"     # first measured day
assert "MAFE3_UNSEAL" not in os.environ
import hashlib, json, subprocess, time
from pathlib import Path
import numpy as np
import polars as pl
from .market import Market, O, L, D0
from .engine import run, flip, net, summarize, forward_drift, episode_calendar
from .signals import Signals, registry
from . import checks

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs" / "PREREGISTRATION.md"
PREREG_SHA = "5f503bf8636151b0e837d21586c018e21012a62be80d55c881fdb4643e40a234"
DISC = ROOT / "results" / "discovery"
OUT = ROOT / "results" / "validation"
YEARS = [2020, 2021, 2022]
K = 10                                   # registered cap on advancement
ALPHA_STRICT, ALPHA_LENIENT = 0.05 / K, 0.05 / 1


def sha256(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    t0 = time.time()
    assert sha256(PREREG) == PREREG_SHA, "pre-registration hash mismatch"
    adv = json.loads((DISC / "advancement.json").read_text())
    ids = adv["advanced_ids"]
    disc = pl.read_csv(DISC / "hypotheses.csv", infer_schema_length=None)
    OUT.mkdir(parents=True, exist_ok=True)
    M = Market.from_loader("2019-11-01", "2023-01-01")
    S = Signals(M)
    print(f"[{time.time()-t0:.0f}s] market: gold bars {int(M.has.sum())}; grid {len(S.grid)}", flush=True)
    ctrl = {"count": checks.count_check(), "positive_control": checks.positive_control(M, S), "negative_control": checks.negative_control(M, S)}
    grid = S.grid
    drift_cache = {}
    def drift(H):
        if H not in drift_cache: drift_cache[H] = forward_drift(M, grid, H * 60)
        return drift_cache[H]

    reg = {h.id: h for h in registry()}
    rows, verdicts = [], {}
    for hid in ids:
        h = reg[hid]
        c = S.cands(h)
        row = {"id": h.id, "family": h.family, "d_registered": h.d, "L_h": h.L, "H_h": h.H}
        if h.kind in ("hod", "dow"):
            sg = int(disc.filter(pl.col("id") == hid)["g2_direction"][0])      # discovery direction, NOT re-estimated
            assert sg in (1, -1)
            ep = run(M, c.with_d(np.ones(len(c), np.int8)))
            ep = ep if sg == 1 else flip(ep); row["g2_direction"] = sg
        else:
            ep = run(M, c); row["g2_direction"] = 0
        assert len(ep["e"]) == 0 or (ep["e"].min() >= D0 and ep["x"].max() < L)
        s = summarize(ep, M, {}, years=YEARS)
        row.update(s)
        n = s["n"]
        gr = ep["gross"]
        row["mean_net_c20_noswap"] = float((gr - ep["c20"]).mean()); row["mean_net_c60_noswap"] = float((gr - ep["c60"]).mean())
        row["mean_net_c35_noswap"] = s["mean_net_noswap"]
        for y in YEARS:
            mk = episode_calendar(ep["e"])[0] == y
            row[f"gross_{y}"] = float(gr[mk].mean()) if mk.any() else float("nan")
        hnom = int(max(1, round(s["median_hold_h"])))
        _, qt, _ = episode_calendar(ep["e"])
        for tag, H in (("hmatch", hnom), ("24h", 24)):
            dq = drift(H)
            dv = np.array([dq.get(q, np.nan) for q in qt]) * ep["d"]
            row[f"drift_{tag}"] = float(np.nanmean(dv)); row[f"gross_minus_drift_{tag}"] = float(gr.mean() - np.nanmean(dv))
        row["H_nominal_h"] = hnom
        mg = s["mean_gross"]; biased = s["share_one_side"] >= 0.70
        same = lambda v: bool(np.sign(v) == np.sign(mg) and mg != 0)
        g4 = same(row["gross_minus_drift_hmatch"]) and same(row["gross_minus_drift_24h"])
        gate_drift = bool(g4) if biased else True
        npos = sum(1 for y in YEARS if s[f"n_{y}"] > 0 and s[f"net_{y}"] > 0)
        p = s["p_net_1s"]
        gate_p_strict, gate_p_lenient = bool(s["mean_net"] > 0 and p < ALPHA_STRICT), bool(s["mean_net"] > 0 and p < ALPHA_LENIENT)
        gate_years = npos >= 2
        row.update(directionally_biased=bool(biased), gate4_drift=gate_drift, gate_p_strict=gate_p_strict, gate_years=gate_years,
                   years_positive=npos, validation_pass=bool(gate_p_strict and gate_years and gate_drift),
                   lenient_pass_nonbinding=bool(gate_p_lenient and gate_years and gate_drift))
        rows.append(row)
        verdicts[hid] = {
            "PASS": row["validation_pass"], "binding_rule": f"one-sided p < 0.05/K = {ALPHA_STRICT} (K=10 registered cap) AND >=2 of 3 years net>0 AND drift gate (4)",
            "n": n, "mean_gross_bps": mg, "mean_cost_bps": s["mean_cost"], "mean_swap_bps": s["mean_swap"], "mean_net_bps": s["mean_net"],
            "mean_net_c20_noswap": row["mean_net_c20_noswap"], "mean_net_c35_noswap": row["mean_net_c35_noswap"], "mean_net_c60_noswap": row["mean_net_c60_noswap"],
            "t_net": s["t_net"], "p_net_1s": p, "p_boot_weekly_block": s["p_boot"],
            "per_year": {str(y): {"n": s[f"n_{y}"], "gross": row[f"gross_{y}"], "net": s[f"net_{y}"]} for y in YEARS}, "years_positive": npos,
            "drift_hmatch": row["drift_hmatch"], "drift_24h": row["drift_24h"], "gross_minus_drift_hmatch": row["gross_minus_drift_hmatch"],
            "gross_minus_drift_24h": row["gross_minus_drift_24h"], "directionally_biased": bool(biased), "gate_p_strict": gate_p_strict,
            "gate_years": gate_years, "gate_drift": gate_drift,
            "lenient_K1_NONBINDING": {"threshold": ALPHA_LENIENT, "p_gate": gate_p_lenient, "would_pass": row["lenient_pass_nonbinding"]}}
    pl.DataFrame(rows, infer_schema_length=None).write_csv(OUT / "hypotheses.csv")
    code = sorted((ROOT / "code" / "mafe3").glob("*.py"))
    parent = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    v = {"preregistration_sha256": sha256(PREREG), "prereg_expected_sha256": PREREG_SHA, "git_parent_commit": parent,
         "code_sha256": {p.name: sha256(p) for p in code}, "window": "entries [2020-01-01, 2023-01-01), exit < 2023-01-01; warm-up from 2019-11-01",
         "K": K, "advanced_ids": ids, "overall_PASS": [i for i, x in verdicts.items() if x["PASS"]], "verdicts": verdicts,
         "controls": {k: x["pass"] for k, x in ctrl.items()}, "runtime_seconds": round(time.time() - t0, 1)}
    (OUT / "verdict.json").write_text(json.dumps(v, indent=2, default=str))
    print(json.dumps(v, indent=2, default=str))


if __name__ == "__main__":
    main()
