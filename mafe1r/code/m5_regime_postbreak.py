"""Amendment A4 (post hoc, descriptive): the regime-bin analysis restricted to days >= 2023-03-22 (after the tape break), bin edges unchanged (all-2023 terciles)."""
"""M2 checks, M3 decomposition, M4 regimes from the per-day outputs of m2_pass.py. Writes CSVs to results/."""
import os, sys, json, glob, datetime as dt
import numpy as np, polars as pl, pandas as pd
ROOT = "/home/ubuntu/mafe-data/mafe1"; OUT = os.environ.get("MAFE_OUT", f"{ROOT}/out")
RES = os.path.join(os.path.dirname(__file__), "..", "results"); os.makedirs(RES, exist_ok=True)
B = 10000; rng = np.random.default_rng(20261014)
FEATS = [f"{f}_{w}" for w in (300, 3600) for f in ("rate", "vol", "rv", "chgfreq", "evperchg", "meansize", "burst")]
HS = (5, 10, 50, 100, 250)

def save(df, name):
    if isinstance(df, pl.DataFrame): df = df.to_pandas()
    df.to_csv(f"{RES}/{name}.csv", index=False)
    return df

# ---------- load
daily = pd.DataFrame([json.load(open(f)) for f in sorted(glob.glob(f"{OUT}/daily/*.json"))])
daily["date"] = pd.to_datetime(daily["date"]); daily["year"] = daily.date.dt.year
trades = pl.read_parquet(f"{OUT}/trades/*.parquet")
trades = trades.with_columns(
    pl.col("date").str.to_date().alias("d"),
    (2.0 + 0.1 + 0.01 / pl.col("p_entry") * 1e4).alias("c1_bps"), pl.lit(21.03).alias("c2_bps"), pl.lit(1.0).alias("c3_bps"))
trades = trades.with_columns(pl.col("d").dt.strftime("%Y-%m").alias("month"), pl.col("d").dt.year().alias("year"),
    (pl.col("d").dt.year().cast(pl.String) + "Q" + pl.col("d").dt.quarter().cast(pl.String)).alias("quarter"))
for c in ("c1", "c2", "c3"):
    trades = trades.with_columns((pl.col("gross_bps") - pl.col(f"{c}_bps")).alias(f"net_{c}_bps"),
                                 (pl.col(f"{c}_bps") * 1e-4 * pl.col("p_entry") * 0.001).alias(f"cost_{c}_usd"))
    trades = trades.with_columns((pl.col("gross_usd") - pl.col(f"cost_{c}_usd")).alias(f"net_{c}_usd"))

an = pl.scan_parquet(f"{OUT}/anchors/*.parquet").with_columns(pl.col("date").str.to_date().alias("d")).with_columns(
    pl.col("d").dt.year().alias("year"), pl.col("d").dt.strftime("%Y-%m").alias("month")).with_columns(
    [pl.col(c).fill_nan(None) for c in [f"R{h}" for h in HS] + ["R300s"] + FEATS])
# ---------- I. Regimes
anf = an.select(["d", "year", "ts", "L", "R300s", "hour"] + FEATS).collect()
edges = {f: np.nanquantile(anf.filter(pl.col("year") == 2023)[f].to_numpy(), [1 / 3, 2 / 3]) for f in FEATS}  # edges: ALL of 2023 (unchanged from the main analysis)
BRK = dt.date(2023, 3, 22); anf = anf.filter(pl.col("d") >= BRK); trades = trades.filter(pl.col("d") >= BRK)
def add_bins(df):
    cols = []
    for f in FEATS:
        x = df[f].to_numpy(); b = np.where(np.isnan(x), -1, np.digitize(x, edges[f])).astype(np.int8)
        cols.append(pl.Series(f"bin_{f}", b))
    wd = df["d"].dt.weekday()
    cols.append(pl.Series("bin_hour8", (df["hour"].to_numpy() // 8).astype(np.int8)))
    cols.append(pl.Series("bin_weekend", (wd.to_numpy() >= 6).astype(np.int8)))
    cols.append(pl.Series("bin_month", df["d"].dt.month().to_numpy().astype(np.int8)))
    return df.with_columns(cols)
anf = add_bins(anf); trb = add_bins(trades.with_columns(pl.col("d")))
BINCOLS = [f"bin_{f}" for f in FEATS] + ["bin_hour8", "bin_weekend", "bin_month"]
def bin_stats(df, valcols, label, subset_name, reps=2000):
    out = []
    for y in (2023, 2024):
        dy = df.filter(pl.col("year") == y)
        for bc in BINCOLS:
            g = dy.filter(pl.col(bc) >= 0).group_by(["d", bc]).agg(pl.len().alias("n"), *[pl.col(v).sum().alias(f"s_{v}") for v in valcols]).to_pandas()
            days = np.sort(g.d.unique()); di = {d: i for i, d in enumerate(days)}; g["di"] = g.d.map(di)
            bins = sorted(g[bc].unique()); n_arr = np.zeros((len(days), len(bins))); S = {v: np.zeros((len(days), len(bins))) for v in valcols}
            for j, b in enumerate(bins):
                gb = g[g[bc] == b]; n_arr[gb.di.values, j] = gb.n.values
                for v in valcols: S[v][gb.di.values, j] = gb[f"s_{v}"].values
            idx = rng.integers(0, len(days), (reps, len(days)))
            for v in valcols:
                means = np.stack([S[v][idx].sum(1)[:, j] / n_arr[idx].sum(1)[:, j] for j in range(len(bins))], 1)  # reps x bins
                obs = S[v].sum(0) / n_arr.sum(0)
                span = means[:, -1] - means[:, 0]
                for j, b in enumerate(bins):
                    out.append(dict(subset=subset_name, year=y, variable=bc[4:], bin=int(b), metric=v, n=int(n_arr[:, j].sum()), mean=obs[j], lo=np.quantile(means[:, j], .025), hi=np.quantile(means[:, j], .975),
                                    span_last_minus_first=obs[-1] - obs[0], span_lo=np.quantile(span, .025), span_hi=np.quantile(span, .975)))
    return out
reg = []
for k in range(1, 6):
    sub = anf.filter(pl.col("L") >= k).filter(pl.col("R300s").is_not_null())
    reg += bin_stats(sub, ["R300s"], "anchors", f"anchors L>={k}")
    t = trb.filter(pl.col("reading") == k).with_columns(pl.col("net_c1_bps").alias("net_c1"), pl.col("net_c2_bps").alias("net_c2"), pl.col("net_c3_bps").alias("net_c3"))
    reg += bin_stats(t, ["gross_bps", "net_c1", "net_c2", "net_c3"], "trades", f"trades R{k}")
save(pd.DataFrame(reg), "m5_regime_bins_postbreak")
# regime variable distribution shift 2023 -> 2024 (share in each bin)
shift = []
for f in FEATS:
    for y in (2023, 2024):
        v = anf.filter(pl.col("year") == y)[f"bin_{f}"].to_numpy(); v = v[v >= 0]
        shift.append(dict(feature=f, year=y, **{f"share_bin{b}": float((v == b).mean()) for b in (0, 1, 2)}))
save(pd.DataFrame(shift), "m5_bin_shares_postbreak")
# monthly regime means (to relate month economics to regime level)
mm = anf.group_by(pl.col("d").dt.strftime("%Y-%m").alias("month")).agg([pl.col(f).mean() for f in FEATS]).sort("month")
save(mm, "m5_monthly_feature_means_dummy")
print("done")
