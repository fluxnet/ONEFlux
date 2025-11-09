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

/*
   MDS rules

   on overwritting default values, ALL mds parameters must be specified!
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "dataset.h"
#include "types.h"
#include "mds_vars.h"
#include "defs.h"
#include "../../common/common.h"
#include "../../compiler.h"

/* constants */
#define PROGRAM_VERSION		"v1.02"
#define BUFFER_SIZE			1024
#define QC_AUTO_PATH		"qc_auto"
#define ERA_PATH			"era"

/* global variables */
char *program_path = NULL;									/* mandatory */
char *qc_auto_files_path = NULL;							/* mandatory */
char *era_files_path = NULL;								/* mandatory */
char *output_files_path = NULL;								/* mandatory */
char folder_delimiter_str[2];                               /* used to get folder delimiter string from FOLDER_DELIMITER char in common.h*/

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
static const char err_var_name_too_long[] = "mds var name too long.\n";
static const char msg_usage[] =	"How to use: meteo_proc parameter\n\n"
								"  parameters:\n\n"
								"    path:\n\n"
								"      -qc_auto_path=qc_auto_files_folder -> set input files folder\n"
								"               if not specified, files will be searched into \"%s\" folder\n\n"
								"      -era_path=era_files_folder -> set era files folder\n"
								"               if not specified, files will be searched into \"%s\" folder\n\n"
								"      -output_path=output_files_folder -> set output files folder\n"
								"               if not specified, files will be created into executable folder\n\n"
								"    mds:\n\n"
							#if 0
								"      -XXX_oor=min,max -> values of oor for XXX\n"
							#endif
								"      -XXX_driver1=YYY -> name of the main driver for XXX filling with MDS\n"
								"      -XXX_driver2a=YYY -> name of the first additional driver for XXX filling with MDS\n"
								"      -XXX_driver2b=YYY -> name of the second additional driver for XXX filling with MDS\n"
								"      -XXX_tdriver1=min[,max] -> set the tolerance values used to define similar conditions related to XXX_driver1\n"
								"      -XXX_tdriver2a=min[,max] -> set the tolerance values used to define similar conditions related to XXX_driver2a\n"
								"      -XXX_tdriver2b=min[,max] -> set the tolerance values used to define similar conditions related to XXX_driver2a\n\n"
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
	} else {
		printf(msg_usage, QC_AUTO_PATH, ERA_PATH);
	}

	/* must return error */
	return 0;
}

