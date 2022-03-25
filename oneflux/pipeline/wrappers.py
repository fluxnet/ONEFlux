'''
oneflux.pipeline.wrappers

For license information:
see LICENSE file or headers in oneflux.__init__.py 

Pipeline execution controller wrappers

@author: Gilberto Z. Pastorello
@contact: gzpastorello@lbl.gov
@date: 2014-04-19
'''
import sys
import os
import logging
import re
import numpy
import socket
import fnmatch

from datetime import datetime

from oneflux import add_file_log, ONEFluxError, log_trace
from oneflux.pipeline import CMD_SEP, COPY, DELETE, DELETE_DIR, HOMEDIR, DATA_DIR, TOOL_DIR, OUTPUT_LOG_TEMPLATE
from oneflux.pipeline.site_data_product import run_site, get_headers_qc, _load_data, update_names_qc, save_csv_txt
from oneflux.pipeline.variables_codes import QC_FULL_DIRECT_D
from oneflux.pipeline.common import CSVMANIFEST_HEADER, ZIPMANIFEST_HEADER, ONEFluxPipelineError, \
                                     run_command, test_dir, test_file, test_file_list, test_file_list_or, \
                                     test_create_dir, create_replace_dir, create_and_empty_dir, test_pattern, \
                                     check_headers_fluxnet2015, get_empty_array_year, \
                                     PRODFILE_TEMPLATE_F, PRODFILE_AUX_TEMPLATE_F, PRODFILE_YEARS_TEMPLATE_F, \
                                     PRODFILE_FIGURE_TEMPLATE_F, ZIPFILE_TEMPLATE_F, NEE_PERC_USTAR_VUT_PATTERN, \
                                     NEE_PERC_USTAR_CUT_PATTERN, UNC_INFO_F, UNC_INFO_ALT_F, NEE_PERC_NEE_F, \
                                     METEO_INFO_F, NEE_INFO_F, \
                                     HOSTNAME, NOW_TS, ERA_FIRST_TIMESTAMP_START, ERA_LAST_TIMESTAMP_START,\
                                     MODE_ISSUER, MODE_PRODUCT
from oneflux.partition.library import PARTITIONING_DT_ERROR_FILE, EXTRA_FILENAME
from oneflux.partition.auxiliary import nan, nan_ext, NAN, NAN_TEST
from oneflux.partition.daytime import ONEFluxPartitionBrokenOptError
from oneflux.pipeline.site_plots import gen_site_plots
from oneflux.tools.partition_nt import run_partition_nt, PROD_TO_COMPARE, PERC_TO_COMPARE
from oneflux.tools.partition_dt import run_partition_dt

DEFAULT_LOGGING_FILENAME = 'report_{s}_{h}_{t}.log'.format(h=HOSTNAME, t=NOW_TS, s='{s}')

log = logging.getLogger(__name__)


class Pipeline(object):
    '''
    ONEFlux Pipeline execution controller class 
    '''
    RECORD_INTERVAL = 'hh'
    VALIDATE_ON_CREATE = False
    SIMULATION = False

    def __init__(self, siteid, timestamp=datetime.now().strftime("%Y%m%d%H%M%S"), *args, **kwargs):
        '''
        Initializes pipeline execution object, including initialization tests (e.g., directories and initial datasets tests)
        '''
        log.info("ONEFlux Pipeline: initialization started")
        self.run_id = socket.getfqdn() + '_run' + timestamp

        if (MODE_ISSUER == 'FLX') and (MODE_PRODUCT == 'FLUXNET2015'):
            FLUXNET_PRODUCT_CLASS = PipelineFLUXNET2015
        else:
            FLUXNET_PRODUCT_CLASS = PipelineFLUXNET

        ### basic checks
        # extra configs
        if args:
            log.warning("ONEFlux Pipeline: non-keyword arguments provided, ignoring: {a}".format(a=args))
        log.debug("ONEFlux Pipeline: keyword arguments: {a}".format(a=kwargs))
        self.configs = kwargs

        # check valid config attribute labels from defaults from classes
        self.driver_classes = [PipelineFPCreator,
                        PipelineQCVisual,
                        PipelineQCAuto,
                        PipelineQCAutoConvert,
                        PipelineQCVisualCross,
                        PipelineUstarMP,
                        PipelineUstarCP,
                        PipelineMeteoERA,
                        PipelineMeteoMDS,
                        PipelineMeteoProc,
                        PipelineNEEProc,
                        PipelineEnergyProc,
                        PipelineNEEPartitionNT,
                        PipelineNEEPartitionDT,
                        PipelineNEEPartitionSR,
                        PipelinePrepareURE,
                        PipelineURE,
                        FLUXNET_PRODUCT_CLASS,
                       ]

        self.valid_attribute_labels = ['data_dir', 'tool_dir', 'data_dir_main', 'prod_to_compare', 'perc_to_compare', 'first_year', 'last_year']
        for driver in self.driver_classes:
            labels = [k.lower() for k, v in driver.__dict__.iteritems() if ((not callable(v)) and (not k.startswith('_')))]
            self.valid_attribute_labels.extend(labels)
        labels = [k.lower() for k, v in Pipeline.__dict__.iteritems() if ((not callable(v)) and (not k.startswith('_')))]
        self.valid_attribute_labels.extend(labels)
        for k in self.configs.keys():
            if k not in self.valid_attribute_labels:
                log.error("Pipeline: unknown config attribute: '{p}'".format(p=k))
        self.first_year = self.configs.get('first_year', None)
        self.last_year = self.configs.get('last_year', None)
        self.data_dir_main = self.configs.get('data_dir_main', None)
        self.site_dir = self.configs.get('site_dir', None)

        # check OS
        if (os.name != 'posix') and (os.name != 'nt'):
            msg = "Unknown operating system '{o}'".format(o=os.name)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)

        # check site ID
        if (len(siteid) != 6) or (not siteid[:2].isalpha()) or (siteid[2] != '-') or (not siteid[3:].isalnum()):
            msg = "Invalid Site ID '{i}'".format(i=siteid)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)

        ### main configurations
        self.siteid = siteid
        self.siteid_short = siteid.replace('-', '')
        log.debug("ONEFlux Pipeline: setting up for site '{v}'".format(v=self.siteid))

        # main data directory (all sites)
        self.data_dir = self.configs.get('data_dir', os.path.join(DATA_DIR, self.siteid)) # TODO: default should be self.site_dir?
        log.debug("ONEFlux Pipeline: using data dir '{v}'".format(v=self.data_dir))

        self.prodfile_template = os.path.join(self.data_dir, FLUXNET_PRODUCT_CLASS.FLUXNET2015_DIR, PRODFILE_TEMPLATE_F)
        self.prodfile_aux_template = os.path.join(self.data_dir, FLUXNET_PRODUCT_CLASS.FLUXNET2015_DIR, PRODFILE_AUX_TEMPLATE_F)
        self.prodfile_years_template = os.path.join(self.data_dir, FLUXNET_PRODUCT_CLASS.FLUXNET2015_DIR, PRODFILE_YEARS_TEMPLATE_F)
        self.prodfile_figure_template = os.path.join(self.data_dir, FLUXNET_PRODUCT_CLASS.FLUXNET2015_DIR, PRODFILE_FIGURE_TEMPLATE_F)
        self.zipfile_template = os.path.join(self.data_dir, FLUXNET_PRODUCT_CLASS.FLUXNET2015_DIR, ZIPFILE_TEMPLATE_F)
        self.nee_perc_ustar_vut = os.path.join(self.data_dir, PipelineNEEProc.NEE_PROC_DIR, NEE_PERC_USTAR_VUT_PATTERN)
        self.nee_perc_ustar_cut = os.path.join(self.data_dir, PipelineNEEProc.NEE_PROC_DIR, NEE_PERC_USTAR_CUT_PATTERN)
        self.nee_perc_nee = os.path.join(self.data_dir, PipelineNEEProc.NEE_PROC_DIR , NEE_PERC_NEE_F)
        self.unc_info = os.path.join(self.data_dir, PipelineURE.URE_DIR , UNC_INFO_F)
        self.unc_info_alt = os.path.join(self.data_dir, PipelineURE.URE_DIR , UNC_INFO_ALT_F)
        self.meteo_info = os.path.join(self.data_dir, PipelineMeteoProc.METEO_PROC_DIR, METEO_INFO_F)
        self.nee_info = os.path.join(self.data_dir, PipelineNEEProc.NEE_PROC_DIR, NEE_INFO_F)
        self.mpdir = os.path.join(self.data_dir, PipelineUstarMP.USTAR_MP_DIR)
        self.cpdir = os.path.join(self.data_dir, PipelineUstarCP.USTAR_CP_DIR)

        # main tool directory (executables)
        self.tool_dir = self.configs.get('tool_dir', TOOL_DIR)
        log.debug("ONEFlux Pipeline: using tool dir '{v}'".format(v=self.tool_dir))

        # resolution of record interval for data set: hh (half-hourly) or hr (hourly)
        self.record_interval = self.configs.get('record_interval', self.RECORD_INTERVAL)
        log.debug("ONEFlux Pipeline: using record interval '{v}'".format(v=self.record_interval))

        # True: runs pre-execution validation on all steps (otherwise only at run time)
        self.validate_on_create = self.configs.get('validate_on_create', self.VALIDATE_ON_CREATE)
        log.debug("ONEFlux Pipeline: using validate on create '{v}'".format(v=self.validate_on_create))

        # True: simulation only -- generates commands, but does not execute them
        self.simulation = self.configs.get('simulation', self.SIMULATION)
        log.debug("ONEFlux Pipeline: using simulation '{v}'".format(v=self.simulation))

        # ERA timestamp ranges
        self.era_first_timestamp_start = self.configs.get('era_first_timestamp_start', ERA_FIRST_TIMESTAMP_START)
        self.era_last_timestamp_start = self.configs.get('era_last_timestamp_start', ERA_LAST_TIMESTAMP_START)
        self.era_first_year = int(self.era_first_timestamp_start[:4])
        self.era_last_year = int(self.era_last_timestamp_start[:4]) 
        log.debug("ONEFlux Pipeline: using ERA first timestamp start '{v}'".format(v=self.era_first_timestamp_start))
        log.debug("ONEFlux Pipeline: using ERA last timestamp start '{v}'".format(v=self.era_last_timestamp_start))


        ### create drivers for individual steps
        self.fp_creator = PipelineFPCreator(pipeline=self)
        self.qc_visual = PipelineQCVisual(pipeline=self)
        self.qc_auto = PipelineQCAuto(pipeline=self)
        self.qc_auto_convert = PipelineQCAutoConvert(pipeline=self)
        self.qc_visual_cross = PipelineQCVisualCross(pipeline=self)
        self.ustar_mp = PipelineUstarMP(pipeline=self)
        self.ustar_cp = PipelineUstarCP(pipeline=self)
        self.meteo_era = PipelineMeteoERA(pipeline=self)
        self.meteo_mds = PipelineMeteoMDS(pipeline=self)
        self.meteo_proc = PipelineMeteoProc(pipeline=self)
        self.nee_proc = PipelineNEEProc(pipeline=self)
        self.energy_proc = PipelineEnergyProc(pipeline=self)
        self.nee_partition_nt = PipelineNEEPartitionNT(pipeline=self)
        self.nee_partition_dt = PipelineNEEPartitionDT(pipeline=self)
        self.nee_partition_sr = PipelineNEEPartitionSR(pipeline=self)
        self.prepare_ure = PipelinePrepareURE(pipeline=self)
        self.ure = PipelineURE(pipeline=self)
        self.fluxnet2015 = FLUXNET_PRODUCT_CLASS(pipeline=self)

        ### validation
        # list all steps
        self.drivers = [self.fp_creator,
                        self.qc_visual,
                        self.qc_auto,
                        self.qc_auto_convert,
                        self.qc_visual_cross,
                        self.ustar_mp,
                        self.ustar_cp,
                        self.meteo_era,
                        self.meteo_mds,
                        self.meteo_proc,
                        self.nee_proc,
                        self.energy_proc,
                        self.nee_partition_nt,
                        self.nee_partition_dt,
                        self.nee_partition_sr,
                        self.prepare_ure,
                        self.ure,
                        self.fluxnet2015,
                       ]

        # pre-execution validation
        if self.validate_on_create:
            log.debug("ONEFlux Pipeline: running all pre-execution validation steps")
            self.pre_validate()
            self.validate_steps()

        log.info("ONEFlux Pipeline: initialization finished")


    def pre_validate(self):
        '''
        Validate pre-execution initialization configurations
        '''
        test_dir(tdir=self.data_dir, label="data")
        test_dir(tdir=self.tool_dir, label="tool")


    def post_validate(self):
        '''
        Validate post-execution results
        '''
        pass # TODO: check logs for failures


    def validate_steps(self):
        '''
        Runs pre-execution validation for all steps set to be run
        '''
        for driver in self.drivers:
            if driver.execute:
                driver.pre_validate()

    def run(self):
        '''
        Executes ONEFlux Pipeline steps set to be run
        '''

        log.info("{s}".format(s=self.siteid))
        log.info("{s} Pipeline: execution started".format(s=self.siteid))
        self.pre_validate()

        try:
            # start site pipeline log
            logger_file, log_file_handler = add_file_log(filename=os.path.join(self.data_dir, DEFAULT_LOGGING_FILENAME.format(s=self.siteid)))
            ts_begin = datetime.now()

            for driver in self.drivers:
                if driver.execute:
                    driver.run()
            self.post_validate()

        except Exception as e:
            log.critical("{s} an error occurred ({d}): {e}".format(s=self.siteid, d=self.site_dir, e=str(e)))
            log_trace(exception=e, level=logging.CRITICAL)
            log_file_handler.flush()
            raise

        finally:
            # close site pipeline log
            ts_end = datetime.now()
            ts_duration = ts_end - ts_begin
            log.info('{s} Pipeline run time {d} ({b} --- {e})'.format(s=self.siteid, d=ts_duration, b=ts_begin, e=ts_end))
            log_file_handler.flush()
            log_file_handler.close()
            logger_file.removeHandler(log_file_handler)

        log.info("{s} Pipeline: execution finished".format(s=self.siteid))


