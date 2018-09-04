/*
	rpot.c

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "rpot.h"
#include "dataset.h"

extern int radiation_check;

/* extern vars */
extern const char *const var_names[];
extern const char *const var_flag_names[];

/* extern errors strings */
extern const char err_out_of_memory[];

/* */
int set_rpot(DATASET *const dataset) {
	int i;
	double *temp;
	int RPOT;

	assert(dataset);

	/* get RPOT column */
	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	if ( -1 == RPOT ) {
		puts("unable to compute rpot!");
		return 0;
	}

	/* get rpot */
	temp = get_rpot(dataset->details);
	if ( !temp ) {
		return 0;
	}

	/* copy rpots */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		dataset->rows[i].value[RPOT] = temp[i];
	}

	/* free memory */
	free(temp);

	/* ok */
	return 1;
}

/* 

check SWin against rpot and create a flag equal to 1 :

- when rpot = 0.0 and swin > 50.0
- when rpot > 200.0 and swin-rpot > 50 and swin is > 15% more than rpot

*/
void set_swin_vs_rpot_flag(DATASET *const dataset, const PREC swin_check, const PREC rpot_check, const PREC swin_limit ){
	int i;
	int SWIN;
	int RPOT;
	int SWIN_VS_RPOT;
	PREC value;

	/* check for null pointer */
	assert(dataset);

	/* */
	SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
	if ( -1 == SWIN ) {
		/* get itp */
		SWIN =  get_var_index(dataset, var_names[itpSWIN_INPUT]);
	}
	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	SWIN_VS_RPOT = get_flag_index(dataset, var_flag_names[SWIN_VS_RPOT_FLAG_INPUT]);
	assert((RPOT != -1)&&(SWIN_VS_RPOT != -1));

	if ( -1 == SWIN ) {
		return;
	}

	/* */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[SWIN]) ) {
			value = dataset->rows[i].value[SWIN] - dataset->rows[i].value[RPOT];
			if ( value > 0.0 ) {
				if ( ARE_FLOATS_EQUAL(dataset->rows[i].value[RPOT], 0.0) ) {
					if ( dataset->rows[i].value[SWIN] > swin_check ) {
						dataset->flags[i].value[SWIN_VS_RPOT] = 1;
					}
				} else if ( (value > swin_check) && (dataset->rows[i].value[RPOT] > rpot_check) ) {
					if ( (value / dataset->rows[i].value[RPOT]) > swin_limit ) {
						dataset->flags[i].value[SWIN_VS_RPOT] = 1;
					}
				}
			}
		} else {
			dataset->flags[i].value[SWIN_VS_RPOT] = INVALID_VALUE;
		}
	}
}

/* 

check SWin (from PPFD) against rpot and create a flag equal to 1 :

- when rpot = 0.0 and swin > 50.0
- when rpot > 200.0 and swin-rpot > 50 and swin is > 15% more than rpot

*/
void set_ppfd_vs_rpot_flag(DATASET *const dataset, const PREC swin_check, const PREC rpot_check, const PREC swin_limit ){
	int i;
	int PPFD;
	int RPOT;
	int PPFD_VS_RPOT;
	PREC value;

	/* check for null pointer */
	assert(dataset);

	/* */
	PPFD = get_var_index(dataset, var_names[PPFD_INPUT]);
	if ( -1 == PPFD ) {
		/* get itp */
		PPFD = get_var_index(dataset, var_names[itpPPFD_INPUT]);
	}
	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	PPFD_VS_RPOT = get_flag_index(dataset, var_flag_names[PPFD_VS_RPOT_FLAG_INPUT]);
	assert((RPOT != -1)&&(PPFD_VS_RPOT != -1));

	if ( -1 == PPFD ) {
		return;
	}

	/* */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[PPFD]) ) {
			value = dataset->rows[i].value[PPFD]*0.5 - dataset->rows[i].value[RPOT];
			if ( value > 0.0 ) {
				if ( ARE_FLOATS_EQUAL(dataset->rows[i].value[RPOT], 0.0) ) {
					if ( dataset->rows[i].value[PPFD]*0.5 > swin_check ) {
						dataset->flags[i].value[PPFD_VS_RPOT] = 1;
					}
				} else if ( (value > swin_check) && (dataset->rows[i].value[RPOT] > rpot_check) ) {
					if ( (value / dataset->rows[i].value[RPOT]) > swin_limit ) {
						dataset->flags[i].value[PPFD_VS_RPOT] = 1;
					}
				}
			}
		} else {
			dataset->flags[i].value[PPFD_VS_RPOT] = INVALID_VALUE;
		}
	}
}

