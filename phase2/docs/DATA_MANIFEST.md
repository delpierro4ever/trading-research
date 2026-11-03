# DATA MANIFEST — Binance USD-M futures (phase 2 ingestion)

Generated 2026-10-14 01:48 UTC by `phase2/code/ingest/gen_manifest.py`. Source: https://data.binance.vision/data/futures/um/. All timestamps UTC, normalised to `datetime[ms, UTC]`. Contains only row counts and timestamp coverage (no price/outcome statistics).

Checksum policy: every zip verified against its sibling `.CHECKSUM` (sha256). Files in scope per S3 listing: 7299. Rejected after 5 retries: **0**.


## Layouts and cadence notes

- **klines_1m / premiumIndexKlines_1m**: 12 CSV columns; `ignore` (always 0) dropped. Kept: open_time, open, high, low, close, volume, close_time, quote_volume, count, taker_buy_volume, taker_buy_quote_volume. Header row present in some files only (detected per file). Timestamps ms; values >=1e14 (µs) are divided by 1000.
- **fundingRate**: calc_time, funding_interval_hours, last_funding_rate (one row per funding event).
- **metrics**: create_time (string UTC, parsed), symbol, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio. Header always present. Nominal cadence 5 min.
- **bookDepth**: timestamp (string UTC, parsed), percentage (signed depth band, -5..-1 and 1..5), depth (base-asset quantity within band), notional (quote value within band). 10 rows per snapshot; dedup key (timestamp, percentage).
- Duplicates: only metrics/BTCUSDT 2020-09..2021-05 (9 months, 75,255 rows) — those daily files list every 5-min row twice with byte-identical values (verified for 2020-09: distinct rows == distinct timestamps); first occurrence kept. No other dataset had duplicates.
- metrics note: some CSV fields are empty strings (e.g. top-trader ratios in early files) and are stored as null.
- Parquet layout: `/home/ubuntu/mafe-data/parquet/<dataset>/<SYM>/<YYYY-MM>.parquet` (zstd); daily files merged into their month. Raw: `/home/ubuntu/mafe-data/raw/<dataset>/<SYM>/` (monthly and daily zips share a directory).

## Per dataset / symbol

### klines_1m / BTCUSDT

- raw zip files: 93; checksum failures/rejects: 0
- rows in parquet: 3,566,880 (raw rows read 3,566,880; duplicates removed 0)
- first / last timestamp: 2020-01-01 00:00:00 / 2026-10-12 23:59:00
- bytes: raw 145.5 MB, parquet 140.6 MB
- schema: `open_time` TIMESTAMP WITH TIME ZONE, `open` DOUBLE, `high` DOUBLE, `low` DOUBLE, `close` DOUBLE, `volume` DOUBLE, `close_time` TIMESTAMP WITH TIME ZONE, `quote_volume` DOUBLE, `count` BIGINT, `taker_buy_volume` DOUBLE, `taker_buy_quote_volume` DOUBLE
- expected grid slots in span at 60s: 3,566,880; present 3,566,880; missing slots 0; gap ranges 0
- observed spacing (seconds: count), top: 60: 3,566,879
- calendar days with data: 2,477 (first 2020-01-01, last 2026-10-12); missing days inside span: 0 in 0 range(s)

### klines_1m / ETHUSDT

- raw zip files: 93; checksum failures/rejects: 0
- rows in parquet: 3,566,880 (raw rows read 3,566,880; duplicates removed 0)
- first / last timestamp: 2020-01-01 00:00:00 / 2026-10-12 23:59:00
- bytes: raw 145.4 MB, parquet 141.0 MB
- schema: `open_time` TIMESTAMP WITH TIME ZONE, `open` DOUBLE, `high` DOUBLE, `low` DOUBLE, `close` DOUBLE, `volume` DOUBLE, `close_time` TIMESTAMP WITH TIME ZONE, `quote_volume` DOUBLE, `count` BIGINT, `taker_buy_volume` DOUBLE, `taker_buy_quote_volume` DOUBLE
- expected grid slots in span at 60s: 3,566,880; present 3,566,880; missing slots 0; gap ranges 0
- observed spacing (seconds: count), top: 60: 3,566,879
- calendar days with data: 2,477 (first 2020-01-01, last 2026-10-12); missing days inside span: 0 in 0 range(s)