class PipelineFPCreator(object):
    '''
    Class to control execution of fp_creator step
    '''
    FP_CREATOR_EXECUTE = False # TODO: change default when method implemented
    ORIGINAL_DATASET_DIR = "00_original_dataset"
    FP_DATASET_DIR = "00_fp_dataset"

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of fp_creator step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('fp_creator_execute', self.FP_CREATOR_EXECUTE)
        self.execute = self.FP_CREATOR_EXECUTE # TODO: remove when method implemented
        self.original_dataset_dir = self.pipeline.configs.get('original_dataset_dir', os.path.join(self.pipeline.data_dir, self.ORIGINAL_DATASET_DIR))
        self.fp_dataset_dir = self.pipeline.configs.get('fp_dataset_dir', os.path.join(self.pipeline.data_dir, self.FP_DATASET_DIR))

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        test_dir(tdir=self.original_dataset_dir, label='original_dataset')

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        pass

    def run(self):
        '''
        Executes fp_creator
        '''

        log.info("Pipeline fp_creator execution started")
        self.pre_validate()

        test_create_dir(tdir=self.fp_dataset_dir, label='fp_dataset')

        # TODO: run

        self.post_validate()
        log.info("Pipeline fp_creator execution finished")

    def fp_creator(self):
        '''
        Converts from AmeriFlux standard format to FPFile format
        '''
        # TODO: finish implementation

        p = re.compile("\d{4,}")
        input_filenames = [ os.path.join(i[0], j) for i in os.walk(self.original_dataset) for j in i[2] ]
        input_filenames = [ i for i in input_filenames if (('AMF' in i) and ((self.pipeline.siteid in i) or (self.pipeline.siteid_short in i)) and (p.search(i) is not None)) ]
# TODO: finish implementation
#        fpfile_list = []
#        for filename in input_filenames[:2]:
#            log.debug("File '{f}' will be converted from AmeriFlux format into FPFile format".format(f=filename))
#            # fpfile = # TODO: load data file
#            # fpfile_list.append(fpfile)
#
#        fpp_data = FPPData(fpfile_list)
#
#        key = variable_key(format_name='fpp', variable_name='irga_height', variable_count=1)
#        heights = fpp_data.data[key][~numpy.isnan(fpp_data.data[key])]
#        print numpy.all(heights == heights[0])
#        print len(heights), len(fpp_data.data)
#
#        filename_template = os.path.join(self.fp_dataset_dir, "{f}.csv".format(f=self.pipeline.siteid_short))
#        fpp_data.save_csv(filename=filename_template, format_name="fpfile_v2", yearly=True)



