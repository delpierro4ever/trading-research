# MAFE-3 data manifest (HistData.com 1-minute BID bars, Amendment 2)

Pre-registration sha256 `5f503bf8636151b0e837d21586c018e21012a62be80d55c881fdb4643e40a234` (verified when this manifest was built).

## Sources

- **Primary:** HistData.com free ASCII M1 bar quotes (BID only) for XAUUSD and EURUSD. Mechanics: GET `https://www.histdata.com/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}/{year}[/{month}]`, parse the hidden form (`tk`, date, datemonth, platform=ASCII, timeframe=M1, fxpair), POST to `https://www.histdata.com/get.php` with the page as Referer; one request at a time, 6 s pause (`code/mafe3/download_histdata.py`). Yearly files 2009-2025 and monthly files for the complete months of 2026 (the in-progress month is not downloaded). Raw zips: `/home/ubuntu/mafe-data/histdata/raw/` (each zip integrity-tested on download and again at build). Parquet (UTC datetime[ms], open/high/low/close/volume, re-partitioned by UTC year): `/home/ubuntu/mafe-data/histdata/parquet/{SYM}/YYYY.parquet`.
- **Spread sanity (reporting only):** Dukascopy daily minute BID/ASK files already on disk (`/home/ubuntu/mafe-data/dukascopy/raw/XAUUSD`).

## Timezone verification

HistData timestamps are EST without DST (UTC-5); UTC = timestamp + 5 h. Check on the first/last bar of each trading week (Sunday opening, Friday closing), expressed in UTC; counts of weeks by UTC hour of the first/last bar. Expected: the weekly open at Sunday 22:00-23:00 UTC and the weekly close at Friday ~21:00-22:00 UTC (the last bar stamped 21:59 UTC means trading stops at 22:00 UTC, i.e. 17:00 EST fixed). Result: both symbols match in every year (median open 23:00 UTC for XAUUSD, 22:00 UTC for EURUSD; median last bar 21:59 UTC), so the +5 h conversion is correct. A handful of weeks open or close an hour earlier/later or early (holiday weeks); 2023 has fewer opening weeks recorded for XAUUSD (see anomaly below).

### XAUUSD

| year | weeks (open) | median open UTC | open hour counts | weeks (close) | median close UTC | close hour counts |
|---|---:|---|---|---:|---|---|
| 2009 | 42 | 23:01 | {'22': 5, '23': 37} | 40 | 21:59 | {'18': 2, '21': 38} |
| 2010 | 52 | 23:00 | {'22': 1, '23': 51} | 52 | 21:59 | {'10': 1, '19': 1, '21': 45, '22': 5} |
| 2011 | 51 | 23:00 | {'23': 51} | 52 | 21:59 | {'21': 47, '22': 5} |
| 2012 | 52 | 23:00 | {'23': 52} | 52 | 21:59 | {'18': 1, '21': 51} |
| 2013 | 52 | 23:00 | {'23': 52} | 52 | 21:59 | {'17': 1, '18': 1, '21': 50} |
| 2014 | 50 | 23:00 | {'23': 50} | 51 | 21:59 | {'18': 2, '21': 49} |
| 2015 | 52 | 23:01 | {'23': 52} | 51 | 21:59 | {'15': 1, '17': 1, '18': 1, '21': 48} |
| 2016 | 51 | 23:01 | {'23': 51} | 51 | 21:59 | {'18': 1, '21': 50} |
| 2017 | 50 | 23:01 | {'23': 50} | 51 | 21:59 | {'18': 1, '21': 50} |
| 2018 | 52 | 23:01 | {'23': 52} | 51 | 21:59 | {'18': 1, '21': 50} |
| 2019 | 51 | 23:00 | {'22': 4, '23': 47} | 51 | 21:59 | {'19': 1, '20': 4, '21': 46} |
| 2020 | 52 | 23:00 | {'22': 4, '23': 48} | 50 | 21:59 | {'17': 1, '18': 1, '20': 4, '21': 44} |
| 2021 | 52 | 23:00 | {'22': 3, '23': 49} | 50 | 21:59 | {'18': 1, '20': 3, '21': 46} |
| 2022 | 51 | 23:00 | {'22': 3, '23': 48} | 51 | 21:59 | {'18': 1, '20': 3, '21': 47} |
| 2023 | 35 | 23:00 | {'22': 3, '23': 32} | 51 | 21:59 | {'17': 1, '18': 1, '19': 3, '20': 7, '21': 39} |
| 2024 | 52 | 23:00 | {'22': 4, '23': 48} | 51 | 21:59 | {'17': 1, '19': 1, '20': 3, '21': 46} |
| 2025 | 52 | 23:00 | {'22': 4, '23': 48} | 51 | 21:59 | {'15': 1, '17': 1, '19': 1, '20': 4, '21': 44} |
| 2026 | 39 | 23:00 | {'22': 3, '23': 36} | 38 | 21:59 | {'0': 1, '17': 2, '20': 3, '21': 32} |