/* 

create a flag comparing SWin and PPFd if both have at least radiation_check_stddev (default:11000) valid values.
flag = 1 for values outside +/- 5*stddev of the residuals in the linear interpolation between Swin and PPFD

*/
int set_swin_vs_ppfd_flag(DATASET *const dataset, const PREC radiation_check_stddev, const PREC swin_vs_ppfd_threshold) {
	int i;
	int SWIN;
	int PPFD;
	int SWIN_VS_PPFD;
	
	/* check for null pointer */
	assert(dataset);

	/* */
	SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
	PPFD = get_var_index(dataset, var_names[PPFD_INPUT]);
	SWIN_VS_PPFD = get_flag_index(dataset, var_flag_names[SWIN_VS_PPFD_FLAG_INPUT]);
	assert(SWIN_VS_PPFD != -1);

	/* */
	if ((-1 == SWIN) || (-1 == PPFD)) {
		/* set flag to INVALID_VALUE */
		for ( i = 0; i < dataset->rows_count; i++ ) {
			dataset->flags[i].value[SWIN_VS_PPFD] = INVALID_VALUE;
		}

		/* check for hourly timeres */
		if ( dataset->details->timeres == HOURLY_TIMERES ) {
			/* check for itpSwin */
			if ( -1 == SWIN ) {
				SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
				if ( -1 == SWIN ) {
					return -1;
				}
			}

			/* check for itpPpfd */
			if ( -1 == PPFD ) {
				PPFD = get_var_index(dataset, var_names[itpPPFD_INPUT]);
				if ( -1 == PPFD ) {
					return -1;
				}
			}
		} else {
			/* */
			return 1;
		}
	}

	/* apply only if valid values count is > radiation_check */
	if ( (dataset->missings[SWIN] <= radiation_check) && (dataset->missings[PPFD] <= radiation_check) ) {
		int i;
		int spike_count;
		SPIKE *spikes;
		SPIKE *spikes_no_leak;

		/* get spikes */
		spikes = NULL;
		spike_count = 0;
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( (!IS_INVALID_VALUE(dataset->rows[i].value[SWIN])) && (!IS_INVALID_VALUE(dataset->rows[i].value[PPFD])) ) {
				spikes_no_leak = realloc(spikes, (++spike_count)*sizeof*spikes_no_leak);
				if ( !spikes_no_leak ) {
					puts(err_out_of_memory);
					free(spikes);
					return 0;
				}

				spikes = spikes_no_leak;
				spikes[spike_count - 1].value1 = dataset->rows[i].value[SWIN];
				spikes[spike_count - 1].value2 = dataset->rows[i].value[PPFD];
				spikes[spike_count - 1].index = i;
			} else {
				dataset->flags[i].value[SWIN_VS_PPFD] = INVALID_VALUE;
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

			/* linear regression between SWin and PPFD */
			for ( i = 0; i < spike_count; i++ ) {
				sumx += spikes[i].value1;
				sumy += spikes[i].value2;
				sumx2 += (spikes[i].value1 * spikes[i].value1);
				sumxy += (spikes[i].value1 * spikes[i].value2);
			}

			divisor = (sumx2 - ((sumx * sumx) / spike_count));

			if ( ! ARE_FLOATS_EQUAL(divisor, 0.0) ) {
				PREC stddev;
				PREC slope;
				PREC intercept;
				PREC *residuals;
				PREC denominator;

				slope = (sumxy - ((sumx * sumy) / spike_count)) / divisor;
				intercept = (sumy - (slope * sumx)) / spike_count;

				residuals = malloc(spike_count*sizeof*residuals);
				if ( ! residuals ) {
					puts(err_out_of_memory);
					free(spikes);
					return 0;
				}

				for ( i = 0; i < spike_count; i++ ) {
					residuals[i] = (spikes[i].value2 - ((slope * spikes[i].value1) + intercept));
				}

				stddev = get_standard_deviation(residuals, spike_count);

				/* compute denominator for distance point line */
				denominator = sqrt(1 + slope * slope);

				/*
					dario said about threshold :
					
					"if the standard deviation is above a minimum threshold the two variables are compared,
					otherwise not because would be flagged as spikes points that differ just for decimals or centesimals"
				*/
				if ( stddev > swin_vs_ppfd_threshold ) {
					for ( i = 0; i < spike_count; i++ ) {
						if ( (residuals[i] >= (radiation_check_stddev * stddev)) || (residuals[i] <= (-radiation_check_stddev * stddev)) ) {
							/* distance point line */
							if ( (fabs(residuals[i]) / denominator) > 50 ) {
								dataset->flags[spikes[i].index].value[SWIN_VS_PPFD] = 1;
							}
						}
					}
				}
				free(residuals);
			}
			free(spikes);
		}
	}

	return 1;
}
