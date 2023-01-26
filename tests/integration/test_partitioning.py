import pytest
import os, glob
import errno
import shutil
from distutils.dir_util import copy_tree


@pytest.fixture
def get_data():
    urllib.request.urlretrieve('ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_output.zip') 
    urllib.request.urlretrieve('ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_input.zip') 
    pass

def equal_csv(csv_1, csv_2):
    with open(csv_1, 'r') as t1, open(csv_2, 'r') as t2:
        fileone = t1.readlines()
        filetwo = t2.readlines()
        for line in filetwo:
            if line not in fileone:
                return False


# create dataset for step 10
def setup_data():
    try:
        os.mkdir('tests/integration/step_10')
    except OSError as e:
        if e.errno == errno.EEXIST:
            print("dir exists")
    
    copy_tree('datadir/test_input/', 'tests/integration/step_10')
    copy_tree('datadir/test_output/US-ARc_sample_output/07_meteo_proc/', \
        'tests/integration/step_10/US-ARc_sample_input/07_meteo_proc/')
    copy_tree('datadir/test_output/US-ARc_sample_output/08_nee_proc/', \
        'tests/integration/step_10/US-ARc_sample_input/08_nee_proc/')
    copy_tree('datadir/test_output/US-ARc_sample_output/02_qc_auto/', \
        'tests/integration/step_10/US-ARc_sample_input/02_qc_auto/')
    
    
# step 10
# TODO: deal with fixtures for running nt_test
# TODO: Does not work without output of step 7 - run step 7 first 
def test_run_partition_nt():
    from oneflux.tools.partition_nt import remove_previous_run, run_python
    setup_data()
    datadir = "./tests/integration/step_10/"
    data_output = "./tests/integration/step_10/test_output"
    siteid = "US-ARc"
    sitedir = "US-ARc_sample_input"
    years = [2005] # years = [2005, 2006]
    PROD_TO_COMPARE = ['c', 'y']
    # PERC_TO_COMPARE = ['1.25', '3.75',]
    PERC_TO_COMPARE = ['1.25',]
    remove_previous_run(datadir=datadir, siteid=siteid, sitedir=sitedir, python=True, 
                        prod_to_compare=PROD_TO_COMPARE, perc_to_compare=PERC_TO_COMPARE,
                        years_to_compare=years)

    run_python(datadir=datadir, siteid=siteid, sitedir=sitedir, prod_to_compare=PROD_TO_COMPARE,
               perc_to_compare=PERC_TO_COMPARE, years_to_compare=years)
    
    # now do simple check of output 
    rootdir = os.path.join(datadir, sitedir, "10_nee_partition_nt")
    nee_y_files = glob.glob(os.path.join(rootdir, "nee_y_1.25_US-ARc_2005*"))
    ref_output = os.path.join(data_output, sitedir, "10_nee_partition_nt")
    ref_y_files = glob.glob(os.path.join(ref_output, "nee_y_1.25_US-ARc_2005*"))
   
    retval = True 
    # log.info(nee_y_files)
    # log.info(compare_y_files)
    for f, b in zip(nee_y_files, ref_y_files):
        if not equal_csv(f, b):
            retval = False

    # clean up data
    shutil.rmtree('./tests/integration/step_10')
    
    return retval 
    # glob the files with this root
    # for file in glob.glob(nee_y_files):
    #     print(file)
    #     log.info(file)
    #     if not equal_csv(file, )
    # with open('saved/nee_y_1.25_US-ARc_2005.csv', 'r') as t1, open(nee_y, 'r') as t2:
