/*
	main.c

	This file is part of gf_mds tool that applies an
	improved and fully parameterizable version of the
	Marginal Distribution Sampling gapfilling method
	described in Reichstein et al. 2005

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: darpap at unitus dot it
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "dataset.h"
#include "../../../compiler.h"
	
/* constants */
#define PROGRAM_VERSION "3.0"
const char def_tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1] =
{
	"NEE"
	, "SW_IN"
	, "TA"
	, "VPD"
	, TIMESTAMP_END_STRING
};

/* static global variables */
static FILES *files;
static int files_count;
static int rows_min = GF_ROWS_MIN;								/* see types.h */
/* v2.04b */
static int sym_mean = 0;
/* v3.0 */
static int max_mdv_win = 0;
static int driver1_qc_col = -1;
static int driver2a_qc_col = -1;
static int driver2b_qc_col = -1;
static PREC driver1_qc_thrs = INVALID_VALUE;
static PREC driver2a_qc_thrs = INVALID_VALUE;
static PREC driver2b_qc_thrs = INVALID_VALUE;

/* global variables */
char *program_path = NULL;										/* required */
char *input_path = NULL;										/* required */
char *output_path = NULL;										/* required */
int timeres = HALFHOURLY_TIMERES;								/* required */
int *years = NULL;												/* required */
int years_count = 0;											/* required */
PREC driver1_tolerance_min = GF_DRIVER_1_TOLERANCE_MIN;			/* required */
PREC driver1_tolerance_max = GF_DRIVER_1_TOLERANCE_MAX;			/* required */
PREC driver2a_tolerance_min = GF_DRIVER_2A_TOLERANCE_MIN;		/* required */
PREC driver2a_tolerance_max = GF_DRIVER_2A_TOLERANCE_MAX;		/* required */
PREC driver2b_tolerance_min = GF_DRIVER_2B_TOLERANCE_MIN;		/* required */
PREC driver2b_tolerance_max = GF_DRIVER_2B_TOLERANCE_MAX;		/* required */

int custom_tokens[GF_TOKENS];

/* strings */
static const char banner[] =	"\ngf_mds v"PROGRAM_VERSION"\n"
								"by A. Ribeca\n\n"
								"scientific contact: <darpap@unitus.it>\n"
								"technical contact: <a.ribeca@unitus.it>\n\n"
								"DIBAF - University of Tuscia, Viterbo, Italy\n"
								"(builded on "__DATE__" at "__TIME__ " with "COMPILER")\n"
								"(use -h parameter for more information)\n";
static const char notes[] = "processed on %s with gf_mds "PROGRAM_VERSION" compiled using "COMPILER" on "__DATE__" at " __TIME__;

/* must have same order of eValues in types.h */
char tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1];
static const char gap_file[] = "%s%smds.csv";
static const char gap_header[] = "%s,%s,FILLED,QC,HAT,SAMPLE,STDDEV,METHOD,QC_HAT,TIMEWINDOW\n";
static const char gap_format[] = "%s,%g,%g,%d,%g,%d,%g,%d,%d,%d\n";

/* v2.04b */
static const char gap_header_sym_mean[] = "%s,%s,FILLED,QC,HAT,DT,DT_MA,DT_MA_SAMPLE,DT_MB,DT_MB_SAMPLE,SAMPLE,STDDEV,METHOD,QC_HAT,TIMEWINDOW\n";
static const char gap_format_sym_mean[] = "%s,%g,%g,%d,%g,%g,%g,%d,%g,%d,%d,%g,%d,%d,%d\n";

