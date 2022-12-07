/*
	main.c

	This file is part of the energy_proc step of processing.
	It is responsible for the gapfilling of the sensible heat
	and latent heat fluxes and the calculation of the energy
	balance closure to create a version of H and LE with the 
	closure forced (bowen ration method). It also performs the
	temporal aggregation at different time resolutions.

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "dataset.h"
#include "types.h"
#include "../../common/common.h"
#include "../../compiler.h"

/* constants */
#define PROGRAM_VERSION		"v1.01"
#define BUFFER_SIZE			1024

/* global variables */
char *program_path = NULL;
char *input_path = NULL;									/* mandatory */
char *output_path = NULL;									/* mandatory */
int debug = 0;												/* mandatory */
int multi = 0;												/* mandatory */
int no_rand_unc = 0;										/* mandatory */
char folder_delimiter_str[2];               /* used to get folder delimiter string from FOLDER_DELIMITER char in common.h*/
int window_size = WINDOW_SIZE;								/* see types.h */
int window_size_daily = WINDOW_SIZE_DAILY;					/* see types.h */
int window_size_weekly = WINDOW_SIZE_WEEKLY;				/* see types.h */
int window_size_monthly = WINDOW_SIZE_MONTHLY;				/* see types.h */
int samples_count = SAMPLES_COUNT;							/* see types.h */
int window_size_method_2_3_hh = WINDOW_SIZE_METHOD_2_3_HH;	/* see types.h */
int window_size_method_2_3_dd = WINDOW_SIZE_METHOD_2_3_DD;	/* see types.h */
int qc_gf_threshold = QC_GF_THRESHOLD;						/* see types.h */

/* strings */
static const char banner[] =	"\nenergy_proc "PROGRAM_VERSION"\n"
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
static const char err_unable_to_convert_value_for[] = "unable to convert value \"%s\" for %s\n\n";
static const char err_unable_create_output_path[] = "unable to create output path: %s\n";
static const char err_bad_window_size[] = "warning: window size must be between %d and %d not %d. default values (%d) will be used.\n\n";
static const char err_window_size_not_by_2[] = "warning: window size must be a value divisible by 2. default values (%d) will be used.\n\n";
static const char err_bad_window_size_daily[] = "warning: window size per daily must be between %d and %d not %d. default values (%d) will be used.\n\n";
static const char err_window_size_not_by_2_daily[] = "warning: window size per daily must be a value divisible by 2. default values (%d) will be used.\n\n";
static const char err_bad_samples_count[] = "warning: samples count must be between %d and %d not %d. default values (%d) will be used.\n\n";
static const char msg_usage[] =	"How to use: energy_proc parameter\n\n"
								"  parameters:\n\n"
								"    -input_path=path where input files are searched (optional)\n"
								"    (if not specified the folder with the energy_proc.exe file is used)\n\n"
								"    -output_path=path where result files are created (optional)\n"
								"    (if not specified the folder with input file is used)\n\n"
								"    -window_size=N -> size of window (default: %d)\n\n"
								"    -samples_count=N -> value of samples (default: %d)\n\n"
								"    -window_size_daily=N -> size of window per daily (default: %d)\n\n"
								"    -debug -> save to file extra stuff for debug purposes\n\n"
								"    -no_rand_unc -> disable random uncertainty computation ( default is off )\n\n"
								"    -multi -> save imported datasets to one big file and exit\n\n"
								"    -qc_gf_thrs=N -> gapfilling qc threshold ( default is %d )\n\n"
								"    -h -> show this help\n\n";

