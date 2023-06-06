/*
	tMeteo_Proc-dataset.c 

	Test the functionality of the dataset.c file. Part of the meteo_proc pipeline. 

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy
*/

#include "utest_oneflux.h"
#include "../../oneflux_steps/common/common.c"
#include "../../oneflux_steps/meteo_proc/src/dataset.c"

/* dataset.c  needs some external variables */
char *qc_auto_files_path = NULL;	/* mandatory */
char *era_files_path = NULL;		/* mandatory */
char *output_files_path = NULL;		/* mandatory */

/*
	test the valid_era_filename function by providing examples of passing and failing inputs.
*/
UTEST(test_is_valid_era_filename, 1)
{
	char* filename;
	
	// test the empty string check works - will return false
	filename = "";
	ASSERT_MSG(!is_valid_era_filename(filename), "Check empty string", filename);
	
	// correct string will return True
	filename = "US-ARc_2009.csv";
	ASSERT_MSG(is_valid_era_filename(filename), "Check that function detects correct string", filename);
	
	// test that year check returns false
	filename = "US-ARc_YYYY.csv";
	ASSERT_MSG(!is_valid_era_filename(filename), "Check that function correctly tests for absent digits", filename);
	
	// test that hyphen and underscore check works
	filename = "US_ARc-YYYY.csv";
	ASSERT_MSG(!is_valid_era_filename(filename), "Check that function detects hypen and underscore absence", filename);

	// minimally correct string will still return True
	filename = "  -   _9999.csv";
	ASSERT_MSG(is_valid_era_filename(filename), "Check that function allows minimally correct filename string", filename);
	
	// test extension check works - will return False
	filename = "US-ARc_2009.txt";
	ASSERT_MSG(!is_valid_era_filename(filename), "Check that extension check is successful", filename);
}

UTEST_STATE();

int main(int argc, const char *const argv[])
{
	return utest_main(argc, argv);
}
