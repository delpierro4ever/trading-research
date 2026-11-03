"""Discovery table (64 primary cells) + F4 conditional policy cells (64), BH over 128, pass flags, frozen candidates."""
import os, sys, json, glob, numpy as np, pandas as pd, stats as S
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
T2023 = int(pd.Timestamp("2023-01-01", tz="UTC").timestamp()) // 60
def load(tag="disc"):
    return pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{S.EV}/{tag}_*.parquet"))], ignore_index=True)
if __name__ == "__main__":
    ev = load(); vol_edges = json.load(open(f"{R}/vol_edges.json"))
    fit_all = ev[ev.t < T2023]; act_e = S.act_edges(fit_all)
    prim, f4, frozen_f4 = [], [], {}
    for cid, fam, tg, H in S.cell_defs():
        d = S.prep(ev[(ev.trig == tg) & (ev.H == H)], fam)
        r = dict(cell=cid, fam=fam, trig=tg, H=H, **S.cell_stats(d))
        if len(d):
            m, lo, hi, p = S.boot(d.net.values, d.cl.values); r.update(ci_lo=lo, ci_hi=hi, p=p)
            yb, cp = S.pass_flags(d); r.update(buckets_pos=yb, coins_pos=cp)
            # stress/maker significance not tested; report means
            r["abs_cost_ratio_oracle"] = r["mfe"] / r["cost"]
        else: r.update(p=1.0, buckets_pos=0, coins_pos=0)
        prim.append(r)
        # ---- F4
        fit = d[d.t < T2023].copy(); te = d[d.t >= T2023].copy()
        q = dict(cell=cid, fam=fam, trig=tg, H=H, n_fit=len(fit), n_test=len(te))
        if len(fit) >= 30 and len(te):
            fit["bin"] = S.bins(fit, vol_edges, act_e); te["bin"] = S.bins(te, vol_edges, act_e)
            gm, cm, nn = S.fit_model(fit)
            sel_bins = np.flatnonzero(gm - cm > 0); te["pg"] = gm[te.bin]; te["pc"] = cm[te.bin]
            te["c2"] = te.cost + te.fund
            q["corr_gross"] = np.corrcoef(te.pg, te.gross)[0, 1] if te.pg.std() > 0 else np.nan
            q["corr_cost"] = np.corrcoef(te.pc, te.c2)[0, 1] if te.pc.std() > 0 else np.nan
            q["uncond_net_2023"] = te.net.mean()
            sel = te[te.bin.isin(sel_bins)]; q["n_sel"] = len(sel); q["sel_bins"] = len(sel_bins)
            if len(sel):
                m, lo, hi, p = S.boot(sel.net.values, sel.cl.values)
                q.update(net=m, ci_lo=lo, ci_hi=hi, p=p, gross=sel.gross.mean(), cost=sel.cost.mean(), net15=sel.net15.mean(),
                         qtr_pos=int((sel.groupby("q").net.mean().reindex([1, 2, 3, 4]) > 0).sum()))
            else: q.update(p=1.0, qtr_pos=0)
            frozen_f4[cid] = dict(sel_bins=[int(b) for b in sel_bins], gm=gm.tolist(), cm=cm.tolist())
        else: q.update(p=1.0, n_sel=0, qtr_pos=0)
        f4.append(q)
    P = pd.DataFrame(prim); Fq = pd.DataFrame(f4)
    allp = np.r_[P.p.values, Fq.p.values]; adj, sig = S.bh(allp)
    P["q_bh"] = adj[:64]; P["bh_sig"] = sig[:64]; Fq["q_bh"] = adj[64:]; Fq["bh_sig"] = sig[64:]
    P["PASS"] = P.bh_sig & (P.buckets_pos >= 3) & (P.coins_pos >= 6) & (P.n >= 100)
    Fq["PASS"] = Fq.bh_sig & (Fq.n_sel >= 60) & (Fq.qtr_pos >= 3)
    P.to_csv(f"{R}/discovery_cells.csv", index=False); Fq.to_csv(f"{R}/f4_cells.csv", index=False)
    json.dump(dict(act_edges=act_e, vol_edges=vol_edges, models=frozen_f4), open(f"{R}/f4_frozen_models.json", "w"))
    cand = dict(primary=P[P.PASS].cell.tolist(), f4=Fq[Fq.PASS].cell.tolist())
    json.dump(cand, open(f"{R}/discovery_survivors.json", "w"), indent=1)
    print("BH family size", len(allp), "survivors", cand)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(P[["cell", "n", "gross", "cost", "fund", "net", "ci_lo", "ci_hi", "p", "q_bh", "buckets_pos", "coins_pos", "mfe", "net_stop"]].round(3).to_string())
    print(Fq[["cell", "n_fit", "n_test", "n_sel", "uncond_net_2023", "net", "p", "q_bh", "qtr_pos", "corr_gross", "corr_cost"]].round(3).to_string())
    # counts per year
    cnt = ev[ev.H == 15].assign(y=lambda d: pd.to_datetime(d.t * 60, unit="s").dt.year).groupby(["trig", "y"]).size().unstack(fill_value=0)
    cnt.to_csv(f"{R}/event_counts_by_year_H15.csv"); print(cnt)
