/*
	spike.c

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "spike.h"
#include "dataset.h"

/* extern vars */
extern const char *const var_names[];

/* extern error strings */
extern const char err_out_of_memory[];
extern const char err_window_size_too_big[];

/* */
int set_night_and_day(DATASET *const dataset) {
	int i;
	int *night;
	int *day;
	int RPOT;
	int SWIN;
	int PPFD;
	int NIGHT;
	int DAY;

	/* check for null pointer */
	assert(dataset);

	/* */
	RPOT = get_var_index(dataset, var_names[RPOT_INPUT]);
	SWIN = get_var_index(dataset, var_names[SWIN_INPUT]);
	PPFD = get_var_index(dataset, var_names[PPFD_INPUT]);
	NIGHT = get_var_index(dataset, var_names[NIGHT_INPUT]);
	DAY = get_var_index(dataset, var_names[DAY_INPUT]);
	assert((-1 != RPOT) && (-1 != NIGHT) && (-1 != DAY));

	/* get itp */
	if ( -1 == SWIN ) {
		SWIN = get_var_index(dataset, var_names[itpSWIN_INPUT]);
	}

	if ( -1 == PPFD ) {
		PPFD = get_var_index(dataset, var_names[itpPPFD_INPUT]);
	}

	/* allocate memory */
	night = malloc(dataset->rows_count*sizeof*night);
	if ( !night ) {
		puts(err_out_of_memory);
		return 0;
	}

	day = malloc(dataset->rows_count*sizeof*day);
	if ( !day ) {
		puts(err_out_of_memory);
		free(night);
		return 0;
	}

	/* is night if RPOT <= 12 or SWIN < 12 or PPFD < 25 */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		night[i] = INVALID_VALUE;
		day[i] = INVALID_VALUE;

		if ( dataset->rows[i].value[RPOT] <= 12.0 ) {
			night[i] = 1;
		}

		if ( (-1 != SWIN) && !IS_INVALID_VALUE(dataset->rows[i].value[SWIN]) ) {
			if ( dataset->rows[i].value[SWIN] < 12.0 ) {
				night[i] = 1;
			} else {
				night[i] = INVALID_VALUE;
			}
		}

		if ( (-1 != PPFD) && !IS_INVALID_VALUE(dataset->rows[i].value[PPFD]) ) {
			if ( dataset->rows[i].value[PPFD] < 25.0 ) {
				night[i] = 1;
			} else {
				night[i] = INVALID_VALUE;
			}
		}

		if ( IS_INVALID_VALUE(night[i]) ) {
			day[i] = 1;
		}
	}

	/* night and day are extended of +/- 1 row to allow the spike check of data at margin between daytime and nighttime */
	dataset->rows[0].value[NIGHT] = INVALID_VALUE;
	if ( (!IS_INVALID_VALUE(night[0])) || (!IS_INVALID_VALUE(night[1])) ) {
		dataset->rows[0].value[NIGHT] = 1;
	}

	dataset->rows[0].value[DAY] = INVALID_VALUE;
	if ( (!IS_INVALID_VALUE(day[0])) || (!IS_INVALID_VALUE(day[1])) ) {
		dataset->rows[0].value[DAY] = 1;
	}

	for ( i = 1; i < dataset->rows_count - 1; i++ ) {
		if ( (IS_INVALID_VALUE(night[i])) && (IS_INVALID_VALUE(night[i-1])) && (IS_INVALID_VALUE(night[i+1])) ) {
			dataset->rows[i].value[NIGHT] = INVALID_VALUE;
		} else	{
			dataset->rows[i].value[NIGHT] = 1;
		}

		if ( (IS_INVALID_VALUE(day[i])) && (IS_INVALID_VALUE(day[i-1])) && (IS_INVALID_VALUE(day[i+1])) ) {
			dataset->rows[i].value[DAY] = INVALID_VALUE;
		} else {
			dataset->rows[i].value[DAY] = 1;
		}
	}

	dataset->rows[dataset->rows_count-1].value[NIGHT] = INVALID_VALUE;
	if ( (!IS_INVALID_VALUE(dataset->rows[dataset->rows_count-1].value[NIGHT])) || (!IS_INVALID_VALUE(dataset->rows[dataset->rows_count-2].value[NIGHT])) ) {
		dataset->rows[dataset->rows_count-1].value[NIGHT] = 1;
	}

	dataset->rows[dataset->rows_count-1].value[DAY] = INVALID_VALUE;
	if ( (!IS_INVALID_VALUE(dataset->rows[dataset->rows_count-1].value[DAY])) || (!IS_INVALID_VALUE(dataset->rows[dataset->rows_count-2].value[DAY])) ) {
		dataset->rows[dataset->rows_count-1].value[DAY] = 1;
	}

	/* free memory */
	free(day);
	free(night);

	/* */
	return 1;
}

