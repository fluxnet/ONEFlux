/*
	ustar.c

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include "ustar.h"

/* extern variables */
extern int percentile_value;
extern int percentile_check;
extern int window_size_forward_mode;
extern int window_size_forward_mode_2;
extern int window_size_forward_mode_3;
extern int window_size_back_mode;
extern int window_size_back_mode_2;
extern int window_size_back_mode_3;
extern int ta_classes_count;
extern int ustar_classes_count;
extern int seasons_group_count;
extern int *samples_per_season;
extern int no_forward_mode;
extern int no_forward_mode_2;
extern int no_forward_mode_3;
extern int no_back_mode;
extern int no_back_mode_2;
extern int no_back_mode_3;
extern PREC threshold_check;

/* error strings */
static const char too_ta_classes[] = "too ta classes (%d)! We have only %d samples for %d season!";
static const char too_ustar_classes[] = "too ustar classes (%d)! We have only %d samples for %d season!";

/* extern strings */
extern const char err_out_of_memory[];
extern const char err_too_less_values[];

/* todo : implement a better comparison for equality */
static int compare_ta(const void * a, const void * b) {
	if ( ((ROW *)a)->value[TA] < ((ROW *)b)->value[TA]) {
		return -1;
	} else if ( ((ROW *)a)->value[TA] > ((ROW *)b)->value[TA] ) {
		return 1;
	} else	{
		return 0;
	}
}

/* todo : implement a better comparison for equality */
static int compare_ustar(const void * a, const void * b) {
	if ( ((ROW *)a)->value[USTAR] < ((ROW *)b)->value[USTAR]) {
		return -1;
	} else if ( ((ROW *)a)->value[USTAR] > ((ROW *)b)->value[USTAR] ) {
		return 1;
	} else	{
		return 0;
	}
}

/* meanws : a mean with start position */
/* todo : check it */
static PREC meanws(const PREC *const array, const int array_count, const int index, const int element_count) {
	int i = 0;
	int count = 0;
	PREC mean = 0.0;

	if ( index > array_count ) {
		return 0.0;
	}

	for ( i = index; i < index+element_count; i++ ) {
		if ( i >= array_count ) {
			break;
		}

		if ( IS_INVALID_VALUE(array[i]) ) {
			return INVALID_VALUE;
		}

		mean += array[i];

		++count;
	}
	mean /= count;

	/* check for NAN */
	if ( mean != mean ) {
		return INVALID_VALUE;
	}

	/* */
	return mean;
}

/* compute Pearson's correlation */
static PREC correlation(const ROW *const rows, const int start, const int end) {
	int i;
    PREC xmean;
    PREC ymean;
   	PREC s;
    PREC xv;
    PREC yv;
	PREC t1;
	PREC t2;
	PREC corr;

	xmean = 0.0;
	ymean = 0.0;
    for ( i = start; i <= end; i++ ) {
		if ( IS_INVALID_VALUE(rows[i].value[TA]) ) {
			return INVALID_VALUE;
		}

		if ( IS_INVALID_VALUE(rows[i].value[USTAR]) ) {
			return INVALID_VALUE;
		}

		xmean += rows[i].value[TA];
		ymean += rows[i].value[USTAR];
    }
	xmean /= ((end-start)+1);
	ymean /= ((end-start)+1);

	s = 0.0;
    xv = 0.0;
    yv = 0.0;
	for ( i = start; i <= end; i++ ) {
        t1 = rows[i].value[TA] - xmean;
        t2 = rows[i].value[USTAR] - ymean;

        xv = xv + t1 * t1;
        yv = yv + t2 * t2;

        s = s + t1 * t2;
    }

	/* */
	corr = (s/(SQRT(xv)*SQRT(yv)));

	/* check for NAN */
	if ( corr != corr ) {
		corr = INVALID_VALUE;
	}

	/* */
	return corr;
}

