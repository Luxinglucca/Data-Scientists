# Project Plan: How Weather and Disasters Affect State Employment

## Overview

This project is aimed to analyze how weather conditions as well as weather-related disasters are related to US economic outcomes.
We will integrate three datasets, FRED's monthly state economic indicators, monthly state climate data from NOAA NCEI, and federal declarations
of disasters from OpenFEMA. These sources link data by state as well as date (year & month).

We are going to focus on acquisition, a pre-integration quality check, cleaning, integration, a post-integration quality check, and an analysis
since this is a data curation project. We are going to use Python scripts to implement workflow so that this project runs from raw data acquisition
to our final results. We are going to store the data as versioned raw files as well as a SQLite database. 

## Team

Lucas: Team Lead / Workflow & Reproducibility
- Set up repository structure and naming conventions
- Build the automated workflow with Snakemake
- Declare dependencies (requirements.txt with pinned versions) and maintain the reproducing instructions
- Test the full pipeline on a fresh clone before each release, manage project-plan, status-report, and final-project releases
  
Sam: Acquisition & Ethics
- FRED and OpenFEMA acquisition scripts, review terms of use and licensing
  
Helen: Quality & Cleaning
- NOAA acquisition, pre and post-integration quality checks, cleaning scripts
  
Yash: Analysis & Documentation
- Schema design, integration scripts, analysis, metadata/data dictionary, final report

## Research Questions

1. Are months with extreme temperature in a state associated with changes in that state's unemployment rate and nonfarm
   employment in the following 1-6 months?
2. Are FEMA declared weather-related disasters (hurricanes, floods, severe storms, etc) associated with changes in state
   employment compared to months without disasters?
3. Do these associations differ by season or by region?

## Datasets

### FRED: State Unemployment Rate and Total Nonfarm Employment
- **Source/URL:** https://fred.stlouisfed.org
- **Publisher:** Federal Reserve Bank of St. Louis, which republishes data originally produced by the U.S. Bureau of Labor Statistics (LAUS and CES programs)
- **Format:** CSV, downloaded from public download link (no API key needed)
- **Size:** Two series for each of the 50 states plus DC, monthly. Roughly 440 rows per series from 1990 on
- **Years covered:** Unemployment rate from 1976; nonfarm employment from 1990. Our analysis window starts in 1990 when both are available.
- **License/terms:** The BLS series are labeled public domain on FRED, with citation requested ("Source: U.S. Bureau of Labor Statistics, retrieved from FRED"). FRED's own terms limit storing and redistributing FRED content, so we will confirm each series' label before committing it (see Constraints).
- **Join:** Each series ID maps to a state through build_state_id_map.py. Joined on state + year-month.

### OpenFEMA: Disaster Declarations Summaries (v2)
- **Source/URL:** https://www.fema.gov/openfema-data-page/disaster-declarations-summaries-v2
- **Publisher:** Federal Emergency Management Agency (FEMA), U.S. Department of Homeland Security
- **Format:** CSV, about 24 MB
- **Size:** 70,571 rows covering 5,283 disasters. Each row is one declared county or area within a disaster, not one disaster.
- **Years covered:** Declarations from May 1953 to October 2026 (as of our 10/2026 download)
- **License/terms:** Public data under the OpenFEMA Terms and Conditions. We must cite the dataset URL and our download date, include the statement "This product uses the Federal Emergency Management Agency's OpenFEMA API, but is not endorsed by FEMA," and not use FEMA logos.
- **Join:** Joined on the `state` column (two-letter code, also `fipsStateCode`) + year-month taken from `incidentBeginDate`. County rows are aggregated to state-month.

### NOAA NCEI: Statewide Average Temperature (nClimDiv)
- **Source/URL:** https://www.ncei.noaa.gov/pub/data/cirs/climdiv/ (file climdiv-tmpcst, statewide monthly average temperature)
- **Publisher:** NOAA National Centers for Environmental Information (NCEI). Citation: Vose, R. S., et al. (2014), NOAA Monthly U.S. Climate Divisional Database (NClimDiv), doi:10.7289/V5M32STR
- **Format:** Fixed-width text file. Each line is one state and one year, with 12 monthly values in degrees Fahrenheit. This replaces the single-state, single-month Climate at a Glance export currently in the repo (data.csv).
- **Size:** 49 states (the contiguous 48 plus Alaska) times about 130 years, roughly 6,400 lines or about 77,000 state-months
- **Years covered:** 1895 to present for the contiguous states. Alaska starts in 1925. Hawaii and DC are not included.
- **License/terms:** U.S. government data, free to use. NOAA makes no warranty about accuracy, and users are responsible for judging fitness for use. We will cite the dataset DOI.
- **Join:** NOAA uses its own state codes (001 = Alabama through 048 = Wyoming alphabetically, 050 = Alaska), which build_state_id_map.py maps to state abbreviations. Joined on state + year-month after reshaping the 12 monthly columns into one row per month.

## Workflow, Storage & Reproducibility Plan

The pipeline will be built from separate & single-purpose Python scripts. They each will have defined inputs and outputs, and will be tied together by a Snakemake workflow. 

### Planned Stages

