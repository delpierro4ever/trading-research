"""Compute discovery event tables per coin (signals 2020-07..2023-12). Usage: run_events.py [tag] [lag] [cheat]  (controls reuse this)"""
import sys, os, json, numpy as np, pandas as pd, engine as E
os.makedirs(E.GRID.replace("grid", "events"), exist_ok=True)
tag = sys.argv[1] if len(sys.argv) > 1 else "disc"
shift = int(sys.argv[2]) if len(sys.argv) > 2 else 0
cheat = len(sys.argv) > 3 and sys.argv[3] == "cheat"
edges = {}
for c in E.COINS:
    ev = E.run_coin(c, 0, E.DISC_END, Fshift=shift, cheat=cheat)
    ev.to_parquet(f"/home/ubuntu/mafe-data/mafe4/events/{tag}_{c}.parquet"); print(c, len(ev), flush=True)
    if tag == "disc": edges[c] = E.vol_edges(c)
if tag == "disc": json.dump(edges, open("/home/ubuntu/mafe-research-archive/mafe4/results/vol_edges.json", "w"), indent=1)