### premiumIndexKlines_1m / BTCUSDT

- raw zip files: 93; checksum failures/rejects: 0
- rows in parquet: 3,555,159 (raw rows read 3,555,159; duplicates removed 0)
- first / last timestamp: 2020-01-01 00:00:00 / 2026-10-12 23:59:00
- bytes: raw 63.1 MB, parquet 101.2 MB
- schema: `open_time` TIMESTAMP WITH TIME ZONE, `open` DOUBLE, `high` DOUBLE, `low` DOUBLE, `close` DOUBLE, `volume` DOUBLE, `close_time` TIMESTAMP WITH TIME ZONE, `quote_volume` DOUBLE, `count` BIGINT, `taker_buy_volume` DOUBLE, `taker_buy_quote_volume` DOUBLE
- expected grid slots in span at 60s: 3,566,880; present 3,555,159; missing slots 11,721; gap ranges 15
- observed spacing (seconds: count), top: 60: 3,555,143, 86460: 4, 120: 2, 660: 1, 4980: 1, 1500: 1
- largest gaps (up to 15 of 15):
  - 2021-07-24 00:00:00 .. 2021-07-27 23:59:00 (5,760 slots)
  - 2021-07-01 00:00:00 .. 2021-07-01 23:59:00 (1,440 slots)
  - 2022-10-02 00:00:00 .. 2022-10-02 23:59:00 (1,440 slots)
  - 2023-02-24 00:00:00 .. 2023-02-24 23:59:00 (1,440 slots)
  - 2026-06-29 00:00:00 .. 2026-06-29 23:59:00 (1,440 slots)
  - 2020-12-01 22:40:00 .. 2020-12-02 00:01:00 (82 slots)
  - 2022-07-12 13:52:00 .. 2022-07-12 14:31:00 (40 slots)
  - 2020-01-19 13:09:00 .. 2020-01-19 13:37:00 (29 slots)
  - 2020-12-17 07:32:00 .. 2020-12-17 07:55:00 (24 slots)
  - 2023-11-10 03:59:00 .. 2023-11-10 04:08:00 (10 slots)
  - 2022-07-12 13:14:00 .. 2022-07-12 13:21:00 (8 slots)
  - 2023-11-10 03:38:00 .. 2023-11-10 03:41:00 (4 slots)
  - 2024-08-12 10:02:00 .. 2024-08-12 10:03:00 (2 slots)
  - 2022-07-12 12:57:00 .. 2022-07-12 12:57:00 (1 slots)
  - 2022-07-13 06:59:00 .. 2022-07-13 06:59:00 (1 slots)
- calendar days with data: 2,469 (first 2020-01-01, last 2026-10-12); missing days inside span: 8 in 5 range(s)
  - 2021-07-01 .. 2021-07-01
  - 2021-07-24 .. 2021-07-27
  - 2022-10-02 .. 2022-10-02
  - 2023-02-24 .. 2023-02-24
  - 2026-06-29 .. 2026-06-29

### premiumIndexKlines_1m / ETHUSDT

