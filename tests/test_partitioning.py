import oneflux.partition.nighttime
import oneflux.partition.library # optimisation related functions
import oneflux.partition.ecogeo
from oneflux.partition.library import QC_AUTO_DIR, METEO_PROC_DIR, NEE_PROC_DIR, NT_OUTPUT_DIR, HEADER_SEPARATOR, EXTRA_FILENAME, NT_STR
import os

from distutils.dir_util import copy_tree

# LIBRARY
# looks like a good candidate for unit testing - lots of maths functions:
# get_first_last_ts
# cov2cor
# root_mean_sq_error
# least_squares () - calls scipy function 
# check_parameters (checks values within given threshold)

# loading data function:
# load outputs

# Less easy:
# create_data_structures - very long function
#  nlinlts1 (non-linear least-squares driver function)

# function is used in daytime at present - so ignore for now
# array consisting of 6 elements

# this function isn't actually used much
def test_check_parameters():
    from oneflux.partition.library import check_parameter
   
    p1 = [0, 0, 0, 50, 0, 0]
    
    p2 = [0.2199999, 250, 0, 0, 0, 0]

# flux partition in nighttime.py is a huge function (250+ lines)

def test_load_output():
    from oneflux.partition.library import load_output
    datadir = "./datadir/test_input"
    sitedir = "US-ARc_sample_input"
    siteid = "US-ARc"
    sitedir_full = os.path.join(datadir, sitedir)
    meteo_proc_dir = os.path.join(sitedir_full, METEO_PROC_DIR)
    meteo_proc_f = os.path.join(meteo_proc_dir, '{s}_meteo_hh.csv'.format(s=siteid))
    whole_dataset_meteo, headers_meteo, timestamp_list_meteo, year_list_meteo = load_output(meteo_proc_f)
    
    
    
# create dataset for step 10
def setup_data():
    try:
        os.mkdir('tests/data/step_10')
    except OSError as e:
        if e.errno == errno.EEXIST:
            print("dir exists")
    
    copy_tree('datadir/test_input/', 'tests/data/step_10')
   
    # copy data from assumed output as input to suite of partitioning tests 
    copy_tree('datadir/test_output/US-ARc_sample_output/07_meteo_proc/', \
        'tests/data/step_10/US-ARc_sample_input/07_meteo_proc/')
    copy_tree('datadir/test_output/US-ARc_sample_output/08_nee_proc/', \
        'tests/data/step_10/US-ARc_sample_input/08_nee_proc/')
    copy_tree('datadir/test_output/US-ARc_sample_output/02_qc_auto/', \
        'tests/data/step_10/US-ARc_sample_input/02_qc_auto/')
    


def test_create_data_structures():
    return True
    ustar_type = ['c'] 
    create_data_structures(ustar_type=ustar_type, whole_dataset_nee=whole_dataset_nee, whole_dataset_meteo=whole_dataset_meteo)
    pass

def test_compu():
    from oneflux.partition.nighttime import compu
    from oneflux.partition.nighttime import load_output
    from oneflux.partition.nighttime import create_data_structures
    from oneflux.partition.compu import compu_qcnee_filter
    ustar_type = ['y']
   

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