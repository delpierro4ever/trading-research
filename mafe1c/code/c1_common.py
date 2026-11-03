"""Shared helpers for MAFE-1C analysis: load trades, attach cost models K1-K4 (PREREG §3), bootstrap utilities."""
import numpy as np, pandas as pd, polars as pl, json
ROOT = "/home/ubuntu/mafe-data/mafe1"
RES = "/home/ubuntu/mafe-research-archive/mafe1c/results"
SEED = 20261015
END2024_MS = 1735689600000  # 2025-01-01T00:00Z
def costs(df):
    """add cost columns (bps) and net columns. latency slippage is inside gross_bps (entry delayed 500 ms)."""
    df = df.copy()
    var = df.spread_bps + df.impact_small_bps
    df["gross0_bps"] = df.gross_bps + df.lat500_bps
    df["var_bps"] = var
    df["cost_K1"] = 2.0 + 0.1 + df.tick_bps
    df["cost_K2"] = 10.0 + var
    df["cost_K3"] = 2.0 + 5.0 + 0.65 + 0.5 * var
    df["cost_K3lo"] = df.cost_K3 - 0.33; df["cost_K3hi"] = df.cost_K3 + 0.34
    df["cost_K4"] = 20.0 + var
    df["cost_K4b"] = 15.0 + var
    for k in ("K1", "K2", "K3", "K3lo", "K3hi", "K4", "K4b"): df[f"net_{k}"] = df.gross_bps - df[f"cost_{k}"]
    return df
def load_trades(rule="ALL", sub="p2324", years=None):
    d = pl.read_parquet(f"{ROOT}/c1/{sub}/trades_{rule}/*.parquet").to_pandas()
    d["day"] = pd.to_datetime(d["date"]); d["year"] = d.day.dt.year; d["month"] = d.day.dt.strftime("%Y-%m")
    d["dow"] = d.day.dt.dayofweek
    if sub == "p2324": d = d[d.exit_ts < END2024_MS]  # drop the one trade whose exit price is read from 2025-01-01 (mafe1r definition ended 2024-12-31)
    if years: d = d[d.year.isin(years)]
    return costs(d.reset_index(drop=True))
def day_agg(df, cols, key="day"):
    g = df.groupby(key)
    n = g.size().rename("N"); s = g[cols].sum()
    return pd.concat([n, s], axis=1)
def boot_mean_ci(da, col, B=10000, rng=None, alpha=0.05):
    """day-block bootstrap of ratio-of-sums (sum col / sum N) over days; da = day_agg output."""
    rng = rng or np.random.default_rng(SEED)
    N = da.N.values.astype(float); S = da[col].values; n = len(N)
    idx = rng.integers(0, n, (B, n)); m = S[idx].sum(1) / N[idx].sum(1)
    return S.sum() / N.sum(), np.quantile(m, alpha / 2), np.quantile(m, 1 - alpha / 2), m
