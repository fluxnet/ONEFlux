/*
	main.c

	This file is part of the qc_auto step of processing.
	It is responsible for a number of basic quality check test
	and the creation of the input files for the following
	processing steps

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <assert.h>
#include "dataset.h"
#include "rpot.h"
#include "marginal.h"
#include "ustar.h"
#include "spike.h"
#include "../../compiler.h"

/* constants */
#define PROGRAM_VERSION			"v1.01"
const int days_per_month[MONTHS] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

/* enum */
enum {
	EQUAL = 0,
	GREATER,
	LESS,
	GREATER_EQUAL,
	LESS_EQUAL,

	COMPARE
};

/* struct */
typedef struct {
	int start;
	int end;
	int first;
	int month;
} SOLAR_NOON_PERIOD;

/* */
typedef struct {
	int swin;
	int ppfd;
	int period;
} SUMPERIOD;

/* */
const SOLAR_NOON_PERIOD solar_noon_periods[] = {
	{ 171, 191, 180, 7 },		/* June 20 - July 10 - July 1		*/
	{ 201, 221, 210, 8 },		/* July 20 - 9 August - August 1	*/
	{ 140, 160, 149, 6 },		/* May 20 - June 10 - June 1		*/

	{ 1, 21, 10, 1 },			/* January 1 - January 20 - January 10		*/
	{ 32, 52, 41, 2 },			/* February 1 - February 20 - February 10	*/
	{ 335, 355, 344, 12 },		/* December 1 - December 20 - December 10	*/
};

/* extern variables */
extern const char *const var_names[];
extern const char *const var_flag_names[];

/* global variables */
char *program_path = NULL;	/* mandatory */
char *input_path = NULL;	/* mandatory */
char *output_path = NULL;	/* mandatory */
int marginals_window = MARGINALS_WINDOW;							/* see common.h */
PREC swin_check = SWIN_CHECK;										/* see common.h */
PREC rpot_check = RPOT_CHECK;										/* see common.h */
PREC swin_limit = SWIN_LIMIT;										/* see common.h */
int radiation_check = RADIATION_CHECK;								/* see common.h */
PREC radiation_check_stddev = RADIATION_CHECK_STDDEV;				/* see common.h */
PREC rgvsppfd_threshold = SWINVSPPFD_THRESHOLD;						/* see common.h */
int ustar_check = USTAR_CHECK;										/* see common.h */
PREC ustar_check_stddev = USTAR_CHECK_STDDEV;						/* see common.h */
int spikes_window = SPIKES_WINDOW;									/* see common.h */
int lowvar_min_values = LOWVAR_MIN_VALUES;							/* see common.h */
int lowvar_stddev_values = LOWVAR_STDDEV_VALUES;					/* see common.h */
int lowvar_window = LOWVAR_WINDOW;									/* see common.h */
PREC spike_check_1 = SPIKE_CHECK_1;									/* see common.h */
PREC spike_check_2 = SPIKE_CHECK_2;									/* see common.h */
PREC spike_check_3 = SPIKE_CHECK_3;									/* see common.h */
int spike_check_1_return = SPIKE_CHECK_1_RETURN;					/* see common.h */
int spike_check_2_return = SPIKE_CHECK_2_RETURN;					/* see common.h */
int spike_check_3_return = SPIKE_CHECK_3_RETURN;					/* see common.h */
PREC spike_threshold_nee = SPIKE_THRESHOLD_NEE;						/* see common.h */
PREC spike_threshold_le = SPIKE_THRESHOLD_LE;						/* see common.h */
PREC spike_threshold_h = SPIKE_THRESHOLD_H;							/* see common.h */
int files_found_count;
PREC height;
static int doy;
static int qc2_filter;												/* default is off */
static int no_spike_filter;											/* default is off */

static int db_output;												/* default is off */
static int graph_output;											/* default is off */
static int ustar_output;											/* default is off */
static int nee_output;												/* default is off */
static int energy_output;											/* default is off */
static int meteo_output;											/* default is off */
static int sr_output;												/* default is off */
static int solar_output;											/* default is off */
static int one_timestamp;											/* default is off */

/* static global variables */
static FILES *files_found;

/* strings */
static const char banner[] =	"\nqc_auto "PROGRAM_VERSION"\n"
								"by Alessio Ribeca\n\n"
								"scientific contact: darpap at unitus dot it\n"
								"technical contact: a dot ribeca at unitus dot it\n\n"
								"DIBAF - University of Tuscia, Viterbo, Italy\n"
								"(builded on "__DATE__" at "__TIME__ " with "COMPILER")\n"
								"(use -h parameter for more information)\n";
static const char notes[] = "processed on %s with qc_auto "PROGRAM_VERSION" compiled using "COMPILER" on "__DATE__" at " __TIME__;
const char filter[] = "*.*";

/* messages */
static const char msg_dataset_not_specified[] =
"dataset not specified."
#if defined (_WIN32) || defined (linux)
" searching..."
#endif
"\n";
static const char msg_dataset_path[] = "dataset path = %s\n";
static const char msg_output_path[] = "output path = %s\n\n";
static const char msg_processing[] = "	- found %s, %d...ok\n";
static const char msg_ok[] = "ok";
static const char msg_summary[] = "\n%d file%s found: %d processed, %d skipped.\n\n";
static const char msg_usage[] =	"usage: qc_auto parameters output_formats\n\n"
								"parameters:\n\n"
								"-input_path=filename or path to be processed (optional)\n"
								"-output_path=path where result files are created (optional)\n"
								"-marginals_window -> size of window for marginals (default is %d)\n"
								"-sw_in_check -> value for SW_IN check (default is %g)\n"
								"-sw_in_pot_check -> value for SW_IN_POT check (default is %g)\n"
								"-sw_in_limit -> value for SW_IN limit (default is %g)\n"
								"-radiation_check -> value for radiation check (default is %d)\n"
								"-radiation_check_stddev -> std dev for radiation check (default is %g)\n"
								"-sw_in_vs_ppfd_in_threshold -> thrs value for SW_IN vs PPFD_IN (default is %g)\n"
								"-spikes_window -> size of window for spikes (default is %d)\n"
								"-qc2_filter -> enable qc2 filter (default is off)\n"
								"-no_spike_filter -> disable spike filtering for NEE, H and LE\n"
								"-doy=X -> custom doy for solar noon\n"
								"-h -> show this help\n\n"
								"output formats:\n"
								"(one or more must be present)\n\n"
								"-db -> create input file for db computation (default is off)\n"
								"-graph -> create input file for graphical viewing (default is off)\n"
								"-ut -> create input file for u* computation (default is off)\n"
								"-nee -> create input file for NEE uncertainty computation (default is off)\n"
								"-energy -> create input file for energy corr. computation (default is off)\n"
								"-meteo -> create input file for meteo computation (default is off)\n"
								"-sr -> create input file for Sundown Respiration partitioning (default is off)\n"
								"-solar -> create input file for shift detection (default is off)\n"
								"-all -> create all inputs files except sr and solar\n\n";
/* error messages */
extern const char err_out_of_memory[];
const char err_empty_file[] = "empty file ?";
const char err_window_size_too_big[] = "window size too big.";
static const char err_unable_get_current_directory[] = "unable to retrieve current directory.\n";
static const char err_unable_to_register_atexit[] = "unable to register clean-up routine.\n";
static const char err_unable_to_get_year[] = "unable to get year for %s\n";
static const char err_output_path_no_delimiter[] = "output path must terminating with a \"%c\"\n\n";
static const char err_unable_create_output_path[] = "unable to create output path: %s\n\n";
static const char err_dataset_already_specified[] = "dataset already specified (%s)! \"%s\" skipped.\n";
static const char err_output_already_specified[] = "output path already specified (%s)! \"%s\" skipped.\n";
static const char err_arg_needs_param[] = "%s parameter not specified.\n\n";
static const char err_arg_no_needs_param[] = "%s no needs parameter.\n\n";
static const char err_unable_convert_value_arg[] = "unable to convert value \"%s\" for %s.\n\n";
static const char err_no_output_specified[] = "no output specified.";
static const char err_buffer_too_small[]= "buffer too small for notes!";
static const char err_negative_doy[] = "custom doy can't be negative: %d.\n";

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
PREC *copy_value(const DATASET *const dataset, const int column) {
	int i;
	PREC *copy;

	/* check for null pointer */
	assert(dataset);

	/* allocate memory */
	copy = malloc(dataset->rows_count*sizeof*copy);
	if ( !copy ) {
		return NULL;
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		copy[i] = dataset->rows[i].value[column];
	}

	/* */
	return copy;
}

/* */
static void clean_up(void) {
	if ( program_path ) {
		free(program_path);
	}
	if ( files_found ) {
		free_files(files_found, files_found_count);
	}
	check_memory_leak();
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
int set_prec_value(char *arg, char *param, void *p) {
	int error;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	/* convert param */
	*(PREC *)p = convert_string_to_prec(param, &error);
	if ( error ) {
		printf(err_unable_convert_value_arg, param, arg);
		return 0;
	}

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
int save_all(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	/* enable all outputs */
	db_output = 1;
	graph_output = 1;
	ustar_output = 1;
	nee_output = 1;
	energy_output = 1;
	meteo_output = 1;

	/* ok */
	return 1;
}

/* */
int preserve_swin(const DATASET *const dataset) {
	int i;
	int SWIN;
	int SWIN_OR;

	if ( dataset ) {
		SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
		SWIN_OR = get_var_index(dataset, var_names[SWIN_ORIGINAL]);
		if ( -1 == SWIN ) {
			/* check itp */
			SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
		}
		if ( -1 != SWIN ) {
			if ( -1 == SWIN_OR ) {
				printf("unable to get %s var.\n", var_names[SWIN_ORIGINAL]);
				return 0;
			}
			for ( i = 0; i < dataset->rows_count; i++ ) {
				dataset->rows[i].value[SWIN_OR] = dataset->rows[i].value[SWIN];
			}
			/*
			dataset->header[SWIN_OR].index = dataset->header[SWIN].index;
			*/
		}
	}

	/* ok */
	return 1;
}

/* */
int preserve_ppfd(const DATASET *const dataset) {
	int i;
	int PPFD;
	int PPFD_OR;

	if ( dataset ) {
		PPFD = get_var_index(dataset, var_names[PPFD_INPUT]);
		PPFD_OR = get_var_index(dataset, var_names[PPFD_ORIGINAL]);
		if ( -1 == PPFD ) {
			/* check itp */
			PPFD = get_var_index(dataset, var_names[itpPPFD_INPUT]);
		}
		if ( -1 != PPFD ) {
			if ( -1 == PPFD_OR ) {
				printf("unable to get %s var.\n", var_names[PPFD_ORIGINAL]);
				return 0;
			}
			for ( i = 0; i < dataset->rows_count; i++ ) {
				dataset->rows[i].value[PPFD_OR] = dataset->rows[i].value[PPFD];
			}
			/*
			dataset->header[PPFD_OR].index = dataset->header[PPFD].index;
			*/
		}
	}

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
						MARGINALS_WINDOW,
						SWIN_CHECK,
						RPOT_CHECK,
						SWIN_LIMIT,
						RADIATION_CHECK,
						RADIATION_CHECK_STDDEV,
						SWINVSPPFD_THRESHOLD,
						SPIKES_WINDOW
	);

	/* must return error */
	return 0;
}

/* */
void compute_missings(DATASET *const dataset) {
	int i;
	int y;

	assert(dataset);

	for ( i = 0; i < dataset->columns_count; i++ ) {
		dataset->missings[i] = 0;
		for ( y = 0; y < dataset->rows_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->rows[y].value[i]) ) {
				++dataset->missings[i];
			}
		}
	}
}

/* */
int ustar_from_tau(DATASET *const dataset) {
	int USTAR;
	int TAU;

	/* check null parameter */
	assert(dataset);

	/* get columns indexes */
	USTAR = get_var_index(dataset, var_names[USTAR_INPUT]);
	TAU = get_var_index(dataset, var_names[TAU_INPUT]);

	/* check indexes */
	if ( -1 == TAU ) {
		return 1;
	}

	if ( -1 == USTAR ) {
		USTAR = add_var_to_dataset(dataset, var_names[USTAR_INPUT]);
		if ( -1 == USTAR ) {
			printf("unable to add %s var.\n", var_names[USTAR_INPUT]);
			return 0;
		}
	}

	/* ustar from tau */
	if ( dataset->rows_count == dataset->missings[USTAR] ) {
		int i;

		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( IS_INVALID_VALUE(dataset->rows[i].value[TAU]) ) {
				if ( !IS_INVALID_VALUE(dataset->rows[i].value[USTAR]) ) {
					dataset->rows[i].value[USTAR] = INVALID_VALUE;
					++dataset->missings[USTAR];
				}
			} else {
				if ( IS_INVALID_VALUE(dataset->rows[i].value[USTAR]) ) {
					--dataset->missings[USTAR];
				}
				dataset->rows[i].value[USTAR] = SQRT(FABS(dataset->rows[i].value[TAU])/1.2);

				/* check for nan */
				if ( dataset->rows[i].value[USTAR] != dataset->rows[i].value[USTAR] ) {
					dataset->rows[i].value[USTAR] = INVALID_VALUE;
					++dataset->missings[USTAR];
				}
			}
		}
	}

	/* ok */
	return 1;
}