### EURUSD

| year | weeks (open) | median open UTC | open hour counts | weeks (close) | median close UTC | close hour counts |
|---|---:|---|---|---:|---|---|
| 2009 | 52 | 22:00 | {'22': 51, '23': 1} | 52 | 21:59 | {'2': 1, '21': 50, '22': 1} |
| 2010 | 52 | 22:00 | {'22': 52} | 52 | 21:59 | {'19': 1, '20': 1, '21': 39, '22': 11} |
| 2011 | 51 | 22:00 | {'22': 51} | 52 | 21:59 | {'21': 48, '22': 4} |
| 2012 | 52 | 22:00 | {'22': 52} | 52 | 21:59 | {'21': 52} |
| 2013 | 52 | 22:00 | {'22': 52} | 52 | 21:59 | {'21': 52} |
| 2014 | 51 | 22:00 | {'22': 51} | 52 | 21:59 | {'21': 52} |
| 2015 | 52 | 22:00 | {'22': 52} | 51 | 21:59 | {'21': 51} |
| 2016 | 52 | 22:00 | {'22': 52} | 52 | 21:59 | {'21': 52} |
| 2017 | 50 | 22:00 | {'22': 50} | 52 | 21:59 | {'21': 52} |
| 2018 | 52 | 22:00 | {'22': 52} | 52 | 21:59 | {'21': 52} |
| 2019 | 51 | 22:00 | {'21': 4, '22': 47} | 52 | 21:59 | {'20': 4, '21': 48} |
| 2020 | 52 | 22:00 | {'21': 4, '22': 48} | 52 | 21:59 | {'7': 1, '20': 4, '21': 47} |
| 2021 | 52 | 22:00 | {'21': 3, '22': 49} | 52 | 21:59 | {'20': 3, '21': 49} |
| 2022 | 52 | 22:00 | {'21': 3, '22': 49} | 52 | 21:59 | {'20': 3, '21': 49} |
| 2023 | 51 | 22:00 | {'21': 2, '22': 39, '23': 10} | 52 | 21:59 | {'0': 1, '18': 1, '19': 3, '20': 10, '21': 37} |
| 2024 | 52 | 22:00 | {'21': 3, '22': 49} | 52 | 21:59 | {'20': 4, '21': 48} |
| 2025 | 52 | 22:00 | {'21': 4, '22': 48} | 52 | 21:59 | {'20': 4, '21': 48} |
| 2026 | 39 | 22:00 | {'21': 3, '22': 36} | 39 | 21:59 | {'0': 1, '20': 4, '21': 34} |

## Coverage and quality

### XAUUSD

