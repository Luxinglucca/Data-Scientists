**Overview**

This project is aimed to analyze how weather conditions as well as weather-related disasters are related to US economic outcomes.
We will integrate three datasets, FRED's monthly state economic indicators, monthly state climate data from NOAA NCEI, and federal declarations
of disasters from OpenFEMA. These sources link data by state as well as date (year & month).

We are going to focus on acquisition, a pre-integration quality check, cleaning, integration, a post-integration quality check, and an analysis
since this is a data curation project. We are going to use Python scripts to implement workflow so that this project runs from raw data acquisition
to our final results. We are going to store the data as versioned raw files as well as a SQLite database. 

**Team**

[name]: Team Lead
- set up repo, monitor workflow, check reproducibility, release management
  
[name]: Acquisition & Ethics
- API key handling, FRED and OpenFEMA acquisition scripts, review terms of use and licensing
  
[name]: Quality & Cleaning
- NOAA acquisition, pre and post-integration quality checks, cleaning scripts
  
[name]: Analysis & Documentation
- Schema design, integration scripts, analysis, metadata/data dictionary, final report

**Research Questions**

1. Are months with extreme temperature in a state associated with changes in that state's unemployment rate and nonfarm
   employment in the following 1-6 months?
2. Are FEMA declared weather-related disasters (hurricanes, floods, severe storms, etc) associated with changes in state
   employment compared to months without disasters?
3. Do these associations differ by season or by region?

**Datasets**

**Timeline**

**Constraints**

**Gaps**
