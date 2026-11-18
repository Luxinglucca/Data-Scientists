"""Shared helpers for the pipeline scripts (paths, checksums, state lists, NOAA parser).

Every script is meant to be run from anywhere; paths are resolved relative to the repo root.
"""
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
# Raw files currently sit in the repo root. If data/raw/ exists (planned layout), it is used instead,
# so nothing here needs editing after the files are moved.
RAW_DIR = ROOT / "data" / "raw" if (ROOT / "data" / "raw").is_dir() else ROOT
CLEANED_DIR = ROOT / "data" / "cleaned"
RESULTS_DIR = ROOT / "results"
CHECKSUM_FILE = RAW_DIR / "checksums.sha256"

# Raw file names (lowercase, descriptive). acquire_fred.py / acquire_fema.py should use the same names.
NOAA_RAW = RAW_DIR / "noaa_climdiv_tmpcst_raw.txt"
NOAA_META = RAW_DIR / "noaa_climdiv_tmpcst_raw.meta.json"
FRED_GLOB = "fred_*_raw.csv"  # one file per series, e.g. fred_ilur_raw.csv


def find_fema_raw():
    """FEMA's download keeps its default name (DisasterDeclarationsSummaries*.csv); also accept the planned name."""
    for pattern in ("DisasterDeclarationsSummaries*.csv", "fema_declarations_raw.csv"):
        hits = sorted(RAW_DIR.glob(pattern))
        if hits:
            return hits[0]
    return RAW_DIR / "DisasterDeclarationsSummaries.csv"


FEMA_RAW = find_fema_raw()
STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
    "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon",
    "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
    "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia",
    "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}
STATE_ABBRS = set(STATE_NAMES)  # 50 states + DC

# nClimDiv state-level codes: 001-048 alphabetical (contiguous states), 049 Hawaii, 050 Alaska.
# 101-110 are multi-state regions / national and 111+ are special regions: not states.
NOAA_STATE_CODES = {f"{i:03d}" for i in range(1, 51)}
NOAA_MISSING = -99.90
NOAA_LINE_LEN = 94  # 3 state + 1 division + 2 element + 4 year + 12 * 7 values


# ---------------------------------------------------------------- checksums
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_checksums():
    """Return {filename: sha256} from checksums.sha256 in RAW_DIR (sha256sum format)."""
    out = {}
    if CHECKSUM_FILE.exists():
        for line in CHECKSUM_FILE.read_text().splitlines():
            if line.strip():
                digest, name = line.split(None, 1)
                out[name.strip().lstrip("*")] = digest
    return out


def record_checksum(path):
    """Add or update one file's line in checksums.sha256 (compatible with `sha256sum -c`)."""
    path = Path(path)
    sums = read_checksums()
    sums[path.name] = sha256_file(path)
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHECKSUM_FILE.write_text("".join(f"{d}  {n}\n" for n, d in sorted(sums.items())))
    return sums[path.name]


# ---------------------------------------------------------------- NOAA parser
def read_climdiv(path):
    """Parse a climdiv-*st fixed-width file.

    Returns (df, n_bad_lines). df has state_code, division, element, year, m01..m12 (floats).
    Lines of the wrong length or with unparseable numbers are skipped and counted.
    """
    rows, bad = [], 0
    with open(path, encoding="ascii", errors="replace") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line.strip():
                continue
            if len(line) < NOAA_LINE_LEN or line[NOAA_LINE_LEN:].strip():
                bad += 1
                continue
            try:
                vals = [float(line[10 + 7 * i: 17 + 7 * i]) for i in range(12)]
                year = int(line[6:10])
            except ValueError:
                bad += 1
                continue
            rows.append([line[0:3], line[3], line[4:6], year, *vals])
    cols = ["state_code", "division", "element", "year"] + [f"m{m:02d}" for m in range(1, 13)]
    return pd.DataFrame(rows, columns=cols), bad


# ---------------------------------------------------------------- cleaning log
class CleaningLog:
    """Collects (step, rows_affected, note) and writes results/cleaning_log_<source>.csv."""

    def __init__(self, source):
        self.source = source
        self.entries = []

    def add(self, step, rows, note=""):
        self.entries.append({"step": step, "rows_affected": int(rows), "note": note})
        print(f"[{self.source}] {step}: {int(rows):,} {note}")

    def write(self):
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULTS_DIR / f"cleaning_log_{self.source}.csv"
        pd.DataFrame(self.entries).to_csv(out, index=False)
        return out