class PipelineQCVisual(object):
    '''
    Class to control execution of qc_visual step
    '''
    QC_VISUAL_EXECUTE = False # TODO: change default when method implemented
    QC_VISUAL_DIR = "01_qc_visual"
    QC_VISUAL_DIR_INNER = "qcv_files"
    _OUTPUT_FILE_PATTERNS = [
        #[OUTPUT_LOG_TEMPLATE.format(t='*'), ], # TODO: change when method implemented
    ]
    _OUTPUT_FILE_PATTERNS_INNER = [
        "{s}_qcv_????.csv",
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of qc_visual step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('qv_visual_execute', self.QC_VISUAL_EXECUTE)
        self.execute = self.QC_VISUAL_EXECUTE # TODO: remove when method implemented
        self.qc_visual_dir = self.pipeline.configs.get('qc_visual_dir', os.path.join(self.pipeline.data_dir, self.QC_VISUAL_DIR))
        self.qc_visual_dir_inner = self.pipeline.configs.get('qc_visual_files_dir', os.path.join(self.qc_visual_dir, self.QC_VISUAL_DIR_INNER))
        self.output_file_pattern = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.output_file_patterns_inner = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_INNER]

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        pass # TODO: check FPCreator or independent check of fp files

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.qc_visual_dir, label='qc_visual.post_validate')
        test_dir(tdir=self.qc_visual_dir_inner, label='qc_visual.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_pattern, tdir=self.qc_visual_dir, label='qc_visual.post_validate')
        test_file_list(file_list=self.output_file_patterns_inner, tdir=self.qc_visual_dir_inner, label='qc_visual.post_validate')

    def run(self):
        '''
        Executes qc_visual
        '''

        log.info("Pipeline qc_visual execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.qc_visual_dir, label='qc_visual.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)
        create_replace_dir(tdir=self.qc_visual_dir_inner, label='qc_visual.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        # TODO: run

        self.post_validate()
        log.info("Pipeline qc_visual execution finished")


class PipelineQCAuto(object):
    '''
    Class to control execution of qc_auto step.
    Executes QC Automated Quality Flagging step.
    '''
    QC_AUTO_EXECUTE = True
    QC_AUTO_EX = 'qc_auto'
    QC_AUTO_DIR = '02_qc_auto'
    _OUTPUT_FILE_PATTERNS = [
        '{s}_qca_energy_????.csv',
        '{s}_qca_meteo_????.csv',
        '{s}_qca_nee_????.csv',
        '{s}_qca_ustar_????.csv',
        OUTPUT_LOG_TEMPLATE.format(t='*'),
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of qc_auto step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.label = 'qc_auto'
        self.execute = self.pipeline.configs.get('qc_auto_execute', self.QC_AUTO_EXECUTE)
        self.qc_auto_ex = self.pipeline.configs.get('qc_auto_ex', os.path.join(self.pipeline.tool_dir, self.QC_AUTO_EX))
        self.qc_auto_dir = self.pipeline.configs.get('qc_auto_dir', os.path.join(self.pipeline.data_dir, self.QC_AUTO_DIR))
        self.qc_auto_dir_fmt = self.qc_auto_dir + os.sep
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.input_qc_visual_dir = '..' + os.sep + os.path.basename(self.pipeline.qc_visual.qc_visual_dir) + os.sep + os.path.basename(self.pipeline.qc_visual.qc_visual_dir_inner) + os.sep
        self.output_log = os.path.join(self.qc_auto_dir, 'report_{t}.txt'.format(t=self.pipeline.run_id))
        self.cmd_txt = 'cd "{o}" {cmd_sep} {c} -input_path="{i}" -output_path=. -ustar -graph -nee -energy -meteo -solar > "{log}"'
        self.cmd = self.cmd_txt.format(c=self.qc_auto_ex, i=self.input_qc_visual_dir, o=self.qc_auto_dir_fmt, log=self.output_log, cmd_sep=CMD_SEP)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check executable
        test_file(tfile=self.qc_auto_ex, label='{s}.pre_validate'.format(s=self.label))

        # check dependency steps
        self.pipeline.qc_visual.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.qc_auto_dir, label='{s}.post_validate'.format(s=self.label))

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.qc_auto_dir, label='{s}.post_validate'.format(s=self.label))

    def run(self):
        '''
        Executes qc_auto
        '''

        log.info('Pipeline {s} execution started'.format(s=self.label))
        self.pre_validate()

        create_replace_dir(tdir=self.qc_auto_dir, label='{s}.run'.format(s=self.label), suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info('Execution command: {c}'.format(c=self.cmd))
        if self.pipeline.simulation:
            log.info('Simulation only, {s} execution command skipped'.format(s=self.label))
        else:
            run_command(self.cmd)
            self.post_validate()

        log.info('Pipeline {s} execution finished'.format(s=self.label))


class PipelineQCAutoConvert(object):
    '''
    Class to execute qc_auto_convert step.
    Converts outputs from qc_auto step from previous versions
    into current version for subsequent processing steps.
    
    This is a legacy step and should not be needed on any new run.    
    '''
    QC_AUTO_CONVERT_EXECUTE = False # Legacy step, default is not to run
    QC_AUTO_CONVERT_DIR = "02_qc_auto"
    _QC_AUTO_CONVERT_ORIGINAL = '.original'
    _OUTPUT_FILE_PATTERNS = [
        "{s}_qca_energy_????.csv",
        "{s}_qca_meteo_????.csv",
        "{s}_qca_nee_????.csv",
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of qc_auto step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('qc_auto_convert_execute', self.QC_AUTO_CONVERT_EXECUTE)
        self.qc_auto_convert_dir = self.pipeline.configs.get('qc_auto_convert_dir', os.path.join(self.pipeline.data_dir, self.QC_AUTO_CONVERT_DIR))
        self.qc_auto_convert_original = self._QC_AUTO_CONVERT_ORIGINAL
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.qc_auto_convert_files_to_convert = []

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check output directory
        test_dir(tdir=self.qc_auto_convert_dir, label='qc_auto_convert.pre_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.qc_auto_convert_dir, label='qc_auto_convert.pre_validate')

        for fname in self.output_file_patterns:
            if '*' in fname or '?' in fname:
                matches = test_pattern(tdir=self.qc_auto_convert_dir, tpattern=fname, label='qc_auto_convert.pre_validate')
                matches = [entry for entry in matches if not entry.endswith(self.qc_auto_convert_original)]
                for match_fname in matches:
                    headers, first_numeric_line, timestamp_format, headers_line, first_lines = get_headers_qc(filename=os.path.join(self.qc_auto_convert_dir, match_fname))
                    if 'TIMESTAMP_START' not in headers:
                        self.qc_auto_convert_files_to_convert.append(match_fname)
                        continue
                    for h in headers:
                        if h not in QC_FULL_DIRECT_D.keys():
                            self.qc_auto_convert_files_to_convert.append(match_fname)
                            break

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.qc_auto_convert_dir, label='qc_auto_convert.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.qc_auto_convert_dir, label='qc_auto_convert.post_validate')

    def run(self):
        '''
        Executes qc_auto_convert
        '''

        log.info("Pipeline qc_auto_convert execution started")
        self.pre_validate()

        if not self.qc_auto_convert_files_to_convert:
            log.debug("Pipeline qc_auto_convert all files already converted for {s}".format(s=self.pipeline.siteid))
        else:
            for fname in self.qc_auto_convert_files_to_convert:
                filename = os.path.join(self.qc_auto_convert_dir, fname)
                filename_backup = os.path.join(self.qc_auto_convert_dir, fname + self.qc_auto_convert_original)
                headers, first_numeric_line, timestamp_format, headers_line, first_lines = get_headers_qc(filename=filename)
                first_lines = [e.replace('Sc_negl,', 'sc_negl,') for e in first_lines]
                data = _load_data(filename=filename, resolution='hh', headers=headers, skip_header=first_numeric_line - 1)
                data = update_names_qc(data=data)
                header = '\n'.join(first_lines) + '\n' + ','.join(data.dtype.names)
                if os.path.isfile(filename_backup) and os.stat(filename_backup).st_size > 0:
                    log.warning("Pipeline qc_auto_convert renamed file exists {fb}, overwriting {f}".format(f=filename, fb=filename_backup))
                else:
                    log.debug("Pipeline qc_auto_convert renaming {f} to {fb}".format(f=filename, fb=filename_backup))
                    os.rename(filename, filename_backup)
                log.debug("Pipeline qc_auto_convert saving converted version of {f}".format(f=filename))
                save_csv_txt(filename=filename, data=data, header=header)

        self.post_validate()
        log.info("Pipeline qc_auto_convert execution finished")



class PipelineQCVisualCross(object):
    '''
    Class to control execution of qc_visual_cross step.
    
    This is an external step and is only necessary for extended QA/QC activities.
    '''
    QC_VISUAL_CROSS_EXECUTE = False # TODO: change default when method implemented
    QC_VISUAL_CROSS_DIR = "03_qc_visual_cross"

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of qc_visual_cross step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('qc_visual_cross_execute', self.QC_VISUAL_CROSS_EXECUTE)
        self.execute = self.QC_VISUAL_CROSS_EXECUTE # TODO: remove when method implemented
        self.qc_visual_cross_dir = self.pipeline.configs.get('qc_visual_cross_dir', os.path.join(self.pipeline.data_dir, self.QC_VISUAL_CROSS_DIR))

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        pass

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        pass

    def run(self):
        '''
        Executes qc_visual_cross
        '''

        log.info("Pipeline qc_visual_cross execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.qc_visual_cross_dir, label='qc_visual_cross.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        # TODO: implement run

        self.post_validate()
        log.info("Pipeline qc_visual_cross execution finished")


class PipelineUstarMP(object):
    '''
    Class to control execution of ustar_mp step.
    Executes USTAR Moving Point Threshold estimation.
    '''
    USTAR_MP_EXECUTE = True
    USTAR_MP_EX = 'ustar_mp'
    USTAR_MP_DIR = '04_ustar_mp'
    _OUTPUT_FILE_PATTERNS = [
        "{s}_usmp_????.txt",
        OUTPUT_LOG_TEMPLATE.format(t='*'),
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of ustar_mp step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.label = 'ustar_mp'
        self.execute = self.pipeline.configs.get('ustar_mp_execute', self.USTAR_MP_EXECUTE)
        self.ustar_mp_ex = self.pipeline.configs.get('ustar_mp_ex', os.path.join(self.pipeline.tool_dir, self.USTAR_MP_EX))
        self.ustar_mp_dir = self.pipeline.configs.get('ustar_mp_dir', os.path.join(self.pipeline.data_dir, self.USTAR_MP_DIR))
        self.ustar_mp_dir_fmt = self.ustar_mp_dir + os.sep
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.input_qc_auto_dir = self.pipeline.qc_auto.qc_auto_dir + os.sep
        self.output_log = os.path.join(self.ustar_mp_dir, 'report_{t}.txt'.format(t=self.pipeline.run_id))
        self.cmd_txt = 'cd "{o}" {cmd_sep} mkdir input {cmd_sep} {cp} "{i}"*_ustar_*.csv ./input/ {cmd_sep} {c} -input_path=./input/ -output_path=./ > "{log}"'
        self.cmd = self.cmd_txt.format(c=self.ustar_mp_ex, i=self.input_qc_auto_dir, o=self.ustar_mp_dir_fmt, log=self.output_log, cmd_sep=CMD_SEP, cp=COPY)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check executable
        test_file(tfile=self.ustar_mp_ex, label='{s}.pre_validate'.format(s=self.label))

        # check dependency steps
        self.pipeline.qc_auto.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.ustar_mp_dir, label='{s}.post_validate'.format(s=self.label))

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.ustar_mp_dir, label='{s}.post_validate'.format(s=self.label))

    def run(self):
        '''
        Executes ustar_mp
        '''

        log.info('Pipeline {s} execution started'.format(s=self.label))
        self.pre_validate()

        create_replace_dir(tdir=self.ustar_mp_dir, label='{s}.run'.format(s=self.label), suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info('Execution command: {c}'.format(c=self.cmd))
        if self.pipeline.simulation:
            log.info('Simulation only, {s} execution command skipped'.format(s=self.label))
        else:
            run_command(self.cmd)
            self.post_validate()
        log.info('Pipeline {s} execution finished'.format(s=self.label))


class PipelineUstarCP(object):
    '''
    Class to control execution of ustar_cp step.
    Executes Ustar Changing Point threshold estimation.
    '''
    USTAR_CP_EXECUTE = True
    USTAR_CP_EX = "ustar_cp"
    USTAR_CP_DIR = "05_ustar_cp"
    _OUTPUT_FILE_PATTERNS = [
        "{s}_uscp_????.txt",
        OUTPUT_LOG_TEMPLATE.format(t='*'),
    ]
    USTAR_CP_MCR_DIR = None

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of ustar_cp step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.label = 'ustar_cp'
        self.execute = self.pipeline.configs.get('ustar_cp_execute', self.USTAR_CP_EXECUTE)
        self.ustar_cp_ex = self.pipeline.configs.get('ustar_cp_ex', os.path.join(self.pipeline.tool_dir, self.USTAR_CP_EX))
        self.ustar_cp_dir = self.pipeline.configs.get('ustar_cp_dir', os.path.join(self.pipeline.data_dir, self.USTAR_CP_DIR))
        self.ustar_cp_dir_fmt = self.ustar_cp_dir + os.sep
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.input_qc_auto_dir = self.pipeline.qc_auto.qc_auto_dir + os.sep
        self.ustar_cp_mcr_dir = self.pipeline.configs.get('ustar_cp_mcr_dir', self.USTAR_CP_MCR_DIR)
        self.output_log = os.path.join(self.ustar_cp_dir, 'report_{t}.txt'.format(t=self.pipeline.run_id))
        self.cmd_txt = ''
        self.cmd_txt += 'cd "{o}"' + ' {cmd_sep} '
        self.cmd_txt += 'mkdir input' + ' {cmd_sep} '
        self.cmd_txt += '{cp} "{i}"*_ustar_*.csv ./input/' + ' {cmd_sep} '
#        self.cmd_txt += '{cp} "{i}"*_ustar_*.csv .' + ' {cmd_sep} '
        self.cmd_txt += '{cp} {c} .' + ' {cmd_sep} '
#        self.cmd_txt += './{clocal} input/ > "{log}"' + ' {cmd_sep} '
        self.cmd_txt += 'cd "{o}" {cmd_sep} ./{clocal} "{o}input/" "{o}"> "{log}"' + ' {cmd_sep} '
        self.cmd_txt += '{dl} {clocal}'
        self.cmd = self.cmd_txt.format(c=self.ustar_cp_ex,
                                       clocal=os.path.basename(self.ustar_cp_ex),
                                       i=self.input_qc_auto_dir,
                                       o=self.ustar_cp_dir_fmt,
                                       log=self.output_log,
                                       cmd_sep=CMD_SEP,
                                       cp=COPY,
                                       dl=DELETE)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check can run
        if (os.name == 'posix'):
            log.debug("Unix-based system detected, checking MCR")
            if (self.ustar_cp_mcr_dir is None) or (not os.path.isdir(self.ustar_cp_mcr_dir)):
                msg = "Value '{d}' is not a valid directory for MATLAB Compiler Runtime path, skipping pre-validate for {s} step".format(d=self.ustar_cp_mcr_dir, s=self.label)
                log.error(msg)
                return

        # check executable
        test_file(tfile=self.ustar_cp_ex, label='{s}.pre_validate'.format(s=self.label))

        # check dependency steps
        self.pipeline.qc_auto.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.ustar_cp_dir, label='{s}.post_validate'.format(s=self.label))

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.ustar_cp_dir, label='{s}.post_validate'.format(s=self.label), log_only=True)

    def run(self):
        '''
        Executes ustar_cp
        '''

        log.info("Pipeline {s} execution started".format(s=self.label))
        self.pre_validate()

        create_replace_dir(tdir=self.ustar_cp_dir, label='{s}.run'.format(s=self.label), suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info('Execution command: {c}'.format(c=self.cmd))
        if self.pipeline.simulation:
            log.info('Simulation only, {s} execution command skipped'.format(s=self.label))
        else:
            if self.run_ustarcp():
                self.post_validate()
        log.info('Pipeline {s} execution finished'.format(s=self.label))

    def run_ustarcp(self):
        # on Unix systems, the MATLAB Compiler Runtime has to be configured first
        if (os.name == 'posix'):
            log.debug("Unix-based system detected, setting environment variables")
            if (self.ustar_cp_mcr_dir is None) or (not os.path.isdir(self.ustar_cp_mcr_dir)):
                msg = "Value '{d}' is not a valid directory for MATLAB Compiler Runtime path, skipping {s} step".format(d=self.ustar_cp_mcr_dir, s=self.label)
                log.error(msg)
                return False

            ldlib = os.environ.get("LD_LIBRARY_PATH")
            ldlib = ('' if ldlib is None else ldlib)
            #mcr_jre_dir = "{h}/sys/java/jre/glnxa64/jre/lib/amd64".format(h=self.ustar_cp_mcr_dir) # MATLAB2012a only
            new_ldlib = ":".join([os.path.join(self.ustar_cp_mcr_dir, "runtime/glnxa64"),
                                   os.path.join(self.ustar_cp_mcr_dir, "bin/glnxa64"),
                                   os.path.join(self.ustar_cp_mcr_dir, "sys/os/glnxa64"),
                                   os.path.join(self.ustar_cp_mcr_dir, "sys/opengl/lib/glnxa64"),  # MATLAB2018a only
                                   #os.path.join(mcr_jre_dir, "server"), # MATLAB2012a only
                                   #os.path.join(mcr_jre_dir, "client"), # MATLAB2012a only
                                   #mcr_jre_dir, # MATLAB2012a only
                                   ])
            new_ldlib = (new_ldlib if ldlib.strip() == '' else ldlib + ':' + new_ldlib)

            ### MATLAB2018a
            log.debug("Setting MCR_ROOT environment variable to '{d}'".format(d=self.ustar_cp_mcr_dir))
            log.debug("Setting LD_LIBRARY_PATH environment variable to '{d}'".format(d=new_ldlib))
            os.environ["MCR_ROOT"] = self.ustar_cp_mcr_dir
            os.environ["LD_LIBRARY_PATH"] = new_ldlib

            # ### MATLAB2012a
            #log.debug("Setting MCR_HOME environment variable to '{d}'".format(d=self.ustar_cp_mcr_dir))
            #log.debug("Setting MCR_JRE environment variable to '{d}'".format(d=mcr_jre_dir))
            #log.debug("Setting LD_LIBRARY_PATH environment variable to '{d}'".format(d=new_ldlib))
            #os.environ["MCR_HOME"] = self.ustar_cp_mcr_dir
            #os.environ["MCR_JRE"] = mcr_jre_dir
            #os.environ["LD_LIBRARY_PATH"] = new_ldlib

        run_command(self.cmd)
        return True


class PipelineMeteoERA(object):
    '''
    Class to control execution of meteo_era step.
    
    N.B.: Step dependent on external Python code to be integrated in future releases.
    '''
    METEO_ERA_EXECUTE = False # TODO: change default when method implemented
    METEO_ERA_DIR = "06_meteo_era"
    _OUTPUT_FILE_PATTERNS = [
        "{s}_????.csv",
        "stat_{s}.txt",
        "stat30_{s}_nocorr.txt",
        "stat30_{s}.txt",
    ]
    _OUTPUT_FILE_PATTERNS_EXTRA = [
        "{s}_????-????.nc",
        "{s}_LWin_????-????.pdf", # missing for some sites
        "{s}_LWin_calc_????-????.pdf", # missing for some sites
        "{s}_nocorr_????.csv",
        "{s}_Pa_????-????.pdf", # missing for some sites
        "{s}_Precip_????-????.pdf", # missing for some sites
        "{s}_Rg_????-????.pdf", # missing for some sites
        "{s}_Ta_????-????.pdf", # missing for some sites
        "{s}_VPD_????-????.pdf", # missing for some sites
        "{s}_WS_????-????.pdf", # missing for some sites
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of meteo_era step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('meteo_era_execute', self.METEO_ERA_EXECUTE)
        self.execute = self.METEO_ERA_EXECUTE # TODO: remove when method implemented
        self.meteo_era_dir = self.pipeline.configs.get('meteo_era_dir', os.path.join(self.pipeline.data_dir, self.METEO_ERA_DIR))
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.output_file_patterns_extra = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_EXTRA]

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        pass

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.meteo_era_dir, label='meteo_era.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.meteo_era_dir, label='meteo_era.post_validate', log_only=True)
        test_file_list(file_list=self.output_file_patterns_extra, tdir=self.meteo_era_dir, label='meteo_era.post_validate', log_only=True)

        # test "stat_{s}.txt" file for 100.0 % missing data on variables
        self.check_era_stat(log_only=True)

    def check_era_stat(self, filename=None, log_only=False):
        '''
        Checks stats file generated by ERA downscaling.
        If percentage of missing values is not in range (0-100) or
        if more than two variables have 100% missing, stops execution
        (returns False if simulation only)
        
        :param filename: full path of file to be checked (default used if not provided)
        :type filename: str
        :rtype: bool
        '''

        if filename is None:
            era_stat_file = os.path.join(self.meteo_era_dir, "stat_{s}.txt".format(s=self.pipeline.siteid))
        else:
            era_stat_file = filename

        if not os.path.isfile(era_stat_file):
            msg = 'meteo_era stat file not found: {f}'.format(f=era_stat_file)
            if log_only:
                log.error(msg)
                return False
            else:
                log.critical(msg)
                if self.pipeline.simulation:
                    return False
                else:
                    raise ONEFluxPipelineError(msg)

        count_files_at_100perc = 0
        valid_var_labels = ['Ta', 'Pa', 'VPD', 'WS', 'Precip', 'Rg', 'LWin', 'LWin_calc']
        valid_var_labels_critical = ['Ta', 'Rg']
        valid_var_labels_missing = []
        with open(era_stat_file, 'rU') as f:
            lines = f.readlines()
        for line in lines[1:]:
            l = line.strip().split(',')

            # variable label
            var_label = l[0].strip()
            if var_label not in valid_var_labels:
                msg = '{s}: invalid variable label \'{p}\' in ERA stat file {f}'.format(s=self.pipeline.siteid, p=var_label, f=era_stat_file)
                log.critical(msg)
                if self.pipeline.simulation:
                    return False
                else:
                    raise ONEFluxPipelineError(msg)

            # percent missing data
            try:
                perc = float(l[2])
            except ValueError:
                msg = "{s}: invalid percentage '{p}' in ERA stat file {f}".format(s=self.pipeline.siteid, p=l[2], f=era_stat_file)
                log.critical(msg)
                if self.pipeline.simulation:
                    return False
                else:
                    raise ONEFluxPipelineError(msg)

            if (perc < 0.0) or (perc > 100.0):
                msg = "{s}: invalid percentage '{p}' in ERA stat file {f}".format(s=self.pipeline.siteid, p=l[2], f=era_stat_file)
                log.critical(msg)
                if self.pipeline.simulation:
                    return False
                else:
                    raise ONEFluxPipelineError(msg)

            if perc == 100.0:
                count_files_at_100perc += 1
                if var_label in valid_var_labels_critical:
                    valid_var_labels_missing.append(var_label)
                log.warning("{s}: found 100% missing for variable '{v}' in ERA stat file {f}".format(s=self.pipeline.siteid, v=l[0], f=era_stat_file))

        if count_files_at_100perc > 2:
            msg = "{s}: more than one variable with 100% missing values in ERA stat file {f}".format(s=self.pipeline.siteid, f=era_stat_file)
            log.error(msg)
        
        if valid_var_labels_missing:
            msg = '{s}: critical variable(s) \'{v}\' with 100% missing values in ERA stat file {f}'.format(s=self.pipeline.siteid, v=','.join(valid_var_labels_missing), f=era_stat_file)
            log.critical(msg)
            if self.pipeline.simulation:
                return False
            else:
                raise ONEFluxPipelineError(msg)
        return True


    def run(self):
        '''
        Executes meteo_era
        '''

        log.info("Pipeline meteo_era execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.meteo_era_dir, label='meteo_era.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        # TODO: implement run

        self.post_validate()
        log.info("Pipeline meteo_era execution finished")


class PipelineMeteoMDS(object):
    '''
    Class to control execution of meteo_mds step.
    Executes the Meteorological variables
    gap-filling using MDS implementation.
    
    Step not used in ONEFlux Pipeline (MDS method applied within meteo_proc, nee_proc, energy_proc steps.
    '''
    METEO_MDS_EXECUTE = False # TODO: change default when method implemented
    METEO_MDS_DIR = "07a_meteo_mds"
    METEO_NARR_DIR = "07b_meteo_narr"
    METEO_MDS_EX = "meteo_mds"

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of meteo_mds step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('meteo_mds_execute', self.METEO_MDS_EXECUTE)
        self.execute = self.METEO_MDS_EXECUTE # TODO: remove when method implemented
        self.meteo_mds_dir = self.pipeline.configs.get('meteo_mds_dir', os.path.join(self.pipeline.data_dir, self.METEO_MDS_DIR))
        self.meteo_narr_dir = self.pipeline.configs.get('meteo_narr_dir', os.path.join(self.pipeline.data_dir, self.METEO_NARR_DIR))
        self.meteo_mds_ex = self.pipeline.configs.get('meteo_mds_ex', os.path.join(self.pipeline.tool_dir, self.METEO_MDS_EX))
        self.cmd = "" # TODO: implement

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        test_file(tfile=self.meteo_mds_ex, label='meteo_mds')
        test_create_dir(tdir=self.meteo_mds_dir, label='meteo_mds')
        test_create_dir(tdir=self.meteo_narr_dir, label='meteo_narr')

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        pass

    def run(self):
        '''
        Executes meteo_mds
        '''

        log.info("Pipeline meteo_mds execution started")
        self.pre_validate()

        # TODO: implement run

        self.post_validate()
        log.info("Pipeline meteo_mds execution finished")

    def run_meteomds(self):
        einput = self.qcauto + os.sep
        eoutput = self.meteomds + os.sep
        eoutput_log = os.path.join(self.meteomds, 'results.txt')

        for tdir in [os.path.join(self.meteomds, i) for i in ['input', 'input_nee', 'ta', 'swin', 'vpd', 'rh', 'nee']]:
            self.test_create_dir(tdir=tdir, label='MeteoMDS')

        cp_data = "{copy} {i}*_meteo_*.csv {o}".format(copy=COPY, i=einput, o=os.path.join(eoutput, 'input') + os.sep)
        cp_data_nee = "{copy} {i}*_nee_*.csv {o}".format(copy=COPY, i=einput, o=os.path.join(eoutput, 'input_nee') + os.sep)
        log.info("Data copy command '{c}'".format(c=cp_data))
        log.info("Data copy command '{c}' (NEE)".format(c=cp_data_nee))
        if not self.simulation:
            os.system(cp_data)
            os.system(cp_data_nee)

        input_filenames = [ os.path.join(i[0], j) for i in os.walk(os.path.join(self.meteomds, 'input')) for j in i[2] ]
        input_filenames = ','.join([ i for i in input_filenames if '_meteo_' in i])
        input_filenames_nee = [ os.path.join(i[0], j) for i in os.walk(os.path.join(self.meteomds, 'input_nee')) for j in i[2] ]
        input_filenames_nee = ','.join([ i for i in input_filenames_nee if '_nee_' in i])

        cp_tool = "{copy} {c} {o}".format(copy=COPY, c=self.ex_meteomds, o=eoutput)
        cmd_ta = "cd {o} {cmd_sep} ./{c} -input={f} -output={n} -tofill=Ta > {l}".format(cmd_sep=CMD_SEP, o=eoutput, c=os.path.basename(self.ex_meteomds), f=input_filenames, n=os.path.join(self.meteomds, 'ta') + os.sep, l=eoutput_log[:-4] + '_ta.txt')
        cmd_swin = "cd {o} {cmd_sep} ./{c} -input={f} -output={n} -tofill=SWin > {l}".format(cmd_sep=CMD_SEP, o=eoutput, c=os.path.basename(self.ex_meteomds), f=input_filenames, n=os.path.join(self.meteomds, 'swin') + os.sep, l=eoutput_log[:-4] + '_swin.txt')
        cmd_vpd = "cd {o} {cmd_sep} ./{c} -input={f} -output={n} -tofill=VPD > {l}".format(cmd_sep=CMD_SEP, o=eoutput, c=os.path.basename(self.ex_meteomds), f=input_filenames, n=os.path.join(self.meteomds, 'vpd') + os.sep, l=eoutput_log[:-4] + '_vpd.txt')
        cmd_rh = "cd {o} {cmd_sep} ./{c} -input={f} -output={n} -tofill=RH > {l}".format(cmd_sep=CMD_SEP, o=eoutput, c=os.path.basename(self.ex_meteomds), f=input_filenames, n=os.path.join(self.meteomds, 'rh') + os.sep, l=eoutput_log[:-4] + '_rh.txt')
        cmd_nee = "cd {o} {cmd_sep} ./{c} -input={f} -output={n} -tofill=NEE > {l}".format(cmd_sep=CMD_SEP, o=eoutput, c=os.path.basename(self.ex_meteomds), f=input_filenames_nee, n=os.path.join(self.meteomds, 'nee') + os.sep, l=eoutput_log[:-4] + '_nee.txt')
        del_tool = "{delete} {o}{c}".format(delete=DELETE, o=eoutput, c=os.path.basename(self.ex_meteomds))

        log.info("Tool copy command '{c}'".format(c=cp_tool))
        log.info("Execution Ta   command '{c}'".format(c=cmd_ta))
        log.info("Execution SWin command '{c}'".format(c=cmd_swin))
        log.info("Execution VPD  command '{c}'".format(c=cmd_vpd))
        log.info("Execution RH   command '{c}'".format(c=cmd_rh))
        log.info("Execution NEE  command '{c}'".format(c=cmd_nee))
        log.info("Tool delete command '{c}'".format(c=del_tool))
        if not self.simulation:
            os.system(cp_tool)
            os.system(cmd_ta)
            os.system(cmd_swin)
            os.system(cmd_vpd)
            os.system(cmd_rh)
            os.system(cmd_nee)
            os.system(del_tool)



class PipelineMeteoProc(object):
    '''
    Class to control execution of meteo_proc step.
    Executes the Meteorological variables gap-filling using
    the ECMWF ERA-5 (or ERA-Interim) downscaled data product.
    '''
    METEO_PROC_EXECUTE = True
    METEO_PROC_DIR = "07_meteo_proc"
    METEO_PROC_EX = "meteo_proc"
    _OUTPUT_FILE_PATTERNS = [
        "{s}_meteo_hh.csv",
        "{s}_meteo_dd.csv",
        "{s}_meteo_ww.csv",
        "{s}_meteo_mm.csv",
        "{s}_meteo_yy.csv",
        OUTPUT_LOG_TEMPLATE.format(t='*'),
    ]
    _OUTPUT_FILE_PATTERNS_INFO = [
        "{s}_meteo_hh_info.txt",
        "{s}_meteo_dd_info.txt",
        "{s}_meteo_ww_info.txt",
        "{s}_meteo_mm_info.txt",
        "{s}_meteo_yy_info.txt",
    ]

    def __init__(self, pipeline):
        '''
        Initializes paramters for execution of meteo_proc step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('meteo_proc_execute', self.METEO_PROC_EXECUTE)
        self.meteo_proc_ex = self.pipeline.configs.get('meteo_proc_ex', os.path.join(self.pipeline.tool_dir, self.METEO_PROC_EX))
        self.meteo_proc_dir = self.pipeline.configs.get('meteo_proc_dir', os.path.join(self.pipeline.data_dir, self.METEO_PROC_DIR))
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.output_file_patterns_info = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_INFO]
        self.input_meteo_era_dir = '..' + os.sep + os.path.basename(self.pipeline.meteo_era.meteo_era_dir) + os.sep
        self.input_qc_auto_dir = '..' + os.sep + os.path.basename(self.pipeline.qc_auto.qc_auto_dir) + os.sep
        self.output_meteo_proc_dir = self.meteo_proc_dir + os.sep
        self.output_log = os.path.join(self.meteo_proc_dir, 'report_{t}.txt'.format(t=self.pipeline.run_id))
        self.cmd_txt = 'cd "{o}" {cmd_sep} {c} -qc_auto_path="{q}" -era_path="{e}" -output_path=. > "{log}"'
        self.cmd = self.cmd_txt.format(o=self.output_meteo_proc_dir,
                                       cmd_sep=CMD_SEP,
                                       c=self.meteo_proc_ex,
                                       q=self.input_qc_auto_dir,
                                       e=self.input_meteo_era_dir,
                                       log=self.output_log)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check executable
        test_file(tfile=self.meteo_proc_ex, label='meteo_proc.pre_validate')

        # check dependency steps
        self.pipeline.qc_auto.post_validate()
        self.pipeline.meteo_era.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.meteo_proc_dir, label='meteo_proc.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.meteo_proc_dir, label='meteo_proc.post_validate')
        test_file_list(file_list=self.output_file_patterns_info, tdir=self.meteo_proc_dir, label='meteo_proc.post_validate')

    def run(self):
        '''
        Executes meteo_proc
        '''

        log.info("Pipeline meteo_proc execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.meteo_proc_dir, label='meteo_proc.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info("Execution command '{c}'".format(c=self.cmd))
        if self.pipeline.simulation:
            log.info("Simulation only, meteo_proc execution command skipped")
        else:
            run_command(self.cmd)
            self.post_validate()

        log.info("Pipeline meteo_proc execution finished")


class PipelineNEEProc(object):
    '''
    Class to control execution of nee_proc step.
    Executes the NEE filtering, gapfilling, uncertainty estimation,
    and reference model selection.
    '''
    NEE_PROC_EXECUTE = True
    NEE_PROC_DIR = "08_nee_proc"
    NEE_PROC_EX = "nee_proc"
    _OUTPUT_FILE_PATTERNS = [
        "{s}_NEE_hh.csv",
        "{s}_NEE_dd.csv",
        "{s}_NEE_ww.csv",
        "{s}_NEE_mm.csv",
        "{s}_NEE_yy.csv",
        OUTPUT_LOG_TEMPLATE.format(t='*'),
    ]
    _OUTPUT_FILE_PATTERNS_INFO = [
        "{s}_NEE_hh_info.txt",
        "{s}_NEE_ww_info.txt",
        "{s}_NEE_dd_info.txt",
        "{s}_NEE_mm_info.txt",
        "{s}_NEE_yy_info.txt",
    ]
    _OUTPUT_FILE_PATTERNS_Y = [
        "{s}_USTAR_percentiles_y.csv",
    ]
    _OUTPUT_FILE_PATTERNS_Y_ALT = [
        "{s}_NEE_percentiles_y_hh.csv",
        "{s}_NEE_percentiles_y.csv",
    ]
    _OUTPUT_FILE_PATTERNS_C = [
        "{s}_????_????_USTAR_percentiles_c.csv", # not generated when fewer than 3 site-years
    ]
    _OUTPUT_FILE_PATTERNS_C_ALT = [
        "{s}_NEE_percentiles_c_hh.csv", # not generated when fewer than 3 site-years
        "{s}_NEE_percentiles_c.csv", # not generated when fewer than 3 site-years
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of nee_proc step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('nee_proc_execute', self.NEE_PROC_EXECUTE)
        self.nee_proc_ex = self.pipeline.configs.get('nee_proc_ex', os.path.join(self.pipeline.tool_dir, self.NEE_PROC_EX))
        self.nee_proc_dir = self.pipeline.configs.get('nee_proc_dir', os.path.join(self.pipeline.data_dir, self.NEE_PROC_DIR))
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.output_file_patterns_info = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_INFO]
        self.output_file_patterns_y = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_Y]
        self.output_file_patterns_y_alt = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_Y_ALT]
        self.output_file_patterns_c = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_C]
        self.output_file_patterns_c_alt = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_C_ALT]
        self.input_qc_auto_dir = '..' + os.sep + os.path.basename(self.pipeline.qc_auto.qc_auto_dir) + os.sep
        self.input_ustar_mp_dir = '..' + os.sep + os.path.basename(self.pipeline.ustar_mp.ustar_mp_dir) + os.sep
        self.input_ustar_cp_dir = '..' + os.sep + os.path.basename(self.pipeline.ustar_cp.ustar_cp_dir) + os.sep
        self.input_meteo_proc_dir = '..' + os.sep + os.path.basename(self.pipeline.meteo_proc.meteo_proc_dir) + os.sep
        self.output_nee_proc_dir = self.nee_proc_dir + os.sep
        self.output_log = os.path.join(self.nee_proc_dir, 'report_{t}.txt'.format(t=self.pipeline.run_id))
        self.cmd_txt = 'cd "{o}" {cmd_sep} {c} -qc_auto_path="{q}" -ustar_mp_path="{ump}" -ustar_cp_path="{ucp}" -meteo_path="{m}" -output_path=. > "{log}"'
        self.cmd = self.cmd_txt.format(o=self.output_nee_proc_dir,
                                       cmd_sep=CMD_SEP,
                                       c=self.nee_proc_ex,
                                       q=self.input_qc_auto_dir,
                                       ump=self.input_ustar_mp_dir,
                                       ucp=self.input_ustar_cp_dir,
                                       m=self.input_meteo_proc_dir,
                                       log=self.output_log)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check executable
        test_file(tfile=self.nee_proc_ex, label='nee_proc.pre_validate')

        # check dependency steps
        self.pipeline.qc_auto.post_validate()
        self.pipeline.ustar_mp.post_validate()
        self.pipeline.ustar_cp.post_validate()
        self.pipeline.meteo_proc.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.nee_proc_dir, label='nee_proc.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.nee_proc_dir, label='nee_proc.post_validate')
        test_file_list(file_list=self.output_file_patterns_info, tdir=self.nee_proc_dir, label='nee_proc.post_validate')
        test_file_list(file_list=self.output_file_patterns_y, tdir=self.nee_proc_dir, label='nee_proc.post_validate')
        test_file_list_or(file_list=self.output_file_patterns_y_alt, tdir=self.nee_proc_dir, label='nee_proc.post_validate')
        test_file_list(file_list=self.output_file_patterns_c, tdir=self.nee_proc_dir, label='nee_proc.post_validate', log_only=True)
        test_file_list_or(file_list=self.output_file_patterns_c_alt, tdir=self.nee_proc_dir, label='nee_proc.post_validate', log_only=True)

    def run(self):
        '''
        Executes nee_proc
        '''

        log.info("Pipeline nee_proc execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.nee_proc_dir, label='nee_proc.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info("Execution command '{c}'".format(c=self.cmd))
        if self.pipeline.simulation:
            log.info("Simulation only, nee_proc execution command skipped")
        else:
            run_command(self.cmd)
            self.post_validate()

        log.info("Pipeline nee_proc execution finished")


class PipelineEnergyProc(object):
    '''
    Class to control execution of energy_proc step.
    Executes the LE and H filtering, gapfilling, and corrections.
    '''
    ENERGY_PROC_EXECUTE = True
    ENERGY_PROC_EX = "energy_proc"
    ENERGY_PROC_DIR = "09_energy_proc"
    _OUTPUT_FILE_PATTERNS = [
        "{s}_energy_hh_info.txt",
        "{s}_energy_dd_info.txt",
        "{s}_energy_ww_info.txt",
        "{s}_energy_mm_info.txt",
        "{s}_energy_yy_info.txt",
        "{s}_energy_hh.csv",
        "{s}_energy_dd.csv",
        "{s}_energy_ww.csv",
        "{s}_energy_mm.csv",
        "{s}_energy_yy.csv",
        OUTPUT_LOG_TEMPLATE.format(t='*'),
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of energy_proc step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('energy_proc_execute', self.ENERGY_PROC_EXECUTE)
        self.energy_proc_ex = self.pipeline.configs.get('energy_proc_ex', os.path.join(self.pipeline.tool_dir, self.ENERGY_PROC_EX))
        self.energy_proc_dir = self.pipeline.configs.get('energy_proc_dir', os.path.join(self.pipeline.data_dir, self.ENERGY_PROC_DIR))
        self.energy_proc_input_dir = os.path.join(self.energy_proc_dir, 'input')
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.input_qc_auto_dir = '..' + os.sep + os.path.basename(self.pipeline.qc_auto.qc_auto_dir) + os.sep
        self.output_energy_proc_dir = self.energy_proc_dir + os.sep
        self.output_energy_proc_input_dir = self.energy_proc_input_dir + os.sep
        self.output_log = os.path.join(self.energy_proc_dir, OUTPUT_LOG_TEMPLATE.format(t=self.pipeline.run_id))
        self.cmd_cp_data_txt = '{copy} "{i}"/*_qca_energy*.csv "{o}"'
        self.cmd_cp_data = self.cmd_cp_data_txt.format(copy=COPY, i=self.pipeline.qc_auto.qc_auto_dir, o=self.output_energy_proc_input_dir)
        self.cmd_cp_tool_txt = '{copy} {c} "{o}"'
        self.cmd_cp_tool = self.cmd_cp_tool_txt.format(copy=COPY, c=self.energy_proc_ex, o=self.output_energy_proc_dir)
        self.cmd_execute_txt = 'cd "{o}" {cmd_sep} ./{c} -input_path="input" -output_path="." > "{log}"'
        self.cmd_execute = self.cmd_execute_txt.format(cmd_sep=CMD_SEP, o=self.output_energy_proc_dir, c=os.path.basename(self.energy_proc_ex), log=self.output_log)
        self.cmd_del_tool_txt = '{delete} "{o}{c}"'
        self.cmd_del_tool = self.cmd_del_tool_txt.format(delete=DELETE, o=self.output_energy_proc_dir, c=os.path.basename(self.energy_proc_ex))

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check executable
        test_file(tfile=self.energy_proc_ex, label='energy_proc.pre_validate')

        # check dependency steps
        self.pipeline.qc_auto.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.energy_proc_dir, label='energy_proc.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.energy_proc_dir, label='energy_proc.post_validate')

    def run(self):
        '''
        Executes energy_proc
        '''

        log.info("Pipeline energy_proc execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.energy_proc_dir, label='energy_proc.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)
        test_create_dir(tdir=self.energy_proc_input_dir, label='energy_proc.run', simulation=self.pipeline.simulation)

        log.info("Data copy command '{c}'".format(c=self.cmd_cp_data))
        log.info("Tool copy command '{c}'".format(c=self.cmd_cp_tool))
        log.info("Execution command '{c}'".format(c=self.cmd_execute))
        log.info("Tool delete command '{c}'".format(c=self.cmd_del_tool))
        if self.pipeline.simulation:
            log.info("Simulation only, energy_proc execution command skipped")
        else:
            run_command(self.cmd_cp_data)
            run_command(self.cmd_cp_tool)
            run_command(self.cmd_execute)
            run_command(self.cmd_del_tool)
            self.post_validate()

        log.info("Pipeline energy_proc execution finished")



class PipelineNEEPartitionNT(object):
    '''
    Class to control execution of nee_partition_nt step
    '''
    NEE_PARTITION_NT_EXECUTE = True
    NEE_PARTITION_NT_DIR = "10_nee_partition_nt"
    _OUTPUT_FILE_PATTERNS_Y = [
        "nee_y_?.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME), # 1.25, 3.75, 8.75
        "nee_y_??.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME), # 11.25, ..., 98.75
        "nee_y_50_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),
    ]
    _OUTPUT_FILE_PATTERNS_C = [
        "nee_c_?.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME), # 1.25, 3.75, 8.75
        "nee_c_??.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME), # 11.25, ..., 98.75
        "nee_c_50_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of nee_partition_nt step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.label = 'nee_partition_nt'
        self.execute = self.pipeline.configs.get('nee_partition_nt_execute', self.NEE_PARTITION_NT_EXECUTE)
        self.nee_partition_nt_dir = self.pipeline.configs.get('nee_partition_nt_dir', os.path.join(self.pipeline.data_dir, self.NEE_PARTITION_NT_DIR))
        self.output_file_patterns_y = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_Y]
        self.output_file_patterns_c = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_C]
        self.prod_to_compare = self.pipeline.configs.get('prod_to_compare', PROD_TO_COMPARE)
        self.perc_to_compare = self.pipeline.configs.get('perc_to_compare', PERC_TO_COMPARE)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check dependency steps
        self.pipeline.nee_proc.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''

        # check output directory
        test_dir(tdir=self.nee_partition_nt_dir, label='{s}.post_validate'.format(s=self.label))

        # check output files
        test_file_list(file_list=self.output_file_patterns_y, tdir=self.nee_partition_nt_dir, label='{s}.post_validate'.format(s=self.label), log_only=True)
        test_file_list(file_list=self.output_file_patterns_c, tdir=self.nee_partition_nt_dir, label='{s}.post_validate'.format(s=self.label), log_only=True)

    def run(self):
        '''
        Executes nee_partition_nt
        '''

        log.info("Pipeline {s} execution started".format(s=self.label))
        self.pre_validate()

        create_replace_dir(tdir=self.nee_partition_nt_dir, label='{s}.run'.format(s=self.label), suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info('Execution command: oneflux.tools.partition_nt.run_partition_nt()')
        if self.pipeline.simulation:
            log.info('Simulation only, {s} execution command skipped'.format(s=self.label))
        else:
            run_partition_nt(datadir=self.pipeline.data_dir_main,
                             siteid=self.pipeline.siteid,
                             sitedir=self.pipeline.site_dir,
                             years_to_compare=range(self.pipeline.first_year, self.pipeline.last_year + 1),
                             py_remove_old=False,
                             prod_to_compare=self.prod_to_compare,
                             perc_to_compare=self.perc_to_compare,)
            self.post_validate()

        log.info("Pipeline {s} execution finished".format(s=self.label))


class PipelineNEEPartitionDT(object):
    '''
    Class to control execution of nee_partition_dt step
    '''
    NEE_PARTITION_DT_EXECUTE = True
    NEE_PARTITION_DT_DIR = "11_nee_partition_dt"
    _OUTPUT_FILE_PATTERNS_Y = [
        "nee_y_?.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),  # 1.25, 3.75, 8.75
        "nee_y_??.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),  # 11.25, ..., 98.75
        "nee_y_50_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),
    ]
    _OUTPUT_FILE_PATTERNS_C = [
        "nee_c_?.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),  # 1.25, 3.75, 8.75
        "nee_c_??.??_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),  # 11.25, ..., 98.75
        "nee_c_50_{s}_????{extra}.csv".format(s='{s}', extra=EXTRA_FILENAME),
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of nee_partition_dt step

        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.label = 'nee_partition_dt'
        self.execute = self.pipeline.configs.get('nee_partition_dt_execute', self.NEE_PARTITION_DT_EXECUTE)
        self.nee_partition_dt_dir = self.pipeline.configs.get('nee_partition_dt_dir', os.path.join(self.pipeline.data_dir, self.NEE_PARTITION_DT_DIR))
        self.output_file_patterns_y = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_Y]
        self.output_file_patterns_c = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_C]
        self.prod_to_compare = self.pipeline.configs.get('prod_to_compare', PROD_TO_COMPARE)
        self.perc_to_compare = self.pipeline.configs.get('perc_to_compare', PERC_TO_COMPARE)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check dependency steps
        self.pipeline.nee_proc.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''

        # check output directory
        test_dir(tdir=self.nee_partition_dt_dir, label='{s}.post_validate'.format(s=self.label))

        # check output files
        test_file_list(file_list=self.output_file_patterns_y, tdir=self.nee_partition_dt_dir, label='{s}.post_validate'.format(s=self.label), log_only=True)
        test_file_list(file_list=self.output_file_patterns_c, tdir=self.nee_partition_dt_dir, label='{s}.post_validate'.format(s=self.label), log_only=True)

    def run(self, count=0, rerun=False):
        '''
        Executes nee_partition_dt
        '''

        log.info("Pipeline {s} execution started".format(s=self.label))
        self.pre_validate()

        # if execution fails on optimization step, add window to exclusion and restart with count+1
        suffix = (self.pipeline.run_id if (count == 0) else self.pipeline.run_id + '_{c}'.format(c=count))

        # either first execution or final execution after all windows found, so previous files can be removed
        if not rerun:
            # removes original intermediate files from re-runs
            create_and_empty_dir(tdir=self.nee_partition_dt_dir, label='{s}.run'.format(s=self.label), suffix=suffix, simulation=self.pipeline.simulation)

            # # keeping original intermediate files from re-runs
            # create_replace_dir(tdir=self.nee_partition_dt_dir, label='{s}.run'.format(s=self.label), suffix=suffix, simulation=self.pipeline.simulation)

        # changed to true if a call with rerun=True made in this iteration
        rerun_call = False

        # call partitioning and catches optimization fail exceptions
        log.info('Execution command: oneflux.tools.partition_dt.run_partition_dt()')
        if self.pipeline.simulation:
            log.info('Simulation only, {s} execution command skipped'.format(s=self.label))
        else:
            try:
                run_partition_dt(datadir=self.pipeline.data_dir_main,
                                 siteid=self.pipeline.siteid,
                                 sitedir=self.pipeline.site_dir,
                                 years_to_compare=range(self.pipeline.first_year, self.pipeline.last_year + 1),
                                 py_remove_old=False,
                                 prod_to_compare=self.prod_to_compare,
                                 perc_to_compare=self.perc_to_compare,)
            except ONEFluxPartitionBrokenOptError as e:
                error_filename = os.path.join(self.pipeline.data_dir, PARTITIONING_DT_ERROR_FILE.format(s=self.pipeline.siteid))
                lines2append = ''
                if not os.path.isfile(error_filename):
                    lines2append += 'site_year_nee_des,begin,end\n'
                lines2append += e.line2add + '\n'
                with open(error_filename, "a") as f:
                    f.write(lines2append)
                log.warning('Added line "{line}" to error file "{f}"'.format(line=e.line2add, f=error_filename))

                # if not alredy in rerun mode, marks as rerun, when returning from next call knows rerun for all versions required
                if not rerun:
                    log.warning('Will re-run all years/perc/prod for site {s} with {n} restarts'.format(s=self.pipeline.siteid, n=count + 10000))
                    rerun_call = True
                log.warning('Restarting DT partitioning for site {s} with {n} restarts'.format(s=self.pipeline.siteid, n=count))
                self.run(count=count + 1, rerun=True)

            if rerun_call:
                self.run(count=count + 10000, rerun=False)

            self.post_validate()

        log.info("Pipeline {s} execution finished".format(s=self.label))



class PipelineNEEPartitionSR(object):
    '''
    Class to control execution of nee_partition_nt step
    '''
    NEE_PARTITION_SR_EXECUTE = False # TODO: change default when method implemented
    NEE_PARTITION_SR_DIR = os.path.join("13_nee_partition_sr", "reco")
    _OUTPUT_FILE_PATTERNS = [
        "{s}_????_sr_reco.csv",
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of nee_partition_sr step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('nee_partition_st_execute', self.NEE_PARTITION_SR_EXECUTE)
        self.execute = self.NEE_PARTITION_SR_EXECUTE # TODO: remove when method implemented
        self.nee_partition_sr_dir = self.pipeline.configs.get('nee_partition_sr_dir', os.path.join(self.pipeline.data_dir, self.NEE_PARTITION_SR_DIR))
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check dependency steps
        self.pipeline.nee_proc.post_validate()

    def post_validate(self, executed=False):
        '''
        Validate post-execution results
        '''
        log_only = not executed

        # check output directory
        test_dir(tdir=self.nee_partition_sr_dir, label='nee_partition_sr.post_validate', log_only=log_only)

        # check output files
        test_file_list(file_list=self.output_file_patterns, tdir=self.nee_partition_sr_dir, label='nee_partition_sr.post_validate', log_only=log_only)


    def run(self):
        '''
        Executes nee_partition_sr
        '''

        log.info("Pipeline nee_partition_sr execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.nee_partition_sr_dir, label='nee_partition_sr.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        # TODO: implement run

        self.post_validate(executed=True)
        log.info("Pipeline nee_partition_sr execution finished")


class PipelinePrepareUREPW(object):
    '''
    Class to control execution of data conversions in preparation
    to run URE step. Takes output of PV-Wave NT and DT steps and
    creates input files for URE.
    '''
    PREPARE_URE_EXECUTE = True
    PREPARE_URE_DIR = os.path.join("12_ure", "input")
    _OUTPUT_FILE_PATTERNS_NT_DT = [
        "{s}_????_DT_GPP.csv",
        "{s}_????_DT_Reco.csv",
        "{s}_????_NT_GPP.csv",
        "{s}_????_NT_Reco.csv",
    ]
    _OUTPUT_FILE_PATTERNS_SR = [
        "{s}_????_sr_reco.csv",
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of ure step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('prepare_ure_execute', self.PREPARE_URE_EXECUTE)
        self.prepare_ure_dir = self.pipeline.configs.get('prepare_ure_dir', os.path.join(self.pipeline.data_dir, self.PREPARE_URE_DIR))
        self.output_file_patterns_nt_dt = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_NT_DT]
        self.output_file_patterns_sr = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_SR]

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check dependency steps
        self.pipeline.nee_partition_nt.post_validate()
        self.pipeline.nee_partition_dt.post_validate()
        self.pipeline.nee_partition_sr.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.prepare_ure_dir, label='prepare_ure.post_validate')

        # check output files
        # NT and DT
        test_file_list(file_list=self.output_file_patterns_nt_dt, tdir=self.prepare_ure_dir, label='prepare_ure.post_validate')

        # SR
        test_file_list(file_list=self.output_file_patterns_sr, tdir=self.prepare_ure_dir, label='prepare_ure.post_validate', log_only=True)

    def run(self):
        '''
        Executes prepare_ure
        '''
        log.info("Pipeline prepare_ure execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.prepare_ure_dir, label='prepare_ure.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

#       #  get output files from NT and DT partitioning steps
#       #  TODO: finish implementation
        for root, _, filenames in os.walk(self.pipeline.nee_partition_nt.nee_partition_nt_dir):
            for f in filenames:
                print os.path.join(root, f)

        for root, _, filenames in os.walk(self.pipeline.nee_partition_dt.nee_partition_dt_dir):
            for f in filenames:
                print os.path.join(root, f)

        if os.path.isdir(self.pipeline.nee_partition_sr.nee_partition_sr_dir):
            for root, _, filenames in os.walk(self.pipeline.nee_partition_dt.nee_partition_sr_dir):
                for f in filenames:
                    print os.path.join(root, f)

        # execute prepare_ure step
        if not self.execute and not self.pipeline.simulation:
            # TODO: run prepare conversion step
            pass
        self.post_validate()

        log.info("Pipeline prepare_ure execution finished")


class PipelinePrepareURE(object):
    '''
    Class to control execution of data conversions in preparation
    to run URE step. Takes output of NT and DT steps and
    creates input files for URE.
    '''
    PREPARE_URE_EXECUTE = True
    PREPARE_URE_DIR = os.path.join("12_ure_input")
    DT_GPP_TEMPLATE = "{s}_{y}_DT_GPP.csv"
    DT_RECO_TEMPLATE = "{s}_{y}_DT_RECO.csv"
    NT_GPP_TEMPLATE = "{s}_{y}_NT_GPP.csv"
    NT_RECO_TEMPLATE = "{s}_{y}_NT_RECO.csv"
    _OUTPUT_FILE_PATTERNS_NT_DT = [
        DT_GPP_TEMPLATE.format(y='????', s='{s}'),
        DT_RECO_TEMPLATE.format(y='????', s='{s}'),
        NT_GPP_TEMPLATE.format(y='????', s='{s}'),
        NT_RECO_TEMPLATE.format(y='????', s='{s}'),
    ]
    _OUTPUT_FILE_PATTERNS_SR = [
        "{s}_????_sr_reco.csv",
    ]

    def __init__(self, pipeline, perc=PERC_TO_COMPARE, prod=PROD_TO_COMPARE):
        '''
        Initializes parameters for execution of ure step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.FILENAME_TEMPLATE = 'nee_{prod}_{perc}_{s}_{year}{extra}.csv'
        self.perc = perc
        self.prod = prod
        self.execute = self.pipeline.configs.get('prepare_ure_execute', self.PREPARE_URE_EXECUTE)
        self.prepare_ure_dir = self.pipeline.configs.get('prepare_ure_dir', os.path.join(self.pipeline.data_dir, self.PREPARE_URE_DIR))
        self.prepare_ure_dir_fmt = self.prepare_ure_dir + os.sep
        self.output_file_patterns_nt_dt = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_NT_DT]
        self.output_file_patterns_sr = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_SR]


    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check dependency steps
        self.pipeline.nee_partition_nt.post_validate()
        self.pipeline.nee_partition_dt.post_validate()
        self.pipeline.nee_partition_sr.post_validate()


    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.prepare_ure_dir, label='prepare_ure.post_validate')

        # check output files
        # NT and DT
        test_file_list(file_list=self.output_file_patterns_nt_dt, tdir=self.prepare_ure_dir, label='prepare_ure.post_validate')

        # SR
        test_file_list(file_list=self.output_file_patterns_sr, tdir=self.prepare_ure_dir, label='prepare_ure.post_validate', log_only=True)


    def check_cleanup_nt(self, reco, gpp, filename):
        """
        Checks and data cleanup for NT partitioning results
        
        :param reco: RECO results from NT partitioning
        :type reco: numpy.ndarray
        :param gpp: GPP results from NT partitioning
        :type gpp: numpy.ndarray
        :param filename: name of data source file (NT results)
        :type filename: str
        """

        # if NaN, INF, < -9990, < -6999 set to -9999
        reco[nan_ext(reco)] = NAN
        gpp[nan_ext(gpp)] = NAN

        # if -100 < RECO < 100, set to -9999 (replicate for GPP on same indices)
        mask_too_low = (reco < -100)
        mask_too_high = (reco > 100)
        count_too_low = numpy.sum(mask_too_low)
        count_too_high = numpy.sum(mask_too_high)
        reco[mask_too_low | mask_too_high] = NAN
        gpp[mask_too_low | mask_too_high] = NAN

        if count_too_low > 0:
            log.warning('URE checks: NT RECO below -100 [{c}]: {s}'.format(c=count_too_low, s=filename))
        if count_too_high > 0:
            log.warning('URE checks: NT RECO above 100 [{c}]: {s}'.format(c=count_too_high, s=filename))

        # if RECO or GPP have gaps, log warnings
        count_reco_nan = numpy.sum(reco < NAN_TEST)
        count_gpp_nan = numpy.sum(gpp < NAN_TEST)

        if count_reco_nan > 0:
            log.warning('URE checks: NT RECO NaN values [{c}]: {s}'.format(c=count_reco_nan, s=filename))
        if count_gpp_nan > 0:
            log.warning('URE checks: NT GPP NaN values [{c}]: {s}'.format(c=count_gpp_nan, s=filename))

        return reco, gpp


    def check_cleanup_dt(self, reco, gpp, filename):
        """
        
        :param reco: RECO results from DT partitioning
        :type reco: numpy.ndarray
        :param gpp: GPP results from DT partitioning
        :type gpp: numpy.ndarray
        :param filename: name of data source file (DT results)
        :type filename: str
        """

        # if NaN, INF, < -9990, < -6999 set to -9999
        gpp[nan_ext(gpp)] = NAN
        reco[nan_ext(reco)] = NAN

        # if DT GPP is negative, set to -9999
        mask_negative_gpp_dt = (gpp < 0)
        count_negative_gpp_dt = numpy.sum(mask_negative_gpp_dt)
        if count_negative_gpp_dt:
            log.warning('URE checks: Negative values for DT GPP [{c} records]: {s}'.format(c=count_negative_gpp_dt, s=filename))
            gpp[mask_negative_gpp_dt] = NAN

        # if -100 < RECO < 100, set to -9999
        mask_too_low = (reco < -100)
        mask_too_high = (reco > 100)
        count_too_low = numpy.sum(mask_too_low)
        count_too_high = numpy.sum(mask_too_high)
        reco[mask_too_low | mask_too_high] = NAN

        if count_too_low > 0:
            log.warning('URE checks: DT RECO below -100 [{c}]: {s}'.format(c=count_too_low, s=filename))
        if count_too_high > 0:
            log.warning('URE checks: DT RECO above 100 [{c}]: {s}'.format(c=count_too_high, s=filename))

        # if -150 < GPP < 150, set to -9999
        mask_too_low = (gpp < -150)
        mask_too_high = (gpp > 150)
        count_too_low = numpy.sum(mask_too_low)
        count_too_high = numpy.sum(mask_too_high)
        gpp[mask_too_low | mask_too_high] = NAN

        if count_too_low > 0:
            log.warning('URE checks: DT GPP below -150 [{c}]: {s}'.format(c=count_too_low, s=filename))
        if count_too_high > 0:
            log.warning('URE checks: DT GPP above 150 [{c}]: {s}'.format(c=count_too_high, s=filename))

        # if RECO or GPP have gaps, log warnings
        count_reco_nan = numpy.sum(reco < NAN_TEST)
        count_gpp_nan = numpy.sum(gpp < NAN_TEST)

        if count_reco_nan > 0:
            log.warning('URE checks: DT RECO NaN values [{c}]: {s}'.format(c=count_reco_nan, s=filename))
        if count_gpp_nan > 0:
            log.warning('URE checks: DT GPP NaN values [{c}]: {s}'.format(c=count_gpp_nan, s=filename))

        # if DT output is hourly resolution and
        # number of records is for half-hourly,
        # duplicates were added in DT partitioning,
        # and sub-sample of every 2nd record needed;
        if (self.pipeline.record_interval.lower() == 'hr') and (len(reco) > (24 * 366)):
            log.warning('URE checks: hourly DT record with duplicate records, subsampling: {s}'.format(s=filename))
            reco = reco[::2]
            gpp = gpp[::2]

        return reco, gpp


    def convert_files(self):
        '''
        Runs the actual conversion of partitioning outputs into URE inputs
        '''

        # per year/per var input files -- per year output files
        for year in range(self.pipeline.first_year, self.pipeline.last_year + 1):
            # headers for outputs
            headers = ['{s}_{y}_{pd}_{pc}.hdr'.format(s=self.pipeline.siteid, y=year, pd=pd, pc=pc).replace('.', '__') for pd in PROD_TO_COMPARE for pc in PERC_TO_COMPARE]

            # allocate output arrays for year
            gpp_dt_data = get_empty_array_year(year=year, start_end=False, variable_list=headers, record_interval=self.pipeline.record_interval)
            gpp_nt_data = get_empty_array_year(year=year, start_end=False, variable_list=headers, record_interval=self.pipeline.record_interval)
            reco_dt_data = get_empty_array_year(year=year, start_end=False, variable_list=headers, record_interval=self.pipeline.record_interval)
            reco_nt_data = get_empty_array_year(year=year, start_end=False, variable_list=headers, record_interval=self.pipeline.record_interval)

            # populate output filnames for year
            gpp_dt_output_filename = os.path.join(self.prepare_ure_dir, self.DT_GPP_TEMPLATE.format(y=year, s=self.pipeline.siteid))
            gpp_nt_output_filename = os.path.join(self.prepare_ure_dir, self.NT_GPP_TEMPLATE.format(y=year, s=self.pipeline.siteid))
            reco_dt_output_filename = os.path.join(self.prepare_ure_dir, self.DT_RECO_TEMPLATE.format(y=year, s=self.pipeline.siteid))
            reco_nt_output_filename = os.path.join(self.prepare_ure_dir, self.NT_RECO_TEMPLATE.format(y=year, s=self.pipeline.siteid))

            # within year, load and reformat reco and gpp variables for each product and percentile
            for pd in self.prod:
                for pc in self.perc:
                    # variable label format -- keeping original label -- TODO: update when new URE code available)
                    var = '{s}_{y}_{pd}_{pc}.hdr'.format(s=self.pipeline.siteid, y=year, pd=pd, pc=pc).replace('.', '__')
                    generic_filename = self.FILENAME_TEMPLATE.format(prod=pd, perc=pc, s=self.pipeline.siteid, year=year, extra=EXTRA_FILENAME)
                    nt_filename = os.path.join(self.pipeline.nee_partition_nt.nee_partition_nt_dir, generic_filename)

                    # load NT
                    if test_file(tfile=nt_filename, label='ure.run', log_only=True):
                        with open(nt_filename, 'r') as f:
                            header_line = f.readline()
                            input_headers = [i.strip().replace('.', '__').lower() for i in header_line.strip().split(',')]
                        reco_idx, gpp_idx = input_headers.index('reco_2'), input_headers.index('gpp_2'),
                        data = numpy.genfromtxt(fname=nt_filename, names=True, delimiter=',', skip_header=0, usemask=False, usecols=(reco_idx, gpp_idx,))
                        reco_nt_data[var][:], gpp_nt_data[var][:] = self.check_cleanup_nt(reco=data['reco_2'], gpp=data['gpp_2'], filename=nt_filename)

                    # load DT
                    dt_filename = os.path.join(self.pipeline.nee_partition_dt.nee_partition_dt_dir, generic_filename)
                    if test_file(tfile=dt_filename, label='ure.run', log_only=True):
                        with open(dt_filename, 'r') as f:
                            header_line = f.readline()
                            input_headers = [i.strip().replace('.', '__').lower() for i in header_line.strip().split(',')]
                        reco_idx, gpp_idx = input_headers.index('reco_hblr'), input_headers.index('gpp_hblr'),
                        data = numpy.genfromtxt(fname=dt_filename, names=True, delimiter=',', skip_header=0, usemask=False, usecols=(reco_idx, gpp_idx,))
                        reco_dt_data[var][:], gpp_dt_data[var][:] = self.check_cleanup_dt(reco=data['reco_hblr'], gpp=data['gpp_hblr'], filename=dt_filename)

                # save NT
                numpy.savetxt(fname=gpp_nt_output_filename, X=gpp_nt_data, delimiter=',', fmt='%s', header=','.join([i.replace('__', '.') for i in gpp_nt_data.dtype.names]), comments='')
                log.info("Pipeline prepare_ure: saved '{s}'".format(s=gpp_nt_output_filename))
                numpy.savetxt(fname=reco_nt_output_filename, X=reco_nt_data, delimiter=',', fmt='%s', header=','.join([i.replace('__', '.') for i in reco_nt_data.dtype.names]), comments='')
                log.info("Pipeline prepare_ure: saved '{s}'".format(s=reco_nt_output_filename))

                # save DT
                numpy.savetxt(fname=gpp_dt_output_filename, X=gpp_dt_data, delimiter=',', fmt='%s', header=','.join([i.replace('__', '.') for i in gpp_dt_data.dtype.names]), comments='')
                log.info("Pipeline prepare_ure: saved '{s}'".format(s=gpp_dt_output_filename))
                numpy.savetxt(fname=reco_dt_output_filename, X=reco_dt_data, delimiter=',', fmt='%s', header=','.join([i.replace('__', '.') for i in reco_dt_data.dtype.names]), comments='')
                log.info("Pipeline prepare_ure: saved '{s}'".format(s=reco_dt_output_filename))


    def run(self):
        '''
        Executes prepare_ure
        '''
        log.info("Pipeline prepare_ure execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.prepare_ure_dir, label='prepare_ure.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        # execute prepare_ure step
        if self.pipeline.simulation:
            log.info('Simulation only, {s} execution command skipped'.format(s=self.label))
        else:
            self.convert_files()
            self.post_validate()

        log.info("Pipeline prepare_ure execution finished")


class PipelineURE(object):
    '''
    Class to control execution of URE step.
    Executes the Uncertainty and References Estimations/calculations.
    '''
    URE_EXECUTE = True
    URE_EX = "ure"
    URE_DIR = "12_ure"
    _OUTPUT_FILE_PATTERNS = [
        "{s}_DT_GPP_dd.csv",
        "{s}_DT_GPP_hh.csv",
        "{s}_DT_GPP_mm.csv",
        "{s}_DT_GPP_ww.csv",
        "{s}_DT_GPP_yy.csv",
        "{s}_DT_RECO_dd.csv",
        "{s}_DT_RECO_hh.csv",
        "{s}_DT_RECO_mm.csv",
        "{s}_DT_RECO_ww.csv",
        "{s}_DT_RECO_yy.csv",
        "{s}_NT_GPP_dd.csv",
        "{s}_NT_GPP_hh.csv",
        "{s}_NT_GPP_mm.csv",
        "{s}_NT_GPP_ww.csv",
        "{s}_NT_GPP_yy.csv",
        "{s}_NT_RECO_dd.csv",
        "{s}_NT_RECO_hh.csv",
        "{s}_NT_RECO_mm.csv",
        "{s}_NT_RECO_ww.csv",
        "{s}_NT_RECO_yy.csv",
        OUTPUT_LOG_TEMPLATE.format(t='*'), # TODO: change when method implemented
    ]
    _OUTPUT_FILE_PATTERNS_INFO = [
        "{s}_DT_GPP_dd_info.txt",
        "{s}_DT_GPP_hh_info.txt",
        "{s}_DT_GPP_mm_info.txt",
        "{s}_DT_GPP_ww_info.txt",
        "{s}_DT_GPP_yy_info.txt",
        "{s}_DT_RECO_dd_info.txt",
        "{s}_DT_RECO_hh_info.txt",
        "{s}_DT_RECO_mm_info.txt",
        "{s}_DT_RECO_ww_info.txt",
        "{s}_DT_RECO_yy_info.txt",
        "{s}_NT_GPP_dd_info.txt",
        "{s}_NT_GPP_hh_info.txt",
        "{s}_NT_GPP_mm_info.txt",
        "{s}_NT_GPP_ww_info.txt",
        "{s}_NT_GPP_yy_info.txt",
        "{s}_NT_RECO_dd_info.txt",
        "{s}_NT_RECO_hh_info.txt",
        "{s}_NT_RECO_mm_info.txt",
        "{s}_NT_RECO_ww_info.txt",
        "{s}_NT_RECO_yy_info.txt",
    ]
    _OUTPUT_FILE_PATTERNS_MEF = [
        "{s}_DT_GPP_mef_matrix_dd_c_????_????.csv",
        "{s}_DT_GPP_mef_matrix_dd_y_????_????.csv",
        "{s}_DT_GPP_mef_matrix_hh_c_????_????.csv",
        "{s}_DT_GPP_mef_matrix_hh_y_????_????.csv",
        "{s}_DT_GPP_mef_matrix_mm_c_????_????.csv",
        "{s}_DT_GPP_mef_matrix_mm_y_????_????.csv",
        "{s}_DT_GPP_mef_matrix_ww_c_????_????.csv",
        "{s}_DT_GPP_mef_matrix_ww_y_????_????.csv",
        "{s}_DT_GPP_mef_matrix_yy_c_????_????.csv",
        "{s}_DT_GPP_mef_matrix_yy_y_????_????.csv",
        "{s}_DT_RECO_mef_matrix_dd_c_????_????.csv",
        "{s}_DT_RECO_mef_matrix_dd_y_????_????.csv",
        "{s}_DT_RECO_mef_matrix_hh_c_????_????.csv",
        "{s}_DT_RECO_mef_matrix_hh_y_????_????.csv",
        "{s}_DT_RECO_mef_matrix_mm_c_????_????.csv",
        "{s}_DT_RECO_mef_matrix_mm_y_????_????.csv",
        "{s}_DT_RECO_mef_matrix_ww_c_????_????.csv",
        "{s}_DT_RECO_mef_matrix_ww_y_????_????.csv",
        "{s}_DT_RECO_mef_matrix_yy_c_????_????.csv",
        "{s}_DT_RECO_mef_matrix_yy_y_????_????.csv",
        "{s}_NT_GPP_mef_matrix_dd_c_????_????.csv",
        "{s}_NT_GPP_mef_matrix_dd_y_????_????.csv",
        "{s}_NT_GPP_mef_matrix_hh_c_????_????.csv",
        "{s}_NT_GPP_mef_matrix_hh_y_????_????.csv",
        "{s}_NT_GPP_mef_matrix_mm_c_????_????.csv",
        "{s}_NT_GPP_mef_matrix_mm_y_????_????.csv",
        "{s}_NT_GPP_mef_matrix_ww_c_????_????.csv",
        "{s}_NT_GPP_mef_matrix_ww_y_????_????.csv",
        "{s}_NT_GPP_mef_matrix_yy_c_????_????.csv",
        "{s}_NT_GPP_mef_matrix_yy_y_????_????.csv",
        "{s}_NT_RECO_mef_matrix_dd_c_????_????.csv",
        "{s}_NT_RECO_mef_matrix_dd_y_????_????.csv",
        "{s}_NT_RECO_mef_matrix_hh_c_????_????.csv",
        "{s}_NT_RECO_mef_matrix_hh_y_????_????.csv",
        "{s}_NT_RECO_mef_matrix_mm_c_????_????.csv",
        "{s}_NT_RECO_mef_matrix_mm_y_????_????.csv",
        "{s}_NT_RECO_mef_matrix_ww_c_????_????.csv",
        "{s}_NT_RECO_mef_matrix_ww_y_????_????.csv",
        "{s}_NT_RECO_mef_matrix_yy_c_????_????.csv",
        "{s}_NT_RECO_mef_matrix_yy_y_????_????.csv",
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of ure step
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.label = 'ure'
        self.execute = self.pipeline.configs.get('ure_execute', self.URE_EXECUTE)
        self.ure_ex = self.pipeline.configs.get('ure_ex', os.path.join(self.pipeline.tool_dir, self.URE_EX))
        self.ure_dir = self.pipeline.configs.get('ure_dir', os.path.join(self.pipeline.data_dir, self.URE_DIR))
        self.ure_dir_fmt = self.ure_dir + os.sep
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.output_file_patterns_info = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_INFO]
        self.output_file_patterns_mef = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS_MEF]
        self.input_prepare_ure_dir = self.pipeline.prepare_ure.prepare_ure_dir_fmt
        self.output_log = os.path.join(self.ure_dir, 'report_{t}.txt'.format(t=self.pipeline.run_id))
        self.cmd_txt = 'cd "{o}" {cmd_sep} {c} -input_path={i} -output_path={o} > "{log}"'
        self.cmd = self.cmd_txt.format(c=self.ure_ex, i=self.input_prepare_ure_dir, o=self.ure_dir_fmt, log=self.output_log, cmd_sep=CMD_SEP, cp=COPY)

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check executable
        test_file(tfile=self.ure_ex, label='ure.pre_validate')

        # check dependency steps
        self.pipeline.prepare_ure.post_validate()

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.ure_dir, label='ure.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.ure_dir, label='ure.post_validate')
        test_file_list(file_list=self.output_file_patterns_info, tdir=self.ure_dir, label='ure.post_validate', log_only=True)
        test_file_list(file_list=self.output_file_patterns_mef, tdir=self.ure_dir, label='ure.post_validate', log_only=True)

    def run(self):
        '''
        Executes ure
        '''
        log.info('Pipeline {s} execution started'.format(s=self.label))
        self.pre_validate()

        create_replace_dir(tdir=self.ure_dir, label='{s}.run'.format(s=self.label), suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info('Execution command: {c}'.format(c=self.cmd))
        if self.pipeline.simulation:
            log.info('Simulation only, {s} execution command skipped'.format(s=self.label))
        else:
            run_command(self.cmd)
            self.post_validate()
        log.info('Pipeline {s} execution finished'.format(s=self.label))


class PipelineFLUXNET(object):
    '''
    Step to generate FLUXNET data product
    '''
    FLUXNET2015_EXECUTE = True
    FLUXNET2015_DIR = '99_fluxnet2015'
    FLUXNET2015_SITE_PLOTS = True
    FLUXNET2015_FIRST_T1 = None
    FLUXNET2015_LAST_T1 = None
    FLUXNET2015_FIRST_T2 = None
    FLUXNET2015_LAST_T2 = None
    FLUXNET2015_VERSION_PROCESSING = 3
    FLUXNET2015_VERSION_DATA = 1
    _OUTPUT_FILE_PATTERNS = [
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_AUXMETEO_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_AUXNEE_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_FULLSET_DD_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_FULLSET_HH_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_FULLSET_MM_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_FULLSET_WW_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_FULLSET_YY_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_SUBSET_DD_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_SUBSET_HH_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_SUBSET_MM_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_SUBSET_WW_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_SUBSET_YY_????-????_*-*.csv",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_FULLSET_????-????_*-*.zip",
        MODE_ISSUER + "_{s}_" + MODE_PRODUCT + "_SUBSET_????-????_*-*.zip",
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of step to generate
        FLUXNET2015 data product
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('fluxnet2015_execute', self.FLUXNET2015_EXECUTE)
        self.fluxnet2015_dir = self.pipeline.configs.get('fluxnet2015_dir', os.path.join(self.pipeline.data_dir, self.FLUXNET2015_DIR))
        self.fluxnet2015_site_plots = self.pipeline.configs.get('fluxnet2015_site_plots', self.FLUXNET2015_SITE_PLOTS)
        self.fluxnet2015_first_t1 = self.pipeline.configs.get('fluxnet2015_first_t1', self.FLUXNET2015_FIRST_T1)
        self.fluxnet2015_last_t1 = self.pipeline.configs.get('fluxnet2015_last_t1', self.FLUXNET2015_LAST_T1)
        self.fluxnet2015_first_t2 = self.pipeline.configs.get('fluxnet2015_first_t2', self.FLUXNET2015_FIRST_T2)
        self.fluxnet2015_last_t2 = self.pipeline.configs.get('fluxnet2015_last_t2', self.FLUXNET2015_LAST_T2)
        self.fluxnet2015_version_processing = self.pipeline.configs.get('fluxnet2015_version_processing', self.FLUXNET2015_VERSION_PROCESSING)
        self.fluxnet2015_version_data = self.pipeline.configs.get('fluxnet2015_version_data', self.FLUXNET2015_VERSION_DATA)
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.csv_manifest_entries = None
        self.zip_manifest_entries = None
        self.csv_manifest_lines = [CSVMANIFEST_HEADER, ]
        self.zip_manifest_lines = [ZIPMANIFEST_HEADER, ]
        self.csv_manifest_file = os.path.join(self.fluxnet2015_dir, OUTPUT_LOG_TEMPLATE.format(t='CSV_' + self.pipeline.run_id)[:-4] + '.csv')
        self.zip_manifest_file = os.path.join(self.fluxnet2015_dir, OUTPUT_LOG_TEMPLATE.format(t='ZIP_' + self.pipeline.run_id)[:-4] + '.csv')

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check dependency steps
        self.pipeline.qc_visual.post_validate()
        self.pipeline.meteo_proc.post_validate()
        self.pipeline.nee_proc.post_validate()
        self.pipeline.energy_proc.post_validate()
        self.pipeline.ure.post_validate()

        # check minimal tier information
        if self.fluxnet2015_first_t1 is None:
            msg = "PipelineFLUXNET2015: First Tier1 site year not provided or invalid: '{v}'".format(v=self.fluxnet2015_first_t1)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        if self.fluxnet2015_last_t1 is None:
            msg = "PipelineFLUXNET2015: Last Tier1 site year not provided or invalid: '{v}'".format(v=self.fluxnet2015_last_t1)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.fluxnet2015_dir, label='fluxnet2015.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.fluxnet2015_dir, label='fluxnet2015.post_validate')

        # check all variables present
        log.info("Checking FLUXNET2015 FULLSET data product files for variables ({s})".format(s=self.pipeline.siteid))
        all_present = True
        for filename_pattern in self.output_file_patterns:
            if ('FULLSET' in filename_pattern) and ('.zip' not in filename_pattern.lower()):
                matches = fnmatch.filter(os.listdir(self.fluxnet2015_dir), filename_pattern)
                matches_alt = fnmatch.filter(os.listdir(self.fluxnet2015_dir), filename_pattern.replace('_HH_', '_HR_'))
                for filename in matches + matches_alt:
                    all_present = check_headers_fluxnet2015(filename=os.path.join(self.fluxnet2015_dir, filename))
        if not all_present:
            log.critical("Missing variables in FLUXNET2015 FULLSET output for site {s}".format(s=self.pipeline.siteid))

    def run(self):
        '''
        Executes fluxnet2015
        '''

        log.info("Pipeline fluxnet2015 execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.fluxnet2015_dir, label='fluxnet2015.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info("Execution command oneflux.pipeline.site_data_product.run_site")
        if self.pipeline.simulation:
            log.info("Simulation only, fluxnet2015 execution command skipped")
        else:
            self.csv_manifest_entries, self.zip_manifest_entries = run_site(siteid=self.pipeline.siteid,
                                                                            sitedir=os.path.basename(self.pipeline.data_dir),
                                                                            first_t1=self.fluxnet2015_first_t1,
                                                                            last_t1=self.fluxnet2015_last_t1,
                                                                            version_processing=self.fluxnet2015_version_processing,
                                                                            version_data=self.fluxnet2015_version_data,
                                                                            pipeline=self.pipeline,
                                                                            era_first_timestamp_start=self.pipeline.era_first_timestamp_start,
                                                                            era_last_timestamp_start=self.pipeline.era_last_timestamp_start)
            if self.fluxnet2015_site_plots:
                gen_site_plots(siteid=self.pipeline.siteid,
                               sitedir=os.path.basename(self.pipeline.data_dir),
                               version_data=self.fluxnet2015_version_data,
                               version_processing=self.fluxnet2015_version_processing,
                               pipeline=self.pipeline)

            # write manifest entries for site
            for entry in self.csv_manifest_entries:
                self.csv_manifest_lines.append(','.join(entry) + '\n')
            for entry in self.zip_manifest_entries:
                self.zip_manifest_lines.append(','.join(entry) + '\n')
            log.debug("Pipeline fluxnet2015 writing site CSV manifest file: {f}".format(f=self.csv_manifest_file))
            with open(self.csv_manifest_file, 'w') as f:
                f.writelines(self.csv_manifest_lines)
            log.debug("Pipeline fluxnet2015 writing site ZIP manifest file: {f}".format(f=self.zip_manifest_file))
            with open(self.zip_manifest_file, 'w') as f:
                f.writelines(self.zip_manifest_lines)

            self.post_validate()

        log.info("Pipeline fluxnet2015 execution finished")


class PipelineFLUXNET2015(object):
    '''
    Step to generate FLUXNET2015 data product
    '''
    FLUXNET2015_EXECUTE = True
    FLUXNET2015_DIR = '99_fluxnet2015'
    FLUXNET2015_SITE_PLOTS = True
    FLUXNET2015_FIRST_T1 = None
    FLUXNET2015_LAST_T1 = None
    FLUXNET2015_FIRST_T2 = None
    FLUXNET2015_LAST_T2 = None
    FLUXNET2015_VERSION_PROCESSING = 3
    FLUXNET2015_VERSION_DATA = 1
    _OUTPUT_FILE_PATTERNS = [
        "FLX_{s}_FLUXNET2015_AUXMETEO_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_AUXNEE_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_FULLSET_DD_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_FULLSET_HH_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_FULLSET_MM_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_FULLSET_WW_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_FULLSET_YY_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_SUBSET_DD_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_SUBSET_HH_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_SUBSET_MM_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_SUBSET_WW_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_SUBSET_YY_????-????_*-*.csv",
        "FLX_{s}_FLUXNET2015_FULLSET_????-????_*-*.zip",
        "FLX_{s}_FLUXNET2015_SUBSET_????-????_*-*.zip",
    ]

    def __init__(self, pipeline):
        '''
        Initializes parameters for execution of step to generate
        FLUXNET2015 data product
        
        :param pipeline: ONEFlux Pipeline object driving the execution
        :type pipeline: Pipeline
        '''
        self.pipeline = pipeline
        self.execute = self.pipeline.configs.get('fluxnet2015_execute', self.FLUXNET2015_EXECUTE)
        self.fluxnet2015_dir = self.pipeline.configs.get('fluxnet2015_dir', os.path.join(self.pipeline.data_dir, self.FLUXNET2015_DIR))
        self.fluxnet2015_site_plots = self.pipeline.configs.get('fluxnet2015_site_plots', self.FLUXNET2015_SITE_PLOTS)
        self.fluxnet2015_first_t1 = self.pipeline.configs.get('fluxnet2015_first_t1', self.FLUXNET2015_FIRST_T1)
        self.fluxnet2015_last_t1 = self.pipeline.configs.get('fluxnet2015_last_t1', self.FLUXNET2015_LAST_T1)
        self.fluxnet2015_first_t2 = self.pipeline.configs.get('fluxnet2015_first_t2', self.FLUXNET2015_FIRST_T2)
        self.fluxnet2015_last_t2 = self.pipeline.configs.get('fluxnet2015_last_t2', self.FLUXNET2015_LAST_T2)
        self.fluxnet2015_version_processing = self.pipeline.configs.get('fluxnet2015_version_processing', self.FLUXNET2015_VERSION_PROCESSING)
        self.fluxnet2015_version_data = self.pipeline.configs.get('fluxnet2015_version_data', self.FLUXNET2015_VERSION_DATA)
        self.output_file_patterns = [i.format(s=self.pipeline.siteid) for i in self._OUTPUT_FILE_PATTERNS]
        self.csv_manifest_entries = None
        self.zip_manifest_entries = None
        self.csv_manifest_lines = [CSVMANIFEST_HEADER, ]
        self.zip_manifest_lines = [ZIPMANIFEST_HEADER, ]
        self.csv_manifest_file = os.path.join(self.fluxnet2015_dir, OUTPUT_LOG_TEMPLATE.format(t='CSV_' + self.pipeline.run_id)[:-4] + '.csv')
        self.zip_manifest_file = os.path.join(self.fluxnet2015_dir, OUTPUT_LOG_TEMPLATE.format(t='ZIP_' + self.pipeline.run_id)[:-4] + '.csv')

    def pre_validate(self):
        '''
        Validate pre-execution requirements
        '''
        # check dependency steps
        self.pipeline.qc_visual.post_validate()
        self.pipeline.meteo_proc.post_validate()
        self.pipeline.nee_proc.post_validate()
        self.pipeline.energy_proc.post_validate()
        self.pipeline.ure.post_validate()

        # check minimal tier information
        if self.fluxnet2015_first_t1 is None:
            msg = "PipelineFLUXNET2015: First Tier1 site year not provided or invalid: '{v}'".format(v=self.fluxnet2015_first_t1)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)
        if self.fluxnet2015_last_t1 is None:
            msg = "PipelineFLUXNET2015: Last Tier1 site year not provided or invalid: '{v}'".format(v=self.fluxnet2015_last_t1)
            log.critical(msg)
            raise ONEFluxPipelineError(msg)

    def post_validate(self):
        '''
        Validate post-execution results
        '''
        # check output directory
        test_dir(tdir=self.fluxnet2015_dir, label='fluxnet2015.post_validate')

        # check output files and result report (log)
        test_file_list(file_list=self.output_file_patterns, tdir=self.fluxnet2015_dir, label='fluxnet2015.post_validate')

        # check all variables present
        log.info("Checking FLUXNET2015 FULLSET data product files for variables ({s})".format(s=self.pipeline.siteid))
        all_present = True
        for filename_pattern in self.output_file_patterns:
            if ('FULLSET' in filename_pattern) and ('.zip' not in filename_pattern.lower()):
                matches = fnmatch.filter(os.listdir(self.fluxnet2015_dir), filename_pattern)
                matches_alt = fnmatch.filter(os.listdir(self.fluxnet2015_dir), filename_pattern.replace('_HH_', '_HR_'))
                for filename in matches + matches_alt:
                    all_present = check_headers_fluxnet2015(filename=os.path.join(self.fluxnet2015_dir, filename))
        if not all_present:
            log.critical("Missing variables in FLUXNET2015 FULLSET output for site {s}".format(s=self.pipeline.siteid))

    def run(self):
        '''
        Executes fluxnet2015
        '''

        log.info("Pipeline fluxnet2015 execution started")
        self.pre_validate()

        create_replace_dir(tdir=self.fluxnet2015_dir, label='fluxnet2015.run', suffix=self.pipeline.run_id, simulation=self.pipeline.simulation)

        log.info("Execution command oneflux.pipeline.site_data_product.run_site")
        if self.pipeline.simulation:
            log.info("Simulation only, fluxnet2015 execution command skipped")
        else:
            self.csv_manifest_entries, self.zip_manifest_entries = run_site(siteid=self.pipeline.siteid,
                                                                            sitedir=os.path.basename(self.pipeline.data_dir),
                                                                            first_t1=self.fluxnet2015_first_t1,
                                                                            last_t1=self.fluxnet2015_last_t1,
                                                                            version_processing=self.fluxnet2015_version_processing,
                                                                            version_data=self.fluxnet2015_version_data,
                                                                            pipeline=self.pipeline,
                                                                            era_first_timestamp_start=self.pipeline.era_first_timestamp_start,
                                                                            era_last_timestamp_start=self.pipeline.era_last_timestamp_start)
            if self.fluxnet2015_site_plots:
                gen_site_plots(siteid=self.pipeline.siteid,
                               sitedir=os.path.basename(self.pipeline.data_dir),
                               version_data=self.fluxnet2015_version_data,
                               version_processing=self.fluxnet2015_version_processing,
                               pipeline=self.pipeline)

            # write manifest entries for site
            for entry in self.csv_manifest_entries:
                self.csv_manifest_lines.append(','.join(entry) + '\n')
            for entry in self.zip_manifest_entries:
                self.zip_manifest_lines.append(','.join(entry) + '\n')
            log.debug("Pipeline fluxnet2015 writing site CSV manifest file: {f}".format(f=self.csv_manifest_file))
            with open(self.csv_manifest_file, 'w') as f:
                f.writelines(self.csv_manifest_lines)
            log.debug("Pipeline fluxnet2015 writing site ZIP manifest file: {f}".format(f=self.zip_manifest_file))
            with open(self.zip_manifest_file, 'w') as f:
                f.writelines(self.zip_manifest_lines)

            self.post_validate()

        log.info("Pipeline fluxnet2015 execution finished")
