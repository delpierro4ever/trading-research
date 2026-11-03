"""Compose docs/STAGE2_REPORT.md from results/stage2 (no new computation). Usage (phase3/code): python -m mafe3.stage2.make_report"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]; R = ROOT / "results" / "stage2"

def md(df, floatfmt=3):
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join((f"{v:.{floatfmt}f}" if isinstance(v, float) else str(v)) for v in r.values) + " |")
    return "\n".join(out)

def main():
    orc = pd.read_csv(R / "oracle.csv")
    orc["decision"] = orc.kept.map({True: "kept", False: "excluded"})
    orc = orc[["H_min", "oracle_bps", "cost35_bps", "mean_swap_bps", "threshold_bps", "ratio", "decision"]]
    ic = pd.read_csv(R / "ic.csv"); top = pd.read_csv(R / "ic_top_by_concept.csv")
    top = top[["H", "concept", "feature", "ic", "mean_year_ic", "t_years", "years_same_sign"]]
    cnt = json.loads((R / "trackA_candidate_count.json").read_text()); fun = json.loads((R / "trackA_funnel.json").read_text())
    ctrlA = json.loads((R / "trackA_controls.json").read_text()); ctrlB = json.loads((R / "trackB_controls.json").read_text())
    A = pd.read_csv(R / "trackA_discA.csv")
    bestA = A.sort_values("p").head(10)[["spec", "H", "d", "n", "gross", "cost", "swap", "net35", "net50", "t", "p", "days"]]
    S = pd.read_csv(R / "trackB_summary.csv"); W = pd.read_csv(R / "trackB_walkforward.csv"); I = pd.read_csv(R / "trackB_importance.csv")
    Sg = S[["model", "H", "n", "gross", "cost", "swap", "net35", "net50", "t", "p_boot", "pos_years", "days", "pass"]]
    Wy = W.pivot_table(index=["model", "H"], columns="year", values="net35").round(2).reset_index()
    Wn = W.pivot_table(index=["model", "H"], columns="year", values="n").astype(int).reset_index()
    Wc = W.groupby(["model", "H"]).pred_corr.mean().round(4).reset_index()
    lg = I[I.model == "lgbm"]
    imp_all = lg.groupby("feature").importance.mean().sort_values(ascending=False).head(10).reset_index()
    imp_h = {H: g.sort_values("importance", ascending=False).head(10) for H, g in lg.groupby("H")}
    rd = I[I.model == "ridge"]
    rd_h = {H: g.sort_values("importance", ascending=False).head(6) for H, g in rd.groupby("H")}
    txt = f"""# MAFE-3 Stage 2 report — machine-native pattern search + combined model (XAUUSD)

Pre-registration: `docs/STAGE2_PREREGISTRATION.md` (sha256 `4adad97f739c04645fbb4bdca431594ec96789b44c29a7b8af2331c56ba6b080`, verified at run time), features frozen in
`docs/STAGE2_FEATURES.md`. Data: HistData M1 BID, discovery 2010–2019 only. **The validation window (2020–2022) and the holdout (2023+) were not read in stage 2:
neither track produced a candidate that reached validation.** All numbers are bps per trade, non-overlapping episodes, cost = $0.35/oz round trip (robustness $0.50) + swap.

## Step 0 — oracle exclusion (discovery, all valid 5-minute grid points)

Oracle = mean over grid points of max(MFE long, MFE short) over the hold, in bps; kept if oracle ≥ 4 × (cost $0.35 + mean swap).

{md(orc)}

Kept horizons: **30, 60, 240 min**. H = 5 and 15 are excluded (15 min narrowly: ratio 3.72 < 4).

## Section 6 — gross information: Spearman IC per concept (discovery 2010–2019)

IC between the z-scored feature and the long gross forward return (pooled, 5-minute grid with overlapping horizons, so naive significance is meaningless; stability is judged by
the sign across the 10 calendar years). Strongest |IC| per concept and H (full table: `results/stage2/ic.csv`):

{md(top, 4)}

Reading: the information is small (|IC| ≤ 0.045) but its sign is stable in all 10 years at 30–60 min, and it is dominated by *mean reversion* (negative IC for speed, displacement, location in the range, signed rejection). At 240 min ICs are smaller and
less stable. The time-of-day cosine reflects the intraday drift profile.

## Track A — mechanical search

Candidates: {cnt['n_signal_masks']} signal definitions ({cnt['by_kind']['S']} single-feature tails, {cnt['by_kind']['P']} cross-concept pair signals (484 pairs × 4 quintile-tail combinations), {cnt['by_kind']['C']} session × feature) × {cnt['n_horizons']} horizons × 2 directions = **{cnt['n_candidates']}**
(recorded in the commit before any evaluation). Thresholds were fitted on discovery-A (2010–2014) only.

| step | count |
|---|---:|
| candidates | {fun['n_candidates']} |
| with n ≥ 100 non-overlapping episodes in A | {fun['n_with_n_ge_100']} |
| net($0.35) > 0 in A | {fun['n_net35_pos']} |
| smallest one-sided p | {fun['min_p']:.4f} |
| BH q = 0.10 survivors (m_A) | {fun['n_bh']} |
| after n ≥ 100, net($0.50) > 0, ≥ 30 days | {fun['m_A']} |
| B replication / collapse / validation | not run (no A-survivor) |

