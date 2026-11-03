"""MAFE-2 validation run (2024), one read. Usage (from phase2/code):
   python -m mafe2.run_validation repro   # discovery reproduction check (writes to a temp dir only)
   python -m mafe2.run_validation run     # descriptive stage-2 discovery stats, then the 2024 validation read
Reuses discovery features/engine/stats unchanged. The shared modules hard-code the discovery time base (NMIN/NGRID);
for the validation read these module globals are re-bound (not edited) so the same arrays/indices extend to 2025-01-01
(T0 stays 2020-01-01, so grid indices and causal z-scores are identical to what discovery code would give).
Data is requested only with end <= 2025-01-01; the holdout guard is never touched."""
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile, time, shutil
from pathlib import Path
import numpy as np
import polars as pl
from . import data, features, engine, pipeline, run_discovery
from .features import Market, to_min, _kline_arrays
from .engine import build_registry, z_direction, run_episodes, net
from .stats import grid_calendar, summarize

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs" / "PREREGISTRATION.md"
PREREG_SHA = "355c93a3184f03de55b652c44004acba9630781ffcd75f4ad572ded0e0413055"
OUT = ROOT / "results" / "validation"
EPI = Path("/home/ubuntu/mafe-data/episodes/validation")
K = 6
ALPHA = 0.05 / K
SYMS = ("BTCUSDT", "ETHUSDT")
G_2024 = (366 + 365 + 365 + 365) * 24
G_2025 = G_2024 + 366 * 24
NMIN_D, NGRID_D = features.NMIN, features.NGRID       # discovery time base (2020-2023)
NMIN_V, NGRID_V = G_2025 * 60, G_2025
STAGE1 = ["F4_L4h_H24h_R", "F6_glob_H24h_R", "F4_L1h_H24h_R"]
STAGE2 = {"S2_LONG_F4_L4h": "F4_L4h_H24h_R", "S2_LONG_F6_glob": "F6_glob_H24h_R", "S2_LONG_F4_L1h": "F4_L1h_H24h_R"}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def set_timebase(nmin: int, ngrid: int):
    features.NMIN = nmin; features.NGRID = ngrid
    engine.NMIN = nmin; engine.NGRID = ngrid
    pipeline.NGRID = ngrid


def load_market_validation(symbol: str) -> Market:
    """Same loading as features.load_market but 2020-01-01 .. 2025-01-01 (exclusive) and no bookDepth (F8 not used)."""
    s, e = "2020-01-01", "2025-01-01"
    k = data.load("klines_1m", symbol, s, e, ["open", "close", "volume", "taker_buy_volume"])
    ka = _kline_arrays(k, ["open", "close", "volume", "taker_buy_volume"])
    p = data.load("premiumIndexKlines_1m", symbol, s, e, ["close"])
    pa = _kline_arrays(p, ["close"])
    f = data.load("fundingRate", symbol, s, e, ["last_funding_rate"])
    m = data.load("metrics", symbol, s, e, ["sum_open_interest_value", "count_toptrader_long_short_ratio", "count_long_short_ratio"])
    return Market(symbol, open=ka["open"], close=ka["close"], vol=ka["volume"], tbv=ka["taker_buy_volume"], prem=pa["close"],
                  fund_min=to_min(f["calc_time"].to_numpy()), fund_rate=f["last_funding_rate"].to_numpy().astype(float),
                  met_s=to_min(m["create_time"].to_numpy()) * 60.0,
                  oi_val=m["sum_open_interest_value"].to_numpy().astype(float),
                  top_ratio=m["count_toptrader_long_short_ratio"].to_numpy().astype(float),
                  glob_ratio=m["count_long_short_ratio"].to_numpy().astype(float))


def drift_benchmark(mk, g_lo: int, g_hi: int, H: int = 1440) -> dict:
    """Mean 24h gross (bps) of a long entered at every grid hour g in [g_lo, g_hi) (entry open t+1min, exit open entry+H;
    exit must be inside the loaded period). Overlapping by construction; reported for context only."""
    g = np.arange(g_lo, g_hi)
    e = g * 60 + 1; x = e + H
    ok = x < len(mk.open)
    e, x = e[ok], x[ok]
    pe, px = mk.open[e], mk.open[x]
    v = (pe > 0) & (px > 0)
    r = np.log(px[v] / pe[v]) * 1e4
    return {"n_grid_points": int(v.sum()), "mean_gross_bps_long": float(r.mean()), "std_bps": float(r.std(ddof=1))}