1. acquire_fred.py, acquire_noaa.py, acquire_fema.py - download raw data and record SHA-256 checksums
2. assess_raw_quality.py - pre-integration quality assessment checking for accuracy, completeness, timeliness, and consistency
3. clean_fred.py, clean_noaa.py, clean_fema.py - cleaning any issues with the data found in step 2
4. build_state_id_map.py - maps state names, abbreviations, FIPS codes, NOAA state codes, and FRED series IDs
5. join_datasets.py - merges/joins cleaned datasets on state & year-month and loads them into SQLite
6. assess_integrated_quality.py - post-integration quality assessment
7. analyze.py - analysis and graphs

To run the whole project, we'll type snakemake --cores 1 in the main project folder, and it will go from raw data to final results. Each step lists the files it needs and the files it makes, so we can rerun just one step if something changes, and it's easy to trace where every output came from.

### Storage and Organization

The raw files will be unmodified. Every step after will write to a different location and each step will be easily traceable.

All the files will use lowercase & descriptive names such as fema_declarations_raw.csv and not data.csv.

```
data/raw/          unmodified downloads + checksums.sha256

data/cleaned/      cleaned per-source files

data/integrated/   joined dataset + project.db 

scripts/           one script per workflow stage

results/           quality reports, analysis tables, figures

docs/              data dictionary, metadata, workflow diagram

Snakefile, requirements.txt, LICENSE, README.md
```

### Reproducibility

Anyone should be able to download our repo and run it without changing anything. To make that work, all file paths will be relative to the project folder, meaning that no paths will point to one person's computer. We won't need API keys because all three sources have public download links. We'll list the exact package versions in requirements.txt and say which version of Python we used. Also, the raw data will be committed to the repo, since every file is under 50 MB. Before each submission, we'll test it by downloading a fresh copy and running everything from scratch.

## Timeline

### By project plan (10/22/2026)
- Set up repo folders and submit the project-plan release (Lucas)
- Write FRED and FEMA dataset descriptions and review terms of use (Sam)
- Write NOAA dataset description and quality/cleaning constraints (Helen)
- Revise, tag, and submit report, ensuring rubric sections are met within the project plan (Yash)
- Write timeline and explore further gaps (Yash)
### By status report (11/19/2026)
- Set up Snakefile and requirements.txt (Lucas)
- Connect download scripts to the workflow (Lucas)
- Test on a fresh copy and submit the status-report release (Lucas)
- Write acquire_fred.py and acquire_fema.py to download raw data and record checksums and download dates (Sam)
- Move the FEMA file into data/raw/ and rename it to match our naming rules (Sam)
- Write down licenses and required citations for each source in docs/ (Sam)
- Write acquire_noaa.py to download the NOAA temperature file (Helen)
- Write assess_raw_quality.py to check all three sources before joining (Helen)
- Write cleaning scripts for FRED, NOAA, and FEMA (Helen)
- Writer down and summarize challenges and problems we have encountered, as well as how we went about solving them (Yash)
- Update the timeline to reflect adaptable deadlines and changing scopes (Yash)
- Begin exploring modeling methods and correlation analysis for final submission (Yash)

### By final (12/08/2026)
- Write project code (Yash & Sam)
- Get the whole project running with one command (Lucas)
- Write the reproducing steps in the README (Lucas)
- Final fresh-copy test and submit the final-project release (Lucas)
- Check that raw file checksums still match on a fresh copy (Sam)
- Write the data sources and ethics section of the README and final report (Sam)
- Write assess_integrated_quality.py and save the quality report in results/ (Helen)
- Revise and submit all required deliverables (Yash)
- Ensure project aligns with rubric expectations (Yash)

## Constraints
- OpenFEMA data is updated continuously, so downloading it later might give a different file. We’ll save the copy we use in the repo, record the exact date we downloaded it, and include its checksum so anyone can confirm they’re using the same file.
- FRED's terms limit sharing its data, but our plan puts raw data in a public repo. The series we use come from the BLS and are public domain, so this should be fine, but we'll double-check each one. If any series isn't public domain, we'll download it when the pipeline runs instead of saving it in the repo.
- The FEMA file has one row per county, not per disaster, and it includes non-weather events like COVID-19 (about 7,900 rows) and U.S. territories. We'll need to filter these out and combine rows before joining.
- NOAA doesn't have data for Hawaii or DC, and Alaska only starts in 1925. The temperature question (RQ1) will cover 49 states, while the disaster question (RQ2) can include all 50 plus DC.
- The three sources end at different months, and the most recent numbers from FRED and NOAA are early estimates that can change later. NOAA also marks missing months with -99.90. We'll cut all sources to the same end month and treat -99.90 as missing.
- Average temperatures vary greatly in the U.S. by state, so using historical averages for that state may be better
- FEMA declaration timings matter, so this may need to be adjusted

## Gaps

- None of us have used Snakemake on a full project before. We may need help from the TAs or professor to get the workflow running.
- Our team has both Windows and Mac computers. The scripts could run for one person and not work for another. We'll need to test the workflow on both before each submission.
- There may be data issues that we have not yet discovered, along with hidden correlations and potentially non-causal variables that could confound our analysis
- Employment could change because of unrelated economic conditions that we need to adjust and account for, this is essential to a clean analysis, so we are seeking reccommendations as to how to approach this
