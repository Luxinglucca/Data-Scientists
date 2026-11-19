# Milestone 3: Interim Status Report

## Updates on Tasks (+ artifact links)

- Set up Snakefile and requirements.txt (Lucas) (Status = Complete)
  Artifacts:
    - [Snakefile](Snakefile)
    - [requirements.txt](requirements.txt)
    - [.gitattributes](.gitattributes)
  
- Connect download scripts to the workflow (Lucas) (Status = In progress, acquire_noaa.py is connected, FEMA and FRED are waiting on the download scripts)
  Artifact: [Snakefile](Snakefile)
  

- Test on a fresh copy and submit the status-report release (Lucas) (Status = In progress, fresh-copy test passed on Windows)
  
- Write acquire_fred.py and acquire_fema.py to download raw data and record checksums and download dates (Sam) (Status = Complete)
  Artifacts:
    - [acquire_fred.py](scripts/acquire_fred.py)
    - [acquire_fema.py](scripts/acquire_fema.py)
- Move the FEMA file into data/raw/ and rename it to match our naming rules (Sam) (Status = Complete)
  Artifact: [fema_declarations_raw.csv](data/raw/fema_declarations_raw.csv)
- Write down licenses and required citations for each source in docs/ (Sam) (Status = Complete)
  Artifact: [data_sources_and_licenses.md](docs/data_sources_and_licenses.md)
- Write acquire_noaa.py to download the NOAA temperature file (Status = Complete)
  Artifact: [acquire_noaa.py](scripts/acquire_noaa.py)
  
- Write assess_raw_quality.py to check all three sources before joining (Status = Complete)
  Artifact: [assess_raw_quality.py](scripts/assess_raw_quality.py)
  
- Write cleaning scripts for FRED, NOAA, and FEMA (Status = Complete)
  Artifacts:
    - [clean_fred.py](scripts/clean_fred.py)
    - [clean_noaa.py](scripts/clean_noaa.py)
    - [clean_fema.py](scripts/clean_fema.py)
  
- Writer down and summarize challenges and problems we have encountered, as well as how we went about solving them (Yash)
- Artifacts:
    - See below
- Update the timeline to reflect adaptable deadlines and changing scopes (Yash):
    - See below
- Begin exploring modeling methods and correlation analysis for final submission (Yash)
    - See Below

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

Our course project plan was received very well with no comments and a perfect score That being said, we have had to move back some deadlines, particularly as they relate to building and writing out the code, to after Thanksgiving break due to our busy schedules (this is further outlined in the challenges section). 

Outside of timeline shifts, nothing has materially changed for the project, its scope, or the final result. 

## Challenges + Planned Solutions
- FRED's website blocked our download script at first because the script identified itself as a web browser. We changed how the script identifies itself, and all 102 series downloaded. (Sam)
- FRED's terms of use generally restrict sharing its data. We checked and confirmed that the BLS series we use are public domain, so committing them to the repo is allowed. Any copyrighted series we add later will be downloaded when the pipeline runs instead of being committed. (Sam)

**Timeliness Given Exams & Recruitment** --> One thing our team has struggled with throughout the project has been getting our schedules to align so we can come together and generate deliverables in coordination with one another rather than in a vacuum. This has been particularly difficult as we are all in the midst of a tough recruiting season and midterm season tends to line up with November / December. Mitigating this challenge, we have been highly communicative using online measures such as zoom meetings and our text groupchat, which enables us all to stay up to date and current. When we return from break as well, we plan on having multiple in-person team meetings before finals begin to iron out the remainder of the final project and ensure we are all on track to receive a good grade.

**GitHub Use** --> Our team is not entirely familiar with how to use GitHub, and we are learning as we make our way through the project. To solve this, I have personally consulted many articles on using push and pull requests through VS code, ensuring my software is up to date, and leaning on those in my group who are more experienced with the platform. Going forward, our more experienced members will be taking control of the repository, ensuring that everything is up to submission standards.

**Navigating Ethics** --> This is the first time in a data science course where we are being asked to properly cite and accredit all the sources for a project. Knowing this, there are numerous hurdles to ensuring our information is accurate and up to date to prevent any data violations as we build our final product. Mitigating, we plan on attending office hours to ensure our citations, disclaimers, and README section is properly formatted and up to snuff for submission. 

## Modeling Methods

### Individual Team Member Contribution Summary
- **Helen:** I was responsible for NOAA data acquisition, raw data quality assessment, and cleaning the project's three
  data sources. I created acquire_noaa.py to download the NOAA temperature dataset, developed assess_raw_quality.py to
  check the FRED, NOAA, and FEMA datasets for quality issues before integration, and wrote individual cleaning scripts for
  FRED, NOAA, and FEMA to address inconsistencies and prepare the data for integration.
- **Sam:** I wrote acquire_fred.py and acquire_fema.py. Fred downloaded 102 series - the unemployment rate and nonfarm employment for the 50 states and DC. Fema downloaded the disaster declarations file. Both scripts record checksums and download dates, and neither overwrites raw data that is already saved. Also renamed the FEMA file to follow our naming rules, and updated the Snakefile to match. Documented each source's license, the required citation, and FEMA's non endorsement statement in docs/. Fixed the FRED download problem from the Challenges section.
- **Lucas:** I was responsible for the workflow and reproducibility. I set up the Snakefile so the acquire, raw quality
  assessment, and cleaning steps run in order with one command. I also made requirements.txt with pinned package versions.
  When I tested on a fresh copy of the repo on Windows, the raw data checksums didn't match because git was changing the
  line endings in the files. To fix this I added a .gitattributes file. I also set up the workflow so re-running it
  can't delete or re-download the raw data. Next I'm doing the full fresh-copy test and the status-report release.
- **Yash:** 




