"""Clean the raw FRED state series (unemployment rate and total nonfarm employment).

Input : fred_<series_id>_raw.csv (repo root or data/raw/) (one file per series, FRED's fredgraph.csv export:
        first column observation_date (or DATE), second column named after the series ID)
Output: data/cleaned/fred_state_monthly_cleaned.csv   (long format, one row per series-month)
        results/cleaning_log_fred.csv

Columns: series_id, measure, seasonal_adjustment, year_month (YYYY-MM), value
  measure = unemployment_rate_pct | nonfarm_employment_thousands
Series IDs are NOT converted to states here; build_state_id_map.py / join_datasets.py do that.

Series naming handled: <ST>UR (unemployment rate, seasonally adjusted), <ST>NA (total nonfarm,
seasonally adjusted) and <ST>NAN (total nonfarm, not seasonally adjusted).

Steps: read every file -> parse dates -> FRED's "." placeholder and blanks become missing and are
dropped -> non-numeric values dropped -> impossible values dropped (rate outside 0-100, employment <= 0)
-> duplicate series-months dropped -> sort.
"""
import re
import sys

import pandas as pd

from common import CLEANED_DIR, FRED_GLOB, RAW_DIR, CleaningLog

OUT = CLEANED_DIR / "fred_state_monthly_cleaned.csv"
SERIES_RE = re.compile(r"^[A-Z]{2}(UR|NAN|NA)$")


def classify(series_id):
    if series_id.endswith("UR"):
        return "unemployment_rate_pct", "seasonally_adjusted"
    if series_id.endswith("NAN"):
        return "nonfarm_employment_thousands", "not_seasonally_adjusted"
    return "nonfarm_employment_thousands", "seasonally_adjusted"


def main():
    log = CleaningLog("fred")
    files = sorted(RAW_DIR.glob(FRED_GLOB))
    if not files:
        sys.exit(f"No raw FRED files matching {FRED_GLOB} in {RAW_DIR}. Run acquire_fred.py first.")

    frames, skipped = [], []
    for f in files:
        df = pd.read_csv(f, dtype=str)
        if df.shape[1] < 2:
            skipped.append(f.name)
            continue
        series_id = df.columns[1].strip().upper()
        if not SERIES_RE.match(series_id):
            skipped.append(f.name)
            continue
        df = df.iloc[:, :2]
        df.columns = ["date", "value"]
        df["series_id"] = series_id
        frames.append(df)
    log.add("series files read", len(frames), f"of {len(files)} files")
    if skipped:
        log.add("files skipped (unrecognised layout or series ID)", len(skipped), ", ".join(skipped))

    df = pd.concat(frames, ignore_index=True)
    log.add("raw rows", len(df))

    df["value"] = df["value"].str.strip()
    n = len(df)
    df = df[df["value"].notna() & ~df["value"].isin(["", "."])]
    log.add("dropped: missing value ('.' or blank)", n - len(df))

    n = len(df)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"].str.strip(), errors="coerce")
    df = df.dropna(subset=["value", "date"])
    log.add("dropped: non-numeric value or unparseable date", n - len(df))

    meas = df["series_id"].map(classify)
    df["measure"] = meas.str[0]
    df["seasonal_adjustment"] = meas.str[1]

    n = len(df)
    ok = ((df["measure"] == "unemployment_rate_pct") & df["value"].between(0, 100)) | \
         ((df["measure"] == "nonfarm_employment_thousands") & (df["value"] > 0))
    df = df[ok]
    log.add("dropped: impossible values", n - len(df), "rate outside 0-100 or employment <= 0")

    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    n = len(df)
    df = df.drop_duplicates(["series_id", "year_month"], keep="last")
    log.add("dropped: duplicate series-months", n - len(df))

    df = df.sort_values(["series_id", "year_month"])[
        ["series_id", "measure", "seasonal_adjustment", "year_month", "value"]]
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    log.add("rows written", len(df), f"{df['series_id'].nunique()} series, "
            f"{df['year_month'].min()} to {df['year_month'].max()}")
    log.write()
    return 0


if __name__ == "__main__":
    sys.exit(main())
