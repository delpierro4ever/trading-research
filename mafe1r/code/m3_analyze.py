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

# ---------- A. reconstruction: anchors
an = pl.scan_parquet(f"{OUT}/anchors/*.parquet").with_columns(pl.col("date").str.to_date().alias("d")).with_columns(
    pl.col("d").dt.year().alias("year"), pl.col("d").dt.strftime("%Y-%m").alias("month")).with_columns(
    [pl.col(c).fill_nan(None) for c in [f"R{h}" for h in HS] + ["R300s"] + FEATS])
rec = []
for y in (2023, 2024):
    dy = daily[daily.year == y]
    rec.append(dict(item=f"{y} rows", observed=int(dy.rows.sum()), archive=752974771 if y == 2023 else 551044283))
    rec.append(dict(item=f"{y} anchors S1 (segment=UTC day)", observed=int(dy.n_anch_S1.sum()), archive=4058700 if y == 2023 else 3254095))
    rec.append(dict(item=f"{y} anchors S2 (segment=year)", observed=int(dy.n_anch_S2.sum()), archive=4058700 if y == 2023 else 3254095))
    rec.append(dict(item=f"{y} days", observed=len(dy), archive=365 if y == 2023 else 366))
st = [json.load(open(f)) for f in glob.glob(f"{ROOT}/parquet/*.stats.json")]
rec.append(dict(item="all zip bytes", observed=sum(x["zip_bytes"] for x in st), archive=17717147907))
rec.append(dict(item="dups", observed=sum(x["dups"] for x in st), archive=0)); rec.append(dict(item="id gaps within files", observed=sum(x["gaps"] for x in st), archive=0))
rec.append(dict(item="unsorted/non-monotone files", observed=sum((not x["sorted"]) or (not x["ts_monotone"]) for x in st), archive=0))
rec.append(dict(item="files with us timestamps", observed=sum(x["ts_unit_in_file"] == "us" for x in st), archive=None))
save(pd.DataFrame(rec), "m1_m2_reconstruction_counts")

ladder = []
for y in (2023, 2024):
    a = an.filter(pl.col("year") == y).collect()
    for sub, expr in (("all anchors", pl.lit(True)), ("L>=2", pl.col("L") >= 2), ("L>=3", pl.col("L") >= 3), ("L>=4", pl.col("L") >= 4), ("L==5", pl.col("L") == 5)):
        x = a.filter(expr)
        row = dict(year=y, subset=sub, n=len(x))
        for h in HS: row[f"R{h}"] = x[f"R{h}"].drop_nulls().mean()
        row["R300s"] = x["R300s"].drop_nulls().mean(); ladder.append(row)
    for L in range(1, 6):
        x = a.filter(pl.col("L") == L); row = dict(year=y, subset=f"L=={L}", n=len(x))
        for h in HS: row[f"R{h}"] = x[f"R{h}"].drop_nulls().mean()
        row["R300s"] = x["R300s"].drop_nulls().mean(); ladder.append(row)
    ok = a.filter(pl.col("R5").is_not_null())
    r = np.corrcoef(ok["L"].to_numpy(), ok["R5"].to_numpy())[0, 1]
    sl = np.polyfit(ok["L"].to_numpy(), ok["R5"].to_numpy(), 1)[0] / ok["R5"].std()
    ladder.append(dict(year=y, subset="corr(L,R5) | std slope", n=len(ok), R5=r, R10=sl))
    del a
save(pd.DataFrame(ladder), "m2_response_ladder_by_year")

# anchor-level monthly estimand
am = an.group_by(["month", "L"]).agg([pl.len().alias("n")] + [pl.col(f"R{h}").mean().alias(f"R{h}") for h in HS] + [pl.col("R300s").mean().alias("R300s")]).sort(["month", "L"]).collect()
save(am, "m3_anchor_monthly_by_L")
amall = an.group_by("month").agg([pl.len().alias("n")] + [pl.col(f"R{h}").mean().alias(f"R{h}") for h in HS] + [pl.col("R300s").mean().alias("R300s")]).sort("month").collect()
save(amall, "m3_anchor_monthly_all")

