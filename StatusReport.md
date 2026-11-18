# Milestone 3: Interim Status Report

## Updates on Tasks (+ artifact links)

- Set up Snakefile and requirements.txt (Lucas)
- Connect download scripts to the workflow (Lucas)
- Test on a fresh copy and submit the status-report release (Lucas)
- Write acquire_fred.py and acquire_fema.py to download raw data and record checksums and download dates (Sam)
- Move the FEMA file into data/raw/ and rename it to match our naming rules (Sam)
- Write down licenses and required citations for each source in docs/ (Sam)
- Write acquire_noaa.py to download the NOAA temperature file
- Status = Complete
- Artifact: [acquire_noaa.py](scripts/acquire_noaa.py)
  
- Write assess_raw_quality.py to check all three sources before joining
- Status = Complete
- Artifact: [assess_raw_quality.py](scripts/assess_raw_quality.py)
  
- Write cleaning scripts for FRED, NOAA, and FEMA
- Status = Complete
- Artifacts:
    - [clean_fred.py](scripts/clean_fred.py)
    - [clean_noaa.py](scripts/clean_noaa.py)
    - [clean_fema.py](scripts/clean_fema.py)
  
- Writer down and summarize challenges and problems we have encountered, as well as how we went about solving them (Yash)
- Update the timeline to reflect adaptable deadlines and changing scopes (Yash)
- Begin exploring modeling methods and correlation analysis for final submission (Yash)

## Updated Timeline

### Everything Planned up until 11/19/2026 = Complete
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


## Changes to Project Plan Itself + Feedback from Project Plan

1. 

## Challenges + Planned Solutions
- 

### Individual Team Member Contribution Summary
- **Helen:** I was responsible for NOAA data acquisition, raw data quality assessment, and cleaning the project's three
  data sources. I created acquire_noaa.py to download the NOAA temperature dataset, developed assess_raw_quality.py to
  check the FRED, NOAA, and FEMA datasets for quality issues before integration, and wrote individual cleaning scripts for
  FRED, NOAA, and FEMA to address inconsistencies and prepare the data for integration.
- **Sam:** 
- **Lucas:** 
- **Yash:** 




