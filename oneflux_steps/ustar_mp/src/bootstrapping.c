/*
	bootstrapping.c

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include "bootstrapping.h"
#include "ustar.h"

/* extern variables */
extern int year;
extern int leap_year;
extern int ta_classes_count;
extern int seasons_group_count;
extern const int percentiles[];
extern int *samples_per_season;
extern int *seasons_end_index;
extern char buffer[BUFFER_SIZE];
extern char *site;
extern PREC *ustar_mean;
extern PREC *fx_mean;
extern WINDOW *ta_window;
extern WINDOW *ustar_window;
extern int no_forward_mode;
extern int no_forward_mode_2;
extern int no_forward_mode_3;
extern int no_back_mode;
extern int no_back_mode_2;
extern int no_back_mode_3;

/* strings */
static const char *ustar_threshold_modes[6] = {
	"forward mode",
	"forward mode 2",
	"forward mode 3",
	"back mode",
	"back mode 2",
	"back mode 3"
};

/* errors strings */
static const char err_invalid_percentile_index[] = "invalid percentile index!\n";

/* extern strings */
extern const char err_out_of_memory[];
extern const char err_unable_to_create_results_file[];

/* */
static int compare_row(const void * a, const void * b) {
	if ( ((ROW *)a)->index < ((ROW *)b)->index ) {
		return -1;
	} else if ( ((ROW *)a)->index > ((ROW *)b)->index ) {
		return 1;
	} else {
		return 0;
	}
}