# ---------- B. periods table
def period_table(key):
    g = trades.group_by(["reading", key]).agg(
        pl.len().alias("N"), pl.col("gross_bps").sum().alias("gross_bps_sum"), pl.col("gross_bps").mean().alias("gross_bps_per_trade"),
        pl.col("gross_usd").sum().alias("gross_usd"), pl.col("gross_usd").mean().alias("gross_usd_per_trade"),
        pl.col("p_entry").mean().alias("mean_price"),
        *[e for c in ("c1", "c2", "c3") for e in (pl.col(f"{c}_bps").mean().alias(f"cost_{c}_bps_per_trade"), pl.col(f"cost_{c}_usd").sum().alias(f"cost_{c}_usd"),
            pl.col(f"cost_{c}_usd").mean().alias(f"cost_{c}_usd_per_trade"), pl.col(f"net_{c}_bps").mean().alias(f"net_{c}_bps_per_trade"),
            pl.col(f"net_{c}_usd").sum().alias(f"net_{c}_usd"), pl.col(f"net_{c}_usd").mean().alias(f"net_{c}_usd_per_trade"))]
    ).sort(["reading", key]).rename({key: "period"}).with_columns(pl.col("period").cast(pl.String), pl.lit(key).alias("period_type"))
    return g
pt = pl.concat([period_table(k) for k in ("month", "quarter", "year")])
save(pt, "m3_period_table")

# ---------- C. day-block bootstrap
dayf = trades.group_by(["reading", "d"]).agg(pl.len().alias("N"), pl.col("gross_bps").sum().alias("G"), pl.col("c1_bps").sum().alias("C1"),
                                             pl.col("gross_usd").sum().alias("GU")).sort(["reading", "d"]).to_pandas()
dayf["d"] = pd.to_datetime(dayf["d"]); dayf["month"] = dayf.d.dt.strftime("%Y-%m"); dayf["quarter"] = dayf.d.dt.year.astype(str) + "Q" + dayf.d.dt.quarter.astype(str); dayf["year"] = dayf.d.dt.year.astype(str)
def boot_ratio(num, den, reps=B):
    n = len(num); idx = rng.integers(0, n, (reps, n))
    return num[idx].sum(1) / den[idx].sum(1)
rows = []
for rd in range(1, 6):
    df_r = dayf[dayf.reading == rd]
    for pt_name in ("month", "quarter", "year"):
        for per, g in df_r.groupby(pt_name):
            N = g.N.values.astype(float); G = g.G.values; C1 = g.C1.values
            gb = boot_ratio(G, N); n1 = boot_ratio(G - C1, N); n2 = boot_ratio(G - 21.03 * N, N); n3 = boot_ratio(G - 1.0 * N, N)
            q = lambda a: (np.quantile(a, .025), np.quantile(a, .975))
            rows.append(dict(reading=rd, period_type=pt_name, period=per, days=len(g), N=int(N.sum()), gross_per_trade=G.sum() / N.sum(), gross_lo=q(gb)[0], gross_hi=q(gb)[1],
                             net_c1=(G - C1).sum() / N.sum(), net_c1_lo=q(n1)[0], net_c1_hi=q(n1)[1], net_c2=(G - 21.03 * N).sum() / N.sum(), net_c2_lo=q(n2)[0], net_c2_hi=q(n2)[1],
                             net_c3=(G - N).sum() / N.sum(), net_c3_lo=q(n3)[0], net_c3_hi=q(n3)[1]))
save(pd.DataFrame(rows), "m3_bootstrap_ci")

# ---------- D. heterogeneity permutation (gross bps/trade across periods)
def hetero(df_r, key, reps=B):
    lab = pd.factorize(df_r[key])[0]; k = lab.max() + 1
    N = df_r.N.values.astype(float); G = df_r.G.values
    def stats(l):
        n = np.bincount(l, N, k); g = np.bincount(l, G, k); m = g / n; mu = G.sum() / N.sum()
        return (n * (m - mu) ** 2).sum(), m.max(), m.min()
    Q, mx, mn = stats(lab)
    nq = np.empty(reps); nmx = np.empty(reps); nmn = np.empty(reps)
    for i in range(reps):
        nq[i], nmx[i], nmn[i] = stats(rng.permutation(lab))
    return dict(Q=Q, p_Q=(nq >= Q).mean(), best=mx, worst=mn, null_best_med=np.median(nmx), null_best_95=np.quantile(nmx, .95), null_worst_5=np.quantile(nmn, .05),
                p_best=(nmx >= mx).mean(), p_worst=(nmn <= mn).mean(), periods=int(k))
hr = []
for rd in range(1, 6):
    df_r = dayf[dayf.reading == rd]
    for scope, sub in (("2023+2024", df_r), ("2023", df_r[df_r.year == "2023"]), ("2024", df_r[df_r.year == "2024"])):
        for key in ("month", "quarter"):
            if sub[key].nunique() > 1: hr.append(dict(reading=rd, scope=scope, by=key, **hetero(sub, key, 5000 if scope == "2023+2024" else 5000)))
