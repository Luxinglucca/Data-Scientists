"""Pre-integration quality assessment of the three raw sources (FRED, NOAA, FEMA).

Reads only the raw files (repo root or data/raw/) (never modifies it). Writes:
    results/raw_quality_checks.csv   every check: source, dimension, check, status, detail
    results/raw_quality_report.md    readable summary
    results/raw_quality_fred_series.csv  per-series FRED profile

Dimensions: accuracy (incl. file integrity), completeness, timeliness, consistency.
Status: PASS, WARN (look at it; cleaning may handle it), FAIL (blocks use), INFO (context only).
Exit code is 0 unless --strict is given and a FAIL exists.
"""
import argparse
import json
import sys
from datetime import date

import pandas as pd

from common import (CHECKSUM_FILE, FEMA_RAW, RAW_DIR, FRED_GLOB, NOAA_META, NOAA_MISSING, NOAA_RAW, NOAA_STATE_CODES, RAW_DIR,
                    RESULTS_DIR, STATE_ABBRS, read_checksums, read_climdiv, sha256_file)

TODAY = pd.Timestamp(date.today())
CHECKS = []


def add(source, dimension, check, status, detail=""):
    CHECKS.append({"source": source, "dimension": dimension, "check": check, "status": status, "detail": detail})


def pf(cond, warn=False):
    return "PASS" if cond else ("WARN" if warn else "FAIL")


def fmt_list(items, n=12):
    items = sorted(items)
    return ", ".join(map(str, items[:n])) + (f" ... (+{len(items) - n} more)" if len(items) > n else "")


# ------------------------------------------------------------------ integrity
def assess_integrity():
    sums = read_checksums()
    # only the project's raw data files (RAW_DIR may be the repo root, which also holds README, data.csv, etc.)
    files = sorted(set(RAW_DIR.glob(FRED_GLOB)) | {p for p in (NOAA_RAW, FEMA_RAW) if p.exists()})
    if not sums:
        add("all", "accuracy", "checksum file present", "FAIL", f"{CHECKSUM_FILE} missing or empty")
        return
    unlisted = [p.name for p in files if p.name not in sums]
    changed = [p.name for p in files if p.name in sums and sha256_file(p) != sums[p.name]]
    missing = [n for n in sums if not (RAW_DIR / n).exists()]
    add("all", "accuracy", "raw files match recorded SHA-256", pf(not changed),
        f"{len(files) - len(changed) - len(unlisted)} verified; changed: {fmt_list(changed) or 'none'}")
    add("all", "completeness", "every raw file has a checksum", pf(not unlisted, warn=True),
        f"no checksum for: {fmt_list(unlisted) or 'none'}")
    add("all", "completeness", "every checksum has a file", pf(not missing, warn=True),
        f"missing files: {fmt_list(missing) or 'none'}")