/*

1)      NEE = Fc+Sc; NEE_FLAG = 1

if Sc = -9999

2)      NEE = Fc + Sc_top_tower; NEE_FLAG = 2

if CO2 = -9999 AND SC_NEGL=1

3)      NEE=Fc; NEE_FLAG = 3

*/
int set_nee(DATASET *const dataset) {
	int i;
	PREC sit;
	int CO2;
	int FC;
	int FCSTOR;
	int FCSTORTT;
	int SC;
	int NEE;
	int NEE_FLAG;
	int HEIGHT;
	int QCFOOT;
	int SC_NEGL;
	PREC value;
	int has_fcstor;

	/* */
	assert(dataset);

	/* seconds in timeres */
	sit = (HOURLY_TIMERES == dataset->details->timeres)  ? 3600.0 : 1800.0;

	/* */
	CO2 = get_var_index(dataset, var_names[CO2_INPUT]);
	FC = get_var_index(dataset, var_names[FC_INPUT]);
	SC = get_var_index(dataset, var_names[SC_INPUT]);
	FCSTOR = get_var_index(dataset, var_names[FCSTOR_INPUT]);
	FCSTORTT = get_var_index(dataset, var_names[FCSTORTT_INPUT]);
	NEE = get_var_index(dataset, var_names[NEE_INPUT]);
	HEIGHT = get_var_index(dataset, var_names[HEIGHT_INPUT]);
	NEE_FLAG = get_flag_index(dataset, var_flag_names[NEE_FLAG_INPUT]);
	QCFOOT = get_var_index(dataset, var_names[QCFOOT_INPUT]);
	SC_NEGL = get_var_index(dataset, var_names[SC_NEGL_INPUT]);
	assert((FCSTOR != -1)&&(FCSTORTT != -1)&&(HEIGHT != -1)&&(NEE_FLAG != -1)&&(SC_NEGL != -1));

	/* added on 20160822 */
	/* check for FC */
	if ( (-1 == FC) || (dataset->rows_count == dataset->missings[FC]) ) {
		/* do not add NEE */
		return 1;
	}

	/* */
	has_fcstor = 0;
	if ( NEE != -1 ) {
		has_fcstor = 1;
		for ( i = 0; i < dataset->rows_count; i++ ) {
			dataset->rows[i].value[FCSTOR] = dataset->rows[i].value[NEE];
		}
		dataset->missings[FCSTOR] = dataset->missings[NEE];
	} else {
		NEE = add_var_to_dataset(dataset, var_names[NEE_INPUT]);
		if ( -1 == NEE ) {
			printf("unable to add '%s'\n", var_names[NEE_INPUT]);
			return 0;
		}
	}

	/* */
	if ( ! has_fcstor && (FC != -1) && (SC != -1) ) {
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( ! IS_INVALID_VALUE(dataset->rows[i].value[FC]) && !IS_INVALID_VALUE(dataset->rows[i].value[SC]) ) {
				value = dataset->rows[i].value[FC] + dataset->rows[i].value[SC];
				if ( (value > STORAGE_RANGE_MIN) && (value < STORAGE_RANGE_MAX) ) {
					dataset->rows[i].value[FCSTOR] = value;
					--dataset->missings[FCSTOR];
				}
			}
		}
	}

	/* */
	if ( (CO2 != -1) && (FC != -1) && ! IS_INVALID_VALUE(dataset->rows[0].value[HEIGHT]) ) {
		for ( i = 1; i < dataset->rows_count; i++ ) {
			if ( (! IS_INVALID_VALUE(dataset->rows[i].value[CO2])) && (! IS_INVALID_VALUE(dataset->rows[i-1].value[CO2])) && (! IS_INVALID_VALUE(dataset->rows[i].value[FC])) ) {
				value = (PREC)(dataset->rows[i].value[FC] + ((dataset->rows[i].value[CO2]-dataset->rows[i-1].value[CO2])/sit)*(dataset->rows[i].value[HEIGHT]/0.024));
				if ( (value > STORAGE_RANGE_MIN) && (value < STORAGE_RANGE_MAX) ) {
					dataset->rows[i].value[FCSTORTT] = value;
					--dataset->missings[FCSTORTT];
				}
			}
		}
	}

	/* */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		dataset->flags[i].value[NEE_FLAG] = INVALID_VALUE;
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[FCSTOR]) ) {
			dataset->rows[i].value[NEE] = dataset->rows[i].value[FCSTOR];
			dataset->flags[i].value[NEE_FLAG] = 1;
			--dataset->missings[NEE];
		} else if ( ! IS_INVALID_VALUE(dataset->rows[i].value[FCSTORTT]) ) {
			dataset->rows[i].value[NEE] = dataset->rows[i].value[FCSTORTT];
			dataset->flags[i].value[NEE_FLAG] = 2;
			--dataset->missings[NEE];
		} else if ( (1 == dataset->rows[i].value[SC_NEGL]) && ! IS_INVALID_VALUE(dataset->rows[i].value[FC]) ) {
			dataset->rows[i].value[NEE] = dataset->rows[i].value[FC];
			dataset->flags[i].value[NEE_FLAG] = 3;
			--dataset->missings[NEE];
		}
	}

	if ( QCFOOT != -1 ) {
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( (0 == dataset->rows[i].value[QCFOOT]) && !IS_INVALID_VALUE(dataset->rows[i].value[NEE]) ) {
				dataset->rows[i].value[NEE] = INVALID_VALUE;
				dataset->flags[i].value[NEE_FLAG] = INVALID_VALUE;
				++dataset->missings[NEE];
			}
		}
	}

	/* ok */
	return 1;
}

/* */
static int set_vpd(DATASET *const dataset) {
	int i;
	int TA;
	int RH;
	int VPD;
	int set_itp;
	PREC value;

	/* */
	assert(dataset);

	/* reset */
	set_itp = 0;

	/* */
	TA = get_var_index(dataset, var_names[TA_INPUT]);
	RH = get_var_index(dataset, var_names[RH_INPUT]);
	VPD = get_var_index(dataset, var_names[VPD_INPUT]);

	/* VPD already on dataset ? */
	if ( VPD != -1 ) {
		return 1;
	}

	/* it is possible to compute VPD ? */
	if ( -1 == TA ) {
		/* check for itp */
		TA = get_var_index(dataset, var_names[itpTA_INPUT]);
		if ( -1 == TA ) {
			return 1;
		}
		set_itp = 1;
	}

	/* it is possible to compute VPD ? */
	if ( -1 == RH ) {
		/* check for itp */
		RH = get_var_index(dataset, var_names[itpRH_INPUT]);
		if ( -1 == RH ) {
			return 1;
		}
		set_itp = 1;
	}

	/* add column */
	VPD = add_var_to_dataset(dataset, var_names[set_itp ? itpVPD_INPUT : VPD_INPUT]);
	if ( -1 == VPD ) {
		printf("unable to add '%s'\n", var_names[set_itp ? itpVPD_INPUT : VPD_INPUT]);
		return 0;
	}

	/* */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		value = INVALID_VALUE;
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[TA]) && !IS_INVALID_VALUE(dataset->rows[i].value[RH]) ) {
			/* 6.11 is for hPa, checked againist L4 on January 30, 2012 */
			value = 6.11 * exp(17.26938818 * dataset->rows[i].value[TA] / (237.3 + dataset->rows[i].value[TA]));
			value *= (1 - dataset->rows[i].value[RH] / 100.0);
			/* convert NaN to invalid value */
			if ( value != value ) {
				value = INVALID_VALUE;
			}

			/* check range */
			if ( !IS_INVALID_VALUE(value) ) {
				if ( value < VPD_RANGE_MIN || value > VPD_RANGE_MAX ) {
					value = INVALID_VALUE;
				}
			}
		}
		dataset->rows[i].value[VPD] = value;
		if ( IS_INVALID_VALUE(value) ) {
			++dataset->missings[VPD];
		} else {
			--dataset->missings[VPD];
		}
	}

	/* */
	return 1;
}

/* */
static void set_qc2_flag(DATASET *const dataset, const char *const var, const char *const flag) {
	int i;
	int VAR;
	int FLAG;

	/* */
	assert(dataset);

	/* */
	VAR = get_var_index(dataset, var);
	FLAG = get_flag_index(dataset, flag);
	assert(FLAG != -1);

	if ( -1 != VAR ) {
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( ARE_FLOATS_EQUAL(dataset->rows[i].value[VAR], 2.0) ) {
				dataset->flags[i].value[FLAG] = 1;
			}
		}
	}
}

/*
	checks for negative and missing incoming radiation data in relation to Potential incoming radiation
	if the potential radiation is 0 also the measured are set to 0
	needed because negative radiation affect partitioning quality and
	to increase number of nightime data needed for ustar threshold calculation
*/
static void check_for_neg(DATASET *const dataset, const char *const var) {
	int i;
	int y;
	int VAR;
	int RPOT;
	int TEMP;
	int flag;
	int window_size;
	int window_start;
	int window_end;
	int count;
	int is_swin;

	VAR = get_var_index(dataset, var);
	if ( -1 == VAR ) {
		return;
	}

	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	if ( -1 == RPOT ) {
		return;
	}

	TEMP = get_var_index(dataset, var_names[TEMP_INPUT]);
	assert(TEMP != -1);

	is_swin = -1;
	if ( ! string_compare_i(var, var_names[SWIN_INPUT])
		|| ! string_compare_i(var, var_names[itpSWIN_INPUT]) ) {
			is_swin = get_flag_index(dataset, var_flag_names[SWIN_FROM_PPFD_FLAG_INPUT]);
			assert(is_swin != -1);
	}
	
	for ( i = 0; i < dataset->rows_count; ++i ) {
		dataset->rows[i].value[TEMP] = dataset->rows[i].value[VAR];
	}

	window_size = 24;
	if ( HOURLY_TIMERES == dataset->details->timeres ) {
		window_size = 12;
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		flag = IS_INVALID_VALUE(dataset->rows[i].value[TEMP]);
		if ( flag || (dataset->rows[i].value[TEMP] < 0)  ) {
			if ( ARE_FLOATS_EQUAL(0, dataset->rows[i].value[RPOT]) ) {
				count = 0;
				window_start = i - window_size;
				if ( window_start < 0 ) window_start = 0;
				window_end = i + window_size;
				if ( window_end > dataset->rows_count ) window_end = dataset->rows_count;
				for ( y = window_start; y < window_end; ++y ) {
					if ( ! IS_INVALID_VALUE(dataset->rows[y].value[TEMP]) ) {
						++count;
						break;
					}
				}

				if ( count ) {
					dataset->rows[i].value[VAR] = 0;
					if ( is_swin != -1 ) {
						dataset->flags[i].value[is_swin] = 1;
					}
					if ( flag ) {
						--dataset->missings[VAR];
					}
				}
			} else {
				dataset->rows[i].value[VAR] = INVALID_VALUE;
				if ( !flag ) {
					++dataset->missings[VAR];
				}
			}
		}
	}
}

/* */
static int set_swin_from_ppfd(DATASET *const dataset) {
#define PPFD_TO_SWIN_CONV	0.52
#define SLOPE_DEFAULT		(1./PPFD_TO_SWIN_CONV)
#define SLOPE_TOL			0.2
/* please note that + on MIN and - and MAX are rights! */
#define SLOPE_MIN			(1./(PPFD_TO_SWIN_CONV+SLOPE_TOL))
#define SLOPE_MAX			(1./(PPFD_TO_SWIN_CONV-SLOPE_TOL))

	int i;
	int SWIN;
	int PPFD;
	int SWIN_FROM_PPFD;
	int valid_swin;
	int valid_ppfd;
	int all_valids_count;
	PREC sumx;
	PREC sumy;
	PREC sumx2;
	PREC sumxy;
	PREC divisor;
	PREC slope;
	PREC intercept;
	SPIKE *all_valids; /* used for linear regression! */

	/* */
	assert(dataset);

	/* */
	SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
	if ( -1 == SWIN ) {
		/* get itp */
		SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
	}
	PPFD = get_var_index(dataset, var_names[PPFD_INPUT]);
	if ( -1 == PPFD ) {
		/* get itp */
		PPFD = get_var_index(dataset, var_names[itpPPFD_INPUT]);
	}
	SWIN_FROM_PPFD = get_flag_index(dataset, var_flag_names[SWIN_FROM_PPFD_FLAG_INPUT]);
	assert(SWIN_FROM_PPFD!=1);

	/* check for PPFD var */
	if ( -1 == PPFD ) {
		return 1;
	}

	/* get valid ppfd count */
	valid_ppfd = dataset->rows_count - dataset->missings[PPFD];
	if ( !valid_ppfd ) {
		return 1;
	}

	valid_swin = 0;
	if ( -1 != SWIN ) {
		valid_swin = dataset->rows_count - dataset->missings[SWIN];
	}
	if ( !valid_swin ) {
		if ( -1 == SWIN ) {
			SWIN = add_var_to_dataset(dataset, var_names[SWIN_INPUT]);
			if ( -1 == SWIN ) {
				printf("unable to add %s var.\n", var_names[SWIN_INPUT]);
				return 0;
			}

			for ( i = 0; i < dataset->rows_count; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows[i].value[PPFD]) ) {
					/* update value */
					dataset->rows[i].value[SWIN] = dataset->rows[i].value[PPFD] * PPFD_TO_SWIN_CONV;
					/* update flag */
					dataset->flags[i].value[SWIN_FROM_PPFD] = 3;
					/* update missings */
					--dataset->missings[SWIN];
				}
			}
		}
	} else {
		/* alloc memory */
		all_valids = malloc(valid_swin*sizeof*all_valids);
		if ( !all_valids ) {
			puts(err_out_of_memory);
			return 0;
		}

		all_valids_count = 0;
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows[i].value[SWIN]) && !IS_INVALID_VALUE(dataset->rows[i].value[PPFD]) ) {
				all_valids[all_valids_count].value1 = dataset->rows[i].value[SWIN];	/* x */
				all_valids[all_valids_count].value2 = dataset->rows[i].value[PPFD];	/* y */
				all_valids[all_valids_count++].index = i; /* not used */
			}
		}

		if ( !all_valids_count ) {
			free(all_valids);
			return 1;
		}

		/* reset */
		sumx = 0.0;
		sumy = 0.0;
		sumx2 = 0.0;
		sumxy = 0.0;

		/* linear regression between SWin and PPFD */
		for ( i = 0; i < all_valids_count; i++ ) {
			sumx += all_valids[i].value1;
			sumy += all_valids[i].value2;
			sumx2 += (all_valids[i].value1 * all_valids[i].value1);
			sumxy += (all_valids[i].value1 * all_valids[i].value2);
		}

		divisor = (sumx2 - ((sumx * sumx) / all_valids_count));

		if ( !ARE_FLOATS_EQUAL(divisor, 0.0) ) {
			slope = (sumxy - ((sumx * sumy) / all_valids_count)) / divisor;	/* a */
			intercept = (sumy - (slope * sumx)) / all_valids_count;			/* b */

			/* check slope */
			if ( (slope < SLOPE_MIN) || (slope > SLOPE_MAX) ) {
				printf("unable to compute %s from %s: slope is %f\n\n", var_names[SWIN_INPUT], var_names[PPFD_INPUT], slope);
				free(all_valids);

				return 0;
			}

			/* x = (y - b) / a */
			for ( i = 0; i < dataset->rows_count; i++ ) {
				if ( IS_INVALID_VALUE(dataset->rows[i].value[SWIN]) && !IS_INVALID_VALUE(dataset->rows[i].value[PPFD]) ) {
					dataset->rows[i].value[SWIN] = (dataset->rows[i].value[PPFD] - intercept) / slope;
					/* update flag */
					dataset->flags[i].value[SWIN_FROM_PPFD] = 2;
					/* update missings */
					--dataset->missings[SWIN];
				}
			}
		}
		free(all_valids);
	}

	/* ok */
	return 1;
#undef SLOPE_MAX
#undef SLOPE_MIN
#undef SLOPE_TOL
#undef SLOPE_DEFAULT
#undef PPFD_TO_SWIN_CONV
}