save(pd.DataFrame(hr), "m3_heterogeneity")

# ---------- E. shift-share (net in bps-sum under c1)
tabs = pt.filter(pl.col("period_type").is_in(["quarter", "year"])).to_pandas(); tabs["N"] = tabs["N"].astype(float)
def periods_pair(rd):
    t = tabs[tabs.reading == rd].set_index("period")
    qs = sorted(p for p in t.index if "Q" in p); pairs = list(zip(qs[:-1], qs[1:])) + [("2023", "2024")]
    # half-year pairs
    return t, pairs
ss = []
for rd in range(1, 6):
    t, pairs = periods_pair(rd)
    h = trades.filter(pl.col("reading") == rd).with_columns(pl.when(pl.col("d").dt.month() <= 6).then(pl.col("d").dt.year().cast(pl.String) + "H1").otherwise(pl.col("d").dt.year().cast(pl.String) + "H2").alias("half"))
    hh = h.group_by("half").agg(pl.len().alias("N"), pl.col("gross_bps").mean().alias("g"), pl.col("c1_bps").mean().alias("c")).to_pandas().set_index("half")
    for a_, b_ in pairs:
        A_, B_ = t.loc[a_], t.loc[b_]
        N0, N1 = A_.N, B_.N; g0, g1 = A_.gross_bps_per_trade, B_.gross_bps_per_trade; c0, c1 = A_.cost_c1_bps_per_trade, B_.cost_c1_bps_per_trade
        v0, v1 = g0 - c0, g1 - c1
        tot = N1 * v1 - N0 * v0; tc = (N1 - N0) * v0; tg = N0 * (g1 - g0); tcost = -N0 * (c1 - c0); ti = (N1 - N0) * (v1 - v0)
        ss.append(dict(reading=rd, A=a_, B=b_, N_A=N0, N_B=N1, g_A=g0, g_B=g1, c_A=c0, c_B=c1, net_A_sum=N0 * v0, net_B_sum=N1 * v1, dNet=tot, term_trades=tc, term_gross=tg, term_cost=tcost, term_interaction=ti, check=tot - (tc + tg + tcost + ti)))
    for a_, b_ in (("2023H1", "2023H2"), ("2024H1", "2024H2"), ("2023H2", "2024H1")):
        nn = h.group_by("half").agg(pl.len().alias("N")).to_pandas().set_index("half").N.astype(float)
        if a_ not in nn.index or b_ not in nn.index: continue
        N0, N1 = nn[a_], nn[b_]; g0, g1, c0, c1 = hh.loc[a_, "g"], hh.loc[b_, "g"], hh.loc[a_, "c"], hh.loc[b_, "c"]; v0, v1 = g0 - c0, g1 - c1
        tot = N1 * v1 - N0 * v0
        ss.append(dict(reading=rd, A=a_, B=b_, N_A=N0, N_B=N1, g_A=g0, g_B=g1, c_A=c0, c_B=c1, net_A_sum=N0 * v0, net_B_sum=N1 * v1, dNet=tot, term_trades=(N1 - N0) * v0, term_gross=N0 * (g1 - g0), term_cost=-N0 * (c1 - c0), term_interaction=(N1 - N0) * (v1 - v0), check=0))
save(pd.DataFrame(ss), "m3_shift_share_c1")

