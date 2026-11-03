"""Post-hoc descriptive diagnostics (declared as amendments A2-A3 in ANALYSIS_PLAN.md): anchor sampling design vs replay; pre/post 2023-03-22 split."""
import os, numpy as np, polars as pl, pandas as pd, datetime as dt
ROOT = "/home/ubuntu/mafe-data/mafe1/out"; RES = os.path.join(os.path.dirname(__file__), "..", "results")
rng = np.random.default_rng(7)
an = pl.scan_parquet(f"{ROOT}/anchors/*.parquet").with_columns(pl.col("date").str.to_date().alias("d")).filter(pl.col("R300s").is_not_nan() & (pl.col("L") == 5)).select(["d", "i", "R300s", "R5", "rv_300", "rate_300"]).collect()
an = an.with_columns((pl.col("i") % 250 == 0).alias("event_driven"),
    pl.when(pl.col("d") < dt.date(2023, 3, 22)).then(pl.lit("2023 pre-break (Jan1-Mar21)")).when(pl.col("d") < dt.date(2024, 1, 1)).then(pl.lit("2023 post-break (Mar22-Dec31)")).otherwise(pl.lit("2024")).alias("era"))
def dayboot(df, col, reps=3000):
    g = df.group_by("d").agg(pl.len().alias("n"), pl.col(col).sum().alias("s")).sort("d"); n = g["n"].to_numpy().astype(float); s = g["s"].to_numpy()
    idx = rng.integers(0, len(n), (reps, len(n))); b = s[idx].sum(1) / n[idx].sum(1)
    return s.sum() / n.sum(), np.quantile(b, .025), np.quantile(b, .975), int(n.sum())
rows = []
for era in ["2023 pre-break (Jan1-Mar21)", "2023 post-break (Mar22-Dec31)", "2024"]:
    for name, f in (("all L==5 anchors", pl.lit(True)), ("event-driven anchors (i%250==0)", pl.col("event_driven")), ("time-driven only (first-in-30s, not i%250==0)", ~pl.col("event_driven"))):
        sub = an.filter((pl.col("era") == era) & f)
        for col in ("R300s",):
            m, lo, hi, n = dayboot(sub, col); rows.append(dict(era=era, anchors=name, metric=col, n=n, mean=m, lo=lo, hi=hi))
pd.DataFrame(rows).to_csv(f"{RES}/m5_anchor_sampling_and_era.csv", index=False); print(pd.DataFrame(rows).to_string())
# era-split of R5 replay (reading 5 and 2) trade-level gross/net
tr = pl.read_parquet(f"{ROOT}/trades/*.parquet").with_columns(pl.col("date").str.to_date().alias("d"))
tr = tr.with_columns(pl.when(pl.col("d") < dt.date(2023, 3, 22)).then(pl.lit("2023 pre-break")).when(pl.col("d") < dt.date(2024, 1, 1)).then(pl.lit("2023 post-break")).otherwise(pl.lit("2024")).alias("era"),
                     (pl.col("gross_bps") - (2.1 + 0.01 / pl.col("p_entry") * 1e4)).alias("net_c1"))
rows = []
for rd in (1, 2, 3, 4, 5):
    for era in ["2023 pre-break", "2023 post-break", "2024"]:
        s = tr.filter((pl.col("reading") == rd) & (pl.col("era") == era))
        for col in ("gross_bps", "net_c1"):
            m, lo, hi, n = dayboot(s, col); rows.append(dict(reading=rd, era=era, metric=col, n=n, mean=m, lo=lo, hi=hi, days=s["d"].n_unique()))
pd.DataFrame(rows).to_csv(f"{RES}/m5_replay_by_era.csv", index=False); print(pd.DataFrame(rows).to_string())
# ladder by era (L==5 anchors, all anchors) : mean direction-normalised response by event horizon
HS = (5, 10, 50, 100, 250)
a2 = pl.scan_parquet(f"{ROOT}/anchors/*.parquet").with_columns(pl.col("date").str.to_date().alias("d")).with_columns(
    [pl.col(c).fill_nan(None) for c in [f"R{h}" for h in HS] + ["R300s"]]).with_columns(
    pl.when(pl.col("d") < dt.date(2023, 3, 22)).then(pl.lit("2023 pre-break")).when(pl.col("d") < dt.date(2024, 1, 1)).then(pl.lit("2023 post-break")).otherwise(pl.lit("2024")).alias("era")).collect()
rows = []
for era in ["2023 pre-break", "2023 post-break", "2024"]:
    for name, f in (("all anchors", pl.lit(True)), ("L==5", pl.col("L") == 5)):
        s = a2.filter((pl.col("era") == era) & f); row = dict(era=era, subset=name, n=len(s))
        for c in [f"R{h}" for h in HS] + ["R300s"]: row[c] = s[c].mean()
        rows.append(row)
pd.DataFrame(rows).to_csv(f"{RES}/m5_ladder_by_era.csv", index=False); print(pd.DataFrame(rows).to_string())