- raw zip files: 93; checksum failures/rejects: 0
- rows in parquet: 3,555,162 (raw rows read 3,555,162; duplicates removed 0)
- first / last timestamp: 2020-01-01 00:00:00 / 2026-10-12 23:59:00
- bytes: raw 63.8 MB, parquet 101.4 MB
- schema: `open_time` TIMESTAMP WITH TIME ZONE, `open` DOUBLE, `high` DOUBLE, `low` DOUBLE, `close` DOUBLE, `volume` DOUBLE, `close_time` TIMESTAMP WITH TIME ZONE, `quote_volume` DOUBLE, `count` BIGINT, `taker_buy_volume` DOUBLE, `taker_buy_quote_volume` DOUBLE
- expected grid slots in span at 60s: 3,566,880; present 3,555,162; missing slots 11,718; gap ranges 15
- observed spacing (seconds: count), top: 60: 3,555,146, 86460: 4, 120: 2, 2400: 1, 1800: 1, 345660: 1
- largest gaps (up to 15 of 15):
  - 2021-07-24 00:00:00 .. 2021-07-27 23:59:00 (5,760 slots)
  - 2021-07-01 00:00:00 .. 2021-07-01 23:59:00 (1,440 slots)
  - 2022-10-02 00:00:00 .. 2022-10-02 23:59:00 (1,440 slots)
  - 2023-04-09 00:00:00 .. 2023-04-09 23:59:00 (1,440 slots)
  - 2026-06-29 00:00:00 .. 2026-06-29 23:59:00 (1,440 slots)
  - 2020-12-01 22:40:00 .. 2020-12-02 00:01:00 (82 slots)
  - 2022-07-12 13:53:00 .. 2022-07-12 14:31:00 (39 slots)
  - 2020-01-19 13:09:00 .. 2020-01-19 13:37:00 (29 slots)
  - 2020-12-17 07:32:00 .. 2020-12-17 07:55:00 (24 slots)
  - 2023-11-10 03:59:00 .. 2023-11-10 04:08:00 (10 slots)
  - 2022-07-12 13:16:00 .. 2022-07-12 13:21:00 (6 slots)
  - 2023-11-10 03:38:00 .. 2023-11-10 03:41:00 (4 slots)
  - 2024-08-12 10:02:00 .. 2024-08-12 10:03:00 (2 slots)
  - 2022-07-12 12:57:00 .. 2022-07-12 12:57:00 (1 slots)
  - 2022-07-13 06:59:00 .. 2022-07-13 06:59:00 (1 slots)
- calendar days with data: 2,469 (first 2020-01-01, last 2026-10-12); missing days inside span: 8 in 5 range(s)
  - 2021-07-01 .. 2021-07-01
  - 2021-07-24 .. 2021-07-27
  - 2022-10-02 .. 2022-10-02
  - 2023-04-09 .. 2023-04-09
  - 2026-06-29 .. 2026-06-29

### fundingRate / BTCUSDT

- raw zip files: 81; checksum failures/rejects: 0
- rows in parquet: 7,395 (raw rows read 7,395; duplicates removed 0)
- first / last timestamp: 2020-01-01 00:00:00 / 2026-09-30 16:00:00
- bytes: raw 78.1 KB, parquet 189.4 KB
- schema: `calc_time` TIMESTAMP WITH TIME ZONE, `funding_interval_hours` BIGINT, `last_funding_rate` DOUBLE
- funding_interval_hours counts: 8: 7,395
- calendar days with data: 2,465 (first 2020-01-01, last 2026-09-30); missing days inside span: 0 in 0 range(s)

### fundingRate / ETHUSDT

- raw zip files: 81; checksum failures/rejects: 0
- rows in parquet: 7,395 (raw rows read 7,395; duplicates removed 0)
- first / last timestamp: 2020-01-01 00:00:00 / 2026-09-30 16:00:00
- bytes: raw 78.1 KB, parquet 189.4 KB
- schema: `calc_time` TIMESTAMP WITH TIME ZONE, `funding_interval_hours` BIGINT, `last_funding_rate` DOUBLE
- funding_interval_hours counts: 8: 7,395
- calendar days with data: 2,465 (first 2020-01-01, last 2026-09-30); missing days inside span: 0 in 0 range(s)

### metrics / BTCUSDT

