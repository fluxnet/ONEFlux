/*
	test_01.c 
		
	check library output for reference:
	
	Running suite(s): Meteo
	66%: Checks: 3, Failures: 1, Errors: 0
	test_01.c:13:F:Sanity checks:sanity_check:0: this should fail
	test_01.c:18:P:Sanity checks:sanity_check_2:0: Passed
	test_01.c:53:P:Dataset files:test_is_valid_era_filename:0: Passed
*/

#include "utest_oneflux.h"
#include "../../oneflux_steps/common/common.c"
#include "../../oneflux_steps/meteo_proc/src/dataset.c"

/*
	dataset.c  needs some external variables
*/
char *qc_auto_files_path = NULL;	/* mandatory */
char *era_files_path = NULL;		/* mandatory */
char *output_files_path = NULL;		/* mandatory */

UTEST(sanity_check, 1)
{
	FAIL_UNLESS(5 == 5, "this should succeed");
    FAIL_UNLESS(6 == 5, "this should fail");
}

UTEST(sanity_check, 2)
{
	FAIL_UNLESS(5 == 5, "this should succeed");
}

UTEST(test_is_valid_era_filename, 1)
{
	char* filename;
	
	filename = "";
	
	/* CK_ASSERT_MSG:  Fails test if supplied condition evaluates to false and displays user provided message. */

	CK_ASSERT_MSG(!is_valid_era_filename(filename), "False should be returned for this string: '%s'", filename);
	
	filename = "  -   _9999.csv";
	CK_ASSERT_MSG(is_valid_era_filename(filename), "True should be returned for this string: %s", filename);
	
	filename = "";
	CK_ASSERT_MSG(!is_valid_era_filename(filename), "False should be returned for this string: %s", filename);
	
	// example of a correct string
	filename = "US-ARc_2009.csv";
	CK_ASSERT_MSG(is_valid_era_filename(filename), "True should be returned for this string: %s", filename);
}

/*
	PLEASE NOTE:

	we can use 'UTEST_MAIN' instead of call 'UTEST_STATE' and 'main'
	but in this way we can do our own stuff like load files and so on...
*/

UTEST_STATE();

int main(int argc, const char *const argv[])
{
	/* do your own stuff here! */
	
	return utest_main(argc, argv);
}