# ---------- F. Hyp B marginal trades
hb = []
for rd in (1, 2, 3, 4, 5):
    t = trades.filter(pl.col("reading") == rd).to_pandas()
    for y in (2023, 2024):
        ty = t[t.year == y]
        for L, g in ty.groupby("L"):
            gd = g.groupby("date").agg(N=("gross_bps", "size"), G=("gross_bps", "sum"))
            b = boot_ratio(gd.G.values, gd.N.values.astype(float), 3000)
            hb.append(dict(reading=rd, year=y, split="entry run length L", group=int(L), N=len(g), gross_per_trade=g.gross_bps.mean(), lo=np.quantile(b, .025), hi=np.quantile(b, .975)))
        # order in day thirds
        n_day = ty.groupby("date").seq.transform("max") + 1
        third = np.minimum((ty.seq * 3 // n_day), 2)
        for tt, g in ty.groupby(third):
            gd = g.groupby("date").agg(N=("gross_bps", "size"), G=("gross_bps", "sum")); b = boot_ratio(gd.G.values, gd.N.values.astype(float), 3000)
            hb.append(dict(reading=rd, year=y, split="order within day (third)", group=int(tt), N=len(g), gross_per_trade=g.gross_bps.mean(), lo=np.quantile(b, .025), hi=np.quantile(b, .975)))
    # high/low count months over whole sample
    mc = t.groupby("month").size(); med = mc.median(); t["cnt_grp"] = np.where(t.month.map(mc) > med, "high-count month", "low-count month")
    for gname, g in t.groupby("cnt_grp"):
        gd = g.groupby("date").agg(N=("gross_bps", "size"), G=("gross_bps", "sum")); b = boot_ratio(gd.G.values, gd.N.values.astype(float), 3000)
        hb.append(dict(reading=rd, year=0, split="monthly trade-count split (median)", group=gname, N=len(g), gross_per_trade=g.gross_bps.mean(), lo=np.quantile(b, .025), hi=np.quantile(b, .975), months=int(g.month.nunique())))
save(pd.DataFrame(hb), "m3_hypB_marginal")
mcnt = trades.group_by(["reading", "month"]).agg(pl.len().alias("N")).sort(["reading", "month"]).to_pandas()
save(mcnt, "m3_monthly_trade_counts")

# ---------- G. structural break around 2023-03-22 + daily series
daily["share_L2p"] = 1 - daily.nL.apply(lambda v: v[0]) / daily.rows; daily["share_L5"] = daily.nL.apply(lambda v: v[4]) / daily.rows
daily["buy_share"] = daily.n_buy / daily.rows
dcols = ["rows", "mean_qty", "med_qty", "p90_qty", "vol_btc", "rv_day_bps", "chgfreq", "share_L2p", "share_L5", "buy_share"]
save(daily.drop(columns=["nL", "n_trades"]), "m4_daily_series")
brk = []
pre = daily[(daily.date >= "2023-02-22") & (daily.date <= "2023-03-21")]; post = daily[(daily.date >= "2023-03-22") & (daily.date <= "2023-04-18")]
for c in dcols:
    a, b = pre[c].values, post[c].values; d_obs = b.mean() - a.mean()
    bs = np.array([rng.choice(b, len(b)).mean() - rng.choice(a, len(a)).mean() for _ in range(5000)])
    brk.append(dict(metric=c, pre_mean=a.mean(), post_mean=b.mean(), diff=d_obs, ci_lo=np.quantile(bs, .025), ci_hi=np.quantile(bs, .975), rel_change=d_obs / a.mean()))
save(pd.DataFrame(brk), "m4_structural_break_2023_03_22")
# gross/trade around the break (R2..R5)
tb = trades.filter((pl.col("d") >= dt.date(2023, 2, 22)) & (pl.col("d") <= dt.date(2023, 4, 18))).with_columns((pl.col("d") >= dt.date(2023, 3, 22)).alias("post")).group_by(["reading", "post"]).agg(pl.len().alias("N"), pl.col("gross_bps").mean().alias("gross_per_trade")).sort(["reading", "post"])
save(tb, "m4_break_gross")

# ---------- H. spread proxy / Hyp E
sp = trades.filter(pl.col("reading") == 2).group_by("month").agg(pl.col("p_entry").mean().alias("mean_price"), (0.01 / pl.col("p_entry") * 1e4).mean().alias("spread_proxy_bps"),
    pl.col("c1_bps").mean().alias("c1_bps"), pl.col("cost_c1_usd").mean().alias("c1_usd_per_trade"), pl.col("gross_usd").mean().alias("gross_usd_per_trade")).sort("month")
save(sp, "m3_hypE_spread_proxy")

# ---------- I. Regimes
anf = an.select(["d", "year", "ts", "L", "R300s", "hour"] + FEATS).collect()
edges = {f: np.nanquantile(anf.filter(pl.col("year") == 2023)[f].to_numpy(), [1 / 3, 2 / 3]) for f in FEATS}
json.dump({k: list(map(float, v)) for k, v in edges.items()}, open(f"{RES}/m4_bin_edges_2023.json", "w"), indent=1)
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
save(pd.DataFrame(reg), "m4_regime_bins")
# regime variable distribution shift 2023 -> 2024 (share in each bin)
shift = []
for f in FEATS:
    for y in (2023, 2024):
        v = anf.filter(pl.col("year") == y)[f"bin_{f}"].to_numpy(); v = v[v >= 0]
        shift.append(dict(feature=f, year=y, **{f"share_bin{b}": float((v == b).mean()) for b in (0, 1, 2)}))
save(pd.DataFrame(shift), "m4_bin_shares_by_year")
# monthly regime means (to relate month economics to regime level)
mm = anf.group_by(pl.col("d").dt.strftime("%Y-%m").alias("month")).agg([pl.col(f).mean() for f in FEATS]).sort("month")
save(mm, "m4_monthly_feature_means")
print("done")
