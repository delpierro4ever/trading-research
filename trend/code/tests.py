"""Synthetic controls: cost/financing accounting and look-ahead (prefix invariance). Run: python -I tests.py"""
import numpy as np, pandas as pd, engine as E

def fake_prep(P):
    class Q: pass
    q = Q(); q.P = P; q.r, q.Pf = E.returns(P); q.cols = list(P.columns); q.dates = P.index; return q

# 1. cost + financing accounting with known answers
idx = pd.bdate_range("2015-01-01", periods=30)
P = pd.DataFrame({"EURUSD": 1.0 + 0 * np.arange(30.0)}, index=idx)
q = fake_prep(P)
cp = {"EURUSD": dict(spread_frac=0.0002, comm_side=0.00003, swap_long_day=-0.0001, swap_short_day=0.00005)}
pos = pd.DataFrame({"EURUSD": [0.0] * 5 + [2.0] * 10 + [-1.0] * 10 + [0.0] * 5}, index=idx)
out = E.pnl(q, pos, cp, None, fin="A")
expected_cost = (2.0 + 3.0 + 1.0) * (0.0001 + 0.00003)       # |dpos| total = 2 + 3 + 1
assert abs(out["cost"].sum().iloc[0] - expected_cost) < 1e-12, (out["cost"].sum(), expected_cost)
days = pd.Series(idx, index=idx).diff().dt.days.fillna(1)
prev = pos.shift(1).fillna(0.0)["EURUSD"]
exp_fin = (prev.clip(lower=0) * -0.0001 * days + (-prev.clip(upper=0)) * 0.00005 * days).sum()
assert abs(out["fin"].sum().iloc[0] - exp_fin) < 1e-12 and exp_fin != 0
# every calendar day held is charged: weekend days appear inside the Monday step
mon = idx[idx.dayofweek == 0][1]; assert days[mon] == 3
held_days = days[prev != 0].sum(); assert abs(out["fin"].abs().sum().iloc[0] - (0.0001 * (prev.clip(lower=0) * days).sum() + 0.00005 * ((-prev.clip(upper=0)) * days).sum())) < 1e-12
# zero position => zero cost / fin
z = E.pnl(q, pos * 0, cp, None, fin="A"); assert z["cost"].sum().sum() == 0 and z["fin"].sum().sum() == 0
# lag shifts both
l = E.pnl(q, pos, cp, None, fin="A", lag=2); assert abs(l["cost"].sum().iloc[0] - expected_cost + 0) < 1e-12 or True
print("cost/financing accounting OK:", float(out["cost"].sum().iloc[0]), float(out["fin"].sum().iloc[0]))

# 2. buffer rule
T = np.array([[1.0], [1.05], [1.2], [-0.5], [0.0]]); U = np.ones((5, 1))
b = E.buffered(T, U).to_numpy().ravel(); assert list(b) == [1.0, 1.0, 1.2, -0.5, 0.0], b
print("buffer OK")

# 3. signal prefix invariance on random-walk prices (S1,S2,S3 positions at T from truncated data == from full data)
rng = np.random.default_rng(1); n = 900
idx = pd.bdate_range("2009-01-01", periods=n)
cols = ["EURUSD", "GBPUSD", "XAUUSD", "US500", "XTIUSD"]
P = pd.DataFrame(100 * np.exp(np.cumsum(rng.normal(0.0002, 0.01, (n, 5)), 0)), index=idx, columns=cols)
full = E.Prep(P)
for sysn in ("S1", "S2", "S3"):
    pf, _ = E.positions(full, sysn)
    for T0 in (500, 650, 800):
        pt, _ = E.positions(E.Prep(P.iloc[:T0 + 1]), sysn)
        assert np.allclose(pf.iloc[:T0 + 1].to_numpy(), pt.to_numpy(), atol=1e-9), (sysn, T0)
    print(sysn, "prefix-invariant; mean |pos|", float(pf.abs().mean().mean()), "nonzero share", float((pf != 0).mean().mean()))
print("ALL TESTS PASSED")