- Files: 26; raw rows 6145906; duplicate timestamps removed 1194; not-whole-minute stamps 0; structurally invalid bars dropped (high < max(o,c), low > min(o,c), high < low, non-positive or NaN) 0; bars outside a very wide plausibility band (XAU 300-6000, EUR 0.3-3.0) 0; rows kept 6144712; bars with non-zero volume 0 (volume is always 0 in HistData M1).
- First bar 2009-03-15 22:00:00 UTC; last bar 2026-10-01 04:58:00 UTC. First bar on/after 2010-01-04: 2010-01-04 00:00:00 UTC, open 1095.73 (plausibility: XAU ~1100, EURUSD ~1.43 in Jan 2010).
- Longest weekend closure (Fri -> Sun/Mon): 73.2 h.
- Duplicate timestamps: 1194 removed (first occurrence kept after a stable sort), of which 732 timestamps had conflicting OHLC values; duplicated timestamps by UTC year: {'2019': 60, '2020': 60, '2021': 60, '2022': 60, '2023': 60, '2024': 60, '2025': 60, '2026': 732}. (Observed pattern: 60 timestamps per UTC year in 2019-2025 appear twice within a yearly file, one clock hour block, e.g. XAUUSD 2019-10-28 00:00-00:59 UTC; the 2026 monthly files overlap each other. Discovery contains this duplicate hour in 2019 only; the first occurrence is kept, a deterministic choice made before any outcome was computed.)
- Gaps >= 60 min in the middle of the week (not a Fri->Sun/Mon closure), by UTC year: {'2009': 9, '2010': 19, '2011': 18, '2012': 54, '2013': 19, '2014': 112, '2015': 210, '2016': 208, '2017': 207, '2018': 206, '2019': 210, '2020': 211, '2021': 210, '2022': 208, '2023': 751, '2024': 209, '2025': 208, '2026': 158}.
- Start hour (UTC) of those mid-week gaps >= 60 min and < 24 h, by year: {'2009': {'17': 1, '18': 1, '20': 1, '22': 5}, '2010': {'0': 1, '4': 1, '5': 1, '14': 1, '18': 6, '19': 1, '20': 2, '21': 2, '22': 3}, '2011': {'1': 1, '4': 1, '11': 1, '16': 1, '17': 1, '18': 2, '19': 5, '20': 1, '21': 1, '22': 3, '23': 1}, '2012': {'15': 1, '17': 1, '18': 2, '19': 1, '21': 10, '22': 37, '23': 1}, '2013': {'1': 1, '2': 1, '13': 1, '15': 1, '17': 2, '18': 2, '21': 6, '22': 2, '23': 1}, '2014': {'17': 2, '18': 3, '21': 64, '22': 40}, '2015': {'17': 3, '18': 1, '19': 1, '21': 171, '22': 30, '23': 2}, '2016': {'17': 1, '18': 5, '21': 189, '22': 11}, '2017': {'17': 2, '18': 4, '21': 143, '22': 56, '23': 1}, '2018': {'17': 2, '18': 4, '21': 71, '22': 127}, '2019': {'6': 1, '17': 3, '18': 2, '19': 1, '20': 16, '21': 183, '23': 1}, '2020': {'4': 1, '12': 1, '17': 5, '20': 16, '21': 184, '23': 1}, '2021': {'4': 1, '17': 5, '20': 12, '21': 188, '23': 1}, '2022': {'17': 1, '19': 6, '20': 12, '21': 187, '23': 1}, '2023': {'7': 1, '8': 3, '9': 17, '10': 54, '11': 52, '12': 40, '13': 58, '14': 41, '15': 60, '16': 44, '17': 50, '18': 49, '19': 46, '20': 39, '21': 150, '22': 5, '23': 41}, '2024': {'0': 1, '19': 7, '20': 15, '21': 183, '23': 1}, '2025': {'19': 6, '20': 16, '21': 182, '23': 1}, '2026': {'19': 4, '20': 12, '21': 138, '22': 1, '23': 1}}
- Gaps >= 6 h beyond the normal weekend closure (40): 2009-05-25 17:01:00 -> 2009-05-25 23:15:00 (6.2h); 2009-12-24 18:20:00 -> 2009-12-27 23:01:00 (76.7h); 2009-12-31 21:58:00 -> 2010-01-03 23:00:00 (73.0h); 2010-04-02 14:11:00 -> 2010-04-02 20:46:00 (6.6h); 2012-12-24 18:45:00 -> 2012-12-26 11:00:00 (40.2h); 2012-12-31 21:58:00 -> 2013-01-01 22:00:00 (24.0h); 2013-03-29 02:24:00 -> 2013-03-29 12:18:00 (9.9h); 2013-12-24 18:45:00 -> 2013-12-26 11:09:00 (40.4h); 2013-12-31 20:59:00 -> 2014-01-01 23:04:00 (26.1h); 2014-04-17 22:14:00 -> 2014-04-20 23:00:00 (72.8h); 2014-12-24 18:44:00 -> 2014-12-25 23:01:00 (28.3h); 2014-12-31 21:58:00 -> 2015-01-01 23:01:00 (25.1h); 2015-04-02 23:01:00 -> 2015-04-03 13:58:00 (14.9h); 2015-12-24 18:45:00 -> 2015-12-27 23:01:00 (76.3h); 2015-12-31 21:58:00 -> 2016-01-03 23:01:00 (73.0h); 2016-03-24 21:58:00 -> 2016-03-27 23:01:00 (73.0h); 2017-04-13 21:59:00 -> 2017-04-16 23:01:00 (73.0h); 2018-03-29 21:59:00 -> 2018-04-01 23:01:00 (73.0h); 2018-12-24 18:44:00 -> 2018-12-25 23:00:00 (28.3h); 2018-12-31 21:58:00 -> 2019-01-01 23:00:00 (25.0h); 2019-04-18 21:58:00 -> 2019-04-21 23:00:00 (73.0h); 2019-12-24 18:44:00 -> 2019-12-25 23:00:00 (28.3h); 2019-12-31 21:58:00 -> 2020-01-01 23:00:00 (25.0h); 2020-04-09 21:59:00 -> 2020-04-12 23:00:00 (73.0h); 2020-11-30 04:59:00 -> 2020-12-01 00:00:00 (19.0h); 2020-12-24 18:44:00 -> 2020-12-27 23:00:00 (76.3h); 2020-12-31 21:58:00 -> 2021-01-03 23:00:00 (73.0h); 2021-04-01 21:59:00 -> 2021-04-04 23:00:00 (73.0h); 2021-05-31 04:59:00 -> 2021-06-01 01:00:00 (20.0h); 2021-12-23 21:58:00 -> 2021-12-26 23:00:00 (73.0h); 2022-04-14 21:58:00 -> 2022-04-17 23:00:00 (73.0h); 2023-04-06 21:58:00 -> 2023-04-10 00:00:00 (74.0h); 2023-07-12 16:59:00 -> 2023-07-12 23:00:00 (6.0h); 2024-03-28 20:58:00 -> 2024-03-31 23:00:00 (74.0h); 2024-12-24 18:43:00 -> 2024-12-25 23:00:00 (28.3h); 2024-12-31 21:57:00 -> 2025-01-01 23:00:00 (25.1h); 2025-04-17 21:58:00 -> 2025-04-20 23:00:00 (73.0h); 2025-12-24 18:43:00 -> 2025-12-25 23:04:00 (28.4h); 2025-12-31 21:57:00 -> 2026-01-01 23:00:00 (25.1h); 2026-04-02 21:58:00 -> 2026-04-05 23:00:00 (73.0h).

