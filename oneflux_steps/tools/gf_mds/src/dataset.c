/*
	dataset.c

	this file is part of gf_mds

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: darpap at unitus dot it
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "dataset.h"

/* structures */
typedef struct {
	ROW *rows;
	int *columns;
	int rows_count;
	int allocated_rows_count;
} DATASET;

/* extern variables */
extern int *years;
extern int years_count;
extern DD **details_list;
extern int hourly_dataset;
extern int has_dtime;
extern int custom_tokens[GF_TOKENS];
extern const char def_tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1];
extern char tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1];
extern const PREC dtime[LEAP_YEAR_ROWS];

/* strings */
static const char delimiter[] = ", ";
static const char Isodate[] = "TIMESTAMP";
static const char Dtime[] = "Dtime";

/* error strings */
static const char err_redundancy[] = "redundancy: var \"%s\" already founded at column %d.\n";
static const char err_unable_find_column[] = "unable to find column for \"%s\" var.\n";
static const char err_conversion[] = "error during conversion of \"%s\" value at row %d, column %d.\n";
static const char err_isodate_conversion[] = "error during conversion of TIMESTAMP at row %d.\n";
static const char err_row_assigned[] = "row %d already assigned! dtime error.\n";
static const char err_invalid_index[]= "invalid %s at row %d\n";
static const char err_unable_get_header[] = "unable to get header.";
static const char err_unable_to_import_all_values[] = "unable to import all values for row %d\n";
static const char err_too_many_rows_csv_standard[] = "too many rows imported: %d should be %d. Timeres specified is %s.\n";
static const char err_too_many_rows[] = "too many rows imported: %d should be %d.\n";
static const char err_no_isodate[]= "unable to concatenate dataset with %s. please use %s instead.\n";

/* extern error strings */
extern const char err_empty_file[];
extern const char err_out_of_memory[];
extern const char err_unable_open_file[];

/* */
static void free_datasets(DATASET *datasets, const int count) {
	int i;

	for ( i = 0; i < count; i++ ) {	
		free(datasets[i].rows);
		free(datasets[i].columns);
	}
	free(datasets);
}

/* */
void free_details_list(DD **details_list, const int count) {
	int i;

	for ( i = 0; i < count; i++ ) {
		free_dd(details_list[i]);
	}
	free(details_list);
}

