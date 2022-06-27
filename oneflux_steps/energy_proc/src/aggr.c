/*
	aggr.c

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "aggr.h"
#include "ecbcf.h"

/* */
extern int no_rand_unc;

/* */
const int days_per_month[MONTHS] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

/* */
int aggr_by_days(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp) {
	int i;
	int y;
	int j;
	int rows_per_day;
	int h_count;
	int le_count;
	int g_count;
	int day;
	int error;
	int *all_valid_rows_index;
	char mask;
	PREC ECBcf;
	PREC median;
	PREC perc25;
	PREC perc75;
	PREC diff;

	/* */
	rows_per_day = dataset->hourly ? 24 : 48;

	/* */
	all_valid_rows_index = malloc(rows_per_day*sizeof*all_valid_rows_index);
	if ( !all_valid_rows_index ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop on each row */
	day = 0;
	for ( i = 0; i < dataset->rows_count; i += rows_per_day ) {
		/* get H and LE mean and index of "all" valid */
		h_count = 0;
		le_count = 0;
		g_count = 0;

		dataset->rows_aggr[day].h_mean = 0.0;
		dataset->rows_aggr[day].le_mean = 0.0;
		dataset->rows_aggr[day].n = 0;
		dataset->rows_aggr[day].rand[LE_INDEX] = 0.0;

		dataset->rows_aggr[day].rand[H_INDEX] = 0.0;
		dataset->rows_aggr[day].rand_samples_count[LE_INDEX] = 0;
		dataset->rows_aggr[day].rand_samples_count[H_INDEX] = 0;

		dataset->rows_aggr[day].value[G_FILLED] = 0.0;

		for ( j = 0; j < rows_per_day; j++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows[i+j].value[H]) && (dataset->rows[i+j].value[H] == dataset->rows[i+j].value[H]) ) {
				dataset->rows_aggr[day].h_mean += dataset->rows[i+j].value[H];
				++h_count;
			}
			if ( !IS_INVALID_VALUE(dataset->rows[i+j].value[LE]) && (dataset->rows[i+j].value[LE] == dataset->rows[i+j].value[LE]) ) {
				dataset->rows_aggr[day].le_mean += dataset->rows[i+j].value[LE];
				++le_count;
			}

			/* update mask */
			mask = 0;
			if ( !IS_INVALID_VALUE(dataset->rows[i+j].value[H]) ) {
				mask |= H_VALID;
			}

			if ( !IS_INVALID_VALUE(dataset->rows[i+j].value[LE]) ) {
				mask |= LE_VALID;
			}

			if ( !IS_INVALID_VALUE(dataset->rows[i+j].value[G]) ) {
				mask |= G_VALID;
			}

			if ( !IS_INVALID_VALUE(dataset->rows[i+j].value[NETRAD]) ) {
				mask |= NETRAD_VALID;
			}

			/* get all valid index */
			if ( IS_FLAG_SET(mask, ECBCF_ALL_VALID) && (dataset->gf_rows[LE_INDEX][i+j].quality <= 1) && (dataset->gf_rows[H_INDEX][i+j].quality <= 1)) {
				all_valid_rows_index[(int)dataset->rows_aggr[day].n++] = i+j;
			}

			/* rand unc */
			if ( !no_rand_unc ) {
				if ( !IS_INVALID_VALUE(dataset->rows[i+j].rand[LE_INDEX]) ) {
					dataset->rows_aggr[day].rand[LE_INDEX] += (dataset->rows[i+j].rand[LE_INDEX] * dataset->rows[i+j].rand[LE_INDEX]);
					++dataset->rows_aggr[day].rand_samples_count[LE_INDEX];
				}
				if ( !IS_INVALID_VALUE(dataset->rows[i+j].rand[H_INDEX]) ) {
					dataset->rows_aggr[day].rand[H_INDEX] += (dataset->rows[i+j].rand[H_INDEX] * dataset->rows[i+j].rand[H_INDEX]);
					++dataset->rows_aggr[day].rand_samples_count[H_INDEX];
				}
			}

			/* aggr G */
			if ( ! IS_INVALID_VALUE(dataset->gf_rows[G_INDEX][i+j].filled) ) {
				dataset->rows_aggr[day].value[G_FILLED] += dataset->gf_rows[G_INDEX][i+j].filled;
				++g_count;
			}
		}
		if ( h_count ) {
			dataset->rows_aggr[day].h_mean /= h_count;
		} else {
			dataset->rows_aggr[day].h_mean = INVALID_VALUE;
		}

		if ( le_count ) {
			dataset->rows_aggr[day].le_mean /= le_count;
		} else {
			dataset->rows_aggr[day].le_mean = INVALID_VALUE;
		}

		if ( g_count ) {
			dataset->rows_aggr[day].value[G_FILLED] /= g_count;
		} else {
			dataset->rows_aggr[day].value[G_FILLED] = INVALID_VALUE;
		}

		if ( !no_rand_unc ) {
			if ( dataset->rows_aggr[day].rand_samples_count[LE_INDEX] ) {
				dataset->rows_aggr[day].rand[LE_INDEX] = SQRT(dataset->rows_aggr[day].rand[LE_INDEX]) / dataset->rows_aggr[day].rand_samples_count[LE_INDEX];
			} else {
				dataset->rows_aggr[day].rand[LE_INDEX] = INVALID_VALUE;
			}
			if ( dataset->rows_aggr[day].rand_samples_count[H_INDEX] ) {
				dataset->rows_aggr[day].rand[H_INDEX] = SQRT(dataset->rows_aggr[day].rand[H_INDEX]) / dataset->rows_aggr[day].rand_samples_count[H_INDEX];
			} else {
				dataset->rows_aggr[day].rand[H_INDEX] = INVALID_VALUE;
			}
		}

		/* */
		dataset->rows_aggr[day].value[H] = INVALID_VALUE;
		dataset->rows_aggr[day].value[LE] = INVALID_VALUE;
		dataset->rows_aggr[day].value[NETRAD] = INVALID_VALUE;
		dataset->rows_aggr[day].value[G] = INVALID_VALUE;
		ECBcfs[day] = INVALID_VALUE;
		if ( dataset->rows_aggr[day].n >= (rows_per_day/2) ) {
			dataset->rows_aggr[day].value[H] = 0.0;
			dataset->rows_aggr[day].value[LE] = 0.0;
			dataset->rows_aggr[day].value[NETRAD] = 0.0;
			dataset->rows_aggr[day].value[G] = 0.0;
			for ( j = 0; j < dataset->rows_aggr[day].n; j++ ) {
				dataset->rows_aggr[day].value[H] += dataset->rows[all_valid_rows_index[j]].value[H];
				dataset->rows_aggr[day].value[LE] += dataset->rows[all_valid_rows_index[j]].value[LE];
				dataset->rows_aggr[day].value[G] += dataset->rows[all_valid_rows_index[j]].value[G];
				dataset->rows_aggr[day].value[NETRAD] += dataset->rows[all_valid_rows_index[j]].value[NETRAD];
			}
			dataset->rows_aggr[day].value[H] /= dataset->rows_aggr[day].n;
			dataset->rows_aggr[day].value[LE] /= dataset->rows_aggr[day].n;
			dataset->rows_aggr[day].value[NETRAD] /= dataset->rows_aggr[day].n;
			dataset->rows_aggr[day].value[G] /= dataset->rows_aggr[day].n;

			/* compute ecbcf */
			ECBcf = ECBCF(dataset->rows_aggr[day].value[NETRAD],dataset->rows_aggr[day].value[G], dataset->rows_aggr[day].value[H], dataset->rows_aggr[day].value[LE]);
			if ( IS_VALID_VALUE(ECBcf) ) {
				ECBcfs[day] = ECBcf;
			}
		}

		/* loop on each qc */
		for ( y = 0; y < VARS_TO_FILL; y++ ) {
			PREC v;
            
            /*
                July 25th 2019 - bug on quality flags for gapfilled LE and H fixed in ecbcf.c,
                here also fixed with the following four IF statements
                in order to correctly calculate the QC value in case of missing data
            */

			if ( H_INDEX == y ) v = dataset->rows_aggr[day].value[H];
			if ( LE_INDEX == y ) v = dataset->rows_aggr[day].value[LE];
			if ( G_INDEX == y ) v = dataset->rows_aggr[day].value[G];

			if ( IS_INVALID_VALUE(v) ) {
				dataset->rows_aggr[day].quality[y] = INVALID_VALUE;
			} else {			
				dataset->rows_aggr[day].quality[y] = 0;
				/* loop on agg */
				for ( j = 0; j < rows_per_day; j++ ) {
					if ( ! IS_INVALID_VALUE(dataset->gf_rows[y][i+j].quality)
							&& (dataset->gf_rows[y][i+j].quality < 2) ) {
						++dataset->rows_aggr[day].quality[y];
					}
				}
				dataset->rows_aggr[day].quality[y] /= rows_per_day;
			}
		}

		/* update values */
		dataset->rows_aggr[day].value[LEcorr] = INVALID_VALUE;
		dataset->rows_aggr[day].value[LEcorr25] = INVALID_VALUE;
		dataset->rows_aggr[day].value[LEcorr75] = INVALID_VALUE;
		dataset->rows_aggr[day].value[Hcorr] = INVALID_VALUE;
		dataset->rows_aggr[day].value[Hcorr25] = INVALID_VALUE;
		dataset->rows_aggr[day].value[Hcorr75] = INVALID_VALUE;
		dataset->rows_aggr[day].value[p25] = INVALID_VALUE;
		dataset->rows_aggr[day].value[p50] = INVALID_VALUE;
		dataset->rows_aggr[day].value[p75] = INVALID_VALUE;
		dataset->rows_aggr[day].ecbcf_samples_count = 0;
		dataset->rows_aggr[day].ecbcf_method = 0;

		/* */
		++day;
	}

	/* free memory */
	free(all_valid_rows_index);

	/* get median */
	median = get_median(ECBcfs, dataset->rows_aggr_count, &error);
	if ( error ) {
		puts("unable to get median.");
		return 0;
	}

	/* */
	for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
		ECBcfs_temp[i] = INVALID_VALUE;
	}

	/* */
	if ( !IS_INVALID_VALUE(median) ) {
		/* get 25% percentile */
		perc25 = get_percentile(ECBcfs, dataset->rows_aggr_count, 25, &error);
		if ( error ) {
			puts("unable to get 25% percentile.");
			return 0;
		}

		/* get 75% percentile */
		perc75 = get_percentile(ECBcfs, dataset->rows_aggr_count, 75, &error);
		if ( error ) {
			puts("unable to get 75% percentile.");
			return 0;
		}

		/* get diff */
		diff = ABS(perc75-perc25);

		/* apply filter */
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			if ( (ECBcfs[i] > (median-FACTOR*diff)) && (ECBcfs[i] < (median+FACTOR*diff)) ) {
				ECBcfs_temp[i] = ECBcfs[i];
			}
		}
	}

	/* ok */
	return 1;
}