static int parse_mds(char *arg, char *param, void *p) {
	int ret = 0; /* defaults to err */	

	if ( !param || !param[0] ) {
		printf(err_arg_needs_param, arg);
	} else {
		/*
			get var name getting last occurency of '_' 
			'cause we can have var that has an underscore in the name
			e.g.: SW_IN
		*/
		char* pp = strrchr(arg, '_');
		if ( !pp ) {
			ret = -1; /* unknown argument */
		} else {
		#define VAR_MAX_LEN	15

			int i = pp - arg;
			if ( i > VAR_MAX_LEN ) {
				printf(err_var_name_too_long); 
			} else {
				char var[VAR_MAX_LEN+1] = { 0 };
				int index;
				int is_tolerance = 0;
				int is_oor = 0;
				
				strncpy(var, arg, i);

				/* skip underscore */
				++pp;

				/* check if var name is allowed, e.g. it is one of allowed */
				for ( i = 0; i < DEF_VARS_COUNT; ++i ) {
					if ( !string_compare_i(var, sz_defs[i]) ) {
						break;
					}
				}

				ret = (DEF_VARS_COUNT == i) ? -1 : 0;
				if ( ret != -1 ) {
				#if 0
					/* check for oor for main var */
					if ( ! string_compare_i(pp, "oor") ) {
						is_oor = 1;
						index = MDS_VAR_TO_FILL;
					}

					/* 
						1234567
						driver1

						7 is minimal accepted length of arg after var name
					*/
					else 
				#endif
						if ( strlen(pp) < 7 ) {
						ret = -1; /* unknown argument */
					} else {
						/* what we are parsing ? driver or tolerance ? */
						is_tolerance = ! string_n_compare_i(pp, "tdriver", 7);
						is_oor = ! string_n_compare_i(pp, "odriver", 7);
						if ( ! is_tolerance && ! is_oor ) {
							/* we must be sure that we have 'driver' as suffix */
							if ( string_n_compare_i(pp, "driver", 6) ) {
								is_tolerance = -1;
							}
						}
						if ( -1 == is_tolerance ) {
							ret = -1; /* unknown argument */
						} else {
							/* which index ? 6 is lenght of "driver" string */
							index = ! string_n_compare_i(pp+6+is_tolerance+is_oor, "1", 1);
							if ( !index ) {
								index = ! string_n_compare_i(pp+6+is_tolerance+is_oor, "2a", 2);
								if ( index ) {
									++index;
								} else  {
									index = ! string_n_compare_i(pp+6+is_tolerance+is_oor, "2b", 2);
									if ( index ) {
										index += 2;
									} else  {
										ret = -1; /* unknown argument */
									}
								}
							}
						}
					}

					if ( ret != -1 ) {
						const char* driver_name = NULL;
						int error = 0;
						PREC min = INVALID_VALUE;
						PREC max = INVALID_VALUE;

						const char err_unable_convert_tolerance[] = "unable to convert tolerance \"%s\" for %s.\n\n";
						const char err_unable_convert_oor[] = "unable to convert oor \"%s\" for %s.\n\n";
						const char err_driver_already_specified[] = "driver already specified: \"%s\" for %s.\n\n";
						const char err_oor_needs_min_and_max[] = "oor for %s needs 2 values. min and max.\n\n";

						if ( !is_tolerance && !is_oor ) {
							/* get driver name */
							driver_name = param;
						} else {
							pp = strchr(param, ',');
							if ( ! pp ) {
								if ( is_oor ) {
									printf(err_oor_needs_min_and_max, arg);
									error = 1;
									is_oor = 0; /* we disable to print error below */
								} else {
									/* get min */
									min = convert_string_to_prec(param, &error);
								}
							} else {
								*pp = '\0'; /* remove comma */
								min = convert_string_to_prec(param, &error);
								*pp = ','; /* re-add comma */
								if ( ! error ) {
									/* get max */
									++pp; /* skip comma */
									error = ! pp[0]; /* check for missing value */
									if ( ! error ) {
										max = convert_string_to_prec(pp, &error);
									}
								}
							}
						}

						if ( error ) {
							if ( is_tolerance ) {
								printf(err_unable_convert_tolerance, param, arg);
							} else if ( is_oor ) {
								printf(err_unable_convert_oor, param, arg);
							}
						} else {
							MDS_VARS* vars = p;

							/* check if we already have that var */
							for ( i = 0; i < vars->count; ++i ) {
								if (!string_compare_i(var, vars->vars[i].name[MDS_VAR_TO_FILL]) ) {
									break;
								}
							}

							if ( i == vars->count ) {
								MDS_VAR* vars_noleak = realloc(vars->vars, (vars->count+1)*sizeof*vars_noleak);
								if ( !vars_noleak ) {
									printf("%s for %s\n\n", err_out_of_memory, arg);
								} else {
									vars->vars = vars_noleak;
									memset(&vars->vars[vars->count], 0, sizeof(vars->vars[vars->count]));

									Mds_Var_Init(&vars->vars[vars->count]);
									++vars->count;
								}
							}

							ret = 1; /* ok...for now */

							/*
								err codes

								0 -> out of memory
								1 -> ok (no error)
								2 -> driver or tolerances already specified
							*/

							if ( ! vars->vars[i].name[MDS_VAR_TO_FILL] ) {
								vars->vars[i].name[MDS_VAR_TO_FILL] = string_copy(var);
								ret = vars->vars[i].name[MDS_VAR_TO_FILL] ? 1 : 0;
							}

							if ( 1 == ret ) {
								if ( !is_tolerance && !is_oor ) {
									if ( vars->vars[i].name[index] ) {
										ret = 2;
									} else {
										vars->vars[i].name[index] = string_copy(param);
										if ( !vars->vars[i].name[index] ) {
											ret = 0;
										}

									}
								} else {
									if (		(	is_tolerance && (!IS_INVALID_VALUE(vars->vars[i].tolerances[index][MDS_VAR_TOLERANCE_MIN])
													|| !IS_INVALID_VALUE(vars->vars[i].tolerances[index][MDS_VAR_TOLERANCE_MAX])))
												||
												(	is_oor && (!IS_INVALID_VALUE(vars->vars[i].oors[index][MDS_VAR_OOR_MIN])
													|| !IS_INVALID_VALUE(vars->vars[i].oors[index][MDS_VAR_OOR_MAX])))
									){
										ret = 2;
									} else if ( is_tolerance ) {
										vars->vars[i].tolerances[index][MDS_VAR_TOLERANCE_MIN] = min;
										vars->vars[i].tolerances[index][MDS_VAR_TOLERANCE_MAX] = max;
									} else { /* is_oor */
										vars->vars[i].oors[index][MDS_VAR_OOR_MIN] = min;
										vars->vars[i].oors[index][MDS_VAR_OOR_MAX] = max;
									}
								}
							}

							if ( ret != 1 ) {
								switch ( ret ) {
									case 0:
										printf("%s for %s\n\n", err_out_of_memory, arg);
									break;

									case 2:
										printf(err_driver_already_specified, param, arg);
									break;
								}

								/* return with valid values...0 or 1 */
								ret = 0;
							}
						}
					}
				}
			}

		#undef VAR_MAX_LEN
		}
	}

	return ret;
}

