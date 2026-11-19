# Data Sources, Licenses, and Required Citations

This file lists where each raw dataset comes from, the terms we are using it under, and how it must be cited in the README, final report, and any figures.

Download dates and SHA-256 checksums for each raw file are recorded in `data/raw/checksums.sha256` and the `*.meta.json` files next to the raw data.

## Summary

| Source | Publisher | Raw files | License / terms | Committed to repo? |
|---|---|---|---|---|
| FRED state employment series | Federal Reserve Bank of St. Louis (data from U.S. Bureau of Labor Statistics) | `data/raw/fred_<series>_raw.csv` (102 files) | BLS series are public domain; citation requested. FRED Terms of Use apply. | Yes |
| OpenFEMA Disaster Declarations Summaries (v2) | FEMA, U.S. Department of Homeland Security | `data/raw/fema_declarations_raw.csv` | U.S. government data; OpenFEMA Terms and Conditions apply. Citation and non-endorsement statement required. | Yes |
| NOAA nClimDiv statewide temperature | NOAA National Centers for Environmental Information (NCEI) | `data/raw/noaa_climdiv_tmpcst_raw.txt` | U.S. government data, free to use; no warranty. Citation by DOI. | Yes |

## FRED: State Unemployment Rate and Total Nonfarm Employment

- **Series used:** `<ST>UR` (unemployment rate, %, seasonally adjusted) and `<ST>NA` (all employees, total nonfarm, thousands, seasonally adjusted) for the 50 states and DC.
- **Download link:** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>` (downloaded by `scripts/acquire_fred.py`)
- **Original source:** U.S. Bureau of Labor Statistics, State Employment and Unemployment release (LAUS and CES programs)
- **Terms:** https://fred.stlouisfed.org/legal/
- **Copyright status:** Each series page is labeled "Public Domain: Citation Requested." Public domain series can be used and shared with a citation.
- **Note on FRED's terms:** FRED's Terms of Use restrict storing and redistributing FRED content in general. We rely on the public domain status of these BLS series to commit them to a public repo. If we add any series labeled "Copyrighted," it will not be committed and will be downloaded at run time instead.
- **Required citation (one per series):**
  > U.S. Bureau of Labor Statistics, Unemployment Rate in Illinois [ILUR], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/ILUR, accessed (download date).
- **Short form for figures:** "Source: U.S. Bureau of Labor Statistics, via FRED."

## OpenFEMA: Disaster Declarations Summaries (v2)

- **Download link:** https://www.fema.gov/api/open/v2/DisasterDeclarationsSummaries.csv (downloaded by `scripts/acquire_fema.py`)
- **Dataset page:** https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2
- **Terms:** https://www.fema.gov/about/openfema/terms-conditions
- **What the terms require:**
  - Cite the endpoint and version (DisasterDeclarationsSummaries, v2), preferably by URL.
  - Cite the date (and preferably time) the data was downloaded. This is recorded in `data/raw/fema_declarations_raw.meta.json`.
  - Include this statement in the README and final report:
    > This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA.
  - Do not use FEMA or DHS logos, and do not imply FEMA endorses our work.
  - Do not present modified data as official FEMA data. Our cleaned and integrated files are labeled as our own derived versions.
- **Required citation:**
  > Federal Emergency Management Agency (FEMA). OpenFEMA Dataset: Disaster Declarations Summaries - v2. https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2, downloaded (date and time UTC).

## NOAA NCEI: Statewide Average Temperature (nClimDiv)

- **Download location:** https://www.ncei.noaa.gov/pub/data/cirs/climdiv/ (file `climdiv-tmpcst`, downloaded by `scripts/acquire_noaa.py`)
- **Terms:** Free U.S. government data. NOAA and NCEI make no warranty about accuracy or completeness; users are responsible for judging whether the data fits their purpose.
- **Required citation:**
  > Vose, R. S., et al. (2014). NOAA Monthly U.S. Climate Divisional Database (NClimDiv). NOAA National Climatic Data Center. doi:10.7289/V5M32STR

## Ethics and Responsible Use

- **No personal data.** All three datasets are aggregate public statistics (state-level or county-level). No individuals can be identified, so there are no privacy concerns or need for IRB review.
- **Respectful downloading.** No API keys or logins are used. The FRED script requests one series at a time with a pause between requests, and none of the acquire scripts re-download files that are already saved. Each source is downloaded once and the copy we use is committed, so re-running the pipeline does not put repeated load on these servers.
- **Accurate representation.** Our results show associations, not causes. FEMA declarations reflect a political and administrative process (a governor's request and a federal decision), not just how severe a disaster was. We will say this in the final report so the data is not overstated.
- **Data changes over time.** OpenFEMA updates continuously, and the newest FRED and NOAA months are preliminary and get revised. Download dates and checksums let anyone confirm which version we used.
