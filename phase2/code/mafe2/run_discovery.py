"""MAFE-2 discovery run (2020-2023). Usage: python -m mafe2.run_discovery  (from phase2/code)."""
from __future__ import annotations
import hashlib, json, subprocess, sys, time
from pathlib import Path
import numpy as np
import polars as pl
from .features import load_market, NGRID, T0
from .engine import build_registry, net
from .pipeline import Pipeline
from .stats import grid_calendar, summarize, bh

ROOT = Path(__file__).resolve().parents[2]            # phase2/
PREREG = ROOT / "docs" / "PREREGISTRATION.md"
PREREG_SHA = "85f65b98645554055a0a435d7cd4e6f8f68405c18efc52fc84299f213c5a18a2"
OUT = ROOT / "results" / "discovery"
EPI = Path("/home/ubuntu/mafe-data/episodes/discovery")
K_MAX = 10


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save_episodes(hid, sym, ep, net12, net8):
    d = EPI / sym
    d.mkdir(parents=True, exist_ok=True)
    g = ep["g"]
    entry = (np.datetime64("2020-01-01T00:00:00", "ms") + (g * 60 + 1).astype("timedelta64[m]").astype("timedelta64[ms]"))
    exit_ = entry + np.timedelta64(int(ep["H"]), "m")
    pl.DataFrame({"hyp": [hid] * len(g), "symbol": [sym] * len(g), "grid_idx": g, "entry_time": entry, "exit_time": exit_,
                  "direction": ep["d"], "gross_bps": ep["gross"], "funding_bps": ep["fund"], "net12_bps": net12, "net8_bps": net8}
                 ).write_parquet(d / f"{hid}.parquet")