# ------------------------------------------------------------------ FRED
def assess_fred():
    src = "FRED"
    files = sorted(RAW_DIR.glob(FRED_GLOB))
    if not files:
        add(src, "completeness", "raw files found", "FAIL", f"no files matching {FRED_GLOB}")
        return
    profiles, non_numeric_total = [], 0
    for f in files:
        df = pd.read_csv(f, dtype=str)
        sid = df.columns[1].strip().upper() if df.shape[1] > 1 else f.stem
        d = pd.to_datetime(df.iloc[:, 0], errors="coerce")
        raw = df.iloc[:, 1].str.strip()
        miss = raw.isin([".", ""]) | raw.isna()
        num = pd.to_numeric(raw.where(~miss), errors="coerce")
        non_numeric = int((num.isna() & ~miss).sum())
        non_numeric_total += non_numeric
        valid = d.notna()
        dd = d[valid].sort_values()
        expected = pd.period_range(dd.min(), dd.max(), freq="M") if len(dd) else []
        profiles.append({
            "file": f.name, "series_id": sid, "rows": len(df), "first": dd.min(), "last": dd.max(),
            "missing_values": int(miss.sum()), "non_numeric": non_numeric, "bad_dates": int((~valid).sum()),
            "duplicate_dates": int(d.duplicated().sum()),
            "month_gaps": len(expected) - dd.dt.to_period("M").nunique() if len(dd) else 0,
            "not_first_of_month": int((dd.dt.day != 1).sum()),
            "min": num.min(), "max": num.max(),
        })
    p = pd.DataFrame(profiles)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    p.to_csv(RESULTS_DIR / "raw_quality_fred_series.csv", index=False)

    p["measure"] = p["series_id"].map(lambda s: "unemployment" if s.endswith("UR") else "nonfarm")
    p["state"] = p["series_id"].str[:2]
    for measure in ["unemployment", "nonfarm"]:
        m = p[p["measure"] == measure]
        if m.empty and measure == "nonfarm":
            add(src, "completeness", "nonfarm: series not downloaded", "INFO", "optional; unemployment rate only")
            continue
        absent = STATE_ABBRS - set(m["state"])
        add(src, "completeness", f"{measure}: series for all 50 states + DC", pf(not absent),
            f"{m['state'].nunique()}/51 states; missing: {fmt_list(absent) or 'none'}")
        if m.empty:
            continue
        add(src, "consistency", f"{measure}: same latest month in every series", pf(m["last"].nunique() == 1, True),
            f"latest months: {fmt_list(m['last'].dt.strftime('%Y-%m').unique())}")
        start_ok = (m["first"] <= pd.Timestamp("1990-01-01")).all()
        add(src, "completeness", f"{measure}: covers analysis window start (1990-01)", pf(start_ok),
            f"latest first-observation: {m['first'].max():%Y-%m}")
        lag = (TODAY - m["last"].max()).days
        add(src, "timeliness", f"{measure}: latest observation within 120 days", pf(lag <= 120, True),
            f"latest {m['last'].max():%Y-%m}, {lag} days ago")
    add(src, "completeness", "missing-value placeholders ('.')", "INFO" if p["missing_values"].sum() else "PASS",
        f"{int(p['missing_values'].sum())} across {int((p['missing_values'] > 0).sum())} series")
    add(src, "accuracy", "all values numeric", pf(non_numeric_total == 0), f"{non_numeric_total} non-numeric values")
    ur, nf = p[p["measure"] == "unemployment"], p[p["measure"] == "nonfarm"]
    add(src, "accuracy", "unemployment rate within 0-30%", pf(ur.empty or (ur["min"].min() >= 0 and ur["max"].max() <= 30), True),
        f"range {ur['min'].min()} to {ur['max'].max()}" if len(ur) else "no series")
    add(src, "accuracy", "nonfarm employment positive", pf(nf.empty or nf["min"].min() > 0),
        f"min {nf['min'].min()}" if len(nf) else "no series")
    add(src, "consistency", "no duplicate dates", pf(p["duplicate_dates"].sum() == 0), f"{int(p['duplicate_dates'].sum())} duplicates")
    add(src, "consistency", "no gaps in monthly sequence", pf(p["month_gaps"].sum() == 0, True),
        f"{int(p['month_gaps'].sum())} missing months; series: {fmt_list(p.loc[p['month_gaps'] > 0, 'series_id']) or 'none'}")
    add(src, "consistency", "dates are valid and first-of-month", pf((p["bad_dates"] + p["not_first_of_month"]).sum() == 0),
        f"{int(p['bad_dates'].sum())} unparseable, {int(p['not_first_of_month'].sum())} not on the 1st")