/* todo : add check for null arguments */
int bootstrapping(	FILE *const f,
					const ROW_FULL_DETAILS *const rows,
					const int rows_count,
					const int bootstrapping_count,
					PREC *const threshold_forward_mode_container,
					PREC *const threshold_forward_mode_2_container,
					PREC *const threshold_forward_mode_3_container,
					PREC *const threshold_back_mode_container,
					PREC *const threshold_back_mode_2_container,
					PREC *const threshold_back_mode_3_container,
					PREC *const threshold_high_forward_mode_container,
					PREC *const threshold_high_forward_mode_2_container,
					PREC *const threshold_high_forward_mode_3_container,
					PREC *const threshold_high_back_mode_container,
					PREC *const threshold_high_back_mode_2_container,
					PREC *const threshold_high_back_mode_3_container,
					PREC *const threshold_valid_forward_mode_container,
					PREC *const threshold_valid_forward_mode_2_container,
					PREC *const threshold_valid_forward_mode_3_container,
					PREC *const threshold_valid_back_mode_container,
					PREC *const threshold_valid_back_mode_2_container,
					PREC *const threshold_valid_back_mode_3_container) {
	int i;
	int b;
	int z;
	int index;
	int mode;
	int rows_boot_count;
	int days_boot;
	int row_random;
	int error;
	int valid_count[6];
	PREC median;
	PREC ustar_taken;
	PREC percentile;
	ROW *rows_boot;
	PREC *modes[6];
	PREC *high_modes[6];
	PREC *valid_modes[6];
	int enabled[6];

	/* check modes enabled */
	enabled[0] = !no_forward_mode;
	enabled[1] = !no_forward_mode_2;
	enabled[2] = !no_forward_mode_3;
	enabled[3] = !no_back_mode;
	enabled[4] = !no_back_mode_2;
	enabled[5] = !no_back_mode_3;
	
	/* set pointers */
	modes[0] = threshold_forward_mode_container;
	modes[1] = threshold_forward_mode_2_container;
	modes[2] = threshold_forward_mode_3_container;
	modes[3] = threshold_back_mode_container;
	modes[4] = threshold_back_mode_2_container;
	modes[5] = threshold_back_mode_3_container;

	high_modes[0] = threshold_high_forward_mode_container;
	high_modes[1] = threshold_high_forward_mode_2_container;
	high_modes[2] = threshold_high_forward_mode_3_container;
	high_modes[3] = threshold_high_back_mode_container;
	high_modes[4] = threshold_high_back_mode_2_container;
	high_modes[5] = threshold_high_back_mode_3_container;

	valid_modes[0] = threshold_valid_forward_mode_container;
	valid_modes[1] = threshold_valid_forward_mode_2_container;
	valid_modes[2] = threshold_valid_forward_mode_3_container;
	valid_modes[3] = threshold_valid_back_mode_container;
	valid_modes[4] = threshold_valid_back_mode_2_container;
	valid_modes[5] = threshold_valid_back_mode_3_container;
	
	/* alloc memory */
	rows_boot = malloc(rows_count*sizeof(ROW));
	if ( !rows_boot ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop for bootstrapping */
	for ( b = 0; b < bootstrapping_count; b++ ) {
		/* reset */
		rows_boot_count = 0;
		days_boot = 0;

		/* reset season */
		for ( i = 0; i < seasons_group_count; i++ ) {
			samples_per_season[i] = 0;
		}

		/* create random dataset */
		i = 0;
		while ( i < rows_count ) {
			/* get random number */
			row_random = get_random_number(rows_count);

			/* is day ? */
			if ( IS_INVALID_VALUE(rows[row_random].night) ) {
				/* inc days */
				++days_boot;
			} else if ( IS_FLAG_SET(rows[row_random].flags, ALL_VALID) ) {
				rows_boot[rows_boot_count].value[NEE] = rows[row_random].value[NEE];
				rows_boot[rows_boot_count].value[TA] = rows[row_random].value[TA];
				rows_boot[rows_boot_count].value[USTAR] = rows[row_random].value[USTAR];
				rows_boot[rows_boot_count].index = row_random;

				/* compute samples per season */
				index = 0;
				for ( z = 0; z < seasons_group_count; z++ ) {
					if ( row_random < seasons_end_index[z] ) {
						index = z;
						break;
					}
				}
				++samples_per_season[index];
				++rows_boot_count;
			}

			/* next row */
			++i;
		}

		/* if night and valid values founded, compute ustar threshold */
		if ( rows_boot_count ) {
			/* sort rows */
			qsort(rows_boot, rows_boot_count, sizeof(ROW), compare_row);

			/* get ustar thresholds */
			if ( !ustar_threshold(rows_boot, rows_boot_count, days_boot,
								NULL, NULL, NULL, NULL, NULL, NULL,
								threshold_forward_mode_container, threshold_forward_mode_2_container, threshold_forward_mode_3_container,
								threshold_back_mode_container, threshold_back_mode_2_container, threshold_back_mode_3_container,
								ustar_mean, fx_mean, ta_window, ustar_window) ) {
				free(rows_boot);
				return 0;
			}

			/* write results */
			for ( mode = 0 ; mode < 6; mode++ ) {
				if ( enabled[mode] ) {
					for ( i = 0; i < seasons_group_count; i++ ) {
						median = median_ustar_threshold(modes[mode], ta_classes_count, i, &error);
						if ( error ) {
							puts(err_out_of_memory);
							return 0;
						}
						fprintf(f, "%*g", TABSPACE, median);

						if ( 0 == i ) {
							ustar_taken = median;
						} else if ( median > ustar_taken ) {
							ustar_taken = median;
						}
					}
					fprintf(f, " %s\n", ustar_threshold_modes[mode]);
					/* put selected values */
					high_modes[mode][b] = ustar_taken;
				}
			}
	
			for ( i = 0; i < seasons_group_count; i++ ) {
				fprintf(f, "%*d", TABSPACE, samples_per_season[i]);
			}
			fputs("\n", f);
		} else {
			/* no high values 'cause ustar threshold is not computed */
			high_modes[0][b] = INVALID_VALUE;
			high_modes[1][b] = INVALID_VALUE;
			high_modes[2][b] = INVALID_VALUE;
			high_modes[3][b] = INVALID_VALUE;
			high_modes[4][b] = INVALID_VALUE;
			high_modes[5][b] = INVALID_VALUE;
		}
	}

	/* compute valid thresholds */
	for ( mode = 0; mode < 6; mode++ ) {
		if ( enabled[mode] ) {
			valid_count[mode] = 0;
			for ( b = 0; b < bootstrapping_count; b++ ) {
				if (	!IS_INVALID_VALUE(high_modes[mode][b]) &&
						!ARE_FLOATS_EQUAL(high_modes[mode][b], USTAR_THRESHOLD_NOT_FOUND) ) {
					valid_modes[mode][valid_count[mode]++] = high_modes[mode][b];
				}
			}

			/* sort */
			qsort(valid_modes[mode], valid_count[mode], sizeof(PREC), compare_prec);
		}
	}
	fputs("\n", f);

	/* show valid thresholds */
	for ( mode = 0; mode < 6; mode++ ) {
		if ( enabled[mode] ) {
			fprintf(f, "%*s", TABSPACE, ustar_threshold_modes[mode]); 
		}
	}
	fputs("\n", f);
	for ( i = 0; i < bootstrapping_count; i++ ) {
		for ( mode = 0; mode < 6; mode++ ) {
			if ( enabled[mode] ) {
				if ( i < valid_count[mode] ) {
					fprintf(f, "%*g", TABSPACE, valid_modes[mode][i]);
				} else {
					fprintf(f, "%*g", TABSPACE, (PREC)INVALID_VALUE);
				}
			}
		}
		fputs("\n", f);
	}
	fputs("\n", f);

	/* show percentiles */
	b = PERCENTILES_COUNT / 2; /* for shown 50% */
	for ( mode = 0; mode < 6; mode++ ) {
		if ( enabled[mode] ) {
			fprintf(f, "-- percentiles %s\n", ustar_threshold_modes[mode]);
			if ( valid_count[mode] < PERCENTILES_COUNT ) {
				fprintf(f, "not enough values. percentiles not computed.\n");
			} else {
				for ( i = 0; i < PERCENTILES_COUNT; i++ ) {
					if ( !percentiles[i] ) {
						fprintf(f, err_invalid_percentile_index);
					} else {
						percentile = (PREC)percentiles[i];
						percentile /= 100.0;
						percentile *= valid_count[mode];
						percentile -= 1;
						fprintf(f, "%*g%s\n", TABSPACE, valid_modes[mode][(int)percentile], i == b ? " 50%" : "" );
					}
				}
			}
			fputs("\n", f);
		}
	}

	/* free memory */
	free(rows_boot);

	/* */
	return 1;
}
