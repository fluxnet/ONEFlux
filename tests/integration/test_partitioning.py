import oneflux.tools.partition_nt

# not sure about the existence of this test. Not really a unit test
@pytest.fixture
def get_data():
    pass

def equal_csv(csv_1, csv_2):
    with open(csv_1, 'r') as t1, open(csv_2, 'r') as t2:
        fileone = t1.readlines()
        filetwo = t2.readlines()
        for line in filetwo:
            if line not in fileone:
                return False
   
    
# TODO: deal with fixtures for running nt_test
# step 10
def test_run_partition_nt():
    datadir = "./datadir/test_input"
    data_output = "./datadir/test_output"
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
    
    # log.info(nee_y_files)
    # log.info(compare_y_files)
    for f, b in zip(nee_y_files, ref_y_files):
        if not equal_csv(f, b):
            return False

    # glob the files with this root
    # for file in glob.glob(nee_y_files):
    #     print(file)
    #     log.info(file)
    #     if not equal_csv(file, )
    # with open('saved/nee_y_1.25_US-ARc_2005.csv', 'r') as t1, open(nee_y, 'r') as t2:

if __name__ == '__main__':
    raise ONEFluxError('Not executable')
