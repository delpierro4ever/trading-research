"""MAFE-2 stage 3 (Amendment 2): cross-asset test of the capitulation-long S2_LONG_F4_L4h, run ONCE.
Usage (from phase2/code):  python -m mafe2.run_stage3
Reuses features.Features.premium (F4 4h mean premium-index close), features.zscore, engine.z_direction/run_episodes
(entry t+1min, 24h hold, greedy non-overlap, funding in (entry, exit]) and run_validation.episodes_for via the same
time-base re-binding used for the 2024 validation. No metrics/bookDepth are needed. Data requested only with end<=2025-01-01.
Refuses to run if results/stage3/verdict.json already exists (read-once)."""
from __future__ import annotations
import hashlib, json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import polars as pl
from . import data, features, pipeline, run_validation as rv
from .features import Market, Features, to_min, _kline_arrays, zscore, LS
from .engine import build_registry
from .stats import grid_calendar, t_test, block_bootstrap_p

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "docs" / "PREREGISTRATION.md"
PREREG_SHA = "ced06b5e5b10c9b44f1609b088035e714cd5ee92bfc8ae7ef1c51aa37d844712"
OUT = ROOT / "results" / "stage3"
EPI = Path("/home/ubuntu/mafe-data/episodes/stage3")
CHOSEN = Path("/home/ubuntu/mafe-data/stage3/chosen.json")
HYP_ID = "F4_L4h_H24h_R"            # S2_LONG_F4_L4h = this hypothesis, long side only
COST16, COST12 = 16.0, 12.0
BOOT_B, SEED = 10_000, 20241
G_2024, G_2025 = rv.G_2024, rv.G_2025
T0 = datetime(2020, 1, 1, tzinfo=timezone.utc)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_market_light(symbol: str) -> Market:
    """Same arrays as rv.load_market_validation (klines, premium, funding) from 2021-11-01; metrics replaced by a stub (unused)."""
    s, e = "2021-11-01", "2025-01-01"
    k = data.load("klines_1m", symbol, s, e, ["open", "close", "volume", "taker_buy_volume"])
    ka = _kline_arrays(k, ["open", "close", "volume", "taker_buy_volume"])
    p = data.load("premiumIndexKlines_1m", symbol, s, e, ["close"])
    pa = _kline_arrays(p, ["close"])
    f = data.load("fundingRate", symbol, s, e, ["last_funding_rate"])
    z = np.zeros(1)
    return Market(symbol, open=ka["open"], close=ka["close"], vol=ka["volume"], tbv=ka["taker_buy_volume"], prem=pa["close"],
                  fund_min=to_min(f["calc_time"].to_numpy()), fund_rate=f["last_funding_rate"].to_numpy().astype(float),
                  met_s=z, oi_val=z, top_ratio=z, glob_ratio=z)


def light_pipe(mk):
    g = np.arange(features.NGRID)
    prem4h = Features(mk).premium(g, LS["4h"])          # == Features.all(g)["F4_4h"]
    return SimpleNamespace(mk=mk, z={"F4_4h": zscore(prem4h)})


def quarter_drift(mk, g_lo, qt, H=1440):
    """{quarter label: mean 24h gross (bps) of a long entered at every grid hour g>=g_lo in that quarter; exit inside loaded period}."""
    g = np.arange(g_lo, G_2025)
    e = g * 60 + 1; x = e + H
    ok = x < len(mk.open)
    g, e, x = g[ok], e[ok], x[ok]
    pe, px = mk.open[e], mk.open[x]
    v = (pe > 0) & (px > 0)
    r = np.log(px[v] / pe[v]) * 1e4
    q = qt[g[v]]
    return {int(u): float(r[q == u].mean()) for u in np.unique(q)}, {int(u): int((q == u).sum()) for u in np.unique(q)}


