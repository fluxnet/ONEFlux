/*
	dataset.c

	this file is part of ure - Uncertainty and References Extraction

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

/* v1.02 */
/* maybe one day they're used again* /
/*
#include "info_gpp_dt_hh.h"
#include "info_gpp_dt_dd.h"
#include "info_gpp_dt_ww.h"
#include "info_gpp_dt_mm.h"
#include "info_gpp_dt_yy.h"
#include "info_gpp_nt_hh.h"
#include "info_gpp_nt_dd.h"
#include "info_gpp_nt_ww.h"
#include "info_gpp_nt_mm.h"
#include "info_gpp_nt_yy.h"
#include "info_reco_dt_hh.h"
#include "info_reco_dt_dd.h"
#include "info_reco_dt_ww.h"
#include "info_reco_dt_mm.h"
#include "info_reco_dt_yy.h"
#include "info_reco_nt_hh.h"
#include "info_reco_nt_dd.h"
#include "info_reco_nt_ww.h"
#include "info_reco_nt_mm.h"
#include "info_reco_nt_yy.h"
*/

/* v1.02 */
/* defines */
#define MAT_VALUE(m, r, c) ((m)->values[(r) * (m)->columns_count + (c)])

/* externs */
extern char *g_input_path;
extern char *g_output_path;

/* v1.02 */
extern char *g_y_filter;
extern char *g_c_filter;
extern int g_debug;
extern int g_valid_data_count;
extern int g_valid_perc_count;
extern char *g_file_buf; 
extern int g_file_buf_size;
extern int g_min_7_perc_count;
extern int g_min_3_perc_count;

extern const char *types_suffix[TYPES_SUFFIX];
extern const char *authors_suffix[AUTHORS_SUFFIX];

/* v1.02 */
/* structs */
typedef struct {
	PREC* values;
	int* indices;
	int* percentiles;
	int rows_count;
	int columns_count;
} MATRIX_REF;

/* constants */
#define GPP_FILENAME_LEN	22		/* .ext included */
#define RECO_FILENAME_LEN	23		/* .ext included */
static const float percentiles_test_1[PERCENTILES_COUNT_1] = { 5, 16, 25, 50, 75, 84, 95 };
static const float percentiles_test_2[PERCENTILES_COUNT_2] = {
																1.25,
																3.75,
																6.25,
																8.75,
																11.25,
																13.75,
																16.25,
																18.75,
																21.25,
																23.75,
																26.25,
																28.75,
																31.25,
																33.75,
																36.25,
																38.75,
																41.25,
																43.75,
																46.25,
																48.75,
																51.25,
																53.75,
																56.25,
																58.75,
																61.25,
																63.75,
																66.25,
																68.75,
																71.25,
																73.75,
																76.25,
																78.75,
																81.25,
																83.75,
																86.25,
																88.75,
																91.25,
																93.75,
																96.25,
																98.75,
																50
};
const int days_per_month[MONTHS] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

/* strings */
static const char dataset_delimiter[] = ",\r\n";
static const char output_file_hh[] = "%s%s_%s_%s_hh.csv";
static const char output_file_dd[] = "%s%s_%s_%s_dd.csv";
static const char output_file_ww[] = "%s%s_%s_%s_ww.csv";
static const char output_file_mm[] = "%s%s_%s_%s_mm.csv";
static const char output_file_yy[] = "%s%s_%s_%s_yy.csv";
static const char header_file_hh[] = "%s,DTIME,";
static const char header_file_dd[] = "%s,DOY,";
static const char header_file_ww[] = "%s,WEEK,";
static const char header_file_mm[] = "%s,";
static const char header_file_yy[] = "%s,";
static const char header_file_reco[] = "RECO,RECO_n\n";
static const char *types[TYPES] = { "hh_y",
									"dd_y",
									"ww_y",
									"mm_y",
									"yy_y",
									"hh_c",
									"dd_c",
									"ww_c",
									"mm_c",
									"yy_c"
};
static const char output_var_1[] =	"%s_ref_y,"
									"%s_ust50_y,"
									"%s_mean_y,"
									"%s_SE_y,";
static const char output_var_2[] =	",%s_ref_c,"
									"%s_ust50_c,"
									"%s_mean_c,"
									"%s_SE_c,";


static const char model_efficiency_info[] = ""
"Model Efficiency selection:\n"
"The reference %s has been selected on the basis of the Model Efficiency.\n"
"Starting from the 40 different %s estimations it has been calculated the Model Efficiency between each version and the others 39.\n"
"The reference %s has been selected as the one with higher Model Efficiency sum (so the most similar to the others 39).\n"
"In this dataset have been selected as reference:\n\n";
static const char model_efficiency_c_info[] = "%s_ref_c = filtered using the ustar percentile %g\n";
static const char model_efficiency_y_info[] = "%s_ref_y filtered on year %d using the ustar percentile %g \n";
static const char model_efficiency_y_one_year_info[] = "%s_ref_y filtered using the ustar percentile %g\n";

static const char err_bad_dataset[] = "bad dataset. each columns has an invalid value at least.\n";
static const char err_unable_compute_variance[] = "unable to compute variance for column %d\n";

/* v1.02 */
static const char warning_no_setvbuf[] = "unable to use internal buffer...";

/* v1.02 */
static const char* get_filename(const char* path) {
	const char* p = NULL;
	const char* p2 = strrchr(path, '/');
	p = strrchr(path, '\\');
	
	if ( ! p || (p2 && (p2 > p)) )
		p = p2;
	if ( p )
	{
		++p;
		if ( '\0' == *p )
			p = NULL;
	}
	else
		p = path;
	return p;
}

/* v1.02 */
static int save_matrix_ref(const char*const filename, MATRIX_REF* matrix_ref) {
	int i;
	int j;
	int ret = 0; /* defaults to err */
	FILE* f = fopen(filename, "w");
	if ( ! f ) {
		puts("unable to create file!");
	} else {
		if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
			printf(warning_no_setvbuf);
		}

		fputs("INDEX,", f);
		for ( i = 0; i < matrix_ref->columns_count-1; ++i ) {
			fprintf(f, "%g", percentiles_test_2[matrix_ref->percentiles[i]]);
			if ( i < matrix_ref->columns_count-2 ) {
				fputs(",", f);
			}
		}
		fputs("\n", f);

		for ( i = 0; i < matrix_ref->rows_count; i++ ) {
			fprintf(f, "%d,", matrix_ref->indices[i]);
			for ( j = 0; j < matrix_ref->columns_count-1; ++j ) {
				fprintf(f, "%g", MAT_VALUE(matrix_ref, i, j));
				if ( j < matrix_ref->columns_count-2 ) {
					fputs(",", f);
				}
			}
			fputs("\n", f);
		}
		fclose(f);
		ret = 1;
	}
	return ret;
}

/* v1.02 */
static void free_matrix_ref(MATRIX_REF* m) {
	if ( m->indices ) {
		free(m->indices);
	}
	if ( m->percentiles ) {
		free(m->percentiles);
	}
	if ( m->values ) {
		free(m->values);
	}
	free(m);
}