Ten most significant candidates in A (none survives BH; t-test p; note the repeated "C|1|·|hi20, d = −1, H = 240" pattern = short in the London session after a strong up-move, i.e. the same underlying 2010–2014 gold weakness):

{md(bestA)}

Controls (`trackA_controls.json`): positive (planted feature = noisy realised 30 min return) n ≈ 20 600, gross +6.4 bps, net +3.9, p < 1e-200, pass = {ctrlA['positive']['pass']};
negative (rows of the feature matrix permuted, the full {cnt['n_candidates']} candidates re-searched): mean gross {ctrlA['negative']['mean_gross']:.3f} bps, mean net {ctrlA['negative']['mean_net35']:.2f}, BH survivors {ctrlA['negative']['n_bh']}, pass = {ctrlA['negative']['pass']}.

## Track B — combined model (walk-forward 2013–2019, train on 2010…y−1, 1-day purge)

Pooled 2013–2019. Gate: n ≥ 200, net($0.35) > 0 and net($0.50) > 0, weekly-block-bootstrap one-sided p < 0.05/6 = 0.0083, ≥ 5 of 7 years positive.

{md(Sg)}

Per-year net($0.35) of the traded episodes:

{md(Wy, 2)}

Number of trades per year:

{md(Wn, 0)}

Mean out-of-sample correlation of the prediction with the realised H-return (all grid points, per year, averaged over 2013–2019):

{md(Wc, 4)}

The models carry a small positive amount of information (corr ≈ 0.016–0.019) and the trades they select earn a positive **gross** edge of +0.8 to +1.7 bps, which is below the 2.6 bps cost. **No model × H passes (0 of 6).**
Controls (`trackB_controls.json`): planted feature (H = 60): ridge net +1.63, LightGBM net +2.14, pass = {ctrlB['positive_pass']}; permuted inputs: nothing passes and nothing is significant, pass = {ctrlB['negative_pass']}.

### Importances

LightGBM gain (normalised, mean over the 7 walk-forward fits), top 10 over the three horizons:

{md(imp_all, 4)}

By horizon (top 10, gain share): """
    for H, g in imp_h.items(): txt += f"\n- H = {H}: " + ", ".join(f"{a} {b:.3f}" for a, b in zip(g.feature, g.importance))
    txt += "\n\nRidge (mean |standardised coefficient| over the 7 fits, bps per 1 sd), top 6:"
    for H, g in rd_h.items(): txt += f"\n- H = {H}: " + ", ".join(f"{a} {b:.2f}" for a, b in zip(g.feature, g.importance))
    txt += """

The final 2010–2019 models (frozen, saved outside the repo; importances in `results/stage2/final_lgbm_importance_H*.csv`, `final_ridge_coef_H*.csv`) were fitted but **not applied to any later data**.
LightGBM spends its splits mostly on spiky range/touch/location features (c_loc60c, a_th, a_tl, l_pdl, l_pdh, r_fail) and on the time of day; ridge puts its weight on the short-term speed
contrast (s_5, s_acc, s_30), i.e. the same short-horizon mean reversion visible in the IC table.

## Validation and holdout

Not run. Track A had no discovery-A survivor; Track B had no model passing the discovery gate. Section 5 therefore leaves the holdout sealed. `phase3/results/stage2/` contains no validation output.

## Implementation decisions (all made before outcomes unless noted; conservative reading)

1. Features: see `STAGE2_FEATURES.md` (38 columns; ridge inputs = 45 after one-hot encoding of session and weekday). σ_k = per-minute rms of 1 m returns; "its 20th percentile" of the compression ratio = trailing 20 trading days, so it is causal; time features are not z-scored; sessions: 21–24 UTC belongs to none.
2. Grid: 5-minute grid points with a gold bar in the 6 minutes ending at t−2; entries/exits/weekend rule/swap through the stage-1 engine (`resolve`, `swap_bps`); the oracle uses BID highs/lows over [entry, entry+H).
3. Track A: both tails of each single feature (≤ p10, ≥ p90) and the quintile tails for pairs/context; direction is a separate candidate; BH on the t-test one-sided p of net($0.35) > 0 in A; the A gate also required ≥ 30 distinct days; for B and validation the p used would have been max(t-test, weekly block bootstrap) (conservative; never reached). Near-duplicate collapse: overlap = share of one candidate's episodes that intersect the other's, collapse if either direction exceeds 50 %.
4. Track B: ridge intercept unpenalised, inputs z-clipped at ±5 and missing → 0; LightGBM native API, `bagging_freq = 1` (needed to activate bagging), NaN native; the "expected swap" in the trading rule is the deterministic rollover charge of the planned hold; greedy non-overlap pooled across years; year positive = mean net($0.35) > 0 among years with ≥ 1 trade.
5. Bug fixes unrelated to outcomes: LightGBM's sklearn wrapper needed scikit-learn, so the native `lgb.train` API was used (before any real Track B run); the negative-control criterion of Track B was rewritten after the first control run (the first criterion mis-specified noise tolerance for n = 87 trades); the real discovery runs were executed once each.
"""
    (ROOT / "docs" / "STAGE2_REPORT.md").write_text(txt)

if __name__ == "__main__":
    main()
