/*
	main.c

	This file is part of the ure step of processing.
	It is responsible for calculation and extraction of the NEE,
	GPP and RECO uncertainties and reference values starting
	from the different realizations created by the nee_proc tool.

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "dataset.h"
#include "types.h"
#include "../../common/common.h"
#include "../../compiler.h"

/* constants */
#define PROGRAM_VERSION					"v1.02"
#define BUFFER_SIZE						1024

/* v1.02 */
/*
	minimum amount of valid data in the 40 percentiles to be used in the MEF.
	it is calculated respect to the percentile with the largest number of valid data,
	if below the threshold the percentile is excluded.
*/
#define VALID_DATA_COUNT_DEFAULT		90

/* v1.02 */
/*
	minimum number of 40 percentiles with valid data to return GPP and RECO products.
	if below the threshold no results are produced for the flux processed.
*/
#define VALID_PERC_COUNT_DEFAULT		10

/* v1.02 */
/* min number of the 40 percentiles to proceed to the 7 product percentiles extraction. */
#define MIN7PERC_COUNT_DEFAULT			30

/* v1.02 */
/*
	min number of the 40 percentiles to proceed to the extraction of three (instead of 7) percentiles (25%, 50% and 75%).
	above the min_7_perc_count all the 7 are extracted
*/
#define MIN3PERC_COUNT_DEFAULT			10

/* v1.02 */
#define FILE_BUF_DEFAULT_SIZE_IN_MB		20


/* global variables */
char *g_program_path = NULL;						/* mandatory */
char *g_input_path = NULL;							/* mandatory */
char *g_output_path = NULL;							/* mandatory */
/* v1.02 */
char* g_filter_path = NULL;							/* mandatory */
int g_debug = 0;									/* mandatory */
int g_no_internal_buf = 0;							/* mandatory */
int g_valid_data_count = VALID_DATA_COUNT_DEFAULT;	/* mandatory */
int g_valid_perc_count = VALID_PERC_COUNT_DEFAULT;	/* mandatory */
int g_min_7_perc_count = MIN7PERC_COUNT_DEFAULT;	/* mandatory */
int g_min_3_perc_count = MIN3PERC_COUNT_DEFAULT;	/* mandatory */
char *g_file_buf = NULL;							/* mandatory */
int g_file_buf_size = 0;							/* mandatory */

const char *types_suffix[TYPES_SUFFIX] = { "GPP", "RECO" };
const char *authors_suffix[AUTHORS_SUFFIX] = { "NT", "DT" };

/* strings */
static const char banner[] =	"\nure "PROGRAM_VERSION" - Uncertainty and References Extraction\n"
								"by Alessio Ribeca\n\n"
								"scientific contact: darpap at unitus dot it\n"
								"technical contact: a dot ribeca at unitus dot it\n\n"
								"DIBAF - University of Tuscia, Viterbo, Italy\n"
								"(builded on "__DATE__" at "__TIME__ " with "COMPILER")\n"
								"(use -h parameter for more information)\n";
static const char err_unable_to_register_atexit[] = "unable to register clean-up routine.\n";
static const char err_arg_needs_param[] = "%s parameter not specified.\n\n";
static const char err_arg_no_needs_param[] = "%s no needs parameter.\n\n";
static const char err_path_already_specified[] = "path already specified for %s: %s\n\n";
static const char err_unable_get_current_directory[] = "unable to retrieve current directory.\n";
static const char err_unable_convert_value_arg[] = "unable to convert value \"%s\" for %s.\n\n";
static char msg_usage[] =		"How to use: ure parameter\n\n"
								"  parameters:\n\n"
								"    -input_path=filename or path to be processed (optional)\n"
								"    -output_path=path where result files are created (optional)\n"
								/* v1.02 */
								"    -valid_data_count = minimum amount of valid data in the 40 percentiles to be used in the MEF.\n"
								"                        it is calculated respect to the percentile with the largest number of valid data,\n"
								"                        if below the threshold the percentile is excluded. default is %d\n"
								"    -valid_perc_count = minimum number of 40 percentiles with valid data to return GPP and RECO products.\n"
								"                        if below the threshold no results are produced for the flux processed. default is %d\n"
								"    -min_7_perc_count = min number of the 40 percentiles to proceed to the 7 product percentiles extraction. default is %d\n"
								"    -min_3_perc_count = min number of the 40 percentiles to proceed to the extraction of three (instead of 7) percentiles (25%, 50% and 75%).\n"
								"                        above the min_7_perc_count all the 7 are extracted. default is %d\n"
								"    -debug -> save to file extra stuff for debug purposes\n"

								"    -h -> show this help\n\n";

/* v1.02 */
int set_int_value(char *arg, char *param, void *p) {
	int error;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	/* convert param */
	*(int *)p = convert_string_to_int(param, &error);
	if ( error ) {
		printf(err_unable_convert_value_arg, param, arg);
		return 0;
	}

	/* ok */
	return 1;
}

/* v1.02 */
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
static int set_path(char *arg, char *param, void *p) {
	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	*(char **)p = string_copy(param);
	if ( !(*(char **)p) ) {
		puts(err_out_of_memory);
		return 0;
	}

	return 1;
}

