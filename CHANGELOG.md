# Changelog
Changes to ONEFlux

## v1.3.6-rc - 2026-05-29
- adding gf indexes for gf_mds and nee_proc by @ARibecaJob in #137
- Add check inputs function to remove empty variables by @gilbertozp in #139
- Modelled ustar updates by @luca-difiore in #140

## v1.3.5-rc - 2026-03-10
### What's Changed
- Update how context txt files are stored in ONEFlux repo by @gilbertozp in #132
- Fixes long-gap implementation handling of skipped NT/DT partitioning by @gilbertozp in #133
- URE v1.021: new parameters have been added to specify MEF filter files. by @ARibecaJob in #131
- Add parameter handling for MEF filter(s) computed in nee_proc to be used in ure by @gilbertozp in #134
- Add parameters to main runoneflux script to allow skipping partitioning steps by @gilbertozp in #135


## v1.3.4-rc - 2026-01-16
### What's Changed
- Adding a first version of synthetic ustar module by @luca-difiore in #130
- Improved handling of \_REF variables not being generated - reference column fixes by @ARibecaJob in #126


## v1.3.3-rc - 2026-01-09
### What's Changed
- Fix error in diagnostic plots when VUT version of NEE not calculated by @gilbertozp in #125
- qc_auto v1.02 - qc_auto now produces the input file for energy_proc even if H and/or LE are missing, setting them all with values -9999 by @ARibecaJob in #123
- qc_auto v1.03: qc_auto now calculates SW_IN from PPFD_IN either is SW_IN is all invalid or missing by @ARibecaJob in #124
- Update text for data readme and license files added to data packages by @gilbertozp in #127


## v1.3.2-rc - 2025-12-12
### Changed
- Add back ERA files and fixes BIF generation issues


## v1.3.1-rc - 2025-12-10
### Changed
- Add missing runtime specific metadata (including network and processing center), fix order of BIF outputs, and update settings template


## v1.3.0-rc - 2025-12-09
### Changed
- Updates filename conventions; add metadata files in BIF format to each individual site data package; and add LICENSE and README files with additional usage information to site data package.


## v1.1.3-rc - 2025-11-30
### Changed
- Fix handling of AUX file generation when VUT execution fails


## v0.8.5-rc - 2025-11-30
### Changed
- Fix handling of AUX file generation when VUT execution fails


## v1.1.2-rc - 2025-11-09
### Changed
- Fixes for nee_proc and energy_proc; additional information logged; updated defaults to settings


## v0.8.4-rc - 2025-11-09
### Changed
- Fixes for nee_proc and energy_proc; additional information logged; updated defaults to settings


## v1.1.1-rc - 2025-10-23
### Changed
- Fixes dynamic header generation and restores default pipeline steps configuration


## v0.8.3-rc - 2025-10-23
### Changed
- Fixes dynamic header generation


## v1.1.0-rc - 2025-10-14
### Added
- Preparations for changes to long gaps and full record flux partitioning.


## v0.8.2-rc - 2025-10-01
### Changed
- Fixes bugs from implementation of skipping partitioning steps.


## v0.8.1-rc - 2025-09-25
### Changed 
- Fixes for variable declaration to be compatible with GCC versions 10 and newer, and fixing hardcoded parameter in the downscaling code


## v0.8.0-rc - 2025-03-21
### Added
- Support for CUT only thresholds, custom driver variables for MDS gapfilling, skipping flux partitioning steps

### Changed
- Fixes for soil variable handling


## v0.6.0-rc - 2025-01-10
### Added
- New integrated downscaling code

### Changed
- Removing support for Sundown Reference partitioning method results


## v0.5.0-rc - 2024-09-30
### Changed
- Bug fixes for MDS gapfilling shared modules


## v0.4.1-rc - 2022-03-25
### Changed
- Bug fixes and handling for new ERA data product


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