/* */
ROW *import_dataset(const LIST *const list, const int list_count, int *const rows_count) {
	int i;
	int y;
	int j;
	int z;
	int file;
	int assigned_required_values_count;
	int error;
	int is_csv_standard;
	char *p;
	char *token;
	FILE *f;
	PREC value;
	ROW *rows;
	ROW *rows_no_leak;
	DATASET *datasets;
	TIMESTAMP *t;
	char buffer[BUFFER_SIZE];

	/* check parameters */
	assert(list && rows_count);

	/* alloc memory for datasets */
	datasets = malloc(list_count*sizeof*datasets);
	if ( !datasets ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* alloc memory for rows and columns in datasets */
	for ( i = 0; i < list_count; i++ ) {
		datasets[i].allocated_rows_count = LEAP_YEAR_ROWS;
		datasets[i].rows = malloc(datasets[i].allocated_rows_count*sizeof*datasets[i].rows);
		if ( !datasets[i].rows ) {
			puts(err_out_of_memory);
			free_datasets(datasets, list_count);
			return NULL;
		}

		datasets[i].columns = malloc(GF_REQUIRED_DATASET_VALUES*sizeof*datasets[i].columns);
		if ( !datasets[i].columns ) {
			puts(err_out_of_memory);
			free_datasets(datasets, list_count);
			return NULL;
		}
	}

	/* alloc memory for details list */
	details_list = malloc(sizeof*details_list*list_count);
	if ( !details_list ) {
		puts(err_out_of_memory);
		free_datasets(datasets, list_count);
		return NULL;
	}
	for ( i = 0; i < list_count; i++ ) {
		details_list[i] = NULL;
	}

	/* alloc memory for years */
	years = malloc(list_count*sizeof*years);
	if ( !years ) {
		puts(err_out_of_memory);
		free_details_list(details_list, list_count);
		free_datasets(datasets, list_count);
		return NULL;
	}

	/* has dtime ? */
	if ( has_dtime ) {
		if ( ! string_compare_i(tokens[GF_ROW_INDEX], Isodate) ) {
			strcpy(tokens[GF_ROW_INDEX], Dtime);
		}
	}

	/* loop for each file */
	for ( file = 0; file < list_count; file++ ) {
		/* reset datasets */
		datasets[file].rows_count = 0;

		/* open file */
		f = fopen(list[file].fullpath, "r");
		if ( !f ) {
			puts(err_unable_open_file);
			free_details_list(details_list, list_count);
			free_datasets(datasets, list_count);
			return 0;
		}

		/* */
		if ( !get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			puts(err_empty_file);
			fclose(f);
			free_details_list(details_list, list_count);
			free_datasets(datasets, list_count);
			return 0;
		}

		/* reset column positions */
		for ( i = 0; i < GF_REQUIRED_DATASET_VALUES; i++ ) {
			datasets[file].columns[i] = -1;
		}

		/* no details ? */
		is_csv_standard = 0;
		if ( ! string_n_compare_i(buffer, "site", 4) ) {
			/* update flag */
			is_csv_standard = 1;

			/* rewind file */
			fseek(f, 0, SEEK_SET);

			/* get details */
			details_list[file] = parse_dd(f);
			if ( !details_list[file] ) {
				fclose(f);
				free_details_list(details_list, list_count);
				free_datasets(datasets, list_count);
				return 0;
			}

			/* hourly ? */
			hourly_dataset = 0;
			if ( HOURLY_TIMERES == details_list[file]->timeres ) {
				hourly_dataset = 1;
			}

			if ( !get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
				puts(err_unable_get_header);
				free_details_list(details_list, list_count);
				free_datasets(datasets, list_count);
				fclose(f);
				return NULL;
			}
		}

		/* parse header */
		for ( i = 0, token = string_tokenizer(buffer, delimiter, &p); token; token = string_tokenizer(NULL, delimiter, &p), ++i ) {
			for ( y = 0; y < GF_REQUIRED_DATASET_VALUES; y++ ) {
				if ( !string_compare_i(token, tokens[y]) ) {
					/* check if column was already assigned */
					if ( -1 != datasets[file].columns[y] ) {
						printf(err_redundancy, tokens[y], datasets[file].columns[y]+1);
						free_details_list(details_list, list_count);
						free_datasets(datasets, list_count);
						fclose(f);
						return NULL;
					} else {
						/* assign column position */
						datasets[file].columns[y] = i;
						/* do not break loop 'cause we can use var to be filled in methods! */
						/* break */
					}
				}
			}
		}

		/* check for required colums */
		for ( i = 0; i < GF_REQUIRED_DATASET_VALUES; i++ ) {
			if ( -1 == datasets[file].columns[i] ) {
				printf(err_unable_find_column, tokens[i]);
				free_details_list(details_list, list_count);
				free_datasets(datasets, list_count);
				fclose(f);
				return NULL;
			}
		}

		/* import values */
		while ( get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			/* alloc rows if needed */
			if ( datasets[file].rows_count++ == datasets[file].allocated_rows_count ) {
				i = LEAP_YEAR_ROWS;
				if ( hourly_dataset ) {
					i /= 2;
				}
				datasets[file].allocated_rows_count += i;
				rows_no_leak = realloc(datasets[file].rows, datasets[file].allocated_rows_count*sizeof*rows_no_leak);
				if ( !rows_no_leak ) {
					puts(err_out_of_memory);
					free_details_list(details_list, list_count);
					free_datasets(datasets, list_count);
					fclose(f);
					return NULL;
				}

				/* assign pointer */
				datasets[file].rows = rows_no_leak;
			}

			/* get values */
			assigned_required_values_count = 0;
			for ( i = 0, token = string_tokenizer(buffer, delimiter, &p); token; token = string_tokenizer(NULL, delimiter, &p), i++ ) {
				/* loop for each mandatory values */
				for ( y = 0; y < GF_REQUIRED_DATASET_VALUES; y++ ) {
					if ( datasets[file].columns[y] == i ) {
						if ( (GF_ROW_INDEX == y) && !has_dtime ) {
							t = get_timestamp(token);
							if ( ! t ) {
								printf(err_conversion, token, i+1, datasets[file].rows_count);
								free_details_list(details_list, list_count);
								free_datasets(datasets, list_count);
								fclose(f);
								return NULL;
							}
							/* set year */
							if ( !(datasets[file].rows_count-1) ) {
								years[file] = t->YYYY;
							}
							j = get_row_by_timestamp(t, hourly_dataset);
							free(t);
							if ( -1 == j ) {
								printf(err_isodate_conversion, datasets[file].rows_count);
								free_details_list(details_list, list_count);
								free_datasets(datasets, list_count);
								fclose(f);
								return NULL;
							}
							value = j;
						} else {
							/* convert token */
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf(err_conversion, token, i+1, datasets[file].rows_count);
								free_details_list(details_list, list_count);
								free_datasets(datasets, list_count);
								fclose(f);
								return NULL;
							}
							
							/* convert dtime to row */
							if ( (GF_ROW_INDEX == y) && has_dtime ) {
								if ( hourly_dataset ) {
									j = DTIME_TO_ROW_HOURLY(value);
								} else {
									j = DTIME_TO_ROW(value);
								}

								/* fix to zero based index */
								--j;

								/* assign it */
								value = j;
							}
						}

						/* check for NAN */
						if ( value != value ) {
							value = INVALID_VALUE;
						}

						/* assign value */
						datasets[file].rows[datasets[file].rows_count-1].value[y] = value;

						/* update counter */
						++assigned_required_values_count;
					}
				}
			}

			/* check if all required values have been imported */
			if ( assigned_required_values_count != GF_REQUIRED_DATASET_VALUES ) {
				printf(err_unable_to_import_all_values, datasets[file].rows_count); 
				free_details_list(details_list, list_count);
				free_datasets(datasets, list_count);
				fclose(f);
				return NULL;
			}

			/* set year for old dataset */
			if ( !(datasets[file].rows_count-1) && has_dtime ) {
				years[file] = INVALID_VALUE;
			}
		}

		/* close file */
		fclose(f);
	}

	/* create clean dataset */
	j = 0;
	rows = NULL;
	for ( file = 0; file < list_count; file++ ) {
		/* csv standard ? */
		if ( details_list[file] ) {
			i = get_rows_count_by_dd(details_list[file]);
		} else {
			/* number of rows we want to allocate  */
			i = LEAP_YEAR_ROWS;
			
			/* check if a full not leap dataset was imported */
			if ( (hourly_dataset ? YEAR_ROWS / 2 : YEAR_ROWS) == datasets[file].rows_count ) {
				i = YEAR_ROWS;
			}

			if ( hourly_dataset ) {
				i /= 2;
			}
		}

		/* check if imported rows are > than i (counts of rows we wants to allocate) */
		if ( datasets[file].rows_count > i ) {
			if ( details_list[file] ) {
				printf(err_too_many_rows_csv_standard, datasets[file].rows_count, i, get_timeres_in_string(details_list[file]->timeres));		
			} else {
				printf(err_too_many_rows, datasets[file].rows_count, i);		
			}
			free(rows);
			free_details_list(details_list, list_count);
			free_datasets(datasets, list_count);
			return NULL;
		}

		/* alloc memory */
		rows_no_leak = realloc(rows, (j+i)*sizeof*rows_no_leak);
		if ( !rows_no_leak ) {
			puts(err_out_of_memory);
			free(rows);
			free_details_list(details_list, list_count);
			free_datasets(datasets, list_count);
			return NULL;
		}

		/* assign pointer */
		rows = rows_no_leak;

		/* reset newly rows */
		for ( y = 0; y < i; y++ ) {
			for ( z = 0; z < GF_REQUIRED_DATASET_VALUES; z++ ) {
				rows[j+y].value[z] = INVALID_VALUE;
			}
			rows[j+y].assigned = 0;
		}

		/* assign rows */
		z = i;
		for ( i = 0; i < datasets[file].rows_count; i++ ) {
			y = (int)datasets[file].rows[i].value[GF_ROW_INDEX];
			
			/* check row index */
			if ( (y < 0) || (y >= z) ) {
				printf(err_invalid_index, has_dtime ? Dtime : Isodate, i+1);
				free(rows);
				free_details_list(details_list, list_count);
				free_datasets(datasets, list_count);
				return NULL;
			}

			/* check if row was already assigned */
			if ( rows[j+y].assigned ) {
				printf(err_row_assigned, i+1);
				free(rows);
				free_details_list(details_list, list_count);
				free_datasets(datasets, list_count);
				return NULL;
			}

			/* assign values */
			rows[j+y].value[GF_TOFILL] = datasets[file].rows[i].value[GF_TOFILL];
			rows[j+y].value[GF_SWIN] = datasets[file].rows[i].value[GF_SWIN];
			rows[j+y].value[GF_TA] = datasets[file].rows[i].value[GF_TA];
			rows[j+y].value[GF_VPD] = datasets[file].rows[i].value[GF_VPD];
			rows[j+y].value[GF_ROW_INDEX] = datasets[file].rows[i].value[GF_ROW_INDEX];
			rows[j+y].assigned = 1;

			/* inc */
			/* ++*rows_count; */
		}

		/* keep track of allocated rows */
		j += z;
	}
	*rows_count = j;

	/* fix years for old dataset type */
	y = 0;
	for ( i = 0; i < list_count; i++ ) {
		if ( IS_INVALID_VALUE(years[i]) ) {
			++y;
		}
	}

	/* free memory */
	free_datasets(datasets, list_count);

	/* */
	if ( y > 1 ) {
		printf(err_no_isodate, Dtime, Isodate);
		free(rows);
		free_details_list(details_list, list_count);
		rows = NULL;
	}

	/* return pointer */
	return rows;
}