- raw zip files: 2233; checksum failures/rejects: 0
- rows in parquet: 642,470 (raw rows read 717,725; duplicates removed 75,255)
- first / last timestamp: 2020-09-01 00:00:00 / 2026-10-12 23:55:00
- bytes: raw 24.8 MB, parquet 25.3 MB
- schema: `create_time` TIMESTAMP WITH TIME ZONE, `symbol` VARCHAR, `sum_open_interest` DOUBLE, `sum_open_interest_value` DOUBLE, `count_toptrader_long_short_ratio` DOUBLE, `sum_toptrader_long_short_ratio` DOUBLE, `count_long_short_ratio` DOUBLE, `sum_taker_long_short_vol_ratio` DOUBLE
- expected grid slots in span at 300s: 643,104; present 642,470; missing slots 634; gap ranges 156
- observed spacing (seconds: count), top: 300: 642,313, 600: 108, 900: 17, 1200: 6, 1500: 5, 1800: 3
- largest gaps (up to 15 of 156):
  - 2024-02-16 13:35:00 .. 2024-02-16 23:55:00 (125 slots)
  - 2021-02-19 20:05:00 .. 2021-02-20 01:15:00 (63 slots)
  - 2021-06-22 18:30:00 .. 2021-06-22 22:45:00 (52 slots)
  - 2021-06-22 00:25:00 .. 2021-06-22 03:25:00 (37 slots)
  - 2021-04-27 11:10:00 .. 2021-04-27 13:35:00 (30 slots)
  - 2021-06-22 12:50:00 .. 2021-06-22 14:25:00 (20 slots)
  - 2021-01-20 00:50:00 .. 2021-01-20 02:10:00 (17 slots)
  - 2021-02-19 00:35:00 .. 2021-02-19 01:30:00 (12 slots)
  - 2021-06-23 02:15:00 .. 2021-06-23 03:10:00 (12 slots)
  - 2020-11-15 03:15:00 .. 2020-11-15 04:05:00 (11 slots)
  - 2020-10-22 03:50:00 .. 2020-10-22 04:35:00 (10 slots)
  - 2021-06-22 04:30:00 .. 2021-06-22 05:15:00 (10 slots)
  - 2021-02-05 00:35:00 .. 2021-02-05 01:15:00 (9 slots)
  - 2021-06-22 09:15:00 .. 2021-06-22 09:55:00 (9 slots)
  - 2020-11-21 03:20:00 .. 2020-11-21 03:55:00 (8 slots)
- calendar days with data: 2,233 (first 2020-09-01, last 2026-10-12); missing days inside span: 0 in 0 range(s)

### metrics / ETHUSDT

- raw zip files: 1777; checksum failures/rejects: 0
- rows in parquet: 511,636 (raw rows read 511,636; duplicates removed 0)
- first / last timestamp: 2021-12-01 00:00:00 / 2026-10-12 23:55:00
- bytes: raw 20.2 MB, parquet 20.2 MB
- schema: `create_time` TIMESTAMP WITH TIME ZONE, `symbol` VARCHAR, `sum_open_interest` DOUBLE, `sum_open_interest_value` DOUBLE, `count_toptrader_long_short_ratio` DOUBLE, `sum_toptrader_long_short_ratio` DOUBLE, `count_long_short_ratio` DOUBLE, `sum_taker_long_short_vol_ratio` DOUBLE
- expected grid slots in span at 300s: 511,776; present 511,636; missing slots 140; gap ranges 10
- observed spacing (seconds: count), top: 300: 511,625, 600: 5, 900: 2, 1200: 2, 37800: 1
- largest gaps (up to 15 of 10):
  - 2024-02-16 13:35:00 .. 2024-02-16 23:55:00 (125 slots)
  - 2023-09-12 08:40:00 .. 2023-09-12 08:50:00 (3 slots)
  - 2025-08-29 06:20:00 .. 2025-08-29 06:30:00 (3 slots)
  - 2021-12-04 05:25:00 .. 2021-12-04 05:30:00 (2 slots)
  - 2024-10-28 16:25:00 .. 2024-10-28 16:30:00 (2 slots)
  - 2021-12-04 05:00:00 .. 2021-12-04 05:00:00 (1 slots)
  - 2021-12-15 19:05:00 .. 2021-12-15 19:05:00 (1 slots)
  - 2021-12-24 15:05:00 .. 2021-12-24 15:05:00 (1 slots)
  - 2021-12-29 23:25:00 .. 2021-12-29 23:25:00 (1 slots)
  - 2021-12-31 16:05:00 .. 2021-12-31 16:05:00 (1 slots)
- calendar days with data: 1,777 (first 2021-12-01, last 2026-10-12); missing days inside span: 0 in 0 range(s)

### bookDepth / BTCUSDT