/* */
static void set_invalid_by_flag_value(DATASET *const dataset, const char *const var, const char *const flag, const int value, const int compare_type) {
	int i;
	int VAR;
	int FLAG;
	int ok;

	/* */
	assert(dataset && var && flag);

	/* */
	VAR = get_var_index(dataset, var);
	FLAG = get_flag_index(dataset, flag);
	assert(FLAG != -1);

	/* */
	if ( -1 == VAR ) {
		return;
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		ok = 0;
		switch ( compare_type ) {
			case EQUAL:
				if ( value == (int)dataset->flags[i].value[FLAG] ) {
					ok = 1;
				}
			break;

			case GREATER:
				if ( (int)dataset->flags[i].value[FLAG] > value ) {
					ok = 1;
				}
			break;

			case LESS:
				if ( (int)dataset->flags[i].value[FLAG] < value ) {
					ok = 1;
				}
			break;

			case GREATER_EQUAL:
				if ( (int)dataset->flags[i].value[FLAG] >= value ) {
					ok = 1;
				}
			break;

			case LESS_EQUAL:
				if ( (int)dataset->flags[i].value[FLAG] <= value ) {
					ok = 1;
				}
			break;
		}

		if ( ok ) {
			/* */
			if ( !IS_INVALID_VALUE(dataset->rows[i].value[VAR]) ) {
				++dataset->missings[VAR];
			}

			/* */
			dataset->rows[i].value[VAR] = INVALID_VALUE;
		}
	}
}

/* */
static void set_invalid_by_flag(DATASET *const dataset, const char *const var, const char *const flag) {
	set_invalid_by_flag_value(dataset, var, flag, 1, EQUAL);
}

/* */
static char *timestamp_for_sr(int row, int yy, const int timeres) {
	TIMESTAMP *t;
	static char buffer[16+1] = { 0 };

	t = timestamp_end_by_row(row, yy, timeres);
	sprintf(buffer, "%02d,%02d,%04d,%02d,%02d", t->MM, t->DD, t->YYYY, t->hh, t->mm); 

	/* */
	return buffer;
}

/* */
static int write_dd_with_notes(FILE *const f, const DATASET *const dataset) {
	int i;
	int buffer_len;
	int huge_buffer_len;
	char *huge_buffer;
	char buffer[BUFFER_SIZE];

	/* */
	assert(f && dataset);

	/* alloc memory */
	huge_buffer = malloc(HUGE_BUFFER_SIZE*sizeof*huge_buffer);
	if ( !huge_buffer ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* */
	sprintf(huge_buffer, notes, get_datetime_in_timestamp_format());
	for ( i = 0; i < dataset->columns_count; i++ ) {
		if ( dataset->header[i].index ) {
			/* add exception here */
			if (	! string_compare_i(dataset->header[i].name, var_names[SWC_INPUT]) ||
					! string_compare_i(dataset->header[i].name, var_names[itpSWC_INPUT]) ||
					! string_compare_i(dataset->header[i].name, var_names[TS_INPUT]) ||
					! string_compare_i(dataset->header[i].name, var_names[itpTS_INPUT]) ) {
				continue;
			}

			sprintf(buffer, "\nnotes,var %s_%d was renamed in %s", dataset->header[i].name, dataset->header[i].index, dataset->header[i].name);
			for ( buffer_len = 0; buffer[buffer_len]; buffer_len++ );
			for ( huge_buffer_len = 0; huge_buffer[huge_buffer_len]; huge_buffer_len++ );
			if ( huge_buffer_len+buffer_len < HUGE_BUFFER_SIZE-1 ) {
				strcat(huge_buffer, buffer);
			} else {
				puts(err_buffer_too_small);
				free(huge_buffer);
				return 0;
			}
		}
	}

	/* */
	i = write_dd(dataset->details, f, huge_buffer);

	/* free memory */
	free(huge_buffer);

	/* */
	return i;
}

/* */
static void set_spikes_value(DATASET *const dataset, int *const NEE, int *const H, int *const LE) {
	int i;
	int NEE_SPIKE;
	int H_SPIKE;
	int LE_SPIKE;

	/* */
	assert(dataset);

	/* */
	*NEE = get_var_index(dataset, var_names[NEE_INPUT]);
	*H = get_var_index(dataset, var_names[H_INPUT]);
	*LE = get_var_index(dataset, var_names[LE_INPUT]);
	NEE_SPIKE = get_var_index(dataset, var_names[NEE_SPIKE_INPUT]);
	H_SPIKE = get_var_index(dataset, var_names[H_SPIKE_INPUT]);
	LE_SPIKE = get_var_index(dataset, var_names[LE_SPIKE_INPUT]);
	assert(NEE_SPIKE != -1);
	assert(H_SPIKE != -1);
	assert(LE_SPIKE != -1);

	/* */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( *NEE != -1 ) {
			dataset->rows[i].value[NEE_SPIKE] = dataset->rows[i].value[*NEE];
		}
		if ( *H != -1 ) {
			dataset->rows[i].value[H_SPIKE] = dataset->rows[i].value[*H];
		}
		if ( *LE != -1 ) {
			dataset->rows[i].value[LE_SPIKE] = dataset->rows[i].value[*LE];
		}
	}
}

/* */
static int save_db_file(DATASET *const dataset) {
	int i;
	int y;
	int var;
	int flag;
	FILE *f;
	char buffer[256];
	const int vars_index[] = {
								NEE_INPUT,
								VPD_INPUT,
								itpVPD_INPUT,
								RPOT_INPUT,
	};
	const int flags_index[] = {
									NEE_FLAG_INPUT,
									USTAR_FLAG_INPUT,
									MARGINAL_NEE_FLAG_INPUT,
									MARGINAL_LE_FLAG_INPUT,
									MARGINAL_H_FLAG_INPUT,

									SWIN_FROM_PPFD_FLAG_INPUT,

									SWIN_VS_RPOT_FLAG_INPUT,
									PPFD_VS_RPOT_FLAG_INPUT,
									SWIN_VS_PPFD_FLAG_INPUT,
									SPIKE_NEE_FLAG_INPUT,
									SPIKE_LE_FLAG_INPUT,
									SPIKE_H_FLAG_INPUT,
									QC2_NEE_FLAG_INPUT,
									QC2_LE_FLAG_INPUT,
									QC2_H_FLAG_INPUT
	};

	/* */
	assert(dataset);

	/* create file */
	sprintf(buffer, "%s%s_qca_db_%d.csv", output_path, dataset->details->site, dataset->details->year);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create db file!");
		return 0;
	}

	/* write dataset details */
	if ( !write_dd_with_notes(f, dataset) ) {
		fclose(f);
		return 0;
	}

	/* write header (var) */
	if ( one_timestamp ) {
		fputs(TIMESTAMP_STRING, f);
	} else {
		fputs(TIMESTAMP_HEADER, f);
	}
	for ( i = 0; i < SIZEOF_ARRAY(vars_index); i++ ) {
		var = get_var_index(dataset, var_names[vars_index[i]]);
		if ( var != -1 ) {
			fprintf(f, ",%s", var_names[vars_index[i]]);
			/*
			if ( dataset->header[var].index ) {
				fprintf(f, "_%d", dataset->header[var].index);
			}
			*/
		}
	}

	/* write header (flag) */
	for ( i = 0; i < SIZEOF_ARRAY(flags_index); i++ ) {
		flag = get_flag_index(dataset, var_flag_names[flags_index[i]]);
		if ( flag != -1 ) {
			fprintf(f, ",FLAG_%s", var_flag_names[flags_index[i]]);
		}
	}
	fputs("\n", f);

	/* write... */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* ...timestamp_start.... */
		if ( ! one_timestamp ) {
			fprintf(f, "%s,", timestamp_start_by_row_s(i, dataset->details->year, dataset->details->timeres));
		}
		/* ...timestamp_end.... */
		fprintf(f, "%s", timestamp_end_by_row_s(i, dataset->details->year, dataset->details->timeres));
		/* ...values... */
		for ( y = 0; y < SIZEOF_ARRAY(vars_index); y++ ) {
			var = get_var_index(dataset, var_names[vars_index[y]]);
			if( var != -1 ) {
				fprintf(f, ",%g", dataset->rows[i].value[var]);
			}
		}
		/* ...flags... */
		for ( y = 0; y < SIZEOF_ARRAY(flags_index); y++ ) {
			flag = get_flag_index(dataset, var_flag_names[flags_index[y]]);
			if( flag != -1 ) {
				fprintf(f, ",%g", dataset->flags[i].value[flag]);
			}
		}
		fputs("\n", f);
	}

	/* */
	fclose(f);

	/* */
	return 1;
}