/* v1.02 */
static MATRIX_REF* create_matrix_for_ref(DATASET *const dataset, int type, int* const fatal_err) {
	char buf[BUFFER_SIZE] = { 0 };
	int ret; 
	int i;
	int j;
	MATRIX_REF* matrix_ref;
	MATRIX_REF* matrix_ref_temp;
	int max_perc_rows_count;

	/* reset */
	ret = 0;
	matrix_ref = NULL;
	*fatal_err = 1; /* defaults to error */
	
	matrix_ref_temp = malloc(sizeof*matrix_ref_temp);
	if ( !matrix_ref_temp ) {
		puts(err_out_of_memory);
	} else {
		matrix_ref_temp->rows_count = dataset->rows_count;
		matrix_ref_temp->columns_count = PERCENTILES_COUNT_2;
		matrix_ref_temp->values = malloc(matrix_ref_temp->rows_count*matrix_ref_temp->columns_count*sizeof*matrix_ref_temp->values);
		if ( !matrix_ref_temp->values ) {
			puts(err_out_of_memory);
			free_matrix_ref(matrix_ref_temp);
			matrix_ref_temp = NULL;
		} else {
			matrix_ref_temp->indices = malloc(matrix_ref_temp->rows_count*sizeof*matrix_ref_temp->indices);
			if ( !matrix_ref_temp->indices ) {
				puts(err_out_of_memory);
				free_matrix_ref(matrix_ref_temp);
				matrix_ref_temp = NULL;
			} else {
				matrix_ref_temp->percentiles = malloc(PERCENTILES_COUNT_2*sizeof*matrix_ref_temp->percentiles);
				if ( !matrix_ref_temp->percentiles ) {
					puts(err_out_of_memory);
					free_matrix_ref(matrix_ref_temp);
					matrix_ref_temp = NULL;
				} else {
					for ( i = 0; i < dataset->rows_count; ++i ) {
						matrix_ref_temp->indices[i] = i;
						for ( j = 0; j < PERCENTILES_COUNT_2; ++j ) {
							if ( (type < HH_C) ) {
								MAT_VALUE(matrix_ref_temp, i, j) = dataset->percentiles_y[i].value[j];
							} else {
								MAT_VALUE(matrix_ref_temp, i, j) = dataset->percentiles_c[i].value[j];
							}
						}
					}
					for ( i = 0; i < PERCENTILES_COUNT_2; ++i ) {
						matrix_ref_temp->percentiles[i] = i;
					}
					*fatal_err = 0;
				}
			}
		}
	}

	/* saving clean matrix */
	if ( matrix_ref_temp ) {
		if ( g_debug ) {
			sprintf(buf, "%s%s_percentiles_%s_imported.csv", g_output_path, dataset->details->site, types[type]);
			printf("- - debug: saving imported %s matrix (%s)...",  types[type], get_filename(buf));
			if ( save_matrix_ref(buf, matrix_ref_temp) ) {
				puts("ok!");
			}
		}
	}

	/* remove all rows where all percentiles are invalid */ 
	if ( matrix_ref_temp ) {
		int original_rows_count = matrix_ref_temp->rows_count;
		int invalids_count;
		for ( i = 0; i < matrix_ref_temp->rows_count; ++i ) {
			invalids_count = 0;
			for ( j = 0; j < matrix_ref_temp->columns_count-1; ++j ) {
				if ( IS_INVALID_VALUE(MAT_VALUE(matrix_ref_temp, i, j)) ) {
					++invalids_count;
				}
			}

			/* j here equals matrix_ref_temp->columns_count-1 */
			if ( invalids_count == j ) {
				int z;
				/* find how many consecutive invalid rows */
				for ( z = i + 1; z < matrix_ref_temp->rows_count; ++z ) {
					invalids_count = 0;
					for ( j = 0; j < matrix_ref_temp->columns_count-1; ++j ) {
						if ( IS_INVALID_VALUE(MAT_VALUE(matrix_ref_temp, z, j)) ) {
							++invalids_count;
						}
					}

					/* j here equals matrix_ref_temp->columns_count-1 */
					if ( invalids_count != j ) {
						break;
					}
				}

				/* move remaining valid rows up */
				if ( z < matrix_ref_temp->rows_count ) {
					memmove(	&matrix_ref_temp->values[i * matrix_ref_temp->columns_count]
								, &matrix_ref_temp->values[z * matrix_ref_temp->columns_count]
								, (matrix_ref_temp->rows_count - z) * matrix_ref_temp->columns_count * sizeof(PREC)
					);

					memmove(	&matrix_ref_temp->indices[i]
								, &matrix_ref_temp->indices[z]
								, (matrix_ref_temp->rows_count - z) * sizeof*matrix_ref_temp->indices
					);
				}

				matrix_ref_temp->rows_count -= (z - i);

				/* recheck same index since new data is now here */
				--i;
			}
		}

		if ( original_rows_count != matrix_ref_temp->rows_count ) {
			printf("- - matrix_ref %s: removed %d rows entirely invalid\n", types[type], original_rows_count - matrix_ref_temp->rows_count);
		}

		if ( g_debug ) {
			if ( matrix_ref_temp->rows_count ) {
				sprintf(buf, "%s%s_percentiles_%s_reduced_rows.csv", g_output_path, dataset->details->site, types[type]);
				printf("- - debug: saving reduced %s matrix (%s)...",  types[type], get_filename(buf));
				if ( save_matrix_ref(buf, matrix_ref_temp) ) {
					puts("ok!");
				}
			}
		}

		if ( ! matrix_ref_temp->rows_count ) {
			free_matrix_ref(matrix_ref_temp);
			matrix_ref_temp = NULL;
		}
	}

	/* check max valid per percentiles */ 
	if ( matrix_ref_temp ) {
		int count;
		max_perc_rows_count = 0;
		for ( j = 0; j < matrix_ref_temp->columns_count-1; ++j ) {
			count = 0;
			for ( i = 0; i < matrix_ref_temp->rows_count; i++ ) {
				if ( ! IS_INVALID_VALUE(MAT_VALUE(matrix_ref_temp, i, j)) ) {
					++count;
				}
			}
			if ( count > max_perc_rows_count ) {
				max_perc_rows_count = count;
				/* break loop if we found maximum */
				if ( max_perc_rows_count == matrix_ref_temp->rows_count ) {
					break;
				}
			}
		}

		printf("- - matrix_ref %s: maximum valid rows count %d\n", types[type], max_perc_rows_count);
	}

	/* check for valid_data_count */
	if ( matrix_ref_temp ) {
		/* used float var due promotion... */
		/* e.g.: 0.7 * 90 = 62 instead of 63 ! */
		float v = ((float)g_valid_data_count / 100.f) * max_perc_rows_count;
		int perc = (int)v;
		int valid_rows_count;
		int valid_columns_count = 0;

		/* first pass, we count how many columns we need */
		for ( j = 0; j < matrix_ref_temp->columns_count-1; ++j ) {
			valid_rows_count = 0;
			for ( i = 0; i < matrix_ref_temp->rows_count; i++ ) {
				if ( ! IS_INVALID_VALUE(MAT_VALUE(matrix_ref_temp, i, j)) ) {
					++valid_rows_count;
				}
			}
			if ( valid_rows_count >= perc ) {
				++valid_columns_count;
			}
		}

		/* if no valid columns are found, fatal_err is 0 so it's ok to continue */
		if ( !valid_columns_count ) {
			printf("- - matrix_ref %s: all rows are invalid\n", types[type]);
		} else {
			if ( valid_columns_count < g_valid_perc_count ) {
				printf("- - matrix_ref %s: %d valid columns instead of %d\n", types[type], valid_columns_count, g_valid_perc_count);
			} else {
				*fatal_err = 1;
				matrix_ref = malloc(sizeof*matrix_ref);
				if ( matrix_ref ) {
					matrix_ref->rows_count = matrix_ref_temp->rows_count;
					matrix_ref->columns_count = valid_columns_count + 1; /* we add 50% */
					matrix_ref->values = malloc(matrix_ref->rows_count*matrix_ref->columns_count*sizeof*matrix_ref->values);
					if ( matrix_ref->values ) {
						matrix_ref->indices = malloc(matrix_ref->rows_count*sizeof*matrix_ref->indices);
						if ( matrix_ref->indices ) {
							matrix_ref->percentiles = malloc(matrix_ref->columns_count*sizeof*matrix_ref->percentiles);
							if ( matrix_ref->percentiles ) {
								*fatal_err = 0;
							}
						}
					}
				}
				if ( *fatal_err ) {
					puts(err_out_of_memory);
					free_matrix_ref(matrix_ref);
					matrix_ref = NULL;
				} else {
					int column_index = 0;
					/* second pass, fill new struct */
					for ( j = 0; j < matrix_ref_temp->columns_count-1; ++j ) {
						valid_rows_count = 0;
						for ( i = 0; i < matrix_ref_temp->rows_count; i++ ) {
							if ( ! IS_INVALID_VALUE(MAT_VALUE(matrix_ref_temp, i, j)) ) {
								++valid_rows_count;
							}
						}
						if ( valid_rows_count >= perc ) {
							for ( i = 0; i < matrix_ref_temp->rows_count; i++ ) {
								MAT_VALUE(matrix_ref, i, column_index) = MAT_VALUE(matrix_ref_temp, i, j);
							}
							for ( i = 0; i < matrix_ref_temp->rows_count; i++ ) {
								matrix_ref->indices[i] = matrix_ref_temp->indices[i];
							}
							matrix_ref->percentiles[column_index] = matrix_ref_temp->percentiles[j];
							++column_index;
						} else {
							printf("- - matrix_ref %s: percentile %g removed\n", types[type], percentiles_test_2[j]);
						}
					}

					/* set 50% index */
					matrix_ref->percentiles[column_index] = PERCENTILES_COUNT_2 - 1;

					if ( matrix_ref->columns_count < PERCENTILES_COUNT_2 ) {
						int newline = 0;
						printf("- - matrix_ref %s: reduced to %d percentiles\n", types[type], matrix_ref->columns_count - 1);							
						for ( i = 0; i < matrix_ref->columns_count - 1; ++i ) {
							if ( (0 == i) || newline ) {
								printf("- - matrix_ref %s: ", types[type]);
								newline = 0;
							}
							printf("%g ", percentiles_test_2[matrix_ref->percentiles[i]]);
							if ( (0 == ((i + 1) % 8)) && (i < matrix_ref->columns_count - 1) ) {
								puts("");
								newline = 1;
							}
						}
						puts("");
					} else {
						printf("- - matrix_ref %s: no percentile reduction\n", types[type]);
					}

					if ( g_debug ) {
						sprintf(buf, "%s%s_percentiles_%s_reduced_percentiles.csv", g_output_path, dataset->details->site, types[type]);
						printf("- - debug: saving reduced %s matrix (%s)...",  types[type], get_filename(buf));
						if ( save_matrix_ref(buf, matrix_ref) ) {
							puts("ok!");
						}
					}
				}
			}
		}
	}

	if ( matrix_ref_temp ) {
		free_matrix_ref(matrix_ref_temp);
		matrix_ref_temp = NULL;
	}

	/* remove rows that contain one or more invalid values */
	if ( matrix_ref ) {
		int original_rows_count = matrix_ref->rows_count;
		for ( i = 0; i < matrix_ref->rows_count; ++i ) {
			for ( j = 0; j < matrix_ref->columns_count-1; ++j ) {
				if ( IS_INVALID_VALUE(MAT_VALUE(matrix_ref, i, j)) ) {
					break;
				}
			}

			if ( j < matrix_ref->columns_count-1 ) {
				int z;
				/* find how many consecutive invalid rows */
				for ( z = i + 1; z < matrix_ref->rows_count; ++z ) {
					for ( j = 0; j < matrix_ref->columns_count-1; ++j ) {
						if ( IS_INVALID_VALUE(MAT_VALUE(matrix_ref, z, j)) ) {
							break;
						}
					}

					if ( j == matrix_ref->columns_count-1 ) {
						break;
					}
				}

				/* move remaining valid rows up */
				if (z < matrix_ref->rows_count) {
					memmove(	&matrix_ref->values[i * matrix_ref->columns_count]
								, &matrix_ref->values[z * matrix_ref->columns_count]
								, (matrix_ref->rows_count - z) * matrix_ref->columns_count * sizeof(PREC)
					);

					memmove(	&matrix_ref->indices[i]
								, &matrix_ref->indices[z]
								, (matrix_ref->rows_count - z) * sizeof*matrix_ref->indices
					);
				}

				matrix_ref->rows_count -= (z - i);

				/* recheck same index since new data is now here */
				--i;
			}
		}

		if ( original_rows_count != matrix_ref->rows_count ) {
			printf("- - matrix_ref %s: removed %d rows with one or more invalid value\n", types[type], original_rows_count - matrix_ref->rows_count);
		} else {
			printf("- - matrix_ref %s: no invalid value reduction\n", types[type]);
		}

		if ( g_debug ) {
			if ( matrix_ref->rows_count ) {
				sprintf(buf, "%s%s_percentiles_%s_only_valid_rows.csv", g_output_path, dataset->details->site, types[type]);
				printf("- - debug: saving reduced %s matrix (%s)...",  types[type], get_filename(buf));
				if ( save_matrix_ref(buf, matrix_ref) ) {
					puts("ok!");
				}
			}
		}

		if ( !matrix_ref->rows_count ) {
			free_matrix_ref(matrix_ref);
			matrix_ref = NULL;

		}
	}

	return matrix_ref;
}

/* using Model Efficiency, on error returns -1 */
int get_reference(const MATRIX_REF *const matrix_ref, const DATASET *const dataset, const int type, const int author_index, const int type_index, int *const fatal_err) {
	int i;
	int j;
	int row;
	int column;
	int mean_count;
	int square_count;
	int rows_valids_count;
	PREC mean;
	PREC square;
	PREC variance;
	PREC sum;
	ME *mes;
	PREC *mess;
	char buffer[256];
	FILE *f;

	/* reset */
	*fatal_err = 1; /* defaults to error */

	/* alloc memory */
	mes = malloc((matrix_ref->columns_count-1)*sizeof*mes);
	if ( !mes ) {
		puts(err_out_of_memory);
		return -1;
	}

	/* alloc memory */
	mess = malloc((matrix_ref->columns_count-1)*sizeof*mess);
	if ( !mess ) {
		puts(err_out_of_memory);
		free(mes);
		return -1;
	}

	*fatal_err = 0;

	/* reset */
	for ( i = 0; i < matrix_ref->columns_count-1; i++ ) {
		for ( j = 0; j < matrix_ref->columns_count-1; j++ ) {
			mes[i].value[j] = INVALID_VALUE;
		}
	}

	/* mef computation	*/
	for ( column = 0; column < matrix_ref->columns_count-1; column++ ) {
		/* calculates mean of the percentile analysed */
		mean = 0.0;
		mean_count = 0;
		for ( row = 0; row < matrix_ref->rows_count; row++ ) {
			if ( ! IS_INVALID_VALUE(MAT_VALUE(matrix_ref, row, column)) ) {
				mean += MAT_VALUE(matrix_ref, row, column);
				++mean_count;
			} else {
				puts("- - get_reference: unexpected invalid value found");
			}
		}
		if ( mean_count ) {
			mean /= mean_count;
		}
		/* calculates the sum of the squared difference of the single value in the percentile and the mean when value is valid */
		square = 0.0;
		square_count = 0;
		for ( row = 0; row < matrix_ref->rows_count; row++ ) {
			if ( ! IS_INVALID_VALUE(MAT_VALUE(matrix_ref, row, column)) ) {
				square += SQUARE(MAT_VALUE(matrix_ref, row, column) - mean);
				++square_count;
			} else {
				puts("- - get_reference: unexpected invalid value found");
			}
		}
		if ( square_count ) {
			variance = square / square_count;
		} else {
			printf("- - get_reference: unable to get variance for %s, column %d\n\n", types[type], column + 1);
			free(mess);
			free(mes);
			return -1;
		}

		/*
			here we calculate the model efficiency of the percentile analysed against all the others.
			NOTE: if there are invalid (-9999) values in one of the two the record is skipped
		*/
		for ( i = 0; i < matrix_ref->columns_count-1; i++ ) {
			sum = 0.0;
			rows_valids_count = 0;
			for ( j = 0; j < matrix_ref->rows_count; j++ ) {
				if ( ! IS_INVALID_VALUE(MAT_VALUE(matrix_ref, j, column)) && ! IS_INVALID_VALUE(MAT_VALUE(matrix_ref, j, i)) ) {
					sum += (MAT_VALUE(matrix_ref, j, column) - MAT_VALUE(matrix_ref, j, i))*(MAT_VALUE(matrix_ref, j, column) - MAT_VALUE(matrix_ref, j, i));
					++rows_valids_count;
				} else {
					puts("- - get_reference: unexpected invalid value found");
				}
			}
			/* v1.02 */
			/* columns and rows was inverted */
			/* so that each comparison is organized by column */
			if ( rows_valids_count ) {
				sum /= rows_valids_count;
				sum /= variance;
				/* mes[column].value[i] = 1 - sum; */
				mes[i].value[column] = 1 - sum;
			} else {
				/* mes[column].value[i] = INVALID_VALUE; */
				mes[i].value[column] = INVALID_VALUE;
			}
		}
	}

	/* v1.02 */
	/* get selected */
	for ( column = 0; column < matrix_ref->columns_count-1; column++ ) {
		mess[column] = 0.0;
		for ( row = 0; row < matrix_ref->columns_count-1; row++ ) {	
			if ( ! IS_INVALID_VALUE(mes[row].value[column]) ) {
				mess[column] += mes[row].value[column];
			}
		}
	}

	column = 0;
	sum = mess[0]; /* used as start point */
	/* we start from 1 */
	for ( i = 1; i < matrix_ref->columns_count-1; i++ ) {
		if ( mess[i] > sum ) {
			sum = mess[i];
			column = i;
		}
	}

	/* v1.02 */
	/* we can have a reduced matrix */
	/* so ref must be reflect the original 40x40 matrix */
	column = matrix_ref->percentiles[column];

	/* v1.02 */
	if ( g_debug ) {
		printf("- - debug: column ref for %s is %g%% (%d)\n", types[type], percentiles_test_2[column], column + 1);
	}

	if ( g_debug ) {
		if ( dataset->years_count > 1 ) {
			sprintf(buffer, "%s%s_%s_%s_mef_matrix_%s_%d_%d.csv", g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index], types[type], dataset->years[0].year, dataset->years[dataset->years_count-1].year);
		} else {
			sprintf(buffer, "%s%s_%s_%s_mef_matrix_%s_%d_%d.csv", g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index], types[type], dataset->years[0].year, dataset->years[dataset->years_count-1].year);
		}
		f = fopen(buffer, "w");
		if ( f ) {
			/* v1.02 */
			if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
				printf(warning_no_setvbuf);
			}

			for ( i = 0; i < matrix_ref->columns_count-1; i++ ) {
				fprintf(f, "%g", percentiles_test_2[matrix_ref->percentiles[i]]);
				if ( i < matrix_ref->columns_count-1-1 ) {
					fputs(",", f);
				}
			}
			fputs("\n", f);

			for ( i = 0; i < matrix_ref->columns_count-1; i++ ) {
				for ( j = 0; j < matrix_ref->columns_count-1; j++ ) {
					fprintf(f, "%g", mes[i].value[j]);
					if ( j < matrix_ref->columns_count-1-1 ) {
						fputs(",", f);
					}
				}
				fputs("\n", f);
			}
			fclose(f);
		} else {
			printf("- get_reference: unable to save %s\n", buffer);
		}
	}

	/* free memory */
	free(mess);
	free(mes);

	/* */
	return column;
}

