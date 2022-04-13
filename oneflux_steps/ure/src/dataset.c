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
#include "info_reco_sr.h"

/* externs */
extern char *input_path;
extern char *output_path;
extern const char *types_suffix[TYPES_SUFFIX];
extern const char *authors_suffix[AUTHORS_SUFFIX];

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


/* using Model Efficiency, on error returns -1 */
int get_reference(const DATASET *const dataset, const int is_c, const int type, const int author_index, const int type_index) {
	int i;
	int j;
	int row;
	int column;
	int mean_count;
	int square_count;
	int percentiles_rows_count;
	int percentiles_columns_count;
	int shrinked;
	PREC mean;
	PREC square;
	PREC variance;
	PREC sum;
	ME *mes;
	ME *percentiles;
	PREC *mess;
	char buffer[256];
	int bad_columns[PERCENTILES_COUNT_2-1];
	FILE *f;

	/* */
	percentiles_columns_count = PERCENTILES_COUNT_2-1;
	shrinked = 0;

	/* alloc memory */
	mes = malloc(percentiles_columns_count*sizeof*mes);
	if ( !mes ) {
		puts(err_out_of_memory);
		return -1;
	}

	/* alloc memory */
	mess = malloc(percentiles_columns_count*sizeof*mess);
	if ( !mess ) {
		puts(err_out_of_memory);
		free(mes);
		return -1;
	}

	/* alloc memory */
	percentiles_rows_count = dataset->rows_count;
	percentiles = malloc(percentiles_rows_count*sizeof*percentiles);
	if ( ! percentiles ) {
		puts(err_out_of_memory);
		free(mess);
		free(mes);
		return -1;
	}

	/* reset */
	for ( i = 0; i < percentiles_columns_count; i++ ) {
		for ( j = 0; j < percentiles_columns_count; j++ ) {
			mes[i].value[j] = INVALID_VALUE;
		}
		bad_columns[i] = 0;
	}

	/* fill percentiles struct */
	row = 0;
	for ( i = 0; i < percentiles_rows_count; ++i ) {
		column = 0; /* keep track of invalid column count */
		for ( j = 0; j < percentiles_columns_count; ++j ) {
			if ( is_c ) {
				percentiles[row].value[j] = dataset->percentiles_c[i].value[j];
			} else {
				percentiles[row].value[j] = dataset->percentiles_y[i].value[j];
			}
			if ( IS_INVALID_VALUE(percentiles[row].value[j]) ) {
				++column;
			}
		}
		if ( column != percentiles_columns_count ) {
			++row;
		}
	}
	percentiles_rows_count = row;

	/* scan bad columns */
	for ( i = 0; i < percentiles_columns_count; ++i ) {
		for ( j = 0; j < percentiles_rows_count; ++j ) {
			if ( IS_INVALID_VALUE(percentiles[j].value[i]) ) {
				bad_columns[i] = 1;
				break;
			}
		}
	}

	/* count "clean" columns */
	j = 0;
	for ( i = 0; i < percentiles_columns_count; ++i ) {
		if ( ! bad_columns[i] ) {
			++j;
			column = i;
		}
	}
	if ( ! j ) {
		/* all columns has a -9999 at least, exit */
		puts(err_bad_dataset);
		free(percentiles);
		free(mess);
		free(mes);
		return -1;
	} else if ( 1 == j ) {
		/* only one column valid! we've ref! */
		free(percentiles);
		free(mess);
		free(mes);
		return column;
	} else if ( j != percentiles_columns_count ) {
		column = 0;
		for ( j = 0; j < percentiles_columns_count; ++j ) {
			if (  bad_columns[j] ) {
				continue;
			}
			if ( column != j ) {
				for ( i = 0; i < percentiles_rows_count; i++ ) {
					percentiles[i].value[column] = percentiles[i].value[j];
				}
			}
			++column;
		}
		percentiles_columns_count = column;
		shrinked = 1;
	}
	for ( column = 0; column < percentiles_columns_count; column++ ) {
		mean = 0.0;
		mean_count = 0;
		for ( row = 0; row < percentiles_rows_count; row++ ) {
			mean += percentiles[row].value[column];
			++mean_count;
		}
		if ( mean_count ) {
			mean /= mean_count;
		}
		square = 0.0;
		square_count = 0;
		for ( row = 0; row < percentiles_rows_count; row++ ) {
			square += SQUARE(percentiles[row].value[column] - mean);
			++square_count;
		}
		if ( square_count ) {
			variance = square / square_count;
		} else {
			printf(err_unable_compute_variance, column);
			free(percentiles);
			free(mess);
			free(mes);
			return -1;
		}

		for ( i = 0; i < percentiles_columns_count; i++ ) {
			sum = 0.0;
			for ( j = 0; j < percentiles_rows_count; j++ ) {
				sum += (percentiles[j].value[column] - percentiles[j].value[i])
						* (percentiles[j].value[column] - percentiles[j].value[i]);
			}
			sum /= percentiles_rows_count;
			sum /= variance;

			mes[column].value[i] = 1 - sum;
		}
	}

	/* get selected */
	for ( column = 0; column < percentiles_columns_count; ++column ) {
		mess[column] = 0.0;
		for ( row = 0; row < percentiles_columns_count; ++row ) {
			mess[column] += mes[row].value[column];
		}
	}

	column = 0;
	sum = mess[0]; /* used as start point */
	for ( i = 0; i < percentiles_columns_count; i++ ) {
		if ( mess[i] > sum ) {
			sum = mess[i];
			column = i;
		}
	}
	if ( shrinked ) {
		j = 0;
		row = -1; /* used as index */
		for ( i = 0; i < PERCENTILES_COUNT_2-1; ++i ) { /* must be PERCENTILES_COUNT_2-1 not percentiles_columns_count */
			if ( ! bad_columns[i] ) {
				if ( ++row == column ) {
					column = i;
					break;
				}
			}
		}
	}

	/* save mess */
	if ( dataset->years_count > 1 ) {
		sprintf(buffer, "%s%s_%s_%s_mef_matrix_%s_%d_%d.csv", output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index], types[type], dataset->years[0].year, dataset->years[dataset->years_count-1].year);
	} else {
		sprintf(buffer, "%s%s_%s_%s_mef_matrix_%s_%d.csv", output_path, dataset->details->site, authors_suffix[author_index], types_suffix[type_index], types[type], dataset->years[0].year);
	}
	f = fopen(buffer, "w");
	if ( f ) {
		for ( i = 0; i < PERCENTILES_COUNT_2-1; i++ ) {
			if ( ! bad_columns[i] ) {				/* must be PERCENTILES_COUNT_2-1 not percentiles_columns_count */
				fprintf(f, "%g", percentiles_test_2[i]);
				if ( i < percentiles_columns_count-1 ) {
					fputs(",", f);
				}
			}
		}
		fputs("\n", f);
		for ( i = 0; i < percentiles_columns_count; i++ ) {
			for ( j = 0; j < percentiles_columns_count; j++ ) {
				fprintf(f, "%g", mes[i].value[j]);
				if ( j < percentiles_columns_count-1 ) {
					fputs(",", f);
				}
			}
			fputs("\n", f);
		}
		fclose(f);
	} else {
		printf("unable to save %s for debug purposes.\n", buffer);
	}

	/* free memory */
	free(percentiles);
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

	/* get mean */
	mean = get_mean(valid_values, valid_count);
	if ( IS_INVALID_VALUE(mean) ) {
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

/* */
P_MATRIX *process_matrix(const DATASET *const dataset, const int is_c, int *ref, const int type, const int author_index, const int type_index) {
	int row;
	int percentile;
	int error;
	PREC *temp;
	P_MATRIX *p_matrix;

	/* check paramenters */
	assert(dataset && ref);

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

	/*
		In the annual time aggregation if the site has only 1 year
		the calculation of the Model Efficiency is impossible or it doesn't make sense.
		For this reason in these cases the REF is set at the same percentile selected in the monthly files.
	*/
	if ( (YY_Y == type) && (1 == dataset->years_count) )  {
		/* ref remains same of monthly aggregation */
	} else {
		/* get references */
		*ref = get_reference(dataset, is_c, type, author_index, type_index);
		if ( -1 == *ref ) {
			free(p_matrix);
			free(temp);
			return NULL;
		}
	}

	/* compute percentile matrix */
	for ( row = 0; row < dataset->rows_count; row++ ) {
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2-1; percentile++ ) {
			if ( is_c ) {
				temp[percentile] = dataset->percentiles_c[row].value[percentile];
			} else {
				temp[percentile] = dataset->percentiles_y[row].value[percentile];
			}
		}
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			p_matrix[row].value[percentile] = get_percentile_allowing_invalid(temp, PERCENTILES_COUNT_2-1, percentiles_test_1[percentile], &error);
			if ( error ) {
				printf("unable to compute %g%% percentile.", percentiles_test_1[percentile]);
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
static const char *get_info(const int author_index, const int type_index, const int timeres) {
	int index;
	static const char *infos[] = { /* DO NOT CHANGE THIS ORDER */
									info_gpp_nt_hh
									, info_gpp_nt_dd
									, info_gpp_nt_ww
									, info_gpp_nt_mm
									, info_gpp_nt_yy
									, info_gpp_dt_hh
									, info_gpp_dt_dd
									, info_gpp_dt_ww
									, info_gpp_dt_mm
									, info_gpp_dt_yy
									, info_reco_nt_hh
									, info_reco_nt_dd
									, info_reco_nt_ww
									, info_reco_nt_mm
									, info_reco_nt_yy
									, info_reco_dt_hh
									, info_reco_dt_dd
									, info_reco_dt_ww
									, info_reco_dt_mm
									, info_reco_dt_yy
									, info_reco_sr 
	};

	assert((author_index >= 0) && (author_index < AUTHORS_SUFFIX));
	assert((type_index >= 0) && (type_index < TYPES_SUFFIX));
	assert((timeres >=0) && (timeres < TIMERES));
	if ( (AUTHOR_SR == author_index) && (TYPE_GPP == type_index) ) {
		/* SR can be used only with RECO type not GPP */
		assert(0);
	}

	index = (type_index * TYPES_SUFFIX * TIMERES) + (author_index * TIMERES) + timeres;

	/* fix for sr */
	if ( index > SIZEOF_ARRAY(infos) ) {
		index = SIZEOF_ARRAY(infos) - 1;
	}

	return infos[index];
}

/* */
static char *get_invalid_years(DATASET *const dataset) {
	int i;
	char year[5];
	static char buffer[256]; /* should be enough */

	assert(dataset);

	buffer[0] = '-';
	buffer[1] = '/0';
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


/* */
int compute_datasets(DATASET *const datasets, const int datasets_count, const int author_index, const int type_index) {
	int i;
	int j;
	int y;
	int z;
	int row;
	int dataset;
	int year;
	int rows_count;
	int index;
	int element;
	int assigned;
	int error;
	int percentile;
	int ref_y;
	int ref_c;
	int temp_rows_count;
	int is_leap;
	int exists;
	int valids_y_count;
	int valids_c_count;
	int timestamp_column_index;
	int rows_per_day;
	char *buffer;
	char *p;
	char *token;
	PREC value;
	int start;
	int end;
	PREC startValue;
	PREC endValue;
	FILE *f;
	PERCENTILE *matrix_y_daily;
	PERCENTILE *matrix_y_temp;
	PERCENTILE *matrix_c_daily;				/* mandatory */
	PERCENTILE *matrix_c_temp = NULL;		/* mandatory */
	P_MATRIX *p_matrix_y;
	P_MATRIX *p_matrix_c = NULL;			/* mandatory */
	TIMESTAMP *t;

	const int columns_founded_count = PERCENTILES_COUNT_2+PERCENTILES_COUNT_2;

	/* allocate memory for buffer */
	buffer = malloc(HUGE_BUFFER_SIZE*sizeof*buffer);
	if ( !buffer ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop on each dataset */
	for ( dataset = 0; dataset < datasets_count; dataset++ ) {
		rows_per_day = datasets[dataset].hourly ? 24 : 48;

		/* show */
		printf("- %s, %d year%s:\n",	datasets[dataset].details->site,
										datasets[dataset].years_count,
										((datasets[dataset].years_count > 1) ? "s" : "")
		);

		/* alloc memory for percentiles c */
		datasets[dataset].percentiles_c = malloc(datasets[dataset].rows_count*sizeof*datasets[dataset].percentiles_c);
		if ( !datasets[dataset].percentiles_c ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}

		/* alloc memory for percentiles y */
		datasets[dataset].percentiles_y = malloc(datasets[dataset].rows_count*sizeof*datasets[dataset].percentiles_y);
		if ( !datasets[dataset].percentiles_y ) {
			puts(err_out_of_memory);
			free(buffer);
			free(datasets[dataset].percentiles_c);
			return 0;
		}

		/* reset index */
		index = 0;
		/* loop on each year */
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			/* show */
			printf("- %02d importing %d...", year+1, datasets[dataset].years[year].year);
			/* leap year ? */
			is_leap = IS_LEAP_YEAR(datasets[dataset].years[year].year);
			/* compute rows count */
			rows_count = is_leap ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( datasets[dataset].hourly ) {
				rows_count /= 2;
			}

			/* database exists ? */
			if ( ! datasets[dataset].years[year].exist ) {
				/* adding null values */
				for ( i = 0; i < rows_count; i++ ) {
					/* set INVALID_VALUE each value */
					for ( y = 0; y < PERCENTILES_COUNT_2; y++ ) {
						datasets[dataset].percentiles_y[index+i].value[y] = INVALID_VALUE;
						datasets[dataset].percentiles_c[index+i].value[y] = INVALID_VALUE;
					}
				}
				/* alert */
				puts("ok (nothing found, null year added)");
			} else {
				/* build-up filename */
				sprintf(buffer, "%s%s_%d_%s_%s.csv",	input_path,
														datasets[dataset].details->site,
														datasets[dataset].years[year].year,
														authors_suffix[author_index],
														types_suffix[type_index]
				);

				/* open file */
				f = fopen(buffer, "r");
				if ( !f ) {
					printf("unable to open %s\n\n", buffer);
					free(buffer);
					return 0;
				}

				/* get header */
				if ( !get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE) ) {
				    puts("no header found.");
					free(buffer);					
					fclose(f);
					return 0;
				}

				/* get timestamp index */
				timestamp_column_index = get_column_of(buffer, dataset_delimiter, TIMESTAMP_START_STRING);
				if ( -2 == timestamp_column_index ) {
					puts(err_out_of_memory);
					free(buffer);
					fclose(f);
					return 0;
				} else if ( -1 == timestamp_column_index ) {
					/*  check for timestamp */
					timestamp_column_index = get_column_of(buffer, dataset_delimiter, TIMESTAMP_STRING);
					if ( -2 == timestamp_column_index ) {
						puts(err_out_of_memory);
						free(buffer);
						fclose(f);
						return 0;
					} else if ( -1 == timestamp_column_index ) {
						puts("no valid header found.");
						free(buffer);
						fclose(f);
						return 0;
					}
				} else {
					timestamp_column_index = get_column_of(buffer, dataset_delimiter, TIMESTAMP_END_STRING);
					if ( -2 == timestamp_column_index ) {
						puts(err_out_of_memory);
						free(buffer);
						fclose(f);
						return 0;
					} else if ( -1 == timestamp_column_index ) {
						printf("unable to find %s column\n", TIMESTAMP_END_STRING);
						free(buffer);
						fclose(f);
						return 0;
					}
				}

				/* loop on each row */
				element = 0;
				while ( get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE) ) {
					/* prevent too many rows */
					if ( element++ == rows_count ) {
						printf("too many rows for %s, %d", datasets[dataset].details->site, datasets[dataset].years[year].year);
						free(buffer);
						fclose(f);
						return 0;
					}

					/* reset values */
					for ( i = 0; i < PERCENTILES_COUNT_2; i++ ) {
						datasets[dataset].percentiles_c[index+element-1].value[i] = INVALID_VALUE;
						datasets[dataset].percentiles_y[index+element-1].value[i] = INVALID_VALUE;
					}
					assigned = 0;
					for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
						/* skip timestamp */
						if ( timestamp_column_index != i ) {
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf("unable to convert value %s at row %d, column %d\n", token, element+1, i+1);
								free(buffer);
								fclose(f);
								return 0;
							}

							/* convert NaN to invalid value */
							if ( value != value ) {
								value = INVALID_VALUE;
							}

							/* */
							if ( i-1 < PERCENTILES_COUNT_2 ) {
								datasets[dataset].percentiles_c[index+element-1].value[i-1] = value;
							} else {
								datasets[dataset].percentiles_y[index+element-1].value[i-1-PERCENTILES_COUNT_2] = value;
							}
							++assigned;
						}
					}

					/* check assigned */
					if ( assigned != columns_founded_count ) {
						printf("expected %d columns not %d\n", columns_founded_count, assigned);
						free(buffer);
						fclose(f);
						return 0;
					}
				}

				/* close file */
				fclose(f);

				/* check rows count */
				if ( element != rows_count ) {
					printf("rows count should be %d not %d\n", rows_count, element);
					free(buffer);
					return 0;
				}

				/* ok */
				puts("ok");
			}

			/* update index */
			index += rows_count;
		}

		/*
			Temporary test to check is invalid (-9999) values are present in the GPP and Reco output.
			This is happening due to some issue in the partitioning code that will be removed with the Gilberto version.
			For the moment to solve the issue if -9999 are found in the timeseries they are filled by linear interpolation between the first two valid values
			(in general only one or few half hours are missing)

			added on May 23, 2016
			fill first values and last values if missing with next\previous values
		*/

		/* _c */
		for ( i = 0; i < PERCENTILES_COUNT_2; i++ ) {
			for ( y = 0; y < datasets[dataset].rows_count; y++ ) {
				if ( IS_INVALID_VALUE(datasets[dataset].percentiles_c[y].value[i]) ) {
					/* first value ? */
					if ( ! y ) {
						datasets[dataset].percentiles_c[y].value[i] = datasets[dataset].percentiles_c[y+1].value[i];
						continue;
					}
					/* last values ? */
					if ( y == datasets[dataset].rows_count-1 ) {
						datasets[dataset].percentiles_c[y].value[i] = datasets[dataset].percentiles_c[y-1].value[i];
						continue;
					}
					start = -1;
					end = -1;
					z = y-1;
					startValue = INVALID_VALUE;
					while ( z >= 0 ) {
						startValue = datasets[dataset].percentiles_c[z].value[i];
						if ( !IS_INVALID_VALUE(startValue) ) {
							start = z;
							break; 
						}
						--z;
					}
					if ( -1 == start ) {
						continue;
					}

					z = y + 1;
					endValue = INVALID_VALUE;
					while ( z < datasets[dataset].rows_count ) {
						endValue = datasets[dataset].percentiles_c[z].value[i];
						if ( !IS_INVALID_VALUE(endValue) ) {
							end = z;
							break; 
						}
						++z;
					}
					if ( -1 == end ) {
						continue;
					}

					value = (startValue+endValue) / 2;
					datasets[dataset].percentiles_c[y].value[i] = value;
					if ( end - start > 2 ) {
						printf("- invalid values found from row %d to row %d for percentile %g%% c, replaced with %f (%02d: %f, %02d: %f)\n", y+1, end, percentiles_test_2[i], value, start+1, startValue, end+1, endValue);
					} else {
						printf("- invalid value found at row %d for percentile %g%% c, replaced with %f (%02d: %f, %02d: %f)\n", y+1, percentiles_test_2[i], value, start+1, startValue, end+1, endValue);
					}

					/* check for gap > 1 */
					if ( end - start > 2 ) {
						z = start+2;
						while ( z < end ) {
							datasets[dataset].percentiles_c[z].value[i] = value;
							++y;
							++z;
						}
					}
				}
			}
		}

		/* _y */
		for ( i = 0; i < PERCENTILES_COUNT_2; i++ ) {
			for ( y = 0; y < datasets[dataset].rows_count; y++ ) {
				if ( IS_INVALID_VALUE(datasets[dataset].percentiles_y[y].value[i]) ) {
					/* first value ? */
					if ( ! y ) {
						datasets[dataset].percentiles_y[y].value[i] = datasets[dataset].percentiles_y[y+1].value[i];
						continue;
					}
					/* last values ? */
					if ( y == datasets[dataset].rows_count-1 ) {
						datasets[dataset].percentiles_y[y].value[i] = datasets[dataset].percentiles_y[y-1].value[i];
						continue;
					}
					start = -1;
					end = -1;
					z = y-1;
					startValue = INVALID_VALUE;
					while ( z >= 0 ) {
						startValue = datasets[dataset].percentiles_y[z].value[i];
						if ( !IS_INVALID_VALUE(startValue) ) {
							start = z;
							break; 
						}
						--z;
					}
					if ( -1 == start ) {
						continue;
					}

					z = y + 1;
					endValue = INVALID_VALUE;
					while ( z < datasets[dataset].rows_count ) {
						endValue = datasets[dataset].percentiles_y[z].value[i];
						if ( !IS_INVALID_VALUE(endValue) ) {
							end = z;
							break; 
						}
						++z;
					}
					if ( -1 == end ) {
						continue;
					}

					value = (startValue+endValue) / 2;
					datasets[dataset].percentiles_y[y].value[i] = value;
					if ( end - start > 2 ) {
						printf("- invalid values found from row %d to row %d for percentile %g%% y, replaced with %f (%02d: %f, %02d: %f)\n", y+1, end, percentiles_test_2[i], value, start+1, startValue, end+1, endValue);
					} else {
						printf("- invalid value found at row %d for percentile %g%% y, replaced with %f (%02d: %f, %02d: %f)\n", y+1, percentiles_test_2[i], value, start+1, startValue, end+1, endValue);
					}

					/* check for gap > 1 */
					if ( end - start > 2 ) {
						z = start+2;
						while ( z < end ) {
							datasets[dataset].percentiles_y[z].value[i] = value;
							++y;
							++z;
						}
					}
				}
			}
		}


		/* dump dataset for debug purposes */
		/*
		{
			char buffer2[64];
			sprintf(buffer, "%s%s", output_path, datasets[dataset].details->site);
			sprintf(buffer2, "_%d", datasets[dataset].years[0].year);
			strcat(buffer, buffer2);
			if ( datasets[dataset].years_count > 1 ) {
				sprintf(buffer2, "_%d", datasets[dataset].years[datasets[dataset].years_count-1].year);
				strcat(buffer, buffer2);
			}
			sprintf(buffer2, "_%s_%s_dump.csv", authors_suffix[author_index], types_suffix[type_index]);
			strcat(buffer, buffer2);
			
			f = fopen(buffer, "w");
			if ( ! f ) {
				printf("unable to save %s for debug purposes!", buffer);
			} else {
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

				for ( i = 0; i < datasets[dataset].rows_count; ++i ) {
					for ( j = 0; j < PERCENTILES_COUNT_2; ++j ) {
						fprintf(f, "%g,", datasets[dataset].percentiles_c[i].value[j]);
					}
					for ( j = 0; j < PERCENTILES_COUNT_2; ++j ) {
						fprintf(f, "%g", datasets[dataset].percentiles_y[i].value[j]);
						if ( j < PERCENTILES_COUNT_2-1 ) {
							fputs(",", f);
						}
					}
					fputs("\n", f);
				}
				fclose(f);
			}
		}
		*/

		/* */
		printf("- computing hh...");

		/* process nee_matrix y */
		p_matrix_y = process_matrix(&datasets[dataset], 0, &ref_y, HH_Y, author_index, type_index);
		if ( !p_matrix_y ) {
			free(buffer);
			return 0;
		}

		/* process nee_matrix c */
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_matrix(&datasets[dataset], 1, &ref_c, HH_C, author_index, type_index);
			if ( !p_matrix_c ) {
				free(p_matrix_y);
				free(buffer);
				return 0;
			}
		}

		/* */
		printf("ok\n- saving hh...");

		/* save output hh */
		sprintf(buffer, output_file_hh, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
			}
			free(p_matrix_y);
			free(buffer);
			return 0;
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
		if ( datasets[dataset].years_count >= 3 ) {
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
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			if ( datasets[dataset].hourly ) {
				y /= 2;
			}

			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < y; row++ ) {
				/* TIMESTAMP_START */
				p = timestamp_start_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly); 
				fputs(p, f);
				/* TIMESTAMP_END */
				p = timestamp_end_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly); 
				fprintf(f, ",%s,", p);
				/* dtime */
				fprintf(f, "%g,", get_dtime_by_row(row, datasets[dataset].hourly));
				if ( exists ) {
					fprintf(f, "%g,%g,%g,%g,",
															datasets[dataset].percentiles_y[j+row].value[ref_y],
															datasets[dataset].percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
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

				if ( datasets[dataset].years_count >= 3 ) {
					if ( exists ) {
						fprintf(f, ",%g,%g,%g,%g,",
															datasets[dataset].percentiles_c[j+row].value[ref_c],
															datasets[dataset].percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
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
		sprintf(buffer, "%s%s_%s_%s_hh_info.txt", output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if  ( !f ) {
			printf("unable to create %s\n", buffer);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
			}
			free(p_matrix_y);
			free(buffer);
			return 0;
		}

		fprintf(f, model_efficiency_info,	types_suffix[type_index],
											types_suffix[type_index],
											types_suffix[type_index]
		);
		if ( datasets[dataset].years_count >= 3 ) {
			fprintf(f, model_efficiency_c_info, types_suffix[type_index], percentiles_test_2[ref_c]);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				fprintf(f, model_efficiency_y_info, types_suffix[type_index], datasets[dataset].years[i].year, percentiles_test_2[ref_y]);
			}
		} else {
			fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], percentiles_test_2[ref_y]);
		}
		fclose(f);

		/* */
		puts("ok");

		/* free memory */
		free(p_matrix_y);
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
		}

		/*
		*
		*	daily
		*
		*/

		printf("- computing daily...");

		/* compute daily rows */
		temp_rows_count = datasets[dataset].rows_count / rows_per_day;

		/* alloc memory for daily */
		matrix_y_temp = malloc(temp_rows_count*sizeof*matrix_y_temp);
		if ( !matrix_y_temp ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			matrix_c_temp = malloc(temp_rows_count*sizeof*matrix_c_temp);
			if ( !matrix_c_temp ) {
				puts(err_out_of_memory);
				free(matrix_y_temp);
				free(buffer);
				return 0;
			}
		}

		/* compute dd */
		index = 0;
		for ( row = 0; row < datasets[dataset].rows_count; row += rows_per_day ) {
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				matrix_y_temp[index].value[percentile] = 0.0;
				if ( datasets[dataset].years_count >= 3 ) {
					matrix_c_temp[index].value[percentile] = 0.0;
				}
				valids_y_count = 0;
				valids_c_count = 0;
				for ( i = 0; i < rows_per_day; i++ ) {
					/* check for valid value! */
					if ( ! IS_INVALID_VALUE(datasets[dataset].percentiles_y[row+i].value[percentile]) ) {
						matrix_y_temp[index].value[percentile] += datasets[dataset].percentiles_y[row+i].value[percentile];
						++valids_y_count;
					}
					/* check for valid value! */
					if ( (datasets[dataset].years_count >= 3) && ! IS_INVALID_VALUE(datasets[dataset].percentiles_c[row+i].value[percentile]) ) {
						matrix_c_temp[index].value[percentile] += datasets[dataset].percentiles_c[row+i].value[percentile];
						++valids_c_count;
					}
				}
				if ( ! valids_y_count ) {
					matrix_y_temp[index].value[percentile] = INVALID_VALUE;
				} else {
					matrix_y_temp[index].value[percentile] /= rows_per_day;
					matrix_y_temp[index].value[percentile] *= CO2TOC;
				}
				if ( datasets[dataset].years_count >= 3 ) {
					if ( ! valids_c_count ) {
						matrix_c_temp[index].value[percentile] = INVALID_VALUE;
					} else {
						matrix_c_temp[index].value[percentile] /= rows_per_day;
						matrix_c_temp[index].value[percentile] *= CO2TOC;
					}
				}
			}
			++index;
		}
		if ( index != temp_rows_count ) {
			printf("daily rows should be %d not %d", temp_rows_count, index);
			free(matrix_y_temp);
			if ( datasets[dataset].years_count >= 3 ) {
				free(matrix_c_temp);
			}
			free(buffer);
			return 0;
		}

		/* update daily rows_count */
		rows_count = temp_rows_count;

		/* copy pointer */
		matrix_y_daily = matrix_y_temp;
		if ( datasets[dataset].years_count >= 3 ) {
			matrix_c_daily = matrix_c_temp;
		}

		/* update */
		datasets[dataset].rows_count = temp_rows_count;
		free(datasets[dataset].percentiles_y);
		datasets[dataset].percentiles_y = matrix_y_temp;
		if ( datasets[dataset].years_count >= 3 ) {
			free(datasets[dataset].percentiles_c);
			datasets[dataset].percentiles_c = matrix_c_temp;
		}

		/* get p_matrix */
		p_matrix_y = process_matrix(&datasets[dataset], 0, &ref_y, DD_Y, author_index, type_index);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for daily y");
			free(buffer);
			return 0;
		}

		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_matrix(&datasets[dataset], 1, &ref_c, DD_C, author_index, type_index);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for daily c");
				free(p_matrix_y);
				free(buffer);
				return 0;
			}
		}

		/* */
		printf("ok\n- saving daily...");

		/* save output dd */
		sprintf(buffer, output_file_dd, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(p_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
			}
			free(buffer);
			return 0;
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
		if ( datasets[dataset].years_count >= 3 ) {
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
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			if ( datasets[dataset].hourly ) {
				y /= 2;
			}

			y /= rows_per_day;

			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < y; row++ ) {
				t = timestamp_end_by_row(row*(datasets[dataset].hourly ? 24 : 48), datasets[dataset].years[i].year, datasets[dataset].hourly);

				fprintf(f, "%04d%02d%02d,%d,",			t->YYYY,
														t->MM,
														t->DD,
														row+1
				);

				if ( exists ) {
					fprintf(f, "%g,%g,%g,%g,",
														datasets[dataset].percentiles_y[j+row].value[ref_y],
														datasets[dataset].percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
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

				if ( datasets[dataset].years_count >= 3 ) {
					if ( exists ) {
						fprintf(f, ",%g,%g,%g,%g,",
															datasets[dataset].percentiles_c[j+row].value[ref_c],
															datasets[dataset].percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
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
			element += ((IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (datasets[dataset].hourly ? 2 : 1));
		}

		/* close file */
		fclose(f);

		/* free memory */
		free(p_matrix_y);
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
		}

		/* save info dd */
		sprintf(buffer, "%s%s_%s_%s_dd_info.txt", output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if  ( !f ) {
			printf("unable to create %s\n", buffer);
			free(buffer);
			return 0;
		}

		fprintf(f, model_efficiency_info,	types_suffix[type_index],
											types_suffix[type_index],
											types_suffix[type_index]
		);
		if ( datasets[dataset].years_count >= 3 ) {
			fprintf(f, model_efficiency_c_info, types_suffix[type_index], percentiles_test_2[ref_c]);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				fprintf(f, model_efficiency_y_info, types_suffix[type_index], datasets[dataset].years[i].year, percentiles_test_2[ref_y]);
			}
		} else {
			fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], percentiles_test_2[ref_y]);
		}
		fclose(f);

		/* */
		puts("ok");

		/*
		*
		* weekly
		*
		*/

		printf("- computing weekly...");

		/* */
		temp_rows_count = 52 * datasets[dataset].years_count;
		matrix_y_temp = malloc(temp_rows_count*sizeof*matrix_y_temp);
		if ( !matrix_y_temp ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}

		if ( datasets[dataset].years_count >= 3 ) {
			matrix_c_temp = malloc(temp_rows_count*sizeof*matrix_c_temp);
			if ( !matrix_c_temp ) {
				puts(err_out_of_memory);
				free(matrix_y_temp);
				free(buffer);
				return 0;
			}
		}

		/* compute ww */
		j = 0;
		index = 0;
		element = 0;
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( datasets[dataset].hourly  ) {
				y /= 2;
			}
			y /= rows_per_day;
			for ( i = 0; i < 51; i++ ) {
				row = i*7;
				for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
					matrix_y_temp[index+i].value[percentile] = 0.0;
					if ( datasets[dataset].years_count >= 3 ) {
						matrix_c_temp[index+i].value[percentile] = 0.0;
					}
					valids_y_count = 0;
					valids_c_count = 0;
					for ( j = 0; j < 7; j++ ) {
						/* check for valid value! */
						if ( ! IS_INVALID_VALUE(datasets[dataset].percentiles_y[element+row+j].value[percentile]) ) {
							matrix_y_temp[index+i].value[percentile] += datasets[dataset].percentiles_y[element+row+j].value[percentile];
							++valids_y_count;
						}
						/* check for valid value! */
						if ( (datasets[dataset].years_count >= 3) && ! IS_INVALID_VALUE(datasets[dataset].percentiles_c[element+row+j].value[percentile]) ) {
							matrix_c_temp[index+i].value[percentile] += datasets[dataset].percentiles_c[element+row+j].value[percentile];
							++valids_c_count;
						}
					}
					if ( ! valids_y_count ) {
						matrix_y_temp[index+i].value[percentile] = INVALID_VALUE;
					} else {
						matrix_y_temp[index+i].value[percentile] /= 7;
					}
					if ( datasets[dataset].years_count >= 3 ) {
						if ( ! valids_c_count ) {
							matrix_c_temp[index+i].value[percentile] = INVALID_VALUE;
						} else {
							matrix_c_temp[index+i].value[percentile] /= 7;
						}
					}
				}
			}
			row += j; /* 51*7 */;
			z = y-row;
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				matrix_y_temp[index+i].value[percentile] = 0.0;
				if ( datasets[dataset].years_count >= 3 ) {
					matrix_c_temp[index+i].value[percentile] = 0.0;
				}
				valids_y_count = 0;
				valids_c_count = 0;
				for ( j = 0; j < z; j++ ) {
					/* check for valid value! */
					if ( ! IS_INVALID_VALUE(datasets[dataset].percentiles_y[element+row+j].value[percentile]) ) {
						matrix_y_temp[index+i].value[percentile] += datasets[dataset].percentiles_y[element+row+j].value[percentile];
						++valids_y_count;
					}
					/* check for valid value! */
					if ( (datasets[dataset].years_count >= 3) && ! IS_INVALID_VALUE(datasets[dataset].percentiles_c[element+row+j].value[percentile]) ) {
						matrix_c_temp[index+i].value[percentile] += datasets[dataset].percentiles_c[element+row+j].value[percentile];
						++valids_c_count;
					}
				}
				if ( ! valids_y_count ) {
					matrix_y_temp[index+i].value[percentile] = INVALID_VALUE;
				} else {
					matrix_y_temp[index+i].value[percentile] /= z;
				}
				if ( datasets[dataset].years_count >= 3 ) {
					if ( ! valids_c_count ) {
						matrix_c_temp[index+i].value[percentile] = INVALID_VALUE;
					} else {
						matrix_c_temp[index+i].value[percentile] /= z;
					}
				}
			}

			/* */
			index += 52;
			element += y;
		}

		/* update */
		datasets[dataset].rows_count = temp_rows_count;
		datasets[dataset].percentiles_y = matrix_y_temp;
		if ( datasets[dataset].years_count >= 3 ) {
			datasets[dataset].percentiles_c = matrix_c_temp;
		}

		/* get p_matrix */
		p_matrix_y = process_matrix(&datasets[dataset], 0, &ref_y, WW_Y, author_index, type_index);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for weekly y");
			free(matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(matrix_c_daily);
			}
			free(buffer);
			return 0;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_matrix(&datasets[dataset], 1, &ref_c, WW_C, author_index, type_index);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for weekly c");
				free(p_matrix_y);
				free(matrix_y_daily);
				free(matrix_c_daily);
				free(buffer);
				return 0;
			}
		}

		/* */
		printf("ok\n- saving weekly...");

		/* save output ww */
		sprintf(buffer, output_file_ww, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(p_matrix_y);
			free(matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(matrix_c_daily);
			}
			free(buffer);
			return 0;
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
		if ( datasets[dataset].years_count >= 3 ) {
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
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < 52; row++ ) {
				/* write timestamp_start */
				p = timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly, 1);
				fprintf(f, "%s,", p);
				/* write timestamp_end */
				p = timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly, 0);
				fprintf(f, "%s,", p);
				/* write week */
				fprintf(f, "%d,", row+1);
				if ( exists ) {
					fprintf(f, "%g,%g,%g,%g,",
														datasets[dataset].percentiles_y[j+row].value[ref_y],
														datasets[dataset].percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
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

				if ( datasets[dataset].years_count >= 3 ) {
					if ( exists ) {
						fprintf(f, ",%g,%g,%g,%g,",
															datasets[dataset].percentiles_c[j+row].value[ref_c],
															datasets[dataset].percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
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
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
		}

		/* save info ww */
		sprintf(buffer, "%s%s_%s_%s_ww_info.txt", output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if  ( !f ) {
			printf("unable to create %s\n", buffer);
			free(matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(matrix_c_daily);
			}
			free(buffer);
			return 0;
		}
		fprintf(f, model_efficiency_info,	types_suffix[type_index],
											types_suffix[type_index],
											types_suffix[type_index]
		);
		if ( datasets[dataset].years_count >= 3 ) {
			fprintf(f, model_efficiency_c_info, types_suffix[type_index], percentiles_test_2[ref_c]);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				fprintf(f, model_efficiency_y_info, types_suffix[type_index], datasets[dataset].years[i].year, percentiles_test_2[ref_y]);
			}
		} else {
			fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], percentiles_test_2[ref_y]);
		}
		fclose(f);

		/* */
		printf("ok\n- computing monthly...");

		/*
		*
		* monthly
		*
		*/

		/* set daily */
		free(datasets[dataset].percentiles_y);
		datasets[dataset].percentiles_y = matrix_y_daily;
		if ( datasets[dataset].years_count >= 3 ) {
			free(datasets[dataset].percentiles_c);
			datasets[dataset].percentiles_c = matrix_c_daily;
		}

		temp_rows_count = 12 * datasets[dataset].years_count;
		matrix_y_temp = malloc(temp_rows_count*sizeof*matrix_y_temp);
		if ( !matrix_y_temp ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}

		if ( datasets[dataset].years_count >= 3 ) {
			matrix_c_temp = malloc(temp_rows_count*sizeof*matrix_c_temp);
			if ( !matrix_c_temp ) {
				puts(err_out_of_memory);
				free(matrix_y_temp);
				free(buffer);
				return 0;
			}
		}

		/* compute mm */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			for ( i = 0; i < 12; i++ ) {
				for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
					matrix_y_temp[index+i].value[percentile] = 0.0;
					if ( datasets[dataset].years_count >= 3 ) {
						matrix_c_temp[index+i].value[percentile] = 0.0;
					}
					z = days_per_month[i];
					if ( (1 == i) && IS_LEAP_YEAR(year) ) {
						++z;
					}
					valids_y_count = 0;
					valids_c_count = 0;
					for ( j = 0; j < z; j++ ) {
						/* check for valid value! */
						if ( ! IS_INVALID_VALUE(datasets[dataset].percentiles_y[row+j].value[percentile]) ) {
							matrix_y_temp[index+i].value[percentile] += datasets[dataset].percentiles_y[row+j].value[percentile];
							++valids_y_count;
						}
						/* check for valid value! */
						if ( (datasets[dataset].years_count >= 3) && ! IS_INVALID_VALUE(datasets[dataset].percentiles_c[row+j].value[percentile]) ) {
							matrix_c_temp[index+i].value[percentile] += datasets[dataset].percentiles_c[row+j].value[percentile];
							++valids_c_count;
						}
					}
					if ( ! valids_y_count ) {
						matrix_y_temp[index+i].value[percentile] = INVALID_VALUE;
					} else {
						matrix_y_temp[index+i].value[percentile] /= z;
					}
					if ( datasets[dataset].years_count >= 3 ) {
						if ( ! valids_c_count ) {
							matrix_c_temp[index+i].value[percentile] = INVALID_VALUE;
						} else {
							matrix_c_temp[index+i].value[percentile] /= z;
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
		datasets[dataset].rows_count = temp_rows_count;
		datasets[dataset].percentiles_y = matrix_y_temp;
		if ( datasets[dataset].years_count >= 3 ) {
			datasets[dataset].percentiles_c = matrix_c_temp;
		}

		/* get p_matrix */
		p_matrix_y = process_matrix(&datasets[dataset], 0, &ref_y, MM_Y, author_index, type_index);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for monthly y");
			free(matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(matrix_c_daily);
			}
			free(buffer);
			return 0;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_matrix(&datasets[dataset], 1, &ref_c, MM_C, author_index, type_index);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for monthly c");
				free(p_matrix_y);
				free(matrix_y_daily);
				free(matrix_c_daily);
				free(buffer);
				return 0;
			}
		}

		/* */
		printf("ok\n- saving monthly...");

		/* save output mm */
		sprintf(buffer, output_file_mm, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(p_matrix_y);
			free(matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(matrix_c_daily);
			}
			free(buffer);
			return 0;
		}

		/* write header mm */
		fprintf(f, header_file_mm, TIMESTAMP_STRING);
		fprintf(f, output_var_1, types_suffix[type_index], types_suffix[type_index], types_suffix[type_index], types_suffix[type_index]);;
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "%s_%02g_y", types_suffix[type_index], percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
		if ( datasets[dataset].years_count >= 3 ) {
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
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			year = datasets[dataset].years[i].year;
			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < 12; row++ ) {
				fprintf(f, "%04d%02d,",				year,
													row+1
				);

				if ( exists ) {
					fprintf(f, "%g,%g,%g,%g,",
														datasets[dataset].percentiles_y[j+row].value[ref_y],
														datasets[dataset].percentiles_y[j+row].value[PERCENTILES_COUNT_2-1],
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
				if ( datasets[dataset].years_count >= 3 ) {
					if ( exists ) {
						fprintf(f, ",%g,%g,%g,%g,",
														datasets[dataset].percentiles_c[j+row].value[ref_c],
														datasets[dataset].percentiles_c[j+row].value[PERCENTILES_COUNT_2-1],
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
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
		}

		/* save info mm */
		sprintf(buffer, "%s%s_%s_%s_mm_info.txt", output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if  ( !f ) {
			printf("unable to create %s\n", buffer);
			free(matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(matrix_c_daily);
			}
			free(buffer);
			return 0;
		}
		fprintf(f, model_efficiency_info,	types_suffix[type_index],
											types_suffix[type_index],
											types_suffix[type_index]
		);
		if ( datasets[dataset].years_count >= 3 ) {
			fprintf(f, model_efficiency_c_info, types_suffix[type_index], percentiles_test_2[ref_c]);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				fprintf(f, model_efficiency_y_info, types_suffix[type_index], datasets[dataset].years[i].year, percentiles_test_2[ref_y]);
			}
		} else {
			fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], percentiles_test_2[ref_y]);
		}
		fclose(f);

		/* */
		printf("ok\n- computing yearly...");

		/*
		*
		* yearly
		*
		*/

		/* set daily */
		free(datasets[dataset].percentiles_y);
		datasets[dataset].percentiles_y = matrix_y_daily;
		if ( datasets[dataset].years_count >= 3 ) {
			free(datasets[dataset].percentiles_c);
			datasets[dataset].percentiles_c = matrix_c_daily;
		}

		matrix_y_temp = malloc(datasets[dataset].years_count*sizeof*matrix_y_temp);
		if ( !matrix_y_temp ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}

		if ( datasets[dataset].years_count >= 3 ) {
			matrix_c_temp = malloc(datasets[dataset].years_count*sizeof*matrix_c_temp);
			if ( !matrix_c_temp ) {
				puts(err_out_of_memory);
				free(matrix_y_temp);
				free(buffer);
				return 0;
			}
		}

		/* compute yy */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			y = IS_LEAP_YEAR(year) ? 366 : 365;
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				matrix_y_temp[index].value[percentile] = 0.0;
				if ( datasets[dataset].years_count >= 3 ) {
					matrix_c_temp[index].value[percentile] = 0.0;
				}
				valids_y_count = 0;
				valids_c_count = 0;
				for ( j = 0; j < y; j++ ) {
					/* check for valid value! */
					if ( ! IS_INVALID_VALUE(datasets[dataset].percentiles_y[row+j].value[percentile]) ) {
						matrix_y_temp[index].value[percentile] += datasets[dataset].percentiles_y[row+j].value[percentile];
						++valids_y_count;
					}
					/* check for valid value! */
					if ( (datasets[dataset].years_count >= 3) && ! IS_INVALID_VALUE(datasets[dataset].percentiles_c[row+j].value[percentile]) ) {
						matrix_c_temp[index].value[percentile] += datasets[dataset].percentiles_c[row+j].value[percentile];
						++valids_c_count;
					}
				}
				if ( ! valids_y_count ) {
					matrix_y_temp[index].value[percentile] = INVALID_VALUE;
				}
				if ( datasets[dataset].years_count >= 3 ) {
					if ( ! valids_c_count ) {
						matrix_c_temp[index].value[percentile] = INVALID_VALUE;
					}
				}
			}

			/* */
			row += y;
			++year;
			++index;
		}

		/* free daily */
		free(datasets[dataset].percentiles_y);
		if ( datasets[dataset].years_count >= 3 ) {
			free(datasets[dataset].percentiles_c);
		}

		/* update */
		datasets[dataset].rows_count = datasets[dataset].years_count;
		datasets[dataset].percentiles_y = matrix_y_temp;
		if ( datasets[dataset].years_count >= 3 ) {
			datasets[dataset].percentiles_c = matrix_c_temp;
		}

		/* get p_matrix */
		p_matrix_y = process_matrix(&datasets[dataset], 0, &ref_y, YY_Y, author_index, type_index);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for yearly y");
			free(buffer);
			return 0;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_matrix(&datasets[dataset], 1,  &ref_c, YY_C, author_index, type_index);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for yearly c");
				free(p_matrix_y);
				free(buffer);
				return 0;
			}
		}

		/* */
		printf("ok\n- saving yearly...");

		/* save output yy */
		sprintf(buffer, output_file_yy, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(p_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
			}
			free(buffer);
			return 0;
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
		if ( datasets[dataset].years_count >= 3 ) {
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
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			year = datasets[dataset].years[i].year;
			exists = datasets[dataset].years[i].exist;
			fprintf(f, "%d,", year);
			if ( exists ) {
				fprintf(f, "%g,%g,%g,%g,",
												datasets[dataset].percentiles_y[i].value[ref_y],
												datasets[dataset].percentiles_y[i].value[PERCENTILES_COUNT_2-1],
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
			if ( datasets[dataset].years_count >= 3 ) {
				if ( exists ) {
					fprintf(f, ",%g,%g,%g,%g,",
														datasets[dataset].percentiles_c[i].value[ref_c],
														datasets[dataset].percentiles_c[i].value[PERCENTILES_COUNT_2-1],
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
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
		}

		/* save info yy */
		sprintf(buffer, "%s%s_%s_%s_yy_info.txt", output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if  ( !f ) {
			printf("unable to create %s\n", buffer);
			free(matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(matrix_c_daily);
			}
			free(buffer);
			return 0;
		}
		fprintf(f, model_efficiency_info,	types_suffix[type_index],
											types_suffix[type_index],
											types_suffix[type_index]
		);
		if ( datasets[dataset].years_count >= 3 ) {
			fprintf(f, model_efficiency_c_info, types_suffix[type_index], percentiles_test_2[ref_c]);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				fprintf(f, model_efficiency_y_info, types_suffix[type_index], datasets[dataset].years[i].year, percentiles_test_2[ref_y]);
			}
		} else {
			fprintf(f, model_efficiency_y_one_year_info, types_suffix[type_index], percentiles_test_2[ref_y]);
		}
		fclose(f);

		/* */
		puts("ok\n");
	}

	/* free memory */
	free(buffer);

	/* ok */
	return 1;
}

/* */
int compute_sr_datasets(DATASET *const datasets, const int datasets_count, const int author_index, const int type_index) {
	int i;
	int j;
	int y;
	int z;
	int index;
	int dataset;
	int year;
	int rows_per_day;
	int is_leap;
	int rows_count;
	int reco_column;
	int qc_column;
	int tn_column;
	int valids_count;
	int temp_rows_count;
	int element;
	int assigned;
	int error;
	int row;
	int columns_count;
	PREC value;
	char *buffer;
	char *token;
	char *p;
	FILE *f;
	SR *srs_temp;
	SR *srs_daily;
	TIMESTAMP *t;

	/* allocate memory for buffer */
	buffer = malloc(HUGE_BUFFER_SIZE*sizeof*buffer);
	if ( !buffer ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* loop on each dataset */
	for ( dataset = 0; dataset < datasets_count; dataset++ ) {
		rows_per_day = datasets[dataset].hourly ? 24 : 48;

		/* show */
		printf("- %s, %d year%s:\n",	datasets[dataset].details->site,
										datasets[dataset].years_count,
										((datasets[dataset].years_count > 1) ? "s" : "")
		);

		/* alloc memory for srs */
		datasets[dataset].srs = malloc(datasets[dataset].rows_count*sizeof*datasets[dataset].srs);
		if ( !datasets[dataset].srs ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}

		/* reset index */
		index = 0;
		/* loop on each year */
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			/* reset */
			reco_column = -1;
			qc_column = -1;
			tn_column = -1;
			/* show */
			printf("- %02d importing %d...", year+1, datasets[dataset].years[year].year);
			/* leap year ? */
			is_leap = IS_LEAP_YEAR(datasets[dataset].years[year].year);
			/* compute rows count */
			rows_count = is_leap ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( datasets[dataset].hourly ) {
				rows_count /= 2;
			}
			/* database exists ? */
			if ( !datasets[dataset].years[year].exist ) {
				/* adding null values */
				for ( i = 0; i < rows_count; i++ ) {
					datasets[dataset].srs[index+i].reco = INVALID_VALUE;
					datasets[dataset].srs[index+i].qc = -1;
					datasets[dataset].srs[index+i].tn = -1;
					datasets[dataset].srs[index+i].reco_n = 0;
				}
				/* alert */
				puts("ok (nothing found, null year added)");
			} else {
				/* build-up filename */
				sprintf(buffer, "%s%s_%d_%s_%s.csv",	input_path,
														datasets[dataset].details->site,
														datasets[dataset].years[year].year,
														authors_suffix[author_index],
														types_suffix[type_index]
				);

				/* open file */
				f = fopen(buffer, "r");
				if ( !f ) {
					printf("unable to open %s\n\n", buffer);
					free(buffer);
					return 0;
				}

				/* get header */
				if ( !get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE) ) {
					puts("unable to get header!\n");
					fclose(f);
					free(buffer);
					return 0;
				}

				/* parse header */
				columns_count = 0;
				for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
					if ( ! string_compare_i(token, "reco") ) {
						reco_column = i;
						++columns_count;
					} else if ( ! string_compare_i(token, "qc") ) {
						qc_column = i;
						++columns_count;
					} else if ( ! string_compare_i(token, "tn") ) {
						tn_column = i;
						++columns_count;
					}
				}

				if ( -1 == reco_column ) {
					puts("column RECO not found.\n");
					fclose(f);
					free(buffer);
					return 0;
				}

				/* loop on each row */
				element = 0;
				while ( get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE) ) {
					/* prevent too many rows */
					if ( element++ == rows_count ) {
						printf("too many rows for %s, %d", datasets[dataset].details->site, datasets[dataset].years[year].year);
						free(buffer);
						fclose(f);
						return 0;
					}

					/* reset values */
					datasets[dataset].srs[index+element-1].reco = INVALID_VALUE;
					datasets[dataset].srs[index+element-1].qc = -1;
					datasets[dataset].srs[index+element-1].tn = -1;
					datasets[dataset].srs[index+element-1].reco_n = 0;

					assigned = 0;
					for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
						if ( reco_column == i ) {
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf("unable to convert value %s at row %d, column %d\n", token, element+1, i+1);
								free(buffer);
								fclose(f);
								return 0;
							}

							/* convert NaN to invalid value */
							if ( value != value ) {
								value = INVALID_VALUE;
							}
							datasets[dataset].srs[index+element-1].reco = value;
							++assigned;
						} else if ( qc_column == i ) {
							value = convert_string_to_int(token, &error);
							if ( error ) {
								printf("unable to convert value %s at row %d, column %d\n", token, element+1, i+1);
								free(buffer);
								fclose(f);
								return 0;
							}

							/* check for NaN */
							if ( value != value ) {
								printf("NaN value at row %d, column %d\n", element+1, i+1);
								free(buffer);
								fclose(f);
								return 0;
							}
							datasets[dataset].srs[index+element-1].qc = value;
							++assigned;
						} else if ( tn_column == i ) {
							value = convert_string_to_int(token, &error);
							if ( error ) {
								printf("unable to convert value %s at row %d, column %d\n", token, element+1, i+1);
								free(buffer);
								fclose(f);
								return 0;
							}

							/* check for NaN */
							if ( value != value ) {
								printf("NaN value at row %d, column %d\n", element+1, i+1);
								free(buffer);
								fclose(f);
								return 0;
							}
							datasets[dataset].srs[index+element-1].tn = value;
							++assigned;
						}
					}

					/* check assigned */
					if ( assigned != columns_count ) {
						printf("expected %d columns not %d\n", columns_count, assigned);
						free(buffer);
						fclose(f);
						return 0;
					}
				}

				/* close file */
				fclose(f);

				/* check rows count */
				if ( element != rows_count ) {
					printf("rows count should be %d not %d\n", rows_count, element);
					free(buffer);
					return 0;
				}

				/* ok */
				puts("ok");
			}

			/* update index */
			index += rows_count;
		}

		/* */
		printf("- saving hh...");

		/* save output hh */
		sprintf(buffer, output_file_hh, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(buffer);
			return 0;
		}

		/* write header hh */
		fprintf(f, header_file_hh, TIMESTAMP_HEADER);
		fputs("RECO\n" ,f);

		/* write values hh */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( datasets[dataset].hourly ) {
				y /= 2;
			}
			for ( row = 0; row < y; row++ ) {
				/* TIMESTAMP_START */
				p = timestamp_start_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly); 
				fputs(p, f);
				/* TIMESTAMP_END */
				p = timestamp_end_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly); 
				fprintf(f, ",%s,", p);
				/* values */
				fprintf(f, "%g,%g\n", get_dtime_by_row(row, datasets[dataset].hourly), datasets[dataset].srs[j+row].reco);
			}
			j += y;
		}

		/* close file */
		fclose(f);

		/* */
		puts("ok");

		/*
		*
		*	daily
		*
		*/

		/* */
		printf("- computing daily...");

		/* compute daily rows */
		temp_rows_count = datasets[dataset].rows_count / rows_per_day;

		/* alloc memory for daily */
		srs_daily = malloc(temp_rows_count*sizeof*srs_daily);
		if ( !srs_daily ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}

		/* compute dd */
		index = 0;
		for ( row = 0; row < datasets[dataset].rows_count; row += rows_per_day ) {
			srs_daily[index].reco = 0;
			srs_daily[index].qc = -1;
			srs_daily[index].tn = -1;
			srs_daily[index].reco_n = 0;

			valids_count = 0;
			for ( i = 0; i < rows_per_day; i++ ) {
				if ( ! IS_INVALID_VALUE(datasets[dataset].srs[row+i].reco) ) {
					srs_daily[index].reco += datasets[dataset].srs[row+i].reco;
					++valids_count;
				}
			}
			if ( ! valids_count ) {
				srs_daily[index].reco = INVALID_VALUE;
			} else {
				/*	20150813 changed the aggregation in case gaps are present in the day the average is calculated dividing by
					the number of valid values (before was divided by 24 or 48) */
				srs_daily[index].reco /= valids_count;
				srs_daily[index].reco *= CO2TOC;
				srs_daily[index].reco_n = (PREC)valids_count / rows_per_day;
			}
			++index;
		}
		if ( index != temp_rows_count ) {
			printf("daily rows should be %d not %d", temp_rows_count, index);
			free(srs_daily);
			free(buffer);
			return 0;
		}

		/* update daily rows_count */
		rows_count = temp_rows_count;

		/* update */
		datasets[dataset].rows_count = temp_rows_count;
		free(datasets[dataset].srs);
		datasets[dataset].srs = srs_daily;

		/* */
		printf("ok\n- saving daily...");

		/* save output dd */
		sprintf(buffer, output_file_dd, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(buffer);
			return 0;
		}

		/* write header dd */
		fprintf(f, header_file_dd, TIMESTAMP_STRING);
		fputs(header_file_reco, f);

		/* write values dd */
		j = 0;
		element = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			year = datasets[dataset].years[i].year;
			y = IS_LEAP_YEAR(year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			if ( datasets[dataset].hourly ) {
				y /= 2;
			}
			y /= rows_per_day;
			for ( row = 0; row < y; row++ ) {
				t = timestamp_end_by_row(row*(datasets[dataset].hourly ? 24 : 48), datasets[dataset].years[i].year, datasets[dataset].hourly);
				fprintf(f, "%04d%02d%02d,%d,%g,%g\n",	t->YYYY,
														t->MM,
														t->DD,
														row+1,
														datasets[dataset].srs[j+row].reco,
														datasets[dataset].srs[j+row].reco_n
				);
			}
			j += y;

			/* */
			element += ((IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (datasets[dataset].hourly ? 2 : 1));
		}

		/* close file */
		fclose(f);

		/* */
		puts("ok");

		/*
		*
		* weekly
		*
		*/

		/* */
		printf("- computing weekly...");

		/* */
		temp_rows_count = 52 * datasets[dataset].years_count;
		srs_temp = malloc(temp_rows_count*sizeof*srs_temp);
		if ( !srs_temp ) {
			puts(err_out_of_memory);
			free(buffer);
			return 0;
		}

		/* compute ww */
		j = 0;
		index = 0;
		element = 0;
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( datasets[dataset].hourly  ) {
				y /= 2;
			}
			y /= rows_per_day;
			for ( i = 0; i < 51; i++ ) {
				row = i*7;
				srs_temp[index+i].reco = 0;
				srs_temp[index+i].qc = -1;
				srs_temp[index+i].tn = -1;
				srs_temp[index+i].reco_n = 0;
				valids_count = 0;
				for ( j = 0; j < 7; j++ ) {
					if ( !IS_INVALID_VALUE(datasets[dataset].srs[element+row+j].reco) ) {
						srs_temp[index+i].reco += datasets[dataset].srs[element+row+j].reco;
						srs_temp[index+i].reco_n += datasets[dataset].srs[element+row+j].reco_n;
						++valids_count;
					}
				}
				if ( ! valids_count ) {
					srs_temp[index+i].reco = INVALID_VALUE;
				} else {
					/*	20150813 changed the aggregation in case gaps are present in the day the average is calculated dividing by
					the number of valid values (before was divided by 24 or 48) */
					srs_temp[index+i].reco /= valids_count;
					srs_temp[index+i].reco_n /= 7;
				}

			}
			row += j; /* 51*7 */;
			z = y-row;

			srs_temp[index+i].reco = 0;
			srs_temp[index+i].qc = -1;
			srs_temp[index+i].tn = -1;
			srs_temp[index+i].reco_n = 0;
			valids_count = 0;
			for ( j = 0; j < z; j++ ) {
				if ( !IS_INVALID_VALUE(datasets[dataset].srs[element+row+j].reco) ) {
					srs_temp[index+i].reco += datasets[dataset].srs[element+row+j].reco;
					srs_temp[index+i].reco_n += datasets[dataset].srs[element+row+j].reco_n;
					++valids_count;
				}
			}
			if ( ! valids_count ) {
				srs_temp[index+i].reco = INVALID_VALUE;
			} else {
				/*	20150813 changed the aggregation in case gaps are present in the day the average is calculated dividing by
					the number of valid values (before was divided by 24 or 48) */
				srs_temp[index+i].reco /= valids_count;
				srs_temp[index+i].reco_n /= z;
			}

			/* */
			index += 52;
			element += y;
		}

		/* */
		printf("ok\n- saving weekly...");

		/* save output ww */
		sprintf(buffer, output_file_ww, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(srs_temp);
			free(buffer);
			return 0;
		}

		/* write header ww */
		fprintf(f, header_file_ww, TIMESTAMP_HEADER);
		fputs(header_file_reco, f);

		/* write values ww */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			for ( row = 0; row < 52; row++ ) {
				/* write timestamp_start */
				p = timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly, 1);
				fprintf(f, "%s,", p);
				/* write timestamp_end */
				p = timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].hourly, 0);
				fprintf(f, "%s,", p);
				fprintf(f, "%d,%g,%g\n",	row+1,
											srs_temp[j+row].reco,
											srs_temp[j+row].reco_n
				);
			}
			j += 52;
		}

		/* close file */
		fclose(f);

		/*
		*
		* monthly
		*
		*/

		/* */
		printf("ok\n- computing monthly...");

		/* */
		temp_rows_count = 12 * datasets[dataset].years_count;

		/* compute mm */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			for ( i = 0; i < 12; i++ ) {
				srs_temp[index+i].reco = 0;
				srs_temp[index+i].qc = -1;
				srs_temp[index+i].tn = -1;
				srs_temp[index+i].reco_n = 0;

				z = days_per_month[i];
				if ( (1 == i) && IS_LEAP_YEAR(year) ) {
					++z;
				}
				valids_count = 0;
				for ( j = 0; j < z; j++ ) {
					if ( !IS_INVALID_VALUE(datasets[dataset].srs[row+j].reco) ) {
						srs_temp[index+i].reco += datasets[dataset].srs[row+j].reco;
						srs_temp[index+i].reco_n += datasets[dataset].srs[row+j].reco_n;
						++valids_count;
					}
				}
				if ( ! valids_count ) {
					srs_temp[index+i].reco = INVALID_VALUE;
				} else {
					/*	20150813 changed the aggregation in case gaps are present in the day the average is calculated dividing by
					the number of valid values (before was divided by 24 or 48) */
					srs_temp[index+i].reco /= valids_count;
					srs_temp[index+i].reco_n /= z;
				}

				/* */
				row += z;
			}

			/* */
			++year;
			index += i;
		}

		/* */
		printf("ok\n- saving monthly...");

		/* save output mm */
		sprintf(buffer, output_file_mm, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(srs_temp);
			free(buffer);
			return 0;
		}

		/* write header mm */
		fprintf(f, header_file_mm, TIMESTAMP_STRING);
		fputs(header_file_reco, f);

		/* write values mm */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			year = datasets[dataset].years[i].year;
			for ( row = 0; row < 12; row++ ) {
				fprintf(f, "%04d%02d,%g,%g\n",		year,
													row+1,
													srs_temp[j+row].reco,
													srs_temp[j+row].reco_n
				);
			}
			j += 12;
		}

		/* close file */
		fclose(f);

		/*
		*
		* yearly
		*
		*/

		printf("ok\n- computing yearly...");

		/* compute yy */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			y = IS_LEAP_YEAR(year) ? 366 : 365;
			srs_temp[index].reco = 0;
			srs_temp[index].qc = -1;
			srs_temp[index].tn = -1;
			srs_temp[index].reco_n = 0;
			valids_count = 0;
			for ( j = 0; j < y; j++ ) {
				if ( !IS_INVALID_VALUE(datasets[dataset].srs[row+j].reco) ) {
					srs_temp[index].reco += datasets[dataset].srs[row+j].reco;
					srs_temp[index].reco_n += datasets[dataset].srs[row+j].reco_n;
					++valids_count;
				}
			}

			/* */
			if ( ! valids_count ) {
				srs_temp[index].reco = INVALID_VALUE;
			} else {
				srs_temp[index].reco_n /= y;
			}

			/* */
			row += y;
			++year;
			++index;
		}

		/* */
		printf("ok\n- saving yearly...");

		/* save output yy */
		sprintf(buffer, output_file_yy, output_path, datasets[dataset].details->site, authors_suffix[author_index], types_suffix[type_index]);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n", buffer);
			free(srs_temp);
			free(buffer);
			return 0;
		}


		/* write header yy */
		fprintf(f, header_file_yy, TIMESTAMP_STRING);
		fputs(header_file_reco, f);

		/* write values yy */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			year = datasets[dataset].years[i].year;
			fprintf(f, "%d,%g,%g\n",	year, 
										srs_temp[i].reco,
										srs_temp[i].reco_n
			);
		}

		/* close file */
		fclose(f);

		/* free memory */
		free(srs_temp);

		/* */
		puts("ok\n");
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
	int files_founded_count;
	int year;
	char year_c[YEAR_LEN];
	char buffer[FILENAME_SIZE];
	FILES *files_founded;
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
	files_founded = get_files(path, buffer, &files_founded_count, &error);
	if ( error || !files_founded_count ) {
		puts("no files founded!");
		return NULL;
	}

	/* alloc memory for details */
	details = alloc_dd();
	if ( !details ) {
		return NULL;
	}

	/* loop on each files founded */
	for ( file_index = 0; file_index < files_founded_count; file_index++ ) {
		/* check filename */
		if ( !is_valid_filename(files_founded[file_index].list[0].name, author_index, type_index) ) {
			continue;
		}

		/* get site */
		strncpy(details->site, files_founded[file_index].list[0].name, SITE_LEN - 1);
		details->site[SITE_LEN - 1] = '\0';

		/* get year */
		strncpy(year_c, files_founded[file_index].list[0].name+SITE_LEN, YEAR_LEN - 1);
		year_c[YEAR_LEN-1] = '\0';

		/* convert year string to int */
		year = convert_string_to_int(year_c, &error);
		if ( error ) {
			printf("unable to convert year for %s\n\n", files_founded[file_index].list[0].name);
			free_dd(details);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}
		details->year = year;

		/* get timeres */
		f = fopen(files_founded[file_index].list[0].fullpath, "r");
		if ( !f ) {
			printf("unable to get rows count for %s\n\n", files_founded[file_index].list[0].name);
			free_dd(details);
			free_datasets(datasets, *datasets_count);
			return NULL;

		}

		i = get_rows_count_from_file(f);
		if ( !i ) {
			printf("no valid rows founded for %s\n\n", files_founded[file_index].list[0].name);
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
			printf("no valid timeres founded for %s\n\n", files_founded[file_index].list[0].name);
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
				free_files(files_founded, files_founded_count);
				free_datasets(datasets, *datasets_count);
				return NULL;
			}
		}

		/* check if year is already assigned...? */
		for ( y = 0; y < datasets[i].years_count; y++ ) {
			if ( details->year == datasets[i].years[y].year ) {
				puts(err_out_of_memory);
				free_dd(details);
				free_files(files_founded, files_founded_count);
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
	free_files(files_founded, files_founded_count);

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
