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
  
[name]: Acquisition & Ethics
- FRED and OpenFEMA acquisition scripts, review terms of use and licensing
  
[name]: Quality & Cleaning
- NOAA acquisition, pre and post-integration quality checks, cleaning scripts
  
[name]: Analysis & Documentation
- Schema design, integration scripts, analysis, metadata/data dictionary, final report

## Research Questions

1. Are months with extreme temperature in a state associated with changes in that state's unemployment rate and nonfarm
   employment in the following 1-6 months?
2. Are FEMA declared weather-related disasters (hurricanes, floods, severe storms, etc) associated with changes in state
   employment compared to months without disasters?
3. Do these associations differ by season or by region?

## Datasets

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

### By status report (11/19/2026)
- Set up Snakefile and requirements.txt (Lucas)
- Connect download scripts to the workflow (Lucas)
- Test on a fresh copy and submit the status-report release (Lucas)

### By final (12/08/2026)
- Get the whole project running with one command (Lucas)
- Write the reproducing steps in the README (Lucas)
- Final fresh-copy test and submit the final-project release (Lucas)

## Constraints

- OpenFEMA data is updated continuously, so downloading it later might give a different file. We’ll save the copy we use in the repo, record the exact date we downloaded it, and include its checksum so anyone can confirm they’re using the same file.

## Gaps

- None of us have used Snakemake on a full project before. We may need help from the TAs or professor to get the workflow running.
- Our team has both Windows and Mac computers. The scripts could run for one person and not work for another. We'll need to test the workflow on both before each submission.