/* todo : add check for null arguments */
/* disable on February 27, 2013 - replace 10 with bigger values is an error! */
PREC median_ustar_threshold_old(const PREC *const values, const int element, const int season, int *const p_error) {
	int i;
	PREC *median;
	PREC result;
	PREC bigger;

	/* reset */
	*p_error = 0;

	/* get bigger values */
	bigger = INVALID_VALUE;
	for ( i = 0; i < element; i++ ) {
		if (
				!IS_INVALID_VALUE(values[season*element+i]) &&
				!ARE_FLOATS_EQUAL(values[season*element+i], USTAR_THRESHOLD_NOT_FOUND) &&
				(values[season*element+i] > bigger) ) {
			bigger = values[season*element+i];
		}
	}
	if ( IS_INVALID_VALUE(bigger) ) {
		return bigger;
	}

	/* alloc memory */
	median = malloc(element*sizeof*median);
	if ( !median ) {
		*p_error = 1;
		return 0.0;
	}

	/* build-up array */
	for ( i = 0; i < element; i++ ) {
		if ( !IS_INVALID_VALUE(values[season*element+i]) && !ARE_FLOATS_EQUAL(values[season*element+i], USTAR_THRESHOLD_NOT_FOUND) ) {
			median[i] = values[season*element+i];
		} else {
			median[i] = bigger;
		}
	}

	/* get median */
	qsort(median, element, sizeof(PREC), compare_prec);
	if ( element & 1 ) {
		result = median[((element+1)/2)-1];
	} else {
		result = (median[(element/2)-1] + median[element/2]) / (PREC)2.0;
	}

	/* free memory */
	free(median);

	/* ok */
	return result;
}

/* todo : add check for null arguments */
PREC median_ustar_threshold(const PREC *const values, const int element, const int season, int *const p_error)
{
	int i = 0;
	int count = 0;
	PREC *no_leak = NULL;
	PREC *median = NULL;
	PREC result = 0.0;

	/* reset */
	*p_error = 0;

	for ( i = 0; i < element; i++ ) {
		if ( !IS_INVALID_VALUE(values[season*element+i]) && !ARE_FLOATS_EQUAL(values[season*element+i], USTAR_THRESHOLD_NOT_FOUND) ) {
			no_leak = realloc(median, (++count)*sizeof(PREC));
			if ( !no_leak ) {
				free(median);
				*p_error = 1;
				return 0.0;
			}

			median = no_leak;
			median[count-1] = values[season*element+i];
		}
	}

	if ( 0 == count ) {
		return INVALID_VALUE;
	} else if ( 1 == count ) {
		result = median[0];
		free(median);
		return result;
	} 
	/*else if ( count < 4 ) {
		free(median);
		return INVALID_VALUE;
	}
	*/

	qsort(median, count, sizeof(PREC), compare_prec);

	if ( count & 1 ) {
		result = median[((count+1)/2)-1];
	} else {
		result = (median[(count/2)-1] + median[count/2]) / (PREC)2.0;
	}

	free(median);

	return result;
}

/* */
static PREC forward_mode(	const PREC ustar_mean[],
							const PREC fx_mean[],
							const int ustar_classes_count,
							const int window_size,
							const int percentile_check,
							const PREC percentile,
							const PREC threshold_check,
							const int n,
							unsigned char *const percentiled) {
	int i;
	int y;
	int z;
	int threshold_found;
	char is_invalid;
	PREC *means;
	PREC threshold;

	/* reset */
	*percentiled = 0;

	/* checks */
	if ( (n < 1) || (ustar_classes_count - n <= 0) ) {
		return INVALID_VALUE;
	}

	/* alloc memory */
	means = malloc(n*sizeof*means);
	if ( !means ) {
		puts(err_out_of_memory);
		return INVALID_VALUE;
	}

	/* */
	threshold_found = 0;
	for ( i = 0; i <= ustar_classes_count - n; i++ ) {
		/* percentile check */
		if ( percentile_check && (ustar_mean[i+(n-1)] >= percentile) ) {
			threshold = ustar_mean[i+(n-1)];
			threshold_found = 1;
			if ( percentiled ) {
				*percentiled = 1;
			}
			break;
		}

		is_invalid = 0;
		for ( y = 0; y < n; y++ ) {
			means[y] = meanws(fx_mean, ustar_classes_count, i+1+y, window_size);
			if ( IS_INVALID_VALUE(means[y]) ) {
				is_invalid = 1;
				break;
			}
		}
		if ( is_invalid ) {
			/* skip to next ustar class */
			continue;
		}

		z = 0;
		for ( y = 0; y < n; y++ ) {
			if ( fx_mean[i+y] >= (means[y] * threshold_check) ) {
				++z;
			}
		}

		if ( z == n ) {
			threshold = ustar_mean[i];
			threshold_found = 1;
		}

		if ( threshold_found ) {
			break;
		}
	}

	if ( !threshold_found ) {
		threshold = USTAR_THRESHOLD_NOT_FOUND;
	}

	/* free memory */
	free(means);
	
	/* ok ? */
	return threshold;
}