/* */
static void clean_up(void) {
	free(program_path);
	free(qc_auto_files_path);
	free(era_files_path);
	free(output_files_path);
	check_memory_leak();
}

static int get_digits_count(int v)
{
	return (int)floor(log10((float)v)+1);
}

static int setup_default_mds(MDS_VARS* vars) {
#define DEFAULT_TOLERANCES					\
	{										\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE,				\
		(PREC)GF_DRIVER_1_TOLERANCE_MIN,	\
		(PREC)GF_DRIVER_1_TOLERANCE_MAX,	\
		(PREC)GF_DRIVER_2A_TOLERANCE_MIN,	\
		(PREC)GF_DRIVER_2A_TOLERANCE_MAX,	\
		(PREC)GF_DRIVER_2B_TOLERANCE_MIN,	\
		(PREC)GF_DRIVER_2B_TOLERANCE_MAX	\
	}

#define DEFAULT_OOR							\
	{										\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE,				\
		(PREC)INVALID_VALUE					\
	}

	int ret = 0; /* defaults to err */

	MDS_VAR defs[] = {
		{ DEFAULT_TOLERANCES, DEFAULT_OOR, { TA_MET, -1, -1, -1 }, { sz_defs[TA_DEF_VAR], sz_defs[SW_IN_DEF_VAR], sz_defs[TA_DEF_VAR], sz_defs[VPD_DEF_VAR] } }
		, { DEFAULT_TOLERANCES, DEFAULT_OOR, { SW_IN_MET, -1, -1, -1 }, { sz_defs[SW_IN_DEF_VAR], sz_defs[SW_IN_DEF_VAR], sz_defs[TA_DEF_VAR], sz_defs[VPD_DEF_VAR] } }
		, { DEFAULT_TOLERANCES, DEFAULT_OOR, { LW_IN_MET, -1, -1, -1 }, { sz_defs[LW_IN_DEF_VAR], sz_defs[SW_IN_DEF_VAR], sz_defs[TA_DEF_VAR], sz_defs[VPD_DEF_VAR] } }
		, { DEFAULT_TOLERANCES, DEFAULT_OOR, { VPD_MET, -1, -1, -1 }, { sz_defs[VPD_DEF_VAR], sz_defs[SW_IN_DEF_VAR], sz_defs[TA_DEF_VAR], sz_defs[VPD_DEF_VAR] } }
		, { DEFAULT_TOLERANCES, DEFAULT_OOR, { CO2_MET, -1, -1, -1 }, { sz_defs[CO2_DEF_VAR], sz_defs[SW_IN_DEF_VAR], sz_defs[TA_DEF_VAR], sz_defs[VPD_DEF_VAR] } }
		, { DEFAULT_TOLERANCES, DEFAULT_OOR, { -1, -1, -1, -1 }, { sz_defs[TS_DEF_VAR], sz_defs[SW_IN_DEF_VAR], sz_defs[TA_DEF_VAR], sz_defs[VPD_DEF_VAR] } }
		, { DEFAULT_TOLERANCES, DEFAULT_OOR, { -1, -1, -1, -1 }, { sz_defs[SWC_DEF_VAR], sz_defs[SW_IN_DEF_VAR], sz_defs[TA_DEF_VAR], sz_defs[VPD_DEF_VAR] } }
	};

	vars->count = SIZEOF_ARRAY(defs);
	vars->vars = malloc(vars->count*sizeof*vars->vars);
	if ( vars->vars ) {
		int i;

		for ( i = 0; i < vars->count; ++i ) {
			int y;
			for ( y = MDS_VAR_TO_FILL; y < MDS_VARS_COUNT; ++y ) {
				vars->vars[i].name[y] = string_copy(defs[i].name[y]);
				if ( ! vars->vars[i].name[y] ) {
					break;
				}
				vars->vars[i].columns[y] = defs[i].columns[y];
				vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MIN] = defs[i].tolerances[y][MDS_VAR_TOLERANCE_MIN];
				vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MAX] = defs[i].tolerances[y][MDS_VAR_TOLERANCE_MAX];
				vars->vars[i].oors[y][MDS_VAR_OOR_MIN] = defs[i].oors[y][MDS_VAR_OOR_MIN];
				vars->vars[i].oors[y][MDS_VAR_OOR_MAX] = defs[i].oors[y][MDS_VAR_OOR_MAX];
			}
		}

		if ( i < vars->count ) {
			Mds_Vars_Clear(vars);
		} else {
			ret = 1;
		}
	}

	return ret;

