# Raw data quality report

Generated 2026-11-18. Inputs: raw files in `/workspaces/Data-Scientists/data/raw` (unmodified).

Summary: 26 PASS, 2 WARN, 1 FAIL, 4 INFO

## all

| Dimension | Check | Status | Detail |
|---|---|---|---|
| accuracy | raw files match recorded SHA-256 | **PASS** | 2 verified; changed: none |
| completeness | every raw file has a checksum | **PASS** | no checksum for: none |
| completeness | every checksum has a file | **PASS** | missing files: none |

## FRED

| Dimension | Check | Status | Detail |
|---|---|---|---|
| completeness | raw files found | **FAIL** | no files matching fred_*_raw.csv |

## NOAA

| Dimension | Check | Status | Detail |
|---|---|---|---|
| accuracy | every line is 94 characters and parseable | **PASS** | 0 malformed lines of 12810 |
| consistency | element code is 02 (average temperature) and division 0 | **PASS** | elements ['02'], divisions ['0'] |
| consistency | non-state codes present (regions/national) | **INFO** | 48 codes, e.g. 101, 102, 103, 104, 105, 106 ... (+42 more); removed in cleaning |
| completeness | state codes 001-050 present | **PASS** | 50 present; absent: none (049 Hawaii and DC are expected to be absent) |
| consistency | no duplicate state-years | **PASS** | 0 duplicates |
| completeness | no missing years within a state's record | **PASS** | states with gaps: none |
| completeness | contiguous states start 1895, Alaska (050) 1925 | **WARN** | min year 1895; Alaska starts 1925 |
| completeness | missing sentinel (-99.90) only in latest year | **PASS** | 100 sentinels total; 0 before 2026 |
| accuracy | values within NOAA's documented range (-50..140 F) | **PASS** | observed -14.1 to 89.2 |
| accuracy | values plausible for state averages (-40..100 F) | **PASS** | observed -14.1 to 89.2 |
| accuracy | July warmer than January in every state-year | **PASS** | 0 exceptions of 6474 |
| consistency | same latest month for every state | **PASS** | latest months: 2026-10 |
| timeliness | latest state-month within 100 days | **PASS** | latest 2026-10, 48 days ago |
| timeliness | download date and NOAA file version recorded | **PASS** | climdiv-tmpcst-v1.0.0-20261105 downloaded 2026-11-18T04:55:29+00:00 |

## FEMA

| Dimension | Check | Status | Detail |
|---|---|---|---|
| completeness | expected columns present | **PASS** | missing: none |
| completeness | row and disaster counts | **INFO** | 70,571 rows, 5,283 distinct disasters (one row per county/area) |
| completeness | key columns populated | **PASS** | blank %: none |
| consistency | state values are 50 states + DC | **INFO** | 2488 rows in territories/other: PR=2116, MP=97, VI=87, AS=76, MH=53, FM=31, GU=27, PW=1; dropped in cleaning |
| completeness | all 50 states + DC have declarations | **PASS** | missing: none |
| accuracy | incidentBeginDate parses as a date | **PASS** | 0 unparseable (blank ones counted above) |
| accuracy | incident begin dates between 1953 and today | **PASS** | range 1953-05-02 to 2026-10-16 |
| accuracy | incident end not before begin | **WARN** | 2 rows |
| accuracy | declaration date not before incident begin | **INFO** | 153 rows declared before incident began (normal for anticipatory emergency declarations) |
| accuracy | declarationType in DR/EM/FM/FS | **PASS** | counts: DR=46724, EM=21683, FM=2164 |
| consistency | no duplicate id values | **PASS** | 0 duplicate ids, 0 fully identical rows |
| consistency | one fipsStateCode per state | **PASS** | states with >1 code: none |
| consistency | one incident begin date per disaster within a state | **PASS** | 0 disaster-states have several begin dates (month assignment may differ across county rows) |
| timeliness | latest declaration within 180 days | **PASS** | latest declaration 2026-10-17 |
| timeliness | FEMA's lastRefresh within 60 days of today | **PASS** | lastRefresh 2026-10-21 |
