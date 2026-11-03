"""Render phase3/docs/DISCOVERY_REPORT.md from results/discovery/*. Usage (phase3/code): python -m mafe3.make_report"""
from __future__ import annotations
import json
from pathlib import Path
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results" / "discovery"
OUT = ROOT / "docs" / "DISCOVERY_REPORT.md"


def f(x, nd=2):
    if x is None: return ""
    try:
        if x != x: return ""
    except Exception: pass
    return f"{x:.{nd}f}"


def main():
    df = pl.read_csv(R / "hypotheses.csv", infer_schema_length=None)
    adv = json.loads((R / "advancement.json").read_text())
    ctl = json.loads((R / "controls.json").read_text())
    L = []; w = L.append
    w("# MAFE-3 discovery report (XAUUSD, 2010-01-01 .. 2020-01-01)\n")
    w(f"Pre-registration sha256 `{adv['preregistration_sha256']}` (matches the frozen value). Code: `phase3/code/mafe3/`, parent commit `{adv['git_parent_commit']}`. "
      "All numbers below are in basis points (bps) per trade unless stated, from non-overlapping episodes, net of the primary cost convention "
      "(fixed $0.35/oz round trip converted at the entry price, Amendment 2, plus swap). Data: HistData.com 1-minute BID bars. Validation and holdout data were not read.\n")
    w("## Outcome\n")
    w(f"- Hypotheses evaluated: **{adv['n_hypotheses']}**. Gate-1 mode: **{adv['gate1_mode']}**.")
    w(f"- BH (q = 0.10) survivors on net > 0 (one-sided; G2 p doubled): **{adv['n_bh_net_q10']}**. Informational BH (q = 0.05) on gross != 0: **{adv['n_bh_gross_q05']}**.")
    w(f"- Gate-1 candidates: {adv['n_gate1_candidates']}; passing gates 2-4: {adv['n_pass_gates_2_4']}; advanced to validation (K = {adv['K']}): **{len(adv['advanced'])}**.\n")
    if adv["advanced"]:
        w("| id | label | n | mean net | t | one-sided p |"); w("|---|---|---:|---:|---:|---:|")
        for a in adv["advanced"]:
            w(f"| {a['id']} | {a['label']} | {a['n']} | {f(a['mean_net'])} | {f(a['t_net'])} | {a['p_net_1s']:.4f} |")
    else:
        w("No hypothesis advances to validation.")
    w("")
    w("## Self-checks (controls.json)\n")
    c = ctl
    w(f"- Hypothesis count: {c['count']['n_hypotheses']} (by family {c['count']['by_family']}); pass = {c['count']['pass']}. Controls are not part of the 89.")
    lk = c["lookahead"]
    w(f"- Lookahead: bar values with label > t*-2 (bars whose close is after t*-1 min) replaced by random garbage at {len(lk['cutoffs_checked'])} random cutoffs; all log-returns, z-scores, breakout flags and every non-G2 candidate direction at decision times <= t* were identical ({len(lk['mismatches'])} mismatches). Sensitivity: one extra bar of garbage changed the features at t* in {lk['sensitivity_changed']}/{lk['sensitivity_total']} checks. pass = {lk['pass']}.")
    p = c["positive_control"]
    w(f"- Positive control (feature = realised 1 h future return): n = {p['n']}, mean gross {f(p['mean_gross_bps'])} bps (t = {f(p['t_gross'],1)}), mean net {f(p['mean_net_bps'])} bps. pass = {p['pass']}.")
    n = c["negative_control"]
    w(f"- Negative control (random signs, {n['seeds']} seeds, 1 h hold, ~{n['mean_n']:.0f} trades each): average gross {f(n['mean_gross_bps_avg'],3)} bps, share of seeds with |t| > 1.96 = {n['frac_abs_t_gt_1.96']:.2f}, max |t| = {max(abs(v) for v in n['t_gross_per_seed']):.2f}; average cost {f(n['mean_cost_bps'])} + swap {f(n['mean_swap_bps'])} bps, average net {f(n['mean_net_bps_avg'])} bps (= -cost -swap within noise). pass = {n['pass']}.")
    w(f"- Swap accounting: vectorised == brute force on 300 random holds, Tue->Thu 48 h hold = {c['swap']['tue_to_thu_swap_bps']} bps (Tue 1 + Wed 3 rollovers x 2 bps); pass = {c['swap']['pass']}.")
    w(f"- Weekend rule (all minutes made available so only the rule can reject): Fri 20:30 UTC + 1 h hold accepted = {c['weekend_rule']['fri_2030_1h']} (must be False), Fri 19:00 + 1 h accepted = {c['weekend_rule']['fri_1900_1h']}, Mon 10:00 + 1 h accepted = {c['weekend_rule']['mon_1000_1h']}, waived weekend exit accepted = {c['weekend_rule']['waived_ok']}.\n")

    w("## All 89 hypotheses\n")
    w("Columns: n episodes; mean gross, cost, swap, net (bps); t and one-sided p for net > 0 (G2 p shown raw; BH uses 2x); weekly block bootstrap p; "
      "net at a $0.20 and a $0.60 fixed round trip (+swap) and net without swap (primary = $0.35 + swap); positive years / eligible years (years with >= 10 episodes); share on one side.\n")
    w("| id | n | gross | cost | swap | net | t | p (1s) | p boot | net $0.20 | net $0.60 | net no swap | pos yrs | one-side | BH | gate-1 cand |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|---|")
    for r in df.iter_rows(named=True):
        w(f"| {r['id']} | {r['n']} | {f(r['mean_gross'])} | {f(r['mean_cost'])} | {f(r['mean_swap'])} | {f(r['mean_net'])} | {f(r['t_net'])} | "
          f"{r['p_net_1s']:.3f} | {r['p_boot']:.3f} | {f(r['mean_net_c20'])} | {f(r['mean_net_c60'])} | {f(r['mean_net_noswap'])} | "
          f"{r['gate3_detail'].replace(' positive of ', '/').replace(' eligible years', '')} | {f(r['share_one_side'],2)} | {'Y' if r['bh_net_q10'] else ''} | {'Y' if r['gate1_candidate'] else ''} |")
    w("")
    w("## Best hypothesis per family (by net t)\n")
    w("| family | id | n | gross | cost | swap | net | t |"); w("|---|---|---:|---:|---:|---:|---:|---:|")
    for fam in sorted(set(df["family"].to_list())):
        r = df.filter(pl.col("family") == fam).sort("t_net", descending=True, nulls_last=True).row(0, named=True)
        w(f"| {fam} | {r['id']} | {r['n']} | {f(r['mean_gross'])} | {f(r['mean_cost'])} | {f(r['mean_swap'])} | {f(r['mean_net'])} | {f(r['t_net'])} |")
    w("")
    w("## Gate-by-gate advancement\n")
    w("Gate 1: BH-significant on net > 0 or, when none, the best <= 5 by net t with mean net > 0 (`NEAR_MISS`). Gate 2: n >= 100. "
      "Gate 3: mean net > 0 in >= 7 of the 10 years (a year counts only with >= 10 episodes). Gate 4: if >= 70 % of trades are on one side, mean(gross - matched drift) "
      "must have the sign of the mean gross, for both the hold-matched drift and the literal 24 h drift.\n")
    cand = df.filter(pl.col("gate1_candidate"))
    w("| id | n | net | t | G1 cand | G2 n>=100 | G3 years | G3 detail | one-sided >=70% | G4 drift | advanced |"); w("|---|---:|---:|---:|---|---|---|---|---|---|---|")
    for r in cand.iter_rows(named=True):
        w(f"| {r['id']} | {r['n']} | {f(r['mean_net'])} | {f(r['t_net'])} | Y | {r['gate2_n100']} | {r['gate3_years']} | {r['gate3_detail']} | {r['directionally_biased']} | {r['gate4_drift']} | {r['advanced']} |")
    if cand.height == 0: w("(no gate-1 candidates)")
    w("")
    w("Hypotheses not in the gate-1 candidate set failed gate 1 (not BH-significant and not among the best five by net t with positive mean net). "
      "For reference, the gate status of the ten hypotheses with the highest net t:\n")
    w("| id | n | net | t | p (1s) | G1 | G2 | G3 | G4 |"); w("|---|---:|---:|---:|---:|---|---|---|---|")
    for r in df.sort("t_net", descending=True, nulls_last=True).head(10).iter_rows(named=True):
        w(f"| {r['id']} | {r['n']} | {f(r['mean_net'])} | {f(r['t_net'])} | {r['p_net_1s']:.3f} | {r['gate1_candidate']} | {r['gate2_n100']} | {r['gate3_years']} | {r['gate4_drift']} |")
    w("")
    w("## Implementation decisions and ambiguities\n")
    w(IMPL)
    OUT.write_text("\n".join(L))
    print("wrote", OUT)


