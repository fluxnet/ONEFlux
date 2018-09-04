/*
	ustar.c

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "ustar.h"
#include "dataset.h"

/* */
extern int ustar_check;
extern const char *const var_names[];
extern const char *const var_flag_names[];

/* extern errors strings */
extern const char err_out_of_memory[];

/* 

create a flag comparing u* and ws if both have at least ustar_check_stddev (default:9000) valid values.
flag = 1 for values outside +/- 4*stddev of the residuals in the linear interpolation between u* and ws

*/
int set_ustar_flag(DATASET *const dataset, const PREC ustar_check_stddev) {
	int i;
	int USTAR;
	int WS;
	int USTAR_FLAG;
	int TEMP;


	/* check for null pointer */
	assert(dataset);

	/* */
	USTAR = get_var_index(dataset, var_names[USTAR_INPUT]);
	WS = get_var_index(dataset, var_names[WS_INPUT]);
	USTAR_FLAG = get_flag_index(dataset, var_flag_names[USTAR_FLAG_INPUT]);
	TEMP = get_var_index(dataset, var_names[TEMP_INPUT]);
	assert((USTAR_FLAG != -1)&&(TEMP != -1));
	if ( (-1 == USTAR) || (-1 == WS) ) {
		return 1;
	}

	/* get ustar */
	for ( i = 0 ; i < dataset->rows_count; i++ ) {
		dataset->rows[i].value[TEMP] = dataset->rows[i].value[USTAR];
	}

	if ( (dataset->missings[WS] <= ustar_check) && (dataset->missings[USTAR] <= ustar_check) ) {
		int spike_count;
		SPIKE *spikes;
		SPIKE *spikes_no_leak;

		/* get spikes */
		spikes = NULL;
		spike_count = 0;
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( (!IS_INVALID_VALUE(dataset->rows[i].value[WS])) && (!IS_INVALID_VALUE(dataset->rows[i].value[USTAR])) ) {
				spikes_no_leak = realloc(spikes, ++spike_count*sizeof*spikes_no_leak);
				if ( !spikes_no_leak ) {
					puts(err_out_of_memory);
					free(spikes);
					return 0;
				}

				spikes = spikes_no_leak;
				spikes[spike_count - 1].value1 = dataset->rows[i].value[WS];
				spikes[spike_count - 1].value2 = dataset->rows[i].value[USTAR];
				spikes[spike_count - 1].index = i;
			}
		}

		/* process spikes */
		if ( spike_count > 0 ) {
			PREC sumx;
			PREC sumy;
			PREC sumx2;
			PREC sumxy;
			PREC divisor;
			
			/* reset */
			sumx = 0.0;
			sumy = 0.0;
			sumx2 = 0.0;
			sumxy = 0.0;

			/* linear regression between u* and ws */
			for ( i = 0; i < spike_count; i++ ) {
				sumx += spikes[i].value1;
				sumy += spikes[i].value2;
				sumx2 += (spikes[i].value1*spikes[i].value1);
				sumxy += (spikes[i].value1*spikes[i].value2);
			}

			divisor = (sumx2 - ((sumx * sumx) / spike_count));
			if ( !ARE_FLOATS_EQUAL(divisor, 0.0) ) {
				PREC stddev;
				PREC slope;
				PREC intercept;
				PREC *residuals;

				slope = (sumxy - ((sumx * sumy) / spike_count)) / divisor;
				intercept = (sumy - (slope * sumx)) / spike_count;

				residuals = malloc(spike_count*sizeof *residuals);
				if ( !residuals ) {
					puts(err_out_of_memory);
					free(spikes);
					return 0;
				}

				for ( i = 0; i < spike_count; i++ ) {
					residuals[i] = (spikes[i].value2 - ((slope * spikes[i].value1) + intercept));
				}

				stddev = get_standard_deviation(residuals, spike_count);

				for ( i = 0; i < spike_count; i++ ) {
					if ( (residuals[i] >= (ustar_check_stddev * stddev)) || (residuals[i] <= (-ustar_check_stddev * stddev)) ) {
						dataset->flags[spikes[i].index].value[USTAR_FLAG] = 1;
						/* since u* can be very noisy the check is repeated removing the selected residuals */
						dataset->rows[spikes[i].index].value[TEMP] = INVALID_VALUE;
					}
				}

				/* free memory */
				free(residuals);
				free(spikes);

				/* recheck on cleaned u* */
				spikes = NULL;
				spike_count = 0;
				for ( i = 0; i < dataset->rows_count; i++ ) {
					if ( (!IS_INVALID_VALUE(dataset->rows[i].value[WS])) && (!IS_INVALID_VALUE(dataset->rows[i].value[TEMP])) ) {
						spikes_no_leak = realloc(spikes, ++spike_count*sizeof*spikes_no_leak);
						if ( !spikes_no_leak ) {
							puts(err_out_of_memory);
							free(spikes);
							return 0;
						}

						spikes = spikes_no_leak;
						spikes[spike_count - 1].value1 = dataset->rows[i].value[WS];
						spikes[spike_count - 1].value2 = dataset->rows[i].value[TEMP];
						spikes[spike_count - 1].index = i;
					}
				}

				/* process spikes */
				if ( spike_count > 0 ) {
					/* reset */
					sumx = 0.0;
					sumy = 0.0;
					sumx2 = 0.0;
					sumxy = 0.0;

					for ( i = 0; i < spike_count; i++ ) {
						sumx += spikes[i].value1;
						sumy += spikes[i].value2;
						sumx2 += (spikes[i].value1*spikes[i].value1);
						sumxy += (spikes[i].value1*spikes[i].value2);
					}

					divisor = (sumx2 - ((sumx * sumx) / spike_count));
					if ( !ARE_FLOATS_EQUAL(divisor, 0.0) ) {
						slope = (sumxy - ((sumx * sumy) / spike_count)) / divisor;
						intercept = (sumy - (slope * sumx)) / spike_count;

						residuals = malloc(spike_count*sizeof*residuals);
						if ( !residuals ) {
							puts(err_out_of_memory);
							free(spikes);
							return 0;
						}
						
						for ( i = 0; i < spike_count; i++ ) {
							residuals[i] = (spikes[i].value2 - ((slope * spikes[i].value1) + intercept));
						}

						stddev = get_standard_deviation(residuals, spike_count);

						for ( i = 0; i < spike_count; i++ ) {
							if ( (residuals[i] >= (ustar_check_stddev * stddev)) || (residuals[i] <= (-ustar_check_stddev * stddev)) ) {
								dataset->flags[spikes[i].index].value[USTAR_FLAG] = 1;
							}
						}
						/* free memory */
						free(residuals);
					}
				}
			}

			/* free memory */
			free(spikes);
		}
	}

	/* */
	return 1;
}
