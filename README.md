# ONEFlux Processing Pipeline

ONEFlux (Open Network-Enabled Flux processing pipeline) is an eddy covariance data processing codes package jointly developed by the [AmeriFlux Management Project](https://ameriflux.lbl.gov/), the [European Fluxes Database](http://www.europe-fluxdata.eu/), and the [ICOS Ecosystem Thematic Centre](http://www.icos-etc.eu/icos/). ONEFlux is used for the standard processing and data product creation for these networks.

ONEFlux consolidates multiple computations to process half-hourly (or hourly) flux inputs in an automatic fashion, including friction velocity threshold estimation methods and filtering, gap-filling of micrometeorological and flux variables, partitioning of CO2 fluxes into ecosystem respiration and gross primary production, uncertainty estimates, and more.

The current version of the code is compatible with the code base used to create the [FLUXNET2015 dataset](https://fluxnet.fluxdata.org/data/fluxnet2015-dataset/), and data processed with ONEFlux can be used in conjunction with data from FLUXNET2015.

The pipeline controlling code uses **Python version 2.7** (it should work with Python version 3.5 or later, but was not fully tested with these versions; update of the code to Python 3 is ongoing).

**(THERE ARE CAVEATS AND KNOWN LIMITATIONS TO THIS CODE, PLEASE SEE [CAVEATS LIST](#caveats-and-known-limitations) BELOW.)** This iteration of the code is not fully in line with open source/free software development practices, but we intend to steadily move in that direction.


## Required data and metadata variables

To run ONEFlux, certain data variables and addtional information about the site and instrument configuration are needed. *Required* data variables must be available in the input data, otherwise the ONEFlux will not run. *Encouraged* data variables must be present for realated derived data products to be generated, and although ONEFlux will run if these are missing, not all products will be generated. *Suggested* data variables are supported by ONEFlux, but are not directly used for the generation of any derived data products.
  - Required: CO2, FC, H, LE, WS, USTAR, TA, RH, PA, SW_IN (or PPFD_IN)
  - Encouraged: SC (if applicable), G, NETRAD, PPFD_IN, LW_IN, P, SWC, TS
  - Suggested: WD, PPFD_DIF, PPFD_OUT, SW_DIF, SW_OUT, LW_OUT

Additional information information about data variables is [available](https://ameriflux.lbl.gov/data/aboutdata/data-variables/). Also note that multiple depths of soil temperature (TS) and soil water content (SWC) are supported by ONEFlux, using the numeric \_# suffix notation (e.g., TS_1).

Information including site FLUXNET ID, latitude, longitude, timezone (adopted for timestamps in data file), complete history of the height for eddy covariance system (gas analyser and sonic anemometer), the temporal resoltion for the data files (usually 30 or 60 minuted), and how CO2 flux storage is handled at the site, are also all required information for ONEFlux runs.


## Implemented steps

The steps implemented in the ONEFlux processing pipeline are detailed in the [data processing description page](http://fluxnet.fluxdata.org/data/fluxnet2015-dataset/data-processing/) of the [FLUXNET2015 dataset](http://fluxnet.fluxdata.org/data/fluxnet2015-dataset/data-processing/).

The outputs of each of these steps is saved to a sub-directories of a directory containing the data for a site. The structure of these output folders includes:

- **`01_qc_visual/`**: output of QA/QC procedures and visual inspection of data; _this is the main input for the ONEFlux pipeline_.
- **`02_qc_auto/`**: output of data preparation procedures for next steps and automated flagging of data based on quality tests (this step is implemented in C, and source available under `../ONEFlux/oneflux_steps/qc_auto/`).
- (*step 03* is part of a secondary visual inspection and not included in this codebase)
- **`04_ustar_mp/`**: output of the Moving Point detection method for USTAR threshold estimation (this step is implemented in C, and source available under `../ONEFlux/oneflux_steps/ustar_mp/`).
- **`05_ustar_cp/`**: output of the Change Point detection method for USTAR threshold estimation (this step is implemented in MATLAB, and source available under `../ONEFlux/oneflux_steps/ustar_cp/`).
- **`06_meteo_era/`**: output of the downscaling of micromet data using the ERA-Interim dataset (this step is _optional_ and is currently not part of this codebase).
- **`07_meteo_proc/`**: output of the micromet processing step, including gap-filling (this step is implemented in C, and source available under `../ONEFlux/oneflux_steps/meteo_proc/`).
- **`08_nee_proc/`**: output of the NEE processing step, including gap-filling (this step is implemented in C, and source available under `../ONEFlux/oneflux_steps/nee_proc/`).
- **`09_energy_proc/`**: output of the energy (LE and H) processing step, including gap-filling (this step is implemented in C, and source available under `../ONEFlux/oneflux_steps/energy_proc/`).
- **`10_nee_partition_nt/`**: output of the NEE partitioning, nighttime method (this step is implemented in Python, and source available under `../ONEFlux/oneflux/`).
- **`11_nee_partition_dt/`**: output of the NEE partitioning, daytime method (this step is implemented in Python, and source available under `../ONEFlux/oneflux/`).
- **`12_ure_input/`**: output of the preparation of input for the uncertainty estimation step (this step is implemented in Python, and source available under `../ONEFlux/oneflux/`).
- **`12_ure/`**: output of the uncertainty estimation step (this step is implemented in C, and source available under `../ONEFlux/oneflux_steps/ure/`).
- **`99_fluxnet2015/`**: final output of the pipeline with combined products from previous steps (this step is implemented in Python, and source available under `../ONEFlux/oneflux/`).


## Building and installing

A installation script is available in the form of a Makefile, which can be used in Linux (x86-64) systems; versions for Windows and Mac are planned but not available at this time.

Running the command `$ make` in the source code folder will install all required Python dependencies, compile all C modules and install them in the user home directory under `~/bin/oneflux/` (gcc version 4.8 or later is required to compile the C modules), and will also copy to the same destination an executable compiled version of a Matlab code (see below how to install MCR and run this code). Also note that the Python modules for ONEFlux will not be installed, so the source code will need to be used directly to configure paths and call the main pipeline execution.


### Installing MCR to run compiled MATLAB code

A compiled version of the MATLAB code for the Change Point detection method for USTAR threshold estimation is available (under `../ONEFlux/oneflux_steps/ustar_cp/bin/`) and is copied into the executables directory along with the compiled version of the steps implemented in C. (_currently only a version for Linux x86-64 environment is available_)

To run this MATLAB compiled code, it is necessary to install the MATLAB Compiler Runtime toolset. It can be downloaded in the [MCR page](https://www.mathworks.com/products/compiler/matlab-runtime.html). **Version 2018a is required** (this version was used to compile the code). Follow the instructions in the download page to install MCR.

The path to the newly installed MCR environment (e.g., `~/bin/matlab/v94/`) is a necessary input to the pipeline execution if this step is to be executed.



## Running

Run Python using the file runoneflux.py with the following parameters:

```
usage: runoneflux.py [-h] [--perc [PERC [PERC ...]]]
                     [--prod [PROD [PROD ...]]] [-l LOGFILE] [--force-py]
                     [--mcr MCR_DIRECTORY] [--ts TIMESTAMP] [--recint {hh,hr}]
                     COMMAND DATA-DIR SITE-ID SITE-DIR FIRST-YEAR LAST-YEAR

positional arguments:
  COMMAND               ONEFlux command to be run [all, partition_nt, partition_dt]
  DATA-DIR              Absolute path to general data directory
  SITE-ID               Site Flux ID in the form CC-XXX
  SITE-DIR              Relative path to site data directory (within data-dir)
  FIRST-YEAR            First year of data to be processed
  LAST-YEAR             Last year of data to be processed

optional arguments:
  -h, --help            show this help message and exit
  --perc [PERC [PERC ...]]
                        List of percentiles to be processed
  --prod [PROD [PROD ...]]
                        List of products to be processed
  -l LOGFILE, --logfile LOGFILE
                        Logging file path
  --force-py            Force execution of PY partitioning (saves original
                        output, generates new)
  --mcr MCR_DIRECTORY   Path to MCR directory
  --recint {hh,hr}      Record interval for site
  --versionp VERSIONP   Version of processing
  --versiond VERSIOND   Version of data
```

## Running examples

### Sample data

Data formatted to be used in the examples below are available. The [sample input data](ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_input.zip) (around 80MB) can be used to run the full pipeline. To check the processing worked as expected, the [sample output data](ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_output.zip) (around 400MB) cab be used.

- sample input data: [ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_input.zip](ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_input.zip)
- sample output data: [ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_output.zip](ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_output.zip)



### Execution commands

Run all steps in the pipeline:
- *python*: Python interpreter
- *runoneflux.py*: Main code to be executed
- *all*: Pipeline step to be executed (all)
- *"../datadir/"*: Main data directory
- *US-ARc*: Site Flux ID of site to be processed
- *"US-ARc_sample_input"*: Relative path to data directory for site (with main data directory)
- *2005*: First year to be processed
- *2006*: Last year to be processed
- *-l partitioning_nt_US-ARc.log*: Uses file to store execution log
- *--era-fy 1989*: first year of data for the ERA product
- *--era-ly 2014*: last year of data for the ERA product
```
python runoneflux.py all "../datadir/" US-ARc "US-ARc_sample_input" 2005 2006 -l fluxnet_pipeline_US-ARc.log --mcr ~/bin/matlab/v94/ --recint hh --era-fy 1989 --era-ly 2014
```


Run nighttime partitioning method:
```
python runoneflux.py partition_nt "../datadir/" US-ARc "US-ARc_sample_input" 2005 2006 -l fluxnet_pipeline_US-ARc.log
```

Run daytime partitioning with only single percentile and/or a single USTAR threshold type data product (recommended for first executions), use:
- *--prod y*: processes only VUT USTAR threshold product
- *--perc 50*: processes only 50-percentile USTAR threshold
- *--force-py*: forces execution of Python partitioning code (replaces existing outputs)
```
python runoneflux.py partition_dt "../datadir/" US-ARc "US-ARc_sample_input" 2005 2006 -l fluxnet_pipeline_US-ARc.log --prod y --perc 50 --force-py
```

Note that for the execution of the partitioning steps, only if the output ```*.csv``` file doesn’t exist (e.g., ```nee_y_50_US-ARc_2005.csv```), the code will run and generate the file. If it exists, nothing will be done (unless the flag --force-py is used).



## Required input data

### All steps

In the data directory for the site, the input data must be in the expected formats, especially for individual steps within the pipeline. If the full pipeline is being executed, the inputs that must be present should be in the following directories:
- ```01_qc_visual/qcv_files/```
- ```06_meteo_era/``` (optional)

and the outputs will be generated in the directories:
- `02_qc_auto/`
- `04_ustar_mp/`
- `05_ustar_cp/`
- `07_meteo_proc/`
- `08_nee_proc/`
- `09_energy_proc/`
- `10_nee_partition_nt/`
- `11_nee_partition_dt/`
- `12_ure_input/`
- `12_ure/`
- `99_fluxnet2015/`



### Flux partitioning steps only

For both the nighttime and daytime partitioning methods, the inputs that must be present should be in the following directories:
- ```02_qc_auto/```
- ```07_meteo_proc/```
- ```08_nee_proc/```

and the outputs will be generated, respectively, in the directories:
- ```10_nee_partition_nt/```
- ```11_nee_partition_dt/```



## Caveats and known limitations

- **NO SUPPORT.** We are not offering any kind of support for the code at this time (including creation of GitHub issues). This is so we are able to concentrate in improving the code and creating a more usable set of steps within the pipeline. This version of the code is intended to offer insight into how some of the steps work, but not a fully supported codebase. Once the code is more mature, we will revise this approach.

- **NO CODE CONTRIBUTIONS.** Following the same reasoning for not offering support at this time, we will not accept code contributions for now. Once the we have a more mature code and development process we will revise this approach (and start encouraging contributions at that point).

- **Execution environment requirements.** Many of the steps of the ONEFlux codebase have very specific requirements for the execution environment, including how the intermediate files are formatted, what outputs were generated successfully, execution logs being in place, etc. For this reason, it might be difficult for someone else to run this code if there are any unexpected conditions. Someone familiar with Python and C coding and Unix environments might be able to navigate and remedy errors, but the current version of the code is not intended to be "friendly" to the user (we hope to improve this in upcoming versions).

- **Data format requirements.** We have tested this codebase extensively but only on sites included in the FLUXNET2015 dataset. Specific formats with extra metadata (see [sample data](#sample-data) files for examples) are required for the pipeline to run correctly. Preparing a new site to be run could be difficult (this also something we intend to improve soon).

- **Python version.** This code has been tested to work with Python 2.7; it should work under Python 3.5 or later as well, but this was not fully tested.

- **MATLAB code.** The CPD friction velocity threshold estimation step requires an MCR environment configured to run MATLAB step compiled into executable (see [instructions](#installing-mcr-to-run-compiled-matlab-code) above)

- **Daytime partitioning method exceptions.** The current version of the implementation of the daytime flux partitioning method aimed at preserving the behavior of the code used to generate the FLUXNET2015 dataset. There are situations in which the non-linear least squares method fail for a window in the time series, stopping the execution. The solution implemented for the original implementation (mimicked in this version) would involve adding the failed window into a list of exception windows to be skipped when the execution is restarted. This is done automatically in this implementation, but is something that will be removed for future version, avoiding the failure conditions altogether.

- **Performance issues.** The performance of a few of the steps is not optimal. In particular, the daytime and nighttime partitioning methods, can take a long time. The daytime partitioning can be especially slow, with the non-linear least squares method taking a long time to run for each window. This will be addressed in future versions, taking advantage of newer least squares methods and other improvements to the execution flow.

- **Sundown reference partitioning method** One of the methods used for flux partitioning in FLUXNET2015 is not included in this version of the pipeline currently. We are working on porting the code and will include the method in future versions.

- **Micromet downscaling step.** The downscaling of micrometeorological variables using ERA-Interim reanalysis data (for filling long gaps) is another step missing from the current iteration and will be included in future versions.

- **Bug for full years missing.** _Known bug, will be addressed in future updates:_ there are situations when a full year of data missing for CO2 fluxes, or for energy/water fluxes, or micromet variables (or combinations of them), will cause the code to break. 

- **Bug in input for nighttime partition.** _Known bug, will be addressed in future updates:_ Certain rare conditions in the USTAR threshold estimation can cause the nighttime partitioning to break for lack of data for one or more windows within the time series.

- **Incompatibility with numpy version 1.16 or higher.** A change on how [numpy handles access to multiple fields in version 1.16](https://docs.scipy.org/doc/numpy-1.16.0/user/basics.rec.html#accessing-multiple-fields) broke many spots in the code _(to be corrected in future updates)_

- **Default output messages.** The default logging level (both to the screen/standard output and to the log file) are set to the most verbose mode, showing all diagnostics and status messages, which can generate a large log file.

- **Installation setup.** The Python installation script (`setup.py`) is not implemented yet, so configuring the execution environment (e.g., Python Path) might have to be done manually

- **Data input formats.** Some of the data formats are not fully compatible with regional networks and FLUXNET formats. This is being addressed and will be fixed in future versions.

- **Not all steps callable.** The current implementation only offers the execution of the full pipeline, the nighttime, and the daytime partitioning methods. All other methods are available but do not have an easy interface to get them to run individually (will also be changed in future versions). 




[//]: # (## Troubleshooting)


## Support and Funding ##
This material is based upon work supported by:
* U.S. Department of Energy, Office of Science, Office of Biological and Environmental Research, through the AmeriFlux Management Project, under Contract No. DE-AC02-05CH11231
* COOP+ project funded under the European Union's Horizon 2020 research
and innovation programme - grant agreement No 654131
* RINGO project funded under the European Union's Horizon 2020 research
and innovation programme - grant agreement No 730944
* ENVRIFAIR project funded under the European Union's Horizon 2020
research and innovation programme - grant agreement No 824068


## Contributors ##

### Development and Code ###
* Gilberto Pastorello, gzpastorello &lt;at&gt; lbl &lt;DOT&gt; gov
* Dario Papale, darpap &lt;at&gt; unitus &lt;DOT&gt; it
* Carlo Trotta, trottacarlo &lt;at&gt; unitus &lt;DOT&gt; it
* Alessio Ribeca, a.ribeca &lt;at&gt; unitus &lt;DOT&gt; it
* Abdelrahman Elbashandy, aaelbashandy &lt;at&gt; lbl &lt;DOT&gt; gov
* Alan Barr, alan.barr &lt;at&gt; canada &lt;DOT&gt; ca

### Evaluation ###
* Deb Agarwal, daagarwal &lt;at&gt; lbl &lt;DOT&gt; gov
* Sebastien Biraud, scbiraud &lt;at&gt; lbl &lt;DOT&gt; gov


## Citation

When using ONEFlux or referring to data products generated with ONEFlux, please consider citing our reference paper:
> Pastorello et al. The FLUXNET2015 dataset and the ONEFlux processing pipeline for eddy covariance data. Scientific Data 7:225 (2020). [10.1038/s41597-020-0534-3](https://doi.org/10.1038/s41597-020-0534-3)


<br>

---
**(THERE ARE CAVEATS AND KNOWN LIMITATIONS TO THIS CODE, PLEASE SEE [CAVEATS LIST](#caveats-and-known-limitations) (ABOVE)**
