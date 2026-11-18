"""Clean the raw OpenFEMA Disaster Declarations Summaries (v2).

Input : DisasterDeclarationsSummaries*.csv (repo root or data/raw/) (one row per declared county/area within a disaster)
Output: data/cleaned/fema_declarations_cleaned.csv   (still one row per county/area)
        results/cleaning_log_fema.csv

Cleaning does NOT aggregate. join_datasets.py aggregates to state-month and must count
distinct disaster_number (not rows), because one disaster spans many county rows.

Columns kept: id, disaster_number, fema_declaration_string, declaration_type, state (2-letter),
fips_state_code, fips_county_code, designated_area, incident_type, declaration_date,
incident_begin_date, incident_end_date, year_month (from incident_begin_date),
ih/ia/pa/hm program flags.

Steps: trim whitespace, blanks -> missing -> drop exact duplicate records (same id) -> drop rows
without state or incident begin date -> keep the 50 states + DC (territories and tribal-only rows
outside the project's scope are dropped and counted) -> parse dates, flag/drop impossible dates ->
standardise codes (upper-case state, zero-padded FIPS) -> standardise incident type text.
"""
import sys

import pandas as pd

from common import CLEANED_DIR, FEMA_RAW, STATE_ABBRS, CleaningLog

OUT = CLEANED_DIR / "fema_declarations_cleaned.csv"
FIRST_DECLARATION = pd.Timestamp("1953-05-01")  # earliest FEMA declaration (May 1953)

RENAME = {
    "id": "id", "disasterNumber": "disaster_number", "femaDeclarationString": "fema_declaration_string",
    "declarationType": "declaration_type", "state": "state", "fipsStateCode": "fips_state_code",
    "fipsCountyCode": "fips_county_code", "designatedArea": "designated_area", "incidentType": "incident_type",
    "declarationDate": "declaration_date", "incidentBeginDate": "incident_begin_date",
    "incidentEndDate": "incident_end_date", "ihProgramDeclared": "ih_program_declared",
    "iaProgramDeclared": "ia_program_declared", "paProgramDeclared": "pa_program_declared",
    "hmProgramDeclared": "hm_program_declared",
}


def to_date(s):
    return pd.to_datetime(s, errors="coerce", utc=True, format="ISO8601").dt.tz_localize(None)


def main():
    log = CleaningLog("fema")
    df = pd.read_csv(FEMA_RAW, dtype=str, keep_default_na=False)
    log.add("raw rows", len(df), f"{df['disasterNumber'].nunique():,} distinct disasters")

    missing_cols = [c for c in RENAME if c not in df.columns]
    if missing_cols:
        sys.exit(f"Raw FEMA file is missing expected columns: {missing_cols}")
    df = df[list(RENAME)].rename(columns=RENAME)

    for c in df.columns:
        df[c] = df[c].str.strip().replace("", pd.NA)

    n = len(df)
    df = df.drop_duplicates("id", keep="last")
    log.add("dropped: duplicate id", n - len(df))

    n = len(df)
    df = df.dropna(subset=["disaster_number", "state", "incident_begin_date"])
    log.add("dropped: missing disaster number, state or incident begin date", n - len(df))

    df["state"] = df["state"].str.upper()
    n = len(df)
    out_of_scope = df.loc[~df["state"].isin(STATE_ABBRS), "state"].value_counts()
    df = df[df["state"].isin(STATE_ABBRS)]
    log.add("dropped: outside 50 states + DC", n - len(df),
            "; ".join(f"{k}={v}" for k, v in out_of_scope.items()))

    for c in ["declaration_date", "incident_begin_date", "incident_end_date"]:
        df[c] = to_date(df[c])
    n = len(df)
    df = df.dropna(subset=["incident_begin_date"])
    log.add("dropped: unparseable incident begin date", n - len(df))

    today = pd.Timestamp.today().normalize()
    n = len(df)
    df = df[df["incident_begin_date"].between(FIRST_DECLARATION - pd.Timedelta(days=365 * 5), today)]
    log.add("dropped: incident begin date in the future or before 1948", n - len(df))

    bad_end = df["incident_end_date"] < df["incident_begin_date"]
    df.loc[bad_end, "incident_end_date"] = pd.NaT
    log.add("set to missing: incident end date before begin date", bad_end.sum())

    df["disaster_number"] = pd.to_numeric(df["disaster_number"], errors="coerce").astype("Int64")
    df["fips_state_code"] = df["fips_state_code"].str.zfill(2)
    df["fips_county_code"] = df["fips_county_code"].str.zfill(3)
    df["declaration_type"] = df["declaration_type"].str.upper()
    df["incident_type"] = df["incident_type"].str.strip().str.title()
    for c in ["ih_program_declared", "ia_program_declared", "pa_program_declared", "hm_program_declared"]:
        df[c] = df[c].str.lower().map({"true": True, "false": False, "1": True, "0": False})

    df["year_month"] = df["incident_begin_date"].dt.strftime("%Y-%m")
    df = df.sort_values(["incident_begin_date", "disaster_number", "state", "fips_county_code"])

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, date_format="%Y-%m-%d")
    log.add("rows written", len(df), f"{df['disaster_number'].nunique():,} distinct disasters, "
            f"{df['year_month'].min()} to {df['year_month'].max()}")
    log.write()
    return 0


if __name__ == "__main__":
    sys.exit(main())
