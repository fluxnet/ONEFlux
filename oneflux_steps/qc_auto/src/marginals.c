/*
	marginals.c

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>

	description: create flag indicating marginal data defined as singole or double isolated points
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "marginal.h"
#include "dataset.h"

/* extern vars */
extern const char *const var_names[];
extern const char *const var_flag_names[];

/* prototypes */
PREC *copy_value(const DATASET *dataset, const int column);

/* */
static int set_marginals_on_var(DATASET *const dataset, const int marginals_window, const int var_index, const int flag_index) {
	int i;
	int start;
	int invalid_count;
	int TEMP;
	
	/* check for null pointer */
	assert(dataset);

	/* check index */
	if ( -1 == var_index ) {
		return 1;
	}

	/* get TEMP index */
	TEMP = get_var_index(dataset, var_names[TEMP_INPUT]);
	assert(-1 != TEMP);

	/* copy value */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		dataset->rows[i].value[TEMP] = dataset->rows[i].value[var_index];
	}

	/* marginals_window or more marginals */
	invalid_count = 0;
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( IS_INVALID_VALUE(dataset->rows[i].value[TEMP]) ) {
			++invalid_count;
		} else {
			if ( invalid_count >= marginals_window ) {
				start = (i-invalid_count)-1;
				if ( start >= 0 ) {
					dataset->flags[start].value[flag_index] = 1;
				}
			}
			invalid_count = 0;
		}
	}
	/* todo: ask dario */
	/* if ( invalid_count >= marginals_window ) { */
	if ( (invalid_count >= marginals_window) && (invalid_count != dataset->rows_count) ) {
		start = dataset->rows_count - invalid_count -1;
		if ( start >= 0 ) {
			dataset->flags[start].value[flag_index] = 1;
		}
	}

	/* todo: ask dario
	dataset->rows[0].value[TEMP] = 0.0;
	dataset->rows[1].value[TEMP] = 0.0;
	dataset->rows[dataset->rows_count-2].value[TEMP] = 0.0;
	dataset->rows[dataset->rows_count-1].value[TEMP] = 0.0;
	*/

	/* 1 isolated marginals */
	for ( i = 1; i < dataset->rows_count-1; i++ ) {
		if (
				(IS_INVALID_VALUE(dataset->rows[i-1].value[TEMP])) &&
				(!IS_INVALID_VALUE(dataset->rows[i].value[TEMP])) &&
				(IS_INVALID_VALUE(dataset->rows[i+1].value[TEMP]))
		) {
			dataset->flags[i].value[flag_index] = 1;
		}
	}

	/* 2 isolated marginals */
	for ( i = 1; i < dataset->rows_count-2; i++ ) {
		if (
				(IS_INVALID_VALUE(dataset->rows[i-1].value[TEMP])) &&
				(!IS_INVALID_VALUE(dataset->rows[i].value[TEMP])) &&
				(!IS_INVALID_VALUE(dataset->rows[i+1].value[TEMP])) &&
				(IS_INVALID_VALUE(dataset->rows[i+2].value[TEMP]))
		) {
			dataset->flags[i].value[flag_index] = 1;
			dataset->flags[i+1].value[flag_index] = 1;
		}
	}

	/* at end


	if (
			(IS_INVALID_VALUE(dataset->rows[dataset->rows_count-2].value[TEMP])) && 
			(!IS_INVALID_VALUE(dataset->rows[dataset->rows_count-1].value[TEMP]))
	) {
		dataset->flags[dataset->rows_count-1].value[flag_index] = 1;
	}

	if (
			(IS_INVALID_VALUE(dataset->rows[dataset->rows_count-3].value[TEMP])) && 
			(!IS_INVALID_VALUE(dataset->rows[dataset->rows_count-2].value[TEMP])) && 
			(!IS_INVALID_VALUE(dataset->rows[dataset->rows_count-1].value[TEMP]))
	) {
		dataset->flags[dataset->rows_count-2].value[flag_index] = 1;
		dataset->flags[dataset->rows_count-1].value[flag_index] = 1;
	}

	*/

	/* */
	return 1;
}

/* */
int set_marginals(DATASET *const dataset, const int marginals_window) {
	int i;
	int NEE;
	int LE;
	int H;
	int NEE_FLAG;
	int LE_FLAG;
	int H_FLAG;

	/* get columns indexes */
	NEE = get_var_index(dataset, var_names[NEE_INPUT]);
	LE = get_var_index(dataset, var_names[LE_INPUT]);
	H = get_var_index(dataset, var_names[H_INPUT]);
	NEE_FLAG = get_flag_index(dataset, var_flag_names[MARGINAL_NEE_FLAG_INPUT]);
	LE_FLAG = get_flag_index(dataset, var_flag_names[MARGINAL_LE_FLAG_INPUT]);
	H_FLAG = get_flag_index(dataset, var_flag_names[MARGINAL_H_FLAG_INPUT]);
	assert((NEE_FLAG != -1) && (LE_FLAG != -1) && (H_FLAG != -1));

	/* compute marginals */
	i = set_marginals_on_var(dataset, marginals_window, NEE, NEE_FLAG);
	i += set_marginals_on_var(dataset, marginals_window, LE, LE_FLAG);
	i += set_marginals_on_var(dataset, marginals_window, H, H_FLAG);

	/* ok ? */
	return (3==i);
}