/* 

spike detection according with papale et al 2006 biogeosciences
for data before or after a gap where "three points differences" could not be calculated,
flag set as one if difference i-(i+1) or i-(i-1) is above a threshold set as 6 for nee and 100 for le and h

*/
int set_spikes(DATASET *const dataset, const char *const var_name, const PREC zfc, const char *const flag_name, const int result, const int window) {
	int i;
	int y;
	int z;
	int period;
	int time_window;
	int loop;
	int error;
	int VAR;
	int FLAG;
	int TEMP;
	PREC median;
	PREC median_abs;
	PREC min;
	PREC max;
	PREC *p_differences;
	PREC *p_median_abs;

	/* check for null pointer */
	assert(dataset);

	/* */
	VAR = get_var_index(dataset, var_name);
	FLAG = get_flag_index(dataset, flag_name);
	TEMP = get_var_index(dataset, var_names[TEMP_INPUT]);
	period = get_var_index(dataset, var_names[NIGHT_INPUT]);
	assert((TEMP != -1) && (FLAG != -1) && (period != -1));

	/* */
	if ( -1 == VAR ) {
		return 1;
	}

	/* get loop count */
	loop = dataset->rows_count / window;
	if ( loop <= 0 ) {
		puts(err_window_size_too_big);
		return 0;
	}

	/* get last time-window size so we must not to reallocate memory on each loop */
	time_window = dataset->rows_count - ((loop-1)*window);

	/* allocate memory */
	p_differences = malloc(time_window*sizeof*p_differences);
	if ( !p_differences ) {
		puts(err_out_of_memory);
		return 0;
	}

	p_median_abs = malloc(time_window*sizeof*p_median_abs);
	if ( !p_median_abs ) {
		puts(err_out_of_memory);
		free(p_differences);
		return 0;
	}

	z = 0;
	while ( z <= 1 ) {
		/* fill TEMP column */
		for ( i = 0; i < dataset->rows_count; i++ ) {
			if ( IS_INVALID_VALUE(dataset->rows[i].value[period]) || IS_INVALID_VALUE(dataset->rows[i].value[VAR]) ) {
				dataset->rows[i].value[TEMP] = INVALID_VALUE;
			} else {
				dataset->rows[i].value[TEMP] = dataset->rows[i].value[VAR];
			}
		}

		/* time_window loop */
		time_window = window;
		for ( i = 0; i < loop; i++ ) {
			/* fix for last loop */
			if ( i == loop-1) {
				time_window = dataset->rows_count - ((loop-1)*window);
			}

			/* compute differences */
			p_differences[0] = INVALID_VALUE;
			for ( y = 1; y < time_window - 1; y++ ) {

				if (
						IS_INVALID_VALUE(dataset->rows[y+(i*window)-1].value[TEMP]) ||
						IS_INVALID_VALUE(dataset->rows[y+(i*window)].value[TEMP]) ||
						IS_INVALID_VALUE(dataset->rows[y+(i*window)+1].value[TEMP])
				) {
						p_differences[y] = INVALID_VALUE;
				} else {
					p_differences[y] = dataset->rows[y+(i*window)].value[TEMP] - dataset->rows[y+(i*window)-1].value[TEMP];
					p_differences[y] -= dataset->rows[y+(i*window)+1].value[TEMP] - dataset->rows[y+(i*window)].value[TEMP];
				}
			}
			p_differences[time_window-1] = INVALID_VALUE;

			/* get median of differences of differences */
			median = get_median(p_differences, time_window, &error);
			if ( error ) {
				puts(err_out_of_memory);
				free(p_median_abs);
				free(p_differences);
				return 0;
			}

			/* check for median */
			if ( IS_INVALID_VALUE(median) ) {
				continue;
			}

			for ( y = 0; y < time_window; y++ ) {
				if ( IS_INVALID_VALUE(p_differences[y]) ) {
					p_median_abs[y] = INVALID_VALUE;
				} else {
					p_median_abs[y] = FABS(p_differences[y] - median);
				}
			}

			/* compute median of abs */
			median_abs = get_median(p_median_abs, time_window, &error);
			if ( error ) {
				puts(err_out_of_memory);
				free(p_median_abs);
				free(p_differences);
				return 0;
			}

			/* check for median */
			if ( IS_INVALID_VALUE(median_abs) ) {
				continue;
			}

			/* compute min and max */
			max = median + (zfc*median_abs / 0.6745);
			min = median - (zfc*median_abs / 0.6745);

			for ( y = 0; y < time_window; y++ ) {
				if ( !IS_INVALID_VALUE(p_differences[y]) ) {
					if ( p_differences[y] > max ) {
						dataset->flags[y+(i*window)].value[FLAG] = result;
					}

					if ( p_differences[y] < min ) {
						dataset->flags[y+(i*window)].value[FLAG] = result;
					}
				}
			}
		}

		++period;
		++z;
	}

	/* free memory */
	free(p_median_abs);
	free(p_differences);

	/* */
	return 1;
}

