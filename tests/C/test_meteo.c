#include <check.h>
#include <stdio.h>
#include <stdlib.h>
#include "../../oneflux_steps/meteo_proc/src/dataset.c"

char *qc_auto_files_path = NULL; /* mandatory */
char *era_files_path = NULL;     /* mandatory */
char *output_files_path = NULL;

START_TEST(sanity_check) {
    fail_unless(5 == 5, "this should succeed");
    fail_unless(6 == 5, "this should fail");
}
END_TEST

START_TEST(sanity_check_2) {
    fail_unless(5 == 5, "this should succeed");
}
END_TEST

START_TEST(test_import_era_values){

    // create dummy input file and check that 

    // ck_assert_msg();

}
END_TEST

START_TEST(test_is_valid_era_filename) {
    char * filename;
    filename = "";
    char out[1024];
    //ck_assert_msg:  Fails test if supplied condition evaluates to false and displays user provided message.

    // fail_unless(is_valid_era_filename(filename), "this should fail");
    sprintf(out, "%s should be returned for this string: '%s'", "False", filename);
    ck_assert_msg(!is_valid_era_filename(filename), out);
    
    filename = "  -   _9999.csv";
    sprintf(out, "%s should be returned for this string: %s", "True", filename);
    ck_assert_msg(is_valid_era_filename(filename), out);

    // empty string
    filename = "";
    sprintf(out, "%s should be returned for this string: %s", "False", filename);
    ck_assert_msg(!is_valid_era_filename(filename), out);

    // example of a correct string
    filename = "US-ARc_2009.csv";
    sprintf(out, "%s should be returned for this string: %s", "True", filename);
    ck_assert_msg(is_valid_era_filename(filename), out);
}
END_TEST

// // unterminated string (potential bug) no easy way to test this
// START_TEST(test_unterm)
// {
//     char *unterm_str = [ 'h', 'e', 'l', ];
//     fail_unless(is_valid_era_filename(unterm_str));
// }
// END_TEST

Suite *meteo_suite(void) {
    Suite *s;
    TCase *tc_ds_sanity, *tc_ds_files;

    s = suite_create("Meteo");

    /* Dataset sanity case */
    tc_ds_sanity = tcase_create("Sanity checks");
    
    // actual tests
    tcase_add_test(tc_ds_sanity, sanity_check);
    tcase_add_test(tc_ds_sanity, sanity_check_2);

    // add the tests to the suite
    suite_add_tcase(s, tc_ds_sanity);



    /* Dataset file names test case */
    tc_ds_files = tcase_create("Dataset files");

    // actual tests
    tcase_add_test(tc_ds_files, test_is_valid_era_filename);

    // add the tests to the suite
    suite_add_tcase(s, tc_ds_files);

    return s;
}

// boiler plate that should never need
// to be changed
int main(void) {
    int num_failed;
    Suite *s;
    SRunner *sr;

    s = meteo_suite();
    sr = srunner_create(s);

    srunner_run_all(sr, CK_VERBOSE);
    num_failed = srunner_ntests_failed(sr);
    srunner_free(sr);
    return (num_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;

    // SRunner *sr = srunner_create(s1);
    // suite_add_tcase(s1, tc1_1);
    // tcase_add_test(tc1_1, sanity_check);
    // tcase_add_test(tc2_1, sanity_check);
    // srunner_run_all(sr, CK_ENV);
    // nf = srunner_ntests_failed(sr);
    // srunner_free(sr);
    // return nf == 0 ? 0 : 1;
}
