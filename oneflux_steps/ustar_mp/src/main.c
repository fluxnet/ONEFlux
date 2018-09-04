/*
	main.c

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <signal.h>
#include <assert.h>
#include "types.h"
#include "dataset.h"
#include "ustar.h"
#include "bootstrapping.h"
#include "parser.h"
#include "../../compiler.h"

/* constants */
#define PROGRAM_VERSION		"v1.0"

/* static global variables */
static char *input_path;
static FILES *files;
static int files_count;
static unsigned char *threshold_forward_mode_percentiled;
static unsigned char *threshold_forward_mode_2_percentiled;
static unsigned char *threshold_forward_mode_3_percentiled;
static unsigned char *threshold_back_mode_percentiled;
static unsigned char *threshold_back_mode_2_percentiled;
static unsigned char *threshold_back_mode_3_percentiled;
static PREC *threshold_forward_mode_container;
static PREC *threshold_forward_mode_2_container;
static PREC *threshold_forward_mode_3_container;
static PREC *threshold_back_mode_container;
static PREC *threshold_back_mode_2_container;
static PREC *threshold_back_mode_3_container;
static PREC *threshold_high_forward_mode_container;
static PREC *threshold_high_forward_mode_2_container;
static PREC *threshold_high_forward_mode_3_container;
static PREC *threshold_high_back_mode_container;
static PREC *threshold_high_back_mode_2_container;
static PREC *threshold_high_back_mode_3_container;
static PREC *threshold_valid_forward_mode_container;
static PREC *threshold_valid_forward_mode_2_container;
static PREC *threshold_valid_forward_mode_3_container;
static PREC *threshold_valid_back_mode_container;
static PREC *threshold_valid_back_mode_2_container;
static PREC *threshold_valid_back_mode_3_container;
static SEASONS_GROUP *seasons_group;

/* global variables */
char *program_path = NULL;											/* mandatory */
char *output_path = NULL;											/* mandatory */
char *groupby = NULL;												/* mandatory */
int no_bootstrapping = 0;											/* default is off */
int hourly_dataset = 0;												/* default is off */
int dump_dataset = 0;												/* default is off */
int no_forward_mode = 1;											/* default is on */
int no_forward_mode_2 = 0;											/* default is off */
int no_forward_mode_3 = 1;											/* default is on */
int no_back_mode = 1;												/* default is on */
int no_back_mode_2 = 1;												/* default is on */
int no_back_mode_3 = 1;												/* default is on */
int bootstrapping_times = BOOTSTRAPPING_TIMES;						/* see types.h */
int percentile_check = 0;											/* default is off */
int percentile_value = PERCENTILE_CHECK;							/* see types.h */
int no_random_seed = 0;												/* default is off */
int seasons_group_allow_duplicates = 0;								/* default is off */
int seasons_group_by_user = 0;										/* default is off */
int window_size_forward_mode = WINDOWS_SIZE_FOR_FORWARD_MODE;		/* see types.h */
int window_size_forward_mode_2 = WINDOWS_SIZE_FOR_FORWARD_MODE_2;	/* see types.h */
int window_size_forward_mode_3 = WINDOWS_SIZE_FOR_FORWARD_MODE_3;	/* see types.h */
int ta_classes_count = TA_CLASSES_COUNT;							/* see types.h */
int ustar_classes_count = USTAR_CLASSES_COUNT;						/* see types.h */
PREC threshold_check = THRESHOLD_CHECK;								/* see types.h */
int seasons_group_count = 0;
int months_count;
int *seasons_end_index = NULL;										/* keep track of where each seasons ends. */
int *samples_per_season = NULL;
int is_itpSW_IN = 0;
int is_itpTA = 0;

const int months_days[MONTHS] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
const int percentiles[PERCENTILES_COUNT] = { 1, 5, 10, 25, 50, 75, 90, 95, 99 };
PREC *ustar_mean;
PREC *fx_mean;
WINDOW *ta_window;
WINDOW *ustar_window;

/* strings */
static const char banner[] =	"\nustar_mp "PROGRAM_VERSION"\n"
								"by Alessio Ribeca\n\n"
								"scientific contact: darpap at unitus dot it\n"
								"technical contact: a dot ribeca at unitus dot it\n\n"
								"DIBAF - University of Tuscia, Viterbo, Italy\n"
								"(builded on "__DATE__" at "__TIME__ " with "COMPILER")\n"
								"(use -h parameter for more information)\n";
static const char notes[] = "-- processed on %s with ustar_mp "PROGRAM_VERSION" compiled using "COMPILER" on "__DATE__" at "__TIME__"\n";
static const char *modes[6] = {	"-- ustar threshold by season (forward mode)\n\n",
								"-- ustar threshold by season (forward mode 2)\n\n",
								"-- ustar threshold by season (forward mode 3)\n\n",
								"-- ustar threshold by season (back mode)\n\n",
								"-- ustar threshold by season (back mode 2)\n\n",
								"-- ustar threshold by season (back mode 3)\n\n"
};
static const char bootstrapping_result[] = "-- bootstrapping\n\n";
static const char percentiles_result[] = "-- percentiles\n\n";
static const char result_file[] = "%s%sut.txt";
static const char *months[] = {
	"january",
	"february",
	"march",
	"april",
	"may",
	"june",
	"july",
	"agoust",
	"september",
	"october",
	"november",
	"december"
};
static char default_seasons_group[] = "1,2,3;4,5,6;7,8,9;10,11,12";
const char *input_columns_tokens[INPUT_VALUES] = { TIMESTAMP_STRING, "NEE", "TA", "USTAR", "SW_IN" };
char dataset_delimiter[] = ",\r\n";

