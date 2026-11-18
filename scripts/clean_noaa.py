"""Clean the raw NOAA nClimDiv statewide temperature file.

Input : noaa_climdiv_tmpcst_raw.txt (repo root or data/raw/)
Output: data/cleaned/noaa_state_monthly_temperature_cleaned.csv   (one row per state-month)
        results/cleaning_log_noaa.csv

Columns: noaa_state_code (3-digit string, mapped to abbreviations later by build_state_id_map.py),
         year, month, year_month (YYYY-MM), avg_temp_f

Steps: parse fixed-width lines -> keep average-temperature element (02) -> keep state codes 001-050
(drops regional/national aggregates 101-110 and special regions) -> reshape 12 monthly columns to
one row per month -> drop the -99.90 "not yet available" sentinel -> drop values outside NOAA's
documented -50..140 F range -> drop duplicate state-months -> sort.
"""
import sys

from common import (CLEANED_DIR, NOAA_MISSING, NOAA_RAW, NOAA_STATE_CODES, CleaningLog, read_climdiv)

OUT = CLEANED_DIR / "noaa_state_monthly_temperature_cleaned.csv"
TEMP_MIN, TEMP_MAX = -50.0, 140.0  # documented range in NOAA's state-readme.txt


def main():
    log = CleaningLog("noaa")
    wide, bad = read_climdiv(NOAA_RAW)
    log.add("lines parsed", len(wide), "state-year records")
    log.add("malformed lines skipped", bad, "wrong width or non-numeric")

    n = len(wide)
    wide = wide[(wide["element"] == "02") & (wide["division"] == "0")]
    log.add("dropped: not average temperature / not statewide", n - len(wide))

    n = len(wide)
    wide = wide[wide["state_code"].isin(NOAA_STATE_CODES)]
    log.add("dropped: regional, national and special-region codes", n - len(wide))

    long = wide.melt(id_vars=["state_code", "year"], value_vars=[f"m{m:02d}" for m in range(1, 13)],
                     var_name="month", value_name="avg_temp_f")
    long["month"] = long["month"].str[1:].astype(int)
    log.add("state-months after reshape", len(long))

    n = len(long)
    long = long[long["avg_temp_f"] != NOAA_MISSING]
    log.add("dropped: missing-value sentinel (-99.90)", n - len(long), "mostly future months of the latest year")

    n = len(long)
    long = long[long["avg_temp_f"].between(TEMP_MIN, TEMP_MAX)]
    log.add("dropped: outside documented range", n - len(long), f"{TEMP_MIN}..{TEMP_MAX} F")

    n = len(long)
    long = long.drop_duplicates(["state_code", "year", "month"], keep="first")
    log.add("dropped: duplicate state-months", n - len(long))

    long = long.rename(columns={"state_code": "noaa_state_code"})
    long["year_month"] = long["year"].astype(str) + "-" + long["month"].astype(str).str.zfill(2)
    long = long.sort_values(["noaa_state_code", "year", "month"])[
        ["noaa_state_code", "year", "month", "year_month", "avg_temp_f"]]

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    long.to_csv(OUT, index=False)
    log.add("rows written", len(long), f"{long['noaa_state_code'].nunique()} states, "
            f"{long['year_month'].min()} to {long['year_month'].max()}")
    log.write()
    return 0


if __name__ == "__main__":
    sys.exit(main())
