"""Download the OpenFEMA Disaster Declarations Summaries (v2) dataset.

Writes, unmodified, to data/raw/:
    fema_declarations_raw.csv        the full dataset exactly as OpenFEMA serves it
    fema_declarations_raw.meta.json  API endpoint and version, download time (UTC), FEMA's last refresh,
                                     rows, SHA-256, and the citation statement FEMA requires
and records the SHA-256 in checksums.sha256.

The file comes from OpenFEMA's public full-dataset CSV link (no API key needed):
    https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries.csv
OpenFEMA updates this dataset continuously, so a later download can differ. That is why the copy we
use is committed to the repo with its download time and checksum (see ProjectPlan.md, Constraints).

OpenFEMA's terms ask users to cite the endpoint and version, the download date, and to state:
    "This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA."

Raw files are never overwritten: re-running skips the download unless --force is given.
"""
import argparse
import csv
import io
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from common import CHECKSUM_FILE, RAW_DIR, read_checksums, record_checksum, sha256_file

URL = "https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries.csv"
DATASET_PAGE = "https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2"
FEMA_RAW_OUT = RAW_DIR / "fema_declarations_raw.csv"
FEMA_META = RAW_DIR / "fema_declarations_raw.meta.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (course project; data acquisition script)"}
REQUIRED_COLS = {"disasterNumber", "state", "declarationType", "declarationDate", "incidentType",
                 "incidentBeginDate", "fipsStateCode", "fipsCountyCode", "id", "lastRefresh"}
STATEMENT = ("This product uses the Federal Emergency Management Agency's OpenFEMA API, "
             "but is not endorsed by FEMA.")


def fetch(url, retries=3, timeout=300):
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            print(f"  attempt {attempt}/{retries} failed: {e}")
            time.sleep(5 * attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


def sanity_check(data):
    """Check we got the full CSV and not an error page. Returns (rows, distinct disasters, latest lastRefresh)."""
    text = data.decode("utf-8", errors="replace")
    if text.lstrip()[:1] in ("<", "{"):
        raise RuntimeError("got an HTML/JSON page instead of CSV")
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLS - set(reader.fieldnames or [])
    if missing:
        raise RuntimeError(f"CSV is missing expected columns: {sorted(missing)}")
    rows, disasters, last_refresh = 0, set(), ""
    for r in reader:
        rows += 1
        disasters.add(r["disasterNumber"])
        last_refresh = max(last_refresh, r["lastRefresh"] or "")
    if rows < 50_000:
        raise RuntimeError(f"only {rows:,} rows; the full dataset has 70,000+")
    return rows, len(disasters), last_refresh


def drop_stale_checksums():
    """Remove checksums.sha256 lines for raw files that no longer exist (e.g. the old FEMA file name)."""
    sums = read_checksums()
    keep = {n: d for n, d in sums.items() if (RAW_DIR / n).exists()}
    if len(keep) != len(sums):
        CHECKSUM_FILE.write_text("".join(f"{d}  {n}\n" for n, d in sorted(keep.items())))
        print("Removed checksum lines for missing files: " + ", ".join(sorted(set(sums) - set(keep))))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="overwrite an existing raw file")
    args = ap.parse_args()

    drop_stale_checksums()
    if FEMA_RAW_OUT.exists() and not args.force:
        print(f"{FEMA_RAW_OUT} already exists; raw files are not overwritten (use --force). Re-recording checksum.")
        record_checksum(FEMA_RAW_OUT)
        return 0

    print(f"Downloading {URL} (about 25 MB)")
    data = fetch(URL)
    rows, n_disasters, last_refresh = sanity_check(data)

    FEMA_RAW_OUT.parent.mkdir(parents=True, exist_ok=True)
    FEMA_RAW_OUT.write_bytes(data)  # byte-for-byte, no re-encoding or newline translation
    digest = record_checksum(FEMA_RAW_OUT)
    assert sha256_file(FEMA_RAW_OUT) == digest

    meta = {
        "source_url": URL,
        "dataset_page": DATASET_PAGE,
        "api_endpoint": "DisasterDeclarationsSummaries",
        "api_version": "v2",
        "publisher": "Federal Emergency Management Agency (FEMA), U.S. Department of Homeland Security",
        "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fema_last_refresh": last_refresh,
        "bytes": len(data),
        "rows": rows,
        "distinct_disasters": n_disasters,
        "sha256": digest,
        "terms_of_use": "https://www.fema.gov/about/openfema/terms-conditions",
        "required_statement": STATEMENT,
    }
    FEMA_META.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"Saved {FEMA_RAW_OUT.name}: {rows:,} rows, {n_disasters:,} disasters, sha256 {digest[:12]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