def episodes_for(pipe, h, long_only: bool, g_lo: int, g_hi: int):
    d = z_direction(pipe.z[h.feat], h.d, 0)
    d[:g_lo] = 0
    d[g_hi:] = 0
    if long_only:
        d[d < 0] = 0
    return run_episodes(pipe.mk, d, h.H)


def quarter_table(ep, cal, year):
    yr, qt, wk = cal
    n12 = net(ep, 12.0); g = ep["g"]
    out = {}
    for q in (1, 2, 3, 4):
        mk = qt[g] == year * 10 + q if len(g) else np.zeros(0, bool)
        out[f"n_{year}Q{q}"] = int(mk.sum()); out[f"net12_{year}Q{q}"] = float(n12[mk].mean()) if mk.any() else float("nan")
    return out


def stats_row(ep, cal):
    s = summarize(ep["gross"], ep["fund"], ep["g"], cal)
    return {k: v for k, v in s.items() if not (k.startswith("n_20") or k.startswith("net12_20"))}


def split_stats(ep):
    out = {}
    n12 = net(ep, 12.0)
    for nm, dd in (("long", 1), ("short", -1)):
        m = ep["d"] == dd
        out[f"n_{nm}"] = int(m.sum())
        out[f"mean_gross_{nm}"] = float(ep["gross"][m].mean()) if m.any() else float("nan")
        out[f"mean_net12_{nm}"] = float(n12[m].mean()) if m.any() else float("nan")
    return out


def repro():
    """Re-run the unchanged discovery pipeline into a temp dir and compare hypotheses.csv with the committed one.
    run_discovery pins the original pre-registration hash (85f65b...), which no longer matches the amended file, so the pin is
    re-bound to the current hash for this check only (the discovery code is otherwise untouched)."""
    tmp = Path(tempfile.mkdtemp(prefix="mafe2_repro_"))
    run_discovery.PREREG_SHA = sha256(PREREG)
    run_discovery.OUT = tmp / "out"; run_discovery.EPI = tmp / "epi"
    run_discovery.main()
    a = (tmp / "out" / "hypotheses.csv").read_bytes()
    b = (ROOT / "results" / "discovery" / "hypotheses.csv").read_bytes()
    same = a == b
    st1_equal = None
    if not same:
        da = pl.read_csv(tmp / "out" / "hypotheses.csv", infer_schema_length=None)
        db = pl.read_csv(ROOT / "results" / "discovery" / "hypotheses.csv", infer_schema_length=None)
        st1_equal = {i: bool(da.filter(pl.col("id") == i).equals(db.filter(pl.col("id") == i))) for i in STAGE1}
    res = {"hypotheses_csv_byte_identical": same, "stage1_rows_equal": st1_equal,
           "sha256_new": hashlib.sha256(a).hexdigest(), "sha256_committed": hashlib.sha256(b).hexdigest()}
    shutil.rmtree(tmp, ignore_errors=True)
    print("REPRO_RESULT", json.dumps(res))
    return res