def main():
    t_start = time.time()
    assert sha256(PREREG) == PREREG_SHA, "pre-registration hash mismatch"
    OUT.mkdir(parents=True, exist_ok=True)
    hyps = build_registry()
    assert len(hyps) == 139, len(hyps)
    cal = grid_calendar(NGRID)

    pipes = {}
    for sym in ("BTCUSDT", "ETHUSDT"):
        print(f"[{time.time()-t_start:.0f}s] loading {sym}", flush=True)
        pipes[sym] = Pipeline(load_market(sym))
        print(f"[{time.time()-t_start:.0f}s] features {sym} done", flush=True)

    rows = []
    for i, h in enumerate(hyps):
        row = {"id": h.id, "family": h.family, "feature": h.feat or ("hour_of_day" if h.kind == "hod" else "day_of_week"),
               "d": h.d, "H_min": h.H, "f7_param": h.param}
        epb, sgn = pipes["BTCUSDT"].episodes(h)
        epe, _ = pipes["ETHUSDT"].episodes(h, f7_sign=sgn)
        row["f7_direction"] = float(sgn) if sgn is not None else float("nan")
        for sym, ep in (("BTCUSDT", epb), ("ETHUSDT", epe)):
            save_episodes(h.id, sym, ep, net(ep, 12.0), net(ep, 8.0))
        s = summarize(epb["gross"], epb["fund"], epb["g"], cal)
        row.update(s)
        n_e = len(epe["gross"])
        row["eth_n"] = n_e
        row["eth_mean_gross"] = float(epe["gross"].mean()) if n_e else np.nan
        row["eth_mean_net12"] = float((epe["gross"] + epe["fund"] - 12).mean()) if n_e else np.nan
        rows.append(row)
        if i % 20 == 0:
            print(f"[{time.time()-t_start:.0f}s] hyp {i}/139 {h.id} n={s['n']}", flush=True)

    df = pl.DataFrame(rows, infer_schema_length=None)
    p1 = df["p_net12_1s"].to_numpy()
    pg = df["p_gross_2s"].to_numpy()
    mean_net = df["mean_net12"].to_numpy()
    bh_net = bh(p1, 0.10) & (np.nan_to_num(mean_net, nan=-1) > 0)
    bh_gross = bh(pg, 0.05)

    # ---- gates
    fam = df["family"].to_list()
    gate_n = df["n"].to_numpy() >= 100
    gate_years = np.zeros(len(df), bool)
    years_desc = []
    for i in range(len(df)):
        if fam[i] == "F8":
            qs = [df[f"net12_2023Q{q}"][i] for q in (1, 2, 3, 4)]
            pos = sum(1 for v in qs if v is not None and not np.isnan(v) and v > 0)
            gate_years[i] = pos >= 0.75 * 4
            years_desc.append(f"{pos}/4 quarters of 2023")
        else:
            ys = [2021, 2022, 2023]
            if fam[i] in ("F5", "F6"):
                if df["n_2020"][i] >= 100:
                    ys = [2020] + ys
            else:
                ys = [2020] + ys
            pos = sum(1 for y in ys if df[f"n_{y}"][i] > 0 and df[f"net12_{y}"][i] > 0)
            need = 3
            gate_years[i] = pos >= need
            years_desc.append(f"{pos}/{len(ys)} years (need {need})")
    mg = df["mean_gross"].to_numpy(); eg = df["eth_mean_gross"].to_numpy()
    gate_eth = (np.sign(mg) == np.sign(eg)) & (np.nan_to_num(mg) != 0)

    tstat = df["t_net12"].to_numpy()
    if bh_net.any():
        cand = bh_net.copy(); mode = "BH"
    else:
        order = [int(i) for i in np.argsort(-np.nan_to_num(tstat, nan=-1e9)) if np.nan_to_num(mean_net[i], nan=-1) > 0][:5]
        cand = np.zeros(len(df), bool); cand[order] = True; mode = "NEAR_MISS"
    passing = cand & gate_n & gate_years & gate_eth
    ranked = [int(i) for i in np.argsort(-np.nan_to_num(tstat, nan=-1e9)) if passing[i]]
    adv = ranked[:K_MAX]
    label = [""] * len(df)
    for i in adv:
        label[i] = "BH" if mode == "BH" else "NEAR_MISS"
    df = df.with_columns(
        pl.Series("bh_net12_q10", bh_net), pl.Series("bh_gross_q05", bh_gross),
        pl.Series("near_miss_candidate", cand if mode == "NEAR_MISS" else np.zeros(len(df), bool)),
        pl.Series("gate1_candidate", cand), pl.Series("gate2_n100", gate_n), pl.Series("gate3_years", gate_years),
        pl.Series("gate3_detail", years_desc), pl.Series("gate4_eth_sign", gate_eth),
        pl.Series("advanced", [bool(x) for x in (np.array(label) != "")]), pl.Series("label", label))
    df.write_csv(OUT / "hypotheses.csv")

    code_files = sorted((ROOT / "code" / "mafe2").glob("*.py")) + sorted((ROOT / "code" / "tests").glob("*.py"))
    try:
        parent = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except Exception:
        parent = ""
    adv_json = {
        "preregistration_sha256": sha256(PREREG), "prereg_expected_sha256": PREREG_SHA,
        "git_parent_commit_of_code": parent, "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in code_files},
        "gate1_mode": mode, "n_bh_net12_q10": int(bh_net.sum()), "n_bh_gross_q05": int(bh_gross.sum()),
        "n_gate1_candidates": int(cand.sum()), "n_pass_gates_2_4": int(passing.sum()), "K": K_MAX,
        "advanced": [{"id": df["id"][i], "label": label[i], "n": int(df["n"][i]), "mean_net12": float(df["mean_net12"][i]),
                      "t_net12": float(df["t_net12"][i]), "p_net12_1s": float(df["p_net12_1s"][i])} for i in adv],
        "advanced_ids": [df["id"][i] for i in adv],
        "runtime_seconds": round(time.time() - t_start, 1),
    }
    (OUT / "advancement.json").write_text(json.dumps(adv_json, indent=2))
    print(json.dumps(adv_json, indent=2))


if __name__ == "__main__":
    main()
