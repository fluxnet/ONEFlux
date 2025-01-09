"""
runoneflux.py

For license information:
see LICENSE file or headers in oneflux.__init__.py

Execution controller module for running tools/functions in the oneflux library

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
"""

import os
import sys
import logging
import argparse
import traceback

from oneflux import (
    ONEFluxError,
    log_config,
    log_trace,
    VERSION_PROCESSING,
    VERSION_METADATA,
)
from oneflux.tools.partition_nt import (
    run_partition_nt,
    PROD_TO_COMPARE,
    PERC_TO_COMPARE,
)
from oneflux.tools.partition_dt import run_partition_dt
from oneflux.tools.pipeline import run_pipeline, NOW_TS
from oneflux.pipeline.common import ERA_FIRST_YEAR, ERA_LAST_YEAR

log = logging.getLogger(__name__)

DEFAULT_LOGGING_FILENAME = "oneflux.log"
COMMAND_LIST = ["partition_nt", "partition_dt", "all"]

# main function
if __name__ == "__main__":
    # cli arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        metavar="COMMAND",
        help="ONEFlux command to be run",
        type=str,
        choices=COMMAND_LIST,
    )
    parser.add_argument(
        "datadir",
        metavar="DATA-DIR",
        help="Absolute path to general data directory",
        type=str,
    )
    parser.add_argument(
        "siteid", metavar="SITE-ID", help="Site Flux ID in the form CC-XXX", type=str
    )
    parser.add_argument(
        "sitedir",
        metavar="SITE-DIR",
        help="Relative path to site data directory (within data-dir)",
        type=str,
    )
    parser.add_argument(
        "firstyear",
        metavar="FIRST-YEAR",
        help="First year of data to be processed",
        type=int,
    )
    parser.add_argument(
        "lastyear",
        metavar="LAST-YEAR",
        help="Last year of data to be processed",
        type=int,
    )
    parser.add_argument(
        "--perc",
        metavar="PERC",
        help="List of percentiles to be processed",
        dest="perc",
        type=str,
        choices=PERC_TO_COMPARE,
        action="append",
        nargs="*",
    )
    parser.add_argument(
        "--prod",
        metavar="PROD",
        help="List of products to be processed",
        dest="prod",
        type=str,
        choices=PROD_TO_COMPARE,
        action="append",
        nargs="*",
    )
    parser.add_argument(
        "-l",
        "--logfile",
        help="Logging file path",
        type=str,
        dest="logfile",
        default=DEFAULT_LOGGING_FILENAME,
    )
    parser.add_argument(
        "--force-py",
        help="Force execution of PY partitioning (saves original output, generates new)",
        action="store_true",
        dest="forcepy",
        default=False,
    )
    parser.add_argument(
        "--mcr",
        help="Path to MCR directory",
        type=str,
        dest="mcr_directory",
        default=None,
    )
    parser.add_argument(
        "--ts",
        help="Timestamp to be used in processing IDs",
        type=str,
        dest="timestamp",
        default=NOW_TS,
    )
    parser.add_argument(
        "--recint",
        help="Record interval for site",
        type=str,
        choices=["hh", "hr"],
        dest="recint",
        default="hh",
    )
    parser.add_argument(
        "--versionp",
        help="Version of processing (hardcoded default)",
        type=str,
        dest="versionp",
        default=str(VERSION_PROCESSING),
    )
    parser.add_argument(
        "--versiond",
        help="Version of data (hardcoded default)",
        type=str,
        dest="versiond",
        default=str(VERSION_METADATA),
    )
    parser.add_argument(
        "--era-fy",
        help="ERA first year of data (default {y})".format(y=ERA_FIRST_YEAR),
        type=int,
        dest="erafy",
        default=int(ERA_FIRST_YEAR),
    )
    parser.add_argument(
        "--era-ly",
        help="ERA last year of data (default {y})".format(y=ERA_LAST_YEAR),
        type=int,
        dest="eraly",
        default=int(ERA_LAST_YEAR),
    )
    args = parser.parse_args()

    # setup logging file and stdout
    log_config(
        level=logging.DEBUG, filename=args.logfile, std=True, std_level=logging.DEBUG
    )

    # set defaults if no perc or prod
    perc = PERC_TO_COMPARE if args.perc is None else args.perc[0]
    prod = PROD_TO_COMPARE if args.prod is None else args.prod[0]

    firstyear = args.firstyear
    lastyear = args.lastyear

    msg = "Using:"
    msg += "command ({c})".format(c=args.command)
    msg += ", data-dir ({i})".format(i=args.datadir)
    msg += ", site-id ({i})".format(i=args.siteid)
    msg += ", site-dir ({d})".format(d=args.sitedir)
    msg += ", first-year ({y})".format(y=firstyear)
    msg += ", last-year ({y})".format(y=lastyear)
    msg += ", perc ({i})".format(i=perc)
    msg += ", prod ({i})".format(i=prod)
    msg += ", log-file ({f})".format(f=args.logfile)
    msg += ", force-py ({i})".format(i=args.forcepy)
    msg += ", versionp ({i})".format(i=args.versionp)
    msg += ", versiond ({i})".format(i=args.versiond)
    msg += ", era-fy ({i})".format(i=args.erafy)
    msg += ", era-ly ({i})".format(i=args.eraly)
    log.debug(msg)

    # start execution
    try:
        # check arguments
        print(os.path.join(args.datadir, args.sitedir))
        if not os.path.isdir(os.path.join(args.datadir, args.sitedir)):
            raise ONEFluxError("Site dir not found: {d}".format(d=args.sitedir))

        # run command
        log.info("Starting execution: {c}".format(c=args.command))
        if args.command == "all":
            run_pipeline(
                datadir=args.datadir,
                siteid=args.siteid,
                sitedir=args.sitedir,
                firstyear=firstyear,
                lastyear=lastyear,
                prod_to_compare=prod,
                perc_to_compare=perc,
                mcr_directory=args.mcr_directory,
                timestamp=args.timestamp,
                record_interval=args.recint,
                version_data=args.versiond,
                version_proc=args.versionp,
                era_first_year=args.erafy,
                era_last_year=args.eraly,
            )
        elif args.command == "partition_nt":
            run_partition_nt(
                datadir=args.datadir,
                siteid=args.siteid,
                sitedir=args.sitedir,
                years_to_compare=list(range(firstyear, lastyear + 1)),
                py_remove_old=args.forcepy,
                prod_to_compare=prod,
                perc_to_compare=perc,
            )
        elif args.command == "partition_dt":
            run_partition_dt(
                datadir=args.datadir,
                siteid=args.siteid,
                sitedir=args.sitedir,
                years_to_compare=list(range(firstyear, lastyear + 1)),
                py_remove_old=args.forcepy,
                prod_to_compare=prod,
                perc_to_compare=perc,
            )
        else:
            raise ONEFluxError("Unknown command: {c}".format(c=args.command))
        log.info("Finished execution: {c}".format(c=args.command))

    except Exception as e:
        msg = log_trace(exception=e, level=logging.CRITICAL, log=log)
        log.critical("***Problem during execution*** {e}".format(e=str(e)))
        tb = traceback.format_exc()
        log.critical("***Problem traceback*** {s}".format(s=str(tb)))
        sys.exit(msg)

    sys.exit(0)