/* messages */
static const char msg_dataset_not_specified[] =
"dataset not specified."
#if defined (_WIN32) || defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
" searching..."
#endif
"\n";
static const char msg_import_dataset[] = "import %s: ";
static const char msg_input_path[] = "input path = ";
static const char msg_output_path[] = "output path = %s\n";
static const char msg_dataset_grouped[] = "       grouped by";
static const char msg_season[] = "       season %d: ";
static const char msg_night_not_found[] = "warning: night column not found. nights and days computed from RG.";
static const char msg_import_ok[] = "ok\n       %d rows, %d valid rows, %d daytime\n";
const char msg_ok[] = "ok";
static const char msg_ustar_threshold[] = "computing ustar thresholds with %d ta classes and %d ustar classes...";
static const char msg_bootstrapping[] = "bootstrapping (%d times)...";
static const char msg_done[] = "done.\n";
static char msg_usage[] =	"How to use: ustar_mp parameter\n\n"
							"  parameters:\n\n"
							"    -input_path=file or path where input files are searched (optional)\n"
							"    -output_path=path -> where result files are created (optional)\n"
                        	"    -hourly -> specify an hourly dataset\n"
							"    -percentile=XXXXX -> set percentile value (default: %d)\n"
							"    -percentile_check -> enable percentile check\n"
							"    -ta_classes=N -> set number of ta classes (default: %d)\n"
							"    -ustar_classes=N -> set number of ustar classes (default: %d)\n"
							"    -window_size_forward_mode=N -> set window size (default: %d)\n"
							"    -window_size_forward_mode_2=N -> set window size (default: %d)\n"
							"    -window_size_forward_mode_3=N -> set window size (default: %d)\n"
							"    -window_size_back_mode=N -> set window size (default: %d)\n"
							"    -window_size_back_mode_2=N -> set window size (default: %d)\n"
							"    -window_size_back_mode_3=N -> set window size (default: %d)\n"
							"    -bootstrapping_times=N -> set boostrapping times (default: %d)\n"
							"    -dump_dataset -> save to file imported dataset (XXXXX_YYYY_dataset.csv)\n"
							"    -no_bootstrapping -> do not compute bootstrapping\n"
							"    -no_forward_mode_2 -> disable forward mode 2 (default is on)\n"
							"    -forward_mode -> enable forward mode (default is off)\n"
							"    -forward_mode_3 -> enable forward mode 3 (default is off)\n"
							"    -back_mode -> enable back mode (default is off)\n"
							"    -back_mode_2 -> enable back mode 2 (default is off)\n"
							"    -back_mode_3 -> enable back mode 3 (default is off)\n"
							"    -no_random_seed -> no init random seed (debug purposes)\n"
							"    -groupby=M -> use comma to separate months, use semicolon to group by season\n"
							"                  example: -groupby=12,1,2;3,4,5;6,7,8;9,10,11\n"
							"                            create a 4 seasons dataset with december at begin\n"
							"                            no duplicates allowed\n"
							"    -seasons_group_allow_duplicates -> allow duplicates for months\n"
							"    -threshold_check=N -> set threshold check (default: %g)\n\n";

/* errors */
extern const char err_out_of_memory[];
const char err_unable_to_create_results_file[] = "unable to create results file.\n";
const char err_too_less_values[] = "not enough values. u* threshold will not be computed.\n";
static const char err_unable_get_current_directory[] = "unable to retrieve current directory.\n";
static const char err_output_path_no_delimiter[] = "output path must terminating with a \"%c\"\n\n";
static const char err_unable_create_output_path[] = "unable to create output path: %s.\n";
static const char err_unable_to_register_atexit[] = "unable to register clean-up routine.\n";
static const char too_less_ustar_classes_back_mode[] = "not enough ustar classes for back mode %d";
static const char err_all_modes_disabled[] = "all modes disabled. computing ustar thresholds is not possible.\n";
static const char err_forward_mode_ustar_classes[] = "we cannot have %d ustar classes and a window size for forward mode %d of %d\n\n";
static const char err_back_mode_ustar_classes[] = "we cannot have %d ustar classes and a window size for back mode %d of %d\n\n";
static const char err_dataset_already_specified[] = "dataset already specified (%s)! \"%s\" skipped.\n";
static const char err_output_already_specified[] = "output path already specified (%s)! \"%s\" skipped.\n";
static const char err_value_to_high_for_bootstrapping_times[] = "warning: too times for bootstrapping, max value (%d) will be used.\n";
static const char err_no_random_seed[] = "warning: random seed not used.";
static const char err_arg_no_needs_param[] = "%s no needs parameter.\n\n";
static const char err_arg_needs_param[] = "%s parameter not specified.\n\n";
static const char err_unable_to_convert_value_for[] = "unable to convert value \"%s\" for %s\n\n";
static const char err_invalid_value_for[] = "warning: invalid value for %s\n";
static const char err_unable_create_output_filename[] = "unable to create output filename.\n";
static const char err_delimiter_length[] = "%s error: delimiter length must be 1 not %d\n\n";
static const char err_invalid_percentile_value[] = "percentile value must be between 1 and 99, not %d\n\n";
static const char err_no_rows_for_ustar[] = "unable to compute u*: no rows found!\n\n";
static const char err_no_concatenation[] = "computing u* using concatenated datasets is not possible.";

