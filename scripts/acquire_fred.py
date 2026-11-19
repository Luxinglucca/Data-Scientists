"""Download the FRED state employment series used in the project.

For each of the 50 states + DC, two monthly, seasonally adjusted series from the U.S. Bureau of
Labor Statistics, republished on FRED:
    <ST>UR   unemployment rate (percent)              e.g. ILUR
    <ST>NA   all employees, total nonfarm (thousands)  e.g. ILNA

Writes, unmodified, to data/raw/:
    fred_<series id, lowercase>_raw.csv   one file per series (102 files), exactly as FRED serves it
    fred_raw.meta.json                    source URL, download time (UTC), rows and SHA-256 for every series
and records each file's SHA-256 in checksums.sha256.

Each file comes from FRED's public CSV download link for that series (no API key needed):
    https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>
Requests are spaced out (one series at a time, with a pause) to be polite to FRED's servers.

Raw files are never overwritten: series already on disk are skipped unless --force is given.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from common import RAW_DIR, STATE_ABBRS, record_checksum, sha256_file

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SUFFIXES = {"UR": "unemployment rate (percent, seasonally adjusted)",
            "NA": "all employees: total nonfarm (thousands of persons, seasonally adjusted)"}
META = RAW_DIR / "fred_raw.meta.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (course project; data acquisition script)"}
PAUSE_SECONDS = 1.0
CITATION = ("U.S. Bureau of Labor Statistics, {title} [{sid}], retrieved from FRED, "
            "Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/{sid}")


def series_ids():
    return [st + suf for st in sorted(STATE_ABBRS) for suf in SUFFIXES]


def raw_path(sid):
    return RAW_DIR / f"fred_{sid.lower()}_raw.csv"


def fetch(url, retries=3, timeout=60):
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            print(f"  attempt {attempt}/{retries} failed for {url}: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


def sanity_check(sid, data):
    """Check we got a two-column CSV for this series and not an HTML error page. Returns row count."""
    lines = data.decode("utf-8", errors="replace").strip().splitlines()
    if not lines or "<html" in lines[0].lower():
        raise RuntimeError(f"{sid}: got an HTML page instead of CSV")
    header = [c.strip().upper() for c in lines[0].split(",")]
    if len(header) != 2 or header[1] != sid:
        raise RuntimeError(f"{sid}: unexpected header {lines[0]!r}")
    if len(lines) < 100:
        raise RuntimeError(f"{sid}: only {len(lines) - 1} rows; expected hundreds of months")
    return len(lines) - 1


def load_meta():
    if META.exists():
        return json.loads(META.read_text())
    return {
        "source": "FRED (Federal Reserve Economic Data), Federal Reserve Bank of St. Louis",
        "original_publisher": "U.S. Bureau of Labor Statistics (LAUS and CES programs)",
        "terms_of_use": "https://fred.stlouisfed.org/legal/",
        "copyright_label": "Public Domain: Citation Requested (BLS series)",
        "series": {},
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="re-download and overwrite series already on disk")
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    meta = load_meta()
    downloaded, skipped, failed = 0, 0, []

    for i, sid in enumerate(series_ids(), 1):
        path = raw_path(sid)
        if path.exists() and not args.force:
            record_checksum(path)
            skipped += 1
            continue
        url = URL.format(sid)
        print(f"[{i}/{len(series_ids())}] {sid}")
        try:
            data = fetch(url)
            rows = sanity_check(sid, data)
        except RuntimeError as e:
            print(f"  FAILED: {e}")
            failed.append(sid)
            continue
        path.write_bytes(data)  # byte-for-byte, no re-encoding or newline translation
        digest = record_checksum(path)
        assert sha256_file(path) == digest
        meta["series"][sid] = {
            "file": path.name,
            "description": SUFFIXES[sid[2:]],
            "source_url": url,
            "series_page": f"https://fred.stlouisfed.org/series/{sid}",
            "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "rows": rows,
            "sha256": digest,
        }
        downloaded += 1
        time.sleep(PAUSE_SECONDS)

    meta["citation_format"] = CITATION
    META.write_text(json.dumps(meta, indent=2, sort_keys=False) + "\n")
    print(f"FRED: {downloaded} downloaded, {skipped} already on disk (not overwritten), {len(failed)} failed")
    if failed:
        print("Failed series (re-run the script to retry them): " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
