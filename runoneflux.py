'''
runoneflux.py

For license information:
see LICENSE file or headers in oneflux.__init__.py

Execution controller module for running tools/functions in the oneflux library

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import os
import sys
import logging
import argparse
import traceback
import yaml

from oneflux import ONEFluxError, log_config, log_trace, VERSION_PROCESSING, VERSION_METADATA
from oneflux.tools.partition_nt import run_partition_nt, PROD_TO_COMPARE, PERC_TO_COMPARE
from oneflux.tools.partition_dt import run_partition_dt
from oneflux.tools.pipeline import run_pipeline, NOW_TS
from oneflux.pipeline.common import ERA_FIRST_YEAR, ERA_LAST_YEAR
import oneflux

log = logging.getLogger(__name__)

DEFAULT_LOGGING_FILENAME = 'oneflux.log'
COMMAND_LIST = ['partition_nt', 'partition_dt', 'all']

# main function
if __name__ == '__main__':

    # cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--command', metavar="COMMAND", help="ONEFlux command to be run", type=str, choices=COMMAND_LIST, default=None)
    parser.add_argument('--datadir', metavar="DATA-DIR", help="Absolute path to general data directory", type=str, default=None )
    parser.add_argument('--siteid', metavar="SITE-ID", help="Site Flux ID in the form CC-XXX", type=str, default=None)
    parser.add_argument('--sitedir', metavar="SITE-DIR", help="Relative path to site data directory (within data-dir)", type=str, default=None)
    parser.add_argument('--firstyear', metavar="FIRST-YEAR", help="First year of data to be processed", type=int, default=None)
    parser.add_argument('--lastyear', metavar="LAST-YEAR", help="Last year of data to be processed", type=int, default=None)
    parser.add_argument('--perc', metavar="PERC", help="List of percentiles to be processed", dest='perc', type=str, choices=PERC_TO_COMPARE, action='append', nargs='*')
    parser.add_argument('--prod', metavar="PROD", help="List of products to be processed", dest='prod', type=str, choices=PROD_TO_COMPARE, action='append', nargs='*')
    parser.add_argument('-l', '--logfile', help="Logging file path", type=str, dest='logfile', default=DEFAULT_LOGGING_FILENAME)
    parser.add_argument('--force-py', help="Force execution of PY partitioning (saves original output, generates new)", action='store_true', dest='forcepy', default=False)
    parser.add_argument('--mcr', help="Path to MCR directory", type=str, dest='mcr_directory', default=None)
    parser.add_argument('--ts', help="Timestamp to be used in processing IDs", type=str, dest='timestamp', default=NOW_TS)
    parser.add_argument('--recint', help="Record interval for site", type=str, choices=['hh', 'hr'], dest='recint', default='hh')
    parser.add_argument('--versionp', help="Version of processing (hardcoded default)", type=str, dest='versionp', default=str(VERSION_PROCESSING))
    parser.add_argument('--versiond', help="Version of data (hardcoded default)", type=str, dest='versiond', default=str(VERSION_METADATA))
    parser.add_argument('--era-fy', help="ERA first year of data (default {y})".format(y=ERA_FIRST_YEAR), type=int, dest='erafy', default=None)
    parser.add_argument('--era-ly', help="ERA last year of data (default {y})".format(y=ERA_LAST_YEAR), type=int, dest='eraly', default=None)
    parser.add_argument('--configfile', help="Path to config file", type=str, dest='configfile', default=None)
    args = parser.parse_args()

    # setup logging file and stdout
    log_config(level=logging.DEBUG, filename=args.logfile, std=True, std_level=logging.DEBUG)

    command = datadir = siteid = sitedir = firstyear = lastyear = \
        prod = perc = logfile = forcepy = versionp = versiond = erafy = eraly = None
    steps = {}

    if not args.configfile:
        if not args.command and not args.datadir and not args.siteid \
           and not args.sitedir and not args.firstyear and not args.lastyear:
            raise Exception('Please provide path to config file or required parameters: command, datadir, siteid, sitedir.')
    else:
        run_config = {}
        with open(args.configfile, 'r') as f:
            config = yaml.safe_load(f)
        run_config = config.get('run', {})
        command = args.command if args.command else run_config.get('command', 'all')
        datadir = args.datadir if args.datadir else run_config.get('data_dir', None)
        siteid = args.siteid if args.siteid else run_config.get('site_id', None)
        sitedir = args.sitedir if args.sitedir else run_config.get('site_dir', None)
        firstyear = args.firstyear if args.firstyear else run_config.get('first_year', None)
        lastyear = args.lastyear if args.lastyear else run_config.get('last_year', None)
        prod = args.prod if args.prod else run_config.get('prod', None)
        perc = args.perc if args.perc else run_config.get('perc', None)
        logfile = args.logfile if args.logfile else run_config.get('log_file', DEFAULT_LOGGING_FILENAME)
        forcepy = args.forcepy if args.forcepy else run_config.get('force_py', False)
        mcr_directory = args.mrc_directory if args.mcr_directory else run_config.get('mcr_directory', None)
        timestamp = args.timestamp if args.timestamp else run_config.get('record_interval', 'hh')
        recint = args.recint if args.recint else run_config.get('mcr_directory', NOW_TS)
        versionp = args.versionp if args.versionp else run_config.get('version_processing', str(VERSION_PROCESSING))
        versiond = args.versiond if args.versiond else run_config.get('version_data', str(VERSION_METADATA))
        erafy = args.erafy if args.erafy else run_config.get('era_first_year', int(ERA_FIRST_YEAR))
        eraly = args.eraly if args.eraly else run_config.get('era_last_year', int(ERA_LAST_YEAR))
        if not erafy:
            erafy = int(ERA_FIRST_YEAR)
        if not eraly:
            eraly = int(ERA_LAST_YEAR)
        steps = run_config.get('steps', {})

    # set defaults if no perc or prod
    perc = (PERC_TO_COMPARE if perc is None else perc[0])
    prod = (PROD_TO_COMPARE if prod is None else prod[0])

    msg = "Using:"
    msg += "command ({c})".format(c=command)
    msg += ", data-dir ({i})".format(i=datadir)
    msg += ", site-id ({i})".format(i=siteid)
    msg += ", site-dir ({d})".format(d=sitedir)
    msg += ", first-year ({y})".format(y=firstyear)
    msg += ", last-year ({y})".format(y=lastyear)
    msg += ", perc ({i})".format(i=perc)
    msg += ", prod ({i})".format(i=prod)
    msg += ", log-file ({f})".format(f=logfile)
    msg += ", force-py ({i})".format(i=forcepy)
    msg += ", versionp ({i})".format(i=versionp)
    msg += ", versiond ({i})".format(i=versiond)
    msg += ", era-fy ({i})".format(i=erafy)
    msg += ", era-ly ({i})".format(i=eraly)
    log.debug(msg)

    # start execution
    try:
        # check arguments
        print os.path.join(datadir, sitedir)
        if not os.path.isdir(os.path.join(datadir, sitedir)):
            raise ONEFluxError("Site dir not found: {d}".format(d=sitedir))

        # run command
        log.info("Starting execution: {c}".format(c=command))
        if command == 'all':
            run_pipeline(datadir=datadir, siteid=siteid, sitedir=sitedir, firstyear=firstyear, lastyear=lastyear,
                         prod_to_compare=prod, perc_to_compare=perc, mcr_directory=mcr_directory, timestamp=timestamp,
                         record_interval=recint, version_data=versiond, version_proc=versionp,
                         era_first_year=erafy, era_last_year=eraly, steps=steps)
        elif command == 'partition_nt':
            run_partition_nt(datadir=datadir, siteid=siteid, sitedir=sitedir, years_to_compare=range(firstyear, lastyear + 1),
                             py_remove_old=forcepy, prod_to_compare=prod, perc_to_compare=perc)
        elif command == 'partition_dt':
            run_partition_dt(datadir=datadir, siteid=siteid, sitedir=sitedir, years_to_compare=range(firstyear, lastyear + 1),
                             py_remove_old=forcepy, prod_to_compare=prod, perc_to_compare=perc)
        else:
            raise ONEFluxError("Unknown command: {c}".format(c=command))
        log.info("Finished execution: {c}".format(c=command))

    except Exception as e:
        msg = log_trace(exception=e, level=logging.CRITICAL, log=log)
        log.critical("***Problem during execution*** {e}".format(e=str(e)))
        tb = traceback.format_exc()
        log.critical("***Problem traceback*** {s}".format(s=str(tb)))
        sys.exit(msg)

    sys.exit(0)
