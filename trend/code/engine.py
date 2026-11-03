"""TREND backtest engine (daily, vol-targeted trend systems S1/S2/S3). Read PREREG.md for the definitions. Data seal: only <=2022-12-31 is ever loaded here."""
import json, numpy as np, pandas as pd

DAILY = "/home/ubuntu/mafe-data/trend/daily/dev_val.parquet"
INFO = "/home/ubuntu/mafe-research-archive/trend/out/broker_symbolinfo.json"
RAW = "/home/ubuntu/mafe-data/trend/raw"
SEAL = pd.Timestamp("2022-12-31")
CLASSES = {"FX": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP", "AUDJPY", "EURCHF"],
           "METALS": ["XAUUSD", "XAGUSD"], "INDICES": ["US500", "USTEC", "DE40", "UK100", "JP225"], "ENERGY": ["XTIUSD", "XBRUSD"], "CRYPTO": ["BTCUSD", "ETHUSD"]}
MAIN = [i for c in ("FX", "METALS", "INDICES", "ENERGY") for i in CLASSES[c]]
CLS = {i: c for c, l in CLASSES.items() for i in l}
V_TARGET, M_CAP, BUFFER, NMIN = 0.12, 6.0, 0.10, 260

def load_prices(universe=None):
    p = pd.read_parquet(DAILY)
    assert p.index.max() <= SEAL, "sealed data present"
    p = p.loc[:, [c for c in (universe or MAIN) if c in p.columns]]
    return p.astype(float)

# ---------------- costs / financing parameters ----------------
def cost_params():
    d = json.load(open(INFO))["symbols"]; out = {}
    for n, s in d.items():
        mid = (s["bid"] + s["ask"]) / 2
        calc = s["swap_calc"]
        if calc == "Percentage": sl, ss = s["swap_long"] / 100 / 365, s["swap_short"] / 100 / 365
        else: sl, ss = s["swap_long"] * s["pip_size"] / mid, s["swap_short"] * s["pip_size"] / mid
        comm = s["commission"] * 1e-6 if s["commission_type"] == "UsdPerMillionUsdVolume" else 0.0
        out[n] = dict(spread_frac=s["spread"] / mid, comm_side=comm, swap_long_day=sl, swap_short_day=ss, mid=mid)
    return out

def load_rates(index, end="2022-12-31"):
    """daily decimal rates per currency (ffilled). USD from DTB3 (daily); others OECD/FRED 3m interbank (monthly)."""
    def rd(fn):
        s = pd.read_csv(f"{RAW}/{fn}", index_col=0, parse_dates=True).iloc[:, 0]
        return pd.to_numeric(s, errors="coerce").dropna() / 100
    r = {"USD": rd("FRED_DTB3.csv")}
    for c, sid in (("EUR", "EZ"), ("GBP", "GB"), ("JPY", "JP"), ("AUD", "AU"), ("CAD", "CA"), ("CHF", "CH"), ("NZD", "NZ")):
        r[c] = rd(f"FRED_IR3TIB01{sid}M156N.csv")
    full = pd.date_range("2000-01-01", end)
    return pd.DataFrame({c: s.reindex(full.union(s.index)).ffill().reindex(index) for c, s in r.items()})

# ---------------- signals ----------------
def returns(P):
    """P: price frame with NaN for holidays/not-yet-listed. Returns carry-forward simple returns (NaN before first valid)."""
    Pf = P.ffill()
    return Pf.pct_change(fill_method=None), Pf

def ewma_vol(r):
    var = (r ** 2).ewm(span=25, adjust=False, min_periods=20).mean() * 252
    v = np.sqrt(var)
    floor = 0.5 * v.rolling(252, min_periods=60).mean()
    return np.maximum(v, floor).where(v.notna())

def n_valid(P):
    return P.notna().cumsum()

def s1_signal(Pf, lb=252):
    return np.sign(Pf / Pf.shift(lb) - 1)

def s2_signal(Pf, sig, mult=1.0, spans=((16, 64), (32, 128), (64, 256)), scalars=(3.75, 2.65, 1.87)):
    fcs = []
    for (f, s), k in zip(spans, scalars):
        ef = Pf.ewm(span=max(2, int(round(f * mult))), adjust=False).mean(); es = Pf.ewm(span=int(round(s * mult)), adjust=False).mean()
        fcs.append((k * (ef - es) / (Pf * sig / np.sqrt(252))).clip(-20, 20))
    return (sum(fcs) / len(fcs)).clip(-20, 20) / 10.0

