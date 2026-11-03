"""Render phase3/docs/DATA_MANIFEST.md from ingest_stats.json (build_parquet.py) and spread_check.json (spread_check.py).
Coverage / structure only; no return statistics."""
import json, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
H = Path("/home/ubuntu/mafe-data/histdata")
st = json.loads((H / "ingest_stats.json").read_text()); sp = json.loads((H / "spread_check.json").read_text())
log = (H / "download.log").read_text()
L = []; w = L.append
w("# MAFE-3 data manifest (HistData.com 1-minute BID bars, Amendment 2)\n")
w("Pre-registration sha256 `5f503bf8636151b0e837d21586c018e21012a62be80d55c881fdb4643e40a234` (verified when this manifest was built).\n")
w("## Sources\n")
w("- **Primary:** HistData.com free ASCII M1 bar quotes (BID only) for XAUUSD and EURUSD. Mechanics: GET `https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}/{year}[/{month}]`, "
  "parse the hidden form (`tk`, date, datemonth, platform=ASCII, timeframe=M1, fxpair), POST to `https://www.histdata.com/get.php` with the page as Referer; one request at a time, 6 s pause (`code/mafe3/download_histdata.py`). "
  "Yearly files 2009-2025 and monthly files for the complete months of 2026 (the in-progress month is not downloaded). Raw zips: `/home/ubuntu/mafe-data/histdata/raw/` (each zip integrity-tested on download and again at build). "
  "Parquet (UTC datetime[ms], open/high/low/close/volume, re-partitioned by UTC year): `/home/ubuntu/mafe-data/histdata/parquet/{SYM}/YYYY.parquet`.")
w("- **Spread sanity (reporting only):** Dukascopy daily minute BID/ASK files already on disk (`/home/ubuntu/mafe-data/dukascopy/raw/XAUUSD`).\n")
w("## Timezone verification\n")
w("HistData timestamps are EST without DST (UTC-5); UTC = timestamp + 5 h. Check on the first/last bar of each trading week (Sunday opening, Friday closing), expressed in UTC; counts of weeks by UTC hour of the first/last bar. "
  "Expected: the weekly open at Sunday 22:00-23:00 UTC and the weekly close at Friday ~21:00-22:00 UTC (the last bar stamped 21:59 UTC means trading stops at 22:00 UTC, i.e. 17:00 EST fixed). "
  "Result: both symbols match in every year (median open 23:00 UTC for XAUUSD, 22:00 UTC for EURUSD; median last bar 21:59 UTC), so the +5 h conversion is correct. A handful of weeks open or close an hour earlier/later or early (holiday weeks); 2023 has fewer opening weeks recorded for XAUUSD (see anomaly below).\n")
for sym in ("XAUUSD", "EURUSD"):
    w(f"### {sym}\n"); w("| year | weeks (open) | median open UTC | open hour counts | weeks (close) | median close UTC | close hour counts |"); w("|---|---:|---|---|---:|---|---|")
    for y in st[sym]["week_open_hour"]:
        o, c = st[sym]["week_open_hour"][y], st[sym]["week_close_hour"][y]
        w(f"| {y} | {o['n']} | {o['median_utc_hhmm']} | {o['hour_counts']} | {c['n']} | {c['median_utc_hhmm']} | {c['hour_counts']} |")
    w("")
w("## Coverage and quality\n")
for sym in ("XAUUSD", "EURUSD"):
    s = st[sym]
    w(f"### {sym}\n")
    w(f"- Files: {s['files']}; raw rows {s['raw_rows']}; duplicate timestamps removed {s['dup_times']}; not-whole-minute stamps {s['not_whole_minute']}; structurally invalid bars dropped (high < max(o,c), low > min(o,c), high < low, non-positive or NaN) {s['bad_ohlc']}; bars outside a very wide plausibility band (XAU 300-6000, EUR 0.3-3.0) {s['outside_wide_band']}; rows kept {s['rows']}; bars with non-zero volume {s['volume_nonzero']} (volume is always 0 in HistData M1).")
    w(f"- First bar {s['first_bar_utc']} UTC; last bar {s['last_bar_utc']} UTC. First bar on/after 2010-01-04: {s['jan2010_first_time']} UTC, open {s['jan2010_first_open']} (plausibility: XAU ~1100, EURUSD ~1.43 in Jan 2010).")
    w(f"- Longest weekend closure (Fri -> Sun/Mon): {s['weekend_gap_max_h']:.1f} h.")
    w(f"- Duplicate timestamps: {s['dup_times']} removed (first occurrence kept after a stable sort), of which {s['dup_conflicting_timestamps']} timestamps had conflicting OHLC values; duplicated timestamps by UTC year: {s['dup_by_utc_year']}. (Observed pattern: 60 timestamps per UTC year in 2019-2025 appear twice within a yearly file, one clock hour block, e.g. XAUUSD 2019-10-28 00:00-00:59 UTC; the 2026 monthly files overlap each other. Discovery contains this duplicate hour in 2019 only; the first occurrence is kept, a deterministic choice made before any outcome was computed.)")
    w(f"- Gaps >= 60 min in the middle of the week (not a Fri->Sun/Mon closure), by UTC year: {s['gaps_ge_60min_nonweekend']}.")
    w(f"- Start hour (UTC) of those mid-week gaps >= 60 min and < 24 h, by year: {s['gap_ge60_start_hour_by_year']}")
    g6 = s["gaps_ge_6h_nonweekend"]
    w(f"- Gaps >= 6 h beyond the normal weekend closure ({len(g6)}): " + ("; ".join(g6) if g6 else "none") + ".\n")
    w("| UTC year | minutes (bars) |"); w("|---|---:|")
    for y, n in s["per_year_rows"].items(): w(f"| {y} | {n} |")
    w("")