/* 
	The aggregation of RANDUNC is based on the daily values.
	RANDUNC_WW = SQRT(SUM(RANDUNC_HH)^2)/NUM_HH
	the calculation is based on half hourly data, to start from the daily the equation changes in:
	RANDUNC_WW = SQRT[(SUM(RANDUNC_HH_DAY1)^2)+(SUM(RANDUNC_HH_DAY2)^2)+...+(SUM(RANDUNC_HH_DAY7)^2)]/(NUM_HH_DAY1+NUM_HH_DAY2+...+NUM_HH_DAY7)

	since the daily RANDUNC is also:
	RANDUNC_DD = SQRT(SUM(RANDUNC_HH)^2)/NUM_HH

	we ca say that:
	(SUM(RANDUNC_HH)^2)=(RANDUNC_DD^2)*(NUM_HH^2)

	merging the two we obtain that:
	RANDUNC_WW = SQRT[(SUM((RANDUNC_DD_DAY1^2)*(NUM_HH_DAY1^2)))+(SUM((RANDUNC_DD_DAY2^2)*(NUM_HH_DAY2^2)))+...+((SUM((RANDUNC_DD_DAY7^2)*(NUM_HH_DAY7^2))))]/(NUM_HH_DAY1+NUM_HH_DAY2+...+NUM_HH_DAY7)

	This is the equation used in the code. The same applied to all the other aggregations.
*/
int aggr_by_weeks(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp) {
	int i;
	int j;
	int k;
	int year;
	int week;
	int days_per_week;
	int rows_per_day;
	int rows_per_year;
	int index;
	int error;
	int *all_valid_rows_index;
	int h_count;
	int le_count;
	int g_count;
	char mask;
	PREC ECBcf;
	PREC median;
	PREC perc25;
	PREC perc75;
	PREC diff;
	PREC value;
	int le_rand_sum;
	int h_rand_sum;

	/* get rows per day count */
	rows_per_day = dataset->hourly ? 24 : 48;

	/* 9 given from 366-51*7 */
	all_valid_rows_index = malloc(9*rows_per_day*sizeof*all_valid_rows_index);
	if ( !all_valid_rows_index ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop for each year */
	index = 0;
	dataset->rows_aggr_count = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* get rows_per_year count */
		rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_per_year /= 2;
		}

		/* loop for weeks */
		days_per_week = 7;
		k = 0;
		for ( week = 0; week < 52; week++ ) {
			/* fix for last week */
			if ( 52 - 1 == week ) {
				days_per_week = (IS_LEAP_YEAR(dataset->years[year].year) ? 366 : 365) - 51*7;
			}

			/* get H and LE mean and index of "all" valid */
			h_count = 0;
			le_count = 0;
			g_count = 0;
			dataset->rows_aggr[week+(year*52)].h_mean = 0.0;
			dataset->rows_aggr[week+(year*52)].le_mean = 0.0;
			dataset->rows_aggr[week+(year*52)].n = 0;
			dataset->rows_aggr[week+(year*52)].value[G_FILLED] = 0.0;
			for ( i = 0; i < rows_per_day*days_per_week; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[H]) && (dataset->rows[index+k+i].value[H] == dataset->rows[index+k+i].value[H]) ) {
					dataset->rows_aggr[week+(year*52)].h_mean += dataset->rows[index+k+i].value[H];
					++h_count;
				}
				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[LE]) && (dataset->rows[index+k+i].value[LE] == dataset->rows[index+k+i].value[LE]) ) {
					dataset->rows_aggr[week+(year*52)].le_mean += dataset->rows[index+k+i].value[LE];
					++le_count;
				}

				/* update mask */
				mask = 0;
				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[H]) ) {
					mask |= H_VALID;
				}

				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[LE]) ) {
					mask |= LE_VALID;
				}

				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[G]) ) {
					mask |= G_VALID;
				}

				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[NETRAD]) ) {
					mask |= NETRAD_VALID;
				}

				/* get all valid index */
				if ( IS_FLAG_SET(mask, ECBCF_ALL_VALID) && (dataset->gf_rows[LE_INDEX][index+k+i].quality <= 1) && (dataset->gf_rows[H_INDEX][index+k+i].quality <= 1) ) {
					all_valid_rows_index[(int)dataset->rows_aggr[week+(year*52)].n++] = index+k+i;					
				}

				/* aggr G */
				if ( ! IS_INVALID_VALUE(dataset->gf_rows[G_INDEX][index+k+i].filled) ) {
					dataset->rows_aggr[week+(year*52)].value[G_FILLED] += dataset->gf_rows[G_INDEX][index+k+i].filled;
					++g_count;
				}
			}
			if ( h_count ) { dataset->rows_aggr[week+(year*52)].h_mean /= h_count; } else { dataset->rows_aggr[week+(year*52)].h_mean = INVALID_VALUE; }
			if ( le_count ) { dataset->rows_aggr[week+(year*52)].le_mean /= le_count; } else { dataset->rows_aggr[week+(year*52)].le_mean = INVALID_VALUE; }
			if ( g_count ) { dataset->rows_aggr[week+(year*52)].value[G_FILLED] /= g_count; } else { dataset->rows_aggr[week+(year*52)].value[G_FILLED] = INVALID_VALUE; }

			/* loop on each qc */
			for ( i = 0; i < VARS_TO_FILL; i++ ) {
				PREC v;
                
                /*
                    July 25th 2019 - bug on quality flags for gapfilled LE and H fixed in ecbcf.c,
                    here also fixed with the following four IF statements
                    in order to correctly calculate the QC value in case of missing data
                */

				if ( H_INDEX == i ) v = dataset->rows_aggr[week+(year*52)].h_mean;
				if ( LE_INDEX == i ) v = dataset->rows_aggr[week+(year*52)].le_mean;
				if ( G_INDEX == i ) v = dataset->rows_aggr[week+(year*52)].value[G_FILLED]; 

				if ( IS_INVALID_VALUE(v) ) {
					dataset->rows_aggr[week+(year*52)].quality[i] = INVALID_VALUE;
				} else {
					dataset->rows_aggr[week+(year*52)].quality[i] = 0;
					/* loop on agg */
					for ( j = 0; j < rows_per_day*days_per_week; j++ ) {
						if ( ! IS_INVALID_VALUE(dataset->gf_rows[i][index+k+j].quality)
								&& (dataset->gf_rows[i][index+k+j].quality < 2) ) {
							++dataset->rows_aggr[week+(year*52)].quality[i];
						}
					}
					dataset->rows_aggr[week+(year*52)].quality[i] /= rows_per_day*days_per_week;
				}
			}

			k += rows_per_day*days_per_week;

			dataset->rows_aggr[week+(year*52)].value[H] = INVALID_VALUE;
			dataset->rows_aggr[week+(year*52)].value[LE] = INVALID_VALUE;
			dataset->rows_aggr[week+(year*52)].value[NETRAD] = INVALID_VALUE;
			dataset->rows_aggr[week+(year*52)].value[G] = INVALID_VALUE;
			dataset->rows_aggr[week+(year*52)].value[LEcorr] = INVALID_VALUE;
			dataset->rows_aggr[week+(year*52)].value[Hcorr] = INVALID_VALUE;
			dataset->rows_aggr[week+(year*52)].ecbcf_samples_count = 0;
			dataset->rows_aggr[week+(year*52)].ecbcf_method = FIRST;
			ECBcfs[week+(year*52)] = INVALID_VALUE;
			if ( dataset->rows_aggr[week+(year*52)].n >= (rows_per_day*days_per_week/2) ) {
				dataset->rows_aggr[week+(year*52)].value[H] = 0.0;
				dataset->rows_aggr[week+(year*52)].value[LE] = 0.0;
				dataset->rows_aggr[week+(year*52)].value[NETRAD] = 0.0;
				dataset->rows_aggr[week+(year*52)].value[G] = 0.0;
				for ( j = 0; j < dataset->rows_aggr[week+(year*52)].n; j++ ) {
					dataset->rows_aggr[week+(year*52)].value[H] += dataset->rows[all_valid_rows_index[j]].value[H];
					dataset->rows_aggr[week+(year*52)].value[LE] += dataset->rows[all_valid_rows_index[j]].value[LE];
					dataset->rows_aggr[week+(year*52)].value[G] += dataset->rows[all_valid_rows_index[j]].value[G];
					dataset->rows_aggr[week+(year*52)].value[NETRAD] += dataset->rows[all_valid_rows_index[j]].value[NETRAD];
				}
				dataset->rows_aggr[week+(year*52)].value[H] /= dataset->rows_aggr[week+(year*52)].n;
				dataset->rows_aggr[week+(year*52)].value[LE] /= dataset->rows_aggr[week+(year*52)].n;
				dataset->rows_aggr[week+(year*52)].value[NETRAD] /= dataset->rows_aggr[week+(year*52)].n;
				dataset->rows_aggr[week+(year*52)].value[G] /= dataset->rows_aggr[week+(year*52)].n;
				dataset->rows_aggr[week+(year*52)].ecbcf_samples_count = dataset->rows_aggr[week+(year*52)].n / (rows_per_day * days_per_week);

				/* compute ecbcf */
				ECBcf = ECBCF(dataset->rows_aggr[week+(year*52)].value[NETRAD],dataset->rows_aggr[week+(year*52)].value[G], dataset->rows_aggr[week+(year*52)].value[H], dataset->rows_aggr[week+(year*52)].value[LE]);
				if ( IS_VALID_VALUE(ECBcf) ) {
					ECBcfs[week+(year*52)] = ECBcf;
				}
			}
		}
		
		/* update index */
		index += rows_per_year;
		dataset->rows_aggr_count += 52;
	}

	/* free memory */
	free(all_valid_rows_index);

	/* */
	if ( dataset->years_count*52 != dataset->rows_aggr_count ) {
		printf("aggregated rows should be %d not %d\n", dataset->years_count*52, dataset->rows_aggr_count);
		return 0;
	}

	/* get median */
	median = get_median(ECBcfs, dataset->rows_aggr_count, &error);
	if ( error ) {
		puts("unable to get median.");
		return 0;
	}

	/* */
	for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
		ECBcfs_temp[i] = INVALID_VALUE;
	}

	/* */
	if ( !IS_INVALID_VALUE(median) ) {
		/* get 25% percentile */
		perc25 = get_percentile(ECBcfs, dataset->rows_aggr_count, 25, &error);
		if ( error ) {
			puts("unable to get 25% percentile.");
			return 0;
		}

		/* get 75% percentile */
		perc75 = get_percentile(ECBcfs, dataset->rows_aggr_count, 75, &error);
		if ( error ) {
			puts("unable to get 75% percentile.");
			return 0;
		}

		/* get diff */
		diff = ABS(perc75-perc25);

		/* apply filter and method 1 */
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			dataset->rows_aggr[i].value[p50] = INVALID_VALUE;
			if ( (ECBcfs[i] > (median-FACTOR*diff)) && (ECBcfs[i] < (median+FACTOR*diff)) ) {
				/*
				assert(INVALID_VALUE==ECBcfs[i]);
				*/
				ECBcfs_temp[i] = ECBcfs[i];
				dataset->rows_aggr[i].value[p50] = ECBcfs[i];
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[i].le_mean) ) {
					dataset->rows_aggr[i].value[LEcorr] = dataset->rows_aggr[i].le_mean * ECBcfs[i];
				}
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[i].h_mean) ) {
					dataset->rows_aggr[i].value[Hcorr] = dataset->rows_aggr[i].h_mean * ECBcfs[i];
				}
			} else {
				dataset->rows_aggr[i].ecbcf_method = SECOND;
			}
		}
	} else {
		/* no method */
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {		
			dataset->rows_aggr[i].ecbcf_method = INVALID_VALUE-1;
			dataset->rows_aggr[i].ecbcf_samples_count = INVALID_VALUE;
			dataset->rows_aggr[i].quality[LE_INDEX] = INVALID_VALUE;
			dataset->rows_aggr[i].quality[H_INDEX] = INVALID_VALUE;
		}
	}

	/* loop for each year */
	if ( !no_rand_unc ) {
		index = 0;
		for ( year = 0; year < dataset->years_count; year++ ) {
			/* get rows_per_year count */
			rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( dataset->hourly ) {
				rows_per_year /= 2;
			}
			rows_per_year /= (dataset->hourly ? 24 : 48);

			/* loop for weeks */
			k = 0;
			days_per_week = 7;
			for ( week = 0; week < 52; week++ ) {
				le_rand_sum = 0;
				h_rand_sum = 0;
				dataset->rows_temp[week+(year*52)].rand[LE_INDEX] = 0.0;
				dataset->rows_temp[week+(year*52)].rand[H_INDEX] = 0.0;

				/* fix for last week */
				if ( 52 - 1 == week ) {
					days_per_week = (IS_LEAP_YEAR(dataset->years[year].year) ? 366 : 365) - 51*7;
				}

				for ( i = 0; i < days_per_week; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].rand[LE_INDEX]) ) {
						value = dataset->rows_daily[index+k+i].rand[LE_INDEX];
						value *= value;
						value *= (dataset->rows_daily[index+k+i].rand_samples_count[LE_INDEX] * dataset->rows_daily[index+k+i].rand_samples_count[LE_INDEX]);
						dataset->rows_temp[week+(year*52)].rand[LE_INDEX] += value;
						le_rand_sum += dataset->rows_daily[index+k+i].rand_samples_count[LE_INDEX];
					}
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].rand[H_INDEX]) ) {
						value = dataset->rows_daily[index+k+i].rand[H_INDEX];
						value *= value;
						value *= (dataset->rows_daily[index+k+i].rand_samples_count[H_INDEX] * dataset->rows_daily[index+k+i].rand_samples_count[H_INDEX]);
						dataset->rows_temp[week+(year*52)].rand[H_INDEX] += value;
						h_rand_sum += dataset->rows_daily[index+k+i].rand_samples_count[H_INDEX];
					}
				}

				if ( le_rand_sum ) {
					dataset->rows_temp[week+(year*52)].rand[LE_INDEX] = SQRT(dataset->rows_temp[week+(year*52)].rand[LE_INDEX]) / le_rand_sum;
				} else {
					dataset->rows_temp[week+(year*52)].rand[LE_INDEX] = INVALID_VALUE;
				}

				if ( h_rand_sum ) {
					dataset->rows_temp[week+(year*52)].rand[H_INDEX] = SQRT(dataset->rows_temp[week+(year*52)].rand[H_INDEX]) / h_rand_sum;
				} else {
					dataset->rows_temp[week+(year*52)].rand[H_INDEX] = INVALID_VALUE;
				}
				k += days_per_week;
			}
			index += rows_per_year;
		}
	}

	/* ok */
	return 1;
}

