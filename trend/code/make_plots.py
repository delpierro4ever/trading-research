import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT = "/home/ubuntu/mafe-research-archive/trend/out"; BIG = "/home/ubuntu/mafe-data/trend/out"
C = {"S1": "#2a6fdb", "S2": "#d9730d", "S3": "#6b6b6b"}
net = pd.read_parquet(BIG + "/net_returns.parquet"); net.columns = pd.MultiIndex.from_tuples(net.columns) if not isinstance(net.columns, pd.MultiIndex) else net.columns
net = net.loc["2009-01-01":"2022-12-31"]
def style(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e6e6e6", lw=0.8); ax.set_axisbelow(True)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
for ax, (k, t) in zip(axs, (("cons", "Conservative costs (x1.5, financing B)"), ("std", "Standard costs (x1.0, financing A)"))):
    for s in ("S1", "S2", "S3"):
        eq = (1 + net[(s, k)]).cumprod(); ax.plot(eq.index, eq, color=C[s], lw=1.6, label=s); ax.text(eq.index[-1], eq.iloc[-1], f" {s}", color="#333", va="center", fontsize=9)
    ax.axvline(pd.Timestamp("2019-01-01"), color="#999", ls=":", lw=1); ax.text(pd.Timestamp("2019-02-01"), ax.get_ylim()[0] if False else 0.55, "validation", fontsize=8, color="#666")
    ax.set_title(t, fontsize=10, loc="left"); style(ax); ax.set_yscale("log"); ax.set_ylim(0.45, 2.2); ax.set_yticks([0.5, 0.75, 1, 1.5, 2]); ax.set_yticklabels(["0.5", "0.75", "1", "1.5", "2"])
axs[0].set_ylabel("Equity (start = 1, 12% vol target)"); axs[0].legend(frameon=False, loc="upper left", fontsize=8)
fig.tight_layout(); fig.savefig(OUT + "/equity_curves.png", dpi=130); plt.close(fig)
fig, ax = plt.subplots(figsize=(12, 3.8)); w = 0.27
for i, s in enumerate(("S1", "S2", "S3")):
    d = pd.read_csv(f"{OUT}/per_year_{s}.csv", index_col=0); ax.bar(d.index + (i - 1) * w, d["net_cons"] * 100, w - 0.03, color=C[s], label=s)
ax.axhline(0, color="#444", lw=0.8); ax.set_ylabel("Net return, conservative (%)"); ax.legend(frameon=False, ncol=3, fontsize=8); style(ax); ax.set_xticks(range(2009, 2023))
fig.tight_layout(); fig.savefig(OUT + "/per_year.png", dpi=130); plt.close(fig)
m = pd.read_parquet(BIG + "/m3_returns_S1_main21.parquet"); fig, ax = plt.subplots(figsize=(7, 4))
for c, col in (("500_500_cons", "#d9730d"), ("2000_500_cons", "#2a6fdb"), ("10000_500_cons", "#6b6b6b")):
    eq = (1 + m[c].fillna(0)).cumprod(); ax.plot(eq.index, eq, color=col, lw=1.5, label=f"${c.split('_')[0]}")
ax.set_ylabel("Equity / start (S1, real lots, conservative)"); ax.legend(frameon=False, fontsize=8); style(ax); fig.tight_layout(); fig.savefig(OUT + "/m3_equity_S1.png", dpi=130)
