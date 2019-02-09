# Changelog
Changes to ONEFlux will be documented in this file.


## 0.4.0-beta - 2019-02-08
### Added
- Add changelog
- Add optional handling of missing downscaling input files to not stop execution
- Add options for processing and data version outputs



### Changed
- Fix nighttime GPP calculation (was being incorrectly gapfilled after partitioning step)
- Fix hourly resolution bug to correctly run sites at hourly resolution using `--recint hr` flag
- Fix order of USTAR percentiles computation, preserving 50 percentile and UST50 version
- Minor code clean-up
- Pending entries to log files will always be saved before exiting
- More descriptive log file name defaults
- Fix UNCAUX step handling of missing years
- Fix AUXNEE VUT handling for missing years
- Fix path handling for AUX file generation
- Adding and clarifying error/warnings messages



### Removed
- File containing information only relevant to creation of FLUXNET dataset (oneflux/pipeline/fluxnet2015_sites_tiers.py)


## 0.3.0 - 2018-09-06
### Added
- First beta version
- Added steps (oneflux_steps/): qc_auto, ustar_mp, ustar_cp, meteo_proc, energy_proc, nee_proc, ure
- Added driving code (oneflux/pipeline/)
- Added nighttime and daytime partitioning code (oneflux/partition/)