- raw zip files: 1377; checksum failures/rejects: 0
- rows in parquet: 40,328,222 (raw rows read 40,328,222; duplicates removed 0)
- first / last timestamp: 2023-01-01 00:06:05 / 2026-10-12 23:59:30
- bytes: raw 617.2 MB, parquet 461.5 MB
- schema: `timestamp` TIMESTAMP WITH TIME ZONE, `percentage` DOUBLE, `depth` DOUBLE, `notional` DOUBLE
- distinct snapshots: 3,883,551; rows per snapshot min/max: 10/12; levels: [-5.0, -4.0, -3.0, -2.0, -1.0, -0.2, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0]
- spacing between consecutive snapshots (seconds: count), top: 30: 619,105, 29: 576,543, 31: 565,909, 28: 526,284, 32: 501,089, 33: 262,722, 27: 250,697, 34: 103,840
- per year (snapshots / avg seconds per snapshot over days present): 2023: 1,021,111 / 30.7s; 2024: 1,047,474 / 30.1s; 2025: 1,029,747 / 30.6s; 2026: 785,219 / 31.2s
- calendar days with data: 1,377 (first 2023-01-01, last 2026-10-12); missing days inside span: 4 in 3 range(s)
  - 2023-02-08 .. 2023-02-09
  - 2024-04-18 .. 2024-04-18
  - 2026-10-08 .. 2026-10-08

### bookDepth / ETHUSDT

- raw zip files: 1378; checksum failures/rejects: 0
- rows in parquet: 40,357,032 (raw rows read 40,357,032; duplicates removed 0)
- first / last timestamp: 2023-01-01 00:06:05 / 2026-10-12 23:59:30
- bytes: raw 644.7 MB, parquet 462.2 MB
- schema: `timestamp` TIMESTAMP WITH TIME ZONE, `percentage` DOUBLE, `depth` DOUBLE, `notional` DOUBLE
- distinct snapshots: 3,886,432; rows per snapshot min/max: 10/12; levels: [-5.0, -4.0, -3.0, -2.0, -1.0, -0.2, 0.2, 1.0, 2.0, 3.0, 4.0, 5.0]
- spacing between consecutive snapshots (seconds: count), top: 30: 619,389, 29: 577,003, 31: 566,308, 28: 526,757, 32: 501,588, 33: 262,925, 27: 250,907, 34: 103,910
- per year (snapshots / avg seconds per snapshot over days present): 2023: 1,021,112 / 30.7s; 2024: 1,050,354 / 30.1s; 2025: 1,029,747 / 30.6s; 2026: 785,219 / 31.2s
- calendar days with data: 1,378 (first 2023-01-01, last 2026-10-12); missing days inside span: 3 in 2 range(s)
  - 2023-02-08 .. 2023-02-09
  - 2026-10-08 .. 2026-10-08

## Totals

- raw: 1.7 GB; parquet: 1.4 GB


# Stage 3 ingestion (Amendment 2 cross-asset universe)

Generated 2026-10-14 03:17 UTC by `phase2/code/ingest/stage3_screen.py` + `stage3_ingest.py`. Months 2021-11 through 2024-12 only (monthly files); nothing from 2025+ was downloaded. Same checksum policy (sha256 vs sibling .CHECKSUM, 5 retries) and parquet conventions as above. Row counts and coverage only.

Chosen symbols (25): SOLUSDT, XRPUSDT, DOGEUSDT, BNBUSDT, LTCUSDT, MATICUSDT, BCHUSDT, LINKUSDT, AVAXUSDT, ADAUSDT, FILUSDT, 1000SHIBUSDT, DYDXUSDT, MASKUSDT, FTMUSDT, GALAUSDT, ETCUSDT, LINAUSDT, DOTUSDT, NEARUSDT, EOSUSDT, CRVUSDT, SANDUSDT, ATOMUSDT, AXSUSDT

Checksum failures / rejected files after 5 retries in the stage-3 ingest: **0**