/* 
	please see aggr_by_weeks for infos on RANDUNC aggregation
*/
int aggr_by_months(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp) {
	int i;
	int j;
	int k;
	int year;
	int month;
	int days_per_month_count;
	int rows_per_day;
	int rows_per_year;
	int index;
	int error;
	int *all_valid_rows_index;
	int h_count;
	int le_count;
	int g_count;
	char mask;
	PREC ECBcf;
	PREC median;
	PREC perc25;
	PREC perc75;
	PREC diff;
	PREC value;
	int le_rand_sum;
	int h_rand_sum;

	/* get rows per day count */
	rows_per_day = dataset->hourly ? 24 : 48;

	/* */
	all_valid_rows_index = malloc(31*rows_per_day*sizeof*all_valid_rows_index);
	if ( !all_valid_rows_index ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop for each year */
	index = 0;
	dataset->rows_aggr_count = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* get rows_per_year count */
		rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_per_year /= 2;
		}

		/* loop for months */
		k = 0;
		for ( month = 0; month < 12; month++ ) {
			/* compute days per month count */
			days_per_month_count = days_per_month[month];
			if ( (FEBRUARY == month) && IS_LEAP_YEAR(dataset->years[year].year) ) {
				++days_per_month_count;
			}

			/* get H and LE mean and index of "all" valid */
			h_count = 0;
			le_count = 0;
			g_count = 0;
			dataset->rows_aggr[month+(year*12)].h_mean = 0.0;
			dataset->rows_aggr[month+(year*12)].le_mean = 0.0;
			dataset->rows_aggr[month+(year*12)].n = 0;
			dataset->rows_aggr[month+(year*12)].value[G_FILLED] = 0.0;
			for ( i = 0; i < rows_per_day*days_per_month_count; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[H]) && (dataset->rows[index+k+i].value[H] == dataset->rows[index+k+i].value[H]) ) {
					dataset->rows_aggr[month+(year*12)].h_mean += dataset->rows[index+k+i].value[H];
					++h_count;
				}
				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[LE]) && (dataset->rows[index+k+i].value[LE] == dataset->rows[index+k+i].value[LE]) ) {
					dataset->rows_aggr[month+(year*12)].le_mean += dataset->rows[index+k+i].value[LE];
					++le_count;
				}

				/* update mask */
				mask = 0;
				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[H]) ) {
					mask |= H_VALID;
				}

				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[LE]) ) {
					mask |= LE_VALID;
				}

				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[G]) ) {
					mask |= G_VALID;
				}

				if ( !IS_INVALID_VALUE(dataset->rows[index+k+i].value[NETRAD]) ) {
					mask |= NETRAD_VALID;
				}

				/* get all valid index */
				if ( IS_FLAG_SET(mask, ECBCF_ALL_VALID) && (dataset->gf_rows[LE_INDEX][index+k+i].quality <= 1) && (dataset->gf_rows[H_INDEX][index+k+i].quality <= 1) ) {
					all_valid_rows_index[(int)dataset->rows_aggr[month+(year*12)].n++] = index+k+i;					
				}

				/* aggr G */
				if ( ! IS_INVALID_VALUE(dataset->gf_rows[G_INDEX][index+k+i].filled) ) {
					dataset->rows_aggr[month+(year*12)].value[G_FILLED] += dataset->gf_rows[G_INDEX][index+k+i].filled;
					++g_count;
				}
			}
			if ( h_count ) { dataset->rows_aggr[month+(year*12)].h_mean /= h_count; } else { dataset->rows_aggr[month+(year*12)].h_mean = INVALID_VALUE; }
			if ( le_count ) { dataset->rows_aggr[month+(year*12)].le_mean /= le_count; } else { dataset->rows_aggr[month+(year*12)].le_mean = INVALID_VALUE; }
			if ( g_count ) { dataset->rows_aggr[month+(year*12)].value[G_FILLED] /= g_count; } else { dataset->rows_aggr[month+(year*12)].value[G_FILLED] = INVALID_VALUE; }

			/* loop on each qc */
			for ( i = 0; i < VARS_TO_FILL; i++ ) {
				PREC v;
                
                /*
                    July 25th 2019 - bug on quality flags for gapfilled LE and H fixed in ecbcf.c,
                    here also fixed with the following four IF statements
                    in order to correctly calculate the QC value in case of missing data
                */

				if ( H_INDEX == i ) v = dataset->rows_aggr[month+(year*12)].h_mean;
				if ( LE_INDEX == i ) v = dataset->rows_aggr[month+(year*12)].le_mean;
				if ( G_INDEX == i ) v = dataset->rows_aggr[month+(year*12)].value[G_FILLED];

				if ( IS_INVALID_VALUE(v) ) {
					dataset->rows_aggr[month+(year*12)].quality[i] = INVALID_VALUE;
				} else {
					dataset->rows_aggr[month+(year*12)].quality[i] = 0;
					/* loop on agg */
					for ( j = 0; j < rows_per_day*days_per_month_count; j++ ) {
						if ( ! IS_INVALID_VALUE(dataset->gf_rows[i][index+k+j].quality)
								&& (dataset->gf_rows[i][index+k+j].quality < 2) ) {
							++dataset->rows_aggr[month+(year*12)].quality[i];
						}
					}
					dataset->rows_aggr[month+(year*12)].quality[i] /= rows_per_day*days_per_month_count;
				}
			}

			k += rows_per_day*days_per_month_count;

			/* */
			dataset->rows_aggr[month+(year*12)].value[H] = INVALID_VALUE;
			dataset->rows_aggr[month+(year*12)].value[LE] = INVALID_VALUE;
			dataset->rows_aggr[month+(year*12)].value[NETRAD] = INVALID_VALUE;
			dataset->rows_aggr[month+(year*12)].value[G] = INVALID_VALUE;
			dataset->rows_aggr[month+(year*12)].value[LEcorr] = INVALID_VALUE;
			dataset->rows_aggr[month+(year*12)].value[Hcorr] = INVALID_VALUE;
			dataset->rows_aggr[month+(year*12)].ecbcf_method = FIRST;
			dataset->rows_aggr[month+(year*12)].ecbcf_samples_count = 0;
			ECBcfs[month+(year*12)] = INVALID_VALUE;			
			if ( dataset->rows_aggr[month+(year*12)].n >= (rows_per_day*days_per_month_count/2) ) {
				dataset->rows_aggr[month+(year*12)].value[H] = 0.0;
				dataset->rows_aggr[month+(year*12)].value[LE] = 0.0;
				dataset->rows_aggr[month+(year*12)].value[NETRAD] = 0.0;
				dataset->rows_aggr[month+(year*12)].value[G] = 0.0;
				for ( j = 0; j < dataset->rows_aggr[month+(year*12)].n; j++ ) {
					dataset->rows_aggr[month+(year*12)].value[H] += dataset->rows[all_valid_rows_index[j]].value[H];
					dataset->rows_aggr[month+(year*12)].value[LE] += dataset->rows[all_valid_rows_index[j]].value[LE];
					dataset->rows_aggr[month+(year*12)].value[G] += dataset->rows[all_valid_rows_index[j]].value[G];
					dataset->rows_aggr[month+(year*12)].value[NETRAD] += dataset->rows[all_valid_rows_index[j]].value[NETRAD];
				}
				dataset->rows_aggr[month+(year*12)].value[H] /= dataset->rows_aggr[month+(year*12)].n;
				dataset->rows_aggr[month+(year*12)].value[LE] /= dataset->rows_aggr[month+(year*12)].n;
				dataset->rows_aggr[month+(year*12)].value[NETRAD] /= dataset->rows_aggr[month+(year*12)].n;
				dataset->rows_aggr[month+(year*12)].value[G] /= dataset->rows_aggr[month+(year*12)].n;
				dataset->rows_aggr[month+(year*12)].ecbcf_samples_count = dataset->rows_aggr[month+(year*12)].n / (rows_per_day*days_per_month_count);

				/* compute ecbcf */
				ECBcf = ECBCF(dataset->rows_aggr[month+(year*12)].value[NETRAD], dataset->rows_aggr[month+(year*12)].value[G], dataset->rows_aggr[month+(year*12)].value[H], dataset->rows_aggr[month+(year*12)].value[LE]);
				if ( IS_VALID_VALUE(ECBcf) ) {
					ECBcfs[month+(year*12)] = ECBcf;
				}
			}
		}
		
		/* update index */
		index += rows_per_year;
		dataset->rows_aggr_count += 12;
	}

	/* free memory */
	free(all_valid_rows_index);

	/* */
	if ( dataset->years_count*12 != dataset->rows_aggr_count ) {
		printf("aggregated rows should be %d not %d\n", dataset->years_count*12, dataset->rows_aggr_count);
		return 0;
	}

	/* get median */
	median = get_median(ECBcfs, dataset->rows_aggr_count, &error);
	if ( error ) {
		puts("unable to get median.");
		return 0;
	}

	/* */
	for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
		ECBcfs_temp[i] = INVALID_VALUE;
	}

	/* */
	if ( !IS_INVALID_VALUE(median) ) {
		/* get 25% percentile */
		perc25 = get_percentile(ECBcfs, dataset->rows_aggr_count, 25, &error);
		if ( error ) {
			puts("unable to get 25% percentile.");
			return 0;
		}

		/* get 75% percentile */
		perc75 = get_percentile(ECBcfs, dataset->rows_aggr_count, 75, &error);
		if ( error ) {
			puts("unable to get 75% percentile.");
			return 0;
		}

		/* get diff */
		diff = ABS(perc75-perc25);

		/* apply filter */
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			dataset->rows_aggr[i].value[p50] = INVALID_VALUE;
			if ( (ECBcfs[i] > (median-FACTOR*diff)) && (ECBcfs[i] < (median+FACTOR*diff)) ) {
				/*
				assert(INVALID_VALUE==ECBcfs[i]);
				*/
				ECBcfs_temp[i] = ECBcfs[i];
				dataset->rows_aggr[i].value[p50] = ECBcfs[i];
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[i].le_mean) ) {
					dataset->rows_aggr[i].value[LEcorr] = dataset->rows_aggr[i].le_mean * ECBcfs[i];
				}
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[i].h_mean) ) {
					dataset->rows_aggr[i].value[Hcorr] = dataset->rows_aggr[i].h_mean * ECBcfs[i];
				}
			} else {
				dataset->rows_aggr[i].ecbcf_method = SECOND;
			}
		}
	} else {
		/* no method */
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {		
			dataset->rows_aggr[i].ecbcf_method = INVALID_VALUE-1;
			dataset->rows_aggr[i].ecbcf_samples_count = INVALID_VALUE;
			dataset->rows_aggr[i].quality[LE_INDEX] = INVALID_VALUE;
			dataset->rows_aggr[i].quality[H_INDEX] = INVALID_VALUE;
		}
	}

	/* loop for each year */
	if ( !no_rand_unc ) {
		index = 0;
		for ( year = 0; year < dataset->years_count; year++ ) {
			/* get rows_per_year count */
			rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( dataset->hourly ) {
				rows_per_year /= 2;
			}
			rows_per_year /= (dataset->hourly ? 24 : 48);

			/* loop for weeks */
			k = 0;
			for ( month = 0; month < 12; month++ ) {
				/* compute days per month count */
				days_per_month_count = days_per_month[month];
				if ( (FEBRUARY == month) && IS_LEAP_YEAR(dataset->years[year].year) ) {
					++days_per_month_count;
				}

				le_rand_sum = 0;
				h_rand_sum = 0;
				dataset->rows_temp[month+(year*12)].rand[LE_INDEX] = 0.0;
				dataset->rows_temp[month+(year*12)].rand[H_INDEX] = 0.0;

				for ( i = 0; i < days_per_month_count; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].rand[LE_INDEX]) ) {
						value = dataset->rows_daily[index+k+i].rand[LE_INDEX];
						value *= value;
						value *= (dataset->rows_daily[index+k+i].rand_samples_count[LE_INDEX] * dataset->rows_daily[index+k+i].rand_samples_count[LE_INDEX]);
						dataset->rows_temp[month+(year*12)].rand[LE_INDEX] += value;
						le_rand_sum += dataset->rows_daily[index+k+i].rand_samples_count[LE_INDEX];
					}
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].rand[H_INDEX]) ) {
						value = dataset->rows_daily[index+k+i].rand[H_INDEX];
						value *= value;
						value *= (dataset->rows_daily[index+k+i].rand_samples_count[H_INDEX] * dataset->rows_daily[index+k+i].rand_samples_count[H_INDEX]);
						dataset->rows_temp[month+(year*12)].rand[H_INDEX] += value;
						h_rand_sum += dataset->rows_daily[index+k+i].rand_samples_count[H_INDEX];
					}
				}

				if ( le_rand_sum ) {
					dataset->rows_temp[month+(year*12)].rand[LE_INDEX] = SQRT(dataset->rows_temp[month+(year*12)].rand[LE_INDEX]) / le_rand_sum;
				} else {
					dataset->rows_temp[month+(year*12)].rand[LE_INDEX] = INVALID_VALUE;
				}

				if ( h_rand_sum ) {
					dataset->rows_temp[month+(year*12)].rand[H_INDEX] = SQRT(dataset->rows_temp[month+(year*12)].rand[H_INDEX]) / h_rand_sum;
				} else {
					dataset->rows_temp[month+(year*12)].rand[H_INDEX] = INVALID_VALUE;
				}
				k += days_per_month_count;
			}
			index += rows_per_year;
		}
	}

	/* ok */
	return 1;
}

