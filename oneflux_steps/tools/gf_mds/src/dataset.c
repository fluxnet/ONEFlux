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
	TIMESTAMP *timestamps;
	int rows_count;
	int allocated_rows_count;
} DATASET;

/* extern variables */
extern int *years;
extern int years_count;
extern int timeres;
extern int custom_tokens[GF_TOKENS];
extern const char def_tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1];
extern char tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1];

/* strings */
static const char delimiter[] = ", ";

/* error strings */
static const char err_redundancy[] = "redundancy: var \"%s\" already founded at column %d.\n";
static const char err_unable_find_column[] = "unable to find column for \"%s\" var.\n";
static const char err_conversion[] = "error during conversion of \"%s\" value at row %d, column %d.\n";
static const char err_timestamp_conversion[] = "error during conversion of %s at row %d.\n";
static const char err_row_assigned[] = "row %d already assigned!\n";
static const char err_invalid_index[]= "invalid %s at row %d\n";
static const char err_unable_get_header[] = "unable to get header.";
static const char err_unable_to_import_all_values[] = "unable to import all values for row %d\n";
static const char err_no_timestamp[]= "unable to concatenate dataset with %s. please use %s instead.\n";
static const char err_invalid_timestamp[] = "invalid timestamp at row %d: %04d%02d%02d%02d%02d%02d\n";
static const char err_invalid_freq[] = "invalid timestamp at row %d\n";
static const char err_unable_to_create_debug_file[] = "unable to create import debug file: %s\n";
static const char err_too_many_rows[] = "too many rows found! %d instead of %d\n";

/* extern error strings */
extern const char err_empty_file[];
extern const char err_out_of_memory[];
extern const char err_unable_open_file[];

/* */
static void free_datasets(DATASET *datasets, const int count) {
	int i;

	for ( i = 0; i < count; i++ ) {	
		free(datasets[i].timestamps);
		free(datasets[i].rows);
		free(datasets[i].columns);
	}
	free(datasets);
}

