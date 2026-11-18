"""Download the NOAA nClimDiv statewide average temperature file (climdiv-tmpcst).

Writes, unmodified, next to the other raw files (repo root, or data/raw/ if it exists):
    noaa_climdiv_tmpcst_raw.txt        the file exactly as NOAA serves it
    noaa_climdiv_tmpcst_raw.meta.json  source URL, NOAA's versioned file name, download time (UTC), SHA-256
and records the SHA-256 in checksums.sha256 in the same folder.

NOAA publishes versioned names (e.g. climdiv-tmpcst-v1.0.0-20261105) that change every month, so the
script reads the directory listing and picks the newest one. The old /pub/data/cirs/climdiv/ path now
redirects to /monitoring-content/data/us/climdiv/monthly/current/; both are tried.

Raw files are never overwritten: re-running skips the download unless --force is given.
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from common import NOAA_LINE_LEN, NOAA_META, NOAA_RAW, record_checksum, sha256_file

BASE_URLS = [
    "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/",
    "https://www.ncei.noaa.gov/monitoring-content/data/us/climdiv/monthly/current/",
]
# Matches climdiv-tmpcst-v1.0.0-20261105 but not climdiv-norm-tmpcst-... (needs the href quote before "climdiv").
FILE_RE = re.compile(r'href="(?:[^"]*/)?(climdiv-tmpcst-v[0-9.]+-(\d{8}))"')
HEADERS = {"User-Agent": "Mozilla/5.0 (course project; data acquisition script)"}


def fetch(url, retries=3, timeout=60):
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.geturl()
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            print(f"  attempt {attempt}/{retries} failed for {url}: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


def find_latest():
    """Return (file_url, noaa_file_name, yyyymmdd) for the newest climdiv-tmpcst listing entry."""
    for base in BASE_URLS:
        try:
            html, final_url = fetch(base)
        except RuntimeError as e:
            print(e)
            continue
        found = sorted(set(FILE_RE.findall(html.decode("utf-8", errors="replace"))), key=lambda t: t[1])
        if found:
            name, stamp = found[-1]
            if not final_url.endswith("/"):
                final_url += "/"
            return final_url + name, name, stamp
        print(f"  no climdiv-tmpcst file found in listing at {base}")
    raise RuntimeError("could not locate climdiv-tmpcst in any NOAA directory listing")


def sanity_check(data):
    """Cheap check that we got the data file and not an HTML error page."""
    lines = data.decode("ascii", errors="replace").splitlines()
    if len(lines) < 1000:
        raise RuntimeError(f"only {len(lines)} lines; expected several thousand")
    bad = [i for i, l in enumerate(lines, 1) if len(l) < NOAA_LINE_LEN or l[NOAA_LINE_LEN:].strip()]
    if bad:
        raise RuntimeError(f"{len(bad)} lines are not {NOAA_LINE_LEN} characters wide (first: line {bad[0]})")
    return len(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="overwrite an existing raw file")
    args = ap.parse_args()

    if NOAA_RAW.exists() and not args.force:
        print(f"{NOAA_RAW} already exists; raw files are not overwritten (use --force). Re-recording checksum.")
        record_checksum(NOAA_RAW)
        return 0

    url, noaa_name, stamp = find_latest()
    print(f"Downloading {noaa_name} from {url}")
    data, _ = fetch(url, timeout=120)
    n_lines = sanity_check(data)

    NOAA_RAW.parent.mkdir(parents=True, exist_ok=True)
    NOAA_RAW.write_bytes(data)  # byte-for-byte, no re-encoding or newline translation
    digest = record_checksum(NOAA_RAW)

    meta = {
        "source_url": url,
        "noaa_file_name": noaa_name,
        "noaa_file_version_date": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}",
        "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bytes": len(data),
        "lines": n_lines,
        "sha256": digest,
        "citation": "Vose, R. S., et al. (2014), NOAA Monthly U.S. Climate Divisional Database (NClimDiv), "
                    "NOAA NCEI, doi:10.7289/V5M32STR",
    }
    NOAA_META.write_text(json.dumps(meta, indent=2) + "\n")
    assert sha256_file(NOAA_RAW) == digest
    print(f"Saved {NOAA_RAW.name}: {n_lines:,} lines, sha256 {digest[:12]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
