/*
	ecbcf.c

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "ecbcf.h"
#include "dataset.h"

/* extern variables */
extern const char err_out_of_memory[];

/* */
static const int days_in_month[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

/* */
static PREC get_median_from_all_valids(const PREC *const values, const int count) {
	PREC result;

	/* check for null pointer */
	assert(values);

	if ( !count ) {
		return INVALID_VALUE;
	} else if ( 1 == count ) {
		return values[0];
	}

	/* sort values */
	qsort(values, count, sizeof *values, compare_prec);

	/* get median */
	if ( count & 1 ) {
		result = values[((count+1)/2)-1];
	} else {
		result = ((values[(count/2)-1] + values[count/2]) / 2);
	}

	/* check for NAN */
	if ( result != result ) {
		result = INVALID_VALUE;
	}

	/* */
	return result;
}

/* */
static PREC get_percentile_from_all_valids(PREC *const values, const int n, const float percentile, int *const error) {
	int index;
	PREC r;

	/* check parameters */
	assert(values && error);

	/* reset */
	*error = 0;

	/* */
	if ( !n ) {
		return 0.0;
	} else if ( 1 == n ) {
		return values[0];
	}

	/* percentile MUST be a value between 0 and 100*/
	if ( percentile < 0.0 || percentile > 100.0 ) {
		*error = 1;
		return 0.0;
	}

	/* */
	qsort(values, n, sizeof *values, compare_prec);

	/* */
	index = ROUND((percentile / 100.0) * n + 0.5);
	--index;
	if ( index >= n ) {
		return values[n-1];
	}

	/* */
	r = values[index];

	/* */
	return r;
}

/* */
int ecbcf_temp_hh(DATASET *const dataset, PREC *const ecbcfs, PREC *const ecbcfs_temp, PREC *const temp) {
	int i;
	int valids_count;
	int error;
	PREC ECBcf;
	PREC median;
	PREC p25;
	PREC p75;
	PREC diff;

	/* */
	assert(ecbcfs && ecbcfs_temp && temp);

	/* loop on each rows */
	valids_count = 0;
	for ( i = 0; i < dataset->rows_count; i++ ) {
		ecbcfs[i] = INVALID_VALUE;
		if ( IS_FLAG_SET(dataset->rows[i].ecbcf_mask, ECBCF_ALL_VALID) && (dataset->gf_rows[LE_INDEX][i].quality <= 1) && (dataset->gf_rows[H_INDEX][i].quality <= 1) ) {
			ECBcf = ECBCF(dataset->rows[i].value[NETRAD],dataset->rows[i].value[G], dataset->rows[i].value[H], dataset->rows[i].value[LE]);
			if ( IS_VALID_VALUE(ECBcf) ) {
				ecbcfs[i] = ECBcf;
				temp[valids_count++] = ECBcf; /* we need ecbcfs unsorted */
			}
		}
	}

	/*
		remove outliers from the array of calculated ECBCF
	*/

	/* added on May 13, 2013 */
	if ( valids_count ) {
		/* get median */
		median = get_median_from_all_valids(temp, valids_count);
		if ( IS_INVALID_VALUE(median) ) {
			puts("unable to get median.");
			return 0;
		}

		/* get 25% percentile */
		p25 = get_percentile_from_all_valids(temp, valids_count, 25, &error);
		if ( error ) {
			puts("unable to get 25% percentile.");
			return 0;
		}

		/* get 75% percentile */
		p75 = get_percentile_from_all_valids(temp, valids_count, 75, &error);
		if ( error ) {
			puts("unable to get 75% percentile.");
			return 0;
		}

		/* get diff ( interquartile range )*/
		diff = ABS(p75-p25);

		/* apply filter */
		for ( i = 0; i < dataset->rows_count; i++ ) {
			ecbcfs_temp[i] = INVALID_VALUE;
			if ( (ecbcfs[i] > (median-FACTOR*diff)) && (ecbcfs[i] < (median+FACTOR*diff)) ) {
				ecbcfs_temp[i] = ecbcfs[i];
			}
		}
	} else {
		for ( i = 0; i < dataset->rows_count; i++ ) {
			ecbcfs_temp[i] = INVALID_VALUE;
		}
	}

	/* ok */
	return 1;
}

/* */
static void get_hhmm_from_row(int row, int *const hour, int *const minute, const int hourly) {
	assert(hour && minute);

	/* use 1 based index*/
	++row;

	*minute = 0;
	*hour = row % (hourly ? 24 : 48);
	if ( ! hourly ) {
		*hour /= 2;
		/* even row ? */
		if ( row & 1 ) {
			*minute = 30;
		}
	}
}

/* */
int ecbcf_hh(DATASET *const dataset, const int current_row, PREC *const ECBcfs, PREC *const ECBcfs_temp, PREC *const temp, const int window_size, const int windows_size_alt) {
	int i;
	int j;
	int n;
	int hh;
	int mm;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int rows_per_day;
	int rows_to_add;
	int years;
	PREC ECBcf;

	/* check parameter */
	assert(dataset && ECBcfs);

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	ECBcf = 0.0;
	n = 0;

	/* */
	rows_per_day = dataset->hourly ? 24 :48;

	/* */
	if ( THIRD == dataset->rows[current_row].ecbcf_method ) {
		if ( dataset->years_count > 1 ) {
			int index;
			int before;
			int after;
			int ok;
			int m;

			/* compute window size */
			window = (windows_size_alt / 2) * rows_per_day;

			/* */
			m = 1;
			ok = 0;
			do {
				for ( years = 1; years < 3; years++ ) {
					/* get index of dataset */
					j = 0;
					index = -1;
					for ( i = 0; i < dataset->years_count; i++ ) {
						rows_to_add = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
						if ( dataset->hourly ) {
							rows_to_add /= 2;
						}
						j += rows_to_add;
						if ( current_row < j ) {
							index = i;
							break;
						}
					}
					assert(index != -1);

					/* */
					before = index - years;
					after = index + years;
					if ( after >= dataset->years_count ) {
						after = -1;
					}

					/* */
					window *= m;
					j = 5; /* -1h +1h */
					if ( dataset->hourly ) {
						j = 3;
					}

					/* */
					if ( before >= 0 ) {
						rows_to_add = IS_LEAP_YEAR(dataset->years[before].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
						if ( dataset->hourly ) {
							rows_to_add /= 2;
						}
						i = current_row - rows_to_add;
						if ( years > 1 ) {
							rows_to_add = IS_LEAP_YEAR(dataset->years[before+1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
							if ( dataset->hourly ) {
								rows_to_add /= 2;
							}
							i -= rows_to_add;
						}
						window_start = i - window - 2; /* -2 = -1h */
						if ( dataset->hourly ) {
							++window_start;
						}
						window_end = i + window;

						/* loop on window */
						for ( window_current = window_start; window_current < window_end; window_current += rows_per_day ) {
							for ( i = 0; i < j; i++ ) {		
								if ( (window_current+i >= 0) && (window_current+i < dataset->rows_count) ) {
									if ( !IS_INVALID_VALUE(dataset->rows[window_current+i].value[LEcorr]) && (FIRST == dataset->rows[window_current+i].ecbcf_method) ) {
										ECBcf = dataset->rows[window_current+i].value[LEcorr] / dataset->rows[window_current+i].value[LE];
										if ( IS_VALID_VALUE(ECBcf) ) {
											ECBcfs[n++] = ECBcf;
										}
									}
								}
							}
						}
					}

					if ( after > 0 ) {
						rows_to_add = IS_LEAP_YEAR(dataset->years[after-1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
						if ( dataset->hourly ) {
							rows_to_add /= 2;
						}
						i = current_row + rows_to_add;
						if ( years > 1 ) {
							rows_to_add = IS_LEAP_YEAR(dataset->years[after].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
							if ( dataset->hourly ) {
								rows_to_add /= 2;
							}
							i += rows_to_add;
						}
						window_start = i - window - 2; /* -2 = -1h */
						if ( dataset->hourly ) {
							++window_start;
						}
						window_end = i + window;

						/* loop on window for LE */
						for ( window_current = window_start; window_current < window_end; window_current += rows_per_day ) {
							for ( i = 0; i < j; i++ ) {		
								if ( (window_current+i >= 0) && (window_current+i < dataset->rows_count) ) {
									if ( !IS_INVALID_VALUE(dataset->rows[window_current+i].value[LEcorr]) && (FIRST == dataset->rows[window_current+i].ecbcf_method) ) {
										ECBcf = dataset->rows[window_current+i].value[LEcorr] / dataset->rows[window_current+i].value[LE];
										if ( IS_VALID_VALUE(ECBcf) ) {
											ECBcfs[n++] = ECBcf;
										}
									}
								}
							}
						}
					}

					/* */
					if ( n ) {
						ECBcf = 0.0;
						for ( i = 0; i < n; i++ ) {
							ECBcf += ECBcfs[i];
						}

						ECBcf /= n;
						dataset->rows[current_row].ecbcf_samples_count = n;
						dataset->rows[current_row].value[LEcorr] = INVALID_VALUE;
						if ( !IS_INVALID_VALUE(dataset->rows[current_row].value[LE]) ) {
							dataset->rows[current_row].value[LEcorr] = ECBcf * dataset->rows[current_row].value[LE];
						}

						/* loop on window for H */
						n = 0;

						/* */
						if ( before >= 0 ) {
							rows_to_add = IS_LEAP_YEAR(dataset->years[before].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
							if ( dataset->hourly ) {
								rows_to_add /= 2;
							}
							i = current_row - rows_to_add;
							if ( years > 1 ) {
								rows_to_add = IS_LEAP_YEAR(dataset->years[before+1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
								if ( dataset->hourly ) {
									rows_to_add /= 2;
								}
								i -= rows_to_add;
							}
							window_start = i - window - 2; /* -2 = -1h */
							if ( dataset->hourly ) {
								++window_start;
							}
							window_end = i + window;

							/* loop on window for H */
							for ( window_current = window_start; window_current < window_end; window_current += rows_per_day ) {
								for ( i = 0; i < j; i++ ) {		
									if ( (window_current+i >= 0) && (window_current+i < dataset->rows_count) ) {
										if ( !IS_INVALID_VALUE(dataset->rows[window_current+i].value[Hcorr]) && (FIRST == dataset->rows[window_current+i].ecbcf_method) ) {
											ECBcf = dataset->rows[window_current+i].value[Hcorr] / dataset->rows[window_current+i].value[H];
											if ( IS_VALID_VALUE(ECBcf) ) {
												ECBcfs[n++] = ECBcf;
											}
										}
									}
								}
							}
						}

						if ( after > 0 ) {
							rows_to_add = IS_LEAP_YEAR(dataset->years[after-1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
							if ( dataset->hourly ) {
								rows_to_add /= 2;
							}
							i = current_row + rows_to_add;
							if ( years > 1 ) {
								rows_to_add = IS_LEAP_YEAR(dataset->years[after].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
								if ( dataset->hourly ) {
									rows_to_add /= 2;
								}
								i += rows_to_add;
							}
							window_start = i - window - 2; /* -2 = -1h */
							if ( dataset->hourly ) {
								++window_start;
							}
							window_end = i + window;

							/* loop on window for H */
							for ( window_current = window_start; window_current < window_end; window_current += rows_per_day ) {
								for ( i = 0; i < j; i++ ) {		
									if ( (window_current+i >= 0) && (window_current+i < dataset->rows_count) ) {
										if ( !IS_INVALID_VALUE(dataset->rows[window_current+i].value[Hcorr]) && (FIRST == dataset->rows[window_current+i].ecbcf_method) ) {
											ECBcf = dataset->rows[window_current+i].value[Hcorr] / dataset->rows[window_current+i].value[H];
											if ( IS_VALID_VALUE(ECBcf) ) {
												ECBcfs[n++] = ECBcf;
											}
										}
									}
								}
							}
						}

						ECBcf = 0.0;
						for ( i = 0; i < n; i++ ) {
							ECBcf += ECBcfs[i];
						}

						ECBcf /= n;
						dataset->rows[current_row].value[Hcorr] = INVALID_VALUE;
						if ( !IS_INVALID_VALUE(dataset->rows[current_row].value[H]) ) {
							dataset->rows[current_row].value[Hcorr] = ECBcf * dataset->rows[current_row].value[H];
						}

						/* update flag */
						ok = 1;
						break;
					} 
				}

				/* */
				if ( ok ) {
					break;
				}

				/* */
				++m;
			} while ( m < 3 );

			/* */
			if ( !ok ) {
				/* no method */
				dataset->rows[current_row].ecbcf_method = INVALID_VALUE-1;
				dataset->rows[current_row].ecbcf_samples_count = INVALID_VALUE;

				// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
				// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
				// FLUXNET2015 release
				//dataset->gf_rows[LE_INDEX][current_row].quality = INVALID_VALUE;
				//dataset->gf_rows[H_INDEX][current_row].quality = INVALID_VALUE;
			}
		} else {
			/* no method */
			dataset->rows[current_row].ecbcf_method = INVALID_VALUE-1;
			dataset->rows[current_row].ecbcf_samples_count = INVALID_VALUE;

			// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
			// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
			// FLUXNET2015 release
			//dataset->gf_rows[LE_INDEX][current_row].quality = INVALID_VALUE;
			//dataset->gf_rows[H_INDEX][current_row].quality = INVALID_VALUE;
		}
	} else if ( SECOND == dataset->rows[current_row].ecbcf_method ) {
		window = (windows_size_alt / 2) * rows_per_day;
		j = 5; /* -1h +1h */
		if ( dataset->hourly ) {
			j = 3;
		}

		/*
			compute start window

			please note: a window start at e.g.: -48 and fixed to 0 is an error
			'cause 0 is a different midhour...	
		*/
		window_start = current_row - window - 2; /* -2 = -1h */
		if ( dataset->hourly ) {
			++window_start;
		}

		/*
			compute end window

			please note: a window end at e.g.: 17616 and fixed to rows_count is an error
			'cause rows_count is a different midhour...	
		*/
		window_end = current_row + window;

		/* loop on window for LE */
		for ( window_current = window_start; window_current < window_end; window_current += rows_per_day ) {
			for ( i = 0; i < j; i++ ) {		
				if ( (window_current+i >= 0) && (window_current+i < dataset->rows_count) ) {
					if ( !IS_INVALID_VALUE(dataset->rows[window_current+i].value[LEcorr]) && (FIRST == dataset->rows[window_current+i].ecbcf_method) ) {
						ECBcf = dataset->rows[window_current+i].value[LEcorr] / dataset->rows[window_current+i].value[LE];
						if ( IS_VALID_VALUE(ECBcf) ) {
							ECBcfs[n++] = ECBcf;
						}
					}
				}
			}
		}

		/* */
		if ( n ) {
			ECBcf = 0.0;
			for ( i = 0; i < n; i++ ) {
				ECBcf += ECBcfs[i];
			}

			ECBcf /= n;
			dataset->rows[current_row].ecbcf_samples_count = n;
			dataset->rows[current_row].value[LEcorr] = INVALID_VALUE;
			if ( !IS_INVALID_VALUE(dataset->rows[current_row].value[LE]) ) {
				dataset->rows[current_row].value[LEcorr] = ECBcf * dataset->rows[current_row].value[LE];
			}

			/* loop on window for H */
			n = 0;
			for ( window_current = window_start; window_current < window_end; window_current += rows_per_day ) {
				for ( i = 0; i < j; i++ ) {		
					if ( (window_current+i >= 0) && (window_current+i < dataset->rows_count) ) {
						if ( !IS_INVALID_VALUE(dataset->rows[window_current+i].value[Hcorr]) && (FIRST == dataset->rows[window_current+i].ecbcf_method) ) {
							ECBcf = dataset->rows[window_current+i].value[Hcorr] / dataset->rows[window_current+i].value[H];
							if ( IS_VALID_VALUE(ECBcf) ) {
								ECBcfs[n++] = ECBcf;
							}
						}
					}
				}
			}

			/* */
			ECBcf = 0.0;
			for ( i = 0; i < n; i++ ) {
				ECBcf += ECBcfs[i];
			}

			ECBcf /= n;
			/* dataset->rows[current_row].samples_count[ECBCF_INDEX] = n; */
			dataset->rows[current_row].value[Hcorr] = INVALID_VALUE;
			if ( !IS_INVALID_VALUE(dataset->rows[current_row].value[H]) ) {
				dataset->rows[current_row].value[Hcorr] = ECBcf * dataset->rows[current_row].value[H];
			}
		} else {
			dataset->rows[current_row].ecbcf_method = THIRD;
		}
	} else {
		/* compute window */
		window = rows_per_day;
		window *= window_size / 2;

		/*
			compute start window

			please note: a window start at e.g.: -48 and fixed to 0 is an error
			'cause 0 is a different midhour...	
		*/
		window_start = current_row - window - 1; /* -1 = -1 midhour */
		if ( dataset->hourly ) {
			++window_start;
		}

		/*
			compute end window

			please note: a window end at e.g.: 17616 and fixed to rows_count is an error
			'cause rows_count is a different midhour...	
		*/
		window_end = current_row + window;

		/* loop on window */
		hh = 0;
		mm = 0;
		for ( window_current = window_start; window_current < window_end; window_current++ ) {
			if ( (window_current >= 0) && (window_current < dataset->rows_count) ) {
				get_hhmm_from_row(window_current, &hh, &mm, dataset->hourly);
				if (	! IS_INVALID_VALUE(ECBcfs_temp[window_current])
						&& (((hh >= 22) || (hh <= 2)) || ((hh >= 10) && (hh <= 14))) ) {
					ECBcfs[n++] = ECBcfs_temp[window_current];
				}
			}
		}

		/* */
		if ( n >= 5 ) {
			int var;
			int index;

			for ( var = 0; var < n; var++ ) {
				temp[var] = ECBcfs[var];
				if ( ! IS_INVALID_VALUE(dataset->rows[current_row].value[LE]) ) {
					temp[var] *= dataset->rows[current_row].value[LE];				 
				}
			}

			/* */
			qsort(temp, n, sizeof *temp, compare_prec);

			/* 50 % LE */
			index = ROUND((50 / 100.0) * n + 0.5);
			--index;
			if ( index >= n ) {
				dataset->rows[current_row].value[LEcorr] = temp[n-1];
			} else {
				dataset->rows[current_row].value[LEcorr] = temp[index];
			}

			/* 25 % LE */
			index = ROUND((25 / 100.0) * n + 0.5);
			--index;
			if ( index >= n ) {
				dataset->rows[current_row].value[LEcorr25] = temp[n-1];
			} else {
				dataset->rows[current_row].value[LEcorr25] = temp[index];
			}

			/* 75 % LE */
			index = ROUND((75 / 100.0) * n + 0.5);
			--index;
			if ( index >= n ) {
				dataset->rows[current_row].value[LEcorr75] = temp[n-1];
			} else {
				dataset->rows[current_row].value[LEcorr75] = temp[index];
			}

			for ( var = 0; var < n; var++ ) {
				temp[var] = ECBcfs[var];
				if ( !IS_INVALID_VALUE(dataset->rows[current_row].value[H]) ) {
					temp[var] *= dataset->rows[current_row].value[H];
				}
			}

			/* */
			qsort(temp, n, sizeof *temp, compare_prec);

			/* 50 % H */
			index = ROUND((50 / 100.0) * n + 0.5);
			--index;
			if ( index >= n ) {
				dataset->rows[current_row].value[Hcorr] = temp[n-1];
			} else {
				dataset->rows[current_row].value[Hcorr] = temp[index];
			}

			/* 25 % H */
			index = ROUND((25 / 100.0) * n + 0.5);
			--index;
			if ( index >= n ) {
				dataset->rows[current_row].value[Hcorr25] = temp[n-1];
			} else {
				dataset->rows[current_row].value[Hcorr25] = temp[index];
			}

			/* 75 % H */
			index = ROUND((75 / 100.0) * n + 0.5);
			--index;
			if ( index >= n ) {
				dataset->rows[current_row].value[Hcorr75] = temp[n-1];
			} else {
				dataset->rows[current_row].value[Hcorr75] = temp[index];
			}

			dataset->rows[current_row].ecbcf_samples_count = n;
		} else {
			dataset->rows[current_row].ecbcf_method = SECOND;
		}
	}

	/* ok */
	return 1;
}

/* */
int ecbcf_dd(DATASET *const dataset, const int current_row, PREC *const ECBcfs, PREC *const ECBcfs_temp, PREC *const temp, const int window_size, const int windows_size_alt) {
	int i;
	int j;
	int n;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int rows_per_day;
	int years;
	int error;
	PREC ECBcf;

	/* check parameter */
	assert(dataset && ECBcfs);

	/* rows per day */
	rows_per_day = dataset->hourly ? 24: 48;

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	ECBcf = 0.0;
	n = 0;

	/* */
	if ( THIRD == dataset->rows_aggr[current_row].ecbcf_method ) {
		if ( dataset->years_count > 1 ) {
			int index;
			int before;
			int after;
			int ok;
			int m;

			/* compute window size */
			window = windows_size_alt / 2;

			/* */
			m = 1;
			ok = 0;
			do {
				for ( years = 1; years < 3; years++ ) {
					/* get index of dataset */
					j = 0;
					index = -1;
					for ( i = 0; i < dataset->years_count; i++ ) {
						j += ((IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / rows_per_day);
						if ( current_row < j ) {
							index = i;
							break;
						}
					}
					assert(index != -1);

					/* */
					before = index - years;
					after = index + years;
					if ( after >= dataset->years_count ) {
						after = -1;
					}

					/* */
					window *= m;

					/* */
					if ( before >= 0 ) {
						i = current_row - ((IS_LEAP_YEAR(dataset->years[before].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / rows_per_day);
						if ( years > 1 ) {
							i -= (((IS_LEAP_YEAR(dataset->years[before+1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS)) / rows_per_day);
						}
						window_start = i - window;
						if ( window_start < 0 ) {
							window_start = 0;
						}
						window_end = i + window;
						if ( window_end >= dataset->rows_aggr_count ) {
							window_end = dataset->rows_aggr_count - 1;
						}

						/* loop on window for LE */
						for ( window_current = window_start; window_current <= window_end; window_current++ ) {
							if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[LEcorr]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
								ECBcf = dataset->rows_aggr[window_current].value[LEcorr] / dataset->rows_aggr[window_current].le_mean;
								if ( IS_VALID_VALUE(ECBcf) ) {
									ECBcfs[n++] = ECBcf;
								}
							}
						}
					}

					if ( after > 0 ) {
						i = current_row + ((IS_LEAP_YEAR(dataset->years[after-1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / rows_per_day);
						if ( years > 1 ) {
							i += (((IS_LEAP_YEAR(dataset->years[after].year) ? LEAP_YEAR_ROWS : YEAR_ROWS)) / rows_per_day);
						}
						window_start = i - window;
						if ( window_start < 0 ) {
							window_start = 0;
						}
						window_end = i + window;
						if ( window_end >= dataset->rows_aggr_count ) {
							window_end = dataset->rows_aggr_count - 1;
						}

						/* loop on window for LE */
						for ( window_current = window_start; window_current <= window_end; window_current++ ) {
							if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[LEcorr]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
								ECBcf = dataset->rows_aggr[window_current].value[LEcorr] / dataset->rows_aggr[window_current].le_mean;
								if ( IS_VALID_VALUE(ECBcf) ) {
									ECBcfs[n++] = ECBcf;
								}
							}
						}
					}

					/* */
					if ( n ) {
						ECBcf = 0.0;
						for ( i = 0; i < n; i++ ) {
							ECBcf += ECBcfs[i];
						}

						ECBcf /= n;
						dataset->rows_aggr[current_row].ecbcf_samples_count = n;
						dataset->rows_aggr[current_row].value[LEcorr] = INVALID_VALUE;
						if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
							dataset->rows_aggr[current_row].value[LEcorr] = ECBcf * dataset->rows_aggr[current_row].le_mean;
						}

						/* loop on window for H */
						n = 0;

						/* */
						if ( before >=0 ) {
							i = current_row - ((IS_LEAP_YEAR(dataset->years[before].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / rows_per_day);
							if ( years > 1 ) {
								i -= (((IS_LEAP_YEAR(dataset->years[before+1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS)) / rows_per_day);
							}
							window_start = i - window;
							if ( window_start < 0 ) {
								window_start = 0;
							}
							window_end = i + window;
							if ( window_end >= dataset->rows_aggr_count ) {
								window_end = dataset->rows_aggr_count - 1;
							}

							/* loop on window for H */
							for ( window_current = window_start; window_current <= window_end; window_current++ ) {
								if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[Hcorr]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
									ECBcf = dataset->rows_aggr[window_current].value[Hcorr] / dataset->rows_aggr[window_current].h_mean;
									if ( IS_VALID_VALUE(ECBcf) ) {
										ECBcfs[n++] = ECBcf;
									}
								}
							}
						}

						if ( after > 0 ) {
							i = current_row + ((IS_LEAP_YEAR(dataset->years[after-1].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / rows_per_day);
							if ( years > 1 ) {
								i += (((IS_LEAP_YEAR(dataset->years[after].year) ? LEAP_YEAR_ROWS : YEAR_ROWS)) / rows_per_day);
							}
							window_start = i - window;
							if ( window_start < 0 ) {
								window_start = 0;
							}
							window_end = i + window;
							if ( window_end >= dataset->rows_aggr_count ) {
								window_end = dataset->rows_aggr_count - 1;
							}

							/* loop on window for H */
							for ( window_current = window_start; window_current <= window_end; window_current++ ) {
								if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[Hcorr]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
									ECBcf = dataset->rows_aggr[window_current].value[Hcorr] / dataset->rows_aggr[window_current].h_mean;
									if ( IS_VALID_VALUE(ECBcf) ) {
										ECBcfs[n++] = ECBcf;
									}
								}
							}
						}

						ECBcf = 0.0;
						for ( i = 0; i < n; i++ ) {
							ECBcf += ECBcfs[i];
						}

						ECBcf /= n;
						dataset->rows_aggr[current_row].value[Hcorr] = INVALID_VALUE;
						if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
							dataset->rows_aggr[current_row].value[Hcorr] = ECBcf * dataset->rows_aggr[current_row].h_mean;
						}
						
						/* update flag */
						ok = 1;
						break;
					} 
				}

				/* */
				if ( ok ) {
					break;
				}

				/* */
				++m;
			} while ( m < 3 );

			/* */
			if ( !ok ) {
				/* no method */
				dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
				dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

				// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
				// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
				// FLUXNET2015 release
				//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
				//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
			}
		} else {
			/* no method */
			dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
			dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

			// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
			// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
			// FLUXNET2015 release
			//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
			//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
		}
	} else if ( SECOND == dataset->rows_aggr[current_row].ecbcf_method ) {
		window = windows_size_alt / 2;

		/* compute start window */
		window_start = current_row - window;
		if ( window_start < 0 ) {
			window_start = 0;
		}

		/* compute end window */
		window_end = current_row + window;
		if ( window_end >= dataset->rows_aggr_count ) {
			window_end = dataset->rows_aggr_count - 1;
		}

		/* loop on window for LE */
		for ( window_current = window_start; window_current <= window_end; window_current++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[LEcorr]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
				ECBcf = dataset->rows_aggr[window_current].value[LEcorr] / dataset->rows_aggr[window_current].le_mean;
				if ( IS_VALID_VALUE(ECBcf) ) {
					ECBcfs[n++] = ECBcf;
				}
			}
		}

		/* */
		if ( n ) {
			ECBcf = 0.0;
			for ( i = 0; i < n; i++ ) {
				ECBcf += ECBcfs[i];
			}

			ECBcf /= n;
			dataset->rows_aggr[current_row].ecbcf_samples_count = n;
			dataset->rows_aggr[current_row].value[LEcorr] = INVALID_VALUE;

			if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
				dataset->rows_aggr[current_row].value[LEcorr] = ECBcf * dataset->rows_aggr[current_row].le_mean;
			}

			/* loop on window for H */
			n = 0;
			for ( window_current = window_start; window_current <= window_end; window_current++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[Hcorr]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
					ECBcf = dataset->rows_aggr[window_current].value[Hcorr] / dataset->rows_aggr[window_current].h_mean;
					if ( IS_VALID_VALUE(ECBcf) ) {
						ECBcfs[n++] = ECBcf;
					}
				}
			}

			ECBcf = 0.0;
			for ( i = 0; i < n; i++ ) {
				ECBcf += ECBcfs[i];
			}
			ECBcf /= n;

			dataset->rows_aggr[current_row].value[Hcorr] = INVALID_VALUE;
			if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
				dataset->rows_aggr[current_row].value[Hcorr] = ECBcf * dataset->rows_aggr[current_row].h_mean;
			}
		} else {
			dataset->rows_aggr[current_row].ecbcf_method = THIRD;
		}
	} else {
		/* compute window */
		window = window_size / 2;

		/* compute start window */
		window_start = current_row - window;
		if ( window_start < 0 ) {
			window_start = 0;
		}

		/* compute end window */
		window_end = current_row + window;
		if ( window_end >= dataset->rows_aggr_count ) {
			window_end = dataset->rows_aggr_count - 1;
		}

		/* loop on window */
		for ( window_current = window_start; window_current <= window_end; window_current++ ) {
			if ( !IS_INVALID_VALUE(ECBcfs_temp[window_current]) ) {
				ECBcfs[n++] = ECBcfs_temp[window_current];
			}
		}

		/* */
		if ( n >= 5 ) {
			int var;

			for ( var = 0; var < n; var++ ) {
				temp[var] = ECBcfs[var];
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
					temp[var] *= dataset->rows_aggr[current_row].le_mean;				 
				}
			}

			/* 50% LE */
			dataset->rows_aggr[current_row].value[LEcorr] = get_percentile_from_all_valids(temp, n, 50, &error);
			if  ( error ) {
				puts("unable to get 50% percentile.");
				return 0;
			}

			/* 25% LE */
			dataset->rows_aggr[current_row].value[LEcorr25] = get_percentile_from_all_valids(temp, n, 25, &error);
			if  ( error ) {
				puts("unable to get 25% percentile.");
				return 0;
			}

			/* 75% LE */
			dataset->rows_aggr[current_row].value[LEcorr75] = get_percentile_from_all_valids(temp, n, 75, &error);
			if  ( error ) {
				puts("unable to get 75% percentile.");
				return 0;
			}

			/* */
			for ( var = 0; var < n; var++ ) {
				temp[var] = ECBcfs[var];
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
					temp[var] *= dataset->rows_aggr[current_row].h_mean;
				}
			}

			/* 50% H */
			dataset->rows_aggr[current_row].value[Hcorr] = get_percentile_from_all_valids(temp, n, 50, &error);
			if  ( error ) {
				puts("unable to get 50% percentile.");
				return 0;
			}

			/* 25% H */
			dataset->rows_aggr[current_row].value[Hcorr25] = get_percentile_from_all_valids(temp, n, 25, &error);
			if  ( error ) {
				puts("unable to get 25% percentile.");
				return 0;
			}

			/* 75% H */
			dataset->rows_aggr[current_row].value[Hcorr75] = get_percentile_from_all_valids(temp, n, 75, &error);
			if  ( error ) {
				puts("unable to get 75% percentile.");
				return 0;
			}

			/* */
			dataset->rows_aggr[current_row].ecbcf_samples_count = n;
		} else {
			dataset->rows_aggr[current_row].ecbcf_method = SECOND;
		}
	}

	/* ok */
	return 1;
}

/* PLEASE NOTE THAT METHOD 1 IS COMPUTED IN aggr_by_weeks */
int ecbcf_ww(DATASET *const dataset, const int current_row, PREC *const ECBcfs, const int window_size) {
	int i;
	int j;
	int n;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int years;
	PREC ECBcf;

	/* check parameter */
	assert(dataset && ECBcfs);

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	ECBcf = 0.0;
	n = 0;

	/* */
	if ( THIRD == dataset->rows_aggr[current_row].ecbcf_method ) {
		if ( dataset->years_count > 1 ) {
			int index;
			int before;
			int after;
			int ok;
			int m;

			/* compute window size */
			window = window_size / 2;

			/* */
			m = 1;
			ok = 0;
			do {
				for ( years = 1; years < 3; years++ ) {
					/* get index of dataset */
					j = 0;
					index = -1;
					for ( i = 0; i < dataset->years_count; i++ ) {
						j += 52;
						if ( current_row < j ) {
							index = i;
							break;
						}
					}
					assert(index != -1);

					/* */
					before = index - years;
					after = index + years;
					if ( after >= dataset->years_count ) {
						after = -1;
					}

					/* */
					window *= m;

					/* */
					if ( before >= 0 ) {
						i = current_row - (52 * years);
						window_start = i - window;
						if ( window_start < 0 ) {
							window_start = 0;
						}
						window_end = i + window;
						if ( window_end >= dataset->rows_aggr_count ) {
							window_end = dataset->rows_aggr_count - 1;
						}


						/* loop on window */
						for ( window_current = window_start; window_current <= window_end; window_current++ ) {
							if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[p50]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
								ECBcfs[n++] = dataset->rows_aggr[window_current].value[p50];
							}
						}
					}

					if ( after >= 0 ) {
						i = current_row + (52 * years);
						window_start = i - window;
						if ( window_start < 0 ) {
							window_start = 0;
						}
						window_end = i + window;
						if ( window_end >= dataset->rows_aggr_count ) {
							window_end = dataset->rows_aggr_count - 1;
						}

						/* loop on window */
						for ( window_current = window_start; window_current <= window_end; window_current++ ) {
							if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[p50]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
								ECBcfs[n++] = dataset->rows_aggr[window_current].value[p50];
							}
						}
					}

					/* */
					if ( n ) {
						ECBcf = 0.0;
						for ( i = 0; i < n; i++ ) {
							ECBcf += ECBcfs[i];
						}

						ECBcf /= n;
						dataset->rows_aggr[current_row].ecbcf_samples_count = n;
						dataset->rows_aggr[current_row].value[p50] = ECBcf;

						if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
							dataset->rows_aggr[current_row].value[LEcorr] = dataset->rows_aggr[current_row].le_mean * dataset->rows_aggr[current_row].value[p50];
						}

						if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
							dataset->rows_aggr[current_row].value[Hcorr] = dataset->rows_aggr[current_row].h_mean * dataset->rows_aggr[current_row].value[p50];
						}

						/* update flag */
						ok = 1;
						break;
					} 
				}

				/* */
				if ( ok ) {
					break;
				}

				/* */
				++m;
			} while ( m < 3 );

			/* */
			if ( !ok ) {
				/* no method */
				dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
				dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

				// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
				// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
				// FLUXNET2015 release
				//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
				//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
			}
		} else {
			/* no method */
			dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
			dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

			// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
			// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
			// FLUXNET2015 release
			//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
			//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
		}
	} else if ( SECOND == dataset->rows_aggr[current_row].ecbcf_method ) {
		window = window_size / 2;

		/* compute start window */
		window_start = current_row - window;
		if ( window_start < 0 ) {
			window_start = 0;
		}

		/* compute end window */
		window_end = current_row + window;
		if ( window_end >= dataset->rows_aggr_count ) {
			window_end = dataset->rows_aggr_count - 1;
		}

		/* loop on window */
		for ( window_current = window_start; window_current <= window_end; window_current++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[p50]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
				ECBcfs[n++] = dataset->rows_aggr[window_current].value[p50];
			}
		}

		/* */
		if ( n ) {
			ECBcf = 0.0;
			for ( i = 0; i < n; i++ ) {
				ECBcf += ECBcfs[i];
			}

			ECBcf /= n;
			dataset->rows_aggr[current_row].ecbcf_samples_count = n;
			dataset->rows_aggr[current_row].value[p50] = ECBcf;

			if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
				dataset->rows_aggr[current_row].value[LEcorr] = dataset->rows_aggr[current_row].le_mean * dataset->rows_aggr[current_row].value[p50];
			}

			if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
				dataset->rows_aggr[current_row].value[Hcorr] = dataset->rows_aggr[current_row].h_mean * dataset->rows_aggr[current_row].value[p50];
			}
		} else {
			dataset->rows_aggr[current_row].ecbcf_method = THIRD;
		}
	}

	/* ok */
	return 1;
}

/* PLEASE NOTE THAT METHOD 1 IS COMPUTED IN aggr_by_months */
int ecbcf_mm(DATASET *const dataset, const int current_row, PREC *const ECBcfs, const int window_size) {
	int i;
	int j;
	int n;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int years;
	PREC ECBcf;

	/* check parameter */
	assert(dataset && ECBcfs);

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	ECBcf = 0.0;
	n = 0;

	/* */
	if ( THIRD == dataset->rows_aggr[current_row].ecbcf_method ) {
		if ( dataset->years_count > 1 ) {
			int index;
			int before;
			int after;
			int ok;
			int m;

			/* compute window size */
			window = window_size / 2;

			/* */
			m = 1;
			ok = 0;
			do {
				for ( years = 1; years < 3; years++ ) {
					/* get index of dataset */
					j = 0;
					index = -1;
					for ( i = 0; i < dataset->years_count; i++ ) {
						j += 52;
						if ( current_row < j ) {
							index = i;
							break;
						}
					}
					assert(index != -1);

					/* */
					before = index - years;
					after = index + years;
					if ( after >= dataset->years_count ) {
						after = -1;
					}

					/* */
					window *= m;

					/* */
					if ( before >= 0 ) {
						i = current_row - (12 * years);
						window_start = i - window;
						if ( window_start < 0 ) {
							window_start = 0;
						}
						window_end = i + window;
						if ( window_end >= dataset->rows_aggr_count ) {
							window_end = dataset->rows_aggr_count - 1;
						}

						/* loop on window */
						for ( window_current = window_start; window_current <= window_end; window_current++ ) {
							if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[p50]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
								ECBcfs[n++] = dataset->rows_aggr[window_current].value[p50];
							}
						}
					}

					if ( after >= 0 ) {
						i = current_row + (12 * years);
						window_start = i - window;
						if ( window_start < 0 ) {
							window_start = 0;
						}
						window_end = i + window;
						if ( window_end >= dataset->rows_aggr_count ) {
							window_end = dataset->rows_aggr_count - 1;
						}

						/* loop on window */
						for ( window_current = window_start; window_current <= window_end; window_current++ ) {
							if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[p50]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
								ECBcfs[n++] = dataset->rows_aggr[window_current].value[p50];
							}
						}
					}

					/* */
					if ( n ) {
						ECBcf = 0.0;
						for ( i = 0; i < n; i++ ) {
							ECBcf += ECBcfs[i];
						}

						ECBcf /= n;
						dataset->rows_aggr[current_row].ecbcf_samples_count = n;
						dataset->rows_aggr[current_row].value[p50] = ECBcf;

						if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
							dataset->rows_aggr[current_row].value[LEcorr] = dataset->rows_aggr[current_row].le_mean * dataset->rows_aggr[current_row].value[p50];
						}

						if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
							dataset->rows_aggr[current_row].value[Hcorr] = dataset->rows_aggr[current_row].h_mean * dataset->rows_aggr[current_row].value[p50];
						}

						/* update flag */
						ok = 1;
						break;
					} 
				}

				/* */
				if ( ok ) {
					break;
				}

				/* */
				++m;
			} while ( m < 3 );

			/* */
			if ( !ok ) {
				/* no method */
				dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
				dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

				// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
				// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
				// FLUXNET2015 release
				//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
				//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
			}
		} else {
			/* no method */
			dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
			dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

			// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
			// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
			// FLUXNET2015 release
			//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
			//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
		}
	} else if ( SECOND == dataset->rows_aggr[current_row].ecbcf_method ) {
		window = window_size / 2;

		/* compute start window */
		window_start = current_row - window;
		if ( window_start < 0 ) {
			window_start = 0;
		}

		/* compute end window */
		window_end = current_row + window;
		if ( window_end >= dataset->rows_aggr_count ) {
			window_end = dataset->rows_aggr_count - 1;
		}

		/* loop on window */
		for ( window_current = window_start; window_current <= window_end; window_current++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows_aggr[window_current].value[p50]) && (FIRST == dataset->rows_aggr[window_current].ecbcf_method) ) {
				ECBcfs[n++] = dataset->rows_aggr[window_current].value[p50];
			}
		}

		/* */
		if ( n ) {
			ECBcf = 0.0;
			for ( i = 0; i < n; i++ ) {
				ECBcf += ECBcfs[i];
			}

			ECBcf /= n;
			dataset->rows_aggr[current_row].ecbcf_samples_count = n;
			dataset->rows_aggr[current_row].value[p50] = ECBcf;

			if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
				dataset->rows_aggr[current_row].value[LEcorr] = dataset->rows_aggr[current_row].le_mean * dataset->rows_aggr[current_row].value[p50];
			}

			if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
				dataset->rows_aggr[current_row].value[Hcorr] = dataset->rows_aggr[current_row].h_mean * dataset->rows_aggr[current_row].value[p50];
			}
		} else {
			dataset->rows_aggr[current_row].ecbcf_method = THIRD;
		}
	}

	/* ok */
	return 1;
}

