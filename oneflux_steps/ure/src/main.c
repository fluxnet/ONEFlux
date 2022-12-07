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
#define PROGRAM_VERSION			"v1.01"
#define BUFFER_SIZE				1024

/* global variables */
char *program_path = NULL;		/* mandatory */
char *input_path = NULL;		/* mandatory */
char *output_path = NULL;		/* mandatory */
const char *types_suffix[TYPES_SUFFIX] = { "GPP", "RECO" };
const char *authors_suffix[AUTHORS_SUFFIX] = { "NT", "DT", "SR" };

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
static char msg_usage[] =	"How to use: ure parameter\n\n"
							"  parameters:\n\n"
							"    -input_path=filename or path to be processed (optional)\n"
							"    -output_path=path where result files are created (optional)\n"
							"    -h -> show this help\n";
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
	puts(msg_usage);

	/* must return error */
	return 0;
}

static void clean_up(void) {
	free(output_path);
	free(input_path);
	free(program_path);

	check_memory_leak();
}

/* */
int main(int argc, char *argv[]) {
	int author;
	int type;
	DATASET *datasets;
	int datasets_count;
	const ARGUMENT args[] = {
		{ "input_path", set_path, &input_path },
		{ "output_path", set_path, &output_path },
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
	program_path = get_current_directory();
	if ( !program_path ) {
		puts(err_unable_get_current_directory);
		return 1;
	}

	/* parse arguments */
	if ( !parse_arguments(argc, argv, args, SIZEOF_ARRAY(args)) ) {
		return 1;
	}

	/* get input path */
	if ( !input_path ) {
		input_path = string_copy(program_path);
		if ( !input_path ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* get output path */
	if ( output_path ) {
		if ( !path_exists(output_path) ) {
			if ( !create_dir(output_path) ) {
				printf("unable to create output path: %s\n", output_path);
				return 1;
			}
		}
	} else {
		output_path = string_copy(program_path);
		if ( !output_path ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* show paths */
	printf("input path = %s\n", input_path);
	printf("output path = %s\n", output_path);

	/* get datasets */
	for ( author = 0; author < AUTHORS_SUFFIX; author++ ) {
		for ( type = 0; type < TYPES_SUFFIX; type++ ) {
			printf("\nprocessing %s (%s) files...", types_suffix[type],  authors_suffix[author]);
			datasets = get_datasets(input_path, author, type, &datasets_count);
			if ( !datasets ) {
				continue;
			}
			printf("%d dataset%s found%s:\n",	datasets_count,
												(datasets_count>1) ? "s" : "",
												(datasets_count>1) ? "ed" : "");
			/* compute datasets */
			if ( AUTHOR_SR == author ) {
				compute_sr_datasets(datasets, datasets_count, author, type);
			} else {
				compute_datasets(datasets, datasets_count, author, type);
			}
			free_datasets(datasets, datasets_count);
		}
	}
	puts("");

	/* */
	return 0;
}