/* */
static void get_month_and_day_by_doy(const int doy, const int year, int *const month, int *const day) {
	int monthdays;
	int is_leap;
	int days_in_month[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

	/* reset */
	*day = 0;
	*month = 0;
	monthdays = 0;

	is_leap = IS_LEAP_YEAR(year);

	/* check */
	if ( (doy <= 0) || (doy > 365 + is_leap) ) {
		return;
	}

	/* */
	if ( is_leap ) {
		++days_in_month[1];
	}

	/* */
	while ( doy > monthdays ) {
		monthdays += days_in_month[(*month)++];
	}
    *day = doy - monthdays + days_in_month[*month-1];
}

/* */
int get_doy_by_timestamp(const TIMESTAMP *const t) {
	int i;
	int y;
	const int days_in_month[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

	/* */
	if ( ! t ) {
		return -1;
	}

	y = 0;
	for (i = 0; i < t->MM - 1; i++ ) {
		y += days_in_month[i];
		if ( (i == FEBRUARY) && IS_LEAP_YEAR(t->YYYY) ) {
			++y;
		}
	}

	/* */
	return y+t->DD;
}


/* */
static int compute_solar_noon(DATASET *const dataset) {
	int a;
	int i;
	int y;
	int error;
	int rows_in_day;
	int start;
	int end;
	int rows_count;
	int solar_noon;
	int neg_lat;
	int day;
	FILE *f;
	char buffer[256];
	PREC *maxs;
	PREC *swin_perc95;
	PREC *maxs_ppfd;
	PREC *ppfd_perc95;
	PREC *temp;
	double *rpots;
	int period;
	int periods_count;
	int PERIODS;
	int p_month;
	int p_day;
	int is_itpSWin;
	int is_itpPPFD;
	SUMPERIOD sum[3];
	int SWIN;
	int PPFD;
	int RPOT;
	int TEMP;
	SOLAR_NOON_PERIOD *periods;

	/* init */
	PERIODS = SIZEOF_ARRAY(solar_noon_periods);
	periods = malloc(PERIODS*sizeof*periods);
	if ( !periods ) {
		puts(err_out_of_memory);
		return 0;
	}
	for ( i = 0; i < PERIODS; i++ ) {
		periods[i].start = solar_noon_periods[i].start;
		periods[i].end = solar_noon_periods[i].end;
		periods[i].first = solar_noon_periods[i].first;
		periods[i].month = solar_noon_periods[i].month;
	}
	/* check if doy is same day of time zone change */
	for ( i = 0; i < dataset->details->time_zones_count; i++ ) {
		for ( y = 0; y < PERIODS; y++ ) {
			if ( periods[y].first == get_doy_by_timestamp(&dataset->details->time_zones[i].timestamp) ) {
				++periods[y].first;
			}
		}
	}

	PERIODS /= 2;
	period = 0;
	periods_count = PERIODS;
	rows_in_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;
	for ( i = 0; i < PERIODS; i++ ) {
		sum[i].swin = 0;
		sum[i].ppfd = 0;
	}
	is_itpSWin = 0;
	is_itpPPFD = 0;

	SWIN = get_var_index(dataset, var_names[SWIN_ORIGINAL]);
	if ( -1 == SWIN ) {
		/* get itp */
		SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
		if ( -1 != SWIN ) {
			is_itpSWin = 1;
		}
	}

	PPFD = get_var_index(dataset, var_names[PPFD_ORIGINAL]);
	if ( -1 == PPFD ) {
		/* get itp */
		PPFD = get_var_index(dataset, var_names[itpPPFD_INPUT]);
		if ( -1 != PPFD ) {
			is_itpPPFD = 1;
		}
	}

	if ( (-1 == SWIN) &&(-1 == PPFD) ) {
		printf("%s and %s missings!\n", var_names[SWIN_INPUT], var_names[PPFD_INPUT]);
		free(periods);
		return 0;
	}

	TEMP = get_var_index(dataset, var_names[TEMP_INPUT]);
	if ( -1 == TEMP ) {
		puts("unable to get temp var.");
		free(periods);
		return 0;
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		dataset->rows[i].value[TEMP] = INVALID_VALUE;
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[PPFD]) ) {
			dataset->rows[i].value[TEMP] = dataset->rows[i].value[PPFD] * 0.52;
		}
	}

	PPFD = TEMP;

	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	if ( -1 == RPOT ) {
		printf("unable to get %s.\n", var_names[RPOT_INPUT]);
		free(periods);
		return 0;
	}

	/* check latitude */
	neg_lat = 0;
	if ( dataset->details->lat < 0 ) {
		neg_lat = PERIODS;
	}

	/* check doy */
	if ( doy < 0 ) {
		printf(err_negative_doy, doy);
		free(periods);
		return 0;
	} else if ( doy > 0 ) {
		/* check if doy is same day of time zone switch */
		for ( i = 0; i < dataset->details->time_zones_count; i++ ) {
			if ( doy == get_doy_by_timestamp(&dataset->details->time_zones[i].timestamp) ) {
				++doy;
				break;
			}
		}

		rows_count = (dataset->leap_year ? 366 : 365);
		if ( doy > rows_count ) {
			printf("doy can't be > than %d: %d\n", rows_count, doy);
			free(periods);
			return 0;
		}
		start = doy - 10;
		if ( start <= 0 ) {
			start = 1;
		}
		end = doy + 10;
		if ( end > rows_count ) {
			end = rows_count;
		}
		periods[0].start = start;
		periods[0].end = end;
		periods[0].first = doy;
		get_month_and_day_by_doy(doy, dataset->details->year, &periods[0].month, &day);

		periods_count = 1;
		neg_lat = 0;
	}

	/* check period */
	while ( period < periods_count ) {
		start = periods[period + neg_lat].start - 1;
		end = periods[period + neg_lat].end - 1;
		if ( dataset->leap_year ) {
			if ( start > 59 ) {		/* February 28 */
				++start;
			}
			if ( end > 59 ) {		/* February 28 */
				++end;
			}
		}

		/* */
		assert(start < end);

		/* */
		rows_count = end - start;
		start *= rows_in_day;
		end *= rows_in_day;

		/* check valid value */
		sum[period].period = period;
		for ( i = 0; i < rows_in_day; i++ ) {
			for ( y = start; y < end; y += rows_in_day ) {
				if ( !IS_INVALID_VALUE(dataset->rows[i+y].value[SWIN]) ) {
					++sum[period].swin;
				}

				if ( !IS_INVALID_VALUE(dataset->rows[i+y].value[PPFD]) ) {
					++sum[period].ppfd;
				}
			}
		}
		++period;
	}

	/* select period */
	period = -1;
	for ( i = 0 ; i < PERIODS; i++ ) {
		if ( sum[i].swin && sum[i].ppfd ) {
			period = i;
			break;
		}
	}

	if ( -1 == period ) {
		for ( i = 0 ; i < PERIODS; i++ ) {
			if ( sum[i].swin || sum[i].ppfd ) {
				period = i;
				break;
			}
		}

		if ( -1 == period ) {
			puts("no valid period found.");
			free(periods);
			return 0;
		}
	}

	/* check for 20% */
	for ( i = 0 ; i < PERIODS; i++ ) {
		if ( i == period ) {
			continue;
		}

		if (	(sum[i].swin && (sum[i].swin >= sum[period].swin+sum[period].swin*0.2)) ||
				(sum[i].ppfd && (sum[i].ppfd >= sum[period].ppfd+sum[period].ppfd*0.2)) ) {
				period = i;
		}
	}

	if ( (0 == sum[period].swin) && (0 == sum[period].ppfd) ) {
		puts("no valid values in period found.");
		free(periods);
		return 1;
	}

	/* compute RPOT */
	p_day = 1;
	p_month = periods[period].month;
	rpots = get_rpot_with_solar_noon(dataset->details, p_month, p_day, &solar_noon);
	if ( !rpots ) {
		return 0;
	}

	/* free memory */
	free(rpots);
	rpots = NULL;

	/* recompute all */
	start = periods[period + neg_lat].start - 1;
	end = periods[period + neg_lat].end - 1;
	if ( dataset->leap_year ) {
		if ( start > 59 ) {		/* February 28 */
			++start;
		}
		if ( end > 59 ) {		/* February 28 */
			++end;
		}
	}

	/* */
	rows_count = end - start;
	if ( rows_count < 0 ) {
		rows_count = (dataset->leap_year ? 366 : 365) - start + end;
	}
	start *= rows_in_day;
	end *= rows_in_day;

	/* alloc memory */
	maxs = malloc(sizeof*maxs*rows_in_day);
	if ( !maxs ) {
		puts(err_out_of_memory);
		free(periods);
		return 0;
	}

	swin_perc95 = malloc(sizeof*swin_perc95*rows_in_day);
	if ( !swin_perc95 ) {
		puts(err_out_of_memory);
		free(periods);
		free(maxs);
		return 0;
	}

	maxs_ppfd = malloc(sizeof*maxs_ppfd*rows_in_day);
	if ( !maxs_ppfd ) {
		puts(err_out_of_memory);
		free(periods);
		free(swin_perc95);
		free(maxs);
		return 0;
	}

	ppfd_perc95 = malloc(sizeof*ppfd_perc95*rows_in_day);
	if ( !ppfd_perc95 ) {
		puts(err_out_of_memory);
		free(periods);
		free(maxs_ppfd);
		free(swin_perc95);
		free(maxs);
		return 0;
	}

	temp = malloc(sizeof*temp*rows_count);
	if ( !temp ) {
		puts(err_out_of_memory);
		free(periods);
		free(maxs_ppfd);
		free(ppfd_perc95);
		free(swin_perc95);
		free(maxs);
		return 0;
	}

	/* */
	for ( i = 0; i < rows_in_day; i++ ) {
		maxs[i] = INVALID_VALUE;
		maxs_ppfd[i] = INVALID_VALUE;
		for ( y = start; y < end; y += rows_in_day ) {
			if ( dataset->rows[i+y].value[SWIN] > maxs[i] ) {
				maxs[i] = dataset->rows[i+y].value[SWIN];
			}

			if ( dataset->rows[i+y].value[PPFD] > maxs_ppfd[i] ) {
				maxs_ppfd[i] = dataset->rows[i+y].value[PPFD];
			}
		}
	}

	for ( i = 0; i < rows_in_day; i++ ) {
		a = 0;
		for ( y = start; y < end; y += rows_in_day ) {
			temp[a++] = dataset->rows[i+y].value[SWIN];
		}
		swin_perc95[i] = get_percentile(temp, rows_count, 95, &error);
		if ( error ) {
			swin_perc95[i] = INVALID_VALUE;

		}
		a = 0;
		for ( y = start; y < end; y += rows_in_day ) {
			temp[a++] = dataset->rows[i+y].value[PPFD];
		}
		ppfd_perc95[i] = get_percentile(temp, rows_count, 95, &error);
		if ( error ) {
			ppfd_perc95[i] = INVALID_VALUE;
		}
	}

	/* free */
	free(temp);
	temp = NULL;

	/* create file */
	if ( doy ) {
		sprintf(buffer, "%s%s_qca_solar_noon_%d_custom_doy_%d.csv",	output_path,
																	dataset->details->site,
																	dataset->details->year,
																	doy
		);
	} else {
		sprintf(buffer, "%s%s_qca_solar_noon_%d.csv",				output_path,
																	dataset->details->site,
																	dataset->details->year
		);
	}
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create solar noon file!");
		free(periods);
		free(maxs_ppfd);
		free(ppfd_perc95);
		free(swin_perc95);
		free(maxs);
		return 0;
	}

	start = periods[period + neg_lat].first - 1;
	if ( dataset->leap_year ) {
		if ( start > 59 ) {		/* February 28 */
			++start;
		}
	}
	start *= rows_in_day;
	fprintf(f, "site,%s\n", dataset->details->site);
	fprintf(f, "year,%d\n", dataset->details->year);
	fprintf(f, "solar_noon,%d\n", solar_noon);
	if ( doy ) {
		fprintf(f, "periods,%d,%d\n", periods[0].month, day);
	} else {
		fprintf(f, "periods,%d\n", period+neg_lat+1);
	}
	fprintf(f, "timeres,%s\n", get_timeres_in_string(dataset->details->timeres));
	fprintf(f, "%s%s,%s%s_95,%s_%s%s,%s_%s%s_95,%s\n",	is_itpSWin ? "itp" : "", var_names[SWIN_INPUT],
														is_itpSWin ? "itp" : "", var_names[SWIN_INPUT],
														var_names[SWIN_INPUT], is_itpPPFD ? "itp" : "", var_names[PPFD_INPUT],
														var_names[SWIN_INPUT], is_itpPPFD ? "itp" : "", var_names[PPFD_INPUT],
														var_names[RPOT_INPUT]
	);
	for ( i = 0; i < rows_in_day; i++ ) {
		fprintf(f, "%g,%g,%g,%g,%g\n", maxs[i], swin_perc95[i], maxs_ppfd[i], ppfd_perc95[i], dataset->rows[start+i].value[RPOT]);

	}
	fclose(f);
	free(periods);
	free(ppfd_perc95);
	free(maxs_ppfd);
	free(swin_perc95);
	free(maxs);

	/* ok */
	return 1;
}


/* */
static int save_graph_file(DATASET *const dataset) {
	int i;
	int y;
	int var;
	int flag;
	int SWIN;
	int PPFD;
	int SWIN_FROM_PPFD;
	FILE *f;
	char buffer[256];
	const int vars_index[] = {
									NEE_INPUT,
									LE_INPUT,
									H_INPUT,
									VPD_INPUT,
									itpVPD_INPUT,
									RPOT_INPUT,
									SWIN_ORIGINAL,
									itpSWIN_INPUT,
									PPFD_ORIGINAL,
									itpPPFD_INPUT,
									USTAR_INPUT,
									WS_INPUT,
	};

	const int flags_index[] = {
									NEE_FLAG_INPUT,
									USTAR_FLAG_INPUT,
									MARGINAL_NEE_FLAG_INPUT,
									MARGINAL_LE_FLAG_INPUT,
									MARGINAL_H_FLAG_INPUT,
									SWIN_VS_RPOT_FLAG_INPUT,
									PPFD_VS_RPOT_FLAG_INPUT,
									SWIN_VS_PPFD_FLAG_INPUT,
									SPIKE_NEE_FLAG_INPUT,
									SPIKE_LE_FLAG_INPUT,
									SPIKE_H_FLAG_INPUT,
									QC2_NEE_FLAG_INPUT,
									QC2_LE_FLAG_INPUT,
									QC2_H_FLAG_INPUT
	};

	/* */
	assert(dataset);

	SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
	PPFD = get_var_index(dataset, var_names[PPFD_INPUT]);
	SWIN_FROM_PPFD = get_flag_index(dataset, var_flag_names[SWIN_FROM_PPFD_FLAG_INPUT]);
	assert(-1 != SWIN_FROM_PPFD);

	/* create file */
	if ( solar_output ) {
		sprintf(buffer, "%s%s_qcv_shift_graph_%d.csv", output_path, dataset->details->site, dataset->details->year);
	} else {
		sprintf(buffer, "%s%s_qca_graph_%d.csv", output_path, dataset->details->site, dataset->details->year);
	}
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create graph file!");
		return 0;
	}

	/* write dataset details */
	if ( ! write_dd_with_notes(f, dataset) ) {
		fclose(f);
		return 0;
	}

	/* write header (var) */
	if ( one_timestamp ) {
		fputs(TIMESTAMP_STRING, f);
	} else {
		fputs(TIMESTAMP_HEADER, f);
	}
	for ( i = 0; i < SIZEOF_ARRAY(vars_index); i++ ) {
		var = get_var_index(dataset, var_names[vars_index[i]]);
		if ( var != -1 ) {
			if ( SWIN_ORIGINAL == vars_index[i] ) {
				if ( SWIN != -1 ) {
					fprintf(f, ",%s", var_names[SWIN_INPUT]);
				}
			} else if ( PPFD_ORIGINAL == vars_index[i] ) {
				if ( PPFD != -1 ) {
					fprintf(f, ",%s", var_names[PPFD_INPUT]);
				}
			} else {
				fprintf(f, ",%s", var_names[vars_index[i]]);
			}
			/*
			if ( dataset->header[var].index ) {
				fprintf(f, "_%d", dataset->header[var].index);
			}
			*/
		}
	}

	/* write header (flag) */
	for ( i = 0; i < SIZEOF_ARRAY(flags_index); i++ ) {
		flag = get_flag_index(dataset, var_flag_names[flags_index[i]]);
		if ( flag != -1 ) {
			fprintf(f, ",FLAG_%s", var_flag_names[flags_index[i]]);
		}
	}
	fputs("\n", f);

	/* write... */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* ...timestamp_start.... */
		if ( ! one_timestamp ) {
			fprintf(f, "%s,", timestamp_start_by_row_s(i, dataset->details->year, dataset->details->timeres));
		}
		/* ...timestamp_end.... */
		fprintf(f, "%s", timestamp_end_by_row_s(i, dataset->details->year, dataset->details->timeres));
		/* ...values... */
		for ( y = 0; y < SIZEOF_ARRAY(vars_index); y++ ) {
			var = get_var_index(dataset, var_names[vars_index[y]]);
			if( var != -1 ) {
				if ( (SWIN_ORIGINAL == vars_index[y]) && (-1 == SWIN) ) {
					continue;
				} else if ( (PPFD_ORIGINAL == vars_index[y]) &&(-1 == PPFD) ) {
					continue;
				}
				fprintf(f, ",%g", dataset->rows[i].value[var]);
			}
		}
		/* ...flags... */
		for ( y = 0; y < SIZEOF_ARRAY(flags_index); y++ ) {
			flag = get_flag_index(dataset, var_flag_names[flags_index[y]]);
			if( flag != -1 ) {
				fprintf(f, ",%g", dataset->flags[i].value[flag]);
			}
		}
		fputs("\n", f);
	}

	/* */
	fclose(f);
	printf("ok\n	- saving solar noon file...");

	/* write solar noon file */
	if ( solar_output ) {
		return 1;
	} else {
		return compute_solar_noon(dataset);
	}
}

/* */
static int save_nee_file(DATASET *const dataset) {
	int i;
	int y;
	int var;
	FILE *f;
	char buffer[256];
	const int vars_index[] = {
									NEE_INPUT,
									VPD_INPUT,
									itpVPD_INPUT,
									RPOT_INPUT,
									USTAR_INPUT,
									TA_INPUT,
									itpTA_INPUT,
									SWIN_INPUT,
									itpSWIN_INPUT
	};

	/* */
	assert(dataset);

	/* check for mandatory values */
	i = get_var_index(dataset, var_names[NEE_INPUT]);
	if ( -1 == i ) {
		/* added on 20160822 */
		i = get_var_index(dataset, var_names[FC_INPUT]);
		y = 0;
		if ( i != -1 ) {
			y = (dataset->rows_count == dataset->missings[i]);
		}
		if ( (-1 == i) || y )  {
			printf("var %s was not computed, FC is missing. file will be not created\n", var_names[NEE_INPUT]);
		} else {
			printf("var %s is missing. file will be not created\n", var_names[NEE_INPUT]);
		}
		return 0;
	}

	i = get_var_index(dataset, var_names[USTAR_INPUT]);
	if ( -1 == i ) {
		printf("var %s is missing. file will be not created.\n", var_names[USTAR_INPUT]);
		return 0;
	}

	i = get_var_index(dataset, var_names[SWIN_INPUT]);
	if ( -1 == i ) {
		/* get itp */
		i = get_var_index(dataset, var_names[itpSWIN_INPUT]);
		if ( -1 == i ) {
			printf("var %s is missing. file will be not created.\n", var_names[SWIN_INPUT]);
			return 0;
		}
	}

	/* create file */
	sprintf(buffer, "%s%s_qca_nee_%d.csv", output_path, dataset->details->site, dataset->details->year);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create nee file!");
		return 0;
	}

	/* write dataset details */
	if ( ! write_dd_with_notes(f, dataset) ) {
		fclose(f);
		return 0;
	}

	/* write header (var) */
	if ( one_timestamp ) {
		fputs(TIMESTAMP_STRING, f);
	} else {
		fputs(TIMESTAMP_HEADER, f);
	}
	for ( i = 0; i < SIZEOF_ARRAY(vars_index); i++ ) {
		var = get_var_index(dataset, var_names[vars_index[i]]);
		if ( var != -1 ) {
			fprintf(f, ",%s", var_names[vars_index[i]]);
			/*
			if ( dataset->header[var].index ) {
				fprintf(f, "_%d", dataset->header[var].index);
			}
			*/
		}
	}
	fputs("\n", f);

	/* write... */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* ...timestamp_start.... */
		if ( ! one_timestamp ) {
			fprintf(f, "%s,", timestamp_start_by_row_s(i, dataset->details->year, dataset->details->timeres));
		}
		/* ...timestamp_end.... */
		fprintf(f, "%s", timestamp_end_by_row_s(i, dataset->details->year, dataset->details->timeres));
		/* ...values... */
		for ( y = 0; y < SIZEOF_ARRAY(vars_index); y++ ) {
			var = get_var_index(dataset, var_names[vars_index[y]]);
			if( var != -1 ) {
				fprintf(f, ",%g", dataset->rows[i].value[var]);
			}
		}
		fputs("\n", f);
	}

	/* */
	fclose(f);

	/* */
	return 1;
}