| UTC year | minutes (bars) |
|---|---:|
| 2009 | 276109 |
| 2010 | 346196 |
| 2011 | 352266 |
| 2012 | 354797 |
| 2013 | 355160 |
| 2014 | 351606 |
| 2015 | 351666 |
| 2016 | 353415 |
| 2017 | 352360 |
| 2018 | 353778 |
| 2019 | 352628 |
| 2020 | 354291 |
| 2021 | 353386 |
| 2022 | 354568 |
| 2023 | 308752 |
| 2024 | 355592 |
| 2025 | 353951 |
| 2026 | 264191 |

### EURUSD

- Files: 26; raw rows 6495987; duplicate timestamps removed 364; not-whole-minute stamps 0; structurally invalid bars dropped (high < max(o,c), low > min(o,c), high < low, non-positive or NaN) 0; bars outside a very wide plausibility band (XAU 300-6000, EUR 0.3-3.0) 0; rows kept 6495623; bars with non-zero volume 0 (volume is always 0 in HistData M1).
- First bar 2009-01-01 23:59:00 UTC; last bar 2026-10-01 04:58:00 UTC. First bar on/after 2010-01-04: 2010-01-04 00:00:00 UTC, open 1.4315 (plausibility: XAU ~1100, EURUSD ~1.43 in Jan 2010).
- Longest weekend closure (Fri -> Sun/Mon): 72.0 h.
- Duplicate timestamps: 364 removed (first occurrence kept after a stable sort), of which 4 timestamps had conflicting OHLC values; duplicated timestamps by UTC year: {'2019': 60, '2020': 60, '2021': 60, '2022': 60, '2023': 60, '2025': 60, '2026': 4}. (Observed pattern: 60 timestamps per UTC year in 2019-2025 appear twice within a yearly file, one clock hour block, e.g. XAUUSD 2019-10-28 00:00-00:59 UTC; the 2026 monthly files overlap each other. Discovery contains this duplicate hour in 2019 only; the first occurrence is kept, a deterministic choice made before any outcome was computed.)
- Gaps >= 60 min in the middle of the week (not a Fri->Sun/Mon closure), by UTC year: {'2009': 0, '2010': 1, '2011': 0, '2012': 1, '2013': 2, '2014': 2, '2015': 3, '2016': 2, '2017': 0, '2018': 1, '2019': 5, '2020': 3, '2021': 3, '2022': 1, '2023': 679, '2024': 5, '2025': 3, '2026': 7}.
- Start hour (UTC) of those mid-week gaps >= 60 min and < 24 h, by year: {'2015': {'19': 1, '21': 1}, '2016': {'6': 1}, '2018': {'7': 1}, '2019': {'4': 1, '7': 1, '21': 1, '23': 1}, '2020': {'4': 1, '23': 1}, '2021': {'4': 1, '23': 1}, '2022': {'23': 1}, '2023': {'7': 1, '8': 1, '9': 13, '10': 55, '11': 53, '12': 47, '13': 49, '14': 48, '15': 52, '16': 45, '17': 50, '18': 46, '19': 49, '20': 39, '21': 40, '22': 48, '23': 43}, '2024': {'7': 1, '16': 1, '18': 1, '20': 1, '23': 1}, '2025': {'7': 1, '23': 1}, '2026': {'7': 1, '12': 2, '16': 1, '19': 1, '23': 1}}
- Gaps >= 6 h beyond the normal weekend closure (23): 2009-12-31 21:57:00 -> 2010-01-03 22:00:00 (72.0h); 2012-12-24 21:00:00 -> 2012-12-26 11:00:00 (38.0h); 2012-12-31 21:58:00 -> 2013-01-01 22:00:00 (24.0h); 2013-12-24 19:59:00 -> 2013-12-26 11:00:00 (39.0h); 2013-12-31 20:59:00 -> 2014-01-01 22:00:00 (25.0h); 2014-12-24 19:00:00 -> 2014-12-25 23:00:00 (28.0h); 2014-12-31 21:59:00 -> 2015-01-01 18:00:00 (20.0h); 2015-12-24 18:59:00 -> 2015-12-27 22:07:00 (75.1h); 2015-12-31 21:58:00 -> 2016-01-03 22:00:00 (72.0h); 2016-12-26 06:59:00 -> 2016-12-26 23:00:00 (16.0h); 2018-12-25 07:58:00 -> 2018-12-25 22:01:00 (14.1h); 2018-12-31 21:59:00 -> 2019-01-01 22:02:00 (24.1h); 2019-05-27 04:59:00 -> 2019-05-27 11:00:00 (6.0h); 2019-12-25 07:59:00 -> 2019-12-25 22:00:00 (14.0h); 2019-12-31 21:59:00 -> 2020-01-01 22:00:00 (24.0h); 2020-11-30 04:59:00 -> 2020-12-01 00:00:00 (19.0h); 2020-12-31 21:58:00 -> 2021-01-03 22:00:00 (72.0h); 2021-05-31 04:59:00 -> 2021-06-01 01:00:00 (20.0h); 2023-12-25 07:58:00 -> 2023-12-25 22:04:00 (14.1h); 2024-12-25 07:59:00 -> 2024-12-25 22:04:00 (14.1h); 2024-12-31 21:58:00 -> 2025-01-01 22:00:00 (24.0h); 2025-12-25 07:57:00 -> 2025-12-25 22:04:00 (14.1h); 2025-12-31 21:57:00 -> 2026-01-01 22:04:00 (24.1h).