/* */
static PREC get_percentile_allowing_invalid(const PREC *values, const int n, const float percentile, int *const error) {
	int i;
	int y;
	int index;
	PREC r;
	PREC *v;

	/* check parameters */
	assert(values && error);

	/* reset */
	*error = 0;

	/* */
	if ( !n ) {
		return INVALID_VALUE;
	} else if ( 1 == n ) {
		return values[0];
	}

	/* percentile MUST be a value between 0 and 100*/
	if ( percentile < 0.0 || percentile > 100.0 ) {
		*error = 1;
		return 0.0;
	}

	/* */
	v = malloc(n*sizeof*v);
	if ( !v ) {
		*error = 1;
		return 0.0;
	}

	/* */
	y = 0;
	for ( i = 0; i < n; i++ ) {
		if ( !IS_INVALID_VALUE(values[i]) ) {
			v[y++] = values[i];
		}
	}
	if ( !y ) {
		free(v);
		return INVALID_VALUE;
	}

	/* */
	qsort(v, y, sizeof *v, compare_prec);

	/*
		- changed on May 20, 2013
			FROM index = ROUND((percentile / 100.0) * y + 0.5);
			TO index = (percentile / 100) * y;

		- changed again Nov 4, 2013
			added ROUND where 0.5 is added to perc*y and then truncated to the integer.
			E.g.: perc 50 of 5 values is INTEGER[((50/100)*5)+0.5] = 3
	*/
	index = ROUND((percentile / 100) * y);
	if ( --index < 0 ) {
		index = 0;
	}

	if ( index >= y ) {
		r = v[y-1];
		free(v);
		return r;
	}

	/* */
	r = v[index];

    /* */
	free(v);

	/* */
	return r;
}

/* */
PREC get_mean_allowing_invalid(const PREC *const values, const int count) {
	int i;
	int y;
	PREC mean;

	/* check for null pointer */
	assert(values && count);

	/* */
	if ( 1 == count ) {
		return values[0];
	}

	/* compute mean */
	y = 0;
	mean = 0.0;
	for ( i = 0; i < count; i++ ) {
		if ( !IS_INVALID_VALUE(values[i]) ) {
			mean += values[i];
			++y;
		}
	}

	if ( !y ) {
		mean = INVALID_VALUE;
	} else {
		mean /= y;
	}

	/* check for NAN */
	if ( mean != mean ) {
		mean = INVALID_VALUE;
	}

	/* ok */
	return mean;
}

/* */
PREC get_standard_deviation_allowing_invalid(const PREC *const values, const int count, int *const error) {
	int i;
	int valid_count;
	PREC *valid_values;
	PREC mean;
	PREC sum;
	PREC sum2;

	/* check for null pointer */
	assert(values && count && error);

	/* reset */
	*error = 0;

	/* */
	if ( 1 == count ) {
		return INVALID_VALUE;
	}

	/* get valid values */
	valid_values = malloc(count*sizeof*valid_values);
	if ( !valid_values ) {
		*error = 1;
		return INVALID_VALUE;
	}

	valid_count = 0;
	for ( i = 0; i < count; i++ ) {
		if ( !IS_INVALID_VALUE(values[i]) ) {
			valid_values[valid_count++] = values[i];
		}
	}

	/* v1.02 */
	/*
		prevent useless computation and
		divide by zero on sum2 /= valid_count-1;
	*/
	if ( valid_count < 2 ) {
		free(valid_values);
		return INVALID_VALUE;
	}

	/* get mean */
	mean = get_mean(valid_values, valid_count);
	if ( IS_INVALID_VALUE(mean) ) {
		/* v1.02 */
		free(valid_values);

		return INVALID_VALUE;
	}

	/* compute stddev */
	sum = 0.0;
	sum2 = 0.0;
	for ( i = 0; i < valid_count; i++ ) {
		sum = (valid_values[i] - mean);
		sum *= sum;
		sum2 += sum;
	}
	sum2 /= valid_count-1;
	sum2 = (PREC)SQRT(sum2);

	/* check for NAN */
	if ( sum2 != sum2 ) {
		sum2 = INVALID_VALUE;
	}

	/* free memory */
	free(valid_values);

	/* ok */
	return sum2;
}

/* v1.02 */
P_MATRIX *process_matrix(const DATASET *const dataset, MATRIX_REF* matrix_ref, int *ref, const int type, const int author_index, const int type_index) {
	int row;
	int percentile;
	int error;
	int valids_count;
	PREC *temp;
	P_MATRIX *p_matrix;

	/* check parameters */
	assert(dataset && ref);

	/* reset */
	error = 1; /* defaults to error */

	/* alloc memory, -1 'cause we don't use 50% in this computation */
	temp = malloc((PERCENTILES_COUNT_2-1)*sizeof*temp);
	if ( !temp ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* */
	p_matrix = malloc(dataset->rows_count*sizeof*p_matrix);
	if ( !p_matrix ) {
		puts(err_out_of_memory);
		free(temp);
		return NULL;
	}

	/* v1.02 */
	/*
		In the annual time aggregation if the matrix_ref has only 1 row
		the calculation of the Model Efficiency is impossible or it doesn't make sense.
		For this reason in these cases the REF is set at the same percentile selected in the monthly files.
	*/
	if ( (YY_Y == type) && matrix_ref && (1 == matrix_ref->rows_count) )  {
		/* ref remains same of monthly aggregation */
	} else {
		/* get references */
		if ( ! matrix_ref ) {
			*ref = -1;
		} else {
			*ref = get_reference(matrix_ref, dataset, type, author_index, type_index, &error);
			if ( (-1 == *ref) && error ) {
				free(p_matrix);
				free(temp);
				return NULL;
			}
		}
	}

	error = 0;

	/* reset */
	for ( row = 0; row < dataset->rows_count; row++ ) {
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			p_matrix[row].value[percentile] = INVALID_VALUE;
		}
		p_matrix[row].mean = INVALID_VALUE;
		p_matrix[row].std_err = INVALID_VALUE;
	}

	/* compute percentile matrix */
	if ( matrix_ref ) {
		for ( row = 0; row < dataset->rows_count; row++ ) {
			valids_count = 0;
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2-1; percentile++ ) {
				if ( type < HH_C ) {
					temp[percentile] = dataset->percentiles_y[row].value[percentile];
				} else {
					temp[percentile] = dataset->percentiles_c[row].value[percentile];
				}
				/* v1.02 */
				if ( !IS_INVALID_VALUE(temp[percentile]) ) {
					++valids_count;
				}
			}

			/* v1.02 */
			if ( valids_count > g_min_3_perc_count ) {
				for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
					if (	(valids_count < g_min_7_perc_count)
							&& (	
									(25 != percentiles_test_1[percentile])
									&& (50 != percentiles_test_1[percentile])
									&& (75 != percentiles_test_1[percentile])
									) ) {
						continue;
					}
					p_matrix[row].value[percentile] = get_percentile_allowing_invalid(temp, PERCENTILES_COUNT_2-1, percentiles_test_1[percentile], &error);
					/* should no more happens */
					if ( error ) {
						printf("unable to compute %g%% percentile\n", percentiles_test_1[percentile]);
						free(p_matrix);
						free(temp);
						return NULL;
					}
				}
				p_matrix[row].mean = get_mean_allowing_invalid(temp, PERCENTILES_COUNT_2-1);
				if ( IS_INVALID_VALUE(p_matrix[row].mean) ) {
					p_matrix[row].std_err = INVALID_VALUE;
				} else {
					p_matrix[row].std_err = get_standard_deviation_allowing_invalid(temp, PERCENTILES_COUNT_2-1, &error);
					if ( error ) {
						puts(err_out_of_memory);
						free(p_matrix);
						free(temp);
						return NULL;
					}
					p_matrix[row].std_err /= 6.324555320336759; /* sqrt(PERCENTILES_COUNT2-1) */
				}
			}
		}
	}

	/* free memory */
	free(temp);

	/* ok */
	return p_matrix;
}

/* */
static int is_valid_filename(const char *const filename, const int author_index, const int type_index) {
	int i;
	int j;
	char *p;
	char buffer[16];

	/* */
	assert((author_index >= 0) && (author_index < AUTHORS_SUFFIX));
	assert((type_index >= 0) && (type_index < TYPES_SUFFIX));

	/* check for empty string */
	if ( !filename || !filename[0] ) {
		return 0;
	}

	/* */
	j = 0;
	switch ( type_index ) {
		case TYPE_GPP:
			j = GPP_FILENAME_LEN;
		break;

		case TYPE_RECO:
			j = RECO_FILENAME_LEN;
		break;
	}

	/* get filename length */
	for ( i = 0; filename[i]; i++ );

	/* check length */
 	if ( j != i ) {
		return 0;
	}

	/* 3rd char must be a minus */
	if ( '-' != filename[2] ) {
		return 0;
	}

	/* 3rd, 7th, 12th and 15th chars must be an underscore */
	if (  '_' != filename[6] || '_' != filename[11] || '_' != filename[14] ) {
		return 0;
	}

	/* check for digits */
	if ( !isdigit(filename[7]) ) return 0;
	if ( !isdigit(filename[8]) ) return 0;
	if ( !isdigit(filename[9]) ) return 0;
	if ( !isdigit(filename[10]) ) return 0;

	/* check for author and type */
	p = (char *)&filename[12];
	sprintf(buffer, "%s_%s.csv", authors_suffix[author_index], types_suffix[type_index]);
	return ! string_compare_i(p, buffer);
}

/* */
void free_datasets(DATASET *datasets, const int datasets_count) {
	int i;

	/* */
	for ( i = 0; i < datasets_count; i++ ) {
		free_dd(datasets[i].details);
		free(datasets[i].percentiles_y);
		free(datasets[i].percentiles_c);
		free(datasets[i].years);
		free(datasets[i].srs);
		datasets[i].details = NULL;
		datasets[i].percentiles_y = NULL;
		datasets[i].percentiles_c = NULL;
		datasets[i].years = NULL;
		datasets[i].srs = NULL;
	}
	free(datasets);
}

