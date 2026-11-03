"""Render phase2/docs/DISCOVERY_REPORT.md from results/discovery/{hypotheses.csv,advancement.json,controls.json}."""
from __future__ import annotations
import json
from pathlib import Path
import polars as pl
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results" / "discovery"


def f(x, k=1):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:.{k}f}"


def main():
    d = pl.read_csv(R / "hypotheses.csv", infer_schema_length=None)
    adv = json.loads((R / "advancement.json").read_text())
    ctl = json.loads((R / "controls.json").read_text())
    L = []
    w = L.append
    w("# MAFE-2 Discovery Report (2020-2023, BTCUSDT; ETHUSDT sign check)\n")
    w(f"Pre-registration sha256: `{adv['preregistration_sha256']}` (matches the registered value).  ")
    w(f"Code parent commit: `{adv['git_parent_commit_of_code']}`; sha256 of each code file is in `results/discovery/advancement.json`.  ")
    w(f"Run time of the discovery script: {adv['runtime_seconds']} s (feature building plus 139 hypotheses on two symbols).  ")
    w("Only data < 2024-01-01 was read, through `mafe2.data`. All 139 hypotheses are listed in `results/discovery/hypotheses.csv`; "
      "episode-level parquet files are in `/home/ubuntu/mafe-data/episodes/discovery/<SYMBOL>/<id>.parquet` (not in git).\n")
    w("All figures are bps, round trip cost C = 12 bps (primary) unless stated; funding actually settled while held is included in net.\n")

    w("## Headline\n")
    w(f"- Hypotheses: {d.height}. BH (q = 0.10) survivors on net > 0 (one-sided t-test): **{adv['n_bh_net12_q10']}**. "
      f"Smallest one-sided p = {f(d['p_net12_1s'].min(), 5)}; BH threshold for rank 1 = {0.10/139:.5f}.")
    w(f"- Informational screen, mean gross != 0 (two-sided, BH q = 0.05): {adv['n_bh_gross_q05']} hypotheses pass "
      "(not a gate; see list below).")
    w(f"- Gate (1) mode: **{adv['gate1_mode']}**. Candidates entering gates 2-4: {adv['n_gate1_candidates']}; passing gates 2-4: {adv['n_pass_gates_2_4']}; K cap = {adv['K']}.")
    w(f"- Advanced to validation ({len(adv['advanced'])}): " + ", ".join(f"`{a['id']}` ({a['label']})" for a in adv["advanced"]) + ".\n")

    w("## Per-family summary (best and worst cell by net t-statistic)\n")
    w("| Family | cells | BH net survivors | gross-screen survivors | mean net > 0 | best cell | n | gross | net12 | t | worst cell | n | gross | net12 | t |")
    w("|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|")
    for fam in sorted(d["family"].unique().to_list()):
        s = d.filter(pl.col("family") == fam).sort("t_net12", descending=True, nulls_last=True)
        b, wst = s.row(0, named=True), s.row(s.height - 1, named=True)
        w(f"| {fam} | {s.height} | {int(s['bh_net12_q10'].sum())} | {int(s['bh_gross_q05'].sum())} | {int((s['mean_net12'] > 0).sum())} | "
          f"`{b['id']}` | {b['n']} | {f(b['mean_gross'])} | {f(b['mean_net12'])} | {f(b['t_net12'], 2)} | "
          f"`{wst['id']}` | {wst['n']} | {f(wst['mean_gross'])} | {f(wst['mean_net12'])} | {f(wst['t_net12'], 2)} |")
    w("")

    w("## Top 15 hypotheses by net t-statistic\n")
    cols = ["id", "n", "mean_gross", "mean_funding", "mean_net12", "mean_net8", "median_net12", "hit_rate", "t_net12", "p_net12_1s", "p_boot",
            "eth_n", "eth_mean_gross"]
    w("| id | n | gross | funding | net12 | net8 | median net12 | hit | t | p (1-sided t) | p (week bootstrap) | ETH n | ETH gross |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in d.sort("t_net12", descending=True, nulls_last=True).head(15).iter_rows(named=True):
        w(f"| `{r['id']}` | {r['n']} | {f(r['mean_gross'])} | {f(r['mean_funding'], 2)} | {f(r['mean_net12'])} | {f(r['mean_net8'])} | {f(r['median_net12'])} | "
          f"{f(r['hit_rate'], 2)} | {f(r['t_net12'], 2)} | {f(r['p_net12_1s'], 4)} | {f(r['p_boot'], 4)} | {r['eth_n']} | {f(r['eth_mean_gross'])} |")
    w("")

    w("## Advancement decision, gate by gate\n")
    w("Gate (1) was evaluated first: no hypothesis is BH-significant on net > 0 at q = 0.10, so the best 5 by net t-statistic with mean net > 0 "
      "form the `NEAR_MISS` candidate set. Gates (2) n >= 100, (3) mean net > 0 in >= 3 of the counted discovery years "
      "(F5/F6: 2020 counts only if it has >= 100 episodes; F8: >= 75 % of the 4 quarters of 2023), and (4) same sign of mean gross on ETHUSDT "
      "were then applied; ranking by net t-statistic, cap K = 10.\n")
    w("| id | t | mean net12 | p (1-sided) | p (bootstrap) | (1) candidate | (2) n >= 100 | (3) years | (4) ETH sign | advanced |")
    w("|---|---:|---:|---:|---:|---|---|---|---|---|")
    for r in d.filter(pl.col("gate1_candidate")).sort("t_net12", descending=True).iter_rows(named=True):
        w(f"| `{r['id']}` | {f(r['t_net12'], 2)} | {f(r['mean_net12'])} | {f(r['p_net12_1s'], 4)} | {f(r['p_boot'], 4)} | NEAR_MISS | "
          f"{'pass' if r['gate2_n100'] else 'FAIL'} (n={r['n']}) | {'pass' if r['gate3_years'] else 'FAIL'} ({r['gate3_detail']}) | "
          f"{'pass' if r['gate4_eth_sign'] else 'FAIL'} (BTC {f(r['mean_gross'])}, ETH {f(r['eth_mean_gross'])}) | "
          f"{'YES (' + r['label'] + ')' if r['advanced'] else 'no'} |")
    w("")
    w("Per-year net12 (n) of the candidates:\n")
    w("| id | 2020 | 2021 | 2022 | 2023 |")
    w("|---|---:|---:|---:|---:|")
    for r in d.filter(pl.col("gate1_candidate")).sort("t_net12", descending=True).iter_rows(named=True):
        w(f"| `{r['id']}` | " + " | ".join(f"{f(r[f'net12_{y}'], 0)} ({r[f'n_{y}']})" for y in (2020, 2021, 2022, 2023)) + " |")
    w("")
    w("Informational gross screen (mean gross != 0, BH q = 0.05) survivors: " +
      ", ".join(f"`{r['id']}` (gross {f(r['mean_gross'])}, p {r['p_gross_2s']:.1e})" for r in d.filter(pl.col("bh_gross_q05")).iter_rows(named=True)) + ".\n")

    w("## Validation of the code\n")
    w("Run with `python -m tests.run_checks` from `phase2/code` (output in `results/discovery/controls.json`). Overall: **" + ("PASS" if ctl["all_pass"] else "FAIL") + "**.\n")
    w(f"1. Hypothesis count: {ctl['hypothesis_count']} (expected 139): {'pass' if ctl['hypothesis_count_pass'] else 'FAIL'}.")
    for sym in ("BTCUSDT", "ETHUSDT"):
        k = ctl[f"lookahead_{sym}"]
        w(f"2. Lookahead test {sym}: {k['n_points']} random grid points; at each, every dataset was replaced by random garbage after the allowed "
          f"cutoff (klines after t-2min open time, metrics/bookDepth after t-10min, funding after t) and all 17 features plus their z-scores "
          f"recomputed: {k['feature_checks']} feature checks, {k['n_mismatches']} mismatches ({'pass' if k['pass'] else 'FAIL'}). "
          f"Sensitivity (cut tightened by 15 minutes must change the feature): {k['sensitivity_changed_when_cut_tightened']}.")
    p = ctl["positive_control"]
    w(f"3. Positive control (deliberate cheat: future 1 h return as feature, continuation, H = 1 h; not among the 139 and not written to outputs): "
      f"n = {p['n']}, mean gross {f(p['mean_gross_bps'])} bps, mean net12 {f(p['mean_net12_bps'])} bps: {'pass' if p['pass'] else 'FAIL'}.")
    n = ctl["negative_controls"]
    w(f"4. Negative controls (20 seeds each; pooled episodes; expected net = mean funding - 12):")
    for k, v in n.items():
        if isinstance(v, dict):
            w(f"   - `{k}`: n = {v['n_total']}, mean gross {f(v['mean_gross'], 2)} +/- {f(v['se_gross'], 2)} (s.e.), mean funding {f(v['mean_funding'], 3)}, mean net12 {f(v['mean_net12'], 2)}.")
    w(f"   Firing rate: real F1 L=1h {n['firing_rate_F1_1h_real']:.3f}; iid noise feature {n['firing_rate_noise']:.3f} "
      f"(the iid feature fires at the Gaussian rate 13.4 %; the real feature fires less often because returns are fat-tailed). Result: {'pass' if n['pass'] else 'FAIL'}.\n")

    w("## Implementation decisions (ambiguities resolved; conservative reading where possible)\n")
    for s in [
        "Signal rule follows the task clarification (previous 720 hourly grid points, >= 480 non-null, |z| >= 1.5), not the 30-day / 20-day wording of the pre-registration; the two agree in length (30 d = 720 h). Sample standard deviation (ddof = 1). A window with (numerically) zero variance gives no signal.",
        "Greedy non-overlap taken literally: after entering at t+1min with horizon H, the next admissible grid point is the first t' >= exit time, i.e. t + H + 1 h. For H = 1 h the signal can therefore trade at most every second hour (the grid point t+1h is before the exit at t+1h01).",
        "Episodes whose exit would fall at or after 2024-01-01 are dropped (a few at most per hypothesis, last days of December 2023).",
        "Return over L = ln(close of the last usable 1m bar / close of the usable bar L minutes earlier); the last usable bar is the one opening at t-2min. Taker-flow and premium windows are the L bars ending at that bar.",
        "Premium (F4) window must contain all L bars (any missing minute gives no signal). Premium gaps are the dates listed in the manifest; the strict rule drops windows touching them.",
        "Metrics (F5, F6): last row with create_time <= t-10min, and that row (and the comparison row L earlier for F5) may be at most 5 minutes (one sampling interval) older than its target time, otherwise no signal. A null value gives no signal.",
        "bookDepth (F8): snapshot imbalance = (notional at -1 % minus notional at +1 %) / sum; snapshots lacking either band are discarded; the feature is the mean over snapshots in (t-L-10min, t-10min], required to hold >= 80 % of the expected number (L / 30.5 s) and the last snapshot within 60 s of the window end. These two thresholds are my choices (the spec only says 'skip, never fill beyond one sampling interval').",
        "Funding feature: most recent funding row with calc_time <= t. Note some calc_time stamps carry a +2 ms offset (e.g. 00:00:00.002), so the rate for the 00:00 settlement becomes usable from the 01:00 grid point. Funding P&L uses events with time in (entry, exit].",
        "F7 direction = sign of the BTC discovery mean gross of the always-long episodes (ties to +1); the ETH check for F7 reuses the BTC direction. Day-of-week uses UTC, Monday = 0. Because direction is chosen in-sample, mean gross >= 0 by construction, so F7's gross screen is not informative.",
        "F7 p-value for net > 0: the standard one-sided t-test p (equal to the two-sided p halved when mean net > 0; for mean net <= 0 it is >= 0.5, so such cells can never be significant). The two-sided p is also in the CSV (`p_net12_2s`). A hypothesis counts as BH-significant only if mean net > 0 as well.",
        "Bootstrap: ISO-week blocks of the entry time resampled with replacement, 10,000 resamples, null-centred, one-sided p = (1 + #{boot mean - observed mean >= observed mean}) / (B + 1). Seed 12345.",
        "ETH F5/F6 signals are suppressed before 2022-01-01 (amendment notes); ETH F8 uses 2023 (its data start). ETH statistics are mean gross, mean net and n only.",
        "NEAR_MISS fallback is used only if no hypothesis is BH-significant (literal reading); the best 5 are taken before gates (2)-(4) are applied, as gate (1) is defined as the candidate set.",
        "Gate (3) counts a year with zero episodes as not positive; for F5/F6, 2020 (Sept-Dec) counts only if it has >= 100 episodes, otherwise 3 of 3 full years is required. Years/quarters are by entry time.",
    ]:
        w(f"- {s}")
    w("")
    w("## Observations worth a second look (neutral)\n")
    for s in [
        "BTC `count_toptrader_long_short_ratio` is null for most of 2022 (Jan-Apr, Jul-Nov entirely; the Binance archive has a hole) and `count_long_short_ratio` is partly repeated/stale in Jan 2022. F6-top therefore has almost no 2022 signals (5 episodes at H = 24 h, 13 at 4 h, 27 at 1 h). `F6_top_H24h_R` is counted as positive in 2022 on those 5 episodes (net +231 bps), which is how it meets gate (3); on a more demanding reading (years with a minimum number of episodes) it would not. ETH top-ratio has the same hole.",
        "Every surviving near-miss is a 24 h reversal against the premium / positioning level (F4 premium over 1 h and 4 h; F6 top-trader and global ratios), i.e. one economic signal (extreme crowding / premium followed by reversal) seen through correlated features. They are not 4 independent confirmations. Their mean gross (38-57 bps) is larger than the 12 bps cost, and funding contributes about +2.7 to +4.8 bps because the reversal side is the side that receives funding.",
        "None of the 139 reach BH significance on net at q = 0.10; the best one-sided t-test p is 0.0034 against a rank-1 threshold of 0.00072. Of 139 one-sided tests about 14 would fall below 0.10 by chance alone; observed number with p < 0.10: " + str(int((d['p_net12_1s'] < 0.10).sum())) + ", with p < 0.05: " + str(int((d['p_net12_1s'] < 0.05).sum())) + ".",
        "Continuation and reversal cells of the same feature are exact mirrors in gross (same episodes, opposite sign), so the 18 gross-screen survivors are 9 distinct signals; net differs only through the 12 bps cost and the sign of funding.",
        "Most short-horizon (H = 1 h) cells are close to gross 0 (|gross| < 5 bps) and net about -12 bps, consistent with the negative controls.",
        "Among F4 and F6 reversal cells, only the H = 24 h ones reach t > 2 (n of 329-651); H = 4 h cells are about 0 to +5 bps net with t <= 1.2. Episode counts are modest and 2020-2021 vs 2022-2023 regimes are mixed; per-year numbers are in the CSV.",
    ]:
        w(f"- {s}")
    w("")
    (ROOT / "docs" / "DISCOVERY_REPORT.md").write_text("\n".join(L))
    print("report written")


if __name__ == "__main__":
    main()