#undef DEFAULT_OOR
#undef DEFAULT_TOLERANCES
}

static void mds_summary(MDS_VARS* vars) {
	const char* drivers[MDS_VARS_COUNT] = { NULL, "driver1", "driver2a", "driver2b" };
	int i;
	int digits_count = get_digits_count(vars->count);
	if ( digits_count < 2 ) {
		digits_count = 2;
	}
	puts("MDS summary:\n");
	for ( i = 0; i < vars->count; i++ ) {
		int y;

		printf("[%0*d / %0*d] - var to gf: %s", digits_count, i+1, digits_count, vars->count, vars->vars[i].name[MDS_VAR_TO_FILL]);
		if ( ! IS_INVALID_VALUE(vars->vars[i].oors[MDS_VAR_TO_FILL][MDS_VAR_OOR_MIN]) ) {
				printf(" (o: %g,%g)"	, vars->vars[i].oors[MDS_VAR_TO_FILL][MDS_VAR_OOR_MIN]
										, vars->vars[i].oors[MDS_VAR_TO_FILL][MDS_VAR_OOR_MAX]
				);
			}
		for ( y = MDS_VAR_DRIVER_1; y < MDS_VARS_COUNT; ++y ) {
			printf(", %s: %s", drivers[y], vars->vars[i].name[y]);
			if ( IS_INVALID_VALUE(vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MAX]) ) {
				printf(" (t: %g)", vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MIN]);
			} else {
				printf(" (t: %g,%g)"	, vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MIN]
										, vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MAX]
				);
			}
			if ( ! IS_INVALID_VALUE(vars->vars[i].oors[y][MDS_VAR_OOR_MIN]) ) {
				printf(" (o: %g,%g)"	, vars->vars[i].oors[y][MDS_VAR_OOR_MIN]
										, vars->vars[i].oors[y][MDS_VAR_OOR_MAX]
				);
			}
		}
		puts("");
	}
}