/* 

spike detection for data before or after a gap

*/
void set_spikes_2(DATASET *const dataset, const char *const var_name, const char *const flag_name, const PREC threshold) {
	int i;
	int VAR;
	int FLAG;

	/* check for null pointer */
	assert(dataset);

	/* */
	VAR = get_var_index(dataset, var_name);
	FLAG = get_flag_index(dataset, flag_name);
	assert(FLAG != -1);

	/* */
	if ( -1 == VAR ) {
		return;
	}

	/* */
	for ( i = 2; i < dataset->rows_count; i++ ) {
		if (
				(IS_INVALID_VALUE(dataset->rows[i].value[VAR])) &&
				(!IS_INVALID_VALUE(dataset->rows[i-1].value[VAR])) &&
				(!IS_INVALID_VALUE(dataset->rows[i-2].value[VAR]))
		) {
			if ( FABS(dataset->rows[i-1].value[VAR]-dataset->rows[i-2].value[VAR]) > threshold ) {
				dataset->flags[i-1].value[FLAG] = 1;
			}
		}
	}

	for ( i = 0; i < dataset->rows_count-2; i++ ) {
		if (	
				(IS_INVALID_VALUE(dataset->rows[i].value[VAR])) &&
				(!IS_INVALID_VALUE(dataset->rows[i+1].value[VAR])) &&
				(!IS_INVALID_VALUE(dataset->rows[i+2].value[VAR]))
		) {
			if ( FABS(dataset->rows[i+1].value[VAR]-dataset->rows[i+2].value[VAR]) > threshold ) {
				dataset->flags[i+1].value[FLAG] = 1;
			}
		}
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( IS_INVALID_VALUE(dataset->rows[i].value[VAR]) ) {
			dataset->flags[i].value[FLAG] = INVALID_VALUE;
		}
	}
}