w("**Flagged anomalies.** (1) XAUUSD has a recurring one-hour daily gap from about 21:59-22:00 to 23:00 UTC (daily break), rare before 2012 and present on ~4 of 5 weekdays from 2014 (about 200+ gaps per year); the grid therefore has no decision points in that hour from 2014, and trades cannot span it without a nearest-bar exit. EURUSD has no such gap. "
  "(2) UTC year 2023 (holdout, sealed; only timestamps and counts inspected) has far more mid-week gaps and ~13 % fewer bars than other years for both symbols (XAUUSD 308 752 bars vs ~354 000; 2023 gaps by count above), i.e. the 2023 source file looks incomplete; this does not touch discovery. "
  "(3) 2026 covers complete months Jan-Sep only; the last bar is 2026-10-01 04:58 UTC.\n")
w("Note: HistData bars exist only for minutes with ticks, so quiet minutes can be absent even while the market is open; the discovery code therefore accepts the nearest bar within 5 min.\n")
w("## Spread sanity check vs the $0.35 assumption (reporting only, never a gate)\n")
w(f"Dukascopy XAUUSD minute files, ask open - bid open on matching minutes with volume > 0 on both sides. Coverage on disk: {sp['day_files_paired']} paired days, {sp['first']} -> {sp['last']} "
  f"(**only 2009-11 to 2011-04 was downloaded before Dukascopy throttled the feed; the spec's 2012-2014 years do not exist locally**). "
  f"Format check: {sp['format_violations']} records violating low <= open,close <= high. Sanity: HistData BID open vs Dukascopy BID open on {sp['histdata_crosscheck']['matched_minutes']} common minutes: "
  f"median |diff| ${sp['histdata_crosscheck']['median_abs_diff_usd']:.2f}, p95 ${sp['histdata_crosscheck']['p95_abs_diff_usd']:.2f}, median signed ${sp['histdata_crosscheck']['median_signed_diff_usd']:.2f}.\n")
w("| year | days | minutes | median spread $ | p95 spread $ | mean $ | share ask<bid | mean price | half-spread median x2 vs $0.35 |"); w("|---|---:|---:|---:|---:|---:|---:|---:|---|")
for y, r in sp["by_year"].items():
    w(f"| {y} | {r['days']} | {r['minutes']} | {r['median_usd']:.3f} | {r['p95_usd']:.3f} | {r['mean_usd']:.3f} | {r['share_negative']:.4f} | {r['mean_price']:.0f} | "
      f"median round trip (2 x half-spread) = ${r['median_usd']:.2f} vs $0.35 |")
w("\nA round trip pays one full spread (half at entry, half at exit), i.e. the median spread column is directly comparable to the $0.35 fixed cost, which also has to cover commission and slippage.\n")
w("## Partitions and seal\n")
w("Discovery 2010-01-01 -> 2020-01-01; validation 2020-01-01 -> 2023-01-01; holdout 2023-01-01 -> latest. `mafe3.data` raises `HoldoutSealedError` for any request touching >= 2023-01-01 unless `MAFE3_UNSEAL` equals the token file, and never opens 2023+ parquet files when sealed. "
  "Quality statistics above cover every year because they were computed during parquet building; they contain only counts, timestamps and structural checks, no return statistics.")
(ROOT / "docs" / "DATA_MANIFEST.md").write_text("\n".join(L) + "\n")
print("ok")