/* */
static PREC back_mode(	const PREC ustar_mean[],
						const PREC fx_mean[],
						const int ustar_classes_count,
						const int max_window_size,
						const int percentile_check,
						const PREC percentile,
						const PREC threshold_check,
						const int n,
						unsigned char *const percentiled) {
	int i;
	int j;
	int z;
	int threshold_found;
	PREC mean;
	PREC threshold;
	int start;
	int size;

	/* reset */
	*percentiled = 0;

	/* checks */
	if ( (n < 1) || (ustar_classes_count - n <= 0) ) {
		return INVALID_VALUE;
	}

	/* compute start mode by percentile */
	start = (ustar_classes_count * percentile_value) / 100;

	/* */
	threshold_found = 0;
	for ( i = start; i > n; i-- ) {
		size = ustar_classes_count - i;
		if ( !size ) {
			continue;
		} else if ( size > max_window_size ) {
			size = max_window_size;
		}
		mean = meanws(fx_mean, ustar_classes_count, i, size);
		if ( IS_INVALID_VALUE(mean) ) {
			/* skip to next ustar class */
			continue;
		}
		z = 0;
		for ( j = 0; j < n; j++ ) {
			if ( fx_mean[i-(1+j)] <= (mean * threshold_check) ) {
				++z;
			}
		}

		if ( z == n ) {
			threshold = ustar_mean[i-1];
			threshold_found = 1;
		}

		if ( threshold_found ) {
			break;
		}
	}

	if ( !threshold_found ) {
		if ( percentile_check ) {
			threshold = ustar_mean[start];
			*percentiled = 1;
		} else {
			threshold = USTAR_THRESHOLD_NOT_FOUND;
		}
		
	}
	
	/* ok ? */
	return threshold;
}