def main():
    t0 = time.time()
    psha = sha256(PREREG)
    assert psha == PREREG_SHA, f"pre-registration hash mismatch {psha}"
    OUT.mkdir(parents=True, exist_ok=True)
    reg = {h.id: h for h in build_registry()}
    assert all(i in reg for i in STAGE1)

    # ---------- A. descriptive discovery stats for the stage-2 hypotheses (discovery data only, unpatched time base)
    cal_d = grid_calendar(NGRID_D)
    desc_rows, drift_disc = [], {}
    for sym in SYMS:
        pipe = pipeline.Pipeline(features.load_market(sym, books=False))
        drift_disc[sym] = drift_benchmark(pipe.mk, 0, NGRID_D)
        for sid, base in STAGE2.items():
            h = reg[base]
            d = z_direction(pipe.z[h.feat], h.d, pipe.g_start(h)); d[d < 0] = 0
            ep = run_episodes(pipe.mk, d, h.H)
            s = summarize(ep["gross"], ep["fund"], ep["g"], cal_d)
            desc_rows.append({"label": "DESCRIPTIVE_DISCOVERY_2020_2023", "id": sid, "symbol": sym, **s})
        del pipe
    pl.DataFrame(desc_rows, infer_schema_length=None).write_csv(OUT / "stage2_discovery_descriptive.csv")
    print(f"[{time.time()-t0:.0f}s] descriptive stage-2 discovery stats written", flush=True)

    # ---------- B. validation read
    set_timebase(NMIN_V, NGRID_V)
    cal = grid_calendar(NGRID_V)
    run_discovery.EPI = EPI
    pipes = {s: pipeline.Pipeline(load_market_validation(s)) for s in SYMS}
    for s in SYMS:
        assert len(pipes[s].mk.open) == NMIN_V
    drift_val = {s: drift_benchmark(pipes[s].mk, G_2024, G_2025) for s in SYMS}
    hyp_list = [(i, reg[i], False) for i in STAGE1] + [(sid, reg[b], True) for sid, b in STAGE2.items()]
    rows, verdict_h = [], {}
    for hid, h, lo in hyp_list:
        ep = {}
        for sym in SYMS:
            ep[sym] = episodes_for(pipes[sym], h, lo, G_2024, G_2025)
            run_discovery.save_episodes(hid, sym, ep[sym], net(ep[sym], 12.0), net(ep[sym], 8.0))
            assert ep[sym]["g"].min() >= G_2024 and (ep[sym]["g"] * 60 + 1 + h.H).max() < NMIN_V
        eb, ee = ep["BTCUSDT"], ep["ETHUSDT"]
        row = {"id": hid, "stage": 2 if lo else 1, "base_feature": h.feat, "d": h.d, "long_only": lo, "H_min": h.H}
        row.update(stats_row(eb, cal)); row.update(quarter_table(eb, cal, 2024)); row.update(split_stats(eb))
        se = stats_row(ee, cal)
        row.update({"eth_n": se["n"], "eth_mean_gross": se["mean_gross"], "eth_mean_net12": se["mean_net12"], "eth_t_net12": se["t_net12"],
                    "eth_p_net12_1s": se["p_net12_1s"], "eth_p_boot": se["p_boot"], "eth_hit_rate": se["hit_rate"]})
        row.update({f"eth_{k}": v for k, v in quarter_table(ee, cal, 2024).items()})
        row.update({f"eth_{k}": v for k, v in split_stats(ee).items()})
        c1 = bool(row["n"] > 0 and row["p_net12_1s"] < ALPHA)
        c2 = bool(row["n"] > 0 and row["mean_net12"] > 0)
        c3 = bool(row["mean_gross"] > 0 and row["eth_mean_gross"] > 0)
        reasons = [f"one-sided p {row['p_net12_1s']:.5f} {'<' if c1 else '>='} {ALPHA:.5f}",
                   f"mean net12 {row['mean_net12']:.2f} {'> 0' if c2 else '<= 0'}",
                   f"BTC mean gross {row['mean_gross']:.2f}, ETH mean gross {row['eth_mean_gross']:.2f}: " + ("same positive sign" if c3 else "sign condition not met")]
        row["gate_p"] = c1; row["gate_net_pos"] = c2; row["gate_eth_sign"] = c3
        row["verdict"] = "PASS" if (c1 and c2 and c3) else "FAIL"
        verdict_h[hid] = {"verdict": row["verdict"], "reasons": reasons, "n": row["n"], "mean_net12": row["mean_net12"],
                          "p_net12_1s": row["p_net12_1s"], "eth_mean_gross": row["eth_mean_gross"]}
        rows.append(row)
    pl.DataFrame(rows, infer_schema_length=None).write_csv(OUT / "hypotheses.csv")

    code_files = sorted((ROOT / "code" / "mafe2").glob("*.py")) + sorted((ROOT / "code" / "tests").glob("*.py"))
    parent = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    verdict = {"preregistration_sha256": psha, "prereg_expected_sha256": PREREG_SHA, "git_parent_commit_of_code": parent,
               "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in code_files},
               "K": K, "alpha_per_test": ALPHA, "window": "entries in [2024-01-01, 2025-01-01), exit < 2025-01-01",
               "hypotheses": verdict_h, "passed": [k for k, v in verdict_h.items() if v["verdict"] == "PASS"],
               "drift_benchmark_24h_long_gross_bps": {"validation_2024": drift_val, "discovery_2020_2023": drift_disc},
               "runtime_seconds": round(time.time() - t0, 1)}
    (OUT / "verdict.json").write_text(json.dumps(verdict, indent=2))
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    {"repro": repro, "run": main}[sys.argv[1]]()