/* */
static int save_energy_file(DATASET *const dataset) {
	int i;
	int y;
	int var;
	FILE *f;
	char buffer[256];
	const int vars_index[] = {
									H_INPUT,
									LE_INPUT,
									SWIN_INPUT,
									itpSWIN_INPUT,
									TA_INPUT,
									itpTA_INPUT,
									RH_INPUT,
									itpRH_INPUT,
									NETRAD_INPUT,
									G_INPUT,
									VPD_INPUT,
									itpVPD_INPUT,

	};

	/* */
	assert(dataset);

	/* added on October 25, 2016 */
	{
		/* check H */
		var = get_var_index(dataset, var_names[H_INPUT]);
		if ( (-1 == var) || (dataset->rows_count == dataset->missings[var]) ) {
			printf("%s missing. File will be not created.", var_names[H_INPUT]);
			return 1;
		}

		/* check LE */
		var = get_var_index(dataset, var_names[LE_INPUT]);
		if ( (-1 == var) || (dataset->rows_count == dataset->missings[var]) ) {
			printf("%s missing. File will be not created.", var_names[LE_INPUT]);
			return 1;
		}
	}

	/* check how many vars can be written */
	y = 0;
	for ( i = 0; i < SIZEOF_ARRAY(vars_index); i++ ) {
		var = get_var_index(dataset, var_names[vars_index[i]]);
		if ( var != -1 ) {
			++y;
		}
	}
	if ( !y ) {
		puts("No vars to write. File will be not created.");
		return 1;
	}

	/* create file */
	sprintf(buffer, "%s%s_qca_energy_%d.csv", output_path, dataset->details->site, dataset->details->year);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create energy file!");
		return 0;
	}

	/* write dataset details */
	if ( !write_dd_with_notes(f, dataset) ) {
		fclose(f);
		return 0;
	}

	/* write header (var) */
	if ( one_timestamp ) {
		fputs(TIMESTAMP_STRING, f);
	} else {
		fputs(TIMESTAMP_HEADER, f);
	}
	for ( i = 0; i < SIZEOF_ARRAY(vars_index); i++ ) {
		var = get_var_index(dataset, var_names[vars_index[i]]);
		if ( var != -1 ) {
			fprintf(f, ",%s", var_names[vars_index[i]]);
			/*
			if ( dataset->header[var].index ) {
				fprintf(f, "_%d", dataset->header[var].index);
			}
			*/
		}
	}
	fputs("\n", f);

	/* write... */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* ...timestamp_start.... */
		if ( ! one_timestamp ) {
			fprintf(f, "%s,", timestamp_start_by_row_s(i, dataset->details->year, dataset->details->timeres));
		}
		/* ...timestamp_end.... */
		fprintf(f, "%s", timestamp_end_by_row_s(i, dataset->details->year, dataset->details->timeres));
		/* ...values... */
		for ( y = 0; y < SIZEOF_ARRAY(vars_index); y++ ) {
			var = get_var_index(dataset, var_names[vars_index[y]]);
			if( var != -1 ) {
				fprintf(f, ",%g", dataset->rows[i].value[var]);
			}
		}
		fputs("\n", f);
	}

	/* */
	fclose(f);

	/* */
	return 1;
}

/* */
static int save_ustar_file(DATASET *const dataset) {
	int i;
	int y;
	int var;
	FILE *f;
	char buffer[256];
	const int vars_index[] = {
									NEE_INPUT,
									TA_INPUT,
									itpTA_INPUT,
									USTAR_INPUT,
									SWIN_INPUT,
									itpSWIN_INPUT,
									PPFD_INPUT,
									itpPPFD_INPUT,
	};

	/* */
	assert(dataset);

	/* added on 20160822 */
	/* do not create u* file if u* is missing */
	var = get_var_index(dataset, var_names[USTAR_INPUT]);
	if ( -1 != var ) {
		if ( dataset->rows_count == dataset->missings[var] ) {
			var = -1;
		}
	}
	if ( -1 == var ) {
		printf("%s missing! file will be not created\n", var_names[USTAR_INPUT]);
		return 0;
	}
	/* do not create u* file if nee is missing */
	var = get_var_index(dataset, var_names[NEE_INPUT]);
	if ( -1 != var ) {
		if ( dataset->rows_count == dataset->missings[var] ) {
			var = -1;
		}
	}
	if ( -1 == var ) {
		var = get_var_index(dataset, var_names[FC_INPUT]);
		y = 0;
		if ( var != -1 ) {
			y = (dataset->rows_count == dataset->missings[var]);
		}
		if ( (-1 == var) || y )  {
			printf("var %s was not computed, %s is missing. file will be not created\n", var_names[NEE_INPUT], var_names[FC_INPUT]);
		} else {
			printf("var %s is missing. file will be not created\n", var_names[NEE_INPUT]);
		}
		return 0;
	}		

	/* create file */
	sprintf(buffer, "%s%s_qca_ustar_%d.csv", output_path, dataset->details->site, dataset->details->year);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create ustar file!");
		return 0;
	}

	/* write dataset details */
	if ( !write_dd_with_notes(f, dataset) ) {
		fclose(f);
		return 0;
	}

	/* write header (var) */
	if ( one_timestamp ) {
		fputs(TIMESTAMP_STRING, f);
	} else {
		fputs(TIMESTAMP_HEADER, f);
	}
	for ( i = 0; i < SIZEOF_ARRAY(vars_index); i++ ) {
		var = get_var_index(dataset, var_names[vars_index[i]]);
		if ( var != -1 ) {
			fprintf(f, ",%s", var_names[vars_index[i]]);
			/*
			if ( dataset->header[var].index ) {
				fprintf(f, "_%d", dataset->header[var].index);
			}
			*/
		}
	}
	fputs("\n", f);

	/* write... */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* ...timestamp_start.... */
		if ( ! one_timestamp ) {
			fprintf(f, "%s,", timestamp_start_by_row_s(i, dataset->details->year, dataset->details->timeres));
		}
		/* ...timestamp_end.... */
		fprintf(f, "%s", timestamp_end_by_row_s(i, dataset->details->year, dataset->details->timeres));
		/* ...values... */
		for ( y = 0; y < SIZEOF_ARRAY(vars_index); y++ ) {
			var = get_var_index(dataset, var_names[vars_index[y]]);
			if ( var != -1 ) {
				/* commented out on June 27, 2013
				if ( (y == NEE_INPUT) && (flag != -1) ) {
					fprintf(f, "%g", (2 == dataset->flags[i].value[flag]) ? INVALID_VALUE : dataset->rows[i].value[var]);
				} else {
					*/
					fprintf(f, ",%g", dataset->rows[i].value[var]);
				/*
				}
				*/
			}
		}
		fputs("\n", f);
	}

	/* */
	fclose(f);

	/* */
	return 1;
}

/* */
static int save_solar_file(DATASET *const dataset) {
	int a;
	int i;
	int y;
	int error;
	int rows_in_day;
	int start;
	int end;
	int rows_count;
	int solar_noon;
	int neg_lat;
	int day;
	FILE *f;
	char buffer[256];
	PREC *maxs;
	PREC *swin_perc95;
	PREC *maxs_ppfd;
	PREC *ppfd_perc95;
	PREC *temp;
	double *rpots;
	int period;
	int periods_count;
	int PERIODS;
	int p_month;
	int p_day;
	int is_itpSWin;
	int is_itpPPFD;
	SUMPERIOD sum[3];
	int SWIN;
	int PPFD;
	int RPOT;
	int TEMP;
	int solar_doy;
	int doy_loop;
	SOLAR_NOON_PERIOD *periods;

	/* init */
	PERIODS = SIZEOF_ARRAY(solar_noon_periods);
	periods = malloc(PERIODS*sizeof*periods);
	if ( !periods ) {
		puts(err_out_of_memory);
		return 0;
	}
	for ( i = 0; i < PERIODS; i++ ) {
		periods[i].start = solar_noon_periods[i].start;
		periods[i].end = solar_noon_periods[i].end;
		periods[i].first = solar_noon_periods[i].first;
		periods[i].month = solar_noon_periods[i].month;
	}
	/* check if doy is same day of time zone change */
	for ( i = 0; i < dataset->details->time_zones_count; i++ ) {
		for ( y = 0; y < PERIODS; y++ ) {
			if ( periods[y].first == get_doy_by_timestamp(&dataset->details->time_zones[i].timestamp) ) {
				++periods[y].first;
			}
		}
	}

	PERIODS /= 2;
	period = 0;
	periods_count = PERIODS;
	rows_in_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;
	for ( i = 0; i < PERIODS; i++ ) {
		sum[i].swin = 0;
		sum[i].ppfd = 0;
	}
	is_itpSWin = 0;
	is_itpPPFD = 0;

	SWIN = get_var_index(dataset, var_names[SWIN_ORIGINAL]);
	if ( -1 == SWIN ) {
		/* get itp */
		SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
		if ( -1 != SWIN ) {
			is_itpSWin = 1;
		}
	}

	PPFD = get_var_index(dataset, var_names[PPFD_ORIGINAL]);
	if ( -1 == PPFD ) {
		/* get itp */
		PPFD = get_var_index(dataset, var_names[itpPPFD_INPUT]);
		if ( -1 != PPFD ) {
			is_itpPPFD = 1;
		}
	}

	if ( (-1 == SWIN) &&(-1 == PPFD) ) {
		printf("%s and %s missings!", var_names[SWIN_INPUT], var_names[PPFD_INPUT]);
		free(periods);
		return 0;
	}

	TEMP = get_var_index(dataset, var_names[TEMP_INPUT]);
	if ( -1 == TEMP ) {
		puts("unable to get temp var.");
		free(periods);
		return 0;
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		dataset->rows[i].value[TEMP] = INVALID_VALUE;
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[PPFD]) ) {
			dataset->rows[i].value[TEMP] = dataset->rows[i].value[PPFD] * 0.52;
		}
	}

	PPFD = TEMP;

	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	if ( -1 == RPOT ) {
		printf("unable to get %s.", var_names[RPOT_INPUT]);
		free(periods);
		return 0;
	}

	/* check latitude */
	neg_lat = 0;
	if ( dataset->details->lat < 0 ) {
		neg_lat = PERIODS;
	}

	/* create file */
	sprintf(buffer, "%s%s_qcv_shift_solar_noon_%d.csv",				output_path,
																	dataset->details->site,
																	dataset->details->year
	);

	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create solar noon file!");
		free(periods);
		return 0;
	}

	fprintf(f, "site,%s\n", dataset->details->site);
	fprintf(f, "year,%d\n", dataset->details->year);
	fprintf(f, "timeres,%s\n", get_timeres_in_string(dataset->details->timeres));
	fprintf(f, "doy,%s%s,%s%s_95,%s_%s%s,%s_%s%s_95,%s\n",	is_itpSWin ? "itp" : "", var_names[SWIN_INPUT],
															is_itpSWin ? "itp" : "", var_names[SWIN_INPUT],
															var_names[SWIN_INPUT], is_itpPPFD ? "itp" : "", var_names[PPFD_INPUT],
															var_names[SWIN_INPUT], is_itpPPFD ? "itp" : "", var_names[PPFD_INPUT],
															var_names[RPOT_INPUT]
	);

	/* main loop */
	for ( doy_loop = 10; doy_loop < (dataset->leap_year ? 366 : 365); doy_loop += 20 ) {
		/* check if doy is same day of time zone switch */
		solar_doy = doy_loop;
		for ( i = 0; i < dataset->details->time_zones_count; i++ ) {
			if ( solar_doy == get_doy_by_timestamp(&dataset->details->time_zones[i].timestamp) ) {
				++solar_doy;
				break;
			}
		}

		/* */
		rows_count = (dataset->leap_year ? 366 : 365);

		/* */
		start = solar_doy - 10;
		if ( start <= 0 ) {
			start = 1;
		}
		end = solar_doy + 10;
		if ( end > rows_count ) {
			end = rows_count;
		}
		periods[0].start = start;
		periods[0].end = end;
		periods[0].first = solar_doy;
		get_month_and_day_by_doy(solar_doy, dataset->details->year, &periods[0].month, &day);

		period = 0;
		periods_count = 1;
		neg_lat = 0;
	
		/* check period */
		while ( period < periods_count ) {
			start = periods[period + neg_lat].start - 1;
			end = periods[period + neg_lat].end - 1;
			if ( dataset->leap_year ) {
				if ( start > 59 ) {		/* February 28 */
					++start;
				}
				if ( end > 59 ) {		/* February 28 */
					++end;
				}
			}

			/* */
			assert(start < end);

			/* */
			rows_count = end - start;
			start *= rows_in_day;
			end *= rows_in_day;

			/* check valid value */
			sum[period].period = period;
			for ( i = 0; i < rows_in_day; i++ ) {
				for ( y = start; y < end; y += rows_in_day ) {
					if ( !IS_INVALID_VALUE(dataset->rows[i+y].value[SWIN]) ) {
						++sum[period].swin;
					}

					if ( !IS_INVALID_VALUE(dataset->rows[i+y].value[PPFD]) ) {
						++sum[period].ppfd;
					}
				}
			}
			++period;
		}

		/* select period */
		period = -1;
		for ( i = 0 ; i < PERIODS; i++ ) {
			if ( sum[i].swin && sum[i].ppfd ) {
				period = i;
				break;
			}
		}

		if ( -1 == period ) {
			for ( i = 0 ; i < PERIODS; i++ ) {
				if ( sum[i].swin || sum[i].ppfd ) {
					period = i;
					break;
				}
			}

			if ( -1 == period ) {
				for ( i = 0; i < rows_in_day; i++ ) {
					fprintf(f, "%d,%d,%d,%d,%d,%d\n", solar_doy, INVALID_VALUE, INVALID_VALUE, INVALID_VALUE, INVALID_VALUE, INVALID_VALUE);
				}
				continue;
			}
		}

		/* check for 20% */
		for ( i = 0 ; i < PERIODS; i++ ) {
			if ( i == period ) {
				continue;
			}

			if (	(sum[i].swin && (sum[i].swin >= sum[period].swin+sum[period].swin*0.2)) ||
					(sum[i].ppfd && (sum[i].ppfd >= sum[period].ppfd+sum[period].ppfd*0.2)) ) {
					period = i;
			}
		}

		if ( (0 == sum[period].swin) && (0 == sum[period].ppfd) ) {
			for ( i = 0; i < rows_in_day; i++ ) {
				fprintf(f, "%d,%d,%d,%d,%d,%d\n", solar_doy, INVALID_VALUE, INVALID_VALUE, INVALID_VALUE, INVALID_VALUE, INVALID_VALUE);
			}
			continue;
		}

		/* compute RPOT */
		p_day = 1;
		p_month = periods[period].month;
		rpots = get_rpot_with_solar_noon(dataset->details, p_month, p_day, &solar_noon);
		if ( !rpots ) {
			fclose(f);
			return 0;
		}

		/* free memory */
		free(rpots);
		rpots = NULL;

		/* recompute all */
		start = periods[period + neg_lat].start - 1;
		end = periods[period + neg_lat].end - 1;
		if ( dataset->leap_year ) {
			if ( start > 59 ) {		/* February 28 */
				++start;
			}
			if ( end > 59 ) {		/* February 28 */
				++end;
			}
		}

		/* */
		rows_count = end - start;
		if ( rows_count < 0 ) {
			rows_count = (dataset->leap_year ? 366 : 365) - start + end;
		}
		start *= rows_in_day;
		end *= rows_in_day;

		/* alloc memory */
		maxs = malloc(sizeof*maxs*rows_in_day);
		if ( !maxs ) {
			puts(err_out_of_memory);
			free(periods);
			fclose(f);
			return 0;
		}

		swin_perc95 = malloc(sizeof*swin_perc95*rows_in_day);
		if ( !swin_perc95 ) {
			puts(err_out_of_memory);
			free(periods);
			free(maxs);
			fclose(f);
			return 0;
		}

		maxs_ppfd = malloc(sizeof*maxs_ppfd*rows_in_day);
		if ( !maxs_ppfd ) {
			puts(err_out_of_memory);
			free(periods);
			free(swin_perc95);
			free(maxs);
			fclose(f);
			return 0;
		}

		ppfd_perc95 = malloc(sizeof*ppfd_perc95*rows_in_day);
		if ( !ppfd_perc95 ) {
			puts(err_out_of_memory);
			free(periods);
			free(maxs_ppfd);
			free(swin_perc95);
			free(maxs);
			fclose(f);
			return 0;
		}

		temp = malloc(sizeof*temp*rows_count);
		if ( !temp ) {
			puts(err_out_of_memory);
			free(periods);
			free(maxs_ppfd);
			free(ppfd_perc95);
			free(swin_perc95);
			free(maxs);
			fclose(f);
			return 0;
		}

		/* */
		for ( i = 0; i < rows_in_day; i++ ) {
			maxs[i] = INVALID_VALUE;
			maxs_ppfd[i] = INVALID_VALUE;
			for ( y = start; y < end; y += rows_in_day ) {
				if ( dataset->rows[i+y].value[SWIN] > maxs[i] ) {
					maxs[i] = dataset->rows[i+y].value[SWIN];
				}

				if ( dataset->rows[i+y].value[PPFD] > maxs_ppfd[i] ) {
					maxs_ppfd[i] = dataset->rows[i+y].value[PPFD];
				}
			}
		}

		for ( i = 0; i < rows_in_day; i++ ) {
			a = 0;
			for ( y = start; y < end; y += rows_in_day ) {
				temp[a++] = dataset->rows[i+y].value[SWIN];
			}
			swin_perc95[i] = get_percentile(temp, rows_count, 95, &error);
			if ( error ) {
				swin_perc95[i] = INVALID_VALUE;

			}
			a = 0;
			for ( y = start; y < end; y += rows_in_day ) {
				temp[a++] = dataset->rows[i+y].value[PPFD];
			}
			ppfd_perc95[i] = get_percentile(temp, rows_count, 95, &error);
			if ( error ) {
				ppfd_perc95[i] = INVALID_VALUE;
			}
		}

		/* free */
		free(temp);
		temp = NULL;

		/* */
		start = periods[period + neg_lat].first - 1;
		if ( dataset->leap_year ) {
			if ( start > 59 ) {		/* February 28 */
				++start;
			}
		}
		start *= rows_in_day;

		for ( i = 0; i < rows_in_day; i++ ) {
			fprintf(f, "%d,%g,%g,%g,%g,%g\n", solar_doy, maxs[i], swin_perc95[i], maxs_ppfd[i], ppfd_perc95[i], dataset->rows[start+i].value[RPOT]);
		}

		/* free memory */
		free(ppfd_perc95);
		free(maxs_ppfd);
		free(swin_perc95);
		free(maxs);
	}

	/* close file */
	fclose(f);

	/* free emmory */
	free(periods);
	
	/* ok */
	return 1;
}

