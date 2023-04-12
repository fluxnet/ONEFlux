/*
	randunc.c

	this file is part of nee_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "dataset.h"

/* private function */
static PREC get_similiar_mean(const RAND_UNC_ROW *const rows, const int count) {
 	int i;
	PREC mean;

	/* check parameter */
	assert(rows);

	/* get mean */
	mean = 0.0;
	for ( i = 0; i < count; i++ ) {
		mean += rows[i].similiar;
	}
	mean /= count;

	/* check for NAN */
	if ( mean != mean ) {
		mean = INVALID_VALUE;
	}

	/* */
	return mean;
}

/* private function */
static PREC get_similiar_standard_deviation(const RAND_UNC_ROW *const rows, const int count) {
	int i;
	PREC mean;
	PREC sum;
	PREC sum2;

	/* check parameter */
	assert(rows);

	/* get mean */
	mean = get_similiar_mean(rows, count);
	if ( IS_INVALID_VALUE(mean) ) {
		return INVALID_VALUE;
	}

	/* compute standard deviation */
	sum = 0.0;
	sum2 = 0.0;
	for ( i = 0; i < count; i++ ) {
		sum = (rows[i].similiar - mean);
		sum *= sum;
		sum2 += sum;
	}
	sum2 /= count-1;
	sum2 = (PREC)SQRT(sum2);

	/* check for NAN */
	if ( sum2 != sum2 ) {
		sum2 = INVALID_VALUE;
	}

	/* */
	return sum2;
}

/* private function */
static PREC get_similiar_median(const RAND_UNC_ROW *const rows, const int count, int *const error) {
	int i;
	PREC *p_median;
	PREC result;

	/* check for null pointer */
	assert(rows);

	/* reset */
	*error = 0;

	if ( !count ) {
		return INVALID_VALUE;
	} else if ( 1 == count ) {
		return rows[0].similiar;
	}

	/* get valid values */
	p_median = malloc(count*sizeof*p_median);
	if ( !p_median ) {
		*error = 1;
		return INVALID_VALUE;
	}
	for ( i = 0; i < count; i++ ) {
		p_median[i] = rows[i].similiar;
	}

	/* sort values */
	qsort(p_median, count, sizeof *p_median, compare_prec);

	/* get median */
	if ( count & 1 ) {
		result = p_median[((count+1)/2)-1];
	} else {
		result = ((p_median[(count/2)-1] + p_median[count/2]) / 2);
	}

	/* free memory */
	free(p_median);

	/* check for NAN */
	if ( result != result ) {
		result = INVALID_VALUE;
	}

	/* */
	return result;
}

/* */
void random_method_1(RAND_UNC_ROW *const unc_rows, const int unc_rows_count, const int to_rand_index, const int hourly) {
	int i;
	int y;
	int j;
	int z;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int samples_count;
	PREC swin_tolerance;

	/* check parameter */
	assert(unc_rows);

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	samples_count = 0;
	swin_tolerance = 0.0;

	/* j is and index checker for hourly method */
	if ( hourly ) {
		j = 3;
	} else {
		j = 5;
	}
	
	/* */
	z = hourly ? 24 : 48;
	window = z * 7;
	for ( i = 0; i < unc_rows_count; i++ ) {
		/* method 1 */
		if ( 1 == unc_rows[i].method[to_rand_index] ) {
			/* reset */
			samples_count = 0;	
			
			/* get window start index */
			window_start = i - window - 1;
					
			/* get window end index */
			window_end = i + window + 1;
					
			/* compute tolerance for SWin */
			swin_tolerance = unc_rows[i].value[SWIN_UNC];
			if ( swin_tolerance < GF_DRIVER_1_TOLERANCE_MIN ) {
				swin_tolerance = GF_DRIVER_1_TOLERANCE_MIN;
			} else if ( swin_tolerance > GF_DRIVER_1_TOLERANCE_MAX ) {
				swin_tolerance = GF_DRIVER_1_TOLERANCE_MAX;
			}

			/* loop through window */
			for ( window_current = window_start; window_current < window_end; window_current += z ) {
				for ( y = 0; y < j; y++ ) {
					if ( ((window_current+y) < 0) || (window_current+y) >= unc_rows_count ) {
						continue;
					}

					if (	(0 == unc_rows[window_current+y].qc[to_rand_index]) &&
							IS_FLAG_SET(unc_rows[window_current+y].mask, GF_ALL_VALID) &&
							(FABS(unc_rows[window_current+y].value[TA_UNC]-unc_rows[i].value[TA_UNC]) < GF_DRIVER_2A_TOLERANCE_MIN) &&
							(FABS(unc_rows[window_current+y].value[SWIN_UNC]-unc_rows[i].value[SWIN_UNC]) < swin_tolerance ) &&
							(FABS(unc_rows[window_current+y].value[VPD_UNC]-unc_rows[i].value[VPD_UNC]) < GF_DRIVER_2B_TOLERANCE_MIN) ) {
						unc_rows[samples_count++].similiar = unc_rows[window_current+y].value[to_rand_index];
					}
				}
			}

			assert(samples_count<=j*(7*2+1));

			if ( samples_count > 5 ) {
				/* set standard deviation */
				unc_rows[i].rand[to_rand_index] = get_similiar_standard_deviation(unc_rows, samples_count);

				/* set samples */
				unc_rows[i].samples_count[to_rand_index] = samples_count;
			} else {
				unc_rows[i].method[to_rand_index] = 2;
			}
		}
	}
}

/* */
int random_method_2(RAND_UNC_ROW *const unc_rows, const int unc_rows_count, const int to_rand_index, const int hourly) {
	int i;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int samples_count;
	int error;
	PREC value;
	PREC range_min;
	PREC range_max;

	/* check parameter */
	assert(unc_rows);
	
	/* */
	window = (hourly ? 24 : 48) * 14;
	for ( i = 0; i < unc_rows_count; i++ ) {
		/* method 2 */
		if ( 2 == unc_rows[i].method[to_rand_index] ) {
			/* get 20% */
			value = FABS(unc_rows[i].value[to_rand_index]*0.2);
			if ( value < 2 ) {
				value = 2;
			}
			/* compute ranges */
			range_min = unc_rows[i].value[to_rand_index] - value;
			range_max = unc_rows[i].value[to_rand_index] + value;

			/* reset */
			samples_count = 0;	
			
			/* get window start index */
			window_start = i - window;
			if ( window_start < 0 ) {
				window_start = 0;
			}
					
			/* get window end index */
			window_end = i + window;
			if ( window_end > unc_rows_count ) {
				window_end = unc_rows_count;
			}
	
			/* loop through window */
			for ( window_current = window_start; window_current < window_end; window_current ++ ) {
				if ( 1 == unc_rows[window_current].method[to_rand_index] ) {
					if (	(unc_rows[window_current].value[to_rand_index] >= range_min) &&
							(unc_rows[window_current].value[to_rand_index] <= range_max) ) {
							unc_rows[samples_count++].similiar = unc_rows[window_current].rand[to_rand_index];
					}
				}
			}

			if ( samples_count ) {
				/* set median */
				unc_rows[i].rand[to_rand_index] = get_similiar_median(unc_rows, samples_count, &error);
				if ( error ) {
					printf("unable to get median for row %d\n", i);
					return 0;
				}

				/* set samples */
				unc_rows[i].samples_count[to_rand_index] = samples_count;
			} else {
				unc_rows[i].method[to_rand_index] = INVALID_VALUE;
				unc_rows[i].samples_count[to_rand_index] = INVALID_VALUE;
			}
		}
	}

	/* */
	return 1;
}