/* */
static int set_path(char *arg, char *param, void *p) {
	if ( ! param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	if ( *(char **)p ) {
		printf(err_path_already_specified, arg, *(char **)p);
		return 0;
	} else {
		int i;
		int y;
		int add_program_path;
		int no_last_backslash;

		/* */
		add_program_path = 0;

		/* get length */
		for ( i = 0; param[i]; i++ );
		for ( y = 0; program_path[y]; y++ );

		/* check for unit e.g. c: */
		if ( i <= 2 ) {
			add_program_path = 1;
		} else if ( (':' != param[1])  ) {
			add_program_path = 1;
		}

		no_last_backslash = !(param[i-1] == FOLDER_DELIMITER);

		*(char **)p = malloc(i + (add_program_path ? y : 0) + no_last_backslash + 1);
		if ( !(*(char **)p) ) {
			puts(err_out_of_memory);
			return 0;
		}
		**(char **)p = '\0';

		if ( add_program_path ) {
			strcpy(*(char **)p, program_path);
		}
		strcat(*(char **)p, param);
		
		if ( no_last_backslash ) {
			folder_delimiter_str[0] = FOLDER_DELIMITER;
			folder_delimiter_str[1] = '\0';
			strcat(*(char **)p, folder_delimiter_str);
		}
	}
	
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
static int show_help(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	/* */
	printf(msg_usage,	WINDOW_SIZE,
						SAMPLES_COUNT,
						WINDOW_SIZE_DAILY,
						QC_GF_THRESHOLD
	);

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
	int i;
	DATASET *datasets;
	int datasets_count;
	const ARGUMENT args[] = {
		{ "input_path", set_path, &input_path },
		{ "output_path", set_path, &output_path },
		{ "window_size", set_int_value, &window_size },
		{ "window_size_daily", set_int_value, &window_size_daily },
		{ "samples_count", set_int_value, &samples_count },
		{ "no_rand_unc", set_flag, &no_rand_unc }, 
		{ "debug", set_flag, &debug },
		{ "multi", set_flag, &multi },
		{ "qc_gf_thrs", set_int_value, &qc_gf_threshold },
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

	/* for SWAP on diff */
	init_random_seed();

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

	/* check input path */
	if ( !input_path ) {
		input_path = get_current_directory();
		if ( !input_path ) {
			puts(err_unable_get_current_directory);
			return 1;
		}
	}

	/* output path specified ? */
	if ( output_path ) {
		/* check if output path exists */
		if ( ! path_exists(output_path) ) {
			if ( ! create_dir(output_path) ) {
				printf(err_unable_create_output_path, output_path);
				return 1;
			}
		}
	} else {
		output_path = string_copy(program_path);
		if ( ! output_path ) {
			puts(err_unable_get_current_directory);
			return 1;
		}
	}

	/* check window size */
	if ( window_size < MIN_WINDOW_SIZE || window_size > MAX_WINDOW_SIZE ) {
		printf(err_bad_window_size, MIN_WINDOW_SIZE, MAX_WINDOW_SIZE, window_size, WINDOW_SIZE);
		window_size = WINDOW_SIZE;
	}
	if ( window_size & 1 ) {
		printf(err_window_size_not_by_2, WINDOW_SIZE);
		window_size = WINDOW_SIZE;
	}

	/* check window size daily */
	if ( window_size_daily < MIN_WINDOW_SIZE || window_size_daily > MAX_WINDOW_SIZE_DAILY ) {
		printf(err_bad_window_size_daily, MIN_WINDOW_SIZE, MAX_WINDOW_SIZE_DAILY, window_size_daily, WINDOW_SIZE_DAILY);
		window_size_daily = WINDOW_SIZE_DAILY;
	}
	if ( window_size_daily & 1 ) {
		printf(err_window_size_not_by_2_daily, WINDOW_SIZE_DAILY);
		window_size_daily = WINDOW_SIZE_DAILY;
	}

	/* check samples count */
	if ( samples_count < MIN_SAMPLES_COUNT || samples_count > MAX_SAMPLES_COUNT ) {
		printf(err_bad_samples_count, MIN_SAMPLES_COUNT, MAX_SAMPLES_COUNT, samples_count, SAMPLES_COUNT);
		samples_count = SAMPLES_COUNT;
	}

	/* get datasets */
	datasets = get_datasets(input_path, "*.csv", &datasets_count);
	if ( !datasets ) {
		return 1;
	}
	
	/* compute datasets */
	if ( !compute_datasets(datasets, datasets_count) ) {
		free_datasets(datasets, datasets_count);
		return 1;
	}

	/* show datasets */
	printf("%d site%s found%s:\n", datasets_count,
								(datasets_count>1) ? "s" : "",
								(datasets_count>1) ? "ed" : "");
	for ( i = 0; i < datasets_count; i++ ) {
		printf("-- %s (%d year%s)\n",	datasets[i].details->site,
										datasets[i].years_count,
										(datasets[i].years_count>1) ? "s" : "");
	}

	/* free memory */
	free_datasets(datasets, datasets_count);

	/* */
	return 0;
}