/* */
static int show_help(char *arg, char *param, void *p) {
	printf(msg_usage, g_valid_data_count, g_valid_perc_count
					, g_min_7_perc_count, g_min_3_perc_count
	);

	/* must return error */
	return 0;
}

static void clean_up(void) {
	free(g_output_path);
	free(g_input_path);
	free(g_program_path);

	check_memory_leak();
}

/* */
int main(int argc, char *argv[]) {
	int author;
	int type;
	DATASET *datasets;
	int datasets_count;
	const ARGUMENT args[] = {
		{ "input_path", set_path, &g_input_path },
		{ "output_path", set_path, &g_output_path },

		/* v1.02 */
		{ "filter_path", set_path, &g_filter_path },
		{ "valid_data_count", set_int_value, &g_valid_data_count },
		{ "valid_perc_count", set_int_value, &g_valid_perc_count },
		{ "min_7_perc_count", set_int_value, &g_min_7_perc_count },
		{ "min_3_perc_count", set_int_value, &g_min_3_perc_count },
		{ "debug", set_flag, &g_debug },
		/* hidden */
		{ "no_internal_buf", set_flag, &g_no_internal_buf },

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

	/* get program path */
	g_program_path = get_current_directory();
	if ( !g_program_path ) {
		puts(err_unable_get_current_directory);
		return 1;
	}

	/* parse arguments */
	if ( !parse_arguments(argc, argv, args, SIZEOF_ARRAY(args)) ) {
		return 1;
	}

	/* get input path */
	if ( !g_input_path ) {
		g_input_path = string_copy(g_program_path);
		if ( !g_input_path ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* get output path */
	if ( g_output_path ) {
		if ( !path_exists(g_output_path) ) {
			if ( !create_dir(g_output_path) ) {
				printf("unable to create output path: %s\n", g_output_path);
				return 1;
			}
		}
	} else {
		g_output_path = string_copy(g_program_path);
		if ( !g_output_path ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* v1.02 */
	if ( ! g_filter_path ) {
		g_filter_path = string_copy(g_program_path);
		if ( !g_filter_path ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* show paths */
	printf("input path = %s\n", g_input_path);
	printf("output path = %s\n", g_output_path);

	/* v1.02 */
	printf("valid data count = %d%%", g_valid_data_count);
	if ( (g_valid_data_count <= 0) || (g_valid_data_count > 100) ) {
		g_valid_data_count = VALID_DATA_COUNT_DEFAULT;
		printf(". invalid, range is 1-100%%, set to default: %d)", g_valid_data_count);
	}
	puts("");
	printf("valid percentiles count = %d", g_valid_perc_count);
	if ( (g_valid_perc_count <= 0) || (g_valid_perc_count >= PERCENTILES_COUNT_2) ) {
		g_valid_perc_count = VALID_PERC_COUNT_DEFAULT;
		printf(". invalid, range is 1-%d, set to default: %d)", PERCENTILES_COUNT_2-1, g_valid_perc_count);
	}
	puts("");
	printf("min_7_perc_count count = %d", g_min_7_perc_count);
	if ( (g_min_7_perc_count <= 1) || (g_min_7_perc_count >= PERCENTILES_COUNT_2) ) {
		g_min_7_perc_count = MIN7PERC_COUNT_DEFAULT;
		printf(". invalid, range is 2-%d, set to default: %d)", PERCENTILES_COUNT_2-1, g_min_7_perc_count);
	}
	puts("");
	printf("min_3_perc_count count = %d", g_min_3_perc_count);
	if ( (g_min_3_perc_count <= 0) || (g_min_3_perc_count >= g_min_7_perc_count) ) {
		if ( g_min_7_perc_count < MIN7PERC_COUNT_DEFAULT ) {
			g_min_3_perc_count = g_min_7_perc_count - 1;
		} else {
			g_min_3_perc_count = MIN3PERC_COUNT_DEFAULT;
		}
		printf(". invalid, range is 1-%d, set to default: %d)", g_min_7_perc_count, g_min_3_perc_count);
	}
	puts("");

	/* v1.02 */
	/* alloc memory for file buffer */
	if ( ! g_no_internal_buf ) {
		g_file_buf_size = FILE_BUF_DEFAULT_SIZE_IN_MB << 20; /* convert to MB */
		g_file_buf = malloc(g_file_buf_size*sizeof*g_file_buf);
		if ( !g_file_buf  ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* get datasets */
	for ( author = 0; author < AUTHORS_SUFFIX; author++ ) {
		for ( type = 0; type < TYPES_SUFFIX; type++ ) {
			printf("\nprocessing %s (%s) files...", types_suffix[type],  authors_suffix[author]);
			datasets = get_datasets(g_input_path, author, type, &datasets_count);
			if ( !datasets ) {
				continue;
			}
			printf("%d dataset%s found:\n",	datasets_count, (datasets_count>1) ? "s" : "");

			compute_datasets(datasets, datasets_count, author, type);

			free_datasets(datasets, datasets_count);
		}
	}
	puts("");

	if ( ! g_no_internal_buf ) {
		free(g_file_buf);
	}

	/* */
	return 0;
}
