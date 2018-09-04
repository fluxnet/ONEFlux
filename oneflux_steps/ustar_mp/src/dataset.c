/*
	dataset.c

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <assert.h>
#include "dataset.h"

/* extern variables */
extern int hourly_dataset;
extern int months_days[];
extern int is_itpSW_IN;
extern int is_itpTA;

/* defines */
#define DTIME_TO_ROW(x)					(int)(((x*48)-48)+0.5)
#define DTIME_TO_ROW_HOURLY(x)			(int)(((x*24)-24)+0.5)

/* strings */
static const char dataset_files_delimiter[] = "+";
extern char dataset_delimiter[];

/* */
static const char msg_processing[] = "processing: %s ->";
static const char Dtime[] = "DTime";
extern const char *input_columns_tokens[INPUT_VALUES];

/* extern errors strings */
extern const char err_out_of_memory[];

/* errors strings */
static const char err_unable_open_dataset[] = "unable to open dataset.";
static const char err_empty_file[] = "empty file ?";
static const char err_redundancy[] = "redundancy: var \"%s\" already founded at column %d\n";
static const char err_unable_find_column[] = "unable to find column for \"%s\" var.\n";
static const char err_conversion[] = "error during conversion of \"%s\" value at row %d, column %d\n";
static const char err_too_many_rows[] = "too many rows.";
static const char err_imported_rows_count[] = "imported rows should be %d, not %d. Timeres specified is \"%s\".\n";
static const char err_imported_rows_count_or[] = "imported rows should be %d or %d, not %d\n";
static const char err_unable_to_import_all_values[] = "unable to import all values for row %d\n";
static const char err_unable_parse_time[] = "error parsing time: \"%s\"\n";
static const char err_token_too_long[] = "path too long for \"%s\".\n";
static const char err_file_redundancy[] = "redundancy for file \"%s\".\n";
static const char err_unable_open_file[] = "unable to open file.";
static const char err_buffer_too_small[] = "buffer too small.";
static const char err_unable_get_header[] = "unable to get header.";

/* */
static int compare_year(const void* a, const void* b) {
	return (((ROW_FULL_DETAILS *)a)->timestamp.YYYY-((ROW_FULL_DETAILS *)b)->timestamp.YYYY);
}

/* */
static int compare_date(const void* a, const void* b) {
	if ( ((ROW_FULL_DETAILS *)a)->timestamp.YYYY < ((ROW_FULL_DETAILS *)b)->timestamp.YYYY ) {
		return -1;
	} else if ( ((ROW_FULL_DETAILS *)a)->timestamp.YYYY > ((ROW_FULL_DETAILS *)b)->timestamp.YYYY ) {
		return 1;
	} else {
		if ( ((ROW_FULL_DETAILS *)a)->timestamp.MM < ((ROW_FULL_DETAILS *)b)->timestamp.MM ) {
		return -1;
		} else if ( ((ROW_FULL_DETAILS *)a)->timestamp.MM > ((ROW_FULL_DETAILS *)b)->timestamp.MM ) {
			return 1;
		} else {
			if ( ((ROW_FULL_DETAILS *)a)->timestamp.DD < ((ROW_FULL_DETAILS *)b)->timestamp.DD ) {
				return -1;
			} else if ( ((ROW_FULL_DETAILS *)a)->timestamp.DD > ((ROW_FULL_DETAILS *)b)->timestamp.DD ) {
				return 1;
			} else {
				/* check if hour is present */
				if  ( IS_INVALID_VALUE(((ROW_FULL_DETAILS *)a)->timestamp.hh) ) {
					return 0;
				}
				/* sort by hour */
				if ( ((ROW_FULL_DETAILS *)a)->timestamp.hh < ((ROW_FULL_DETAILS *)b)->timestamp.hh ) {
					return -1;
				} else if ( ((ROW_FULL_DETAILS *)a)->timestamp.hh > ((ROW_FULL_DETAILS *)b)->timestamp.hh ) {
					return 1;
				} else {
					if ( ((ROW_FULL_DETAILS *)a)->timestamp.mm < ((ROW_FULL_DETAILS *)b)->timestamp.mm ) {
						return -1;
					} else if ( ((ROW_FULL_DETAILS *)a)->timestamp.mm > ((ROW_FULL_DETAILS *)b)->timestamp.mm ) {
						return 1;
					} else {
						return 0;
					}
				}
			}
		}
	}
}

/* */
void free_ut(UT *ut) {
	int i;

	if ( ut ) {
		for ( i = 0; i < ut->details_count; i++ ) {
			free_dd(ut->details[i]);
		}
		free(ut->details);
		if ( ut->rows_full_details ) {
			free(ut->rows_full_details);
		}
		if ( ut->datasets ) {
			free(ut->datasets);
		}
		free(ut);
	}
}

