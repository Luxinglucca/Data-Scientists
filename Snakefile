# Run from the repo root:
#   snakemake --cores 1 --forceall
#
# Order steps run in:
#   1. acquire
#   2. assess raw quality
#   3. clean

# Raw data files (committed to the repo)
NOAA_RAW = "data/raw/noaa_climdiv_tmpcst_raw.txt"
NOAA_META = "data/raw/noaa_climdiv_tmpcst_raw.meta.json"
FEMA_RAW = "data/raw/fema_declarations_raw.csv"
CHECKSUMS = "data/raw/checksums.sha256"



rule all:
    input:
        "results/raw_quality_report.md",
        "data/cleaned/noaa_state_monthly_temperature_cleaned.csv",
        "data/cleaned/fema_declarations_cleaned.csv",


#  1. acquire

rule acquire_noaa:
    output:
        touch("logs/acquire_noaa.done"),
    shell:
        "python scripts/acquire_noaa.py"

rule acquire_fema:
    output:
        touch("logs/acquire_fema.done"),
    shell:
        "python scripts/acquire_fema.py"

rule acquire_fred:
    output:
        touch("logs/acquire_fred.done"),
    shell:
        "python scripts/acquire_fred.py"


# 2. assess raw quality

rule assess_raw_quality:
    input:
        "logs/acquire_noaa.done",
        NOAA_RAW,
        NOAA_META,
        FEMA_RAW,
        CHECKSUMS,
    output:
        "results/raw_quality_checks.csv",
        "results/raw_quality_report.md",
    shell:
        "python scripts/assess_raw_quality.py"


# 3. clean

rule clean_noaa:
    input:
        NOAA_RAW,
        "results/raw_quality_report.md",
    output:
        "data/cleaned/noaa_state_monthly_temperature_cleaned.csv",
        "results/cleaning_log_noaa.csv",
    shell:
        "python scripts/clean_noaa.py"

rule clean_fema:
    input:
        FEMA_RAW,
        "results/raw_quality_report.md",
    output:
        "data/cleaned/fema_declarations_cleaned.csv",
        "results/cleaning_log_fema.csv",
    shell:
        "python scripts/clean_fema.py"

rule clean_fred:
    input:
        "logs/acquire_fred.done",
        "results/raw_quality_report.md",
    output:
        "data/cleaned/fred_state_monthly_cleaned.csv",
        "results/cleaning_log_fred.csv",
    shell:
        "python scripts/clean_fred.py"
