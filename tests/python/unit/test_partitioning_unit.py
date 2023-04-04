import pytest
import shutil
import oneflux.partition.nighttime
import oneflux.partition.library # optimisation related functions
import oneflux.partition.ecogeo
from oneflux.partition.library import QC_AUTO_DIR, METEO_PROC_DIR, NEE_PROC_DIR, NT_OUTPUT_DIR, HEADER_SEPARATOR, EXTRA_FILENAME, NT_STR
import os, errno

from distutils.dir_util import copy_tree

def test_check_parameters():
    # from oneflux.partition.library import check_parameter
   
    p1 = [0, 0, 0, 50, 0, 0]
    
    p2 = [0.2199999, 250, 0, 0, 0, 0]
    return True

# create dataset for step 10
# TODO: excludes extracting and copying data into correct location. 
@pytest.fixture
def setup_data():
    try:
        os.mkdir('tests/data/step_10')
    except OSError as e:
        if e.errno == errno.EEXIST:
            print("dir exists")
    
    copy_tree('tests/data/test_input/', 'tests/data/step_10')
   
    # copy data from assumed output as input to suite of partitioning tests 
    copy_tree('tests/data/test_output/US-ARc_sample_output/07_meteo_proc/', \
        'tests/data/step_10/US-ARc_sample_input/07_meteo_proc/')
    copy_tree('tests/data/test_output/US-ARc_sample_output/08_nee_proc/', \
        'tests/data/step_10/US-ARc_sample_input/08_nee_proc/')
    copy_tree('tests/data/test_output/US-ARc_sample_output/02_qc_auto/', \
        'tests/data/step_10/US-ARc_sample_input/02_qc_auto/')
    return

# flux partition in nighttime.py is a huge function (250+ lines)
# use module scope to do this once (including downloading and extracting the data)
def test_load_output(setup_data):
    from oneflux.partition.library import load_output
    datadir = "./tests/data/step_10/"
    sitedir = "US-ARc_sample_input"
    siteid = "US-ARc"
    sitedir_full = os.path.join(datadir, sitedir)
    meteo_proc_dir = os.path.join(sitedir_full, METEO_PROC_DIR)
    meteo_proc_f = os.path.join(meteo_proc_dir, '{s}_meteo_hh.csv'.format(s=siteid))
    whole_dataset_meteo, headers_meteo, timestamp_list_meteo, year_list_meteo = load_output(meteo_proc_f)
   
    # TIMESTAMP_START,TIMESTAMP_END,DTIME,TA_f,TA_fqc,TA_ERA,TA_m,TA_mqc,SW_IN_pot,SW_IN_f,SW_IN_fqc,SW_IN_ERA,SW_IN_m,SW_IN_mqc,LW_IN_f,LW_IN_fqc,LW_IN_ERA,LW_IN_m,LW_IN_mqc,LW_IN_calc,LW_IN_calc_qc,LW_IN_calc_ERA,LW_IN_calc_m,LW_IN_calc_mqc,VPD_f,VPD_fqc,VPD_ERA,VPD_m,VPD_mqc,PA,PA_ERA,PA_m,PA_mqc,P,P_ERA,P_m,P_mqc,WS,WS_ERA,WS_m,WS_mqc,CO2_f,CO2_fqc,TS_1_f,TS_1_fqc,SWC_1_f,SWC_1_fqc
    # 198901010000,198901010030,1.02083,-9999.000,-9999,0.316,0.316,2,0,-9999.000,-9999,0.000,0.000,2,-9999.000,-9999,246.830,246.830,2,-9999.000,-9999,253.002,253.002,2,-9999.000,-9999,0.000,0.000,2,-9999.000,96.420,96.420,2,-9999.000,0.000,0.000,2,-9999.000,2.879,2.879,2,-9999.000,-9999,-9999.000,-9999,-9999.000,-9999
    
    print(dir(whole_dataset_meteo))
    # shutil.rmtree('./tests/integration/step_10')

    
def test_least_squares():
    from oneflux.partition.nighttime import least_squares
    pass

def test_create_data_structures():
    return True
    ustar_type = ['c'] 
    create_data_structures(ustar_type=ustar_type, whole_dataset_nee=whole_dataset_nee, whole_dataset_meteo=whole_dataset_meteo)
    pass


def test_compu(setup_data):
    return True
    from oneflux.partition.nighttime import compu
    from oneflux.partition.nighttime import load_output
    from oneflux.partition.nighttime import create_data_structures
    from oneflux.partition.compu import compu_qcnee_filter
    ustar_type = ['y']
   

    sitedir_full = os.path.join(datadir, sitedir)
    meteo_proc_dir = os.path.join(sitedir_full, METEO_PROC_DIR)
    meteo_proc_f = os.path.join(meteo_proc_dir, '{s}_meteo_hh.csv'.format(s=siteid))
    nee_proc_percentiles_f = os.path.join(nee_proc_dir, '{s}_NEE_percentiles_{u}_hh.csv'.format(s=siteid, u=ustar_type))
   
    whole_dataset_meteo, headers_meteo, timestamp_list_meteo, year_list_meteo = load_output(meteo_proc_f)
    whole_dataset_nee, headers_nee, timestamp_list_nee, year_list_nee = load_output(nee_proc_percentiles_f)
    
    data = working_year_data = create_data_structures(ustar_type=ustar_type, whole_dataset_nee=whole_dataset_nee, whole_dataset_meteo=whole_dataset_meteo)
    func = compu_qcnee_filter
    columns = None
    parameters = None
    skip_if_present = False
    no_missing = False
    new_ = False
    
    compu(data, func, columns, parameters, skip_if_present, no_missing, new_)

def test_get_first_last_ts():
    pass

# partitioning_nt -> flux_partition -> nlinlts -> 