# ------------------------------------------------------------------ NOAA
def assess_noaa():
    src = "NOAA"
    if not NOAA_RAW.exists():
        add(src, "completeness", "raw file found", "FAIL", f"{NOAA_RAW.name} missing")
        return
    df, bad = read_climdiv(NOAA_RAW)
    add(src, "accuracy", "every line has the 94-character data layout and parses", pf(bad == 0), f"{bad} malformed lines of {len(df) + bad}")
    add(src, "consistency", "element code is 02 (average temperature) and division 0",
        pf(set(df["element"]) == {"02"} and set(df["division"]) == {"0"}),
        f"elements {sorted(set(df['element']))}, divisions {sorted(set(df['division']))}")

    non_state = sorted(set(df["state_code"]) - NOAA_STATE_CODES)
    add(src, "consistency", "non-state codes present (regions/national)", "INFO",
        f"{len(non_state)} codes, e.g. {fmt_list(non_state, 6)}; removed in cleaning")
    st = df[df["state_code"].isin(NOAA_STATE_CODES)]
    absent = sorted(NOAA_STATE_CODES - set(st["state_code"]))
    add(src, "completeness", "state codes 001-050 present", pf(set(absent) <= {"049"}, True),
        f"{st['state_code'].nunique()} present; absent: {fmt_list(absent) or 'none'} "
        "(049 Hawaii and DC are expected to be absent)")

    add(src, "consistency", "no duplicate state-years", pf(not st.duplicated(["state_code", "year"]).any()),
        f"{int(st.duplicated(['state_code', 'year']).sum())} duplicates")
    yrs = st.groupby("state_code")["year"].agg(["min", "max", "nunique"])
    gaps = yrs[(yrs["max"] - yrs["min"] + 1) != yrs["nunique"]].index
    add(src, "completeness", "no missing years within a state's record", pf(len(gaps) == 0), f"states with gaps: {fmt_list(gaps) or 'none'}")
    early = yrs[(yrs["min"] > 1895) & (yrs.index != "050")]
    add(src, "completeness", "contiguous states start 1895, Alaska (050) 1925", pf(early.empty and ("050" not in yrs.index or yrs.loc["050", "min"] == 1925), True),
        f"min year {int(yrs['min'].min())}; Alaska starts {int(yrs.loc['050', 'min']) if '050' in yrs.index else 'n/a'}")

    months = [f"m{m:02d}" for m in range(1, 13)]
    vals = st[months]
    last_year = st["year"].max()
    sentinel = (vals == NOAA_MISSING)
    in_old = int(sentinel[st["year"] < last_year].to_numpy().sum())
    add(src, "completeness", "missing sentinel (-99.90) only in latest year", pf(in_old == 0, True),
        f"{int(sentinel.to_numpy().sum())} sentinels total; {in_old} before {last_year}")
    real = vals.where(~sentinel)
    lo, hi = real.min().min(), real.max().max()
    add(src, "accuracy", "values within NOAA's documented range (-50..140 F)", pf(lo >= -50 and hi <= 140), f"observed {lo:.1f} to {hi:.1f}")
    add(src, "accuracy", "values plausible for state averages (-40..100 F)", pf(lo >= -40 and hi <= 100, True), f"observed {lo:.1f} to {hi:.1f}")
    both = real["m01"].notna() & real["m07"].notna()
    inverted = int((real.loc[both, "m07"] <= real.loc[both, "m01"]).sum())
    add(src, "accuracy", "July warmer than January in every state-year", pf(inverted == 0, True), f"{inverted} exceptions of {int(both.sum())}")

    long = st.melt(id_vars=["state_code", "year"], value_vars=months, var_name="m", value_name="t")
    long = long[long["t"] != NOAA_MISSING]
    long["ym"] = pd.to_datetime(dict(year=long["year"], month=long["m"].str[1:].astype(int), day=1))
    last = long.groupby("state_code")["ym"].max()
    add(src, "consistency", "same latest month for every state", pf(last.nunique() == 1, True), f"latest months: {fmt_list(last.dt.strftime('%Y-%m').unique())}")
    lag = (TODAY - last.max()).days
    add(src, "timeliness", "latest state-month within 100 days", pf(lag <= 100, True), f"latest {last.max():%Y-%m}, {lag} days ago")
    if NOAA_META.exists():
        meta = json.loads(NOAA_META.read_text())
        add(src, "timeliness", "download date and NOAA file version recorded", "PASS",
            f"{meta.get('noaa_file_name')} downloaded {meta.get('downloaded_utc')}")
    else:
        add(src, "timeliness", "download date recorded", "WARN", f"{NOAA_META.name} missing")


# ------------------------------------------------------------------ FEMA
FEMA_KEY_COLS = ["disasterNumber", "state", "declarationType", "declarationDate", "incidentType",
                 "incidentBeginDate", "fipsStateCode"]


