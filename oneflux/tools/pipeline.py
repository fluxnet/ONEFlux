'''
oneflux.tools.pipeline

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Execution controller module for full pipeline runs

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-08-08
'''
import sys
import os
import logging
import argparse

from datetime import datetime

from oneflux import ONEFluxError, log_trace, VERSION_METADATA, VERSION_PROCESSING
from oneflux.pipeline.wrappers import Pipeline
from oneflux.pipeline.common import TOOL_DIRECTORY, MCR_DIRECTORY, ONEFluxPipelineError, \
                                    NOW_TS, ERA_FIRST_YEAR, ERA_LAST_YEAR, \
                                    ERA_FIRST_TIMESTAMP_START_TEMPLATE, ERA_LAST_TIMESTAMP_START_TEMPLATE
from oneflux.tools.partition_nt import PROD_TO_COMPARE, PERC_TO_COMPARE

log = logging.getLogger(__name__)


def run_pipeline(datadir,
                 siteid,
                 sitedir,
                 firstyear,
                 lastyear,
                 version_data=VERSION_METADATA,
                 version_proc=VERSION_PROCESSING,
                 prod_to_compare=PROD_TO_COMPARE,
                 perc_to_compare=PERC_TO_COMPARE,
                 mcr_directory=None,
                 timestamp=NOW_TS,
                 record_interval='hh',
                 era_first_year=ERA_FIRST_YEAR,
                 era_last_year=ERA_LAST_YEAR,
                 steps={}):

    sitedir_full = os.path.abspath(os.path.join(datadir, sitedir))
    if not sitedir or not os.path.isdir(sitedir_full):
        msg = "Site directory for {s} not found: '{d}'".format(s=siteid, d=sitedir)
        log.critical(msg)
        raise ONEFluxError(msg)

    log.info("Started processing site dir {d}".format(d=sitedir))
    try:
        pipeline = Pipeline(siteid=siteid,
                    data_dir=sitedir_full,
                    data_dir_main=os.path.abspath(datadir),
                    site_dir=sitedir,
                    tool_dir=TOOL_DIRECTORY,
                    first_year=firstyear,
                    last_year=lastyear,
                    prod_to_compare=prod_to_compare,
                    perc_to_compare=perc_to_compare,
                    timestamp=timestamp,
                    record_interval=record_interval,
                    fluxnet2015_first_t1=firstyear,
                    fluxnet2015_last_t1=lastyear,
                    fluxnet2015_version_data=version_data,
                    fluxnet2015_version_processing=version_proc,
                    ustar_cp_mcr_dir=mcr_directory,
                    era_first_timestamp_start=ERA_FIRST_TIMESTAMP_START_TEMPLATE.format(y=era_first_year),
                    era_last_timestamp_start=ERA_LAST_TIMESTAMP_START_TEMPLATE.format(y=era_last_year),
                    qc_auto_execute=steps.get('qc_auto_execute', True),
                    ustar_mp_execute=steps.get('ustar_mp_execute', True),
                    ustar_cp_execute=steps.get('ustar_cp_execute', True),
                    meteo_proc_execute=steps.get('meteo_proc_execute', True),
                    nee_proc_execute=steps.get('nee_proc_execute', True),
                    energy_proc_execute=steps.get('energy_proc_execute', True),
                    nee_partition_nt_execute=steps.get('nee_partition_nt_execute', True),
                    nee_partition_dt_execute=steps.get('nee_partition_dt_execute', True),
                    prepare_ure_execute=steps.get('prepare_ure_execute', True),
                    ure_execute=steps.get('ure_execute', True),
                    fluxnet2015_execute=steps.get('fluxnet2015_execute', True),
                    fluxnet2015_site_plots=steps.get('fluxnet2015_site_plots', True),
                    simulation=False)
        pipeline.run()
        #csv_manifest_entries, zip_manifest_entries = pipeline.fluxnet2015.csv_manifest_entries, pipeline.fluxnet2015.zip_manifest_entries
        log.info("Finished processing site dir {d}".format(d=sitedir_full))
    except ONEFluxPipelineError as e:
        log.critical("ONEFlux Pipeline ERRORS processing site dir {d}".format(d=sitedir_full))
        log_trace(exception=e, level=logging.CRITICAL, log=log)
        raise
    except ONEFluxError as e:
        log.critical("ONEFlux ERRORS processing site dir {d}".format(d=sitedir_full))
        log_trace(exception=e, level=logging.CRITICAL, log=log)
        raise
    except Exception as e:
        log.critical("UNKNOWN ERRORS processing site dir {d}".format(d=sitedir_full))
        log_trace(exception=e, level=logging.CRITICAL, log=log)
        raise

if __name__ == '__main__':
    sys.exit("ERROR: cannot run independently")