- **klines_1m / SOLUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / SOLUSDT**: zips 38; rows 1,664,578; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,502 in 7 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / SOLUSDT**: zips 38; rows 3,546; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 2:99, 4:2, 8:3445
- **klines_1m / XRPUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / XRPUSDT**: zips 38; rows 1,664,580; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,500 in 6 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:54:00..2022-07-12 14:31:00 (38), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / XRPUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / DOGEUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / DOGEUSDT**: zips 38; rows 1,663,135; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,945 in 9 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / DOGEUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / BNBUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / BNBUSDT**: zips 38; rows 1,663,137; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,943 in 8 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / BNBUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / LTCUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / LTCUSDT**: zips 38; rows 1,664,578; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,502 in 6 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / LTCUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / MATICUSDT**: zips 36; rows 1,505,383; first 2021-11-01 00:00:00; last 2024-09-11 09:42:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / MATICUSDT**: zips 38; rows 1,663,139; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,941 in 7 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / MATICUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / BCHUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / BCHUSDT**: zips 38; rows 1,663,137; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,943 in 8 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / BCHUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / LINKUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / LINKUSDT**: zips 38; rows 1,663,138; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,942 in 7 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / LINKUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / AVAXUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / AVAXUSDT**: zips 38; rows 1,663,139; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,941 in 7 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / AVAXUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / ADAUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / ADAUSDT**: zips 38; rows 1,663,141; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,939 in 9 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / ADAUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / FILUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / FILUSDT**: zips 38; rows 1,663,137; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,943 in 8 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / FILUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / 1000SHIBUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / 1000SHIBUSDT**: zips 38; rows 1,664,577; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,503 in 7 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / 1000SHIBUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / DYDXUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / DYDXUSDT**: zips 38; rows 1,663,137; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,943 in 8 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / DYDXUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / MASKUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / MASKUSDT**: zips 38; rows 1,664,585; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,495 in 5 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / MASKUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / FTMUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / FTMUSDT**: zips 38; rows 1,664,578; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,502 in 7 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:52:00..2022-07-12 14:31:00 (40), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / FTMUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / GALAUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / GALAUSDT**: zips 38; rows 1,663,145; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,935 in 6 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / GALAUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / ETCUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / ETCUSDT**: zips 38; rows 1,663,135; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,945 in 9 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:52:00..2022-07-12 14:31:00 (40)
- **fundingRate / ETCUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / LINAUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / LINAUSDT**: zips 38; rows 1,664,576; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,504 in 8 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / LINAUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / DOTUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / DOTUSDT**: zips 38; rows 1,663,138; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,942 in 8 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / DOTUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / NEARUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / NEARUSDT**: zips 38; rows 1,664,579; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,501 in 6 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / NEARUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / EOSUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / EOSUSDT**: zips 38; rows 1,663,137; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,943 in 8 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / EOSUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / CRVUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / CRVUSDT**: zips 38; rows 1,663,138; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,942 in 7 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / CRVUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / SANDUSDT**: zips 39; rows 1,658,880; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 7,200 in 2 gap range(s); largest: 2022-02-26 00:00:00..2022-02-28 23:59:00 (4,320), 2022-04-01 00:00:00..2022-04-02 23:59:00 (2,880)
- **premiumIndexKlines_1m / SANDUSDT**: zips 38; rows 1,664,584; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,496 in 6 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / SANDUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / ATOMUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / ATOMUSDT**: zips 38; rows 1,664,585; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 1,495 in 5 gap range(s); largest: 2023-04-09 00:00:00..2023-04-09 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39), 2023-11-10 03:59:00..2023-11-10 04:08:00 (10)
- **fundingRate / ATOMUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471
- **klines_1m / AXSUSDT**: zips 39; rows 1,666,080; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 0 in 0 gap range(s)
- **premiumIndexKlines_1m / AXSUSDT**: zips 38; rows 1,663,137; first 2021-11-01 00:00:00; last 2024-12-31 23:59:00; missing 1m slots inside span 2,943 in 8 gap range(s); largest: 2022-10-02 00:00:00..2022-10-02 23:59:00 (1,440), 2023-02-24 00:00:00..2023-02-24 23:59:00 (1,440), 2022-07-12 13:53:00..2022-07-12 14:31:00 (39)
- **fundingRate / AXSUSDT**: zips 38; rows 3,471; first 2021-11-01 00:00:00; last 2024-12-31 16:00:00; interval_hours counts 8:3471

Window coverage used for the >10 % replacement rule is recorded per ranked symbol in `results/stage3/universe.csv`.
