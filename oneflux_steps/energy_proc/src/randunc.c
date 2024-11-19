/*
	randunc.c

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "dataset.h"

/* */
void random_method_1(DATASET *const dataset, const int index) {
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
	assert(dataset);

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	samples_count = 0;
	swin_tolerance = 0.0;

	/* j is and index checker for hourly method */
	if ( dataset->hourly ) {
		j = 3;
	} else {
		j = 5;
	}
	
	/* */
	z = dataset->hourly ? 24 : 48;
	window = z * 7;
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* method 1 */
		if ( 1 == dataset->rows[i].rand_method[index] ) {
			/* reset */
			samples_count = 0;	
			
			/* get window start index */
			window_start = i - window - 1;
					
			/* get window end index */
			window_end = i + window + 1;
					
			/* compute tolerance for SWin */
			swin_tolerance = dataset->rows[i].value[SWIN];
			if ( swin_tolerance < GF_DRIVER_1_TOLERANCE_MIN ) {
				swin_tolerance = GF_DRIVER_1_TOLERANCE_MIN;
			} else if ( swin_tolerance > GF_DRIVER_1_TOLERANCE_MAX ) {
				swin_tolerance = GF_DRIVER_1_TOLERANCE_MAX;
			}

			/* loop through window */
			for ( window_current = window_start; window_current < window_end; window_current += z ) {
				for ( y = 0; y < j; y++ ) {
					if ( ((window_current+y) < 0) || (window_current+y) >= dataset->rows_count ) {
						continue;
					}

					if (	(!dataset->gf_rows[index][window_current+y].quality) &&
							IS_FLAG_SET(dataset->gf_rows[index][window_current+y].mask, GF_ALL_VALID) &&
							(FABS(dataset->rows[window_current+y].value[TA]-dataset->rows[i].value[TA]) < GF_DRIVER_2A_TOLERANCE_MIN) &&
							(FABS(dataset->rows[window_current+y].value[SWIN]-dataset->rows[i].value[SWIN]) < swin_tolerance ) &&
							(FABS(dataset->rows[window_current+y].value[VPD]-dataset->rows[i].value[VPD]) < GF_DRIVER_2B_TOLERANCE_MIN) ) {
						dataset->gf_rows[index][samples_count++].similiar = dataset->rows[window_current+y].value[index];
					}
				}
			}

			assert(samples_count<=j*(7*2+1));

			if ( samples_count > 5 ) {
				/* set standard deviation */
				dataset->rows[i].rand[index] = gf_get_similiar_standard_deviation(dataset->gf_rows[index], samples_count);
				/* set samples */
				dataset->rows[i].rand_samples_count[index] = samples_count;
			} else {
				dataset->rows[i].rand_method[index] = 2;
			}
		}
	}
}

/* */
int random_method_2(DATASET *const dataset, const int index) {
	int i;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int samples_count;
	int error;
	PREC range_min;
	PREC range_max;
	PREC value;

	/* check parameter */
	assert(dataset);

	/* */
	window = (dataset->hourly ? 24 : 48) * 14;
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* method 2 - define similiar fluxes when they're between +/- 20% or at least +/- 10 W m2 */
		if ( 2 == dataset->rows[i].rand_method[index] ) {
			value = FABS(dataset->rows[i].value[index]*0.2);
			if ( value < 10 ) {
				value = 10;
			}
			/* compute ranges */
			range_min = dataset->rows[i].value[index] - value;
			range_max = dataset->rows[i].value[index] + value;

			/* reset */
			samples_count = 0;	
			
			/* get window start index */
			window_start = i - window;
			if ( window_start < 0 ) {
				window_start = 0;
			}
					
			/* get window end index */
			window_end = i + window;
			if ( window_end > dataset->rows_count ) {
				window_end = dataset->rows_count;
			}
	
			/* loop through window */
			for ( window_current = window_start; window_current < window_end; window_current ++ ) {
				if ( 1 == dataset->rows[window_current].rand_method[index] ) {
					if (	(dataset->rows[window_current].value[index] >= range_min) &&
							(dataset->rows[window_current].value[index] <= range_max) ) {
								dataset->gf_rows[index][samples_count++].similiar = dataset->rows[window_current].rand[index];
					}
				}
			}

			if ( samples_count ) {
				/* set median */
				dataset->rows[i].rand[index] = gf_get_similiar_median(dataset->gf_rows[index], samples_count, &error);
				if ( error ) {
					printf("unable to get median for for row %d\n", i);
					return 0;
				}

				/* set samples */
				dataset->rows[i].rand_samples_count[index] = samples_count;
			} else {
				dataset->rows[i].rand_method[index] = INVALID_VALUE;
				dataset->rows[i].rand_samples_count[index] = INVALID_VALUE;
			}
		}
	}

	/* */
	return 1;
}