/* todo : check for null arguments */
static int write_results(	FILE *f,
							unsigned char *const threshold_forward_mode_percentiled,
							unsigned char *const threshold_forward_mode_2_percentiled,
							unsigned char *const threshold_forward_mode_3_percentiled,
							unsigned char *const threshold_back_mode_percentiled,
							unsigned char *const threshold_back_mode_2_percentiled,
							unsigned char *const threshold_back_mode_3_percentiled,
							PREC *const threshold_forward_mode_container,
							PREC *const threshold_forward_mode_2_container,
							PREC *const threshold_forward_mode_3_container,
							PREC *const threshold_back_mode_container,
							PREC *const threshold_back_mode_2_container,
							PREC *const threshold_back_mode_3_container) {
	int i;
	int y;
	int error;
	int mode;
	PREC result;
	PREC ustar_threshold_selected;

	/* TODO: removing constant "6" to be more flexible */
	PREC *pmodes[6];
	int enabled[6];

	enabled[0] = !no_forward_mode;
	enabled[1] = !no_forward_mode_2;
	enabled[2] = !no_forward_mode_3;
	enabled[3] = !no_back_mode;
	enabled[4] = !no_back_mode_2;
	enabled[5] = !no_back_mode_3;

	pmodes[0] = threshold_forward_mode_container;
	pmodes[1] = threshold_forward_mode_2_container;
	pmodes[2] = threshold_forward_mode_3_container;
	pmodes[3] = threshold_back_mode_container;
	pmodes[4] = threshold_back_mode_2_container;
	pmodes[5] = threshold_back_mode_3_container;

	for ( mode = 0; mode < 6; mode++ ) {
		/* check if method was applied */
		if ( enabled[mode] ) {
			/* write modes */
			fprintf(f, "%s", modes[mode]);
			for ( i = 0; i < seasons_group_count; i++ ) {
				result = median_ustar_threshold(pmodes[mode], ta_classes_count, i, &error);
				if ( error ) {
					puts(err_out_of_memory);
					fclose(f);
					return 0;
				}

				fprintf(f, "%*g", TABSPACE, result);
				switch ( mode ) {
					case 0:
						if ( threshold_forward_mode_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 1:
						if ( threshold_forward_mode_2_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 2:
						if ( threshold_forward_mode_3_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 3:
						if ( threshold_back_mode_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 4:
						if ( threshold_back_mode_2_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 5:
						if ( threshold_back_mode_3_percentiled ) {
							fputs(" ", f);
						}
					break;
				}

				if ( 0 == i ) {
					ustar_threshold_selected = result;
				} else if ( result > ustar_threshold_selected ) {
					ustar_threshold_selected = result;
				}
			}

			fprintf(f, "\n");

			for ( i = 0; i < seasons_group_count; i++ ) {
				fprintf(f, "%*d", TABSPACE, samples_per_season[i]);
				switch ( mode ) {
					case 0:
						if ( threshold_forward_mode_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 1:
						if ( threshold_forward_mode_2_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 2:
						if ( threshold_forward_mode_3_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 3:
						if ( threshold_back_mode_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 4:
						if ( threshold_back_mode_2_percentiled ) {
							fputs(" ", f);
						}
					break;

					case 5:
						if ( threshold_back_mode_3_percentiled ) {
							fputs(" ", f);
						}
					break;
				}
			}

			fprintf(f, "\n\n%*g\n\n", TABSPACE, ustar_threshold_selected);

			for ( y = 0; y < ta_classes_count; y++ ) {
				for ( i = 0; i < seasons_group_count; i++ ) {
					fprintf(f, "%*g", TABSPACE, pmodes[mode][i*ta_classes_count+y]);
					switch ( mode ) {
						case 0:
							if (	threshold_forward_mode_percentiled &&
									threshold_forward_mode_percentiled[i*ta_classes_count+y] ) {
										fputs("*", f);
							} else {
								fputs(" ", f);
							}
						break;

						case 1:
							if (	threshold_forward_mode_2_percentiled &&
									threshold_forward_mode_2_percentiled[i*ta_classes_count+y] ) {
										fputs("*", f);
							} else {
								fputs(" ", f);
							}
						break;

						case 2:
							if (	threshold_forward_mode_3_percentiled &&
									threshold_forward_mode_3_percentiled[i*ta_classes_count+y] ) {
										fputs("*", f);
							} else {
								fputs(" ", f);
							}
						break;

						case 3:
							if (	threshold_back_mode_percentiled &&
									threshold_back_mode_percentiled[i*ta_classes_count+y] ) {
										fputs("*", f);
							} else {
								fputs(" ", f);
							}
						break;

						case 4:
							if (	threshold_back_mode_2_percentiled &&
									threshold_back_mode_2_percentiled[i*ta_classes_count+y] ) {
										fputs("*", f);
							} else {
								fputs(" ", f);
							}
						break;

						case 5:
							if (	threshold_back_mode_3_percentiled &&
									threshold_back_mode_3_percentiled[i*ta_classes_count+y] ) {
										fputs("*", f);
							} else {
								fputs(" ", f);
							}
						break;
					}
				}

				fprintf(f, "\n");
			}

			fprintf(f, "\n");
		}
	}

	/* OK */
	return 1;
}

/* */
static int get_input_path(char *arg, char *param, void *p) {
	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	if ( input_path ) {
		printf(err_dataset_already_specified, input_path, param);
	} else {
		input_path = param;
	}
	
	/* ok */
	return 1;
}

/* */
static int get_output_path(char *arg, char *param, void *p) {
	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	if ( output_path ) {
		printf(err_output_already_specified, output_path, param);
	} else {
		output_path = param;
	}
	
	/* ok */
	return 1;
}

/* */
static int enable_percentile_check(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	percentile_check = 1;

	/* ok */
	return 1;
}

/* */
static int enable_hourly_dataset(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	hourly_dataset = 1;

	/* ok */
	return 1;
}

/* */
static int set_int_value(char *arg, char *param, void *p) {
	int i;
	int error;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}
	i = convert_string_to_int(param, &error);
	if ( error ) {
		printf(err_unable_to_convert_value_for, param, arg);
		return 0;
	}
	if ( i <= 0 ) {
		printf(err_invalid_value_for, arg);
		return 0;
	}

	/* set value */
	*((int *)p) = i;

	/* ok */
	return 1;
}

/* */
static int set_prec_value(char *arg, char *param, void *p) {
	PREC d;
	int error;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}
	d = convert_string_to_prec(param, &error);
	if ( error ) {
		printf(err_unable_to_convert_value_for, param, arg);
		return 0;
	}

	/* set value */
	*((PREC *)p) = d;

	/* ok */
	return 1;
}

/* */
static int set_groupby(char *arg, char *param, void *p) {
	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}
	groupby = param;
	return 1;
}

/* */
static int enable_arg(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}
	*((int *)p) = 0;
	return 1;
}

/* */
static int disable_arg(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}
	*((int *)p) = 1;
	return 1;
}

/* */
static int show_help(char *arg, char *param, void *p) {
	printf(msg_usage,
						PERCENTILE_CHECK,
						TA_CLASSES_COUNT,
						USTAR_CLASSES_COUNT,
						WINDOWS_SIZE_FOR_FORWARD_MODE,
						WINDOWS_SIZE_FOR_FORWARD_MODE_2,
						WINDOWS_SIZE_FOR_FORWARD_MODE_3,
						WINDOWS_SIZE_FOR_BACK_MODE,
						WINDOWS_SIZE_FOR_BACK_MODE_2,
						WINDOWS_SIZE_FOR_BACK_MODE_3,
						BOOTSTRAPPING_TIMES,
						THRESHOLD_CHECK
	);

	/* must return error */
	return 0;
}

/* */
void clean_up(void) {
	if ( seasons_group ) {
		free_seasons_group(seasons_group, seasons_group_count);
	}
	if ( samples_per_season ) {
		free(samples_per_season);
	}
	if ( seasons_end_index ) {
		free(seasons_end_index);
	}
	if ( ustar_window ) {
		free(ustar_window);
	}
	if ( ta_window ) {
		free(ta_window);
	}
	if ( ustar_mean ) {
		free(ustar_mean);
	}
	if ( fx_mean ) {
		free(fx_mean);
	}
	if ( threshold_back_mode_3_container ) {
		free(threshold_back_mode_3_container);
	}
	if ( threshold_back_mode_2_container ) {
		free(threshold_back_mode_2_container);
	}
	if ( threshold_back_mode_container ) {
		free(threshold_back_mode_container);
	}
	if ( threshold_forward_mode_3_container ) {
		free(threshold_forward_mode_3_container);
	}
	if ( threshold_forward_mode_2_container ) {
		free(threshold_forward_mode_2_container);
	}
	if ( threshold_forward_mode_container ) {
		free(threshold_forward_mode_container);
	}
	if ( threshold_high_forward_mode_container ) {
		free(threshold_high_forward_mode_container);
	}
	if ( threshold_high_forward_mode_2_container ) {
		free(threshold_high_forward_mode_2_container);
	}
	if ( threshold_high_forward_mode_3_container ) {
		free(threshold_high_forward_mode_3_container);
	}
	if ( threshold_high_back_mode_container ) {
		free(threshold_high_back_mode_container);
	}
	if ( threshold_high_back_mode_2_container ) {
		free(threshold_high_back_mode_2_container);
	}
	if ( threshold_high_back_mode_3_container ) {
		free(threshold_high_back_mode_3_container);
	}
	if ( threshold_valid_forward_mode_container ) {
		free(threshold_valid_forward_mode_container);
	}
	if ( threshold_valid_forward_mode_2_container ) {
		free(threshold_valid_forward_mode_2_container);
	}
	if ( threshold_valid_forward_mode_3_container ) {
		free(threshold_valid_forward_mode_3_container);
	}
	if ( threshold_valid_back_mode_container ) {
		free(threshold_valid_back_mode_container);
	}
	if ( threshold_valid_back_mode_2_container ) {
		free(threshold_valid_back_mode_2_container);
	}
	if ( threshold_valid_back_mode_3_container ) {
		free(threshold_valid_back_mode_3_container);
	}
	if ( percentile_check ) {
		if ( threshold_forward_mode_3_percentiled ) {
			free(threshold_forward_mode_3_percentiled);
		}
		if ( threshold_forward_mode_2_percentiled ) {
			free(threshold_forward_mode_2_percentiled);
		}
		if ( threshold_forward_mode_percentiled ) {
			free(threshold_forward_mode_percentiled);
		}
		if ( threshold_back_mode_3_percentiled ) {
			free(threshold_back_mode_3_percentiled);
		}
		if ( threshold_back_mode_2_percentiled ) {
			free(threshold_back_mode_2_percentiled);
		}
		if ( threshold_back_mode_percentiled ) {
			free(threshold_back_mode_percentiled);
		}
	}
	if ( files ) {
		free_files(files, files_count);
	}
	free(program_path);

	check_memory_leak();
}

/* */
int main(int argc, char *argv[]) {
	int i;
	int y;
	int z;
	int error;
	int rows_count;
	int days;
	int files_processed_count;
	int files_not_processed_count;
	int total_files_count;
	int seasons_group_count_bak;
	char buffer[BUFFER_SIZE];
	char filename[FILENAME_SIZE];
	char *p;
	char *string;
	FILE *f;
	ROW *rows;
	UT *ut;
	const ARGUMENT args[] = {
		{ "input_path", get_input_path, NULL },
		{ "output_path", get_output_path, NULL },
		{ "percentile", set_int_value, &percentile_value },
		{ "percentile_check", enable_percentile_check, NULL },
		{ "ta_classes", set_int_value, &ta_classes_count },
		{ "ustar_classes", set_int_value, &ustar_classes_count },
		{ "window_size_forward_mode", set_int_value, &window_size_forward_mode },
		{ "window_size_forward_mode_2", set_int_value, &window_size_forward_mode_2 },
		{ "window_size_forward_mode_3", set_int_value, &window_size_forward_mode_3 },
		{ "groupby", set_groupby, NULL },
		{ "dump_dataset", disable_arg, &dump_dataset }, /* disable_arg used as enable_arg ;) */
		{ "bootstrapping_times", set_int_value, &bootstrapping_times },
		{ "no_random_seed", disable_arg, &no_random_seed },
		{ "no_bootstrapping", disable_arg, &no_bootstrapping },
		{ "hourly", enable_hourly_dataset, NULL },
		{ "forward_mode", enable_arg, &no_forward_mode },
		{ "no_forward_mode_2", disable_arg, &no_forward_mode_2 },
		{ "forward_mode_3", enable_arg, &no_forward_mode_3 },
		{ "back_mode", enable_arg, &no_back_mode },
		{ "back_mode_2", enable_arg, &no_back_mode_2 },
		{ "back_mode_3", enable_arg, &no_back_mode_3 },
		{ "threshold_check", set_prec_value, &threshold_check },
		{ "seasons_group_allow_duplicates", disable_arg, &seasons_group_allow_duplicates },
		{ "h", show_help, NULL },
		{ "help", show_help, NULL },
		{ "?", show_help, NULL },
	};

	/* show banner */
	puts(banner);

	/* register atexit */
	if ( -1 == atexit(clean_up) ) {
		puts(err_unable_to_register_atexit);
		return 1;
	}

	/* parse arguments */
	if ( !parse_arguments(argc, argv, args, SIZEOF_ARRAY(args)) ) {
		return 1;
	}

	/* check arguments */
	if ( ustar_classes_count <= window_size_forward_mode ) {
		printf(err_forward_mode_ustar_classes, ustar_classes_count, window_size_forward_mode, 1);
		return 1;
	} else if ( ustar_classes_count <= window_size_forward_mode_2 ) {
		printf(err_forward_mode_ustar_classes, ustar_classes_count, window_size_forward_mode_2, 2);
		return 1;
	} else if ( ustar_classes_count <= window_size_forward_mode_3 ) {
		printf(err_forward_mode_ustar_classes, ustar_classes_count, window_size_forward_mode_3, 3);
		return 1;
	}
	
	/* check for percentile value */
	else if ( percentile_value <= 0 || percentile_value >= 100 ) {
		printf(err_invalid_percentile_value, percentile_value);
		return 1;
	}

	/* check enabled modes */
	if (	no_forward_mode &&
			no_forward_mode_2 &&
			no_forward_mode_3 &&
			no_back_mode &&
			no_back_mode_2 &&
			no_back_mode_3
	) {
		puts(err_all_modes_disabled);
		return 1;
	}

	/* check groupby */
	if ( !groupby ) {
		groupby = default_seasons_group;
	}

	seasons_group = parse_seasons_group(groupby, &seasons_group_count);
	if ( !seasons_group ) {
		return 1;
	}
	seasons_group_count_bak = seasons_group_count;

	/* alloc memory */
	if ( percentile_check ) {
		threshold_forward_mode_percentiled = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_forward_mode_percentiled);
		if ( !threshold_forward_mode_percentiled ) { puts(err_out_of_memory); return 1; }
		threshold_forward_mode_2_percentiled = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_forward_mode_2_percentiled);
		if ( !threshold_forward_mode_2_percentiled ) { puts(err_out_of_memory); return 1; }
		threshold_forward_mode_3_percentiled = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_forward_mode_3_percentiled);
		if ( !threshold_forward_mode_3_percentiled ) { puts(err_out_of_memory); return 1; }
		threshold_back_mode_percentiled = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_back_mode_percentiled);
		if ( !threshold_back_mode_percentiled ) { puts(err_out_of_memory); return 1; }
		threshold_back_mode_2_percentiled = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_back_mode_2_percentiled);
		if ( !threshold_back_mode_2_percentiled ) { puts(err_out_of_memory); return 1; }
		threshold_back_mode_3_percentiled = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_back_mode_3_percentiled);
		if ( !threshold_back_mode_3_percentiled ) { puts(err_out_of_memory); return 1; }
	}
	threshold_forward_mode_container = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_forward_mode_container);
	if ( !threshold_forward_mode_container ) { puts(err_out_of_memory); return 1; }
	threshold_forward_mode_2_container = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_forward_mode_2_container);
	if ( !threshold_forward_mode_2_container ) { puts(err_out_of_memory); return 1; }
	threshold_forward_mode_3_container = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_forward_mode_3_container);
	if ( !threshold_forward_mode_3_container ) { puts(err_out_of_memory); return 1; }
	threshold_back_mode_container = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_back_mode_container);
	if ( !threshold_back_mode_container ) { puts(err_out_of_memory); return 1; }
	threshold_back_mode_2_container = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_back_mode_2_container);
	if ( !threshold_back_mode_2_container ) { puts(err_out_of_memory); return 1; }
	threshold_back_mode_3_container = malloc(seasons_group_count*ta_classes_count*sizeof*threshold_back_mode_3_container);
	if ( !threshold_back_mode_3_container ) { puts(err_out_of_memory); return 1; }
	ustar_mean = malloc(ustar_classes_count*sizeof*ustar_mean);
	if ( !ustar_mean ) { puts(err_out_of_memory); return 1; }
	fx_mean = malloc(ustar_classes_count*sizeof*fx_mean);
	if ( !fx_mean ) { puts(err_out_of_memory); return 1; }
	ta_window = malloc(ta_classes_count*sizeof*ta_window);
	if ( !ta_window ) { puts(err_out_of_memory); return 1; }
	ustar_window = malloc(ustar_classes_count*sizeof*ustar_window);
	if ( !ustar_window ) { puts(err_out_of_memory); return 1; }
	threshold_high_forward_mode_container = malloc(bootstrapping_times*sizeof*threshold_high_forward_mode_container);
	if ( !threshold_high_forward_mode_container ) { puts(err_out_of_memory); return 1; }
	threshold_high_forward_mode_2_container = malloc(bootstrapping_times*sizeof*threshold_high_forward_mode_2_container);
	if ( !threshold_high_forward_mode_2_container ) { puts(err_out_of_memory); return 1; }
	threshold_high_forward_mode_3_container = malloc(bootstrapping_times*sizeof*threshold_high_forward_mode_3_container);
	if ( !threshold_high_forward_mode_3_container ) { puts(err_out_of_memory); return 1; }
	threshold_high_back_mode_container = malloc(bootstrapping_times*sizeof*threshold_high_back_mode_container);
	if ( !threshold_forward_mode_container ) { puts(err_out_of_memory); return 1; }
	threshold_high_back_mode_2_container = malloc(bootstrapping_times*sizeof*threshold_high_back_mode_2_container);
	if ( !threshold_high_back_mode_2_container ) { puts(err_out_of_memory); return 1; }
	threshold_high_back_mode_3_container = malloc(bootstrapping_times*sizeof*threshold_high_back_mode_3_container);
	if ( !threshold_high_back_mode_3_container ) { puts(err_out_of_memory); return 1; }
	threshold_valid_forward_mode_container = malloc(bootstrapping_times*sizeof*threshold_valid_forward_mode_container);
	if ( !threshold_valid_forward_mode_container ) { puts(err_out_of_memory); return 1; }
	threshold_valid_forward_mode_2_container = malloc(bootstrapping_times*sizeof*threshold_valid_forward_mode_2_container);
	if ( !threshold_valid_forward_mode_2_container ) { puts(err_out_of_memory); return 1; }
	threshold_valid_forward_mode_3_container = malloc(bootstrapping_times*sizeof*threshold_valid_forward_mode_3_container);
	if ( !threshold_valid_forward_mode_3_container ) { puts(err_out_of_memory); return 1; }
	threshold_valid_back_mode_container = malloc(bootstrapping_times*sizeof*threshold_valid_back_mode_container);
	if ( !threshold_valid_back_mode_container ) { puts(err_out_of_memory); return 1; }
	threshold_valid_back_mode_2_container = malloc(bootstrapping_times*sizeof*threshold_valid_back_mode_2_container);
	if ( !threshold_valid_back_mode_2_container ) { puts(err_out_of_memory); return 1; }
	threshold_valid_back_mode_3_container = malloc(bootstrapping_times*sizeof*threshold_valid_back_mode_3_container);
	if ( !threshold_valid_back_mode_3_container ) { puts(err_out_of_memory); return 1; }
	seasons_end_index = malloc(seasons_group_count*sizeof*seasons_end_index);
	if ( !seasons_end_index ) { puts(err_out_of_memory); return 1; }
	samples_per_season = malloc(seasons_group_count*sizeof*samples_per_season);
	if ( !samples_per_season ) { puts(err_out_of_memory); return 1; }

	/* get program path */
	program_path = get_current_directory();
	if ( !program_path ) {
		puts(err_unable_get_current_directory);
		return 1;
	}

	/* dataset specified ? */
	if ( !input_path ) {
		puts(msg_dataset_not_specified);
		input_path = program_path;
	}

	/* output path specified ? */
	if ( output_path ) {
		/* check if last char is a FOLDER_DELIMITER */
		if ( output_path[strlen(output_path)-1] != FOLDER_DELIMITER ) {
			printf(err_output_path_no_delimiter, FOLDER_DELIMITER);
			return 1;
		}

		/* check if output path exists */
		if ( !path_exists(output_path) ) {
			if ( !create_dir(output_path) ) {
				printf(err_unable_create_output_path, output_path);
				return 1;
			}
		}
	} else {
		output_path = program_path;
	}

	/* show input paths */
	printf(msg_input_path);
	for ( i = 0; input_path[i]; i++ ) {
		if ( input_path[i] != ',' ) {
			putchar(input_path[i]);
		} else {
			puts("");
			printf(msg_input_path);
		}
	}
	puts("");

	/* show output path */
	printf(msg_output_path, output_path);

	/* get files */
	files = get_files(program_path, input_path, &files_count, &error);
	if ( error ) {
		return 1;
	}

	/* check for concatenated datasets */
	for ( i = 0; i < files_count; i ++ ) {
		if ( files[i].count > 1 ) {
			puts(err_no_concatenation);
			return 1;
		}
	}

	/* init random seed */
	init_random_seed();

	/* reset */
	files_processed_count = 0;
	files_not_processed_count = 0;
	total_files_count = 0;

	/* loop for searching file */
	for ( z = 0; z < files_count; z++) {
		/* reset */
		seasons_group_count = seasons_group_count_bak;

		/* inc total files founded */
		total_files_count += files[z].count;

		/* processing and create output filename */
		filename[0] = '\0';
		for ( i = 0; i < files[z].count; i++ ) {
			printf(msg_import_dataset, files[z].list[i].fullpath);
			string = string_copy(files[z].list[i].name);
			if ( !string ) {
				puts(err_out_of_memory);
				return 1;
			}

			/* check for extension */
			p = strrchr(string, '.');
			if ( p ) {
				/* remove extension */
				*p = '\0';
			}

			/* add to filename */
			if ( !mystrcat(filename, string, FILENAME_MAX) && '\0' == filename[0]) {
				puts(err_unable_create_output_filename);
				files_not_processed_count += files[z].count;
				free(string);
				continue;
			}

			/* add underscore */
			if ( !add_char_to_string(filename, '_', FILENAME_MAX) && '\0' == filename[0]) {
				puts(err_unable_create_output_filename);
				files_not_processed_count += files[z].count;
				free(string);
				continue;
			}

			/* free memory */
			free(string);
		}

		/* import dataset */
		ut = import_dataset(files[z].list, files[z].count);
		if ( !ut ) {
			files_not_processed_count += files[z].count;
			continue;
		}
		
		/* compute valid night rows && days */
		rows_count = 0;
		days = 0;
		for ( i = 0; i < ut->rows_full_details_count; i++ ) {
			if ( IS_FLAG_SET(ut->rows_full_details[i].flags, ALL_VALID) && !IS_INVALID_VALUE(ut->rows_full_details[i].night) ) {
				++rows_count;
			}
			if ( IS_INVALID_VALUE(ut->rows_full_details[i].night) ) {
				++days;
			}
		}
		printf(msg_import_ok, ut->rows_full_details_count, rows_count, days);
		if ( !rows_count ) {
			puts(err_no_rows_for_ustar);
			free_ut(ut);
			files_not_processed_count += files[z].count;
			continue;
		}

		/* alloc memory for clean dataset */
		rows = malloc(rows_count*sizeof*rows);
		if ( !rows ) {
			puts(err_out_of_memory);
			return 1;
		}

		/* can be grouped */
		if ( ut->can_be_grouped ) {
			int j;
			int k;
			int days;

			/* show and create seasons group */
			k = 0; /* keep track of current clean row */
			days = 0;
			for ( i = 0; i < seasons_group_count; i++ ) {
				printf(msg_season, i+1);
				samples_per_season[i] = 0;
				for ( y = 0; y < seasons_group[i].count; y++ ) {
					if ( (FEBRUARY == seasons_group[i].month[y]) && ((LEAP_YEAR_ROWS/(hourly_dataset?2:1)) == ut->rows_full_details_count) ) {
						++days;
					}
					days += months_days[seasons_group[i].month[y]] * (hourly_dataset?24:48);
					printf("%s ", months[seasons_group[i].month[y]]);
					for ( j = 0; j < ut->rows_full_details_count; j++ ) {
						if (
								(ut->rows_full_details[j].month_per_group == seasons_group[i].month[y]) &&
								IS_FLAG_SET(ut->rows_full_details[j].flags, ALL_VALID) &&
								!IS_INVALID_VALUE(ut->rows_full_details[j].night)
						) {
							rows[k].value[NEE] = ut->rows_full_details[j].value[NEE];
							rows[k].value[TA] = ut->rows_full_details[j].value[TA];
							rows[k].value[USTAR] = ut->rows_full_details[j].value[USTAR];
							rows[k].index = k++;
							++samples_per_season[i];
						}
					}
				}

				seasons_end_index[i] = days;

				/* new line */
				puts("");
			}

			/* new line */
			puts("");
		} else {
			/* fill clean dataset */
			y = 0; /* keep track of current clean row */
			for ( i = 0; i < ut->rows_full_details_count; i++ ) {
				/* fix it */
				if ( IS_FLAG_SET(ut->rows_full_details[i].flags, ALL_VALID) && !IS_INVALID_VALUE(ut->rows_full_details[i].night) ) {
					rows[y].value[NEE] = ut->rows_full_details[i].value[NEE];
					rows[y].value[TA] = ut->rows_full_details[i].value[TA];
					rows[y].value[USTAR] = ut->rows_full_details[i].value[USTAR];
					rows[y].index = y++;
				}
			}
			/* adjust seasons */
			seasons_group_count = 1;
			samples_per_season[seasons_group_count-1] = y;
			seasons_end_index[seasons_group_count-1] = y;
		}

		/* ustar thresholds */
		printf(msg_ustar_threshold, ta_classes_count, ustar_classes_count);

		/* dump dataset ? */
		if ( dump_dataset && rows_count ) {
			printf("dump dataset...");
			sprintf(buffer, "%s%sdataset.csv", output_path, filename);
			f = fopen(buffer, "w");
			if ( f ) {
				fprintf(f, "%s,%s%s,%s\n",
										input_columns_tokens[NEE],
										is_itpTA ? "itp" : "", input_columns_tokens[TA],
										input_columns_tokens[USTAR]
				);
				for ( i = 0; i < rows_count; i++ ) {
					fprintf(f, "%g,%g,%g\n",
											rows[i].value[NEE],
											rows[i].value[TA],
											rows[i].value[USTAR]
					);
				}
				fclose(f);
				puts(msg_ok);
			} else {
				puts("unable to create file!");
			}
		}

		/* check rows, prevent file creation...added on June 27, 2013 */
		if ( rows_count < ta_classes_count*ustar_classes_count ) {
			puts(err_too_less_values);
			free(rows);
			free_ut(ut);
			++files_not_processed_count;
			continue;
		}

		/* create result file */
		if ( ut->details_count ) {
			sprintf(buffer, "%s%s_usmp_%d.txt", output_path, ut->details[0]->site, ut->details[0]->year);
		} else {
			sprintf(buffer, result_file, output_path, filename);
		}
		f = fopen(buffer, "w");
		if ( !f ) {
			puts(err_unable_to_create_results_file);
			free(rows);
			free_ut(ut);
			++files_not_processed_count;
			continue;
		}

		/* compute ustar thresholds */
		if ( !ustar_threshold(	rows,
								rows_count,
								days,
								threshold_forward_mode_percentiled,
								threshold_forward_mode_2_percentiled,
								threshold_forward_mode_3_percentiled,
								threshold_back_mode_percentiled,
								threshold_back_mode_2_percentiled,
								threshold_back_mode_3_percentiled,
								threshold_forward_mode_container,
								threshold_forward_mode_2_container,
								threshold_forward_mode_3_container,
								threshold_back_mode_container,
								threshold_back_mode_2_container,
								threshold_back_mode_3_container,
								ustar_mean,
								fx_mean,
								ta_window,
								ustar_window) ) {
			free(rows);
			free_ut(ut);
			++files_not_processed_count;
			fclose(f);
			continue;
		}

		/* write results */
		if ( !write_results(	f,
								threshold_forward_mode_percentiled,
								threshold_forward_mode_2_percentiled,
								threshold_forward_mode_3_percentiled,
								threshold_back_mode_percentiled,
								threshold_back_mode_2_percentiled,
								threshold_back_mode_3_percentiled,
								threshold_forward_mode_container,
								threshold_forward_mode_2_container,
								threshold_forward_mode_3_container,
								threshold_back_mode_container,
								threshold_back_mode_2_container,
								threshold_back_mode_3_container) ) {
			free(rows);
			free_ut(ut);
			++files_not_processed_count;
			fclose(f);
			continue;
		}
		puts(msg_ok);

		/* free memory */
		free(rows);

		/* bootstrapping ? */
		if ( !no_bootstrapping ) {
			/* check for percentiles */
			if ( bootstrapping_times < PERCENTILES_COUNT ) {
				puts("warning: not enough bootstrapping times. percentiles not computed.");
			}
			printf(msg_bootstrapping, bootstrapping_times);
			fprintf(f, bootstrapping_result);
			if ( !bootstrapping(	f,
									ut->rows_full_details,
									ut->rows_full_details_count,
									bootstrapping_times,
									threshold_forward_mode_container,
									threshold_forward_mode_2_container,
									threshold_forward_mode_3_container,
									threshold_back_mode_container,
									threshold_back_mode_2_container,
									threshold_back_mode_3_container,
									threshold_high_forward_mode_container,
									threshold_high_forward_mode_2_container,
									threshold_high_forward_mode_3_container,
									threshold_high_back_mode_container,
									threshold_high_back_mode_2_container,
									threshold_high_back_mode_3_container,
									threshold_valid_forward_mode_container,
									threshold_valid_forward_mode_2_container,
									threshold_valid_forward_mode_3_container,
									threshold_valid_back_mode_container,
									threshold_valid_back_mode_2_container,
									threshold_valid_back_mode_3_container) ) {
				free_ut(ut);
				fclose(f);
				continue;
			}

			/* ok */
			puts(msg_ok);
		}

		/* write notes */
		sprintf(buffer, notes, get_datetime_in_timestamp_format());
		fputs(buffer, f);
		for ( y = 0; y < ut->details_count; y++ ) {
			if ( ut->details[y] ) {
				for ( i = 0; i < ut->details[y]->notes_count; i++ ) {
					fprintf(f, "-- %s\n", ut->details[y]->notes[i]);
				}
			}
		}
		
		/* close file */
		fclose(f);

		/* free memory */
		free_ut(ut);

		/* inc */
		++files_processed_count;

		/* */
		puts(msg_done);
	}

	/* summary */
	printf("%d file%s founded: %d processed, %d skipped.\n\n",
																total_files_count,
																total_files_count > 1 ? "s" : "",
																files_processed_count,
																files_not_processed_count);
	/* free memory at exit */
	return 0;
}