def pooled_boot_percentile(x, blocks, B=BOOT_B, seed=SEED):
    """Calendar-week block bootstrap, percentile method: resample whole ISO weeks (with replacement) of the pooled panel,
    mean of resampled panel = sum/count; p = share of resampled means <= 0. Weeks = weeks containing >=1 episode."""
    ub, inv = np.unique(blocks, return_inverse=True)
    W = len(ub)
    s = np.bincount(inv, weights=x, minlength=W); c = np.bincount(inv, minlength=W).astype(float)
    rng = np.random.default_rng(seed)
    cnt = rng.multinomial(W, np.full(W, 1.0 / W), size=B).astype(float)
    den = cnt @ c
    bm = (cnt @ s) / den
    return float(np.mean(bm <= 0)), float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5)), int(W)


def main():
    t0 = time.time()
    psha = sha256(PREREG)
    assert psha == PREREG_SHA, f"pre-registration hash mismatch {psha}"
    assert not (OUT / "verdict.json").exists(), "stage 3 is read-once: verdict.json already exists"
    assert (OUT / "universe.csv").exists(), "universe.csv must be written before any outcome is computed"
    OUT.mkdir(parents=True, exist_ok=True); EPI.mkdir(parents=True, exist_ok=True)
    reg = {h.id: h for h in build_registry()}
    h = reg[HYP_ID]
    rv.set_timebase(rv.NMIN_V, rv.NGRID_V)
    cal = grid_calendar(rv.NGRID_V)
    yr, qt, wk = cal

    # ---------- regression check: BTCUSDT 2024 via the exact validation path AND via the light path used for altcoins
    pipe_full = pipeline.Pipeline(rv.load_market_validation("BTCUSDT"))
    ep_full = rv.episodes_for(pipe_full, h, True, G_2024, G_2025)
    n12_full = ep_full["gross"] + ep_full["fund"] - 12.0
    pipe_l = light_pipe(load_market_light("BTCUSDT"))
    ep_l = rv.episodes_for(pipe_l, h, True, G_2024, G_2025)
    n12_l = ep_l["gross"] + ep_l["fund"] - 12.0
    vh = pl.read_csv(ROOT / "results" / "validation" / "hypotheses.csv", infer_schema_length=None).filter(pl.col("id") == "S2_LONG_F4_L4h")
    ref_n, ref_m = int(vh["n"][0]), float(vh["mean_net12"][0])
    reg_check = {"btc_full_path_n": int(len(n12_full)), "btc_full_path_mean_net12": float(n12_full.mean()),
                 "btc_light_path_n": int(len(n12_l)), "btc_light_path_mean_net12": float(n12_l.mean()),
                 "committed_validation_n": ref_n, "committed_validation_mean_net12": ref_m,
                 "episodes_identical": bool(np.array_equal(ep_full["g"], ep_l["g"]))}
    reg_check["pass"] = bool(reg_check["btc_full_path_n"] == ref_n == 72 and reg_check["btc_light_path_n"] == 72 and reg_check["episodes_identical"]
                             and abs(reg_check["btc_full_path_mean_net12"] - ref_m) < 1e-9 and abs(reg_check["btc_light_path_mean_net12"] - ref_m) < 1e-9
                             and abs(ref_m - 53.9) < 0.05)
    print("REGRESSION", json.dumps(reg_check), flush=True)
    assert reg_check["pass"], "BTC regression check failed; altcoins not run"
    del pipe_full, pipe_l

    # ---------- altcoin panel
    uni = pl.read_csv(OUT / "universe.csv", infer_schema_length=None)
    chosen = json.loads(CHOSEN.read_text())
    ch = uni.filter(pl.col("status") == "chosen")
    assert sorted(ch["symbol"].to_list()) == sorted(chosen) and len(chosen) == 25
    frames, sym_rows = [], []
    for r in ch.sort("rank").iter_rows(named=True):
        sym = r["symbol"]
        ws = datetime.fromisoformat(r["window_start"])
        g_lo = int(-(-((ws - T0).total_seconds()) // 3600))
        pipe = light_pipe(load_market_light(sym))
        assert len(pipe.mk.open) == rv.NMIN_V
        ep = rv.episodes_for(pipe, h, True, g_lo, G_2025)
        g = ep["g"]
        assert len(g) == 0 or (g.min() >= g_lo and (g * 60 + 1 + h.H).max() < rv.NMIN_V)
        dq, dn = quarter_drift(pipe.mk, g_lo, qt)
        drift = np.array([dq[int(q)] for q in qt[g]]) if len(g) else np.zeros(0)
        gross, fund = ep["gross"], ep["fund"]
        df = pl.DataFrame({"symbol": [sym] * len(g), "grid_idx": g,
                           "entry_time": np.datetime64("2020-01-01T00:00:00", "ms") + (g * 60 + 1).astype("timedelta64[m]").astype("timedelta64[ms]"),
                           "year": yr[g], "quarter": qt[g], "iso_week": wk[g], "gross_bps": gross, "funding_bps": fund,
                           "net16_bps": gross + fund - COST16, "net12_bps": gross + fund - COST12, "matched_drift_bps": drift,
                           "excess_bps": gross - drift})
        df.write_parquet(EPI / f"{sym}.parquet")
        frames.append(df)
        n = len(g)
        sym_rows.append({"rank": r["rank"], "symbol": sym, "window_start": r["window_start"], "n": n,
                         "mean_gross": float(gross.mean()) if n else np.nan, "mean_funding": float(fund.mean()) if n else np.nan,
                         "mean_net16": float((gross + fund - COST16).mean()) if n else np.nan,
                         "mean_net12": float((gross + fund - COST12).mean()) if n else np.nan,
                         "mean_matched_drift": float(drift.mean()) if n else np.nan, "mean_excess": float((gross - drift).mean()) if n else np.nan,
                         "hit_rate_net16": float((gross + fund - COST16 > 0).mean()) if n else np.nan,
                         "sum_net16": float((gross + fund - COST16).sum()) if n else 0.0})
        print(f"[{time.time()-t0:.0f}s] {sym} n={n}", flush=True)
        del pipe
    sy = pl.DataFrame(sym_rows, infer_schema_length=None)
    sy.write_csv(OUT / "symbols.csv")
    P = pl.concat(frames)
    x = P["net16_bps"].to_numpy(); ex = P["excess_bps"].to_numpy(); wks = P["iso_week"].to_numpy()

    # ---------- gates
    p_pct, ci_lo, ci_hi, nweeks = pooled_boot_percentile(x, wks)
    p_centered = block_bootstrap_p(x, wks, B=BOOT_B)       # existing stats.py convention (null-centred); reported, not the gate
    mean_net16 = float(x.mean())
    gate_a = bool(mean_net16 > 0 and p_pct < 0.05)
    mean_excess = float(ex.mean())
    gate_b = bool(mean_excess > 0)
    elig = sy.filter(pl.col("n") >= 10)
    frac_pos = float((elig["mean_net16"] > 0).mean()) if elig.height else float("nan")
    gate_c = bool(elig.height > 0 and frac_pos >= 0.60)
    years = {}
    for y in (2022, 2023, 2024):
        m = P["year"].to_numpy() == y
        years[y] = {"n": int(m.sum()), "mean_gross": float(P["gross_bps"].to_numpy()[m].mean()) if m.any() else None,
                    "mean_net16": float(x[m].mean()) if m.any() else None, "mean_net12": float(P["net12_bps"].to_numpy()[m].mean()) if m.any() else None,
                    "mean_excess": float(ex[m].mean()) if m.any() else None}
    n_pos_years = sum(1 for y in years.values() if y["mean_net16"] is not None and y["mean_net16"] > 0)
    gate_d = bool(n_pos_years >= 2)
    verdict = "PASS" if (gate_a and gate_b and gate_c and gate_d) else "FAIL"

    # ---------- reported diagnostics (not gates)
    mn, tstat, _, _ = t_test(x)
    top3 = sy.sort("sum_net16", descending=True)["symbol"].head(3).to_list()
    rest = P.filter(~pl.col("symbol").is_in(top3))
    xr = rest["net16_bps"].to_numpy()
    p_rest, lo_r, hi_r, _ = pooled_boot_percentile(xr, rest["iso_week"].to_numpy())
    wk_means = P.group_by("iso_week").agg(m=pl.col("net16_bps").mean(), n=pl.len())
    days = P.with_columns(day=pl.col("entry_time").dt.date())
    dcount = days.group_by("day").agg(n=pl.len(), m=pl.col("net16_bps").mean()).sort(["n", "day"], descending=[True, False])
    top20 = dcount.head(20)["day"].to_list()
    in20 = days.filter(pl.col("day").is_in(top20))
    out20 = days.filter(~pl.col("day").is_in(top20))
    diag = {
        "n_episodes": int(P.height), "n_symbols_with_episodes": int(sy.filter(pl.col("n") > 0).height), "n_symbols_ge10": int(elig.height),
        "pooled_mean_gross": float(P["gross_bps"].mean()), "pooled_mean_funding": float(P["funding_bps"].mean()),
        "pooled_mean_net16": mean_net16, "pooled_mean_net12": float(P["net12_bps"].mean()),
        "pooled_mean_matched_drift": float(P["matched_drift_bps"].mean()), "pooled_mean_excess": mean_excess,
        "naive_t_net16": float(tstat), "naive_p_one_sided": float(t_test(x)[2]),
        "boot_percentile_p": p_pct, "boot_percentile_95ci_mean_net16": [ci_lo, ci_hi], "boot_weeks_in_panel": nweeks,
        "boot_centered_null_p_reported_only": p_centered,
        "excluding_top3_symbols": {"top3": top3, "n": int(rest.height), "mean_net16": float(xr.mean()), "boot_percentile_p": p_rest},
        "equal_weight_per_week_mean_net16": float(wk_means["m"].mean()), "n_weeks_with_episodes": int(wk_means.height),
        "distinct_entry_days": int(dcount.height),
        "top20_simultaneous_entry_days": {"days": [str(d) for d in top20], "episodes_on_days": int(in20.height),
                                          "share_of_episodes": float(in20.height / P.height),
                                          "mean_net16_on_days": float(in20["net16_bps"].mean()),
                                          "mean_net16_other_days": float(out20["net16_bps"].mean()) if out20.height else None,
                                          "max_entries_one_day": int(dcount["n"].max())},
        "per_year": years,
    }
    code_files = sorted((ROOT / "code" / "mafe2").glob("*.py")) + sorted((ROOT / "code" / "ingest").glob("*.py"))
    parent = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = {"hypothesis": "S3_LONG_F4_L4h_XS", "preregistration_sha256": psha, "prereg_expected_sha256": PREREG_SHA,
           "git_parent_commit_of_code": parent, "code_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in code_files},
           "regression_check": reg_check, "symbols": chosen,
           "gates": {"a_pooled_net16_gt0_and_boot_p_lt_0.05": {"mean_net16": mean_net16, "p_percentile": p_pct, "pass": gate_a},
                     "b_pooled_excess_gt0": {"mean_excess": mean_excess, "pass": gate_b},
                     "c_breadth_ge_60pct": {"n_eligible": int(elig.height), "n_positive": int((elig["mean_net16"] > 0).sum()), "fraction": frac_pos, "pass": gate_c},
                     "d_years_positive_ge2_of_3": {"positive_years": n_pos_years, "per_year_mean_net16": {str(k): v["mean_net16"] for k, v in years.items()}, "pass": gate_d}},
           "verdict": verdict, "diagnostics": diag, "bootstrap": {"B": BOOT_B, "seed": SEED, "method": "percentile: share of resampled pooled means <= 0; whole ISO weeks (weeks with >=1 episode) resampled"},
           "runtime_seconds": round(time.time() - t0, 1)}
    (OUT / "verdict.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