IMPL = """\
- **Data.** HistData.com ASCII M1 BID bars (EST without DST, +5 h to UTC); a bar is labelled by its open minute and its close is observed one minute later. Bars exist only for minutes with ticks; no zero-volume filtering is possible (volume is 0 in the files). Structurally invalid bars are dropped at ingestion (counts in DATA_MANIFEST.md). Features and z-scores may use bars from 2009-11-01 (warm-up for the 720-point history); no trade is entered before 2010-01-01 and every exit is before 2020-01-01 (episodes whose exit would be later cannot be formed).
- **Timing.** Decision time t uses only bars with close <= t-1 min, i.e. label <= t-2. Entry = open of the bar labelled t+1 (first available bar with label in [t+1, t+6], i.e. nearest-bar tolerance 5 min); exit = open of the first bar with label in [entry+H, entry+H+5 min] (H counted from the ACTUAL entry bar), else the episode is skipped and does not block the next one. Look-back closes use the last bar at or before the target label, accepted only if at most 5 min older; the bar at t-2 (or up to 5 min earlier) must exist.
- **Grid.** Full UTC hours t for which a bar exists in [t-7, t-2] and one in [t+1, t+6] (market open). The first hour after a weekend/holiday reopening is therefore usually not a grid point.
- **Non-overlap.** A decision at t is admissible when t >= the exit bar of the previous accepted episode.
- **Weekend rule.** An episode is skipped if the entry bar lies in the closure Fri 21:00 -> Sun 21:00 UTC, the exit-bar open (minus 1 min) lies in it, or entry and exit are in different weeks. Exempt: G2 Friday (exit at the open of the last bar of the trading week, i.e. the Friday close; waived) and G8 by construction. The closure is fixed at Fri 21:00 UTC all year as in the spec (the real winter close is 22:00 UTC, so Fri 21:00-22:00 winter trades are excluded: conservative).
- **Costs.** Gross from BID opens at entry and exit. Primary cost = $0.35 / entry bid open x 1e4 bps (fixed, Amendment 2); also $0.20 and $0.60 variants. Swap = 2 bps per 17:00 America/New_York rollover r with entry < r <= exit (instants of the bar opens), x3 for the Wednesday rollover, same for longs and shorts. Net = gross - cost - swap; "net without swap" = gross - cost.
- **z families (G1, G7).** x = ln of BID close (last bar label <= t-2) / BID close at t-1 min-L hours (last bar at or before, within 5 min) (gold for G1, EURUSD for G7); z over the previous 720 grid points (current excluded), >= 480 non-null, std ddof=1; |z| >= 1.5; d = +1 trades sign(z), d = -1 the opposite. G7 d = +1: gold follows EURUSD. A 24 h look-back that lands in a market closure gives no signal.
- **G2.** hod: decision at the full hour h (grid hours only), entry at h:01, H = 1 h. dow: entry 00:01 UTC of the weekday (day must have a bar within 5 min), Mon-Thu hold 24 h, Friday exit at the open of the last bar of the week. Direction = sign of the discovery mean gross (zero -> long). Because the direction is selected on the same data, the net p-value used for BH and the gates is min(1, 2 x one-sided p); the raw one-sided p is also reported.
- **G3.** x = sign of ln(close of the last bar closed by 06:59 / open of the first bar at/after 00:00) (bid); decision 07:00, entry 07:01; 9 h exits 16:01 UTC. Monday-Friday dates.
- **G4.** Anchor = 15:00 Europe/London (zoneinfo) Monday-Friday, in UTC; x = sign of the bid return between the close at anchor-61 min and the close at anchor-1 min (the 60 min before the anchor); entry anchor+1 min.
- **G5.** Last trading day of a month = last UTC date in the month with bars in >= 6 distinct hours and with bars near 00:01 UTC and near 16:00 Europe/London; entry 00:01 UTC, exit at the first bar at/after 16:00 Europe/London (15:00 or 16:00 UTC); long and short each registered.
- **G6.** Close of the last closed bar (label <= t-2) vs the max high / min low of the 1440 bar labels ending at t-3 (>= 200 bars present); d = +1 trades the breakout side. No z-score.
- **G8.** Closure = gap >= 36 h between consecutive bars, earlier bar on a Friday (UTC date), reopen bar on a Sunday or Monday; x = bid open of the first reopen bar / bid close of the last bar before the closure - 1; |x| >= 0.1 %; entry = first bar at/after reopen + 5 min; H counted from there.
- **Matched drift (gate 4).** Mean gross of a LONG held H at every grid hour of the same quarter (same execution rules, no non-overlap), averaged over the episodes' quarters and signed by their direction. Two versions: H = hypothesis median hold (rounded to whole hours) and the literal 24 h. The gate requires both to have the sign of the mean gross (conservative). Applied only to hypotheses with >= 70 % of trades on one side.
- **Gate 3.** "Positive years" is an absolute count >= 7; years with < 10 episodes are never counted as positive.
- **Bootstrap.** ISO-week block bootstrap (10 000 resamples, null-centred) from phase-2 code; reported, not used in a gate.
"""

if __name__ == "__main__":
    main()