| UTC year | minutes (bars) |
|---|---:|
| 2009 | 355880 |
| 2010 | 352320 |
| 2011 | 358369 |
| 2012 | 372161 |
| 2013 | 370611 |
| 2014 | 366477 |
| 2015 | 372210 |
| 2016 | 372679 |
| 2017 | 371635 |
| 2018 | 372607 |
| 2019 | 372470 |
| 2020 | 372275 |
| 2021 | 369442 |
| 2022 | 372805 |
| 2023 | 322578 |
| 2024 | 372379 |
| 2025 | 372024 |
| 2026 | 276701 |

**Flagged anomalies.** (1) XAUUSD has a recurring one-hour daily gap from about 21:59-22:00 to 23:00 UTC (daily break), rare before 2012 and present on ~4 of 5 weekdays from 2014 (about 200+ gaps per year); the grid therefore has no decision points in that hour from 2014, and trades cannot span it without a nearest-bar exit. EURUSD has no such gap. (2) UTC year 2023 (holdout, sealed; only timestamps and counts inspected) has far more mid-week gaps and ~13 % fewer bars than other years for both symbols (XAUUSD 308 752 bars vs ~354 000; 2023 gaps by count above), i.e. the 2023 source file looks incomplete; this does not touch discovery. (3) 2026 covers complete months Jan-Sep only; the last bar is 2026-10-01 04:58 UTC.

