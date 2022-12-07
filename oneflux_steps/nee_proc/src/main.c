/*
	main.c

	This file is part of the nee_proc step of processing.
	It is responsible for the ustar filtering and gapfilling
	of the nee using an ensamble of ustar thresholds. It also
	performs the temporal aggregation at different time
	resolutions.

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
#define PROGRAM_VERSION			"v1.01"
#define BUFFER_SIZE				1024
#define QC_AUTO_PATH			"qc_auto"
#define USTAR_MP_PATH			"ustar_mp"
#define USTAR_CP_PATH			"ustar_cp"
#define METEO_PATH				"meteo"

/* global variables */
char *program_path = NULL;
char *qc_auto_files_path = NULL;			/* mandatory */
char *ustar_mp_files_path = NULL;			/* mandatory */
char *ustar_cp_files_path = NULL;			/* mandatory */
char *meteo_files_path = NULL;				/* mandatory */
char *output_files_path = NULL;				/* mandatory */
char folder_delimiter_str[2];               /* used to get folder delimiter string from FOLDER_DELIMITER char in common.h*/
int no_rand_unc = 0;						/* default is off */
int compute_nee_flags = 0;					/* default if off */
int use_met_gf = 0;							/* default is off */
int mef_save = 0;							/* default is off */
int percentiles_save = 0;					/* default is off */
int qc_gf_threshold = QC_GF_THRESHOLD;		/* see types.h */

/* strings */
static const char banner[] =	"\nnee_proc "PROGRAM_VERSION"\n"
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
static char msg_usage[] =	"How to use: nee_proc parameter\n\n"
							"  parameters:\n\n"
							"    -qc_auto_path=qc_auto_files_folder -> set input files folder\n"
							"             if not specified, files will be searched into \"%s\" folder\n\n"
							"    -ustar_mp_path=ustar_mp_files_folder -> set ustar mp files folder\n"
							"             if not specified, files will be searched into \"%s\" folder\n\n"
							"    -ustar_cp_path=ustar_cp_files_folder -> set ustar cp files folder\n"
							"             if not specified, files will be searched into \"%s\" folder\n\n"
							"    -meteo_path=meteo_files_folder -> set meteo files folder\n"
							"             if not specified, files will be searched into \"%s\" folder\n\n"
							"    -output_path=output_files_folder -> set output files folder\n"
							"             if not specified, files will be created into executable folder\n\n"
							"    -use_met_gf -> enable imports of gf meteo fluxes ( default is off )\n\n"
							"    -no_rand_unc -> disable random uncertainty computation ( default is off )\n\n"
							"    -nee_flags -> save nee flags\n\n"
							"    -qc_gf_thrs=X -> set gapfilling qc threshold ( default is %d )\n\n"
							"    -mef -> save mef matrix\n\n"
							"    -percentiles -> save percentiles for DD,WW,MM,YY time resolution\n\n"
							"    -h -> show this help\n\n";

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
static int set_flag(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	/* enable */
	*(int *)p = 1;

	/* ok */
	return 1;
}

/* */
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

/* */
static int show_help(char *arg, char *param, void *p) {
	printf(msg_usage,
						QC_AUTO_PATH,
						USTAR_MP_PATH,
						USTAR_CP_PATH,
						METEO_PATH,
						qc_gf_threshold
	);
	/* must return error */
	return 0;
}

/* */
static void clean_up(void) {
	free(output_files_path);
	free(qc_auto_files_path);
	free(ustar_mp_files_path);
	free(ustar_cp_files_path);
	free(meteo_files_path);
	free(program_path);

	check_memory_leak();
}

/* */
int main(int argc, char *argv[]) {
	int i;
	DATASET *datasets;
	int datasets_count;
	const ARGUMENT args[] = {
		{ "qc_auto_path", set_path, &qc_auto_files_path },
		{ "ustar_mp_path", set_path, &ustar_mp_files_path },
		{ "ustar_cp_path", set_path, &ustar_cp_files_path },
		{ "meteo_path", set_path, &meteo_files_path },
		{ "output_path", set_path, &output_files_path },
		{ "use_met_gf", set_flag, &use_met_gf },
		{ "no_rand_unc", set_flag, &no_rand_unc },
		{ "nee_flags", set_flag, &compute_nee_flags },
		{ "mef", set_flag, &mef_save },
		{ "percentiles", set_flag, &percentiles_save },
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

	/* get ustar mp path */
	if ( !ustar_mp_files_path ) {
		for ( i = 0; USTAR_MP_PATH[i]; i++ ); i += 2;
		ustar_mp_files_path = malloc(i*sizeof*ustar_mp_files_path);
		if ( !ustar_mp_files_path ) {
			puts(err_out_of_memory);
			return 1;
		}
		sprintf(ustar_mp_files_path, "%s%c", USTAR_MP_PATH, FOLDER_DELIMITER);
	}

	/* get ustar cp path */
	if ( ! ustar_cp_files_path ) {
		for ( i = 0; USTAR_CP_PATH[i]; i++ ); i += 2;
		ustar_cp_files_path = malloc(i*sizeof*ustar_cp_files_path);
		if ( !ustar_cp_files_path ) {
			puts(err_out_of_memory);
			return 1;
		}
		sprintf(ustar_cp_files_path, "%s%c", USTAR_CP_PATH, FOLDER_DELIMITER);
	}

	/* get meteo path */
	if ( ! meteo_files_path ) {
		for ( i = 0; METEO_PATH[i]; i++ ); i += 2;
		meteo_files_path = malloc(i*sizeof*meteo_files_path);
		if ( !meteo_files_path ) {
			puts(err_out_of_memory);
			return 1;
		}
		sprintf(meteo_files_path, "%s%c", METEO_PATH, FOLDER_DELIMITER);
	}

	/* get output path */
	if ( ! output_files_path ) {
		output_files_path = string_copy(program_path);
		if ( !output_files_path ) {
			puts(err_out_of_memory);
			return 1;
		}
	}

	/* check output path */
	if ( ! path_exists(output_files_path) ) {
		if ( !create_dir(output_files_path) ) {
			printf("unable to create output path: %s\n", output_files_path);
			return 1;
		}
	}

	/* show paths */
	printf("qc_auto files path = %s\n", qc_auto_files_path);
	printf("ustar_mp files path = %s\n", ustar_mp_files_path);
	printf("ustar_cp files path = %s\n", ustar_cp_files_path);
	if ( use_met_gf ) {
		printf("meteo files path = %s\n\n", meteo_files_path);
	} else {
		puts("");
	}
	printf("output path = %s\n\n", ! string_compare_i(program_path, output_files_path) ? "current folder" : output_files_path);

	/* show qc gf threshold */
	if ( use_met_gf ) {
		printf("QC gf threshold = %d\n\n", qc_gf_threshold);
	}

	/* get datasets */
	datasets = get_datasets(qc_auto_files_path, &datasets_count);
	if ( ! datasets ) {
		return 1;
	}

	/* compute datasets */
	i = compute_datasets(datasets, datasets_count);
	free_datasets(datasets, datasets_count);
	if ( ! i ) {	
		return 1;
	}

	/* show datasets */
	printf("%d dataset%s found%s.\n",	datasets_count,
										(datasets_count>1) ? "s" : "",
										(datasets_count>1) ? "ed" : "");
	/* */
	return 0;
}