/* messages */
static const char msg_dataset_not_specified[] =
"dataset not specified. searching...\n";
static const char msg_import_dataset[] = "processing: %s%s";
static const char msg_input_path[] = "input path = %s\n";
static const char msg_output_path[] = "output path = %s\n\n";
static const char msg_rows_min[] = "rows min = %d\n\n";
static const char msg_ok[] = "ok";
static const char msg_ok_with_gaps_unfilled[] = "ok with %d gaps unfilled.\n";
static const char msg_summary[] = "\n%d file%s found: %d processed, %d skipped.\n\n";
static const char msg_usage[] =	"This code applies the gapfilling Marginal Distribution Sampling method\n"
								"described in Reichstein et al. 2005 (Global Change Biology).\nThis version "
								"allows larger flexibility in the selection of the drivers.\n"
								"\n"
								"Differences respect to the original method are the possibilities to:\n"
								"1) define the variable to fill and the drivers to use\n"
								"2) change the tolerance of the different drivers (see the paper for details)\n"
								"3) process a multi-years dataset\n"
								"4) process hourly timeseries\n"
								"\n"
								"Basic on the use:\n"
								"The MDS method uses look-up-tables defined around each single gap, looking for\nthe "
								"best compromise between size of the window (as small as possible)\nand number of drivers "
								"used.\nThe main driver (driver1) is used when it is not possible\nto fill the gap using all the "
								"three drivers (driver1, driver2a and driver2b).\nFor details see the original paper.\n"
								"\n"
								"How to use: gf_mds parameters\n\n"
								"  -input=filename -> name of the file to be processed and multiple years\n"
								"    (optional, if not specified all the files in the folder are processed)\n"
								"    use , to separate paths\\files that will be processed singularly\n"
								"    (e.g. -input=ITRoc2003.txt,ITCpz2003.txt will process only these 2 files)\n"
								"    use + to concatenate paths\\files that will me merged in a single file\n"
								"    IMPORTANT: this option should be used only if the years are all consecutive\n"
								"    (multiyears timeseries, e.g. -input=ITRo2003.txt+ITRo2004.txt\n              "
								"       will process the 2 years as one dataset of two years)\n\n"
								"  -output=path where result files are created (optional)\n"
								"    (if not specified the folder with the program file is used)\n\n"
								"  -hourly -> specify that your file is not halfhourly but hourly\n\n"
								"  -tofill=XXXX -> name of the the variable to be filled as reported in\n    the header of the "
								" input file (max %d chrs, default is \"%s\")\n\n"
								"  -driver1=XXXX -> name of the name of the main driver (as in the header)\n    that is used in case using all the 3 drivers "
								"it is not possible to fill\n    the gap (max %d chrs, default is \"%s\", Incoming Solar Radiation in Wm-2)\n\n"
								"  -driver2a=XXXX -> name of the first additional driver as reported in\n    the header of the input file\n"
								"    (max %d chrs, default is \"%s\", Air Temperature in degree C)\n\n"
								"  -driver2b=XXXX -> name of the second additional driver as reported in\n    the header of the input file\n"
								"    (max %d chrs, default is \"%s\", Vapor Pressure Deficit in hPa)\n\n"
								"  -date=XXXX -> name of the variable in the header of the input file\n    where the timestamp is reported "
								"in the format YYYYMMDDHHMM\n    (max %d chrs, default is \"%s\")\n\n"
								"  -tdriver1=min[,max] -> set the tolerance values used to define\n    similar conditions related to driver1. If only "
								"one values is specified\n    it is used for all the driver1 values (e.g. -tdriver1=5).\n    If two values are reported "
								"(e.g. -tdriver1=4,10)\n    the first is used for driver1 values below it, the second for\n    driver1 values above it "
								"while between the two the driver1 value itself\n    is also used as tolerance (in the example a tolerance of 6 "
								"would be\n    used for driver1=6)\n    (default is two values for SW_IN in Wm-2 and are min: %g, max: %g)\n\n"
								"  -tdriver2a=min[,max] -> set the tolerance values used to define\n    similar conditions related to driver2a. "
								"See description for tdriver1\n"
								"    (default is one value for TA in degrees C and is %g)\n\n"
								"  -tdriver2b=min[,max] -> set the tolerance values used to define\n    similar conditions related to driver2b. "
								"See description for tdriver1\n"
								"    (default is one value for VPD in hPa and is %g)\n\n"
								"  -driver1_qc_col=values -> set column for main driver qc check\n\n"
								"  -driver2a_qc_col=values -> set column for first additional driver qc check\n\n"
								"  -driver2b_qc_col=values -> set column for second additional driver qc check\n\n"
								"  -driver1_qc_thrs=values -> set threshold for main driver qc check\n\n"
								"  -driver2a_qc_thrs=values -> set threshold for first additional driver qc check\n\n"
								"  -driver2b_qc_thrs=values -> set threshold for second additional driver qc check\n\n"
								"  -rows_min=value -> set the minimum number of rows with valid data\n"
								"    to run the gapfilling (default: %d)\n\n"
								"  -nohat -> disable hat computing (gapfilling applied to all the records,\n"
								"    even if not missing, enabled by default)\n\n"
								"  -sym_mean -> enable symmetric mean method\n\n"
								"  -max_mdv_win=value -> set max window to be used when MDV is applied as last option\n\n"
								"  -debug -> save used values to compute gf to file\n\n"
								"  -h -> show this help\n\n"