/* */
static char *get_invalid_years(DATASET *const dataset) {
	int i;
	char year[5];
	static char buffer[256]; /* should be enough */

	assert(dataset);

	buffer[0] = '-';
	buffer[1] = '\0';
	for ( i = 0; i < dataset->years_count; ++i ) {
		if ( ! dataset->years[i].exist ) {
			sprintf(year, "%d", dataset->years[i].year);
			strcat(buffer, year);
			strcat(buffer, ", ");
		}
	}

	/* fix last comma ( if any ) */
	for ( i = 0; buffer[i]; ++i );
	if ( i > 1 ) {
		buffer[i-2] = '\0';
	}

	return buffer;
}

/* v1.02 */
static int dump_dataset(const DATASET* const dataset, const char* filename)
{
	int ret = 0; /* defaults to err */
	FILE* f = fopen(filename, "w");
	if ( f ) {
		int i;
		int j;

		if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
			printf(warning_no_setvbuf);
		}
		fputs("INDEX,", f);
		for ( i = 0; i < PERCENTILES_COUNT_2; ++i ) {
			fprintf(f, "%g_c,", percentiles_test_2[i]);
		}
		for ( i = 0; i < PERCENTILES_COUNT_2; ++i ) {
			fprintf(f, "%g_y", percentiles_test_2[i]);
			if ( i < PERCENTILES_COUNT_2-1 ) {
				fputs(",", f);
			}
		}
		fputs("\n", f);

		for ( i = 0; i < dataset->rows_count; ++i ) {
			fprintf(f, "%d,", i);
			for ( j = 0; j < PERCENTILES_COUNT_2; ++j ) {
				fprintf(f, "%g,", dataset->percentiles_c[i].value[j]);
			}
			for ( j = 0; j < PERCENTILES_COUNT_2; ++j ) {
				fprintf(f, "%g", dataset->percentiles_y[i].value[j]);
				if ( j < PERCENTILES_COUNT_2-1 ) {
					fputs(",", f);
				}
			}
			fputs("\n", f);
		}
		fclose(f);

		ret = 1; /* ok */
	}
	return ret;
}