def assess_fema():
    src = "FEMA"
    if not FEMA_RAW.exists():
        add(src, "completeness", "raw file found", "FAIL", f"{FEMA_RAW.name} missing")
        return
    df = pd.read_csv(FEMA_RAW, dtype=str, keep_default_na=False)
    absent = [c for c in FEMA_KEY_COLS + ["id"] if c not in df.columns]
    add(src, "completeness", "expected columns present", pf(not absent), f"missing: {fmt_list(absent) or 'none'}")
    if absent:
        return
    add(src, "completeness", "row and disaster counts", "INFO",
        f"{len(df):,} rows, {df['disasterNumber'].nunique():,} distinct disasters (one row per county/area)")
    blank = {c: round((df[c].str.strip() == "").mean() * 100, 2) for c in FEMA_KEY_COLS}
    worst = {c: v for c, v in blank.items() if v > 0}
    add(src, "completeness", "key columns populated", "PASS" if not worst else ("FAIL" if max(worst.values()) > 5 else "WARN"),
        "blank %: " + (", ".join(f"{c}={v}" for c, v in worst.items()) or "none"))

    states = df["state"].str.strip().str.upper()
    outside = states[~states.isin(STATE_ABBRS) & (states != "")].value_counts()
    add(src, "consistency", "state values are 50 states + DC", "INFO" if len(outside) else "PASS",
        f"{int(outside.sum())} rows in territories/other: " + ", ".join(f"{k}={v}" for k, v in outside.head(10).items()) + "; dropped in cleaning")
    missing_states = STATE_ABBRS - set(states)
    add(src, "completeness", "all 50 states + DC have declarations", pf(not missing_states, True), f"missing: {fmt_list(missing_states) or 'none'}")

    begin = pd.to_datetime(df["incidentBeginDate"], errors="coerce", utc=True, format="ISO8601").dt.tz_localize(None)
    decl = pd.to_datetime(df["declarationDate"], errors="coerce", utc=True, format="ISO8601").dt.tz_localize(None)
    end = pd.to_datetime(df["incidentEndDate"], errors="coerce", utc=True, format="ISO8601").dt.tz_localize(None)
    unparsed = int(begin.isna().sum() - (df["incidentBeginDate"].str.strip() == "").sum())
    add(src, "accuracy", "incidentBeginDate parses as a date", pf(unparsed == 0), f"{unparsed} unparseable (blank ones counted above)")
    add(src, "accuracy", "incident begin dates between 1953 and today", pf(begin.dropna().between("1948-01-01", TODAY).all()),
        f"range {begin.min():%Y-%m-%d} to {begin.max():%Y-%m-%d}")
    add(src, "accuracy", "incident end not before begin", pf((end < begin).sum() == 0, True), f"{int((end < begin).sum())} rows")
    pre = int((decl < begin - pd.Timedelta(days=1)).sum())
    add(src, "accuracy", "declaration date not before incident begin", "INFO" if pre else "PASS",
        f"{pre} rows declared before incident began (normal for anticipatory emergency declarations)")
    types = df["declarationType"].str.strip().value_counts()
    odd = [t for t in types.index if t not in {"DR", "EM", "FM", "FS"}]
    add(src, "accuracy", "declarationType in DR/EM/FM/FS", pf(not odd, True), "counts: " + ", ".join(f"{k}={int(v)}" for k, v in types.items()))

    dup_id = int(df["id"].duplicated().sum())
    dup_rows = int(df.duplicated().sum())
    add(src, "consistency", "no duplicate id values", pf(dup_id == 0, True), f"{dup_id} duplicate ids, {dup_rows} fully identical rows")
    fips_per_state = (df[states.isin(STATE_ABBRS)].assign(s=states, f=df["fipsStateCode"].str.strip().str.zfill(2))
                     .groupby("s")["f"].nunique())
    bad_fips = fips_per_state[fips_per_state > 1].index
    add(src, "consistency", "one fipsStateCode per state", pf(len(bad_fips) == 0), f"states with >1 code: {fmt_list(bad_fips) or 'none'}")
    per_dis = df.assign(b=begin, s=states).groupby(["disasterNumber", "s"])["b"].nunique()
    n_inc = int((per_dis > 1).sum())
    add(src, "consistency", "one incident begin date per disaster within a state", pf(n_inc == 0, True),
        f"{n_inc} disaster-states have several begin dates (month assignment may differ across county rows)")

    last_decl = decl.max()
    add(src, "timeliness", "latest declaration within 180 days", pf((TODAY - last_decl).days <= 180, True),
        f"latest declaration {last_decl:%Y-%m-%d}")
    if "lastRefresh" in df.columns:
        lr = pd.to_datetime(df["lastRefresh"], errors="coerce", utc=True, format="ISO8601").dt.tz_localize(None).max()
        add(src, "timeliness", "FEMA's lastRefresh within 60 days of today", pf((TODAY - lr).days <= 60, True), f"lastRefresh {lr:%Y-%m-%d}")


# ------------------------------------------------------------------ report
def write_outputs():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    res = pd.DataFrame(CHECKS)
    res.to_csv(RESULTS_DIR / "raw_quality_checks.csv", index=False)
    counts = res["status"].value_counts()
    lines = [f"# Raw data quality report", "", f"Generated {TODAY:%Y-%m-%d}. Inputs: raw files in `{RAW_DIR}` (unmodified).", "",
             "Summary: " + ", ".join(f"{counts.get(s, 0)} {s}" for s in ["PASS", "WARN", "FAIL", "INFO"]), ""]
    for source, g in res.groupby("source", sort=False):
        lines += [f"## {source}", "", "| Dimension | Check | Status | Detail |", "|---|---|---|---|"]
        for r in g.itertuples():
            lines.append(f"| {r.dimension} | {r.check} | **{r.status}** | {str(r.detail).replace('|', '/')} |")
        lines.append("")
    (RESULTS_DIR / "raw_quality_report.md").write_text("\n".join(lines))
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="exit 1 if any check FAILs")
    args = ap.parse_args()
    for fn in (assess_integrity, assess_fred, assess_noaa, assess_fema):
        try:
            fn()
        except Exception as e:  # a broken source should show up in the report, not abort the others
            add(fn.__name__.replace("assess_", "").upper(), "accuracy", "assessment ran without error", "FAIL", repr(e))
    counts = write_outputs()
    print(counts.to_string())
    print(f"Report: {RESULTS_DIR / 'raw_quality_report.md'}")
    return 1 if args.strict and counts.get("FAIL", 0) else 0


if __name__ == "__main__":
    sys.exit(main())