;

/* errors messages */
extern const char err_out_of_memory[];
const char err_unable_open_file[] = "unable to open file.";
const char err_empty_file[] = "empty file ?";
static const char err_unable_get_current_directory[] = "unable to retrieve current directory.\n";
static const char err_unable_to_register_atexit[] = "unable to register clean-up routine.\n";
static const char err_unable_create_output_path[] = "unable to create output path: %s.\n";
static const char err_unable_to_convert_value_for[] = "unable to convert value \"%s\" for %s\n\n";
static const char err_output_path_no_delimiter[] = "output path must terminating with a \"%c\"\n\n";
static const char err_unable_open_output_path[] = "unable to open output path.\n";
static const char err_tolerances_not_specified[] = "tolerances not specified for %s\n\n";
static const char err_no_min_tolerance[] = "no min tolerance available for %s\n\n";
static const char err_unable_create_gap_file[] = "unable to create gap file.";
static const char err_unable_convert_tolerance[] = "unable to convert tolerance \"%s\" for %s.\n\n";
static const char err_arg_needs_param[] = "%s parameter not specified.\n\n";
static const char err_arg_no_needs_param[] = "%s no needs parameter.\n\n";
static const char err_dataset_already_specified[] = "dataset already specified (%s)! \"%s\" skipped.\n";
static const char err_output_already_specified[] = "output path already specified (%s)! \"%s\" skipped.\n";
static const char err_unable_create_output_filename[] = "unable to create output filename.\n";
static const char err_rows_min[] = "rows_min must be between %d and %d not %d. default value (%d) will be used";

/* */
static void clean_up(void) {
	if ( files ) {
		free_files(files, files_count);
	}
	if ( program_path ) {
		free(program_path);
	}
#if defined (_WIN32) && defined (_DEBUG) 
	dump_memory_leaks();
#endif
}

/* */
int get_input_path(char *arg, char *param, void *p) {
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
int get_output_path(char *arg, char *param, void *p) {
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
int set_hourly_dataset(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	timeres = HOURLY_TIMERES;

	/* ok */
	return 1;
}

/* */
static int set_token(char *arg, char *param, void *p) {
	int i;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	i = (int)p;
	assert(i < GF_TOKENS);

	strncpy(tokens[i], param, GF_TOKEN_LENGTH_MAX-1);
	tokens[i][GF_TOKEN_LENGTH_MAX-1] = '\0';
	custom_tokens[i] = 1;

	/* ok */
	return 1;
}

/* */
typedef struct {
	const char *name;
	PREC *min;
	PREC *max;
} TOLERANCE;

int set_driver_tolerances(char *arg, char *param, void *p) {
	int error;
	PREC min;
	PREC max;
	char *t;
	TOLERANCE* tol;

	tol = (TOLERANCE*)p;
	assert(tol);

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	if ( !param[0] ) {
		printf(err_tolerances_not_specified, tol->name);
		return 0;
	}

	/* check for comma */
	t = strrchr(param, ',');
	if ( !t ) {
		min = convert_string_to_prec(param, &error);
		if ( error ) {
			printf(err_unable_convert_tolerance, param, tol->name);
			return 0;
		}
		max = INVALID_VALUE;
	} else {
		/* get min */
		*t = 0;
		if ( !param[0] ) {
			printf(err_no_min_tolerance, tol->name);
			return 0;
		}
		min = convert_string_to_prec(param, &error);
		if ( error ) {
			printf(err_unable_convert_tolerance, param, tol->name);
			return 0;
		}

		/* get max */
		++t;
		if ( !t[0] ) {
			max = INVALID_VALUE;
		} else {
			max = convert_string_to_prec(t, &error);
			if ( error ) {
				printf(err_unable_convert_tolerance, param, tol->name);
				return 0;
			}
		}
	}

	/* */
	*tol->min = min;
	*tol->max = max;

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

	/* set value */
	*((int *)p) = i;

	/* ok */
	return 1;
}

/* */
static int set_prec_value(char *arg, char *param, void *p) {
	PREC v;
	int error;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}
	v = convert_string_to_prec(param, &error);
	if ( error ) {
		printf(err_unable_to_convert_value_for, param, arg);
		return 0;
	}

	/* set value */
	*((PREC *)p) = v;

	/* ok */
	return 1;
}

/* */
static int set_flag(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	/* enable */
	*((int *)p) = 1;

	/* ok */
	return 1;
}

/* */
static int reverse_flag(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	*((int *)p) = ! *((int *)p);

	/* ok */
	return 1;
}

/* */
int show_help(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	printf(msg_usage,
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_TOFILL],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_DRIVER_1],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_DRIVER_2A],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_DRIVER_2B],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_ROW_INDEX],
						driver1_tolerance_min,
						driver1_tolerance_max,
						driver2a_tolerance_min,
						driver2b_tolerance_min,
						rows_min
	);

	/* must return error */
	return 0;
}

