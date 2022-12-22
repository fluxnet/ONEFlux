'''
runoneflux.py

For license information:
see LICENSE file or headers in oneflux.__init__.py

Execution controller module for running tools/functions in the oneflux library

@author: Gilberto Pastorello
@contact: gzpastorello@lbl.gov
@date: 2017-01-31
'''
import sys
import logging
import traceback

from oneflux import log_config, log_trace
from oneflux.configs.utils import ONEFluxConfig
from oneflux.tools.partition_nt import run_partition_nt
from oneflux.tools.partition_dt import run_partition_dt
from oneflux.tools.pipeline import run_pipeline

log = logging.getLogger(__name__)
# main function
if __name__ == '__main__':

    # cli arguments
    config = ONEFluxConfig()

    # setup logging file and stdout
    log_config(level=logging.DEBUG,
               filename=config.args.logfile,
               std=True,
               std_level=logging.DEBUG)

    # set defaults if no perc or prod
    config.log_msg()
    config.run_check()
    config.export_to_yaml()
    # start execution
    try:
        # run command
        log.info("Starting execution: {c}".format(c=config.args.command))
        if config.args.command == 'all':
            run_pipeline(config)
        elif config.args.command == 'partition_nt':
            run_partition_nt(**config.get_partition_nt_params())
        elif config.args.command == 'partition_dt':
            run_partition_dt(**config.get_partition_dt_params())
        log.info("Finished execution: {c}".format(c=config.args.command))

    except Exception as e:
        msg = log_trace(exception=e, level=logging.CRITICAL, log=log)
        log.critical("***Problem during execution*** {e}".format(e=str(e)))
        tb = traceback.format_exc()
        log.critical("***Problem traceback*** {s}".format(s=str(tb)))
        sys.exit(msg)

    sys.exit(0)
