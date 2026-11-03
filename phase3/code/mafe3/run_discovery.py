"""MAFE-3 discovery run (2010-01-01 .. 2020-01-01), HistData 1-minute BID bars, Amendment 2. Usage (from phase3/code): python -m mafe3.run_discovery"""
from __future__ import annotations
import hashlib, json, subprocess, time
from pathlib import Path
import numpy as np
import polars as pl
import pandas as pd
from .market import Market, O, L, D0
from .engine import run, flip, net, summarize, forward_drift, episode_calendar, bh
from .signals import Signals, registry
from . import checks

ROOT = Path(__file__).resolve().parents[2]            # phase3/
PREREG = ROOT / "docs" / "PREREGISTRATION.md"
PREREG_SHA = "5f503bf8636151b0e837d21586c018e21012a62be80d55c881fdb4643e40a234"
import os
TEST = os.environ.get("MAFE3_TEST_OUT")        # synthetic-data smoke test only
OUT = Path(TEST) / "res" if TEST else ROOT / "results" / "discovery"
EPI = Path(TEST) / "epi" if TEST else Path("/home/ubuntu/mafe-data/episodes/mafe3/discovery")
K_MAX = 10
YEARS = list(range(2010, 2020))


def sha256(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()


def save_episodes(h, ep, M):
    EPI.mkdir(parents=True, exist_ok=True)
    ent = (ep["e"] + O).astype("datetime64[m]").astype("datetime64[ms]")
    ext = (ep["x"] + O).astype("datetime64[m]").astype("datetime64[ms]")
    pl.DataFrame({"hyp": [h.id] * len(ent), "entry_time": ent, "exit_time": ext, "direction": ep["d"].astype(np.int8),
                  "gross_bps": ep["gross"], "cost_bps": ep["cost"], "swap_bps": ep["swap"], "net_bps": net(ep),
                  "net_c20_bps": net(ep, "c20"), "net_c60_bps": net(ep, "c60"), "net_noswap_bps": net(ep, "noswap")}).write_parquet(EPI / f"{h.id}.parquet")


def main():
    t0 = time.time()
    assert sha256(PREREG) == PREREG_SHA, "pre-registration hash mismatch"
    OUT.mkdir(parents=True, exist_ok=True)
    M = Market.from_loader("2009-11-01", "2020-01-01")       # loader refuses anything >= 2023-01-01; we stop at 2020-01-01
    print(f"[{time.time()-t0:.0f}s] market loaded: gold bars {int(M.has.sum())}, eur bars {int(M.eur_has.sum())}", flush=True)
    S = Signals(M)
    print(f"[{time.time()-t0:.0f}s] signals built; grid points {len(S.grid)}", flush=True)

    # ---------------- controls
    ctrl = {"count": checks.count_check(), "swap": checks.swap_check(M), "weekend_rule": checks.weekend_rule_check(M),
            "positive_control": checks.positive_control(M, S), "negative_control": checks.negative_control(M, S)}
    print(f"[{time.time()-t0:.0f}s] controls (cheap) done", flush=True)
    ctrl["lookahead"] = checks.lookahead_test(M, S)
    (OUT / "controls.json").write_text(json.dumps(ctrl, indent=2, default=str))
    print(f"[{time.time()-t0:.0f}s] controls:", {k: v["pass"] for k, v in ctrl.items()}, flush=True)
    assert all(v["pass"] for v in ctrl.values()), "a self-check failed; see controls.json"

    hyps = registry()
    assert len(hyps) == 89
    grid = S.grid
    drift_cache = {}
    def drift(H):
        if H not in drift_cache: drift_cache[H] = forward_drift(M, grid, H * 60)
        return drift_cache[H]

    rows = []
    for i, h in enumerate(hyps):
        c = S.cands(h)
        row = {"id": h.id, "family": h.family, "d_registered": h.d, "L_h": h.L, "H_h": h.H}
        if h.kind in ("hod", "dow"):
            ep = run(M, c.with_d(np.ones(len(c), np.int8)))
            sg = 1 if (len(ep["gross"]) and ep["gross"].mean() >= 0) else -1
            ep = ep if sg == 1 else flip(ep)
            row["g2_direction"] = sg
        else:
            ep = run(M, c); row["g2_direction"] = 0
        save_episodes(h, ep, M)
        s = summarize(ep, M, {})
        row.update(s)
        # matched drift (gate 4): H-matched and literal 24h version
        n = s["n"]
        if n:
            hnom = int(max(1, round(s["median_hold_h"])))
            _, qt, _ = episode_calendar(ep["e"])
            for tag, H in (("hmatch", hnom), ("24h", 24)):
                dq = drift(H)
                dv = np.array([dq.get(q, np.nan) for q in qt]) * ep["d"]
                row[f"drift_{tag}"] = float(np.nanmean(dv)); row[f"gross_minus_drift_{tag}"] = float(ep["gross"].mean() - np.nanmean(dv))
            row["H_nominal_h"] = hnom
        rows.append(row)
        if i % 10 == 0: print(f"[{time.time()-t0:.0f}s] {i}/89 {h.id} n={n}", flush=True)

    df = pl.DataFrame(rows, infer_schema_length=None)
    p1 = df["p_net_1s"].to_numpy().copy()
    fam = np.array(df["family"].to_list())
    p_bh = p1.copy()
    g2 = fam == "G2"
    p_bh[g2] = np.minimum(1.0, 2 * p1[g2])               # G2: direction chosen in-sample -> two-sided accounting
    mean_net = df["mean_net"].to_numpy(); tnet = df["t_net"].to_numpy()
    pg = df["p_gross_2s"].to_numpy()
    bh_net = bh(p_bh, 0.10) & (np.nan_to_num(mean_net, nan=-1) > 0)
    bh_gross = bh(pg, 0.05)

    # ---------------- gates
    gate_n = df["n"].to_numpy() >= 100
    pos_years, gate_years = [], np.zeros(len(df), bool)
    for i in range(len(df)):
        pos = sum(1 for y in YEARS if df[f"n_{y}"][i] >= 10 and df[f"net_{y}"][i] > 0)
        cnt = sum(1 for y in YEARS if df[f"n_{y}"][i] >= 10)
        pos_years.append(f"{pos} positive of {cnt} eligible years"); gate_years[i] = pos >= 7
    share = df["share_one_side"].to_numpy(); mg = df["mean_gross"].to_numpy()
    biased = np.nan_to_num(share) >= 0.70
    def same_sign(col):
        v = df[col].to_numpy()
        return (np.sign(v) == np.sign(mg)) & (np.nan_to_num(mg) != 0)
    g4 = same_sign("gross_minus_drift_hmatch") & same_sign("gross_minus_drift_24h")
    gate_drift = np.where(biased, g4, True)

    if bh_net.any():
        cand, mode = bh_net.copy(), "BH"
    else:
        order = [int(i) for i in np.argsort(-np.nan_to_num(tnet, nan=-1e9)) if np.nan_to_num(mean_net[i], nan=-1) > 0][:5]
        cand = np.zeros(len(df), bool); cand[order] = True; mode = "NEAR_MISS"
    passing = cand & gate_n & gate_years & gate_drift
    ranked = [int(i) for i in np.argsort(-np.nan_to_num(tnet, nan=-1e9)) if passing[i]]
    adv = ranked[:K_MAX]
    label = [""] * len(df)
    for i in adv: label[i] = mode
    df = df.with_columns(pl.Series("p_for_bh", p_bh), pl.Series("bh_net_q10", bh_net), pl.Series("bh_gross_q05", bh_gross),
                         pl.Series("gate1_candidate", cand), pl.Series("gate2_n100", gate_n), pl.Series("gate3_years", gate_years),
                         pl.Series("gate3_detail", pos_years), pl.Series("directionally_biased", biased),
                         pl.Series("gate4_drift", gate_drift), pl.Series("advanced", [x != "" for x in label]),
                         pl.Series("label", label))
    df.write_csv(OUT / "hypotheses.csv")

    code = sorted((ROOT / "code" / "mafe3").glob("*.py"))
    parent = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    adv_json = {"preregistration_sha256": sha256(PREREG), "prereg_expected_sha256": PREREG_SHA, "git_parent_commit": parent,
                "code_sha256": {p.name: sha256(p) for p in code}, "gate1_mode": mode, "n_hypotheses": len(df),
                "n_bh_net_q10": int(bh_net.sum()), "n_bh_gross_q05": int(bh_gross.sum()), "n_gate1_candidates": int(cand.sum()),
                "n_pass_gates_2_4": int(passing.sum()), "K": K_MAX,
                "advanced": [{"id": df["id"][i], "label": label[i], "n": int(df["n"][i]), "mean_net": float(df["mean_net"][i]),
                              "t_net": float(df["t_net"][i]), "p_net_1s": float(df["p_net_1s"][i])} for i in adv],
                "advanced_ids": [df["id"][i] for i in adv], "runtime_seconds": round(time.time() - t0, 1)}
    (OUT / "advancement.json").write_text(json.dumps(adv_json, indent=2))
    print(json.dumps(adv_json, indent=2))


if __name__ == "__main__":
    main()