/* added on January 17, 2018 */
void show_tolerances(void) {
	printf("%s tolerance%s= %g"
				, tokens[GF_DRIVER_1]
				, IS_INVALID_VALUE(driver1_tolerance_max) ? "" : "s "
				, driver1_tolerance_min
	);
	if ( ! IS_INVALID_VALUE(driver1_tolerance_max) ) {
		printf(", %g", driver1_tolerance_max);
	}
	puts("");

	printf("%s tolerance%s= %g"
				, tokens[GF_DRIVER_2A]
				, IS_INVALID_VALUE(driver2a_tolerance_max) ? "" : "s "
				, driver2a_tolerance_min
	);
	if ( ! IS_INVALID_VALUE(driver2a_tolerance_max) ) {
		printf(", %g", driver2a_tolerance_max);
	}
	puts("");

	printf("%s tolerance%s= %g"
				, tokens[GF_DRIVER_2B]
				, IS_INVALID_VALUE(driver2b_tolerance_max) ? "" : "s "
				, driver2b_tolerance_min
	);
	if ( ! IS_INVALID_VALUE(driver2b_tolerance_max) ) {
		printf(", %g", driver2b_tolerance_max);
	}
	puts("\n");
}

/* */
int main(int argc, char *argv[]) {
	int i;
	int y;
	int z;
	int j;
	int k;
	int w;
	int error;
	int rows_count;
	int files_processed_count;
	int files_not_processed_count;
	int total_files_count;
	int no_gaps_filled_count;
	int hat;
	int debug;
	char buffer[BUFFER_SIZE];
	char filename[FILENAME_SIZE];
	char debug_name[FILENAME_SIZE];
	char *p;
	char *string;
	FILE *f;
	ROW *rows;
	GF_ROW *gf_rows;

	TOLERANCE tol1 = { "driver1", &driver1_tolerance_min, &driver1_tolerance_max };
	TOLERANCE tol2a = { "driver2a", &driver2a_tolerance_min, &driver2a_tolerance_max };
	TOLERANCE tol2b = { "driver2b", &driver2b_tolerance_min, &driver2b_tolerance_max };

	const ARGUMENT args[] = {
		{ "input", get_input_path, NULL },
		{ "output", get_output_path, NULL },
		{ "hourly", set_hourly_dataset, NULL },
		{ "tofill", set_token, (void *)GF_TOFILL },
		{ "driver1", set_token, (void *)GF_DRIVER_1 },
		{ "driver2a", set_token, (void *)GF_DRIVER_2A },		
		{ "driver2b", set_token, (void *)GF_DRIVER_2B },
		{ "date", set_token, (void *)GF_ROW_INDEX },
		{ "tdriver1", set_driver_tolerances, &tol1 },
		{ "tdriver2a", set_driver_tolerances, &tol2a },
		{ "tdriver2b", set_driver_tolerances, &tol2b },
		{ "rows_min", set_int_value, &rows_min },
		{ "nohat", reverse_flag, &hat },
		{ "debug", reverse_flag, &debug },
		{ "rows_min", set_int_value, &rows_min },

		/* v3.0 */
		{ "symmean", reverse_flag, &sym_mean },
		{ "driver1_qc_col", set_int_value, &driver1_qc_col },
		{ "driver2a_qc_col", set_int_value, &driver2a_qc_col },
		{ "driver2b_qc_col", set_int_value, &driver2b_qc_col },
		{ "driver1_qc_thrs", set_prec_value, &driver1_qc_thrs },
		{ "driver2a_qc_thrs", set_prec_value, &driver2a_qc_thrs },
		{ "driver2b_qc_thrs", set_prec_value, &driver2b_qc_thrs },

		{ "h", show_help, NULL },
		{ "?", show_help, NULL },
		{ "help", show_help, NULL },
	};
	
	/* show banner */
	puts(banner);

	/* register atexit */
	if ( -1 == atexit(clean_up) ) {
		puts(err_unable_to_register_atexit);
		return 1;
	}

	/* reset */
	for ( i = 0; i < GF_TOKENS; i++ ) {
		custom_tokens[i] = 0;
	}

	/* defaults */
	debug = 0;
	hat = 1;

	/* v2.04b */
	sym_mean = 0;

	/* parse arguments */
	if ( !parse_arguments(argc, argv, args, SIZEOF_ARRAY(args)) ) {
		return 1;
	}

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

	/* get files */
	files = get_files(program_path, input_path, &files_count, &error);
	if ( error ) {
		return 1;
	}

	/* show paths */
	printf(msg_input_path, input_path);
	printf(msg_output_path, output_path);

	/* show rows min */
	if ( (rows_min < GF_ROWS_MIN_MIN) || (rows_min > GF_ROWS_MIN_MAX) ) {
		printf(err_rows_min, GF_ROWS_MIN_MIN, GF_ROWS_MIN_MAX, rows_min, GF_ROWS_MIN);
		rows_min = GF_ROWS_MIN;
	} else {
		printf(msg_rows_min, rows_min);
	}

	/* assign columns names */
	for ( i = 0; i < GF_TOKENS; i++ ) {
		if ( !custom_tokens[i] ) {
			strncpy(tokens[i], def_tokens[i], GF_TOKEN_LENGTH_MAX-1);
			tokens[i][GF_TOKEN_LENGTH_MAX-1] = '\0';
		}
	}

	/* show tolerances */
	show_tolerances();

	/* reset */
	files_processed_count = 0;
	files_not_processed_count = 0;
	total_files_count = 0;

	/* loop for searching file */
	for ( z = 0; z < files_count; z++) {
		/* inc total files founded */
		total_files_count += files[z].count;

		/* processing and create output filename */
		filename[0] = '\0';
		for ( i = 0; i < files[z].count; i++ ) {
			if ( !i ) {
				printf(msg_import_dataset, files[z].list[i].name, (files[z].count>1) ? "+" : "...");
			} else {
				printf(files[z].list[i].name);
				if ( files[z].count-1 == i ) {
					printf("...");
				} else {
					printf("+");
				}
			}
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
			if ( !string_concat(filename, string, FILENAME_MAX) && '\0' == filename[0]) {
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

			/* v2.04 */
			if ( sym_mean )
			{
				if ( !string_concat(filename, "sym_mean_", FILENAME_MAX) && '\0' == filename[0]) {
					puts(err_unable_create_output_filename);
					files_not_processed_count += files[z].count;
					free(string);
					continue;
				}
			}

			/* free memory */
			free(string);
		}

		/* import dataset */
		rows = import_dataset(files[z].list, files[z].count, &rows_count); 
		if ( !rows ) {
			free(years);
			files_not_processed_count += files[z].count;
			continue;
		}

		if ( debug ) {
			int len = strlen(files[z].list->name);
			char* p = strrchr(files[z].list->name, '.');
			if ( p ) {
				len -= strlen(p);
			}
			sprintf(debug_name, "%.*s", len, files[z].list->name);
		}

		/* gf */
		gf_rows = gf_mds(	rows->value,
							sizeof(ROW),
							rows_count,
							GF_REQUIRED_DATASET_VALUES,
							timeres,
							driver1_tolerance_min,
							driver1_tolerance_max,
							driver2a_tolerance_min,
							driver2a_tolerance_max,
							driver2b_tolerance_min,
							driver2b_tolerance_max,
							GF_TOFILL,
							GF_DRIVER_1,
							GF_DRIVER_2A,
							GF_DRIVER_2B,
							driver1_qc_col,
							driver2a_qc_col,
							driver2b_qc_col,
							driver1_qc_thrs,
							driver2a_qc_thrs,
							driver2b_qc_thrs,
							rows_min,
							hat,
							-1,
							-1,
							&no_gaps_filled_count,
							sym_mean,
							max_mdv_win,
							debug,
							debug_name,
							years[z]
		);
		if ( !gf_rows ) {
			free(years);
			free(rows);
			files_not_processed_count += files[z].count;
			continue;
		}

		/* create output file */
		sprintf(buffer, gap_file, output_path, filename);
		f = fopen(buffer, "w");
		if ( !f ) {
			puts(err_unable_create_gap_file);
			free(years);
			free(rows);
			files_not_processed_count += files[z].count;
			continue;
		}

		/* write header */
		/* v2.04b */
		if ( sym_mean ) {
			fprintf(f, gap_header_sym_mean, tokens[GF_ROW_INDEX], tokens[GF_TOFILL]);
		} else {
			fprintf(f, gap_header, tokens[GF_ROW_INDEX], tokens[GF_TOFILL]);
		}
		
		/* write values */
		for ( y = 0; y < files[z].count; y++ ) {
			y = 0;
			w = 0;
			j = get_rows_count_by_timeres(timeres, years[y]);
			
			/* */
			for ( i = 0; i < rows_count; i++ ) {
				if ( i == j ) {
					++y;
					k = get_rows_count_by_timeres(timeres, years[y]);
					j += k;
					k = get_rows_count_by_timeres(timeres,years[y-1]);
					w += k;
				}
				/* v2.04b */
				if ( sym_mean ) {
					fprintf(f, gap_format_sym_mean,
											timestamp_end_by_row_s(i-w, years[y], timeres),
											rows[i].value[GF_TOFILL],
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? rows[i].value[GF_TOFILL] : gf_rows[i].filled,
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality,
											gf_rows[i].filled,									
											gf_rows[i].filled_sym_mean,
											gf_rows[i].mean_above,
											gf_rows[i].n_above,
											gf_rows[i].mean_below,
											gf_rows[i].n_below,
											gf_rows[i].samples_count,
											gf_rows[i].stddev,
											gf_rows[i].method,
											gf_rows[i].quality,
											gf_rows[i].time_window
					);
				} else {
					fprintf(f, gap_format,
											timestamp_end_by_row_s(i-w, years[y], timeres),
											rows[i].value[GF_TOFILL],
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? rows[i].value[GF_TOFILL] : gf_rows[i].filled,
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality,
											gf_rows[i].filled,									
											gf_rows[i].samples_count,
											gf_rows[i].stddev,
											gf_rows[i].method,
											gf_rows[i].quality,
											gf_rows[i].time_window
					);
				}
			}
		}

		/* close file */
		fclose(f);

		/* free memory */
		free(gf_rows);
		free(years);
		free(rows);
		
		/* increment processed files count */
		files_processed_count += files[z].count;

		/* */
		if ( !no_gaps_filled_count ) {
			puts(msg_ok);
		} else {
			printf(msg_ok_with_gaps_unfilled, no_gaps_filled_count);
		}
	}

	/* summary */
	printf(msg_summary,
						total_files_count,
						total_files_count > 1 ? "s" : "",
						files_processed_count,
						files_not_processed_count
	);

	return 0;
}
