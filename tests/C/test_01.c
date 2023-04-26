/*
	test_01.c 
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