/* */
UT *import_dataset(const LIST *const list, const int list_count) {
	int i;
	int y;
	int j;
	int z;
	int row;
	int assigned;
	int current_row;
	int dataset_rows_count;
	int columns_index[INPUT_VALUES];
	int has_dtime;
	char buffer[BUFFER_SIZE];					/* should be allocated in the heap */
	char buffer2[BUFFER_SIZE];					/* should be allocated in the heap */
	char *token;
	char *p;
	FILE *f;
	ROW_FULL_DETAILS *rows_full_details_no_leak;
	PREC value;
	int error;
	UT *ut;
	DD **details_no_leak;
	TIMESTAMP *t;
	
	/* check parameter */
	if ( ! list ) {
		return NULL;
	}

	/* reset */
	is_itpTA = 0;
	is_itpSW_IN = 0;

	/* alloc memory */
	ut = malloc(sizeof*ut);
	if ( !ut ) {
		puts(err_out_of_memory);
		return 0;
	}
	ut->details = NULL;
	ut->details_count = 0;
	ut->rows_full_details = NULL;
	ut->rows_full_details_count = 0;
	ut->datasets = NULL;
	ut->datasets_count = list_count;
	ut->can_be_grouped = 1;

	/* alloc memory */
	ut->datasets = malloc(ut->datasets_count*sizeof*ut->datasets);
	if ( !ut->datasets ) {
		puts(err_out_of_memory);
		free_ut(ut);
		return NULL;
	}

	/* reset */
	for ( i = 0; i < list_count; ++i ) {
		/* assign */			
		strncpy(ut->datasets[i].name, list[i].fullpath, PATH_SIZE-1);
		ut->datasets[i].name[PATH_SIZE-1] = '\0';
		ut->datasets[i].rows_count = 0;
		ut->datasets[i].flags = 0;
	}

	/* scan for redundancy *
	for ( i = 0; i < ut->datasets_count-1; i++ ) {
		for ( y = i+1; y < ut->datasets_count; y++ ) {
			if ( !string_compare_i(ut->datasets[i].name, ut->datasets[y].name) ) {
				printf(err_file_redundancy, ut->datasets[i].name);
				free_ut(ut);
				return NULL;
			}
		}
	}
	*/

	/* alloc memory */
	z = LEAP_YEAR_ROWS;
	ut->rows_full_details = malloc(z*sizeof*ut->rows_full_details);
	if ( !ut->rows_full_details ) {
		puts(err_out_of_memory);
		free_ut(ut);
		return NULL;
	}

	/* loop for each files */
	current_row = 0;
	for ( i = 0; i < ut->datasets_count; i++ ) {
		/* open file */
		f = fopen(ut->datasets[i].name, "r");
		if ( !f ) {
			puts(err_unable_open_file);
			free_ut(ut);
			return NULL;
		}

		/* reset columns */
		for ( y = 0; y < INPUT_VALUES; y++ ) {
			columns_index[y] = -1;
		}

		/* get header */
		if ( ! get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			puts("no header found!");
			free_ut(ut);
			fclose(f);
			return NULL;
		}

		/* csv_standard ?*/
		if ( ! string_n_compare_i(buffer, "site", 4) ) {
			/* rewind file */
			fseek(f, 0, SEEK_SET);

			/* alloc memory for details, if any */
			details_no_leak = realloc(ut->details, (ut->details_count+1)*sizeof*details_no_leak);
			if ( !details_no_leak ) {
				puts(err_out_of_memory);
				free_ut(ut);
				fclose(f);
				return NULL;
			}
			++ut->details_count;
			ut->details = details_no_leak;

			/* get details */
			ut->details[i] = parse_dd(f);
			if ( ! ut->details[i] ) {
				free_ut(ut);
				return NULL;
			}

			/* hourly ? */
			if ( HOURLY_TIMERES == ut->details[i]->timeres ) {
				hourly_dataset = 1;
			}

			/* get header */
			if ( ! get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
				puts("no header found!");
				free_ut(ut);
				fclose(f);
				return NULL;
			}
		}

		/* parse header */
		has_dtime = 0;

		/*  check for timestamps */
		columns_index[TIME_STAMP] = get_column_of(buffer, dataset_delimiter, TIMESTAMP_START_STRING);
		if ( -2 == columns_index[TIME_STAMP] ) {
			puts(err_out_of_memory);
			free_ut(ut);
			fclose(f);
			return NULL;
		} else if ( -1 == columns_index[TIME_STAMP] ) {
			/*  check for timestamp */
			columns_index[TIME_STAMP] = get_column_of(buffer, dataset_delimiter, TIMESTAMP_STRING);
			if ( -2 == columns_index[TIME_STAMP] ) {
				puts(err_out_of_memory);
				free_ut(ut);
				fclose(f);
				return NULL;
			} else if ( -1 == columns_index[TIME_STAMP] ) {
				/*  check for dtime */
				columns_index[TIME_STAMP] = get_column_of(buffer, dataset_delimiter, Dtime);
				if ( -2 == columns_index[TIME_STAMP] ) {
					puts(err_out_of_memory);
					free_ut(ut);
					fclose(f);
					return NULL;
				} else if ( -1 == columns_index[TIME_STAMP] ) {
					puts("no valid header found.");
					free_ut(ut);
					fclose(f);
					return NULL;
				} else {
					has_dtime = 1;
				}
			}
		} else {
			columns_index[TIME_STAMP] = get_column_of(buffer, dataset_delimiter, TIMESTAMP_END_STRING);
			if ( -2 == columns_index[TIME_STAMP] ) {
				puts(err_out_of_memory);
				free_ut(ut);
				fclose(f);
				return NULL;
			} else if ( -1 == columns_index[TIME_STAMP] ) {
				printf(err_unable_find_column, TIMESTAMP_END_STRING);
				free_ut(ut);
				fclose(f);
				return NULL;
			}
		}
		
		/* parse header */
		for ( y = 0, token = string_tokenizer(buffer, dataset_delimiter, &p); token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++y ) {
			/* skip timestamp ( 1 instead of 0 ) */
			for ( j = 1; j < INPUT_VALUES; j++ ) {
				strcpy(buffer2, "itp");
				strcat(buffer2, input_columns_tokens[j]); 
				if (	! string_compare_i(token, input_columns_tokens[j]) ||
						! string_compare_i(token, buffer2) ) {
					/* check if column was already assigned */
					if ( -1 != columns_index[j] ) {
						printf("column %s already found at index %d\n", token, columns_index[j]+1);
						fclose(f);
						free_ut(ut);
						return NULL;
					} else {
						if ( TA == j ) {
							if ( ! string_compare_i(token, buffer2) ) {
								is_itpTA = 1;
							}
						} else if ( SWIN == j ) {
							if ( ! string_compare_i(token, buffer2) ) {
								is_itpSW_IN = 1;
							}							
						}
						columns_index[j] = y;
					}
				}
			}
		}

		/* check for required colums */
		for ( y = 0; y < INPUT_VALUES; y++ ) {
			if ( -1 == columns_index[y] ) {
				printf(err_unable_find_column, input_columns_tokens[y]);
				free_ut(ut);
				fclose(f);
				return NULL;
			}
		}

		/* read file */
		dataset_rows_count = 0;
		while ( get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			/* prevent heap corruption */
			if ( current_row++ == z ) {
				z += LEAP_YEAR_ROWS;
				rows_full_details_no_leak = realloc(ut->rows_full_details, z*sizeof*rows_full_details_no_leak);
				if ( !rows_full_details_no_leak ) {
					puts(err_out_of_memory);
					free_ut(ut);
					fclose(f);
					return NULL;
				}
				ut->rows_full_details = rows_full_details_no_leak;
			}

			/* reset */
			ut->rows_full_details[current_row-1].flags = 0;
			ut->rows_full_details[current_row-1].night = INVALID_VALUE;
			ut->rows_full_details[current_row-1].month_per_group = INVALID_VALUE;
			ut->rows_full_details[current_row-1].timestamp.DD = INVALID_VALUE;
			ut->rows_full_details[current_row-1].timestamp.MM = INVALID_VALUE;
			ut->rows_full_details[current_row-1].timestamp.YYYY = INVALID_VALUE;
			ut->rows_full_details[current_row-1].timestamp.hh = INVALID_VALUE;
			ut->rows_full_details[current_row-1].timestamp.mm = INVALID_VALUE;

			/* parse row */
			assigned = 0;
			for ( y = 0, token = string_tokenizer(buffer, dataset_delimiter, &p); token; token = string_tokenizer(NULL, dataset_delimiter, &p), y++ ) {
				/* loop for each mandatory values */
				for ( j = 0; j < INPUT_VALUES; j++ ) {
					if ( columns_index[j] == y ) {
						/* check for timestamp */
						if ( TIME_STAMP == j ) {
							if ( has_dtime ) {
								/* convert token */
								value = convert_string_to_prec(token, &error);
								if ( error ) {
									printf(err_conversion, token, y+1, current_row);
									free_ut(ut);
									fclose(f);
									return NULL;
								}
								if ( ! hourly_dataset ) {
									row = DTIME_TO_ROW(value);
								} else {
									row = DTIME_TO_ROW_HOURLY(value);
								}

								/* fix to zero based index */
								--row;

								token = timestamp_end_by_row_s(row, 0, 0);
								if ( !token ) {
									free_ut(ut);
									fclose(f);
									return NULL;
								}
							}

							t = get_timestamp(token);
							if ( ! t ) {
								free_ut(ut);
								fclose(f);
								return NULL;
							}
							ut->rows_full_details[current_row-1].timestamp.DD = t->DD;
							ut->rows_full_details[current_row-1].timestamp.MM = t->MM;
							ut->rows_full_details[current_row-1].timestamp.YYYY = t->YYYY;
							ut->rows_full_details[current_row-1].timestamp.hh = t->hh;
							ut->rows_full_details[current_row-1].timestamp.mm = t->mm;
							ut->rows_full_details[current_row-1].timestamp.ss = t->ss;
							ut->rows_full_details[current_row-1].month_per_group = t->MM-1;
							free(t);

							/*
								fix for month per group, 'cause day 1 and 00:00 belongs to previous month...
								in this way we can have a valid seasons groups
							*/
							if (	/* ut->rows_full_details[current_row-1].month_per_group && */
									(1 == ut->rows_full_details[current_row-1].timestamp.DD) &&
									(0 == ut->rows_full_details[current_row-1].timestamp.hh) &&
									(0 == ut->rows_full_details[current_row-1].timestamp.mm)
							) {
								if ( !ut->rows_full_details[current_row-1].month_per_group ) {
									ut->rows_full_details[current_row-1].month_per_group = ut->rows_full_details[current_row-2].month_per_group;
								} else {
									--ut->rows_full_details[current_row-1].month_per_group;
								}
							}
						} else {
							/* convert token */
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf(err_conversion, token, y+1, current_row);
								free_ut(ut);
								fclose(f);
								return NULL;
							}
							/* check for NAN */
							if ( value != value ) {
								value = INVALID_VALUE;
							}
							/* assign value, -1 for remove timestamp start */
							ut->rows_full_details[current_row-1].value[j] = value;
							/* update flags */
							if ( ! IS_INVALID_VALUE(value) ) {
								ut->rows_full_details[current_row-1].flags |= 1 << (j-1);
							}
						}
						++assigned;
						break;
					}
				}
			}

			/* check if all values are imported */
			if ( assigned != INPUT_VALUES ) {
				printf(err_unable_to_import_all_values, current_row);
				free_ut(ut);
				fclose(f);		
				return NULL;
			}

			if ( ! IS_INVALID_VALUE(ut->rows_full_details[current_row-1].value[SWIN]) && (ut->rows_full_details[current_row-1].value[SWIN] < SWIN_FOR_NIGHT) ) {
				ut->rows_full_details[current_row-1].night = 1;
			}

			/* update */
			++dataset_rows_count;
			++ut->rows_full_details_count;
		}

		/* close file */
		fclose(f);

		/* update row count */
		ut->datasets[i].rows_count = dataset_rows_count;

		/* check imported rows */
		if ( ut->details_count && ut->details[i] ) {
			y = get_rows_count_by_dd(ut->details[i]);
			if ( dataset_rows_count != y ) {
				printf(err_imported_rows_count, y,  dataset_rows_count, get_timeres_in_string(ut->details[i]->timeres));
				free_ut(ut);
				return NULL;
			}
		} else {
			if (	dataset_rows_count != (LEAP_YEAR_ROWS / (hourly_dataset ? 2 : 1)) &&
					dataset_rows_count != (YEAR_ROWS / (hourly_dataset ? 2 : 1)) ) {
				printf(err_imported_rows_count_or, (LEAP_YEAR_ROWS / (hourly_dataset ? 2 : 1)),(YEAR_ROWS / (hourly_dataset ? 2 : 1)), dataset_rows_count);
				free_ut(ut);
				return NULL;
			}
		}
	}

	/* sort */
	if ( ut->datasets_count > 1 ) {
		qsort(ut->rows_full_details, ut->rows_full_details_count, sizeof *ut->rows_full_details, compare_date);
	}
	
	/* free memory */
	free(ut->datasets);
	ut->datasets = NULL;

	/*
	{
		f = fopen("debug.txt", "w");
		if ( f ) {
			fputs("NEE,TA,USTAR,SW_IN,ALL_VALID\n", f);
			for ( i = 0; i < ut->rows_full_details_count; i++ ) {
				fprintf(f, "%g,%g,%g,%g,%s\n",		ut->rows_full_details[i].value[1],
													ut->rows_full_details[i].value[2],
													ut->rows_full_details[i].value[3],
													ut->rows_full_details[i].value[4],
													IS_FLAG_SET(ut->rows_full_details[i].flags, ALL_VALID) ? "yes" : "no"
												);
			}
			fclose(f);
		}
	}
	*/

	/* return pointer */
	return ut;
}