/* PLEASE NOTE THAT METHOD 1 IS COMPUTED IN aggr_by_years */
int ecbcf_yy(DATASET *const dataset, const int current_row, PREC *const ECBcfs) {
	int i;
	int n;
	PREC ECBcf;

	/* check parameter */
	assert(dataset && ECBcfs);

	/* reset */
	ECBcf = 0.0;
	n = 0;

	/* */
	if ( THIRD == dataset->rows_aggr[current_row].ecbcf_method ) {
		/* how many dataset we have ? */
		if ( dataset->years_count > 2 ) {
			int before;
			int after;

			/* */
			before = current_row - 2;
			if ( before < 0 ) {
				before = -1;
			}
			after = current_row + 2;
			if ( after >= dataset->years_count ) {
				after = -1;
			}

			/* */
			if ( before >= 0 ) {
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[before].value[p50]) && (FIRST == dataset->rows_aggr[before].ecbcf_method) ) {
					ECBcfs[n++] = dataset->rows_aggr[before].value[p50];
				}
			}

			if ( after >= 0 ) {
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[after].value[p50]) && (FIRST == dataset->rows_aggr[after].ecbcf_method) ) {
					ECBcfs[n++] = dataset->rows_aggr[after].value[p50];
				}
			}

			/* */
			if ( n ) {
				ECBcf = 0.0;
				for ( i = 0; i < n; i++ ) {
					ECBcf += ECBcfs[i];
				}

				ECBcf /= n;
				dataset->rows_aggr[current_row].ecbcf_samples_count = n;
				dataset->rows_aggr[current_row].value[p50] = ECBcf;

				if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
					dataset->rows_aggr[current_row].value[LEcorr] = dataset->rows_aggr[current_row].le_mean * dataset->rows_aggr[current_row].value[p50];
				}

				if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
					dataset->rows_aggr[current_row].value[Hcorr] = dataset->rows_aggr[current_row].h_mean * dataset->rows_aggr[current_row].value[p50];
				}
			} else {
				/* no method */
				dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
				dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

				// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
				// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
				// FLUXNET2015 release
				//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
				//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
			}
		} else {
			/* no method */
			dataset->rows_aggr[current_row].ecbcf_method = INVALID_VALUE-1;
			dataset->rows_aggr[current_row].ecbcf_samples_count = INVALID_VALUE;

			// commented out on July 25, 2019. It was a bug, changing the value of the QC to -9999 when it was 
			// not possible to calculate the energy balance and create the LE_Corr. It is also a "known issue" in 
			// FLUXNET2015 release
			//dataset->rows_aggr[current_row].quality[LE_INDEX] = INVALID_VALUE;
			//dataset->rows_aggr[current_row].quality[H_INDEX] = INVALID_VALUE;
		}
	} else if ( SECOND == dataset->rows_aggr[current_row].ecbcf_method ) {
		/* how many dataset we have ? */
		if ( dataset->years_count > 1 ) {
			int before;
			int after;

			/* */
			before = current_row - 1;
			if ( before < 0 ) {
				before = -1;
			}
			after = current_row + 1;
			if ( after >= dataset->years_count ) {
				after = -1;
			}

			/* */
			if ( before >= 0 ) {
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[before].value[p50]) && (FIRST == dataset->rows_aggr[before].ecbcf_method) ) {
					ECBcfs[n++] = dataset->rows_aggr[before].value[p50];
				}
			}

			if ( after >= 0 ) {
				if ( !IS_INVALID_VALUE(dataset->rows_aggr[after].value[p50]) && (FIRST == dataset->rows_aggr[after].ecbcf_method) ) {
					ECBcfs[n++] = dataset->rows_aggr[after].value[p50];
				}
			}

			/* */
			if ( n ) {
				ECBcf = 0.0;
				for ( i = 0; i < n; i++ ) {
					ECBcf += ECBcfs[i];
				}

				ECBcf /= n;
				dataset->rows_aggr[current_row].ecbcf_samples_count = n;
				dataset->rows_aggr[current_row].value[p50] = ECBcf;

				if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].le_mean) ) {
					dataset->rows_aggr[current_row].value[LEcorr] = dataset->rows_aggr[current_row].le_mean * dataset->rows_aggr[current_row].value[p50];
				}

				if ( !IS_INVALID_VALUE(dataset->rows_aggr[current_row].h_mean) ) {
					dataset->rows_aggr[current_row].value[Hcorr] = dataset->rows_aggr[current_row].h_mean * dataset->rows_aggr[current_row].value[p50];
				}
			} else {
				dataset->rows_aggr[current_row].ecbcf_method = THIRD;
			}
		} else {
			dataset->rows_aggr[current_row].ecbcf_method = THIRD;
		}
	}
	
	/* ok */
	return 1;
}