/* */
static int save_meteo_file(DATASET *const dataset) {
	int i;
	int y;
	int valids_count;

	int CO2;
	int P;
	int SWIN;
	int TA;
	int PA;
	int RH;
	int WS;
	int LWIN;
	int VPD;
	int RPOT;

	int is_itpSWIN;
	int is_itpTA;
	int is_itpTS;
	int is_itpRH;
	int is_itpP;
	int is_itpSWC;
	int is_itpVPD;

	int vpd_added;
	int co2_added;
	int p_added;
	int swin_added;
	int ta_added;
	int pa_added;
	int rh_added;
	int ws_added;
	int lwin_added;

	int row_per_day;

	int *swc_indexes;
	int swc_indexes_count;
	int *ts_indexes;
	int ts_indexes_count;

	const PREC sigma = 5.6696e-8;
	const PREC T0 = 273.15;
	const PREC Tstroke = 36;
	const PREC ESTAR = 611;
	const PREC A = 17.27;
	PREC value;
	FILE *f;
	char buffer[256];

	/* */
	assert(dataset);

	/* reset */
	is_itpSWIN = 0;
	is_itpTA = 0;
	is_itpTS = 0;
	is_itpRH = 0;
	is_itpP = 0;
	is_itpSWC = 0;
	is_itpVPD = 0;

	/* */
	vpd_added = 0;
	VPD = get_var_index(dataset, var_names[VPD_INPUT]);
	if ( -1 == VPD ) {
		/* check for itp */
		VPD = get_var_index(dataset, var_names[itpVPD_INPUT]);
		if ( -1 == VPD ) {
			VPD = add_var_to_dataset(dataset, var_names[VPD_INPUT]);
			if ( -1 == VPD ) {
				printf("unable to add %s var\n\n", var_names[VPD_INPUT]);
				return 0;
			} else {
				vpd_added = 1;
			}
		}
		is_itpVPD = 1;
	}

	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	if ( -1 == RPOT ) {
		printf("var %s is missing. file will be not created.\n", var_names[RPOT_INPUT]);
		return 0;
	}

	/* get index and check for other var */
	co2_added = 0;
	CO2 = get_var_index(dataset, var_names[CO2_INPUT]);
	if ( -1 == CO2 ) {
		CO2 = add_var_to_dataset(dataset, var_names[CO2_INPUT]);
		if ( -1 == CO2 ) {
			printf("unable to add %s var\n\n", var_names[CO2_INPUT]);
			return 0;
		} else {
			co2_added = 1;
		}
	}

	p_added = 0;
	P = get_var_index(dataset, var_names[P_INPUT]);
	if ( -1 == P ) {
		/* check for itp */
		P = get_var_index(dataset, var_names[itpP_INPUT]);
		if ( -1 == P ) {
			P = add_var_to_dataset(dataset, var_names[P_INPUT]);
			if ( -1 == P ) {
				printf("unable to add %s var\n\n", var_names[P_INPUT]);
				return 0;
			} else {
				p_added = 1;
			}
		} else {
			is_itpP = 1;
		}
	}

	swin_added = 0;
	SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
	if ( -1 == SWIN ) {
		SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
		if ( -1 == SWIN ) {
			SWIN = add_var_to_dataset(dataset, var_names[SWIN_INPUT]);
			if ( -1 == SWIN ) {
				printf("unable to add %s var\n\n", var_names[SWIN_INPUT]);
				return 0;
			} else {
				swin_added = 1;
			}
		} else {
			is_itpSWIN = 1;
		}
	}

	ta_added = 0;
	TA = get_var_index(dataset, var_names[TA_INPUT]);
	if ( -1 == TA ) {
		TA = get_var_index(dataset, var_names[itpTA_INPUT]);
		if ( -1 == TA ) {
			TA = add_var_to_dataset(dataset, var_names[TA_INPUT]);
			if ( -1 == TA ) {
				printf("unable to add %s var\n\n", var_names[TA_INPUT]);
				return 0;
			} else {
				ta_added = 1;
			}
		} else {
			is_itpTA = 1;
		}
	}

	pa_added = 0;
	PA = get_var_index(dataset, var_names[PA_INPUT]);
	if ( -1 == PA ) {
		PA = add_var_to_dataset(dataset, var_names[PA_INPUT]);
		if ( -1 == PA ) {
			printf("unable to add %s var\n\n", var_names[PA_INPUT]);
			return 0;
		} else {
			pa_added = 1;
		}
	}

	rh_added = 0;
	RH = get_var_index(dataset, var_names[RH_INPUT]);
	if ( -1 == RH ) {
		RH = get_var_index(dataset, var_names[itpRH_INPUT]);
		if ( -1 == RH ) {
			RH = add_var_to_dataset(dataset, var_names[RH_INPUT]);
			if ( -1 == RH ) {
				printf("unable to add %s var\n\n", var_names[RH_INPUT]);
				return 0;
			} else {
				rh_added = 1;
			}
		} else {
			is_itpRH = 1;
		}
	}

	ws_added = 0;
	WS = get_var_index(dataset, var_names[WS_INPUT]);
	if ( -1 == WS ) {
		WS = add_var_to_dataset(dataset, var_names[WS_INPUT]);
		if ( -1 == WS ) {
			printf("unable to add %s var\n\n", var_names[WS_INPUT]);
			return 0;
		} else {
			ws_added = 1;
		}
	}

	lwin_added = 0;
	LWIN = get_var_index(dataset, var_names[LWIN_INPUT]);
	if ( -1 == LWIN ) {
		LWIN = add_var_to_dataset(dataset, var_names[LWIN_INPUT]);
		if ( -1 == LWIN ) {
			printf("unable to add %s var\n\n", var_names[LWIN_INPUT]);
			return 0;
		} else {
			lwin_added = 1;
		}
	}

	swc_indexes = get_var_indexes(dataset, var_names[SWC_INPUT], &swc_indexes_count);
	if ( -1 == swc_indexes_count ) {
		/* memory error */
		return 0;
	}

	/* check for itp */
	if ( !swc_indexes ) {
		swc_indexes = get_var_indexes(dataset, var_names[itpSWC_INPUT], &swc_indexes_count);
		if ( -1 == swc_indexes_count ) {
			/* memory error */
			return 0;
		}
		if ( swc_indexes ) {
			is_itpSWC = 1;
		}
	}

	ts_indexes = get_var_indexes(dataset, var_names[TS_INPUT], &ts_indexes_count);
	if ( -1 == ts_indexes_count ) {
		/* memory error */
		return 0;
	}
	if ( !ts_indexes_count ) {
		/* check for itp */
		ts_indexes = get_var_indexes(dataset, var_names[itpTS_INPUT], &ts_indexes_count);
		if ( -1 == ts_indexes_count ) {
			/* memory error */
			return 0;
		}
		if ( ts_indexes_count ) {
			is_itpTS = 1;
		}
	}

	/* allocating memory for meteora */
	dataset->meteora = malloc(sizeof*dataset->meteora*dataset->rows_count);
	if ( !dataset->meteora ) {
		puts(err_out_of_memory);
		free(ts_indexes);
		free(swc_indexes);
		return 0;
	}

	/* reset */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		for ( y = 0; y < METEORA_VALUES; y++ ) {
			dataset->meteora[i].value[y] = INVALID_VALUE;
		}
	}

	/* hourly dataset ? */
	row_per_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;

	/* computing calc */
	for ( i = 0; i < dataset->rows_count; i += row_per_day ) {
		value = 0.0;
		valids_count = 0;
		for ( y = 0; y < row_per_day; y++ ) {

			assert(!IS_INVALID_VALUE(dataset->rows[i+y].value[RPOT]));

			dataset->meteora[i+y].value[FPAR] = INVALID_VALUE;
			if ( !ARE_FLOATS_EQUAL(dataset->rows[i+y].value[RPOT], 0.0) && !IS_INVALID_VALUE(dataset->rows[i+y].value[SWIN]) ) {
				dataset->meteora[i+y].value[FPAR] = dataset->rows[i+y].value[SWIN] / dataset->rows[i+y].value[RPOT];
				if ( dataset->meteora[i+y].value[FPAR] < 0.0 ) {
					dataset->meteora[i+y].value[FPAR] = 0.0;
				}
				value += dataset->meteora[i+y].value[FPAR];
				++valids_count;
			}
		}
		if ( valids_count )  {
			value /= valids_count; /* mean */
			for ( y = 0; y < row_per_day; y++ ) {
				if ( ARE_FLOATS_EQUAL(dataset->rows[i+y].value[RPOT], 0.0) ) {
					assert(dataset->meteora[i+y].value[FPAR] == INVALID_VALUE);
					dataset->meteora[i+y].value[FPAR] = value;
				}
			}
		}
	}

	value = 0.0;
	valids_count = 0;
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( !IS_INVALID_VALUE(dataset->meteora[i].value[FPAR]) ) {
			value += dataset->meteora[i].value[FPAR];
			++valids_count;
		}
	}

	if ( valids_count && (valids_count != dataset->rows_count) ) {
		value /= valids_count;
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( IS_INVALID_VALUE(dataset->meteora[i].value[FPAR]) ) {
				dataset->meteora[i].value[FPAR] = value;
			}
		}
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		if (	IS_INVALID_VALUE(dataset->meteora[i].value[FPAR]) ||
				IS_INVALID_VALUE(dataset->rows[i].value[TA]) ||
				IS_INVALID_VALUE(dataset->rows[i].value[VPD]) ) {
			dataset->meteora[i].value[LWIN_CALC] = INVALID_VALUE;
			continue;
		}

		/* Cloud cover and cloud correction factor Eq. (3) */
		dataset->meteora[i].value[CLOUD_COVER] = 1.0 - (dataset->meteora[i].value[FPAR] - 0.5) / 0.4;
		if ( dataset->meteora[i].value[CLOUD_COVER] > 1.0 ) {
			dataset->meteora[i].value[CLOUD_COVER] = 1.0;
		}
		if ( dataset->meteora[i].value[CLOUD_COVER] < 0.0 ) {
			dataset->meteora[i].value[CLOUD_COVER] = 0.0;
		}
		dataset->meteora[i].value[R_CLOUD] = 1 + 0.22 * SQUARE(dataset->meteora[i].value[CLOUD_COVER]);

		/* Saturation and actual Vapour pressure [3], and associated  emissivity Eq. (2) */
		/* esat=estar*exp(A*((T-Tstar)./(T-Tstroke))); */
		dataset->meteora[i].value[ESAT] = ESTAR * exp(A*((dataset->rows[i].value[TA]/((dataset->rows[i].value[TA]+T0)-Tstroke))));

		/* VP = esat - VPD;%'; */
		dataset->meteora[i].value[VP] = dataset->meteora[i].value[ESAT] - dataset->rows[i].value[VPD] * 100;

		/* VP(VP<0) = 0.00000008; */
		if ( dataset->meteora[i].value[VP] < 0.0 ) {
			dataset->meteora[i].value[VP] = 3.3546e-004;
		}

		dataset->meteora[i].value[epsA] = 0.64 *  pow(dataset->meteora[i].value[VP] / (dataset->rows[i].value[TA]+T0), 0.14285714);

		/* Longwave radiation flux downward Eq. (1) */
		dataset->meteora[i].value[LWIN_CALC] = dataset->meteora[i].value[R_CLOUD] * dataset->meteora[i].value[epsA] * sigma * pow(dataset->rows[i].value[TA]+T0, 4);
		if ( dataset->meteora[i].value[LWIN_CALC] != dataset->meteora[i].value[LWIN_CALC] ) {
			dataset->meteora[i].value[LWIN_CALC] = INVALID_VALUE;
		}
		if ( (dataset->meteora[i].value[LWIN_CALC] < 10.0) || (dataset->meteora[i].value[LWIN_CALC] > 1000.0) )  {
			dataset->meteora[i].value[LWIN_CALC] = INVALID_VALUE;
		}
	}

	/* write */
	sprintf(buffer, "%s%s_qca_synth_allvars_%d.csv", output_path, dataset->details->site, dataset->details->year);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create meteo file: '%s'\n", buffer);
		free(ts_indexes);
		free(swc_indexes);
		return 0;
	}
	fputs("Ta_f,Ta_fqcOK,VPD_f,VPD_fqcOK,Precip_f,Precip_fqcOK,WS_f,WS_fqcOK,Rg_f,Rg_fqcOK,LWin_f,LWin_fqcOK,Pa_f,Pa_fqcOK,LWin_calc,LWin_calcqcOK\n", f);

	for ( i = 0; i < dataset->rows_count; i++ ) {
		fprintf(f, "%g,%d,%g,%d,%g,%d,%g,%d,%g,%d,%g,%d,%g,%d,%g,%d\n",
																		dataset->rows[i].value[TA],
																		ta_added ? INVALID_VALUE : (IS_INVALID_VALUE(dataset->rows[i].value[TA]) ? 0 : 1),

																		dataset->rows[i].value[VPD],
																		vpd_added ? INVALID_VALUE : (IS_INVALID_VALUE(dataset->rows[i].value[VPD]) ? 0 : 1),

																		dataset->rows[i].value[P],
																		p_added ? INVALID_VALUE : (IS_INVALID_VALUE(dataset->rows[i].value[P]) ? 0 : 1),

																		dataset->rows[i].value[WS],
																		ws_added ? INVALID_VALUE : (IS_INVALID_VALUE(dataset->rows[i].value[WS]) ? 0 : 1),

																		dataset->rows[i].value[SWIN],
																		swin_added ? INVALID_VALUE : (IS_INVALID_VALUE(dataset->rows[i].value[SWIN]) ? 0 : 1),

																		dataset->rows[i].value[LWIN],
																		lwin_added ? INVALID_VALUE : (IS_INVALID_VALUE(dataset->rows[i].value[LWIN]) ? 0 : 1),

																		dataset->rows[i].value[PA],
																		pa_added ? INVALID_VALUE : (IS_INVALID_VALUE(dataset->rows[i].value[PA]) ? 0 : 1),

																		dataset->meteora[i].value[LWIN_CALC],
																		IS_INVALID_VALUE(dataset->meteora[i].value[LWIN_CALC]) ? 0 : 1
		);
	}

	/* close file */
	fclose(f);

	/* create output filename */
	sprintf(buffer, "%s%s_qca_meteo_%d.csv", output_path, dataset->details->site, dataset->details->year);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create meteo file: '%s'\n", buffer);
		free(ts_indexes);
		free(swc_indexes);
		return 0;
	}

	/* write dataset details */
	if ( !write_dd_with_notes(f, dataset) ) {
		fclose(f);
		free(ts_indexes);
		free(swc_indexes);
		return 0;
	}

	/* write header */
	if ( one_timestamp ) {
		fputs(TIMESTAMP_STRING, f);
	} else {
		fputs(TIMESTAMP_HEADER, f);
	}
	if ( dataset->rows_count != dataset->missings[CO2] ) fprintf(f, ",%s", var_names[CO2_INPUT]);
	if ( dataset->rows_count != dataset->missings[P] ) fprintf(f, ",%s", is_itpP ? var_names[itpP_INPUT] : var_names[P_INPUT]);
	if ( dataset->rows_count != dataset->missings[SWIN] ) fprintf(f, ",%s", is_itpSWIN ? var_names[itpSWIN_INPUT] : var_names[SWIN_INPUT]);
	if ( dataset->rows_count != dataset->missings[TA] ) fprintf(f, ",%s", is_itpTA ? var_names[itpTA_INPUT] : var_names[TA_INPUT]);
	if ( dataset->rows_count != dataset->missings[PA] ) fprintf(f, ",%s", var_names[PA_INPUT]);
	if ( dataset->rows_count != dataset->missings[RH] ) fprintf(f, ",%s", is_itpRH ? var_names[itpRH_INPUT] : var_names[RH_INPUT]);
	if ( dataset->rows_count != dataset->missings[WS] ) fprintf(f, ",%s", var_names[WS_INPUT]);
	if ( dataset->rows_count != dataset->missings[LWIN] ) fprintf(f, ",%s", var_names[LWIN_INPUT]);
	for ( i = 0; i < swc_indexes_count; i++ ) {
		if ( dataset->rows_count != dataset->missings[swc_indexes[i]] ) {
			fprintf(f, ",%s_%d", dataset->header[swc_indexes[i]].name, dataset->header[swc_indexes[i]].index);
		}
	}
	for ( i = 0; i < ts_indexes_count; i++ ) {
		if ( dataset->rows_count != dataset->missings[ts_indexes[i]] ) {
			fprintf(f, ",%s_%d", dataset->header[ts_indexes[i]].name, dataset->header[ts_indexes[i]].index);
		}
	}
	fprintf(f,",%s", is_itpVPD ? var_names[itpVPD_INPUT] : var_names[VPD_INPUT]);
	fprintf(f,",%s\n", var_names[RPOT_INPUT]);

	/* write values */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* ...timestamp_start.... */
		if ( ! one_timestamp ) {
			fprintf(f, "%s,", timestamp_start_by_row_s(i, dataset->details->year, dataset->details->timeres));
		}
		/* ...timestamp_end.... */
		fprintf(f, "%s", timestamp_end_by_row_s(i, dataset->details->year, dataset->details->timeres));
		/* ...values... */
		if ( dataset->rows_count != dataset->missings[CO2] ) fprintf(f, ",%g", dataset->rows[i].value[CO2]);
		if ( dataset->rows_count != dataset->missings[P] ) fprintf(f, ",%g", dataset->rows[i].value[P]);
		if ( dataset->rows_count != dataset->missings[SWIN] ) fprintf(f, ",%g", dataset->rows[i].value[SWIN]);
		if ( dataset->rows_count != dataset->missings[TA] ) fprintf(f, ",%g", dataset->rows[i].value[TA]);
		if ( dataset->rows_count != dataset->missings[PA] ) fprintf(f, ",%g", dataset->rows[i].value[PA]);
		if ( dataset->rows_count != dataset->missings[RH] ) fprintf(f, ",%g", dataset->rows[i].value[RH]);
		if ( dataset->rows_count != dataset->missings[WS] ) fprintf(f, ",%g", dataset->rows[i].value[WS]);
		if ( dataset->rows_count != dataset->missings[LWIN] ) fprintf(f, ",%g", dataset->rows[i].value[LWIN]);
		for ( y = 0; y < swc_indexes_count; y++ ) {
			if ( dataset->rows_count != dataset->missings[swc_indexes[y]] ) {
				fprintf(f, ",%g", dataset->rows[i].value[swc_indexes[y]]);
			}
		}
		for ( y = 0; y < ts_indexes_count; y++ ) {
			if ( dataset->rows_count != dataset->missings[ts_indexes[y]] ) {
				fprintf(f, ",%g", dataset->rows[i].value[ts_indexes[y]]);
			}
		}
		fprintf(f, ",%g", dataset->rows[i].value[VPD]);
		fprintf(f, ",%g\n", dataset->rows[i].value[RPOT]);
	}
	fclose(f);

	/* free memory */
	free(ts_indexes);
	free(swc_indexes);

	/* ok */
	return 1;
}

