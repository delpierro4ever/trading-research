import pandas as pd, os
R = os.path.join(os.path.dirname(__file__), "..", "results")
p = pd.read_csv(f"{R}/m3_period_table.csv"); b = pd.read_csv(f"{R}/m3_bootstrap_ci.csv")
p["period"] = p.period.astype(str); b["period"] = b.period.astype(str)
x = p[(p.reading == 5) & (p.period_type.isin(["quarter", "year"]))].merge(b[(b.reading == 5)][["period", "period_type", "gross_lo", "gross_hi"]], on=["period", "period_type"])
rows = ["| Period | Trades | Gross P&L (USD, 0.001 BTC) | Gross/trade bps [95% CI] | Cost c1 (USD) | Cost/trade c1 bps (USD) | Net c1 (USD) | Net/trade c1 bps | Net/trade c2 bps | Net/trade c3 bps |", "|---|---:|---:|---|---:|---|---:|---:|---:|---:|"]
for _, r in x.iterrows():
    rows.append(f"| {r.period} | {int(r.N):,} | {r.gross_usd:.1f} | {r.gross_bps_per_trade:.3f} [{r.gross_lo:.2f}, {r.gross_hi:.2f}] | {r.cost_c1_usd:.1f} | {r.cost_c1_bps_per_trade:.3f} ({r.cost_c1_usd_per_trade:.4f}) | {r.net_c1_usd:.1f} | {r.net_c1_bps_per_trade:.3f} | {r.net_c2_bps_per_trade:.2f} | {r.net_c3_bps_per_trade:.3f} |")
open(f"{R}/table_R5_periods.md", "w").write("\n".join(rows)); print("\n".join(rows))
s = pd.read_csv(f"{R}/m3_shift_share_c1.csv"); s = s[s.reading == 5][["A", "B", "N_A", "N_B", "dNet", "term_trades", "term_gross", "term_cost", "term_interaction"]]
rows = ["| A → B | ΔNet (bps·trades) | trade-count term | gross/trade term | cost/trade term | interaction |", "|---|---:|---:|---:|---:|---:|"]
for _, r in s.iterrows(): rows.append(f"| {r.A} → {r.B} | {r.dNet:,.0f} | {r.term_trades:,.0f} | {r.term_gross:,.0f} | {r.term_cost:,.0f} | {r.term_interaction:,.0f} |")
open(f"{R}/table_R5_shiftshare.md", "w").write("\n".join(rows)); print("\n".join(rows))