/* v1.02 */
static int compute_dataset(DATASET *const dataset, const int author_index, const int type_index, char* buffer) {
	int i;
	int j;
	int y;
	int z;
	int row;
	int year;
	int rows_count;
	int index;
	int element;
	int assigned;
	int error;
	int percentile;
	int ref_y = -1;							/* mandatory */
	int ref_c = -1;							/* mandatory */
	int temp_rows_count;
	int is_leap;
	int exists;
	int timestamp_column_index;
	int rows_per_day;
	int fatal_err;
	char *p;
	char *token;
	PREC value;
	FILE *f;
	PERCENTILE *matrix_y_aggr;
	PERCENTILE *matrix_c_aggr = NULL;		/* mandatory */
	PERCENTILE *matrix_y_daily;
	PERCENTILE *matrix_c_daily = NULL;		/* mandatory */
	P_MATRIX *p_matrix_y;
	P_MATRIX *p_matrix_c = NULL;			/* mandatory */

	/* v1.02 */
	MATRIX_REF *matrix_ref_y;
	MATRIX_REF *matrix_ref_c = NULL;		/* mandatory */

	TIMESTAMP *t;

	/* v1.021 */
	const char* mef_filters[] = { g_y_filter, g_c_filter };

	const int columns_found_count = PERCENTILES_COUNT_2+PERCENTILES_COUNT_2;
	
	rows_per_day = dataset->hourly ? 24 : 48;

	/* show */
	printf("- %s, %d year%s:\n",	dataset->details->site,
									dataset->years_count,
									((dataset->years_count > 1) ? "s" : "")
	);

	/* alloc memory for percentiles c */
	dataset->percentiles_c = malloc(dataset->rows_count*sizeof*dataset->percentiles_c);
	if ( !dataset->percentiles_c ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* alloc memory for percentiles y */
	dataset->percentiles_y = malloc(dataset->rows_count*sizeof*dataset->percentiles_y);
	if ( !dataset->percentiles_y ) {
		puts(err_out_of_memory);
		free(dataset->percentiles_c);
		return 0;
	}

	/* reset index */
	index = 0;
	/* loop on each year */
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* show */
		printf("- %02d importing %d...", year+1, dataset->years[year].year);
		/* leap year ? */
		is_leap = IS_LEAP_YEAR(dataset->years[year].year);
		/* compute rows count */
		rows_count = is_leap ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_count /= 2;
		}

		/* database exists ? */
		if ( ! dataset->years[year].exist ) {
			/* adding null values */
			for ( i = 0; i < rows_count; i++ ) {
				/* set INVALID_VALUE each value */
				for ( y = 0; y < PERCENTILES_COUNT_2; y++ ) {
					dataset->percentiles_y[index+i].value[y] = INVALID_VALUE;
					dataset->percentiles_c[index+i].value[y] = INVALID_VALUE;
				}
			}
			/* alert */
			puts("ok! (nothing found, null year added)");
		} else {
			/* build-up filename */
			sprintf(buffer, "%s%s_%d_%s_%s.csv",	g_input_path,
													dataset->details->site,
													dataset->years[year].year,
													authors_suffix[author_index],
													types_suffix[type_index]
			);

			/* open file */
			f = fopen(buffer, "r");
			if ( !f ) {
				printf("unable to open %s\n\n", buffer);
				return 0;
			}

			/* get header */
			if ( !get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE) ) {
			    puts("no header found.");
				fclose(f);
				return 0;
			}

			/* get timestamp index */
			timestamp_column_index = get_column_of(buffer, dataset_delimiter, TIMESTAMP_START_STRING);
			if ( -2 == timestamp_column_index ) {
				puts(err_out_of_memory);
				fclose(f);
				return 0;
			} else if ( -1 == timestamp_column_index ) {
				/*  check for timestamp */
				timestamp_column_index = get_column_of(buffer, dataset_delimiter, TIMESTAMP_STRING);
				if ( -2 == timestamp_column_index ) {
					puts(err_out_of_memory);
					fclose(f);
					return 0;
				} else if ( -1 == timestamp_column_index ) {
					puts("no valid header found.");
					fclose(f);
					return 0;
				}
			} else {
				timestamp_column_index = get_column_of(buffer, dataset_delimiter, TIMESTAMP_END_STRING);
				if ( -2 == timestamp_column_index ) {
					puts(err_out_of_memory);
					fclose(f);
					return 0;
				} else if ( -1 == timestamp_column_index ) {
					printf("unable to find %s column\n", TIMESTAMP_END_STRING);
					fclose(f);
					return 0;
				}
			}

			/* loop on each row */
			element = 0;
			while ( get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE) ) {
				/* prevent too many rows */
				if ( element++ == rows_count ) {
					printf("too many rows for %s, %d", dataset->details->site, dataset->years[year].year);
					fclose(f);
					return 0;
				}

				/* reset values */
				for ( i = 0; i < PERCENTILES_COUNT_2; i++ ) {
					dataset->percentiles_c[index+element-1].value[i] = INVALID_VALUE;
					dataset->percentiles_y[index+element-1].value[i] = INVALID_VALUE;
				}
				assigned = 0;
				for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
					/* skip timestamp */
					if ( timestamp_column_index != i ) {
						value = convert_string_to_prec(token, &error);
						if ( error ) {
							printf("unable to convert value %s at row %d, column %d\n", token, element+1, i+1);
							fclose(f);
							return 0;
						}

						/* convert NaN to invalid value */
						if ( value != value ) {
							value = INVALID_VALUE;
						}

						/* */
						if ( i-1 < PERCENTILES_COUNT_2 ) {
							dataset->percentiles_c[index+element-1].value[i-1] = value;
						} else {
							dataset->percentiles_y[index+element-1].value[i-1-PERCENTILES_COUNT_2] = value;
						}
						++assigned;
					}
				}

				/* check assigned */
				if ( assigned != columns_found_count ) {
					printf("expected %d columns not %d\n", columns_found_count, assigned);
					fclose(f);
					return 0;
				}
			}

			/* close file */
			fclose(f);

			/* check rows count */
			if ( element != rows_count ) {
				printf("rows count should be %d not %d\n", rows_count, element);
				return 0;
			}

			/* ok */
			puts("ok!");
		}

		/* update index */
		index += rows_count;
	}

	/* v1.02 */
	if ( g_debug ) {
		char buffer2[64];
		sprintf(buffer, "%s%s", g_output_path, dataset->details->site);
		sprintf(buffer2, "_%d", dataset->years[0].year);
		strcat(buffer, buffer2);
		if ( dataset->years_count > 1 ) {
			sprintf(buffer2, "_%d", dataset->years[dataset->years_count-1].year);
			strcat(buffer, buffer2);
		}
		sprintf(buffer2, "_%s_%s_hh.csv", authors_suffix[author_index], types_suffix[type_index]);
		strcat(buffer, buffer2);
		printf("- debug: saving imported dataset (%s)...", get_filename(buffer));
		if ( ! dump_dataset(dataset, buffer) ) {
			puts("unable to create file!");
		} else {
			puts("ok!");
		}
	}

	/* v1.02 */
	/* load and apply mef filter */
	/* we mimic is_c with i index ;) */
	for ( i = 0; i < 2; ++i ) {
		int start;
		int end;
		int row;
		int ret;
		FILE* f;

		/* reset */
		row = 0;
		ret = 1; /* ok */

		if ( ! mef_filters[i] ) {
			printf("- mef filter file for %c not specified\n", i ? 'c' : 'y');
		} else {
			f = fopen(mef_filters[i], "r");
			/* please note that if file is not found, is not an error! */
			if ( ! f ) {
				printf("- mef filter file for %c not found\n", i ? 'c' : 'y');
			} else {
				char buf2[BUFFER_SIZE] = { 0 };
				char t1[16] = { 0 }; /* we use 16 for padding */
				char t2[16] = { 0 }; /* we use 16 for padding */
				while ( fgets(buf2, BUFFER_SIZE, f) ) {
					/* skip comment and header */
					if ( row > 1 ) {
						if ( sscanf(buf2, "%12[^,],%12[^,],%d,%d", t1, t2, &start, &end) != 4 ) {
							printf("- error: unable to parse \"%s\" at row %d for %s\n", buf2, row+1, buffer);
							ret = 0;
							break;
						}

						if ( (start < 0) || (start > dataset->rows_count) || (end < 0) || (end > dataset->rows_count) || (start > end) ) {
							printf("- error: invalid range for filtering: %d, %d, rows count: %d for %s\n", start, end, dataset->rows_count, buffer); 
							ret = 0;
							break;
						}

						printf("- applying filter for %c from %s to %s (row: %d to %d)\n", i ? 'c' : 'y', t1, t2, start, end); 

						for ( z = start; z < end; z++ ) {
							/* -1 'cause we keep 50 % out */
							for ( j = 0; j < PERCENTILES_COUNT_2 - 1; ++j ) {
								if ( i ) {
									dataset->percentiles_c[z].value[j] = INVALID_VALUE;
								} else {
									dataset->percentiles_y[z].value[j] = INVALID_VALUE;
								}
							}
						}
					}

					++row;
				}
				
				fclose(f);
			}

			if ( ! ret ) {
				return 0;
			}
		}
	}

	if ( g_debug ) {
		char buffer2[64];
		sprintf(buffer, "%s%s", g_output_path, dataset->details->site);
		sprintf(buffer2, "_%d", dataset->years[0].year);
		strcat(buffer, buffer2);
		if ( dataset->years_count > 1 ) {
			sprintf(buffer2, "_%d", dataset->years[dataset->years_count-1].year);
			strcat(buffer, buffer2);
		}
		sprintf(buffer2, "_%s_%s_filtered.csv", authors_suffix[author_index], types_suffix[type_index]);
		strcat(buffer, buffer2);
		printf("- debug: saving dataset filtered by mef (%s)...", get_filename(buffer));
		if ( ! dump_dataset(dataset, buffer) ) {
			puts("unable to create file!");
		} else {
			puts("ok!");
		}
	}

	/* */
	puts("- processing hh...");

	/* v1.02 */
	matrix_ref_y = create_matrix_for_ref(dataset, HH_Y, &fatal_err);
	if ( !matrix_ref_y && fatal_err ) {
		return 0;
	}

	/* v1.02 */
	if ( dataset->years_count >= 3 ) {
		matrix_ref_c = create_matrix_for_ref(dataset, HH_C, &fatal_err);
		if ( !matrix_ref_c && fatal_err ) {
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* process nee_matrix y */
	p_matrix_y = process_matrix(dataset, matrix_ref_y, &ref_y, HH_Y, author_index, type_index);
	if ( !p_matrix_y ) {
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* process nee_matrix c */
	if ( dataset->years_count >= 3 ) {
		p_matrix_c = process_matrix(dataset, matrix_ref_c, &ref_c, HH_C, author_index, type_index);
		if ( !p_matrix_c ) {
			if ( matrix_ref_c )
				free_matrix_ref(matrix_ref_c);
			free(p_matrix_y);
			if ( matrix_ref_y )
				free_matrix_ref(matrix_ref_y);
			return 0;
		}
	}

	/* */
	printf("- ...hh successfully processed!\n- saving hh...");

	/* save output hh */
	sprintf(buffer, output_file_hh, g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create %s\n", buffer);
		if ( dataset->years_count >= 3 ) {
			free(p_matrix_c);
			if ( matrix_ref_c )
				free_matrix_ref(matrix_ref_c);
		}
		free(p_matrix_y);
		if ( matrix_ref_y )
			free_matrix_ref(matrix_ref_y);
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	/* write header hh */
	fprintf(f, header_file_hh, TIMESTAMP_HEADER);
	fprintf(f, output_var_1, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);

	for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
		fprintf(f, "%s_%02g_y", types_suffix[type_index], percentiles_test_1[percentile]);
		if ( percentile < PERCENTILES_COUNT_1-1 ) {
			fputs(",", f);
		}
	}
	if ( dataset->years_count >= 3 ) {
		fprintf(f, output_var_2, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "%s_%02g_c", types_suffix[type_index], percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
	}
	fputs("\n", f);

	/* write values hh */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

		if ( dataset->hourly ) {
			y /= 2;
		}

		exists = dataset->years[i].exist;
		for ( row = 0; row < y; row++ ) {
			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fprintf(f, ",%s,", p);
			/* dtime */
			fprintf(f, "%g,", get_dtime_by_row(row, dataset->hourly));
			if ( exists ) {
				fprintf(f, "%g,%g,%g,%g,",
														/* v1.02 */
														(-1 == ref_y) ? INVALID_VALUE : dataset->percentiles_y[j+row].value[ref_y],
														dataset->percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
														p_matrix_y[j+row].mean,
														p_matrix_y[j+row].std_err
				);
			} else {
				fprintf(f, "%g,%g,%g,%g,",				(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE

				);
			}

			for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
				if ( exists ) {
					fprintf(f, "%g", p_matrix_y[j+row].value[z]);
				} else {
					fprintf(f, "%g", (PREC)INVALID_VALUE);
				}
				if ( z < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}

			if ( dataset->years_count >= 3 ) {
				if ( exists ) {
					fprintf(f, ",%g,%g,%g,%g,",
														/* v1.02 */
														(-1 == ref_c) ? INVALID_VALUE : dataset->percentiles_c[j+row].value[ref_c],
														dataset->percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
														p_matrix_c[j+row].mean,
														p_matrix_c[j+row].std_err
					);
				} else {
					fprintf(f, ",%g,%g,%g,%g,",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
					);
				}
				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g", p_matrix_c[j+row].value[z]);
					} else {
						fprintf(f, "%g", (PREC)INVALID_VALUE);
					}
					if ( z < PERCENTILES_COUNT_1-1 ) {
						fputs(",", f);
					}
				}
			}
			fputs("\n", f);
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* save info hh */
	sprintf(buffer, "%s%s_%s_%s_hh_info.txt", g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if  ( !f ) {
		printf("unable to create %s\n", buffer);
		if ( dataset->years_count >= 3 ) {
			free(p_matrix_c);
			if ( matrix_ref_c )
				free_matrix_ref(matrix_ref_c);
		}
		free(p_matrix_y);
		if ( matrix_ref_y )
			free_matrix_ref(matrix_ref_y);
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	fprintf(f, model_efficiency_info,	types_suffix[type_index],
										types_suffix[type_index],
										types_suffix[type_index]
	);
	if ( dataset->years_count >= 3 ) {
		/* v1.02 */
		fprintf(f, model_efficiency_c_info, types_suffix[type_index], (-1 == ref_c) ? INVALID_VALUE : percentiles_test_2[ref_c]);
		for ( i = 0; i < dataset->years_count; i++ ) {
			/* v1.02 */
			fprintf(f, model_efficiency_y_info, types_suffix[type_index], dataset->years[i].year, (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
		}
	} else {
		/* v1.02 */
		fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
	}
	fclose(f);

	/* free memory */
	free(p_matrix_y);
	if ( dataset->years_count >= 3 ) {
		free(p_matrix_c);
	}

	puts("ok!");

	/*
	*
	*	daily
	*
	*/

	printf("- aggr dd...");

	/* compute daily rows */
	temp_rows_count = dataset->rows_count / rows_per_day;

	/* alloc memory for daily */
	matrix_y_aggr = malloc(temp_rows_count*sizeof*matrix_y_aggr);
	if ( !matrix_y_aggr ) {
		puts(err_out_of_memory);
		if ( (dataset->years_count >= 3) && matrix_ref_c ) {
			free_matrix_ref(matrix_ref_c);
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);	
		}
		return 0;
	}

	if ( dataset->years_count >= 3 ) {
		matrix_c_aggr = malloc(temp_rows_count*sizeof*matrix_c_aggr);
		if ( !matrix_c_aggr ) {
			free(matrix_y_aggr);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* aggr dd */
	index = 0;
	for ( row = 0; row < dataset->rows_count; row += rows_per_day ) {
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
			int has_invalid_y = 0;
			int has_invalid_c = 0;
			matrix_y_aggr[index].value[percentile] = 0.0;
			if ( dataset->years_count >= 3 ) {
				matrix_c_aggr[index].value[percentile] = 0.0;
			}
			for ( i = 0; i < rows_per_day; i++ ) {
				if ( IS_INVALID_VALUE(dataset->percentiles_y[row+i].value[percentile]) ) {
					has_invalid_y = 1;
					break;
				}
				matrix_y_aggr[index].value[percentile] += dataset->percentiles_y[row+i].value[percentile];
			}
			if ( dataset->years_count >= 3 ) {
				for ( i = 0; i < rows_per_day; i++ ) {
					if ( IS_INVALID_VALUE(dataset->percentiles_c[row+i].value[percentile]) ) {
						has_invalid_c = 1;
						break;
					}
					matrix_c_aggr[index].value[percentile] += dataset->percentiles_c[row+i].value[percentile];
				}
			}
			if ( ! has_invalid_y ) {
				matrix_y_aggr[index].value[percentile] /= rows_per_day;
				matrix_y_aggr[index].value[percentile] *= CO2TOC;
			} else {
				matrix_y_aggr[index].value[percentile] = INVALID_VALUE;
			}
			if ( dataset->years_count >= 3 ) {
				if ( ! has_invalid_c ) {
					matrix_c_aggr[index].value[percentile] /= rows_per_day;
					matrix_c_aggr[index].value[percentile] *= CO2TOC;
				} else {
					matrix_c_aggr[index].value[percentile] = INVALID_VALUE;
				}
			}
		}
		++index;
	}
	if ( index != temp_rows_count ) {
		printf("daily rows should be %d not %d", temp_rows_count, index);
		free(matrix_y_aggr);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_aggr);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/*

		update - please note:
		
		matrix_y_aggr, dataset->percentiles_y and eventually matrix_c_aggr and dataset->percentiles_c
		share the same pointers as matrix_y_daily and matrix_c_daily.
		We need daily (DD) aggregation for next aggregation levels (ww, mm, yy)
		so DO NOT free those pointers !!!
	*/
	rows_count = temp_rows_count;
	matrix_y_daily = matrix_y_aggr;
	dataset->rows_count = temp_rows_count;
	free(dataset->percentiles_y);
	dataset->percentiles_y = matrix_y_aggr;
	if ( dataset->years_count >= 3 ) {
		matrix_c_daily = matrix_c_aggr;
		free(dataset->percentiles_c);
		dataset->percentiles_c = matrix_c_aggr;
	}

	puts("ok!");

	/* v1.02 */
	if ( g_debug ) {
		char buffer2[64];
		sprintf(buffer, "%s%s", g_output_path, dataset->details->site);
		sprintf(buffer2, "_%d", dataset->years[0].year);
		strcat(buffer, buffer2);
		if ( dataset->years_count > 1 ) {
			sprintf(buffer2, "_%d", dataset->years[dataset->years_count-1].year);
			strcat(buffer, buffer2);
		}
		sprintf(buffer2, "_%s_%s_dd.csv", authors_suffix[author_index], types_suffix[type_index]);
		strcat(buffer, buffer2);
		printf("- debug: saving aggregated dd dataset (%s)...", get_filename(buffer));		
		if ( ! dump_dataset(dataset, buffer) ) {
			puts("unable to create file!");
		} else {
			puts("ok!");
		}
	}

	/* v1.02 */
	puts("- computing matrices for dd...");

	/* v1.02 */
	if ( matrix_ref_y ) {
		free_matrix_ref(matrix_ref_y);
	}
	matrix_ref_y = create_matrix_for_ref(dataset, DD_Y, &fatal_err);
	if ( !matrix_ref_y && fatal_err ) {
		if ( dataset->years_count >= 3 ) {
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		return 0;
	}

	/* v1.02 */
	if ( dataset->years_count >= 3 ) {
		if ( matrix_ref_c ) {
			free_matrix_ref(matrix_ref_c);
		}
		matrix_ref_c = create_matrix_for_ref(dataset, DD_C, &fatal_err);
		if ( !matrix_ref_c && fatal_err ) {
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* get p_matrix */
	p_matrix_y = process_matrix(dataset, matrix_ref_y, &ref_y, DD_Y, author_index, type_index);
	if ( !p_matrix_y ) {
		puts("- - unable to get p_matrix for daily y");
		if ( dataset->years_count >= 3 ) {
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	if ( dataset->years_count >= 3 ) {
		p_matrix_c = process_matrix(dataset, matrix_ref_c, &ref_c, DD_C, author_index, type_index);
		if ( !p_matrix_c ) {
			puts("- - unable to get p_matrix for daily c");
			free(p_matrix_y);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* */
	printf("- ...dd matrices successfully computed!\n- saving dd...");

	/* save output dd */
	sprintf(buffer, output_file_dd, g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create %s\n", buffer);
		free(p_matrix_y);
		if ( dataset->years_count >= 3 ) {
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			free(p_matrix_c);
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	/* write header dd */
	fprintf(f, header_file_dd, TIMESTAMP_STRING);
	fprintf(f, output_var_1, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);

	for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
		fprintf(f, "%s_%02g_y", types_suffix[type_index], percentiles_test_1[percentile]);
		if ( percentile < PERCENTILES_COUNT_1-1 ) {
			fputs(",", f);
		}
	}
	if ( dataset->years_count >= 3 ) {
		fprintf(f, output_var_2, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "%s_%02g_c", types_suffix[type_index], percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
	}
	fputs("\n", f);

	/* write values dd */
	j = 0;
	element = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

		if ( dataset->hourly ) {
			y /= 2;
		}

		y /= rows_per_day;

		exists = dataset->years[i].exist;
		for ( row = 0; row < y; row++ ) {
			t = timestamp_end_by_row(row*(dataset->hourly ? 24 : 48), dataset->years[i].year, dataset->details->timeres);

			fprintf(f, "%04d%02d%02d,%d,",			t->YYYY,
													t->MM,
													t->DD,
													row+1
			);

			if ( exists ) {
				fprintf(f, "%g,%g,%g,%g,",
													(-1 == ref_y) ? INVALID_VALUE : dataset->percentiles_y[j+row].value[ref_y],
													dataset->percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
													p_matrix_y[j+row].mean,
													p_matrix_y[j+row].std_err
				);
			} else {
				fprintf(f, "%g,%g,%g,%g,",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
				);
			}

			for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
				if ( exists ) {
					fprintf(f, "%g", p_matrix_y[j+row].value[z]);
				} else {
					fprintf(f, "%g", (PREC)INVALID_VALUE);
				}
				if ( z < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}

			if ( dataset->years_count >= 3 ) {
				if ( exists ) {
					fprintf(f, ",%g,%g,%g,%g,",
														(-1 == ref_c) ? INVALID_VALUE : dataset->percentiles_c[j+row].value[ref_c],
														dataset->percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
														p_matrix_c[j+row].mean,
														p_matrix_c[j+row].std_err
					);
				} else {
					fprintf(f, ",%g,%g,%g,%g,",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
					);
				}

				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g", p_matrix_c[j+row].value[z]);
					} else {
						fprintf(f, "%g",(PREC)INVALID_VALUE);
					}
					if ( z < PERCENTILES_COUNT_1-1 ) {
						fputs(",", f);
					}
				}
			}
			fputs("\n", f);
		}
		j += y;

		/* */
		element += ((IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (dataset->hourly ? 2 : 1));
	}

	/* close file */
	fclose(f);

	/* free memory */
	free(p_matrix_y);
	if ( dataset->years_count >= 3 ) {
		free(p_matrix_c);
	}

	/* save info dd */
	sprintf(buffer, "%s%s_%s_%s_dd_info.txt", g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if  ( !f ) {
		printf("unable to create %s\n", buffer);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	fprintf(f, model_efficiency_info,	types_suffix[type_index],
										types_suffix[type_index],
										types_suffix[type_index]
	);
	if ( dataset->years_count >= 3 ) {
		fprintf(f, model_efficiency_c_info, types_suffix[type_index], (-1 == ref_c) ? INVALID_VALUE : percentiles_test_2[ref_c]);
		for ( i = 0; i < dataset->years_count; i++ ) {
			fprintf(f, model_efficiency_y_info, types_suffix[type_index], dataset->years[i].year, (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
		}
	} else {
		fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
	}
	fclose(f);

	puts("ok!");

	/*
	*
	* weekly
	*
	*/

	printf("- aggr ww...");

	/* */
	temp_rows_count = 52 * dataset->years_count;
	matrix_y_aggr = malloc(temp_rows_count*sizeof*matrix_y_aggr);
	if ( !matrix_y_aggr ) {
		puts(err_out_of_memory);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	if ( dataset->years_count >= 3 ) {
		matrix_c_aggr = malloc(temp_rows_count*sizeof*matrix_c_aggr);
		if ( !matrix_c_aggr ) {
			free(matrix_y_daily);
			free(matrix_c_daily);
			puts(err_out_of_memory);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			free(matrix_y_aggr);
			return 0;
		}
	}

	/* compute ww */
	j = 0;
	index = 0;
	element = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		y = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly  ) {
			y /= 2;
		}
		y /= rows_per_day;
		for ( i = 0; i < 51; i++ ) {
			row = i*7;
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				int has_invalid_y = 0;
				int has_invalid_c = 0;
				matrix_y_aggr[index+i].value[percentile] = 0.0;
				if ( dataset->years_count >= 3 ) {
					matrix_c_aggr[index+i].value[percentile] = 0.0;
				}
				for ( j = 0; j < 7; j++ ) {
					if ( IS_INVALID_VALUE(dataset->percentiles_y[element+row+j].value[percentile]) ) {
						has_invalid_y = 1;
						break;
					}
					matrix_y_aggr[index+i].value[percentile] += dataset->percentiles_y[element+row+j].value[percentile];
				}
				if ( dataset->years_count >= 3 ) {
					for ( j = 0; j < 7; j++ ) {
						if ( IS_INVALID_VALUE(dataset->percentiles_c[element+row+j].value[percentile]) ) {
							has_invalid_c = 1;
							break;
						}
						matrix_c_aggr[index+i].value[percentile] += dataset->percentiles_c[element+row+j].value[percentile];
					}
				}

				if ( has_invalid_y ) {
					matrix_y_aggr[index+i].value[percentile] = INVALID_VALUE;
				} else {
					matrix_y_aggr[index+i].value[percentile] /= 7;
				}
				if ( dataset->years_count >= 3 ) {
					if ( has_invalid_c ) {
						matrix_c_aggr[index+i].value[percentile] = INVALID_VALUE;
					} else {
						matrix_c_aggr[index+i].value[percentile] /= 7;
					}
				}
			}
		}
		row += j; /* 51*7 */
		z = y-row;
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
			int has_invalid_y = 0;
			int has_invalid_c = 0;
			matrix_y_aggr[index+i].value[percentile] = 0.0;
			if ( dataset->years_count >= 3 ) {
				matrix_c_aggr[index+i].value[percentile] = 0.0;
			}
			for ( j = 0; j < z; j++ ) {
				if ( IS_INVALID_VALUE(dataset->percentiles_y[element+row+j].value[percentile]) ) {
					has_invalid_y = 1;
					break;
				}
				matrix_y_aggr[index+i].value[percentile] += dataset->percentiles_y[element+row+j].value[percentile];
			}
			if ( dataset->years_count >= 3 ) {
				for ( j = 0; j < z; j++ ) {
					if ( IS_INVALID_VALUE(dataset->percentiles_c[element+row+j].value[percentile]) ) {
						has_invalid_c = 1;
						break;
					}
					matrix_c_aggr[index+i].value[percentile] += dataset->percentiles_c[element+row+j].value[percentile];
				}
			}
			if ( has_invalid_y ) {
				matrix_y_aggr[index+i].value[percentile] = INVALID_VALUE;
			} else {
				matrix_y_aggr[index+i].value[percentile] /= z;
			}
			if ( dataset->years_count >= 3 ) {
				if ( has_invalid_c ) {
					matrix_c_aggr[index+i].value[percentile] = INVALID_VALUE;
				} else {
					matrix_c_aggr[index+i].value[percentile] /= z;
				}
			}
		}

		/* */
		index += 52;
		element += y;
	}

	/* update */
	dataset->rows_count = temp_rows_count;
	dataset->percentiles_y = matrix_y_aggr;
	if ( dataset->years_count >= 3 ) {
		dataset->percentiles_c = matrix_c_aggr;
	}

	puts("ok!");

	/* v1.02 */
	if ( g_debug ) {
		char buffer2[64];
		sprintf(buffer, "%s%s", g_output_path, dataset->details->site);
		sprintf(buffer2, "_%d", dataset->years[0].year);
		strcat(buffer, buffer2);
		if ( dataset->years_count > 1 ) {
			sprintf(buffer2, "_%d", dataset->years[dataset->years_count-1].year);
			strcat(buffer, buffer2);
		}
		sprintf(buffer2, "_%s_%s_ww.csv", authors_suffix[author_index], types_suffix[type_index]);
		strcat(buffer, buffer2);
		printf("- debug: saving aggregated ww dataset (%s)...", get_filename(buffer));
		if ( ! dump_dataset(dataset, buffer) ) {
			puts("unable to create file!");
		} else {
			puts("ok!");
		}
	}

	/* v1.02 */
	puts("- computing matrices for ww...");

	/* v1.02 */
	if ( matrix_ref_y ) {
		free_matrix_ref(matrix_ref_y);
	}
	matrix_ref_y = create_matrix_for_ref(dataset, WW_Y, &fatal_err);
	if ( !matrix_ref_y && fatal_err ) {
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
		}
		return 0;
	}

	/* v1.02 */
	if ( dataset->years_count >= 3 ) {
		if ( matrix_ref_c ) {
			free_matrix_ref(matrix_ref_c);
		}
		matrix_ref_c = create_matrix_for_ref(dataset, WW_C, &fatal_err);
		if ( !matrix_ref_c && fatal_err ) {
			free(matrix_y_daily);
			free(matrix_c_daily);
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* get p_matrix */
	p_matrix_y = process_matrix(dataset, matrix_ref_y, &ref_y, WW_Y, author_index, type_index);
	if ( !p_matrix_y ) {
		puts("unable to get p_matrix for weekly y");
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}
	if ( dataset->years_count >= 3 ) {
		p_matrix_c = process_matrix(dataset, matrix_ref_c, &ref_c, WW_C, author_index, type_index);
		if ( !p_matrix_c ) {
			puts("unable to get p_matrix for weekly c");
			free(p_matrix_y);
			free(matrix_c_daily);
			free(matrix_y_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* */
	printf("- ...ww matrices successfully computed!\n- saving ww...");

	/* save output ww */
	sprintf(buffer, output_file_ww, g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create %s\n", buffer);
		free(p_matrix_y);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(p_matrix_c);
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	/* write header ww */
	fprintf(f, header_file_ww, TIMESTAMP_HEADER);
	fprintf(f, output_var_1, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
	for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
		fprintf(f, "%s_%02g_y", types_suffix[type_index], percentiles_test_1[percentile]);
		if ( percentile < PERCENTILES_COUNT_1-1 ) {
			fputs(",", f);
		}
	}
	if ( dataset->years_count >= 3 ) {
		fprintf(f, output_var_2, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "%s_%02g_c", types_suffix[type_index], percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
	}
	fputs("\n", f);

	/* write values ww */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		exists = dataset->years[i].exist;
		for ( row = 0; row < 52; row++ ) {
			/* write timestamp_start */
			p = timestamp_ww_get_by_row_s(row, dataset->years[i].year, dataset->details->timeres, 1);
			fprintf(f, "%s,", p);
			/* write timestamp_end */
			p = timestamp_ww_get_by_row_s(row, dataset->years[i].year, dataset->details->timeres, 0);
			fprintf(f, "%s,", p);
			/* write week */
			fprintf(f, "%d,", row+1);
			if ( exists ) {
				fprintf(f, "%g,%g,%g,%g,",
													/* v1.02 */
													(-1 == ref_y) ? INVALID_VALUE :  dataset->percentiles_y[j+row].value[ref_y],
													dataset->percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
													p_matrix_y[j+row].mean,
													p_matrix_y[j+row].std_err
				);
			} else {
				fprintf(f, "%g,%g,%g,%g,",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
				);
			}

			for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
				if ( exists ) {
					fprintf(f, "%g", p_matrix_y[j+row].value[z]);
				} else {
					fprintf(f, "%g", (PREC)INVALID_VALUE);
				}
				if ( z < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}

			if ( dataset->years_count >= 3 ) {
				if ( exists ) {
					fprintf(f, ",%g,%g,%g,%g,",
														/* v1.02 */
														(-1 == ref_c) ? INVALID_VALUE : dataset->percentiles_c[j+row].value[ref_c],
														dataset->percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
														p_matrix_c[j+row].mean,
														p_matrix_c[j+row].std_err
					);
				} else {
					fprintf(f, ",%g,%g,%g,%g,",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
					);
				}

				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g", p_matrix_c[j+row].value[z]);
					} else {
						fprintf(f, "%g", (PREC)INVALID_VALUE);
					}
					if ( z < PERCENTILES_COUNT_1-1 ) {
						fputs(",", f);
					}
				}
			}
			fputs("\n", f);
		}
		j += 52;
	}

	/* close file */
	fclose(f);

	/* free memory */
	free(p_matrix_y);
	if ( dataset->years_count >= 3 ) {
		free(p_matrix_c);
	}

	/* save info ww */
	sprintf(buffer, "%s%s_%s_%s_ww_info.txt", g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if  ( !f ) {
		printf("unable to create %s\n", buffer);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	fprintf(f, model_efficiency_info,	types_suffix[type_index],
										types_suffix[type_index],
										types_suffix[type_index]
	);
	if ( dataset->years_count >= 3 ) {
		fprintf(f, model_efficiency_c_info, types_suffix[type_index], (-1 == ref_c) ? INVALID_VALUE : percentiles_test_2[ref_c]);
		for ( i = 0; i < dataset->years_count; i++ ) {
			fprintf(f, model_efficiency_y_info, types_suffix[type_index], dataset->years[i].year, (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
		}
	} else {
		fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
	}
	fclose(f);

	puts("ok!");

	/*
	*
	* monthly
	*
	*/

	/* */
	printf("- aggr mm...");

	/* set daily */
	free(dataset->percentiles_y);
	dataset->percentiles_y = matrix_y_daily;
	if ( dataset->years_count >= 3 ) {
		free(dataset->percentiles_c);
		dataset->percentiles_c = matrix_c_daily;
	}

	temp_rows_count = 12 * dataset->years_count;
	matrix_y_aggr = malloc(temp_rows_count*sizeof*matrix_y_aggr);
	if ( !matrix_y_aggr ) {
		puts(err_out_of_memory);
		if ( dataset->years_count >= 3 ) {
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			free(matrix_c_daily);
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		free(matrix_y_daily);
		return 0;
	}

	if ( dataset->years_count >= 3 ) {
		matrix_c_aggr = malloc(temp_rows_count*sizeof*matrix_c_aggr);
		if ( !matrix_c_aggr ) {
			puts(err_out_of_memory);
			free(matrix_y_aggr);
			free(matrix_y_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			free(matrix_c_daily);
			return 0;
		}
	}

	/* compute mm */
	index = 0;
	year = dataset->years[0].year;
	for ( row = 0; row < rows_count; ) {
		for ( i = 0; i < 12; i++ ) {
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				int has_invalid_y = 0;
				int has_invalid_c = 0;
				matrix_y_aggr[index+i].value[percentile] = 0.0;
				if ( dataset->years_count >= 3 ) {
					matrix_c_aggr[index+i].value[percentile] = 0.0;
				}
				z = days_per_month[i];
				if ( (1 == i) && IS_LEAP_YEAR(year) ) {
					++z;
				}
				for ( j = 0; j < z; j++ ) {
					if ( IS_INVALID_VALUE(dataset->percentiles_y[row+j].value[percentile]) ) {
						has_invalid_y = 1;
						break;
					}
					matrix_y_aggr[index+i].value[percentile] += dataset->percentiles_y[row+j].value[percentile];
				}
				if ( dataset->years_count >= 3 ) {
					for ( j = 0; j < z; j++ ) {
						if ( IS_INVALID_VALUE(dataset->percentiles_c[row+j].value[percentile]) ) {
							has_invalid_c = 1;
							break;
						}
						matrix_c_aggr[index+i].value[percentile] += dataset->percentiles_c[row+j].value[percentile];
					}
				}
				if ( has_invalid_y ) {
					matrix_y_aggr[index+i].value[percentile] = INVALID_VALUE;
				} else {
					matrix_y_aggr[index+i].value[percentile] /= z;
				}
				if ( dataset->years_count >= 3 ) {
					if ( has_invalid_c ) {
						matrix_c_aggr[index+i].value[percentile] = INVALID_VALUE;
					} else {
						matrix_c_aggr[index+i].value[percentile] /= z;
					}
				}
			}

			/* */
			row += z;
		}

		/* */
		++year;
		index += i;
	}

	/* update */
	dataset->rows_count = temp_rows_count;
	dataset->percentiles_y = matrix_y_aggr;
	if ( dataset->years_count >= 3 ) {
		dataset->percentiles_c = matrix_c_aggr;
	}

	puts("ok!");

	/* v1.02 */
	if ( g_debug ) {
		char buffer2[64];
		sprintf(buffer, "%s%s", g_output_path, dataset->details->site);
		sprintf(buffer2, "_%d", dataset->years[0].year);
		strcat(buffer, buffer2);
		if ( dataset->years_count > 1 ) {
			sprintf(buffer2, "_%d", dataset->years[dataset->years_count-1].year);
			strcat(buffer, buffer2);
		}
		sprintf(buffer2, "_%s_%s_mm.csv", authors_suffix[author_index], types_suffix[type_index]);
		strcat(buffer, buffer2);
		printf("- debug: saving aggregated mm dataset (%s)...", get_filename(buffer));
		if ( ! dump_dataset(dataset, buffer) ) {
			puts("unable to create file!");
		} else {
			puts("ok!");
		}
	}

	/* v1.02 */
	puts("- computing matrices for mm...");

	/* v1.02 */
	if ( matrix_ref_y ) {
		free_matrix_ref(matrix_ref_y);
	}
	matrix_ref_y = create_matrix_for_ref(dataset, MM_Y, &fatal_err);
	if ( !matrix_ref_y && fatal_err ) {
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
		}
		return 0;
	}

	/* v1.02 */
	if ( dataset->years_count >= 3 ) {
		if ( matrix_ref_c ) {
			free_matrix_ref(matrix_ref_c);
		}
		matrix_ref_c = create_matrix_for_ref(dataset, MM_C, &fatal_err);
		if ( !matrix_ref_c && fatal_err ) {
			free(matrix_y_daily);
			free(matrix_c_daily);
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}
	
	/* get p_matrix */
	p_matrix_y = process_matrix(dataset, matrix_ref_y, &ref_y, MM_Y, author_index, type_index);
	if ( !p_matrix_y ) {
		puts("unable to get p_matrix for monthly y");
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	if ( dataset->years_count >= 3 ) {
		p_matrix_c = process_matrix(dataset, matrix_ref_c, &ref_c, MM_C, author_index, type_index);
		if ( !p_matrix_c ) {
			puts("unable to get p_matrix for monthly c");
			free(p_matrix_y);
			free(matrix_y_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			free(matrix_c_daily);
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* */
	printf("- ...mm matrices successfully computed!\n- saving mm...");

	/* save output mm */
	sprintf(buffer, output_file_mm, g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create %s\n", buffer);
		free(p_matrix_y);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			free(p_matrix_c);
			free(matrix_c_daily);
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	/* write header mm */
	fprintf(f, header_file_mm, TIMESTAMP_STRING);
	fprintf(f, output_var_1, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
	for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
		fprintf(f, "%s_%02g_y", types_suffix[type_index], percentiles_test_1[percentile]);
		if ( percentile < PERCENTILES_COUNT_1-1 ) {
			fputs(",", f);
		}
	}
	if ( dataset->years_count >= 3 ) {
		fprintf(f, output_var_2, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "%s_%02g_c", types_suffix[type_index], percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
	}
	fputs("\n", f);

	/* write values mm */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		exists = dataset->years[i].exist;
		for ( row = 0; row < 12; row++ ) {
			fprintf(f, "%04d%02d,",				year,
												row+1
			);

			if ( exists ) {
				fprintf(f, "%g,%g,%g,%g,",
													/* v1.02 */
													(-1 == ref_y) ? INVALID_VALUE : dataset->percentiles_y[j+row].value[ref_y],
													dataset->percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
													p_matrix_y[j+row].mean,
													p_matrix_y[j+row].std_err
				);
			} else {
				fprintf(f, "%g,%g,%g,%g,",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
				);
			}

			for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
				if ( exists ) {
					fprintf(f, "%g", p_matrix_y[j+row].value[z]);
				} else {
					fprintf(f, "%g", (PREC)INVALID_VALUE);
				}
				if ( z < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}
			if ( dataset->years_count >= 3 ) {
				if ( exists ) {
					fprintf(f, ",%g,%g,%g,%g,",
													/* v1.02 */
													(-1 == ref_c) ? INVALID_VALUE : dataset->percentiles_c[j+row].value[ref_c],
													dataset->percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
													p_matrix_c[j+row].mean,
													p_matrix_c[j+row].std_err
					);
				} else {
					fprintf(f, ",%g,%g,%g,%g,",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
					);
				}
				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g", p_matrix_c[j+row].value[z]);
					} else {
						fprintf(f, "%g", (PREC)INVALID_VALUE);
					}
					if ( z < PERCENTILES_COUNT_1-1 ) {
						fputs(",", f);
					}
				}
			}
			fputs("\n", f);
		}
		j += 12;
	}

	/* close file */
	fclose(f);

	/* free memory */
	free(p_matrix_y);
	if ( dataset->years_count >= 3 ) {
		free(p_matrix_c);
	}

	/* save info mm */
	sprintf(buffer, "%s%s_%s_%s_mm_info.txt", g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if  ( !f ) {
		printf("unable to create %s\n", buffer);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	fprintf(f, model_efficiency_info,	types_suffix[type_index],
										types_suffix[type_index],
										types_suffix[type_index]
	);
	if ( dataset->years_count >= 3 ) {
		fprintf(f, model_efficiency_c_info, types_suffix[type_index], (-1 == ref_c) ? INVALID_VALUE : percentiles_test_2[ref_c]);
		for ( i = 0; i < dataset->years_count; i++ ) {
			fprintf(f, model_efficiency_y_info, types_suffix[type_index], dataset->years[i].year, (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
		}
	} else {
		fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
	}
	fclose(f);

	puts("ok!");

	/*
	*
	* yearly
	*
	*/

	/* */
	printf("- aggr yy...");

	/* set daily */
	free(dataset->percentiles_y);
	dataset->percentiles_y = matrix_y_daily;
	if ( dataset->years_count >= 3 ) {
		free(dataset->percentiles_c);
		dataset->percentiles_c = matrix_c_daily;
	}

	matrix_y_aggr = malloc(dataset->years_count*sizeof*matrix_y_aggr);
	if ( !matrix_y_aggr ) {
		puts(err_out_of_memory);
		if ( dataset->years_count >= 3 ) {
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	if ( dataset->years_count >= 3 ) {
		matrix_c_aggr = malloc(dataset->years_count*sizeof*matrix_c_aggr);
		if ( !matrix_c_aggr ) {
			puts(err_out_of_memory);
			free(matrix_y_aggr);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* compute yy */
	index = 0;
	year = dataset->years[0].year;
	for ( row = 0; row < rows_count; ) {
		y = IS_LEAP_YEAR(year) ? 366 : 365;
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
			int has_invalid_y = 0;
			int has_invalid_c = 0;
			matrix_y_aggr[index].value[percentile] = 0.0;
			if ( dataset->years_count >= 3 ) {
				matrix_c_aggr[index].value[percentile] = 0.0;
			}
			for ( j = 0; j < y; j++ ) {
				if ( IS_INVALID_VALUE(dataset->percentiles_y[row+j].value[percentile]) ) {
					has_invalid_y = 1;
					break;
				}
				matrix_y_aggr[index].value[percentile] += dataset->percentiles_y[row+j].value[percentile];
			}
			if ( dataset->years_count >= 3 ) {
				for ( j = 0; j < y; j++ ) {
					if ( IS_INVALID_VALUE(dataset->percentiles_c[row+j].value[percentile]) ) {
						has_invalid_c = 1;
						break;
					}
					matrix_c_aggr[index].value[percentile] += dataset->percentiles_c[row+j].value[percentile];
				}
			}
			if ( has_invalid_y ) {
				matrix_y_aggr[index].value[percentile] = INVALID_VALUE;
			}
			if ( dataset->years_count >= 3 ) {
				if ( has_invalid_c ) {
					matrix_c_aggr[index].value[percentile] = INVALID_VALUE;
				}
			}
		}

		/* */
		row += y;
		++year;
		++index;
	}

	/* update */
	dataset->rows_count = dataset->years_count;
	dataset->percentiles_y = matrix_y_aggr;
	if ( dataset->years_count >= 3 ) {
		dataset->percentiles_c = matrix_c_aggr;
	}

	puts("ok!");

	/* v1.02 */
	if ( g_debug ) {
		char buffer2[64];
		sprintf(buffer, "%s%s", g_output_path, dataset->details->site);
		sprintf(buffer2, "_%d", dataset->years[0].year);
		strcat(buffer, buffer2);
		if ( dataset->years_count > 1 ) {
			sprintf(buffer2, "_%d", dataset->years[dataset->years_count-1].year);
			strcat(buffer, buffer2);
		}
		sprintf(buffer2, "_%s_%s_yy.csv", authors_suffix[author_index], types_suffix[type_index]);
		strcat(buffer, buffer2);
		printf("- debug: saving aggregated yy dataset (%s)...", get_filename(buffer));
		if ( ! dump_dataset(dataset, buffer) ) {
			puts("unable to create file!");
		} else {
			puts("ok!");
		}
	}

	/* v1.02 */
	puts("- computing matrices for yy...");

	/* v1.02 */
	if ( matrix_ref_y ) {
		free_matrix_ref(matrix_ref_y);
	}
	matrix_ref_y = create_matrix_for_ref(dataset, YY_Y, &fatal_err);
	if ( !matrix_ref_y && fatal_err ) {
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
		}
		return 0;
	}

	/* v1.02 */
	if ( dataset->years_count >= 3 ) {
		if ( matrix_ref_c ) {
			free_matrix_ref(matrix_ref_c);
		}
		matrix_ref_c = create_matrix_for_ref(dataset, YY_C, &fatal_err);
		if ( !matrix_ref_c && fatal_err ) {
			free(matrix_y_daily);
			free(matrix_c_daily);
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			return 0;
		}
	}

	/* get p_matrix */
	p_matrix_y = process_matrix(dataset, matrix_ref_y, &ref_y, YY_Y, author_index, type_index);
	if ( !p_matrix_y ) {
		puts("unable to get p_matrix for yearly y");
		free(matrix_y_daily);
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		return 0;
	}
	if ( dataset->years_count >= 3 ) {
		p_matrix_c = process_matrix(dataset, matrix_ref_c, &ref_c, YY_C, author_index, type_index);
		if ( !p_matrix_c ) {
			puts("unable to get p_matrix for yearly c");
			free(p_matrix_y);
			free(matrix_y_daily);
			if ( matrix_ref_y ) {
				free_matrix_ref(matrix_ref_y);
			}
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
			return 0;
		}
	}

	/* */
	printf("- ...yy matrices successfully computed!\n- saving yy...");

	/* save output yy */
	sprintf(buffer, output_file_yy, g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create %s\n", buffer);
		free(p_matrix_y);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(p_matrix_c);
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	/* write header yy */
	fprintf(f, header_file_yy, TIMESTAMP_STRING);
	fprintf(f, output_var_1, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
	for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
		fprintf(f, "%s_%02g_y", types_suffix[type_index], percentiles_test_1[percentile]);
		if ( percentile < PERCENTILES_COUNT_1-1 ) {
			fputs(",", f);
		}
	}
	if ( dataset->years_count >= 3 ) {
		fprintf(f, output_var_2, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "%s_%02g_c", types_suffix[type_index], percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
	}
	fputs("\n", f);

	/* write values yy */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		exists = dataset->years[i].exist;
		fprintf(f, "%d,", year);
		if ( exists ) {
			fprintf(f, "%g,%g,%g,%g,",
											/* v1.02 */
											(-1 == ref_y) ? INVALID_VALUE : dataset->percentiles_y[i].value[ref_y],
											dataset->percentiles_y[i].value[PERCENTILES_COUNT_2-1],
											p_matrix_y[i].mean,
											p_matrix_y[i].std_err
			);
		} else {
			fprintf(f, "%g,%g,%g,%g,",
											(PREC)INVALID_VALUE,
											(PREC)INVALID_VALUE,
											(PREC)INVALID_VALUE,
											(PREC)INVALID_VALUE
			);
		}
		for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
			if ( exists ) {
				fprintf(f, "%g", p_matrix_y[i].value[z]);
			} else {
				fprintf(f, "%g", (PREC)INVALID_VALUE);
			}
			if ( z < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
		}
		if ( dataset->years_count >= 3 ) {
			if ( exists ) {
				fprintf(f, ",%g,%g,%g,%g,",
													/* v1.02 */
													(-1 == ref_c) ? INVALID_VALUE : dataset->percentiles_c[i].value[ref_c],
													dataset->percentiles_c[i].value[PERCENTILES_COUNT_2-1],
													p_matrix_c[i].mean,
													p_matrix_c[i].std_err
				);
			} else {
				fprintf(f, ",%g,%g,%g,%g,",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
				);
			}

			for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
				if ( exists ) {
					fprintf(f, "%g", p_matrix_c[i].value[z]);
				} else {
					fprintf(f, "%g", (PREC)INVALID_VALUE);
				}
				if ( z < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}
		}
		fputs("\n", f);
	}

	/* close file */
	fclose(f);

	/* free memory */
	free(p_matrix_y);
	if ( dataset->years_count >= 3 ) {
		free(p_matrix_c);
	}

	/* save info yy */
	sprintf(buffer, "%s%s_%s_%s_yy_info.txt", g_output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index]);
	f = fopen(buffer, "w");
	if  ( !f ) {
		printf("unable to create %s\n", buffer);
		free(matrix_y_daily);
		if ( dataset->years_count >= 3 ) {
			free(matrix_c_daily);
			if ( matrix_ref_c ) {
				free_matrix_ref(matrix_ref_c);
			}
		}
		if ( matrix_ref_y ) {
			free_matrix_ref(matrix_ref_y);
		}
		return 0;
	}

	/* v1.02 */
	if ( g_file_buf && setvbuf(f, g_file_buf, _IOFBF, g_file_buf_size) ) {
		printf(warning_no_setvbuf);
	}

	fprintf(f, model_efficiency_info,	types_suffix[type_index],
										types_suffix[type_index],
										types_suffix[type_index]
	);
	if ( dataset->years_count >= 3 ) {
		fprintf(f, model_efficiency_c_info, types_suffix[type_index], (-1 == ref_c) ? INVALID_VALUE : percentiles_test_2[ref_c]);
		for ( i = 0; i < dataset->years_count; i++ ) {
			fprintf(f, model_efficiency_y_info, types_suffix[type_index], dataset->years[i].year, (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
		}
	} else {
		fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], (-1 == ref_y) ? INVALID_VALUE : percentiles_test_2[ref_y]);
	}
	fclose(f);

	/* */
	puts("ok!\n");

	free(matrix_y_daily);
	if ( matrix_ref_y ) {
		free_matrix_ref(matrix_ref_y);
	}
	if ( dataset->years_count >= 3 ) {
		free(matrix_c_daily);
		if ( matrix_ref_c ) {
			free_matrix_ref(matrix_ref_c);
		}
	}

	return 1;
}

/* */
int compute_datasets(DATASET *const datasets, const int datasets_count, const int author_index, const int type_index) {
	char *buffer;
	int dataset;
	
	/* allocate memory for buffer */
	buffer = malloc(HUGE_BUFFER_SIZE*sizeof*buffer);
	if ( !buffer ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop on each dataset */
	for ( dataset = 0; dataset < datasets_count; dataset++ ) {
		compute_dataset(&datasets[dataset], author_index, type_index, buffer);
	}

	/* free memory */
	free(buffer);

	/* ok */
	return 1;
}

/* */
DATASET *get_datasets(const char *const path, const int author_index, const int type_index, int *const datasets_count) {
	int i;
	int y;
	int gap;
	int error;
	int assigned;
	int file_index;
	int files_found_count;
	int year;
	char year_c[YEAR_LEN];
	char buffer[FILENAME_SIZE];
	FILES *files_found;
	YEAR *years_no_leak;
	DATASET *datasets;
	DATASET *datasets_no_leak;
	DD *details;
	FILE *f;

	/* check parameters */
	assert(path && datasets_count);

	/* reset */
	datasets = NULL;
	*datasets_count = 0;
	details = NULL;

	/* scan path */
	sprintf(buffer, "*_%s_%s.csv", authors_suffix[author_index], types_suffix[type_index]);
	files_found = get_files(path, buffer, &files_found_count, &error);
	if ( error || !files_found_count ) {
		/* v1.02 */
		/*puts("no files found!");*/
		return NULL;
	}

	/* alloc memory for details */
	details = alloc_dd();
	if ( !details ) {
		return NULL;
	}

	/* loop on each files found */
	for ( file_index = 0; file_index < files_found_count; file_index++ ) {
		/* check filename */
		if ( !is_valid_filename(files_found[file_index].list[0].name, author_index, type_index) ) {
			continue;
		}

		/* get site */
		strncpy(details->site, files_found[file_index].list[0].name, SITE_LEN - 1);
		details->site[SITE_LEN - 1] = '\0';

		/* get year */
		strncpy(year_c, files_found[file_index].list[0].name+SITE_LEN, YEAR_LEN - 1);
		year_c[YEAR_LEN-1] = '\0';

		/* convert year string to int */
		year = convert_string_to_int(year_c, &error);
		if ( error ) {
			printf("unable to convert year for %s\n\n", files_found[file_index].list[0].name);
			free_dd(details);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}
		details->year = year;

		/* get timeres */
		f = fopen(files_found[file_index].list[0].fullpath, "r");
		if ( !f ) {
			printf("unable to get rows count for %s\n\n", files_found[file_index].list[0].name);
			free_dd(details);
			free_datasets(datasets, *datasets_count);
			return NULL;

		}

		i = get_rows_count_from_file(f);
		if ( !i ) {
			printf("no valid rows found for %s\n\n", files_found[file_index].list[0].name);
			fclose(f);
			free_dd(details);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}
		fclose(f);

		/* remove header */
		--i;
		if ( (LEAP_YEAR_ROWS == i) || (YEAR_ROWS == i) ) {
			details->timeres = HALFHOURLY_TIMERES;
		} else if ( (LEAP_YEAR_ROWS/2 == i) || (YEAR_ROWS/2 == i) ) {
			details->timeres = HOURLY_TIMERES;
		} else {
			printf("no valid timeres found for %s\n\n", files_found[file_index].list[0].name);
			free_dd(details);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}

		/* check if site is already assigned */
		assigned = 0;
		for ( i = 0; i < *datasets_count; i++ ) {
			if ( ! string_compare_i(datasets[i].details->site, details->site) ) {
				assigned = 1;
				break;
			}
		}

		/* not assigned ? add site! */
		if ( !assigned ) {
			datasets_no_leak = realloc(datasets, ++*datasets_count*sizeof*datasets_no_leak);
			if ( !datasets_no_leak ) {
				puts(err_out_of_memory);
				free_dd(details);
				free_datasets(datasets, *datasets_count);
				return NULL;

			}
			/* */
			datasets = datasets_no_leak;
			datasets[*datasets_count-1].percentiles_y = NULL;
			datasets[*datasets_count-1].percentiles_c = NULL;
			datasets[*datasets_count-1].rows_count = 0;
			datasets[*datasets_count-1].years = NULL;
			datasets[*datasets_count-1].years_count = 0;
			datasets[*datasets_count-1].details = alloc_dd();
			datasets[*datasets_count-1].srs = NULL;
			if ( !datasets[*datasets_count-1].details ) {
				free_dd(details);
				free_datasets(datasets, *datasets_count);
				return NULL;
			}
			strcpy(datasets[*datasets_count-1].details->site, details->site);
			datasets[*datasets_count-1].details->year = details->year;
			datasets[*datasets_count-1].details->timeres = details->timeres;

			/* assign timeres */
			datasets[*datasets_count-1].hourly = (HOURLY_TIMERES == details->timeres);

			/* do the trick ;) */
			i = *datasets_count-1;
		} else {
			/* check timeres */
			if ( details->timeres != datasets[i].details->timeres ) {
				puts("Different time resolution between years|");
				free_dd(details);
				free_files(files_found, files_found_count);
				free_datasets(datasets, *datasets_count);
				return NULL;
			}
		}

		/* check if year is already assigned...? */
		for ( y = 0; y < datasets[i].years_count; y++ ) {
			if ( details->year == datasets[i].years[y].year ) {
				puts(err_out_of_memory);
				free_dd(details);
				free_files(files_found, files_found_count);
				free_datasets(datasets, *datasets_count);
				return NULL;
			}
		}

		/* add year */
		years_no_leak = realloc(datasets[i].years, ++datasets[i].years_count*sizeof*years_no_leak);
		if ( !years_no_leak ) {
			puts(err_out_of_memory);
			free_dd(details);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}

		/* assign year and compute rows count */
		datasets[i].years = years_no_leak;
		datasets[i].years[datasets[i].years_count-1].year = details->year;
		datasets[i].years[datasets[i].years_count-1].exist = 1;
		datasets[i].rows_count += ((IS_LEAP_YEAR(details->year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (datasets[i].hourly  ? 2 : 1));
	}

	/* free memory */
	free_dd(details);

	/* free memory */
	free_files(files_found, files_found_count);

	/* sort per year */
	for ( i = 0 ; i < *datasets_count; i++ ) {
		while ( 1 ) {
			qsort(datasets[i].years,  datasets[i].years_count, sizeof*datasets[i].years, compare_int);
			/* check for gap */
			gap = 0;
			for ( y = 0; y < datasets[i].years_count-1; y++ ) {
				if ( datasets[i].years[y+1].year - datasets[i].years[y].year > 1 ) {
					gap = 1;
					/* add year */
					years_no_leak = realloc(datasets[i].years, ++datasets[i].years_count*sizeof*years_no_leak);
					if ( !years_no_leak ) {
						puts(err_out_of_memory);
						free_datasets(datasets, *datasets_count);
						return NULL;
					}

					datasets[i].years = years_no_leak;
					datasets[i].years[datasets[i].years_count-1].year = datasets[i].years[y].year + 1;
					datasets[i].years[datasets[i].years_count-1].exist = 0;
					datasets[i].rows_count += ((IS_LEAP_YEAR(datasets[i].years[y].year + 1) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (datasets[i].hourly  ? 2 : 1));
					break;
				}
			}

			if ( !gap ) {
				break;
			}
		}
	}

	/* ok */
	return datasets;
}