/*
	please see aggr_by_weeks for infos on RANDUNC aggregation
*/
int aggr_by_years(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp) {
	int i;
	int j;
	int year;
	int rows_per_day;
	int rows_per_year;
	int index;
	int error;
	int *all_valid_rows_index;
	int h_count;
	int le_count;
	int g_count;
	int le_rand_sum;
	int h_rand_sum;
	char mask;
	PREC ECBcf;
	PREC median;
	PREC perc25;
	PREC perc75;
	PREC diff;
	PREC value;
	
	/* get rows per day count */
	rows_per_day = dataset->hourly ? 24 : 48;

	/* */
	all_valid_rows_index = malloc(366*rows_per_day*sizeof*all_valid_rows_index);
	if ( !all_valid_rows_index ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop for each year */
	index = 0;
	dataset->rows_aggr_count = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* get rows_per_year count */
		rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_per_year /= 2;
		}
		/* get H and LE mean and index of "all" valid */
		h_count = 0;
		le_count = 0;
		g_count = 0;
		dataset->rows_aggr[year].h_mean = 0.0;
		dataset->rows_aggr[year].le_mean = 0.0;
		dataset->rows_aggr[year].n = 0;
		dataset->rows_aggr[year].value[G_FILLED] = 0.0;
		for ( i = 0; i < rows_per_year; i++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows[index+i].value[H]) && (dataset->rows[index+i].value[H] == dataset->rows[index+i].value[H]) ) {
				dataset->rows_aggr[year].h_mean += dataset->rows[index+i].value[H];
				++h_count;
			}
			if ( !IS_INVALID_VALUE(dataset->rows[index+i].value[LE]) && (dataset->rows[index+i].value[LE] == dataset->rows[index+i].value[LE]) ) {
				dataset->rows_aggr[year].le_mean += dataset->rows[index+i].value[LE];
				++le_count;
			}

			/* update mask */
			mask = 0;
			if ( !IS_INVALID_VALUE(dataset->rows[index+i].value[H]) ) {
				mask |= H_VALID;
			}

			if ( !IS_INVALID_VALUE(dataset->rows[index+i].value[LE]) ) {
				mask |= LE_VALID;
			}

			if ( !IS_INVALID_VALUE(dataset->rows[index+i].value[G]) ) {
				mask |= G_VALID;
			}

			if ( !IS_INVALID_VALUE(dataset->rows[index+i].value[NETRAD]) ) {
				mask |= NETRAD_VALID;
			}

			/* get all valid index */
			if ( IS_FLAG_SET(mask, ECBCF_ALL_VALID) && (dataset->gf_rows[LE_INDEX][index+i].quality <= 1) && (dataset->gf_rows[H_INDEX][index+i].quality <= 1) ) {
				all_valid_rows_index[(int)dataset->rows_aggr[year].n++] = index+i;					
			}

			/* aggr G */
			if ( ! IS_INVALID_VALUE(dataset->gf_rows[G_INDEX][index+i].filled) ) {
				dataset->rows_aggr[year].value[G_FILLED] += dataset->gf_rows[G_INDEX][index+i].filled;
				++g_count;
			}
		}
		if ( h_count ) { dataset->rows_aggr[year].h_mean /= h_count; } else { dataset->rows_aggr[year].h_mean = INVALID_VALUE; }
		if ( le_count ) { dataset->rows_aggr[year].le_mean /= le_count; } else { dataset->rows_aggr[year].le_mean = INVALID_VALUE; }
		if ( g_count ) { dataset->rows_aggr[year].value[G_FILLED] /= g_count; } else { dataset->rows_aggr[year].value[G_FILLED] = INVALID_VALUE; }

		/* loop on each qc */
		for ( i = 0; i < VARS_TO_FILL; i++ ) {
			PREC v;
            
            /*
                July 25th 2019 - bug on quality flags for gapfilled LE and H fixed in ecbcf.c,
                here also fixed with the following four IF statements
                in order to correctly calculate the QC value in case of missing data
            */

			if ( H_INDEX == i ) v = dataset->rows_aggr[year].h_mean;
			if ( LE_INDEX == i ) v = dataset->rows_aggr[year].le_mean;
			if ( G_INDEX == i ) v = dataset->rows_aggr[year].value[G_FILLED]; 

			if ( IS_INVALID_VALUE(v) ) {
				dataset->rows_aggr[year].quality[i] = INVALID_VALUE;
			} else {
				dataset->rows_aggr[year].quality[i] = 0;
				/* loop on agg */
				for ( j = 0; j < rows_per_year; j++ ) {
					if ( ! IS_INVALID_VALUE(dataset->gf_rows[i][index+j].quality)
							&& (dataset->gf_rows[i][index+j].quality < 2) ) {
						++dataset->rows_aggr[year].quality[i];
					}
				}
				dataset->rows_aggr[year].quality[i] /= rows_per_year;
			}
		}

		/* */
		dataset->rows_aggr[year].value[H] = INVALID_VALUE;
		dataset->rows_aggr[year].value[LE] = INVALID_VALUE;
		dataset->rows_aggr[year].value[NETRAD] = INVALID_VALUE;
		dataset->rows_aggr[year].value[G] = INVALID_VALUE;
		dataset->rows_aggr[year].value[LEcorr] = INVALID_VALUE;
		dataset->rows_aggr[year].value[Hcorr] = INVALID_VALUE;
		dataset->rows_aggr[year].value[p50] = INVALID_VALUE;
		dataset->rows_aggr[year].ecbcf_samples_count = 0;
		dataset->rows_aggr[year].ecbcf_method = FIRST;
		ECBcfs[year] = INVALID_VALUE;
		if ( dataset->rows_aggr[year].n >= (rows_per_year / 2) ) {
			dataset->rows_aggr[year].value[H] = 0.0;
			dataset->rows_aggr[year].value[LE] = 0.0;
			dataset->rows_aggr[year].value[NETRAD] = 0.0;
			dataset->rows_aggr[year].value[G] = 0.0;
			for ( j = 0; j < dataset->rows_aggr[year].n; j++ ) {
				dataset->rows_aggr[year].value[H] += dataset->rows[all_valid_rows_index[j]].value[H];
				dataset->rows_aggr[year].value[LE] += dataset->rows[all_valid_rows_index[j]].value[LE];
				dataset->rows_aggr[year].value[G] += dataset->rows[all_valid_rows_index[j]].value[G];
				dataset->rows_aggr[year].value[NETRAD] += dataset->rows[all_valid_rows_index[j]].value[NETRAD];
			}
			dataset->rows_aggr[year].value[H] /= dataset->rows_aggr[year].n;
			dataset->rows_aggr[year].value[LE] /= dataset->rows_aggr[year].n;
			dataset->rows_aggr[year].value[NETRAD] /= dataset->rows_aggr[year].n;
			dataset->rows_aggr[year].value[G] /= dataset->rows_aggr[year].n;
			dataset->rows_aggr[year].ecbcf_samples_count = dataset->rows_aggr[year].n / rows_per_year;

			/* compute ecbcf */
			ECBcf = ECBCF(dataset->rows_aggr[year].value[NETRAD], dataset->rows_aggr[year].value[G], dataset->rows_aggr[year].value[H], dataset->rows_aggr[year].value[LE]);
			if ( IS_VALID_VALUE(ECBcf) ) {
				ECBcfs[year] = ECBcf;
			}
		}

		/* update index */
		index += rows_per_year;
		++dataset->rows_aggr_count;
	}

	/* free memory */
	free(all_valid_rows_index);

	/* */
	if ( dataset->years_count != dataset->rows_aggr_count ) {
		printf("aggregated rows should be %d not %d\n", dataset->years_count, dataset->rows_aggr_count);
		return 0;
	}

	/* get median */
	median = get_median(ECBcfs, dataset->rows_aggr_count, &error);
	if ( error ) {
		puts("unable to get median.");
		return 0;
	}

	for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
		ECBcfs_temp[i] = INVALID_VALUE;
	}

	/* */
	if ( !IS_INVALID_VALUE(median) ) {
		/* get 25% percentile */
		perc25 = get_percentile(ECBcfs, dataset->rows_aggr_count, 25, &error);
		if ( error ) {
			puts("unable to get 25% percentile.");
			return 0;
		}

		/* get 75% percentile */
		perc75 = get_percentile(ECBcfs, dataset->rows_aggr_count, 75, &error);
		if ( error ) {
			puts("unable to get 75% percentile.");
			return 0;
		}

		/* get diff */
		diff = ABS(perc75-perc25);

		/* apply filter */
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			dataset->rows_aggr[i].value[p50] = INVALID_VALUE;
			if ( (ECBcfs[i] > (median-FACTOR*diff)) && (ECBcfs[i] < (median+FACTOR*diff)) ) {
				/*
				assert(INVALID_VALUE==ECBcfs[i]);
				*/
				ECBcfs_temp[i] = ECBcfs[i];
				dataset->rows_aggr[i].value[p50] = ECBcfs[i];
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[i].le_mean) ) {
					dataset->rows_aggr[i].value[LEcorr] = dataset->rows_aggr[i].le_mean * ECBcfs[i];
				}
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[i].h_mean) ) {
					dataset->rows_aggr[i].value[Hcorr] = dataset->rows_aggr[i].h_mean * ECBcfs[i];
				}
			} else {
				dataset->rows_aggr[i].ecbcf_method = SECOND;
			}
		}
	} else {
		/* no method */
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {		
			dataset->rows_aggr[i].ecbcf_method = INVALID_VALUE-1;
			dataset->rows_aggr[i].ecbcf_samples_count = INVALID_VALUE;
			dataset->rows_aggr[i].quality[LE_INDEX] = INVALID_VALUE;
			dataset->rows_aggr[i].quality[H_INDEX] = INVALID_VALUE;
		}
	}

	/* loop for each year */
	if ( !no_rand_unc ) {
		index = 0;
		for ( year = 0; year < dataset->years_count; year++ ) {
			/* get rows_per_year count */
			rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( dataset->hourly ) {
				rows_per_year /= 2;
			}
			rows_per_year /= (dataset->hourly ? 24 : 48);

			le_rand_sum = 0;
			h_rand_sum = 0;
			dataset->rows_temp[year].rand[LE_INDEX] = 0.0;
			dataset->rows_temp[year].rand[H_INDEX] = 0.0;
			for ( i = 0; i < rows_per_year; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows_daily[index+i].rand[LE_INDEX]) ) {
					value = dataset->rows_daily[index+i].rand[LE_INDEX];
					value *= value;
					value *= (dataset->rows_daily[index+i].rand_samples_count[LE_INDEX] * dataset->rows_daily[index+i].rand_samples_count[LE_INDEX]);
					dataset->rows_temp[year].rand[LE_INDEX] += value;
					le_rand_sum += dataset->rows_daily[index+i].rand_samples_count[LE_INDEX];
				}
				if ( !IS_INVALID_VALUE(dataset->rows_daily[index+i].rand[H_INDEX]) ) {
					value = dataset->rows_daily[index+i].rand[H_INDEX];
					value *= value;
					value *= (dataset->rows_daily[index+i].rand_samples_count[H_INDEX] * dataset->rows_daily[index+i].rand_samples_count[H_INDEX]);
					dataset->rows_temp[year].rand[H_INDEX] += value;
					h_rand_sum += dataset->rows_daily[index+i].rand_samples_count[H_INDEX];
				}
			}

			if ( le_rand_sum ) {
				dataset->rows_temp[year].rand[LE_INDEX] = SQRT(dataset->rows_temp[year].rand[LE_INDEX]) / le_rand_sum;
			} else {
				dataset->rows_temp[year].rand[LE_INDEX] = INVALID_VALUE;
			}

			if ( h_rand_sum ) {
				dataset->rows_temp[year].rand[H_INDEX] = SQRT(dataset->rows_temp[year].rand[H_INDEX]) / h_rand_sum;
			} else {
				dataset->rows_temp[year].rand[H_INDEX] = INVALID_VALUE;
			}
			index += rows_per_year;
		}
	}

	/* ok */
	return 1;
}
