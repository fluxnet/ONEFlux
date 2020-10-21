# Changelog
Changes to ONEFlux will be documented in this file.

## 0.4.1-beta - 2020-10-21

Unauthorised modifications by Peter Isaac to get ONEFlux to run under Windows.  Tested on Windows 10 with the US-ARc example data set.

### Changed

- Moved location of executable files from ~/bin to ONEFlux\bin.  This allows the Windows executable files to be distributed when the user clones the repository.
- Created make file (ONEFlux\oneflux_steps\make_windows) for compilation under Windows using the GNU make utility and the gcc compiler, both installed via MinGW.  This required the following:
  - 	Copied common.c and common.o to all src directories, temporary until the handling of paths by GNU make under Windows is better understood.
  - 	All executable files are created in the src directories and must be copied to the ONEFlux\bin directory, temporary until an install rule is added to make_windows.
  - 	No clean up of object files, temporary until a clean rule is added to make_windows.
  - 	The ONEFlux\bin directory has to be created manually until the handling of paths by GNU make under Windows is better understood.
- 	Added check for OS to classes in wrappers.py, ".exe" added to executable name for Windows.
- 	Added check for OS to common.run_command() to handle differences in path treatment between *nix and Windows.
- 	Removed ustar_cp from self.drivers in wrappers.Pipeline(), temporary until a compiled version of ustar_cp is available for Windows.
- 	Use of relative paths replaced with absolute paths for meteo_proc and nee_proc.  Relative paths appear to be incorrectly handled by these programs under Windows.
- 	All modifications to code tagged with "# PRI".
- 	Updated version in ONEFlux\oneflux\__init__.py to 0.4.1-beta.

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