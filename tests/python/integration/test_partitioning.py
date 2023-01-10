import pytest
import os, glob
import errno
import shutil
import urllib
from distutils.dir_util import copy_tree
import logging
import time

_log = logging.getLogger(__name__)

@pytest.fixture(scope="module")
def get_data():
    '''
    Utilising python to obtain sample test data. Function currently unused. 
    as a fixture in this class. 
    '''
    from zipfile import ZipFile
    urllib.urlopen('ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_output.zip') 
    urllib.urlopen('ftp://ftp.fluxdata.org/.ameriflux_downloads/.test/US-ARc_sample_input.zip') 
  
    input_zip = "US-ARc_sample_input.zip"
    output_zip = "US-ARc_sample_output.zip"
    
    with ZipFile(input_zip) as zi, ZipFile(output_zip) as zo:
        zi.extractall(path='tests/data/test_input')
        zo.extractall(path='tests/data/test_output')

def equal_csv(csv_1, csv_2):
    '''
    Check equality of two csv files.
    '''
    _log.info("Check csv equality")
    start = time.time()
    with open(csv_1, 'r') as t1, open(csv_2, 'r') as t2:
        fileone = t1.readlines()
        filetwo = t2.readlines()
        for line in filetwo:
            if line not in fileone:
                return False

        _log.info("total time", start - time.time())

        return True


@pytest.fixture
def setup_data():
    '''
    Set up input data for run_partition_nt test. 
    
    Create data directory for tests './tests/integration/step10' and copy 
    data from expected output ('./datadir/test_output/US-ARc_sample_output')
    to this directory.
    '''
    try:
        os.mkdir('tests/integration/data/step_10')
    except OSError as e:
        if e.errno == errno.EEXIST:
            print("directory exists")
            
    testdata = 'tests/python/integration/input/step_10/US-ARc_sample_input'
    
    copy_tree('tests/data/test_input/', testdata)

    refoutdir = 'tests/data/test_output/US-ARc_sample_output'

    copy_tree(os.path.join(refoutdir, '07_meteo_proc'), \
        os.path.join(testdata, '07_meteo_proc'))
    copy_tree(os.path.join(refoutdir, '08_nee_proc'), \
        os.path.join(testdata, '08_nee_proc/'))
    copy_tree(os.path.join(refoutdir, '02_qc_auto'), \
        os.path.join(testdata, '02_qc_auto/'))
    
    
def test_run_partition_nt(setup_data):
    '''
    Run partition_nt on single percentile.
    '''
    datadir = "./tests/python/integration/input/step_10/"
    refoutdir = "./tests/data/test_output/"
    siteid = "US-ARc"
    sitedir = "US-ARc_sample_input"
    years = [2005] # years = [2005, 2006]
    # PROD_TO_COMPARE = ['c', 'y']
    PROD_TO_COMPARE = ['y',]
    # PERC_TO_COMPARE = ['1.25', '3.75',]
    PERC_TO_COMPARE = ['1.25',]
    
    from oneflux.tools.partition_nt import remove_previous_run, run_python
    remove_previous_run(datadir=datadir, siteid=siteid, sitedir=sitedir, python=True, 
                        prod_to_compare=PROD_TO_COMPARE, perc_to_compare=PERC_TO_COMPARE,
                        years_to_compare=years)

    run_python(datadir=datadir, siteid=siteid, sitedir=sitedir, prod_to_compare=PROD_TO_COMPARE,
               perc_to_compare=PERC_TO_COMPARE, years_to_compare=years)
    
    # check whether csv of "output" is same as csv of reference

    # the generated output is actually in the "input" directory.
    rootdir = os.path.join(datadir, sitedir, "10_nee_partition_nt")
    nee_y_files = glob.glob(os.path.join(rootdir, "nee_y_1.25_US-ARc_2005*"))
    nee_y_files = filter(lambda x: not x.endswith('_orig.csv'), nee_y_files)
    
    # paths to the "reference" output data
    refoutdir = os.path.join(refoutdir, "US-ARc_sample_output", "10_nee_partition_nt")
    ref_nee_y_files = glob.glob(os.path.join(refoutdir, "nee_y_1.25_US-ARc_2005*"))
   
    assert len(nee_y_files) == len(ref_nee_y_files)
    retval = True 
    for f, b in zip(nee_y_files, ref_nee_y_files):
        print(f, b)
        assert equal_csv(f, b) == True

    # clean up data. 
    # shutil.rmtree(datadir)