static int mds_merge(MDS_VARS* vars, MDS_VARS* user_vars) {
	int u; /* as user */
	int ret = 0; /* defaults to err */
	for ( u = 0; u < user_vars->count; ++u ) {
		int i;
		int y;

		/* check if we need to overwrite default ones */
		for ( i = 0; i < vars->count; ++i ) {
			if ( ! string_compare_i(user_vars->vars[u].name[MDS_VAR_TO_FILL], vars->vars[i].name[MDS_VAR_TO_FILL]) ) {
				break;
			}
		}
		if ( vars->count == i ) {
			/* add */
			MDS_VAR* var_no_leak = realloc(vars->vars, (vars->count+1)*sizeof*var_no_leak);
			if ( var_no_leak ) {
				vars->vars = var_no_leak;
				memset(&vars->vars[vars->count], 0, sizeof(vars->vars[vars->count]));
				Mds_Var_Clear(&vars->vars[vars->count]);
				i = vars->count++;
			}
		}

		/* if any */
		vars->vars[i].oors[MDS_VAR_TO_FILL][MDS_VAR_OOR_MIN] = user_vars->vars[u].oors[MDS_VAR_TO_FILL][MDS_VAR_OOR_MIN];
		vars->vars[i].oors[MDS_VAR_TO_FILL][MDS_VAR_OOR_MAX] = user_vars->vars[u].oors[MDS_VAR_TO_FILL][MDS_VAR_OOR_MAX];

		for ( y = MDS_VAR_DRIVER_1; y < MDS_VARS_COUNT; ++y ) {
			if ( vars->vars[i].name[y] ) {
				free((void*)vars->vars[i].name[y]);
			}
			vars->vars[i].name[y] = string_copy(user_vars->vars[u].name[y]);
			if ( !vars->vars[i].name[y] ) {
				break;
			}
			vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MIN] = user_vars->vars[u].tolerances[y][MDS_VAR_TOLERANCE_MIN];
			vars->vars[i].tolerances[y][MDS_VAR_TOLERANCE_MAX] = user_vars->vars[u].tolerances[y][MDS_VAR_TOLERANCE_MAX];
			vars->vars[i].oors[y][MDS_VAR_OOR_MIN] = user_vars->vars[u].oors[y][MDS_VAR_OOR_MIN];
			vars->vars[i].oors[y][MDS_VAR_OOR_MAX] = user_vars->vars[u].oors[y][MDS_VAR_OOR_MAX];
		}

		ret = (MDS_VARS_COUNT == y);
	}

	return ret;
}