/* if not found, returns -1, on error returns -2 */
int get_minor_var_indexes(const DATASET *const dataset, const char *const name) {
	int i;
	int index;
	int *indexes;
	int *temp;
	int count;

	/* */
	assert(dataset && name);

	/* */
	count = 0;
	indexes = NULL;
	for ( i = 0; i < dataset->columns_count; ++i ) {
		if ( ! string_compare_i(dataset->header[i].name, name) ) {
			temp = realloc(indexes, ++count*sizeof*temp);
			if ( !temp ) {
				puts(err_out_of_memory);
				free(indexes);
				return -2;
			}
			indexes = temp;
			indexes[count-1] = i;
		}
	}
	if ( !count ) {
		return -1;
	}

	index = dataset->header[indexes[0]].index;
	for ( i = 0; i < count; i++ ) {
		if ( dataset->header[indexes[i]].index < index ) {
			index = dataset->header[indexes[i]].index;
		}
	}
	for ( i = 0; i < count; i++ ) {
		if ( dataset->header[indexes[i]].index == index ) {
			index = indexes[i];
			break;
		}
	}
	free(indexes);
	return index;
}


/* */
static int save_sr_file(DATASET *const dataset) {
	int i;
	int FC;
	int SC;
	int USTAR;
	int SWIN;
	int TS;
	int TA;
	int VPD;
	int process;
	int year;
	int error;
	char buffer[PATH_SIZE];
	char *token;
	char *p;
	const char sc_profile_file[] = "profiles_for_sc.csv";
	FILE *f;

	/* */
	assert(dataset);

	/* */
	strcpy(buffer, program_path);
	strcat(buffer, sc_profile_file);
	
	/* check for table */
	process = 0;
	f = fopen(buffer, "r");
	if ( !f ) {
		printf("failed. unable to open: \"%s\"\n", sc_profile_file);
		return 0;
	}

	while ( fgets(buffer, 256, f) ) {
		/* get site */
		token = string_tokenizer(buffer, ",\r\n", &p);
		if ( ! string_compare_i(token, dataset->details->site) ) {
			/* parse year */
			token = string_tokenizer(NULL, ",\r\n", &p);
			year = convert_string_to_int(token, &error);
			if ( error ) {
				printf("failed. unable to convert year: \"%s\"\n", token);
				fclose(f);
				return 0;
			}
			if ( year == dataset->details->year ) {
				process = 1;
				break;
			}
		}
	}

	fclose(f);

	if ( 0 == process ) {
		puts("site\\year not found in sc profile");
		return 0;
	}

	/* */
	FC = get_var_index(dataset, var_names[FC_INPUT]);
	if ( -1 == FC ) { printf("var %s is missing. file will be not created.\n", var_names[FC_INPUT]); return 0; }
	SC = get_var_index(dataset, var_names[SC_INPUT]);
	if ( -1 == SC ) { printf("var %s is missing. file will be not created.\n", var_names[SC_INPUT]); return 0; }
	USTAR = get_var_index(dataset, var_names[USTAR_INPUT]);
	if ( -1 == USTAR ) { printf("var %s is missing. file will be not created.\n", var_names[USTAR_INPUT]); return 0; }
	SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
	if ( -1 == SWIN ) {
		SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
		if ( -1 == SWIN ) printf("var %s is missing. file will be not created.\n", var_names[SWIN_INPUT]); return 0;
	}
	TS = get_minor_var_indexes(dataset, var_names[TS_INPUT]);
	if ( -2 == TS ) {
		/* memory error */
		return 0;
	}
	if ( -1 == TS ) {
		/* check for itp */
		TS = get_minor_var_indexes(dataset, var_names[itpTS_INPUT]);
		if ( -2 == TS ) {
			/* memory error */
			return 0;
		}
		if ( -1 == TS ) {
			printf("var %s is missing. file will be not created.\n", var_names[TS_INPUT]); return 0;
		}
	}
	TA = get_var_index(dataset, var_names[TA_INPUT]);
	if ( -1 == TA ) { printf("var %s is missing. file will be not created.\n", var_names[TA_INPUT]); return 0; }
	VPD = get_var_index(dataset, var_names[VPD_INPUT]);
	if ( -1 == VPD ) { printf("var %s is missing. file will be not created.\n", var_names[VPD_INPUT]); return 0; }

	/* create output filename */
	sprintf(buffer, "%s%s_qca_sr_%d.csv", output_path, dataset->details->site, dataset->details->year);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create '%s'\n", buffer);
		return 0;
	}

	/* write header */
	fputs("Month,Day,Year,Hour,Minutes,FC,SFC,Fv,RG_in,Ts,Isodate,Ta,VPD\n", f);

	/* write values */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* ...timestamp.... */
		fprintf(f, "%s,", timestamp_for_sr(i, dataset->details->year, dataset->details->timeres));
		/* ...values... */
		fprintf(f, "%g,", dataset->rows[i].value[FC]);
		fprintf(f, "%g,", dataset->rows[i].value[SC]);
		fprintf(f, "%g,", dataset->rows[i].value[USTAR]);
		fprintf(f, "%g,", dataset->rows[i].value[SWIN]);
		fprintf(f, "%g,", dataset->rows[i].value[TS]);
		fprintf(f, "%s,", timestamp_end_by_row_s(i, dataset->details->year, dataset->details->timeres));
		fprintf(f, "%g,", dataset->rows[i].value[TA]);
		fprintf(f, "%g\n", dataset->rows[i].value[VPD]);
	}
	fclose(f);

	/* ok */
	return 1;
}