def s3_signal(Pf, ent=55, ext=20):
    hi_e, lo_e = Pf.shift(1).rolling(ent).max(), Pf.shift(1).rolling(ent).min()
    hi_x, lo_x = Pf.shift(1).rolling(ext).max(), Pf.shift(1).rolling(ext).min()
    out = np.zeros(Pf.shape); X = Pf.to_numpy(); HE, LE, HX, LX = (a.to_numpy() for a in (hi_e, lo_e, hi_x, lo_x))
    for j in range(X.shape[1]):
        st = 0
        for t in range(X.shape[0]):
            x = X[t, j]
            if np.isnan(x) or np.isnan(HE[t, j]): st = 0; out[t, j] = 0; continue
            if st == 1 and x < LX[t, j]: st = 0
            elif st == -1 and x > HX[t, j]: st = 0
            if st == 0:
                if x > HE[t, j]: st = 1
                elif x < LE[t, j]: st = -1
            out[t, j] = st
    return pd.DataFrame(out, index=Pf.index, columns=Pf.columns)

def atr_sigma(Pf, n=20):
    """ATR proxy from closes: mean |dClose| over n days, as % of price, converted to annualised sigma-equivalent (x sqrt(252) x 1.2533)."""
    a = (Pf.diff().abs().rolling(n).mean() / Pf)
    return a * np.sqrt(252) * 1.2533

# ---------------- portfolio ----------------
def rolling_cov(r, win=250):
    X = r.fillna(0.0).to_numpy(); T, n = X.shape
    cs_x = np.vstack([np.zeros(n), np.cumsum(X, 0)])
    outer = X[:, :, None] * X[:, None, :]
    cs_o = np.concatenate([np.zeros((1, n, n)), np.cumsum(outer, 0)], 0)
    cov = np.zeros((T, n, n))
    for t in range(T):
        lo = max(0, t + 1 - win); m = t + 1 - lo
        if m < 60: continue
        sx = cs_x[t + 1] - cs_x[lo]; so = cs_o[t + 1] - cs_o[lo]
        cov[t] = (so - np.outer(sx, sx) / m) / (m - 1) * 252
    return cov

def risk_shares(avail):
    """b_i,t: equal across classes with >=1 available instrument, equal within class."""
    b = pd.DataFrame(0.0, index=avail.index, columns=avail.columns)
    cl = pd.Series({c: CLS[c] for c in avail.columns})
    ncls = pd.DataFrame({k: avail.loc[:, cl[cl == k].index].any(axis=1) for k in cl.unique()}).sum(axis=1)
    for k in cl.unique():
        cols = cl[cl == k].index; n_in = avail[cols].sum(axis=1).replace(0, np.nan)
        b[cols] = avail[cols].astype(float).div(n_in, axis=0).div(ncls.replace(0, np.nan), axis=0).fillna(0.0)
    return b

class Prep:
    """Per-universe cached quantities."""
    def __init__(self, P, nmin=NMIN):
        self.P = P; self.r, self.Pf = returns(P); self.sig = ewma_vol(self.r)
        fresh = P.notna().rolling(10, min_periods=1).max() > 0      # instrument leaves the book if its feed ends (e.g. truncated DE40)
        self.avail = (n_valid(P) >= nmin) & self.sig.notna() & fresh
        self.b = risk_shares(self.avail); self.cov = rolling_cov(self.r); self.cols = list(P.columns)
        self.dates = P.index

def buffered(T, U, buf=BUFFER):
    T = np.nan_to_num(T); U = np.nan_to_num(U); out = np.zeros_like(T)
    for j in range(T.shape[1]):
        cur = 0.0
        for t in range(T.shape[0]):
            tgt = T[t, j]
            if tgt * cur < 0 or abs(tgt - cur) > buf * U[t, j]:
                cur = tgt
            out[t, j] = cur
    return pd.DataFrame(out, index=None)

def positions(prep, system, mult=1.0, literal=False, buf=BUFFER, **kw):
    """Returns DataFrame of positions (fraction of equity) held from close t to close t+1."""
    Pf, avail, b, sig = prep.Pf, prep.avail, prep.b, prep.sig
    if system == "S1": f = s1_signal(Pf, int(round(252 * mult))); s = sig
    elif system == "S2": f = s2_signal(Pf, sig, mult); s = sig
    elif system == "S3": f = s3_signal(Pf, int(round(55 * mult)), int(round(20 * mult))); s = atr_sigma(Pf)
    else: raise ValueError(system)
    ok = avail & s.notna() & f.notna() & (s > 0)
    if literal:   # S3 literal: 0.5% equity risk per ATR(=sigma/sqrt(252)/1.2533) per unit, no portfolio scaling
        unit = (0.005 / (s / np.sqrt(252) / 1.2533)).where(ok, 0.0)
        T = (f * unit).where(ok, 0.0)
    else:
        raw_unit = (b / s).where(ok, 0.0)
        raw = (f * raw_unit).where(ok, 0.0).to_numpy(); X = np.nan_to_num(raw)
        pv = np.einsum("ti,tij,tj->t", X, prep.cov, X)
        m = np.where(pv > 1e-12, V_TARGET / np.sqrt(np.maximum(pv, 1e-12)), 0.0)
        # unit-position scale uses the same multiplier; if raw book is flat (S3) fall back to the all-ones book to keep m defined
        U1 = raw_unit.to_numpy(); pv1 = np.einsum("ti,tij,tj->t", U1, prep.cov, U1)
        m = np.where(pv > 1e-12, m, np.where(pv1 > 1e-12, V_TARGET / np.sqrt(np.maximum(pv1, 1e-12)), 0.0))
        m = np.minimum(m, M_CAP)
        unit = pd.DataFrame(U1 * m[:, None], index=Pf.index, columns=Pf.columns)
        T = pd.DataFrame(X * m[:, None], index=Pf.index, columns=Pf.columns)
    out = buffered(T.to_numpy(), unit.to_numpy(), buf)
    out.index = Pf.index; out.columns = Pf.columns
    return out, unit

