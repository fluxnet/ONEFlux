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


def run_pipeline(config):

    datadir = config.args.datadir
    sitedir = config.args.sitedir
    siteid = config.args.siteid
    sitedir_full = os.path.abspath(os.path.join(datadir, sitedir))
    if not sitedir or not os.path.isdir(sitedir_full):
        msg = "Site directory for {s} not found: '{d}'".format(s=siteid, d=sitedir)
        log.critical(msg)
        raise ONEFluxError(msg)

    log.info("Started processing site dir {d}".format(d=sitedir))
    try:
        pipeline = Pipeline(config)
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