Note: HistData bars exist only for minutes with ticks, so quiet minutes can be absent even while the market is open; the discovery code therefore accepts the nearest bar within 5 min.

## Spread sanity check vs the $0.35 assumption (reporting only, never a gate)

Dukascopy XAUUSD minute files, ask open - bid open on matching minutes with volume > 0 on both sides. Coverage on disk: 463 paired days, 2009-11-01 22:00:00 -> 2011-04-24 23:59:00 (**only 2009-11 to 2011-04 was downloaded before Dukascopy throttled the feed; the spec's 2012-2014 years do not exist locally**). Format check: 0 records violating low <= open,close <= high. Sanity: HistData BID open vs Dukascopy BID open on 505383 common minutes: median |diff| $0.38, p95 $3.67, median signed $-0.18.

| year | days | minutes | median spread $ | p95 spread $ | mean $ | share ask<bid | mean price | half-spread median x2 vs $0.35 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2009 | 53 | 61310 | 0.494 | 0.586 | 0.470 | 0.0000 | 1129 | median round trip (2 x half-spread) = $0.49 vs $0.35 |
| 2010 | 313 | 365764 | 0.506 | 0.704 | 0.508 | 0.0000 | 1226 | median round trip (2 x half-spread) = $0.51 vs $0.35 |
| 2011 | 97 | 112513 | 0.414 | 0.700 | 0.453 | 0.0000 | 1404 | median round trip (2 x half-spread) = $0.41 vs $0.35 |

A round trip pays one full spread (half at entry, half at exit), i.e. the median spread column is directly comparable to the $0.35 fixed cost, which also has to cover commission and slippage.

## Partitions and seal

Discovery 2010-01-01 -> 2020-01-01; validation 2020-01-01 -> 2023-01-01; holdout 2023-01-01 -> latest. `mafe3.data` raises `HoldoutSealedError` for any request touching >= 2023-01-01 unless `MAFE3_UNSEAL` equals the token file, and never opens 2023+ parquet files when sealed. Quality statistics above cover every year because they were computed during parquet building; they contain only counts, timestamps and structural checks, no return statistics.