/* */
static int set_sc_negl(DATASET *const dataset) {
	int i;
	int y;
	int z;
	int SC_NEGL;

	/* */
	SC_NEGL = get_var_index(dataset, var_names[SC_NEGL_INPUT]);
	if ( !SC_NEGL ) {
		return 0;
	}

	/* set 0 to all rows */
	for ( i = 0; i < dataset->rows_count; i++) {
		dataset->rows[i].value[SC_NEGL] = 0;
	}

	for ( i = 0; i < dataset->details->sc_negles_count; i++ ) {
		z = get_row_by_timestamp(&dataset->details->sc_negles[i].timestamp, dataset->details->timeres);
		for ( y = z; y < dataset->rows_count; y++ ) {
			dataset->rows[y].value[SC_NEGL] = dataset->details->sc_negles[i].flag;
		}
	}

	/* ok */
	return 1;
}

/* 
	we cannot have interpolated and not interpolated values of same var
	because we share flags ( e.g. SWIN_FROM_PPFD_FLAG_INPUT used by SW_IN and itpSW_IN )
*/

int check_itps(const DATASET *const dataset) {
	int i;
	int index1;
	int index2;
	int indexes[] = {	SWIN_INPUT
						, itpSWIN_INPUT
						, PPFD_INPUT
						, itpPPFD_INPUT
	};

	for ( i = 0; i < SIZEOF_ARRAY(indexes); i += 2 ) {
		const char *p = var_names[indexes[i]];
		const char *p2 = var_names[indexes[i+1]];
		index1 = get_var_index(dataset, p);
		index2 = get_var_index(dataset, p2);
		if ( (index1 != -1) && (index2 != -1) ) {
			printf("we cannot have %s and %s!\n", p, p2);
			return 1;
		}
	}
	return 0;
}

/* */
int main(int argc, char *argv[]) {
	int NEE;	/* for spikes */
	int H;		/* for spikes */
	int LE;		/* for spikes */
	int z;
	int error;
	int files_processed_count;
	int files_not_processed_count;
	int total_files_count;
	DATASET *dataset;
	const ARGUMENT args[] = {
		{ "input_path", get_input_path, NULL },
		{ "output_path", get_output_path, NULL },
		{ "marginals_window", set_int_value, &marginals_window },
		{ "sw_in_check", set_prec_value, &swin_check },
		{ "sw_in_pot_check", set_prec_value, &rpot_check },
		{ "sw_in_limit", set_prec_value, &swin_limit },
		{ "radiation_check", set_prec_value, &radiation_check },
		{ "radiation_check_stddev", set_prec_value, &radiation_check_stddev },
		{ "sw_in_vs_ppfd_in_threshold", set_prec_value, &rgvsppfd_threshold },
		{ "ustar_check", set_prec_value, &ustar_check },
		{ "ustar_check_stddev", set_prec_value, &ustar_check_stddev },
		{ "spikes_window", set_prec_value, &spikes_window },
		{ "qc2_filter", set_flag, &qc2_filter },
		{ "no_spike_filter", set_flag, &no_spike_filter },
		{ "doy", set_int_value, &doy },

		{ "h", show_help, NULL },
		{ "?", show_help, NULL },
		{ "help", show_help, NULL },

		{ "db", set_flag, &db_output },
		{ "graph", set_flag, &graph_output },
		{ "ustar", set_flag, &ustar_output },
		{ "nee", set_flag, &nee_output },
		{ "energy", set_flag, &energy_output },
		{ "meteo", set_flag, &meteo_output },
		{ "sr", set_flag, &sr_output },
		{ "solar", set_flag, &solar_output },
		{ "all", save_all, NULL },

		/* secret!
			onet = one timestamp!
			it writes TIMESTAMP_END only using TIMESTAMP label
		
		*/
		{ "onet", set_flag, &one_timestamp },
	};

	/* show banner */
	puts(banner);

	/* register atexit */
	if ( -1 == atexit(clean_up) ) {
		puts(err_unable_to_register_atexit);
		return 1;
	}

	/* parse arguments */
	if ( ! parse_arguments(argc, argv, args, SIZEOF_ARRAY(args)) ) {
		return 1;
	}

	/* check output */
	if (	! db_output &&
			! graph_output &&
			! ustar_output &&
			! nee_output &&
			! energy_output &&
			! meteo_output &&
			! sr_output &&
			! solar_output ) {
		puts(err_no_output_specified);
		return 1;
	}

	/* enable graph for solar output */
	if ( solar_output ) {
		graph_output = 1;
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
		int length;
		int need_folder_delimiter;

		/* compute string length */
		for ( length = 0; output_path[length]; length++ );

		/* check if last char is a FOLDER_DELIMITER */
		need_folder_delimiter = 0;
		if ( output_path[length-1] != FOLDER_DELIMITER ) {
			need_folder_delimiter = 1;
		}

		if ( need_folder_delimiter ) {
			char *p = malloc(length+1+1);
			if ( !p ) {
				puts(err_out_of_memory);
				return 1;
			}
			strncpy(p, output_path, length);
			p[length] = FOLDER_DELIMITER;
			p[length+1] = '\0';
			output_path = p;
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

	/* show paths */
	printf(msg_dataset_path, input_path);
	printf(msg_output_path, output_path);

	/* get files */
	files_found = get_files(program_path, input_path, &files_found_count, &error);
	if ( error ) {
		return 1;
	}

	/* reset */
	files_processed_count = 0;
	files_not_processed_count = 0;
	total_files_count = 0;

	/* loop for searching file */
	for ( z = 0; z < files_found_count; z++) {
		/* inc */
		++total_files_count;

		/* import dataset */
		printf("processing %s...", files_found[z].list[0].name);
		dataset = import_dataset(files_found[z].list[0].fullpath);
		if ( !dataset ) {
			puts("nothing found.");
			++files_not_processed_count;
			continue;
		}

		/* processing */
		printf(msg_processing, dataset->details->site, dataset->details->year);

		/* check for coesistence of itp vars and vars */
		if ( check_itps(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* compute missings */
		compute_missings(dataset);

		/* compute u* from tau if u* is missing */
		if ( ! ustar_from_tau(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* fill sc_negl column */
		if ( ! set_sc_negl(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* compute Nee as combination of FcStor and FcStorTT (also calculated here) */
		if ( ! set_nee(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* marginals (create flag indicating marginals) */
		if ( (MARGINALS_WINDOW == marginals_window) && (HOURLY_TIMERES == dataset->details->timeres) ) {
			marginals_window = MARGINALS_WINDOW_HOURLY;
		}
		if ( !set_marginals(dataset, marginals_window) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* compute RPOT */
		if ( !set_rpot(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* copy swin */
		if ( !preserve_swin(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* copy ppfd */
		if ( !preserve_ppfd(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* check negative values */
		check_for_neg(dataset, var_names[SWIN_INPUT]);
		check_for_neg(dataset, var_names[itpSWIN_INPUT]);
		check_for_neg(dataset, var_names[PPFD_INPUT]);
		check_for_neg(dataset, var_names[itpPPFD_INPUT]);

		/* check swin vs rpot and create a flag */
		set_swin_vs_rpot_flag(dataset, swin_check, rpot_check, swin_limit);

		/* check ppfd vs rpot and create a flag */
		set_ppfd_vs_rpot_flag(dataset, swin_check, rpot_check, swin_limit);

		/* check swin vs ppfd and create a flag */
		if ( ! set_swin_vs_ppfd_flag(dataset, radiation_check_stddev, rgvsppfd_threshold) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* ...as function name said... */
		set_invalid_by_flag(dataset, var_names[SWIN_INPUT], var_flag_names[SWIN_VS_PPFD_FLAG_INPUT]);
		set_invalid_by_flag(dataset, var_names[itpSWIN_INPUT], var_flag_names[SWIN_VS_PPFD_FLAG_INPUT]);
		set_invalid_by_flag(dataset, var_names[PPFD_INPUT], var_flag_names[SWIN_VS_PPFD_FLAG_INPUT]);
		set_invalid_by_flag(dataset, var_names[itpPPFD_INPUT], var_flag_names[SWIN_VS_PPFD_FLAG_INPUT]);

		/*  */
		if ( !set_swin_from_ppfd(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* u* flag */
		if ( !set_ustar_flag(dataset, ustar_check_stddev) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* set night and day */
		if ( !set_night_and_day(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* set values for spikes */
		set_spikes_value(dataset, &NEE, &H, &LE);

		/* conditional if on NEE, h and LE spikes detection */
		if ( (SPIKES_WINDOW == spikes_window) && (HOURLY_TIMERES == dataset->details->timeres) ) {
			spikes_window = SPIKES_WINDOW_HOURLY;
		}

		/* spikes detection for nee */
		if ( NEE != -1 ) {
			if ( !set_spikes(dataset, var_names[NEE_SPIKE_INPUT], spike_check_1, var_flag_names[SPIKE_NEE_FLAG_INPUT], spike_check_1_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			if ( !set_spikes(dataset, var_names[NEE_SPIKE_INPUT], spike_check_2, var_flag_names[SPIKE_NEE_FLAG_INPUT], spike_check_2_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			if ( !set_spikes(dataset, var_names[NEE_SPIKE_INPUT], spike_check_3, var_flag_names[SPIKE_NEE_FLAG_INPUT], spike_check_3_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			set_spikes_2(dataset, var_names[NEE_SPIKE_INPUT], var_flag_names[SPIKE_NEE_FLAG_INPUT], spike_threshold_nee);
		}

		/* spikes detection for h */
		if ( H != -1 ) {
			if ( !set_spikes(dataset, var_names[H_SPIKE_INPUT], spike_check_1, var_flag_names[SPIKE_H_FLAG_INPUT], spike_check_1_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			if ( !set_spikes(dataset, var_names[H_SPIKE_INPUT], spike_check_2, var_flag_names[SPIKE_H_FLAG_INPUT], spike_check_2_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			if ( !set_spikes(dataset, var_names[H_SPIKE_INPUT], spike_check_3, var_flag_names[SPIKE_H_FLAG_INPUT], spike_check_3_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			set_spikes_2(dataset, var_names[H_SPIKE_INPUT], var_flag_names[SPIKE_H_FLAG_INPUT], spike_threshold_h);
		}

		/* spikes detection for le */
		if ( LE != -1 ) {
			if ( !set_spikes(dataset, var_names[LE_SPIKE_INPUT], spike_check_1, var_flag_names[SPIKE_LE_FLAG_INPUT], spike_check_1_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			if ( !set_spikes(dataset, var_names[LE_SPIKE_INPUT], spike_check_2, var_flag_names[SPIKE_LE_FLAG_INPUT], spike_check_2_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			if ( !set_spikes(dataset, var_names[LE_SPIKE_INPUT], spike_check_3, var_flag_names[SPIKE_LE_FLAG_INPUT], spike_check_3_return, spikes_window) ) {
				free_dataset(dataset);
				++files_not_processed_count;
				continue;
			}

			set_spikes_2(dataset, var_names[LE_SPIKE_INPUT], var_flag_names[SPIKE_LE_FLAG_INPUT], spike_threshold_le);
		}

		/* set missing
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( IS_INVALID_VALUE(rows[i].value[FC]) ) ++rows[i].flag[flag_fc_miss];
			if ( IS_INVALID_VALUE(rows[i].value[NEE]) ) ++rows[i].flag[flag_nee_miss];
		}
		*/

		/* compute VPD */
		if ( !set_vpd(dataset) ) {
			free_dataset(dataset);
			++files_not_processed_count;
			continue;
		}

		/* save db file */
		if ( db_output ) {
			printf("	- saving db file...");
			if ( save_db_file(dataset) ) {
				puts("ok");
			}
		}

		/* save graph file and solar noon file */
		if ( graph_output ) {
			printf("	- saving graph file...");
			if ( save_graph_file(dataset) ) {
				puts("ok");
			}
		}

		/* set QC2 flag */
		set_qc2_flag(dataset, var_names[QCFC_INPUT], var_flag_names[QC2_NEE_FLAG_INPUT]);
		set_qc2_flag(dataset, var_names[QCH_INPUT], var_flag_names[QC2_H_FLAG_INPUT]);
		set_qc2_flag(dataset, var_names[QCLE_INPUT],var_flag_names[QC2_LE_FLAG_INPUT]);

		/* set INVALID_VALUE on USTAR flagged against WS */
		set_invalid_by_flag(dataset, var_names[USTAR_INPUT], var_flag_names[USTAR_FLAG_INPUT]);

		/* ... as name said... */
		if ( qc2_filter ) { set_invalid_by_flag(dataset, var_names[NEE_INPUT], var_flag_names[QC2_NEE_FLAG_INPUT]); }
		if ( !no_spike_filter ) { set_invalid_by_flag_value(dataset, var_names[NEE_INPUT], var_flag_names[SPIKE_NEE_FLAG_INPUT], SPIKE_CHECK_2_RETURN, GREATER_EQUAL); }
		if ( qc2_filter ) { set_invalid_by_flag(dataset, var_names[H_INPUT], var_flag_names[QC2_H_FLAG_INPUT]); }
		if ( !no_spike_filter ) { set_invalid_by_flag_value(dataset, var_names[H_INPUT], var_flag_names[SPIKE_H_FLAG_INPUT], SPIKE_CHECK_2_RETURN, GREATER_EQUAL); }
		if ( qc2_filter ) { set_invalid_by_flag(dataset, var_names[LE_INPUT], var_flag_names[QC2_LE_FLAG_INPUT]); }
		if ( !no_spike_filter ) { set_invalid_by_flag_value(dataset, var_names[LE_INPUT], var_flag_names[SPIKE_LE_FLAG_INPUT], SPIKE_CHECK_2_RETURN, GREATER_EQUAL); }

		/* save neeunc file */
		if ( nee_output ) {
			printf("	- saving nee file...");
			if ( save_nee_file(dataset) ) {
				puts("ok");
			}
		}

		/* save energy file */
		if ( energy_output ) {
			printf("	- saving energy file...");
			if ( save_energy_file(dataset) ) {
				puts("ok");
			}
		}

		/* save ut file */
		if ( ustar_output ) {
			printf("	- saving ustar file...");
			if ( save_ustar_file(dataset) ) {
				puts("ok");
			}
		}

		/* save sr file */
		if ( sr_output ) {
			printf("	- saving sr file...");
			if ( save_sr_file(dataset) ) {
				puts("ok");
			}
		}

		/* save solar file */
		if ( solar_output ) {
			printf("	- saving solar file...");
			if ( save_solar_file(dataset) ) {
				puts("ok");
			}
		}

		/* save meteora file */
		/* please note that vars will be inserted if missings ! */
		if ( meteo_output ) {
			printf("	- saving meteo file...");
			if ( save_meteo_file(dataset) ) {
				puts("ok");
			}
		}

		/* increment processed files count */
		++files_processed_count;

		/* */
		free_dataset(dataset);

		/* */
		puts("	- done\n");
	}

	/* summary */
	printf(msg_summary,
						total_files_count,
						total_files_count > 1 ? "s" : "",
						files_processed_count,
						files_not_processed_count
	);

	/* free memory at exit */
	return 0;
}