/* updated on January 17, 2018 */
ROW *import_dataset(const LIST *const list, const int list_count, int *const rows_count) {
	int i;
	int y;
	int j;
	int z;
	int file;
	int assigned_required_values_count;
	int error;
	int old_year;
	char *p;
	char *token;
	FILE *f;
	PREC value;
	ROW *rows;
	ROW *rows_no_leak;
	DATASET *datasets;
	char buffer[BUFFER_SIZE];

	/* check parameters */
	assert(list && rows_count);

	*rows_count = 0;

	/* alloc memory for datasets */
	datasets = malloc(list_count*sizeof*datasets);
	if ( !datasets ) {
		puts(err_out_of_memory);
		return NULL;
	}
	memset(datasets, 0, list_count*sizeof*datasets);

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

		datasets[i].timestamps = malloc(datasets[i].allocated_rows_count*sizeof*datasets[i].timestamps);
		if ( !datasets[i].timestamps ) {
			puts(err_out_of_memory);
			free_datasets(datasets, list_count);
			return NULL;
		}
		memset(datasets[i].timestamps, 0, datasets[i].allocated_rows_count*sizeof*datasets[i].timestamps);
	}

	/* alloc memory for years */
	years = malloc(list_count*sizeof*years);
	if ( !years ) {
		puts(err_out_of_memory);
		free_datasets(datasets, list_count);
		return NULL;
	}

	/* loop for each file */
	//*rows_count = 0; /* we must reset here 'cause we can have concatenated datasets */
	for ( file = 0; file < list_count; file++ ) {
		/* reset datasets */
		datasets[file].rows_count = 0;

		/* open file */
		f = fopen(list[file].fullpath, "r");
		if ( !f ) {
			puts(err_unable_open_file);
			free_datasets(datasets, list_count);
			return 0;
		}

		/* */
		if ( !get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			puts(err_empty_file);
			fclose(f);
			free_datasets(datasets, list_count);
			return 0;
		}

		/* reset column positions */
		for ( i = 0; i < GF_REQUIRED_DATASET_VALUES; i++ ) {
			datasets[file].columns[i] = -1;
		}	

		/* parse header */
		for ( i = 0, token = string_tokenizer(buffer, delimiter, &p); token; token = string_tokenizer(NULL, delimiter, &p), ++i ) {
			for ( y = 0; y < GF_REQUIRED_DATASET_VALUES; y++ ) {
				if ( ! string_compare_i(token, tokens[y]) ) {
					/* check if column was already assigned */
					if ( -1 != datasets[file].columns[y] ) {
						printf(err_redundancy, tokens[y], datasets[file].columns[y]+1);
						free_datasets(datasets, list_count);
						fclose(f);
						return NULL;
					} else {
						/* assign column position */
						datasets[file].columns[y] = i;

						/* use same case as input for tofill var */
						if ( GF_TOFILL == y )
						{
							strcpy(tokens[y], token);
						}

						/* do not break loop for var 'cause we can use var to be filled in methods! */
						/*break;*/
					}
				}
			}
		}

		/* check for required colums */
		for ( i = 0; i < GF_REQUIRED_DATASET_VALUES; i++ ) {
			if ( -1 == datasets[file].columns[i] ) {
				printf(err_unable_find_column, tokens[i]);
				free_datasets(datasets, list_count);
				fclose(f);
				return NULL;
			}
		}

		/* import values */
		while ( get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			/* alloc rows if needed */
			if ( datasets[file].rows_count++ == datasets[file].allocated_rows_count ) {
				/* we allocate leap rows to prevent out of bounds! */
				i = get_rows_count_by_timeres(timeres, 2000);
				
				datasets[file].allocated_rows_count += i;
				rows_no_leak = realloc(datasets[file].rows, datasets[file].allocated_rows_count*sizeof*rows_no_leak);
				if ( !rows_no_leak ) {
					puts(err_out_of_memory);
					free_datasets(datasets, list_count);
					fclose(f);
					return NULL;
				}

				/* assign pointer */
				datasets[file].rows = rows_no_leak;

				/* re-alloc memory for timestamps */
				{
					int z;
					TIMESTAMP* timestamp_no_leak;

					timestamp_no_leak = realloc(datasets[file].timestamps, datasets[file].allocated_rows_count*sizeof*timestamp_no_leak);
					if ( !timestamp_no_leak ) {
						puts(err_out_of_memory);
						free_datasets(datasets, list_count);
						fclose(f);
						return NULL;
					}

					/* assign pointer */
					datasets[file].timestamps = timestamp_no_leak;

					for ( z = i; z < datasets[file].allocated_rows_count; ++z ) {
						memset(&datasets[file].timestamps[z], 0, sizeof(TIMESTAMP));
					}
				}
			}

			/* get values */
			assigned_required_values_count = 0;
			for ( i = 0, token = string_tokenizer(buffer, delimiter, &p); token; token = string_tokenizer(NULL, delimiter, &p), i++ ) {
				/* loop for each mandatory values */
				for ( y = 0; y < GF_REQUIRED_DATASET_VALUES; y++ ) {
					if ( datasets[file].columns[y] == i ) {
						if ( GF_ROW_INDEX == y ) {
							TIMESTAMP* t;

							t = get_timestamp(token);
							if ( ! t ) {
								printf(err_conversion, token, i+1, datasets[file].rows_count);
								free_datasets(datasets, list_count);
								fclose(f);
								return NULL;
							}
							datasets[file].timestamps[datasets[file].rows_count-1] = *t;

							/* set year */
							if ( !(datasets[file].rows_count-1) ) {
								years[file] = t->YYYY;
								old_year = years[file];
								*rows_count += get_rows_count_by_timeres(timeres, t->YYYY);
							} else {
								/*
									check if year is changed...
									we don't know if is a multi-year dataset...

								*/
								if ( old_year != t->YYYY ) {
									/* check if is last year */
									if ( (t->MM != 1)
										|| (t->DD != 1)
										|| (t->hh != 0)
										|| (t->mm != 0) ) {
											*rows_count += get_rows_count_by_timeres(timeres, t->YYYY);
											old_year = t->YYYY;
									}
								}

							}
							j = get_row_by_timestamp(t, timeres);
							free(t);
							if ( -1 == j ) {
								printf(err_timestamp_conversion, tokens[GF_ROW_INDEX], datasets[file].rows_count);
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
								free_datasets(datasets, list_count);
								fclose(f);
								return NULL;
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
				free_datasets(datasets, list_count);
				fclose(f);
				return NULL;
			}
		}

		/* close file */
		fclose(f);
	}

	/* save imported file for debugging purposes */
#ifdef _DEBUG
	{
		for ( file = 0; file < list_count; file++ ) {
			char buf[256];
			FILE* s;

			sprintf(buf, "dataset_debug_%02d.csv", file+1);
			s = fopen(buf, "w");
			if ( ! s ) {
				printf(err_unable_to_create_debug_file, buf); 
				free_datasets(datasets, list_count);
				fclose(f);
				return NULL;
			}
			fputs("ROW_INDEX,", f);
			fprintf(f, "%s,", tokens[GF_TOFILL]);
			fprintf(f, "%s,", tokens[GF_DRIVER_1]);
			fprintf(f, "%s,", tokens[GF_DRIVER_2A]);
			fprintf(f, "%s\n", tokens[GF_DRIVER_2B]);
			for ( i = 0; i < datasets[file].rows_count; ++i ) {
				fprintf(f, "%g,%g,%g,%g,%g\n"
							, datasets[file].rows[i].value[GF_ROW_INDEX]
							, datasets[file].rows[i].value[GF_TOFILL]
							, datasets[file].rows[i].value[GF_DRIVER_1]
							, datasets[file].rows[i].value[GF_DRIVER_2A]
							, datasets[file].rows[i].value[GF_DRIVER_2B]
				);
			}
			fclose(s);
		}
	}
#endif

	/* create clean dataset */
	j = 0;
	rows = NULL;
	for ( file = 0; file < list_count; file++ ) {
		/* get number of rows by year */
		i = get_rows_count_by_timeres(timeres, years[file]);

		/* check if imported rows are > than year's rows count */
		if ( datasets[file].rows_count > i ) {
            printf(err_too_many_rows, datasets[file].rows_count, i);
            free(rows);
            free_datasets(datasets, list_count);
            return NULL;
		}

		/* parse timestamps */
		{
			int freq; /* timeres */
			int row;

			for( z = 0; z < datasets[file].rows_count; ++z ) {
				if ( ! check_timestamp(&datasets[file].timestamps[z]) ) {
					printf(err_invalid_timestamp, z+1
								, datasets[file].timestamps[z].YYYY
								, datasets[file].timestamps[z].MM
								, datasets[file].timestamps[z].DD
								, datasets[file].timestamps[z].hh
								, datasets[file].timestamps[z].mm
								, datasets[file].timestamps[z].ss
					);
					free(rows);
					free_datasets(datasets, list_count);
					return NULL;
				}
			}

			/* get timeres by timestamps differences */
			freq = timestamp_difference_in_seconds(&datasets[file].timestamps[1], &datasets[file].timestamps[0]);
			row = 0;
			for( z = 1; z < datasets[file].rows_count-1; ++z ) {
				int diff;

				diff = timestamp_difference_in_seconds(&datasets[file].timestamps[z+1], &datasets[file].timestamps[z]);

				if ( diff < freq ) {
					freq = diff;
					row = z;
				}
			}

			/* check timeres */
			freq /= 60;
			{
				int err;

				err = 0;
				switch ( timeres )
				{
					case QUATERHOURLY_TIMERES:
						if ( freq != 15 ) err = 1;
					break;

					case HALFHOURLY_TIMERES:
						if ( freq != 30 ) err = 1;
					break;

					case HOURLY_TIMERES:
						if ( freq != 60 ) err = 1;
					break;
				}

				if ( err ) {
					printf(err_invalid_freq, row);
					free(rows);
					free_datasets(datasets, list_count);
					return NULL;
				}
			}
		}

		/* alloc memory */
		rows_no_leak = realloc(rows, (j+i)*sizeof*rows_no_leak);
		if ( !rows_no_leak ) {
			puts(err_out_of_memory);
			free(rows);
			free_datasets(datasets, list_count);
			return NULL;
		}

		/* assign pointer */
		rows = rows_no_leak;

		/* reset newly rows */
		for ( y = 0; y < i; y++ ) {
			for ( z = 0; z < GF_REQUIRED_DATASET_VALUES; z++ ) {
				if ( GF_ROW_INDEX == z ) {
					rows[j+y].value[z] = j+y;
				} else {
					rows[j+y].value[z] = INVALID_VALUE;
				}
			}
			rows[j+y].assigned = 0;
		}

		/* assign rows */
		{
			int old_year;
			int k;

			z = i;
			k = 0;
			old_year = datasets[file].timestamps[0].YYYY;
			for ( i = 0; i < datasets[file].rows_count; i++ ) {
				y = (int)datasets[file].rows[i].value[GF_ROW_INDEX];

				if ( (old_year != datasets[file].timestamps[i].YYYY)
						&& (
							(datasets[file].timestamps[i].MM != 1)
							|| (datasets[file].timestamps[i].DD != 1)
							|| (datasets[file].timestamps[i].hh != 0)
							|| (datasets[file].timestamps[i].mm != 0)
							)
				) {
					old_year = datasets[file].timestamps[i].YYYY;
					k += get_rows_count_by_timeres(timeres, old_year);
				}
				
				/* check row index */
				if ( (y < 0) || (y >= z) ) {
					printf(err_invalid_index, tokens[GF_ROW_INDEX], i+1);
					free(rows);
					free_datasets(datasets, list_count);
					return NULL;
				}

				/* check if row was already assigned */
				if ( rows[j+y+k].assigned ) {
					printf(err_row_assigned, i+1);
					free(rows);
					free_datasets(datasets, list_count);
					return NULL;
				}

				/* assign values */
				rows[j+y+k].value[GF_TOFILL] = datasets[file].rows[i].value[GF_TOFILL];
				rows[j+y+k].value[GF_DRIVER_1] = datasets[file].rows[i].value[GF_DRIVER_1];
				rows[j+y+k].value[GF_DRIVER_2A] = datasets[file].rows[i].value[GF_DRIVER_2A];
				rows[j+y+k].value[GF_DRIVER_2B] = datasets[file].rows[i].value[GF_DRIVER_2B];
				rows[j+y+k].value[GF_ROW_INDEX] = datasets[file].rows[i].value[GF_ROW_INDEX];
				rows[j+y+k].assigned = 1;
			}
		}

		/* keep track of allocated rows */
		j += z;
	}
	//assert(*rows_count == j);
	*rows_count = j;

	/* save imported file for debugging purposes */
#ifdef _DEBUG
	{
		char buf[256];
		FILE* s;

		sprintf(buf, "dataset_debug_clean.csv");
		s = fopen(buf, "w");
		if ( ! s ) {
			printf(err_unable_to_create_debug_file, buf); 
			free_datasets(datasets, list_count);
			fclose(f);
			return NULL;
		}
		fputs("ROW_INDEX,", f);
		fprintf(f, "%s,", tokens[GF_TOFILL]);
		fprintf(f, "%s,", tokens[GF_DRIVER_1]);
		fprintf(f, "%s,", tokens[GF_DRIVER_2A]);
		fprintf(f, "%s\n", tokens[GF_DRIVER_2B]);
		for ( i = 0; i < *rows_count; ++i ) {
			fprintf(f, "%g,%g,%g,%g,%g\n"
						, rows[i].value[GF_ROW_INDEX]
						, rows[i].value[GF_TOFILL]
						, rows[i].value[GF_DRIVER_1]
						, rows[i].value[GF_DRIVER_2A]
						, rows[i].value[GF_DRIVER_2B]
			);
		}
		fclose(s);
	}
#endif

	/* free memory */
	free_datasets(datasets, list_count);

	/* return pointer */
	return rows;
}
