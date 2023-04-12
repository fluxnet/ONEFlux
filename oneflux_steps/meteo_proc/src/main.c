/*
	main.c

	This file is part of the meteo_proc step of processing.
	It is responsible for the meteorological data gapfilling
	including the merging with the downscaled meteo data and
	the temporal aggregation at different time resolutions.

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
#define QC_AUTO_PATH		"qc_auto"
#define ERA_PATH			"era"

/* global variables */
char *program_path = NULL;									/* mandatory */
char *qc_auto_files_path = NULL;							/* mandatory */
char *era_files_path = NULL;								/* mandatory */
char *output_files_path = NULL;								/* mandatory */
char folder_delimiter_str[2];                               /* used to get folder delimiter string from FOLDER_DELIMITER char in common.h*/

PREC swin_tolerance_min = GF_DRIVER_1_TOLERANCE_MIN;			/* see common.h */
PREC swin_tolerance_max = GF_DRIVER_1_TOLERANCE_MAX;			/* see common.h */
PREC ta_tolerance = GF_DRIVER_2A_TOLERANCE_MIN;					/* see common.h */
PREC vpd_tolerance = GF_DRIVER_2B_TOLERANCE_MIN;				/* see common.h */

/* strings */
static const char banner[] =	"\nmeteo_proc "PROGRAM_VERSION"\n"
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
static const char err_unable_open_output_path[] = "unable to open output path.\n";
static const char msg_usage[] =	"How to use: meteo_proc parameter\n\n"
								"  parameters:\n\n"
								"    -qc_auto_path=qc_auto_files_folder -> set input files folder\n"
								"             if not specified, files will be searched into \"%s\" folder\n\n"
								"    -era_path=era_files_folder -> set era files folder\n"
								"             if not specified, files will be searched into \"%s\" folder\n\n"
								"    -output_path=output_files_folder -> set output files folder\n"
								"             if not specified, files will be created into executable folder\n\n"
								"    -h -> show this help\n";

/* */
static int set_path(char *arg, char *param, void *p) {
	if ( !param ) {
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
static int show_help(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	/* */
	printf(msg_usage,	QC_AUTO_PATH,
						ERA_PATH
	);

	/* must return error */
	return 0;
}

/* */
static void clean_up(void) {
	free(program_path);
	free(qc_auto_files_path);
	free(era_files_path);
	free(output_files_path);
	check_memory_leak();
}

/* */
int main(int argc, char *argv[]) {
	int i;
	DATASET *datasets;
	int datasets_count;
	const ARGUMENT args[] = {
		{ "qc_auto_path", set_path, &qc_auto_files_path },
		{ "era_path", set_path, &era_files_path },
		{ "output_path", set_path, &output_files_path },
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
	if ( !qc_auto_files_path ) {
		for ( i = 0; QC_AUTO_PATH[i]; i++ ); i += 2;
		qc_auto_files_path = malloc(i*sizeof*qc_auto_files_path);
		if ( !qc_auto_files_path ) {
			puts(err_out_of_memory);
			return 1;
		}
		sprintf(qc_auto_files_path, "%s%c", QC_AUTO_PATH, FOLDER_DELIMITER);
	}

	/* get era path */
	if ( !era_files_path ) {
		for ( i = 0; ERA_PATH[i]; i++ ); i += 2;
		era_files_path = malloc(i*sizeof*era_files_path);
		if ( !era_files_path ) {
			puts(err_out_of_memory);
			return 1;
		}
		sprintf(era_files_path, "%s%c", ERA_PATH, FOLDER_DELIMITER);
	}

	/* output path specified ? */
	if ( !output_files_path ) {
		output_files_path = string_copy(program_path);
		if ( !output_files_path ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* check output path */
	if ( !path_exists(output_files_path) ) {
		/* trying to create output path */
		if ( !create_dir(output_files_path) ) {
			printf("unable to create output folder: %s\n", output_files_path);
			return 1;
		}
	}

	/* get datasets */
	datasets = get_datasets(&datasets_count);
	if ( !datasets ) {
		return 1;
	}

	/* compute datasets */
	if ( !compute_datasets(datasets, datasets_count) ) {
		free_datasets(datasets, datasets_count);
		return 1;
	}

	/* show datasets */
	printf("%d dataset%s found%s.\n",	datasets_count,
										(datasets_count>1) ? "s" : "",
										(datasets_count>1) ? "ed" : "");
	/* */
	return 0;
}