/* */
int main(int argc, char *argv[]) {
	int i;
	int ret = 1; /* defaults to err */
	MDS_VARS mds_vars_by_user;
	MDS_VARS mds_vars;
	DATASET *datasets = NULL;	/* mandatory */
	int datasets_count = 0;		/* mandatory */
	const ARGUMENT args[] = {
		{ "qc_auto_path", set_path, &qc_auto_files_path },
		{ "era_path", set_path, &era_files_path },
		{ "output_path", set_path, &output_files_path },
		{ "variadic", parse_mds, &mds_vars_by_user },
		{ "h", show_help, NULL },
		{ "help", show_help, NULL },
		{ "?", show_help, NULL },
	};

	Mds_Vars_Init(&mds_vars_by_user);
	Mds_Vars_Init(&mds_vars);
	
	/* show banner */
	puts(banner);

	/* register atexit */
	if ( -1 == atexit(clean_up) ) {
		puts(err_unable_to_register_atexit);
	} else {
		/* get program path */
		program_path = get_current_directory();
		if ( !program_path ) {
			puts(err_unable_get_current_directory);
		} else if ( parse_arguments(argc, argv, args, SIZEOF_ARRAY(args)) ) {
			ret = 0; /* ok */
			/* check for user mds */
			if ( mds_vars_by_user.count ) {
				for ( i = 0; i < mds_vars_by_user.count; i++ ) {
					if ( ! mds_vars_by_user.vars[i].name[MDS_VAR_DRIVER_1] ) {
						printf("error: missing driver1 var for %s\n", mds_vars_by_user.vars[i].name[MDS_VAR_TO_FILL]);
						break;
					}
					if ( ! mds_vars_by_user.vars[i].name[MDS_VAR_DRIVER_2A] ) {
						printf("error: missing driver2a var for %s\n", mds_vars_by_user.vars[i].name[MDS_VAR_TO_FILL]);
						break;
					}
					if ( ! mds_vars_by_user.vars[i].name[MDS_VAR_DRIVER_2B] ) {
						printf("error: missing driver2b var for %s\n", mds_vars_by_user.vars[i].name[MDS_VAR_TO_FILL]);
						break;
					}
					if ( IS_INVALID_VALUE(mds_vars_by_user.vars[i].tolerances[MDS_VAR_DRIVER_1][MDS_VAR_TOLERANCE_MIN]) ) {
						printf("error: missing driver1 tolerances var for %s\n", mds_vars_by_user.vars[i].name[MDS_VAR_TO_FILL]);
						break;
					}
					if ( IS_INVALID_VALUE(mds_vars_by_user.vars[i].tolerances[MDS_VAR_DRIVER_2A][MDS_VAR_TOLERANCE_MIN]) ) {
						printf("error: missing driver2a tolerances var for %s\n", mds_vars_by_user.vars[i].name[MDS_VAR_TO_FILL]);
						break;
					}
					if ( IS_INVALID_VALUE(mds_vars_by_user.vars[i].tolerances[MDS_VAR_DRIVER_2B][MDS_VAR_TOLERANCE_MIN]) ) {
						printf("error: missing driver2b tolerances var for %s\n", mds_vars_by_user.vars[i].name[MDS_VAR_TO_FILL]);
						break;
					}
				}
				ret = (i < mds_vars_by_user.count);
			}
			if ( ! ret ) {
				printf("setting default values for mds...");
				if ( ! setup_default_mds(&mds_vars) ) {
					printf("%s\n\n", err_out_of_memory);
				} else {
					puts("ok!\n");
				}

				if ( !ret ) {
					/* merge user mds with defaults ones */
					if ( mds_vars_by_user.count ) {
						printf("merging default values for mds with user...");
						ret = !mds_merge(&mds_vars, &mds_vars_by_user);
						if ( ret ) {
							printf("%s\n\n", err_out_of_memory);
						} else {
							puts("ok!\n");
						}
					}

					if ( !ret ) {
						/* summary for mds */
						mds_summary(&mds_vars);

						/* get input path */
						if ( !qc_auto_files_path ) {
							for ( i = 0; QC_AUTO_PATH[i]; i++ ); i += 2;
							ret = !(qc_auto_files_path = malloc(i*sizeof*qc_auto_files_path));
							if ( ret ) {
								printf("%s\n\n", err_out_of_memory);
							} else {
								sprintf(qc_auto_files_path, "%s%c", QC_AUTO_PATH, FOLDER_DELIMITER);
							}
						}

						if ( !ret ) {
							/* get era path */
							if ( !era_files_path ) {
								for ( i = 0; ERA_PATH[i]; i++ ); i += 2;
								ret = !(era_files_path = malloc(i*sizeof*era_files_path));
								if ( ret ) {
									printf("%s\n\n", err_out_of_memory);
								} else {
									sprintf(era_files_path, "%s%c", ERA_PATH, FOLDER_DELIMITER);
								}
							}

							if ( !ret ) {
								/* output path specified ? */
								if ( !output_files_path ) {
									ret = !(output_files_path = string_copy(program_path));
									if ( ret ) {
										printf("%s\n\n", err_out_of_memory);
									}
								}

								if ( !ret ) {
									/* check output path */
									if ( !path_exists(output_files_path) ) {
										/* trying to create output path */
										ret = !create_dir(output_files_path);
										if ( ret ) {
											printf("unable to create output folder: %s\n", output_files_path);
										}
									}

									if ( ! ret ) {
										/* get datasets */
										ret = !(datasets = get_datasets(&datasets_count));
										if ( !ret ) {
											/* compute datasets */
											if ( !compute_datasets(datasets, datasets_count, &mds_vars) ) {
												free_datasets(datasets, datasets_count);
											} else {
												/* show datasets */
												printf("%d dataset%s found%s.\n",	datasets_count,
																					(datasets_count>1) ? "s" : "",
																					(datasets_count>1) ? "ed" : "");
											}
										}
									}
								}
							}
						}
					}
				}
			}
		}
	}

	Mds_Vars_Clear(&mds_vars);
	Mds_Vars_Clear(&mds_vars_by_user);

	/* */
	return ret;
}