def bh_positions(prep):
    ok = prep.avail & (prep.sig > 0)
    raw = (prep.b / prep.sig).where(ok, 0.0).to_numpy(); pv = np.einsum("ti,tij,tj->t", raw, prep.cov, raw)
    m = np.minimum(np.where(pv > 1e-12, V_TARGET / np.sqrt(np.maximum(pv, 1e-12)), 0.0), M_CAP)
    return pd.DataFrame(raw * m[:, None], index=prep.dates, columns=prep.cols)

# ---------------- P&L ----------------
def pnl(prep, pos, cparams, rates, spread_mult=1.0, comm_mult=1.0, fin="A", lag=0):
    """Returns dict of DataFrames (per instrument, daily): gross, cost, fin, net."""
    if lag: pos = pos.shift(lag).fillna(0.0)
    cols = prep.cols; r = prep.r.fillna(0.0)
    hs = np.array([cparams[c]["spread_frac"] / 2 * spread_mult + cparams[c]["comm_side"] * comm_mult for c in cols])
    dpos = pos.diff(); dpos.iloc[0] = pos.iloc[0]
    cost = dpos.abs() * hs
    prev = pos.shift(1).fillna(0.0)
    gross = prev * r
    days = pd.Series(prep.dates, index=prep.dates).diff().dt.days.fillna(1).to_numpy()[:, None]
    if fin == "A":
        sl = np.array([cparams[c]["swap_long_day"] for c in cols]); ss = np.array([cparams[c]["swap_short_day"] for c in cols])
        fr = prev.clip(lower=0) * sl + (-prev.clip(upper=0)) * ss
        fr = fr * days
    else:
        rf = rates["USD"].to_numpy()[:, None]
        fr = pd.DataFrame(0.0, index=prep.dates, columns=cols)
        for j, c in enumerate(cols):
            pl, ps = prev[c].clip(lower=0).to_numpy(), (-prev[c].clip(upper=0)).to_numpy()
            if CLS[c] == "FX":
                base, quote = c[:3], c[3:]
                diff = (rates[base] - rates[quote]).to_numpy()
                fr[c] = (pl * (diff - 0.01) + ps * (-diff - 0.01)) / 365 * days[:, 0]
            else:
                rr = rates["USD"].to_numpy()
                fr[c] = (-pl * (rr + 0.025) + ps * (rr - 0.025)) / 365 * days[:, 0]
        fr = fr.fillna(0.0)
    net = gross - cost + fr
    return dict(gross=gross, cost=cost, fin=fr, net=net)

# ---------------- metrics ----------------
def equity_stats(x, ppy=252):
    x = pd.Series(x).dropna()
    if len(x) < 30: return {}
    eq = (1 + x).cumprod(); yrs = len(x) / ppy
    dd = eq / eq.cummax() - 1
    roll = (eq / eq.shift(252) - 1).dropna()
    m = (1 + x).groupby([x.index.year, x.index.month]).prod() - 1
    return dict(cagr=eq.iloc[-1] ** (1 / yrs) - 1, vol=x.std() * np.sqrt(ppy), sharpe=x.mean() / x.std() * np.sqrt(ppy) if x.std() > 0 else np.nan,
                maxdd=dd.min(), worst12m=roll.min() if len(roll) else np.nan, pct_pos_months=(m > 0).mean(), n_days=len(x))

def turnover(pos, idx):
    return pos.diff().abs().loc[idx].sum(axis=1).sum() / (len(idx) / 252)

def boot_sharpe(x, n=10000, block=20, seed=20261015):
    x = np.asarray(pd.Series(x).dropna()); T = len(x); rng = np.random.default_rng(seed); p = 1.0 / block
    idx = np.empty((n, T), dtype=np.int32); idx[:, 0] = rng.integers(0, T, n)
    new = rng.random((n, T)) < p; rs = rng.integers(0, T, (n, T))
    for t in range(1, T):
        idx[:, t] = np.where(new[:, t], rs[:, t], (idx[:, t - 1] + 1) % T)
    s = x[idx]; sh = s.mean(1) / s.std(1, ddof=1) * np.sqrt(252)
    return dict(p05=float(np.percentile(sh, 5)), p50=float(np.percentile(sh, 50)), p95=float(np.percentile(sh, 95)), se=float(sh.std()))

WINDOWS = {"DEV": ("2009-01-01", "2018-12-31"), "VAL": ("2019-01-01", "2022-12-31")}
def win(df, w):
    a, b = WINDOWS[w]; return df.loc[a:b]