/* */
int ustar_threshold(ROW *const rows, const int rows_count, const int days,
					unsigned char *const threshold_forward_mode_percentiled,
					unsigned char *const threshold_forward_mode_2_percentiled,
					unsigned char *const threshold_forward_mode_3_percentiled,
					unsigned char *const threshold_back_mode_percentiled,
					unsigned char *const threshold_back_mode_2_percentiled,
					unsigned char *const threshold_back_mode_3_percentiled,
					PREC *const threshold_forward_mode_container,
					PREC *const threshold_forward_mode_2_container,
					PREC *const threshold_forward_mode_3_container,
					PREC *const threshold_back_mode_container,
					PREC *const threshold_back_mode_2_container,
					PREC *const threshold_back_mode_3_container,
					PREC *const ustar_mean,
					PREC *const fx_mean,
					WINDOW *const ta_window,
					WINDOW *const ustar_window )
{
	int i;
	int y;
	int s;
	int seasons_n;
	int season_start_index;
	int ta_samples_count;
	int ta_class_start;
	int ta_class_end;
	int ustar_samples_count;
	int ustar_class_start;
	int ustar_class_end;
	int ustar_total_count;
	int ta_class;
	PREC value;
	PREC corr;
	PREC percentile_index;
	PREC percentile;
	PREC threshold;
	unsigned char percentiled;

	/* check for null pointer */
	if (	!rows ||
			!ustar_mean ||
			!fx_mean ||
			!ta_window ||
			!ustar_window ) {
		return 0;
	}

	if ( !threshold_forward_mode_container && !no_forward_mode ) {
		return 0;
	}

	if ( !threshold_forward_mode_2_container && !no_forward_mode_2 ) {
		return 0;
	}

	if ( !threshold_forward_mode_3_container && !no_forward_mode_3 ) {
		return 0;
	}

	if ( !threshold_back_mode_container && !no_back_mode ) {
		return 0;
	}

	if ( !threshold_back_mode_2_container && !no_back_mode_2 ) {
		return 0;
	}

	if ( !threshold_back_mode_3_container && !no_back_mode_3 ) {
		return 0;
	}

	/* check method */
	if ( rows_count < ta_classes_count*ustar_classes_count ) {
		puts(err_too_less_values);
		return 0;
	} else if ( rows_count+days >= MIN_VALUE_PERIOD ) {
		seasons_n = seasons_group_count;	/* first method */
	} else if ( rows_count > MIN_VALUE_SEASON ) {
		seasons_n = 1;						/* second method, one big season */

		/* accomodate to one big season */
		for ( i = 1; i < seasons_group_count; i++ ) {
			samples_per_season[0] += samples_per_season[i];
		}
		seasons_group_count = 1;
	} else {
		puts(err_too_less_values);
		return 0;
	}

	/* fix added on January 25, 2012 (DKsor, 1997) */
	if ( seasons_n > 1 ) {
		i = 0;
		for ( s = 0; s < seasons_n; s++ ) {
			if ( samples_per_season[s] < TA_CLASS_MIN_SAMPLE*ta_classes_count ) {
				++i;
			}
		}
		if ( i == seasons_n ) {
			seasons_n = 1;					/* second method, one big season */

			/* accomodate to one big season */
			for ( i = 1; i < seasons_group_count; i++ ) {
				samples_per_season[0] += samples_per_season[i];
			}
			seasons_group_count = 1;
		}
	}

	/* reset containers */
	for ( i = 0; i < seasons_group_count; i++ ) {
		for ( y = 0; y < ta_classes_count; y++ ) {
			threshold_forward_mode_container[i*ta_classes_count+y] = INVALID_VALUE;
			threshold_forward_mode_2_container[i*ta_classes_count+y] = INVALID_VALUE;
			threshold_forward_mode_3_container[i*ta_classes_count+y] = INVALID_VALUE;
			threshold_back_mode_container[i*ta_classes_count+y] = INVALID_VALUE;
			threshold_back_mode_2_container[i*ta_classes_count+y] = INVALID_VALUE;
			threshold_back_mode_3_container[i*ta_classes_count+y] = INVALID_VALUE;
			if ( threshold_forward_mode_percentiled ) {
				threshold_forward_mode_percentiled[i*ta_classes_count+y] = 0;
			}
			if ( threshold_forward_mode_2_percentiled ) {
				threshold_forward_mode_2_percentiled[i*ta_classes_count+y] = 0;
			}
			if ( threshold_forward_mode_3_percentiled ) {
				threshold_forward_mode_3_percentiled[i*ta_classes_count+y] = 0;
			}
			if ( threshold_back_mode_percentiled ) {
				threshold_back_mode_percentiled[i*ta_classes_count+y] = 0;
			}
			if ( threshold_back_mode_2_percentiled ) {
				threshold_back_mode_2_percentiled[i*ta_classes_count+y] = 0;
			}
			if ( threshold_back_mode_3_percentiled ) {
				threshold_back_mode_3_percentiled[i*ta_classes_count+y] = 0;
			}
		}
	}

	/* loop for each season */
	for ( s = 0; s < seasons_n; s++ ) {
		/* if number of values are less than TA_CLASS_MIN_SAMPLE*ta_classes_count skip to next season */
		if ( samples_per_season[s] < TA_CLASS_MIN_SAMPLE*ta_classes_count ) {
			/* skip to next season */
			continue;
		}

		/* compute index: this variable keep track of where each season start on dataset */
		season_start_index = 0;
		for ( i = 0; i < s; i++ ) {
			season_start_index += samples_per_season[i];
		}

		/* sort season by ta */
		qsort(&rows[season_start_index], samples_per_season[s], sizeof(ROW), compare_ta);

		/* get samples count for each ta class */
		ta_samples_count = samples_per_season[s] / ta_classes_count;
		if ( ta_samples_count <= 0 ) {
			printf(too_ta_classes, ta_classes_count, samples_per_season[s], s+1);
			return 0;
		}

		/* reset */
		ta_class_start = 0;
		ta_class_end = season_start_index;

		/* reset ta window, mandatory */
		for ( i = 0; i < ta_classes_count; i++ ) {
			ta_window[i].start = -1;
			ta_window[i].end = -1;
		}

		/* adjust ta classes samples size */
		for ( i = 0; i < ta_classes_count - 1; i++ ) {
			/* set start & end indexes */
			ta_class_start = ta_class_end;
			ta_class_end = season_start_index + (ta_samples_count*(i+1)-1);

			/* check bounds */
			if ( ta_class_start >= season_start_index + samples_per_season[s] ) {
				break;
			}

			if ( ta_class_end >= season_start_index + samples_per_season[s] ) {
				ta_class_end = season_start_index + samples_per_season[s] - 1;
			}

			/* get value for comparison */
			value = rows[ta_class_end].value[TA];

			/* compare value with following values till they are not equal */
			while ( ++ta_class_end < season_start_index + samples_per_season[s] ) {
				/* todo : implement better equality comparison */
				if ( !ARE_FLOATS_EQUAL(value, rows[ta_class_end].value[TA]) ) {
					break;
				}
			}

			/* set start & end indexes */
			ta_window[i].start = ta_class_start;
			ta_window[i].end = ta_class_end - 1;
		}

		/* check array bound */
		if ( ta_class_end < season_start_index + samples_per_season[s] ) {
			/* adjust last ta class */
			ta_window[i].start = ta_class_end;
			ta_window[i].end = season_start_index + samples_per_season[s] - 1;
		}

		/* loop for each ta class */
		for ( ta_class = 0; ta_class < ta_classes_count; ta_class++ ) {
			/* check if ta class has valid start index */
			if ( -1 == ta_window[ta_class].start ) {
				/* skip to next ta class */
				continue;
			}

			/* check if ta class has more samples than TA_CLASS_MIN_SAMPLE */
			if ( ta_window[ta_class].end - ta_window[ta_class].start + 1 < TA_CLASS_MIN_SAMPLE ) {
				/* skip to next class */
				continue;
			}

			/* compute correlation */
			corr = correlation(rows, ta_window[ta_class].start, ta_window[ta_class].end);

			/* check if correlation is > CORRELATION_CHECK */
			if ( FABS(corr) > CORRELATION_CHECK ) {
				/*skip to next ta class */
				continue;
			}

			/* compute samples for ustar class */
			ustar_total_count = (ta_window[ta_class].end - ta_window[ta_class].start) + 1;

			/* sort ustar */
			qsort(&rows[ta_window[ta_class].start], ustar_total_count, sizeof(ROW), compare_ustar);

			/* get percentile check */
			percentile_index = (PREC)ustar_total_count; /* promoting int to PREC */
			percentile_index /= 100;
			percentile_index *= percentile_value;
			--percentile_index; /* fix for zero based index */
			percentile = rows[(int)(percentile_index+ta_window[ta_class].start)].value[USTAR];

			/* get samples for each ustar class */
			ustar_samples_count = ustar_total_count / ustar_classes_count;
			if ( ustar_samples_count <= 0 ) {
				printf(too_ustar_classes, ustar_classes_count, samples_per_season[s], s+1);
				return 0;
			}

			/* reset */
			ustar_class_start = 0;
			ustar_class_end = 0;

			/* reset ustar window, mandatory */
			for ( i = 0; i < ustar_classes_count; i++ ) {
				ustar_window[i].start = -1;
				ustar_window[i].end = -1;
			}

			/* adjust ustar classes samples size */
			for ( i = 0; i < ustar_classes_count - 1; i++ ) {
				/* set start & end indexes */
				ustar_class_start = ustar_class_end;
				ustar_class_end = ustar_samples_count * (i + 1) - 1;

				/* check array bounds */
				if ( ustar_class_start >= ustar_total_count ) {
					break;
				}

				if ( ustar_class_end >= ustar_total_count ) {
					ustar_class_end = ustar_total_count - 1;
				}

				/* get value for comparison */
				value = rows[ustar_class_end + ta_window[ta_class].start].value[USTAR];

				/* compare value with following values till they are not equal */
				while ( ++ustar_class_end < ustar_total_count ) {
					/* todo : implement better equality comparison */
					if ( !ARE_FLOATS_EQUAL(value, rows[ustar_class_end + ta_window[ta_class].start].value[USTAR]) ) {
						if ( ustar_class_start == ustar_class_end ) {
							value = rows[ustar_class_end + ta_window[ta_class].start].value[USTAR];
							continue;
						}
						break;
					}
				}

				/* set start & end indexes */
				ustar_window[i].start = ustar_class_start + ta_window[ta_class].start;
				ustar_window[i].end = ustar_class_end - 1 + ta_window[ta_class].start;
			}

			/* check array bounds */
			if ( ustar_class_end < ustar_total_count ) {
				/* adjust last ustar class */
				ustar_window[i].start = ustar_class_end + ta_window[ta_class].start;
				ustar_window[i].end = ustar_total_count - 1 + ta_window[ta_class].start;
			}

			/* compute means */
			i = 0;
			while ( i++ < ustar_classes_count ) {
				/* reset */
				ustar_mean[i-1] = 0.0;
				fx_mean[i-1] = 0.0;

				/* check if ustar has a valid start point */
				if ( -1 == ustar_window[i-1].start ) {
					/* skip to next ustar class */
					continue;
				}

				for ( y = ustar_window[i-1].start; y <= ustar_window[i-1].end; y++ ) {
					ustar_mean[i-1] += rows[y].value[USTAR];
					fx_mean[i-1] += rows[y].value[NEE];
				}

				ustar_mean[i-1] /= ((ustar_window[i-1].end - ustar_window[i-1].start)+1);
				fx_mean[i-1] /= ((ustar_window[i-1].end - ustar_window[i-1].start)+1);
			}

			/* check if first ustar mean > FIRST_USTAR_MEAN_CHECK */
			if ( ustar_mean[0] > FIRST_USTAR_MEAN_CHECK ) {
				/* skip to next ta class */
				continue;
			}

			/* compute threshold forward mode */
			if ( !no_forward_mode ) {
				threshold = forward_mode(	ustar_mean,
											fx_mean,
											ustar_classes_count,
											window_size_forward_mode,
											percentile_check,
											percentile,
											threshold_check,
											1,
											&percentiled);

				/* put threshold into container */
				threshold_forward_mode_container[s*ta_classes_count+ta_class] = threshold;

				/* percentiled ? */
				if ( threshold_forward_mode_percentiled ) {
					threshold_forward_mode_percentiled[s*ta_classes_count+ta_class] = percentiled;
				}

				/* if one big season copy values to other seasons */
				if ( 1 == seasons_n ) {
					for ( i = 0; i < seasons_group_count; i++ ) {
						threshold_forward_mode_container[i*ta_classes_count+ta_class] = threshold;
					}
				}
			}

			/* compute threshold forward mode 2 */
			if ( !no_forward_mode_2 ) {
				threshold = forward_mode(	ustar_mean,
											fx_mean,
											ustar_classes_count,
											window_size_forward_mode_2,
											percentile_check,
											percentile,
											threshold_check,
											2,
											&percentiled);

				/* put threshold into container */
				threshold_forward_mode_2_container[s*ta_classes_count+ta_class] = threshold;

				/* percentiled ? */
				if ( threshold_forward_mode_2_percentiled ) {
					threshold_forward_mode_2_percentiled[s*ta_classes_count+ta_class] = percentiled;
				}

				/* if one big season copy values to other seasons */
				if ( 1 == seasons_n ) {
					for ( i = 0; i < seasons_group_count; i++ ) {
						threshold_forward_mode_2_container[i*ta_classes_count+ta_class] = threshold;
					}
				}
			}

			/* compute threshold forward mode 3 */
			if ( !no_forward_mode_3 ) {
				threshold = forward_mode(	ustar_mean,
											fx_mean,
											ustar_classes_count,
											window_size_forward_mode_3,
											percentile_check,
											percentile,
											threshold_check,
											3,
											&percentiled);

				/* put threshold into container */
				threshold_forward_mode_3_container[s*ta_classes_count+ta_class] = threshold;

				/* percentiled ? */
				if ( threshold_forward_mode_3_percentiled ) {
					threshold_forward_mode_3_percentiled[s*ta_classes_count+ta_class] = percentiled;
				}

				/* if one big season copy values to other seasons */
				if ( 1 == seasons_n ) {
					for ( i = 0; i < seasons_group_count; i++ ) {
						threshold_forward_mode_3_container[i*ta_classes_count+ta_class] = threshold;
					}
				}
			}

			/* compute threshold back mode */
			if ( !no_back_mode ) {
				threshold = back_mode(	ustar_mean,
										fx_mean,
										ustar_classes_count,
										MAX_WINDOW_SIZE_FOR_BACK_MODE,
										percentile_check,
										percentile,
										threshold_check,
										1,
										&percentiled);

				/* put threshold into container */
				threshold_back_mode_container[s*ta_classes_count+ta_class] = threshold;

				/* percentiled ? */
				if ( threshold_back_mode_percentiled ) {
					threshold_back_mode_percentiled[s*ta_classes_count+ta_class] = percentiled;
				}

				/* if one big season copy values to other seasons */
				if ( 1 == seasons_n ) {
					for ( i = 0; i < seasons_group_count; i++ ) {
						threshold_back_mode_container[i*ta_classes_count+ta_class] = threshold;
					}
				}
			}

			/* compute threshold back mode 2 */
			if ( !no_back_mode_2 ) {
				threshold = back_mode(	ustar_mean,
										fx_mean,
										ustar_classes_count,
										MAX_WINDOW_SIZE_FOR_BACK_MODE_2,
										percentile_check,
										percentile,
										threshold_check,
										2,
										&percentiled);

				/* put threshold into container */
				threshold_back_mode_2_container[s*ta_classes_count+ta_class] = threshold;

				/* percentiled ? */
				if ( threshold_back_mode_2_percentiled ) {
					threshold_back_mode_2_percentiled[s*ta_classes_count+ta_class] = percentiled;
				}

				/* if one big season copy values to other seasons */
				if ( 1 == seasons_n ) {
					for ( i = 0; i < seasons_group_count; i++ ) {
						threshold_back_mode_2_container[i*ta_classes_count+ta_class] = threshold;
					}
				}
			}

			if ( !no_back_mode_3 ) {
				threshold = back_mode(	ustar_mean,
										fx_mean,
										ustar_classes_count,
										MAX_WINDOW_SIZE_FOR_BACK_MODE_3,
										percentile_check,
										percentile,
										threshold_check,
										3,
										&percentiled);

				/* put threshold into container */
				threshold_back_mode_3_container[s*ta_classes_count+ta_class] = threshold;

				/* percentiled ? */
				if ( threshold_back_mode_3_percentiled ) {
					threshold_back_mode_3_percentiled[s*ta_classes_count+ta_class] = percentiled;
				}

				/* if one big season copy values to other seasons */
				if ( 1 == seasons_n ) {
					for ( i = 0; i < seasons_group_count; i++ ) {
						threshold_back_mode_3_container[i*ta_classes_count+ta_class] = threshold;
					}
				}
			}
		}
	}

	return 1;
}
