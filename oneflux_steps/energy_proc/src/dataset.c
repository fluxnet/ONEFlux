/*
	dataset.c

	this file is part of energy_proc

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
#include "randunc.h"
#include "ecbcf.h"
#include "aggr.h"
#include "info_hh.h"
#include "info_dd.h"
#include "info_ww.h"
#include "info_mm.h"
#include "info_yy.h"

/* constants */
#define INPUT_FILENAME_LEN			26		/* including extension */

/* externs */
extern char *program_path;
extern char *input_path;
extern char *output_path;
extern int window_size;
extern int window_size_daily;
extern int window_size_weekly;
extern int window_size_monthly;
extern int window_size_method_2_3_hh;
extern int window_size_method_2_3_dd;
extern int window_size_method_2_3_ww;
extern int window_size_method_2_3_mm;
extern int samples_count;
extern int debug;
extern int multi;
extern int no_rand_unc;
extern const int days_per_month[MONTHS];
extern int qc_gf_threshold;

/* strings */
/* please use same order from types.h enum */
static const char *input_columns_tokens[INPUT_VALUES] = { "H", "LE", "SW_IN", "TA", "RH", "NETRAD", "G", "VPD", "FLAG_SPIKE_H", "FLAG_QC2_H", "FLAG_SPIKE_LE", "FLAG_QC2_LE" };
static const char dataset_delimiter[] = " ,\r\n";
static const char field_delimiter[] = ",\r\n";
static const char output_file_diff[] = "%s%s_energy_diff.csv";
static const char output_file_diff_perc[] = "%s%s_energy_diff_perc_%s.csv";
static const char output_file_info[] = "%s%s_energy_%s_info.txt";
static const char output_file_hh[] = "%s%s_energy_hh.csv";
static const char output_file_dd[] = "%s%s_energy_dd.csv";
static const char output_file_ww[] = "%s%s_energy_ww.csv";
static const char output_file_mm[] = "%s%s_energy_mm.csv";
static const char output_file_yy[] = "%s%s_energy_yy.csv";
static const char output_header_diff[] = "%s,DTIME,LE,LE_hat,LE_qc,LE_stddev,LE_diff_abs,LE_diff,H,H_hat,H_qc,H_stddev,H_diff_abs,H_diff\n";
static const char output_header_hh_no_rand_unc[] = "%s,DTIME,LE,LEcorr,LEcorr25,LEcorr75,LE_qc,H,Hcorr,Hcorr25,Hcorr75,H_qc,EBCcf_n,method,G_f,G_qc\n";
static const char output_header_hh[] =	"%s,DTIME,"
										"LE,LEcorr,LEcorr25,LEcorr75,LE_qc,LE_randUnc,LE_randUnc_method,LE_randUnc_n,"
										"LEcorr_joinUnc,"
										"H,Hcorr,Hcorr25,Hcorr75,H_qc,H_randUnc,H_randUnc_method,H_randUnc_n,"
										"Hcorr_joinUnc,"
										"EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_header_dd[] = "%s,DOY,"
										"LE,LEcorr,LEcorr25,LEcorr75,LE_qc,LE_randUnc,LEcorr_joinUnc,"
										"H,Hcorr,Hcorr25,Hcorr75,H_qc,H_randUnc,Hcorr_joinUnc,"
										"EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_header_ww[] = "%s,WEEK,LE,LEcorr,LE_qc,LE_randUnc,H,Hcorr,H_qc,H_randUnc,EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_header_mm[] = "%s,LE,LEcorr,LE_qc,LE_randUnc,H,Hcorr,H_qc,H_randUnc,EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_header_yy[] = "%s,LE,LEcorr,LE_qc,LE_randUnc,H,Hcorr,H_qc,H_randUnc,EBCcf_n,EBCcf_method,G_f,G_qc\n";

static const char output_header_dd_no_rand_unc[] = "%s,DOY,LE,LEcorr,LEcorr25,LEcorr75,LE_qc,H,Hcorr,Hcorr25,Hcorr75,H_qc,EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_format_dd_no_rand_unc[] = "%04d%02d%02d,%d,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";

static const char output_header_ww_no_rand_unc[] = "%s,WEEK,LE,LEcorr,LE_qc,H,Hcorr,H_qc,EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_format_ww_no_rand_unc[] = "%d,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";

static const char output_header_mm_no_rand_unc[] = "%s,LE,LEcorr,LE_qc,H,Hcorr,H_qc,EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_format_mm_no_rand_unc[] = "%04d%02d,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";

static const char output_header_yy_no_rand_unc[] = "%s,LE,LEcorr,LE_qc,H,Hcorr,H_qc,EBCcf_n,EBCcf_method,G_f,G_qc\n";
static const char output_format_yy_no_rand_unc[] = "%04d,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";

static const char output_format_diff[] = "%g,%g,%g,%d,%g,%g,%g,%g,%g,%d,%g,%g,%g\n";
static const char output_format_hh_no_rand_unc[] = "%g,%g,%g,%g,%g,%d,%g,%g,%g,%g,%d,%d,%d,%g,%d\n";

static const char output_format_hh[] =	"%g,"
										"%g,%g,%g,%g,%d,%g,%d,%d,"
										"%g,"
										"%g,%g,%g,%g,%d,%g,%d,%d,"
										"%g,"
										"%d,%d,"
										"%g,%d\n";
static const char output_format_dd[] = "%04d%02d%02d,%d,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";
static const char output_format_ww[] = "%d,%g,%g,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";
static const char output_format_mm[] = "%04d%02d,%g,%g,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";
static const char output_format_yy[] = "%04d,%g,%g,%g,%g,%g,%g,%g,%g,%g,%d,%g,%g\n";

static const char output_file_debug_original[] = "%s%s_energy_original_dataset.csv";
static const char output_header_debug_original[] = "%s,DTIME,H,LE,SW_IN,TA,RH,G,VPD,NETRAD\n";
static const char output_format_debug_original[] = "%g,%g,%g,%g,%g,%g,%g,%g,%g\n";

static const char output_file_debug_gapfilled[] = "%s%s_energy_gapfilled_dataset.csv";
static const char output_header_debug_gapfilled[] = "%s,DTIME,H,H_qc,H_stddev,Le,Le_qc,LE_stddev,NETRAD,G,G_f,G_qc,G_stddev\n";
static const char output_format_debug_gapfilled[] = "%g,%g,%d,%g,%g,%d,%g,%g,%g,%g,%d,%g\n";

static const char output_file_debug_ecbcf_hh[] = "%s%s_energy_EBCcf_hh.csv";
static const char output_header_debug_ecbcf_hh[] = "%s,DTIME,EBCcf,EBCcf_temp\n";
static const char output_format_debug_ecbcf_hh[] = "%g,%g,%g\n";

static const char output_file_debug_aggr_by_day[] = "%s%s_energy_aggr_by_day_dataset.csv";
static const char output_header_debug_aggr_by_day[] = "%s,DOY,H,H_qc,Le,Le_qc,G,NETRAD,EBCcf,EBCcf_temp\n";
static const char output_format_debug_aggr_by_day[] = "%04d%02d%02d,%d,%g,%g,%g,%g,%g,%g,%g,%g\n";

static const char output_file_debug_aggr_by_week[] = "%s%s_energy_aggr_by_week_dataset.csv";
static const char output_header_debug_aggr_by_week[] = "%s,WEEK,H,H_qc,Le,Le_qc,G,NETRAD,EBCcf,EBCcf_temp\n";
static const char output_format_debug_aggr_by_week[] = "%04d,%d,%g,%g,%g,%g,%g,%g,%g,%g\n";

static const char output_file_debug_aggr_by_month[] = "%s%s_energy_aggr_by_month_dataset.csv";
static const char output_header_debug_aggr_by_month[] = "%s,H,H_qc,Le,Le_qc,G,NETRAD,EBCcf,EBCcf_temp\n";
static const char output_format_debug_aggr_by_month[] = "%04d%02d,%g,%g,%g,%g,%g,%g,%g,%g\n";

static const char output_file_debug_aggr_by_year[] = "%s%s_energy_aggr_by_year_dataset.csv";
static const char output_header_debug_aggr_by_year[] = "%s,H,H_qc,Le,Le_qc,G,NETRAD,EBCcf,EBCcf_temp\n";
static const char output_format_debug_aggr_by_year[] = "%04d,%g,%g,%g,%g,%g,%g,%g,%g\n";

static const char dynamic_text[] = ""
"- EBC before correction: 50th perc. = %g, 25th-75th perc. = %g-%g\n"
"- EBC after correction: 50th perc. = %g, 25th-75th perc. = %g-%g\n";

/* */
static int compare_diff(const void * a, const void * b) {
	if ( ((DIFF *)a)->value[ORIG] < ((DIFF *)b)->value[ORIG] ) {
		return -1;
	} else if ( ((DIFF *)a)->value[ORIG] > ((DIFF *)b)->value[ORIG] ) {
		return 1;
	} else {
		return 0;
	}
}

/* */
static int import_values(DATASET *const dataset, const int year_index, const int rows_count, const int index) {
	int i;
	int y;
	int element;
	int assigned;
	int seeked;
	int error;
	int has_flag_qc_h;
	int has_flag_spike_h;
	int has_flag_qc_le;
	int has_flag_spike_le;
	int flag_qc_h_value;
	int flag_spike_h_value;
	int flag_qc_le_value;
	int flag_spike_le_value;
	int columns_index[INPUT_VALUES];
	char *token;
	char *p;
	char buffer[BUFFER_SIZE];
	char buffer2[BUFFER_SIZE];
	PREC value;
	FILE *f;	
	DD *details;

	/* reset */
	has_flag_qc_h = 0;
	has_flag_spike_h = 0;
	has_flag_qc_le = 0;
	has_flag_spike_le = 0;

	/* reset columns */
	for ( i = 0; i < INPUT_VALUES; i++ ) {
		columns_index[i] = -1;
	}

	/* clear dataset */
	for ( i = 0; i < rows_count; i++ ) {
		for ( y = 0; y < DATASET_VALUES_TO_AGGR; y++ ) {
			dataset->rows[index+i].value[y] = INVALID_VALUE;
		}
	}

	/* open file */
	f = fopen(dataset->years[year_index].filename, "r");
	if ( !f ) {
		puts("unable to open file.");
		return 0;
	}

	/* skip details */
	details = parse_dd(f);
	if ( !details ) {
		fclose(f);
		return 0;
	}
	free_dd(details);

	if ( ! fgets(buffer, BUFFER_SIZE, f) ) {
		puts("bad file...empty?");
		fclose(f);
		return 0;
	}

	/*  check for timestamps */
	i = get_column_of(buffer, dataset_delimiter, TIMESTAMP_START_STRING);
	if ( -2 == i ) {
		puts(err_out_of_memory);
		fclose(f);
		return 0;
	} else if ( -1 == i ) {
		/*  check for timestamp */
		i = get_column_of(buffer, dataset_delimiter, TIMESTAMP_STRING);
		if ( -2 == i ) {
			puts(err_out_of_memory);
			fclose(f);
			return 0;
		} else if ( -1 == i ) {
			puts("no valid header found.");
			fclose(f);
			return 0;
		}
	} else {
		i = get_column_of(buffer, dataset_delimiter, TIMESTAMP_END_STRING);
		if ( -2 == i ) {
			puts(err_out_of_memory);
			fclose(f);
			return 0;
		} else if ( -1 == i ) {
			printf("unable to find %s column\n", TIMESTAMP_END_STRING);
			fclose(f);
			return 0;
		}
	}

	/* parse header */
	seeked = 0;
	for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
		for ( y = 0; y < INPUT_VALUES; y++ ) {
			/* check for itp */
			strcpy(buffer2, "itp");
			strcat(buffer2, input_columns_tokens[y]);
			if ( ! string_compare_i(token, input_columns_tokens[y]) || ! string_compare_i(token, buffer2)  ) {
				/* check if it is already assigned */
				if ( columns_index[y] != -1 ) {
					printf("column %s already found at index %d\n", token, columns_index[y]);
					fclose(f);
					return 0;
				} else {
					columns_index[y] = i;
					++seeked;
					/* do not skip, continue searching for redundant columns */
					/* break; */
				}
			}
		}
	}

	/* check columns */
	if ( ! seeked ) {
		puts("nothing found in header. adding null values..");
		fclose(f);
		return 0;
	}

	/* check H and LE and flags */
	if ( columns_index[H_INPUT] != -1 ) {
		dataset->years[year_index].hle |= H_DATASET;
	}
	if ( columns_index[LE_INPUT] != -1 ) {
		dataset->years[year_index].hle |= LE_DATASET;
	}
	if ( columns_index[FLAG_QC_H_INPUT] != -1 ) {
		has_flag_qc_h = 1;
	}
	if ( columns_index[FLAG_SPIKE_H_INPUT] != -1 ) {
		has_flag_spike_h = 1;
	}
	if ( columns_index[FLAG_QC_LE_INPUT] != -1 ) {
		has_flag_qc_le = 1;
	}
	if ( columns_index[FLAG_SPIKE_LE_INPUT] != -1 ) {
		has_flag_spike_le = 1;
	}

	/* get values */
	element = 0;
	while ( get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
		/* prevent too many rows */
		if ( element++ == rows_count ) {
			puts("too many rows!");
			fclose(f);
			return 0;
		}

		assigned = 0;
		error = 0;
		for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
			for ( y = 0; y < INPUT_VALUES; y++ ) {
				if ( i == columns_index[y] ) {
					/* convert string to prec */
					value = convert_string_to_prec(token, &error);
					if ( error ) {
						printf("unable to convert value %s at row %d, column %d\n", token, element+1, i+1);
						fclose(f);
						return 0;
					}

					/* convert nan to invalid value */
					if ( value != value ) {
						value = INVALID_VALUE;
					}

					switch ( y ) {
						case FLAG_QC_H_INPUT:
							flag_qc_h_value = (int)value;
						break;

						case FLAG_SPIKE_H_INPUT:
							flag_spike_h_value = (int)value;
						break;

						case FLAG_QC_LE_INPUT:
							flag_qc_le_value = (int)value;
						break;

						case FLAG_SPIKE_LE_INPUT:
							flag_spike_le_value = (int)value;
						break;

						default:
							dataset->rows[index+element-1].value[y] = value;
					}
					++assigned;
					break;
				}
			}
		}

		/* check assigned */
		if ( assigned != seeked ) {
			printf("expected %d columns not %d\n", seeked, assigned);
			fclose(f);
			return 0;
		}

		/* check flags */
		if ( has_flag_qc_h ) {
			if ( 1 == flag_qc_h_value ) {
				dataset->rows[index+element-1].value[H] = INVALID_VALUE;
			}
		}

		if ( has_flag_spike_h ) {
			if ( flag_spike_h_value >= 2 ) {	/* 5.5 */
				dataset->rows[index+element-1].value[H] = INVALID_VALUE;
			}
		}

		if ( has_flag_qc_le ) {
			if ( 1 == flag_qc_le_value ) {
				dataset->rows[index+element-1].value[LE] = INVALID_VALUE;
			}
		}

		if ( has_flag_spike_le ) {
			if ( flag_spike_le_value >= 2 ) {	/* 5.5 */
				dataset->rows[index+element-1].value[LE] = INVALID_VALUE;
			}
		}
	}

	/* close file */
	fclose(f);

	/* check rows count */
	if ( element != rows_count ) {
		printf("rows count should be %d not %d\n", rows_count, element);
		return 0;
	}

	/* */
	return 1;
}

/* */
void free_datasets(DATASET *datasets, const int datasets_count) {
	int i;
	int y;

	/* */
	for ( i = 0; i < datasets_count; i++ ) {
		for ( y = 0; y < VARS_TO_FILL; y++ ) {
			if ( datasets[i].gf_rows[y] ) {
				free(datasets[i].gf_rows[y]);
			}
		}
		free_dd(datasets[i].details);
		free(datasets[i].rows_temp);
		free(datasets[i].rows_daily);
		free(datasets[i].rows_aggr);
		free(datasets[i].rows);
		free(datasets[i].years);
		free(datasets[i].indexes);
		datasets[i].details = NULL;
		datasets[i].rows = NULL;
		datasets[i].rows_aggr = NULL;
		datasets[i].rows_daily = NULL;
		datasets[i].rows_temp = NULL;
		datasets[i].indexes = NULL;
	}
	free(datasets);
}

/* */
int save_output_diff(const DATASET *const dataset) {
	char *p;
	char buffer[256];
	int i;
	int j;
	int y;
	int row;
	int error;
	FILE *f;

	/* */
	assert(dataset);

	/* create file */
	sprintf(buffer, output_file_diff, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( ! f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_diff, TIMESTAMP_HEADER);
	
	/* write results */
	error = 0;
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			y /= 2;
		}
		for ( row = 0; row < y; row++ ) {
			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fprintf(f, ",%s,", p);		
			/* write values */
			fprintf(f, output_format_diff,	get_dtime_by_row(row, dataset->hourly),
											dataset->rows[j+row].value[LE],
											dataset->gf_rows[LE_INDEX][j+row].filled,
											dataset->gf_rows[LE_INDEX][j+row].quality,
											dataset->gf_rows[LE_INDEX][j+row].stddev,
											( (!IS_INVALID_VALUE(dataset->rows[j+row].value[LE]) && (1 == dataset->gf_rows[LE_INDEX][j+row].quality)) ? FABS(dataset->rows[j+row].value[LE]-dataset->gf_rows[LE_INDEX][j+row].filled) : INVALID_VALUE),
											( (!IS_INVALID_VALUE(dataset->rows[j+row].value[LE]) && (1 == dataset->gf_rows[LE_INDEX][j+row].quality)) ? dataset->rows[j+row].value[LE]-dataset->gf_rows[LE_INDEX][j+row].filled : INVALID_VALUE),
											dataset->rows[j+row].value[H],
											dataset->gf_rows[H_INDEX][j+row].filled,
											dataset->gf_rows[H_INDEX][j+row].quality,
											dataset->gf_rows[H_INDEX][j+row].stddev,
											( (!IS_INVALID_VALUE(dataset->rows[j+row].value[H]) && (1 == dataset->gf_rows[H_INDEX][j+row].quality)) ? FABS(dataset->rows[j+row].value[H]-dataset->gf_rows[H_INDEX][j+row].filled) : INVALID_VALUE),
											( (!IS_INVALID_VALUE(dataset->rows[j+row].value[H]) && (1 == dataset->gf_rows[H_INDEX][j+row].quality)) ? dataset->rows[j+row].value[H]-dataset->gf_rows[H_INDEX][j+row].filled : INVALID_VALUE)
			);
		}
		if ( error ) {
			break;
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* ok */
	return !error;
}

/* */
int save_output_midhourly(const DATASET *const dataset) {
	char *p;
	char buffer[256];
	int i;
	int j;
	int y;
	int row;
	int error;
	PREC LEcorr_joinUnc;
	PREC Hcorr_joinUnc;
	FILE *f;

	/* */
	assert(dataset);

	/* create file */
	sprintf(buffer, output_file_hh, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	if ( no_rand_unc ) {
		fprintf(f, output_header_hh_no_rand_unc, TIMESTAMP_HEADER);
	} else {
		fprintf(f, output_header_hh, TIMESTAMP_HEADER);
	}
	
	/* write results */
	error = 0;
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			y /= 2;
		}
		for ( row = 0; row < y; row++ ) {
			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fprintf(f, ",%s,", p);
			/* write values */
			if ( no_rand_unc ) {
				fprintf(f, output_format_hh_no_rand_unc,	get_dtime_by_row(row, dataset->hourly),
															IS_FLAG_SET(dataset->years[i].hle, LE_DATASET) ? dataset->rows[j+row].value[LE] : INVALID_VALUE,
															dataset->rows[j+row].value[LEcorr],
															dataset->rows[j+row].value[LEcorr25],
															dataset->rows[j+row].value[LEcorr75],
															dataset->gf_rows[LE_INDEX][j+row].quality,
															IS_FLAG_SET(dataset->years[i].hle, H_DATASET) ? dataset->rows[j+row].value[H] : INVALID_VALUE,
															dataset->rows[j+row].value[Hcorr],
															dataset->rows[j+row].value[Hcorr25],
															dataset->rows[j+row].value[Hcorr75],
															dataset->gf_rows[H_INDEX][j+row].quality,
															dataset->rows[j+row].ecbcf_samples_count,
															dataset->rows[j+row].ecbcf_method + 1,
															dataset->gf_rows[G_INDEX][j+row].filled,
															dataset->gf_rows[G_INDEX][j+row].quality

				);
			} else {
				LEcorr_joinUnc = INVALID_VALUE;
				Hcorr_joinUnc = INVALID_VALUE;

				if (	!IS_INVALID_VALUE(dataset->rows[j+row].rand[LE_INDEX]) &&
						!IS_INVALID_VALUE(dataset->rows[j+row].value[LEcorr25])	&&
						!IS_INVALID_VALUE(dataset->rows[j+row].value[LEcorr75]) ) {
					LEcorr_joinUnc = SQRT(
											(dataset->rows[j+row].rand[LE_INDEX] * dataset->rows[j+row].rand[LE_INDEX]) +
											(((dataset->rows[j+row].value[LEcorr75]-dataset->rows[j+row].value[LEcorr25])/IQR) *
											((dataset->rows[j+row].value[LEcorr75]-dataset->rows[j+row].value[LEcorr25])/IQR)));
				}

				if (	!IS_INVALID_VALUE(dataset->rows[j+row].rand[H_INDEX]) &&
						!IS_INVALID_VALUE(dataset->rows[j+row].value[Hcorr25])	&&
						!IS_INVALID_VALUE(dataset->rows[j+row].value[Hcorr75]) ) {
					Hcorr_joinUnc = SQRT(
											(dataset->rows[j+row].rand[H_INDEX] * dataset->rows[j+row].rand[H_INDEX]) +
											(((dataset->rows[j+row].value[Hcorr75]-dataset->rows[j+row].value[Hcorr25])/IQR) *
											((dataset->rows[j+row].value[Hcorr75]-dataset->rows[j+row].value[Hcorr25])/IQR)));
				}

				fprintf(f, output_format_hh,	get_dtime_by_row(row, dataset->hourly),
												IS_FLAG_SET(dataset->years[i].hle, LE_DATASET) ? dataset->rows[j+row].value[LE] : INVALID_VALUE,
												dataset->rows[j+row].value[LEcorr],
												dataset->rows[j+row].value[LEcorr25],
												dataset->rows[j+row].value[LEcorr75],
												dataset->gf_rows[LE_INDEX][j+row].quality,
												dataset->rows[j+row].rand[LE_INDEX],
												dataset->rows[j+row].rand_method[LE_INDEX],
												dataset->rows[j+row].rand_samples_count[LE_INDEX],
												LEcorr_joinUnc,
												IS_FLAG_SET(dataset->years[i].hle, H_DATASET) ? dataset->rows[j+row].value[H] : INVALID_VALUE,
												dataset->rows[j+row].value[Hcorr],
												dataset->rows[j+row].value[Hcorr25],
												dataset->rows[j+row].value[Hcorr75],
												dataset->gf_rows[H_INDEX][j+row].quality,
												dataset->rows[j+row].rand[H_INDEX],
												dataset->rows[j+row].rand_method[H_INDEX],
												dataset->rows[j+row].rand_samples_count[H_INDEX],
												Hcorr_joinUnc,
												dataset->rows[j+row].ecbcf_samples_count,
												dataset->rows[j+row].ecbcf_method + 1,
												dataset->gf_rows[G_INDEX][j+row].filled,
												dataset->gf_rows[G_INDEX][j+row].quality
				);
			}
		}
		if ( error ) {
			break;
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* save info */
	sprintf(buffer, output_file_info, output_path, dataset->details->site, "hh");
	f = fopen(buffer, "wb");
	if ( !f ) {
		puts("unable to create info file!");
		return 0;
	}
	fputs(info_hh, f);
	fclose(f);

	/* ok */
	return !error;
}

/* */
int save_output_daily(const DATASET *const dataset) {
	char buffer[256];
	int i;
	int j;
	int y;
	int row;
	PREC LEcorr_joinUnc;
	PREC Hcorr_joinUnc;
	FILE *f;
	TIMESTAMP *t;

	/* */
	assert(dataset);

	/* create file */
	sprintf(buffer, output_file_dd, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	if ( no_rand_unc ) {
		fprintf(f, output_header_dd_no_rand_unc, TIMESTAMP_STRING);
	} else {
		fprintf(f, output_header_dd, TIMESTAMP_STRING);
	}

	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? 366 : 365;
		for ( row = 0; row < y; row++ ) {
			t = timestamp_end_by_row(row*(dataset->hourly ? 24 : 48), dataset->years[i].year, dataset->details->timeres);
			/* write values */
			if ( no_rand_unc ) {
				fprintf(f, output_format_dd_no_rand_unc,	t->YYYY,
															t->MM,
															t->DD,
															row+1,
															dataset->rows_aggr[j+row].le_mean,
															dataset->rows_aggr[j+row].value[LEcorr],
															dataset->rows_aggr[j+row].value[LEcorr25],
															dataset->rows_aggr[j+row].value[LEcorr75],
															dataset->rows_aggr[j+row].quality[LE_INDEX],
															dataset->rows_aggr[j+row].h_mean,
															dataset->rows_aggr[j+row].value[Hcorr],
															dataset->rows_aggr[j+row].value[Hcorr25],
															dataset->rows_aggr[j+row].value[Hcorr75],
															dataset->rows_aggr[j+row].quality[H_INDEX],
															dataset->rows_aggr[j+row].ecbcf_samples_count,
															dataset->rows_aggr[j+row].ecbcf_method + 1,
															dataset->rows_aggr[j+row].value[G_FILLED],
															dataset->rows_aggr[j+row].quality[G_INDEX]
				);
			} else {
					LEcorr_joinUnc = INVALID_VALUE;
					Hcorr_joinUnc = INVALID_VALUE;
					if (	!IS_INVALID_VALUE(dataset->rows_aggr[j+row].rand[LE_INDEX]) &&
							!IS_INVALID_VALUE(dataset->rows_aggr[j+row].value[LEcorr25])	&&
							!IS_INVALID_VALUE(dataset->rows_aggr[j+row].value[LEcorr75]) ) {
						LEcorr_joinUnc = SQRT(
												(dataset->rows_aggr[j+row].rand[LE_INDEX] * dataset->rows_aggr[j+row].rand[LE_INDEX]) +
												(((dataset->rows_aggr[j+row].value[LEcorr75]-dataset->rows_aggr[j+row].value[LEcorr25])/IQR) *
												((dataset->rows_aggr[j+row].value[LEcorr75]-dataset->rows_aggr[j+row].value[LEcorr25])/IQR)));
					}

					if (	!IS_INVALID_VALUE(dataset->rows_aggr[j+row].rand[H_INDEX]) &&
							!IS_INVALID_VALUE(dataset->rows_aggr[j+row].value[Hcorr25])	&&
							!IS_INVALID_VALUE(dataset->rows_aggr[j+row].value[Hcorr75]) ) {
						Hcorr_joinUnc = SQRT(
												(dataset->rows_aggr[j+row].rand[H_INDEX] * dataset->rows_aggr[j+row].rand[H_INDEX]) +
												(((dataset->rows_aggr[j+row].value[Hcorr75]-dataset->rows_aggr[j+row].value[Hcorr25])/IQR) *
												((dataset->rows_aggr[j+row].value[Hcorr75]-dataset->rows_aggr[j+row].value[Hcorr25])/IQR)));
					}

					fprintf(f, output_format_dd,	t->YYYY,
													t->MM,
													t->DD,
													row+1,
													dataset->rows_aggr[j+row].le_mean,
													dataset->rows_aggr[j+row].value[LEcorr],
													dataset->rows_aggr[j+row].value[LEcorr25],
													dataset->rows_aggr[j+row].value[LEcorr75],
													dataset->rows_aggr[j+row].quality[LE_INDEX],
													dataset->rows_aggr[j+row].rand[LE_INDEX],
													LEcorr_joinUnc,
													dataset->rows_aggr[j+row].h_mean,
													dataset->rows_aggr[j+row].value[Hcorr],
													dataset->rows_aggr[j+row].value[Hcorr25],
													dataset->rows_aggr[j+row].value[Hcorr75],
													dataset->rows_aggr[j+row].quality[H_INDEX],
													dataset->rows_aggr[j+row].rand[H_INDEX],
													Hcorr_joinUnc,
													dataset->rows_aggr[j+row].ecbcf_samples_count,
													dataset->rows_aggr[j+row].ecbcf_method + 1,
													dataset->rows_aggr[j+row].value[G_FILLED],
													dataset->rows_aggr[j+row].quality[G_INDEX]
				);
			}
		}
		j += y;
	}
	
	/* close file */
	fclose(f);

	/* save info */
	sprintf(buffer, output_file_info, output_path, dataset->details->site, "dd");
	f = fopen(buffer, "wb");
	if ( !f ) {
		puts("unable to create info file!");
		return 0;
	}
	fputs(info_dd, f);
	fclose(f);

	/* ok */
	return 1;
}

/* */
int save_output_weekly(const DATASET *const dataset) {
	char *p;
	char buffer[256];
	int i;
	int j;
	int row;
	FILE *f;

	/* */
	assert(dataset);

	/* create file */
	sprintf(buffer, output_file_ww, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	if ( no_rand_unc ) {
		fprintf(f, output_header_ww_no_rand_unc, TIMESTAMP_HEADER);
	} else {
		fprintf(f, output_header_ww, TIMESTAMP_HEADER);
	}

	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		for ( row = 0; row < 52; row++ ) {
			/* write timestamp_start */
			p = timestamp_ww_get_by_row_s(row, dataset->years[i].year, dataset->details->timeres, 1);
			fprintf(f, "%s,", p);
			/* write timestamp_end */
			p = timestamp_ww_get_by_row_s(row, dataset->years[i].year, dataset->details->timeres, 0);
			fprintf(f, "%s,", p);
			/* write values */
			if ( no_rand_unc ) {
				fprintf(f, output_format_ww_no_rand_unc,
											row+1,
											dataset->rows_aggr[j+row].le_mean,
											dataset->rows_aggr[j+row].value[LEcorr],
											dataset->rows_aggr[j+row].quality[LE_INDEX],
											dataset->rows_aggr[j+row].h_mean,
											dataset->rows_aggr[j+row].value[Hcorr],
											dataset->rows_aggr[j+row].quality[H_INDEX],
											dataset->rows_aggr[j+row].ecbcf_samples_count,
											dataset->rows_aggr[j+row].ecbcf_method + 1,
											dataset->rows_aggr[j+row].value[G_FILLED],
											dataset->rows_aggr[j+row].quality[G_INDEX]
				);
			} else {
				fprintf(f, output_format_ww,
										row+1,
										dataset->rows_aggr[j+row].le_mean,
										dataset->rows_aggr[j+row].value[LEcorr],
										dataset->rows_aggr[j+row].quality[LE_INDEX],
										dataset->rows_temp[j+row].rand[LE_INDEX],
										dataset->rows_aggr[j+row].h_mean,
										dataset->rows_aggr[j+row].value[Hcorr],
										dataset->rows_aggr[j+row].quality[H_INDEX],
										dataset->rows_temp[j+row].rand[H_INDEX],
										dataset->rows_aggr[j+row].ecbcf_samples_count,
										dataset->rows_aggr[j+row].ecbcf_method + 1,
										dataset->rows_aggr[j+row].value[G_FILLED],
										dataset->rows_aggr[j+row].quality[G_INDEX]
				);
			}
		}
		j += 52;
	}
	
	/* close file */
	fclose(f);

	/* save info */
	sprintf(buffer, output_file_info, output_path, dataset->details->site, "ww");
	f = fopen(buffer, "wb");
	if ( !f ) {
		puts("unable to create info file!");
		return 0;
	}
	fputs(info_ww, f);
	fclose(f);

	/* ok */
	return 1;
}

/* */
int save_output_monthly(const DATASET *const dataset) {
	int i;
	int j;
	int year;
	int row;
	char buffer[256];
	FILE *f;

	/* */
	assert(dataset);

	/* create file */
	sprintf(buffer, output_file_mm, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	if ( no_rand_unc ) {
		fprintf(f, output_header_mm_no_rand_unc, TIMESTAMP_STRING);
	} else {
		fprintf(f, output_header_mm, TIMESTAMP_STRING);
	}

	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		for ( row = 0; row < 12; row++ ) {
			/* write values */
			if ( no_rand_unc ) {
				fprintf(f, output_format_mm_no_rand_unc,
											year,
											row+1,
											dataset->rows_aggr[j+row].le_mean,
											dataset->rows_aggr[j+row].value[LEcorr],
											dataset->rows_aggr[j+row].quality[LE_INDEX],
											dataset->rows_aggr[j+row].h_mean,
											dataset->rows_aggr[j+row].value[Hcorr],
											dataset->rows_aggr[j+row].quality[H_INDEX],
											dataset->rows_aggr[j+row].ecbcf_samples_count,
											dataset->rows_aggr[j+row].ecbcf_method + 1,
											dataset->rows_aggr[j+row].value[G_FILLED],
											dataset->rows_aggr[j+row].quality[G_INDEX]
				);
			} else {
				fprintf(f, output_format_mm,
										year,
										row+1,
										dataset->rows_aggr[j+row].le_mean,
										dataset->rows_aggr[j+row].value[LEcorr],
										dataset->rows_aggr[j+row].quality[LE_INDEX],
										dataset->rows_temp[j+row].rand[LE_INDEX],
										dataset->rows_aggr[j+row].h_mean,
										dataset->rows_aggr[j+row].value[Hcorr],
										dataset->rows_aggr[j+row].quality[H_INDEX],
										dataset->rows_temp[j+row].rand[H_INDEX],
										dataset->rows_aggr[j+row].ecbcf_samples_count,
										dataset->rows_aggr[j+row].ecbcf_method + 1,
										dataset->rows_aggr[j+row].value[G_FILLED],
										dataset->rows_aggr[j+row].quality[G_INDEX]
			);
			}
		}
		j += 12;
	}
	
	/* close file */
	fclose(f);

	/* save info */
	sprintf(buffer, output_file_info, output_path, dataset->details->site, "mm");
	f = fopen(buffer, "wb");
	if ( !f ) {
		puts("unable to create info file!");
		return 0;
	}
	fputs(info_mm, f);
	fclose(f);

	/* ok */
	return 1;
}

/* */
int save_output_yearly(const DATASET *const dataset) {
	int i;
	char buffer[256];
	FILE *f;

	/* */
	assert(dataset);

	/* create file */
	sprintf(buffer, output_file_yy, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	if ( no_rand_unc ) {
		fprintf(f, output_header_yy_no_rand_unc, TIMESTAMP_STRING);
	} else {
		fprintf(f, output_header_yy, TIMESTAMP_STRING);
	}

	/* */
	for ( i = 0; i < dataset->years_count; i++ ) {
		/* write values */
		if ( no_rand_unc ) {
			fprintf(f, output_format_yy_no_rand_unc,
										dataset->years[i].year,
										dataset->rows_aggr[i].le_mean,
										dataset->rows_aggr[i].value[LEcorr],
										dataset->rows_aggr[i].quality[LE_INDEX],
										dataset->rows_aggr[i].h_mean,
										dataset->rows_aggr[i].value[Hcorr],
										dataset->rows_aggr[i].quality[H_INDEX],
										dataset->rows_aggr[i].ecbcf_samples_count,
										dataset->rows_aggr[i].ecbcf_method + 1,
										dataset->rows_aggr[i].value[G_FILLED],
										dataset->rows_aggr[i].quality[G_INDEX]
			);
		} else {
			fprintf(f, output_format_yy,
									dataset->years[i].year,
									dataset->rows_aggr[i].le_mean,
									dataset->rows_aggr[i].value[LEcorr],
									dataset->rows_aggr[i].quality[LE_INDEX],
									dataset->rows_temp[i].rand[LE_INDEX],
									dataset->rows_aggr[i].h_mean,
									dataset->rows_aggr[i].value[Hcorr],
									dataset->rows_aggr[i].quality[H_INDEX],
									dataset->rows_temp[i].rand[H_INDEX],
									dataset->rows_aggr[i].ecbcf_samples_count,
									dataset->rows_aggr[i].ecbcf_method + 1,
									dataset->rows_aggr[i].value[G_FILLED],
									dataset->rows_aggr[i].quality[G_INDEX]
			);
		}
	}
	
	/* close file */
	fclose(f);

	/* save info */
	sprintf(buffer, output_file_info, output_path, dataset->details->site, "yy");
	f = fopen(buffer, "wb");
	if ( !f ) {
		puts("unable to create info file!");
		return 0;
	}
	fputs(info_yy, f);
	fclose(f);

	/* ok */
	return 1;
}

/* */
int debug_save_original(const DATASET *const dataset) {
	char *p;
	char buffer[BUFFER_SIZE];
	int i;
	int j;
	int y;
	int row;
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_debug_original, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_debug_original, TIMESTAMP_HEADER);
	
	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			y /= 2;
		}
		for ( row = 0; row < y; row++ ) {
			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fprintf(f, ",%s,", p);
			/* write values */
			fprintf(f, output_format_debug_original,	get_dtime_by_row(row, dataset->hourly),
														dataset->rows[j+row].value[H],
														dataset->rows[j+row].value[LE],
														dataset->rows[j+row].value[SWIN],
														dataset->rows[j+row].value[TA],
														dataset->rows[j+row].value[RH],
														dataset->rows[j+row].value[G],
														dataset->rows[j+row].value[VPD],
														dataset->rows[j+row].value[NETRAD]
			);
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* ok */
	return 1;
}

/*  */
int debug_save_gapfilled(const DATASET *const dataset) {
	char *p;
	char buffer[BUFFER_SIZE];
	int i;
	int j;
	int y;
	int row;
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_debug_gapfilled, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_debug_gapfilled, TIMESTAMP_HEADER);
	
	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			y /= 2;
		}
		for ( row = 0; row < y; row++ ) {
			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fprintf(f, ",%s,", p);
			/* write values */
			fprintf(f, output_format_debug_gapfilled,	get_dtime_by_row(row, dataset->hourly),
														dataset->rows[j+row].value[H],
														dataset->gf_rows[H_INDEX][j+row].quality,
														dataset->gf_rows[H_INDEX][j+row].stddev,
														dataset->rows[j+row].value[LE],
														dataset->gf_rows[LE_INDEX][j+row].quality,
														dataset->gf_rows[LE_INDEX][j+row].stddev,
														dataset->rows[j+row].value[NETRAD],
														dataset->rows[j+row].value[G],
														dataset->gf_rows[G_INDEX][j+row].filled,
														dataset->gf_rows[G_INDEX][j+row].quality,
														dataset->gf_rows[G_INDEX][j+row].stddev
			);
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* ok */
	return 1;
}

/* */
int debug_save_ecbcf_hh(const DATASET *const dataset, const PREC *const EBCcfs, const PREC *const EBCcfs_temp) {
	char *p;
	char buffer[BUFFER_SIZE];
	int i;
	int j;
	int y;
	int row;
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_debug_ecbcf_hh, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_debug_ecbcf_hh, TIMESTAMP_HEADER);
	
	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			y /= 2;
		}
		for ( row = 0; row < y; row++ ) {
			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(row, dataset->years[i].year, dataset->details->timeres); 
			fprintf(f, ",%s,", p);
			/* write values */
			fprintf(f, output_format_debug_ecbcf_hh,	get_dtime_by_row(row, dataset->hourly),
														EBCcfs[j+row],
														EBCcfs_temp[j+row]
			);
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* ok */
	return 1;
}

/* */
int debug_save_aggr_by_day(const DATASET *const dataset, const PREC *const ECBcfs, const PREC *const ECBcfs_temp) {
	char buffer[BUFFER_SIZE];
	int i;
	int j;
	int y;
	int row;
	FILE *f;
	TIMESTAMP *t;

	/* create output file */
	sprintf(buffer, output_file_debug_aggr_by_day, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_debug_aggr_by_day, TIMESTAMP_STRING);
	
	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? 366 : 365;
		for ( row = 0; row < y; row++ ) {
			t = timestamp_end_by_row(row*(dataset->hourly ? 24: 48), dataset->years[i].year, dataset->details->timeres);
			/* write values */
			fprintf(f, output_format_debug_aggr_by_day,	t->YYYY,
														t->MM,
														t->DD,
														row+1,
														dataset->rows_aggr[j+row].value[H],
														dataset->rows_aggr[j+row].quality[H_INDEX],
														dataset->rows_aggr[j+row].value[LE],
														dataset->rows_aggr[j+row].quality[LE_INDEX],
														dataset->rows_aggr[j+row].value[G],
														dataset->rows_aggr[j+row].value[NETRAD],
														ECBcfs_temp[j+row],
														ECBcfs[j+row]
			);
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* ok */
	return 1;
}

/* */
int debug_save_aggr_by_week(const DATASET *const dataset, const PREC *const ECBcfs, const PREC *const ECBcfs_temp) {
	int i;
	int row;
	int year;
	char buffer[BUFFER_SIZE];
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_debug_aggr_by_week, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_debug_aggr_by_week, TIMESTAMP_STRING);
	
	/* write results */
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		for ( row = 0; row < 52; row++ ) {
			fprintf(f, output_format_debug_aggr_by_week,
														year,
														row+1,
														dataset->rows_aggr[i*52+row].value[H],
														dataset->rows_aggr[i*52+row].quality[H_INDEX],
														dataset->rows_aggr[i*52+row].value[LE],
														dataset->rows_aggr[i*52+row].quality[LE_INDEX],
														dataset->rows_aggr[i*52+row].value[G],
														dataset->rows_aggr[i*52+row].value[NETRAD],
														ECBcfs_temp[i*52+row],
														ECBcfs[i*52+row]


			);
		}
	}

	/* close file */
	fclose(f);

	/* ok */
	return 1;
}

/* */
int debug_save_aggr_by_month(const DATASET *const dataset, const PREC *const ECBcfs, const PREC *const ECBcfs_temp) {
	int i;
	int row;
	int year;
	char buffer[BUFFER_SIZE];
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_debug_aggr_by_month, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_debug_aggr_by_month, TIMESTAMP_STRING);
	
	/* write results */
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		for ( row = 0; row < 12; row++ ) {
			fprintf(f, output_format_debug_aggr_by_month,
														year,
														row+1,
														dataset->rows_aggr[i*12+row].value[H],
														dataset->rows_aggr[i*12+row].quality[H_INDEX],
														dataset->rows_aggr[i*12+row].value[LE],
														dataset->rows_aggr[i*12+row].quality[LE_INDEX],
														dataset->rows_aggr[i*12+row].value[G],
														dataset->rows_aggr[i*12+row].value[NETRAD],
														ECBcfs_temp[i*12+row],
														ECBcfs[i*12+row]


			);
		}
	}

	/* close file */
	fclose(f);

	/* ok */
	return 1;
}


/* */
int debug_save_aggr_by_year(const DATASET *const dataset, const PREC *const ECBcfs, const PREC *const ECBcfs_temp) {
	int i;
	int year;
	char buffer[BUFFER_SIZE];
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_debug_aggr_by_year, output_path, dataset->details->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_debug_aggr_by_year, TIMESTAMP_STRING);
	
	/* write results */
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		fprintf(f, output_format_debug_aggr_by_year,
													year,
													dataset->rows_aggr[i].value[H],
													dataset->rows_aggr[i].quality[H_INDEX],
													dataset->rows_aggr[i].value[LE],
													dataset->rows_aggr[i].quality[LE_INDEX],
													dataset->rows_aggr[i].value[G],
													dataset->rows_aggr[i].value[NETRAD],
													ECBcfs_temp[i],
													ECBcfs[i]
		);
	}

	/* close file */
	fclose(f);

	/* ok */
	return 1;
}


/* */
static check_le_h(DATASET *const dataset) {
	int i;
	int flag = 0;

	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( ! IS_INVALID_VALUE(dataset->rows[i].value[LE]) || ! IS_INVALID_VALUE(dataset->rows[i].value[H]) ) {
			flag = 1;
			break;
		}
	}

	if ( !flag ) {
		puts("no valid Le and H found.\n");
	}

	return flag;
}

/* */
static int get_meteo(DATASET *const dataset) {
	int i;
	int y;
	int element;
	int index;
	int start_year;
	int rows_count;
	int TA;
	int VPD;
	int SWIN;
	int TA_QC;
	int VPD_QC;
	int SWIN_QC;
	int error;
	int current_row;
	char buffer[BUFFER_SIZE];
	char *token;
	char *p;
	FILE *f;
	TIMESTAMP *t;
	PREC value;
	DD details;

	/* */
	assert(dataset);

	/* check if file exists */
	sprintf(buffer, "%s%s_meteo_hh.csv", input_path, dataset->details->site);
	f = fopen(buffer, "r");
	if ( !f ) {
		/* no found, ok*/
		puts("nothing found.");
		return 1;
	}

	/* get header */
	if ( !fgets(buffer, BUFFER_SIZE, f) ) {
		puts("missing header ?");
		fclose(f);
		return 0;
	}

	/* parse header */
	TA = -1;
	SWIN = -1;
	VPD = -1;
	for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
		if ( ! string_compare_i(token, "TA_m") ) {
			TA = i;
		} else if ( ! string_compare_i(token, "SW_IN_m") ) {
			SWIN = i;
		} else if ( ! string_compare_i(token, "VPD_m") ) {
			VPD = i;
		} else if ( ! string_compare_i(token, "TA_mqc") ) {
			TA_QC = i;
		} else if ( ! string_compare_i(token, "SW_IN_mqc") ) {
			SWIN_QC = i;
		} else if ( ! string_compare_i(token, "VPD_mqc") ) {
			VPD_QC = i;
		}
	}

	/* how many vars we've found */
	i = 0;
	if ( TA != -1 ) ++i;
	if ( SWIN != -1 ) ++i;
	if ( VPD != -1 ) ++i;

	/* nothing found! */
	if ( !i ) {
		puts("nothing found!");
		fclose(f);
		return 1;
	}

	/* check indexes */
	if ( !((TA < SWIN) && (SWIN < VPD)) ) {
		puts("bad indexes for columns.");
		fclose(f);
		return 0;
	}

	/* get starting year */
	if ( !fgets(buffer, BUFFER_SIZE, f) ) {
		puts("bad file.");
		fclose(f);
		return 0;
	}

	/* get isodate */
	t = get_timestamp(string_tokenizer(buffer, dataset_delimiter, &p));
	if ( ! t ) {
		puts("bad file.");
		fclose(f);
		return 0;
	}
	start_year = t->YYYY;
	free(t);
	if ( start_year > dataset->years[0].year ) {
		puts("nothing found!");
		fclose(f);
		return 1;
	}

	/* set timeres */
	details.timeres = dataset->details->timeres;

	/* skip rows */
	index = 0;	
	for ( i = start_year;  i < dataset->years[0].year; i++ ) {
		details.year = i;
		index += get_rows_count_by_dd(&details);
	}
	fseek(f, 0, SEEK_SET);
	for ( i = 0; i < index + 1; i++ ) { /* +1 for skip header */
		if ( !get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			puts("bad file.");
			fclose(f);
			return 0;
		}
	}
	puts("found");

	/* get values */
	index = 0;
	for ( y = 0; y < dataset->years_count; y++ ) {	
		printf("importing meteo %d...", dataset->years[y].year);

		element = 0;
		details.year = dataset->years[y].year;
		rows_count = get_rows_count_by_dd(&details);
		if ( !rows_count ) {
			printf("bad rows count for year %d\n", details.year);
			fclose(f);
			return 0;
		}
		while ( fgets(buffer, BUFFER_SIZE, f) ) {
			for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), i++ ) {
				if ( ! i ) {
					// skip TIMESTAMP_START
					continue;
				}
				// get TIMESTAMP_END
				if ( 1 == i ) {
					t = get_timestamp(token);
					if ( ! t ) {
						fclose(f);
						return 0;
					}

					/* check year */
					if ( details.year != t->YYYY ) {
						/* check for last row */
						if ( !(	(t->YYYY == details.year+1) &&
								(1 == t->MM) &&
								(1 == t->DD) &&
								(0 == t->hh) &&
								(0 == t->mm)) ) {
									printf("bad row: %s\n", token);
							free(t);
							fclose(f);
							return 0;

						}
					}

					current_row = get_row_by_timestamp(t, dataset->details->timeres);
					free(t);
					if ( element != current_row ) {
						printf("bad timestamp: %s\n", token);
						fclose(f);
						return 0;
					}							
				} else {
					value = convert_string_to_prec(token, &error);
					if ( error ) {
						printf("unable to convert value %s at row %d, column %d\n", token, current_row+1, i+1);
						fclose(f);
						return 0;
					}
					
					if ( i == TA ) {
						dataset->rows[index+current_row].value[TA] = value;
					} else if ( i == SWIN ) {
						dataset->rows[index+current_row].value[SWIN] = value;
					} else if ( i == VPD ) {
						dataset->rows[index+current_row].value[VPD] = value;
					} else if ( i == TA_QC ) {
						dataset->rows[index+current_row].value[TA_QC_GF] = value;
					} else if ( i == SWIN_QC ) {
						dataset->rows[index+current_row].value[SWIN_QC_GF] = value;
					} else if ( i == VPD_QC ) {
						dataset->rows[index+current_row].value[VPD_QC_GF] = value;
					}
				}
			}
			
			if ( ++element == rows_count ) {
				break;
			}
		}
		puts("ok");
		index += rows_count;
	}

	/* */
	fclose(f);
	
	/* ok */
	return 1;
}


/* */
int compute_datasets(DATASET *const datasets, const int datasets_count) {
	int i;
	int j;
	int dataset;
	int year;
	int index;
	int error;
	int rows_count_per_year;
	int no_gaps_filled_count;
	int g_valid_rows_count;
	PREC *EBCcfs;
	PREC *EBCcfs_temp;
	PREC *temp;
	DATASET *current_dataset;

	/* loop on each dataset */
	for ( dataset = 0; dataset < datasets_count; dataset++ ) {
		/* set pointers */
		current_dataset = &datasets[dataset];

		/* alloc memory for EBCcfs */
		EBCcfs = malloc(current_dataset->rows_count*sizeof*EBCcfs);
		if ( !EBCcfs ) {
			puts(err_out_of_memory);
			return 1;
		}

		EBCcfs_temp = malloc(current_dataset->rows_count*sizeof*EBCcfs_temp);
		if ( !EBCcfs_temp ) {
			puts(err_out_of_memory);
			free(EBCcfs);
			return 1;
		}

		temp = malloc(current_dataset->rows_count*sizeof*temp);
		if ( !temp ) {
			puts(err_out_of_memory);
			free(EBCcfs_temp);
			free(EBCcfs);
			return 1;
		}

		/*
		for ( i = 0; i < VARS_TO_FILL; i++ ) {
			current->dataset->gf_rows[i] = NULL;
		}
		*/

		/* msg */
		printf("processing %s, %d year%s...\n", current_dataset->details->site,
												current_dataset->years_count,
												(current_dataset->years_count > 1) ? "s" : ""
		);

		/* alloc memory for rows */
		current_dataset->rows = malloc(current_dataset->rows_count*sizeof*current_dataset->rows);
		if ( !current_dataset->rows ) {
			puts(err_out_of_memory);
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			return 0;
		}

		/* alloc memory for aggregated rows */
		current_dataset->rows_aggr = malloc(current_dataset->rows_aggr_count*sizeof*current_dataset->rows_aggr);
		if ( !current_dataset->rows_aggr ) {
			puts(err_out_of_memory);
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->rows);
			current_dataset->rows = NULL; /* mandatory */
			return 0;
		}

		/* alloc memory for daily */
		current_dataset->rows_daily = malloc(current_dataset->rows_aggr_count*sizeof*current_dataset->rows_aggr);
		if ( !current_dataset->rows_daily ) {
			puts(err_out_of_memory);
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL; /* mandatory */
			current_dataset->rows_aggr = NULL; /* mandatory */
			return 0;
		}

		/* alloc memory for temp rows */
		current_dataset->rows_temp_count = current_dataset->years_count * 52;  
		current_dataset->rows_temp = malloc(current_dataset->rows_temp_count*sizeof*current_dataset->rows_temp);
		if ( !current_dataset->rows_temp ) {
			puts(err_out_of_memory);
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			return 0;
		}

		/* alloc memory for indexes */
		current_dataset->indexes_count = current_dataset->rows_count;
		current_dataset->indexes = malloc(current_dataset->indexes_count*sizeof*current_dataset->indexes);
		if ( !current_dataset->indexes ) {
			puts(err_out_of_memory);
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_temp); current_dataset->rows_temp = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
		}

		/* loop on each year */
		error = 0;
		index = 0;
		for ( year = 0; year < current_dataset->years_count; year++ ) {
			/* msg */
			printf("importing year %d...", current_dataset->years[year].year);

			/* compute rows count per year */
			rows_count_per_year = IS_LEAP_YEAR(current_dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( current_dataset->hourly ) {
				rows_count_per_year /= 2;
			}

			/* year exists ? */
			if ( current_dataset->years[year].exist ) {
				/* import values */
				if ( ! import_values(current_dataset, year, rows_count_per_year, index) ) {
					error = 1;
					break;
				}
			} else {
				printf("nothing found, adding null values...");
				for ( i = 0; i < rows_count_per_year; i++ ) {
					for ( j = 0; j < DATASET_VALUES_TO_AGGR; j++ ) {
						current_dataset->rows[index+i].value[j] = INVALID_VALUE;
					}
					current_dataset->rows[index+i].value[SWIN_QC_GF] = INVALID_VALUE;
					current_dataset->rows[index+i].value[TA_QC_GF] = INVALID_VALUE;
					current_dataset->rows[index+i].value[VPD_QC_GF] = INVALID_VALUE;
				}
			}

			/* update index */
			index += rows_count_per_year;

			/* msg */
			puts("ok");
		}

		/* check */
		if ( index != current_dataset->rows_count ) {
			puts("unable to get all values!");
			error = 1;
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* invalidate qcs and count valid G */
		g_valid_rows_count = 0;
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			current_dataset->rows[i].value[SWIN_QC_GF] = INVALID_VALUE;
			current_dataset->rows[i].value[TA_QC_GF] = INVALID_VALUE;
			current_dataset->rows[i].value[VPD_QC_GF] = INVALID_VALUE;

			if ( ! IS_INVALID_VALUE(current_dataset->rows[i].value[G]) ) {
				++g_valid_rows_count;
			}
		}

		/* debug ? */
		if ( debug || multi ) {
			printf("saving original dataset...");
			if ( debug_save_original(current_dataset) ) {
				puts("ok");
			}
			if ( multi ) {
				continue;
			}
		}

		if ( !check_le_h(current_dataset) ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		printf("checking meteos...");
		if ( !get_meteo(current_dataset) ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* gapfilling LE */
		printf("gapfilling LE...");
		current_dataset->gf_rows[LE_INDEX] = gf_mds(current_dataset->rows->value,
													sizeof(ROW),
													current_dataset->rows_count,
													DATASET_VALUES,
													current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
													GF_DRIVER_1_TOLERANCE_MIN,
													GF_DRIVER_1_TOLERANCE_MAX,
													GF_DRIVER_2A_TOLERANCE_MIN,
													GF_DRIVER_2A_TOLERANCE_MAX,
													GF_DRIVER_2B_TOLERANCE_MIN,
													GF_DRIVER_2B_TOLERANCE_MAX,
													LE,
													SWIN,
													TA,
													VPD,
													SWIN_QC_GF,
													TA_QC_GF,
													VPD_QC_GF,
													qc_gf_threshold,
													qc_gf_threshold,
													qc_gf_threshold,
													GF_ROWS_MIN,
													1,
													-1,
													-1,
													&no_gaps_filled_count,
													0,
													0,
													0,
													NULL,
													0);
		
		if ( ! current_dataset->gf_rows[LE_INDEX] ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		if ( no_gaps_filled_count ) {
			printf("unable to fill %d values for LE.\n", no_gaps_filled_count);
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* msg */
		puts("ok");

		/* gapfilling H */
		printf("gapfilling H...");
		current_dataset->gf_rows[H_INDEX] = gf_mds(	current_dataset->rows->value,
													sizeof(ROW),
													current_dataset->rows_count,
													DATASET_VALUES,
													current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
													GF_DRIVER_1_TOLERANCE_MIN,
													GF_DRIVER_1_TOLERANCE_MAX,
													GF_DRIVER_2A_TOLERANCE_MIN,
													GF_DRIVER_2A_TOLERANCE_MAX,
													GF_DRIVER_2B_TOLERANCE_MIN,
													GF_DRIVER_2B_TOLERANCE_MAX,
													H,
													SWIN,
													TA,
													VPD,
													SWIN_QC_GF,
													TA_QC_GF,
													VPD_QC_GF,
													qc_gf_threshold,
													qc_gf_threshold,
													qc_gf_threshold,
													GF_ROWS_MIN,
													1,
													-1,
													-1,
													&no_gaps_filled_count,
													0,
													0,
													0,
													NULL,
													0);
		if ( ! current_dataset->gf_rows[H_INDEX] ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		if ( no_gaps_filled_count ) {
			printf("unable to fill %d values for H.\n", no_gaps_filled_count);
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* msg */
		puts("ok");

		/* gapfilling G */
		if ( g_valid_rows_count ) {
			printf("gapfilling G...");
			current_dataset->gf_rows[G_INDEX] = gf_mds(	current_dataset->rows->value,
																sizeof(ROW),
																current_dataset->rows_count,
																DATASET_VALUES,
																current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
																GF_DRIVER_1_TOLERANCE_MIN,
																GF_DRIVER_1_TOLERANCE_MAX,
																GF_DRIVER_2A_TOLERANCE_MIN,
																INVALID_VALUE,
																GF_DRIVER_2B_TOLERANCE_MIN,
																INVALID_VALUE,
																G,
																SWIN,
																TA,
																VPD,
																SWIN_QC_GF,
																TA_QC_GF,
																VPD_QC_GF,
																qc_gf_threshold,
																qc_gf_threshold,
																qc_gf_threshold,
																GF_ROWS_MIN,
																0, /* do not compute hat for G */
																-1,
																-1,
																&no_gaps_filled_count,
																0,
																45,
																0,
																NULL,
																0);		
		} else {
			/* FIX: alloc an empty array */
			printf("gapfilling G...");
			current_dataset->gf_rows[G_INDEX] = malloc(current_dataset->rows_count*sizeof*current_dataset->gf_rows[G_INDEX]);
			if ( ! current_dataset->gf_rows[G_INDEX] ) {
				puts(err_out_of_memory);
				free(temp);
				free(EBCcfs_temp);
				free(EBCcfs);
				free(current_dataset->indexes); current_dataset->indexes = NULL;
				free(current_dataset->rows_temp);
				free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
				free(current_dataset->rows_aggr);
				free(current_dataset->rows);
				current_dataset->rows = NULL;		/* mandatory */
				current_dataset->rows_aggr = NULL;	/* mandatory */
				current_dataset->rows_temp = NULL;	/* mandatory */
				continue;
			}
			/* reset */
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->gf_rows[G_INDEX][i].mask = 0;
				current_dataset->gf_rows[G_INDEX][i].similiar = INVALID_VALUE;
				current_dataset->gf_rows[G_INDEX][i].stddev = INVALID_VALUE;
				current_dataset->gf_rows[G_INDEX][i].filled = INVALID_VALUE;
				current_dataset->gf_rows[G_INDEX][i].quality = INVALID_VALUE;
				current_dataset->gf_rows[G_INDEX][i].time_window = 0;
				current_dataset->gf_rows[G_INDEX][i].samples_count = 0;
				current_dataset->gf_rows[G_INDEX][i].method = 0;
			}
		}

		/* msg */
		puts("ok");

		/* update dataset by gapfilled value */
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			if ( IS_INVALID_VALUE(current_dataset->rows[i].value[H]) ) {
				current_dataset->rows[i].value[H] = current_dataset->gf_rows[H_INDEX][i].filled;
				current_dataset->rows[i].rand_method[H_INDEX] = 2;
			} else {
				current_dataset->gf_rows[H_INDEX][i].quality = 0;
				current_dataset->rows[i].rand_method[H_INDEX] = 1;
			}

			if ( IS_INVALID_VALUE(current_dataset->rows[i].value[LE]) ) {
				current_dataset->rows[i].value[LE] = current_dataset->gf_rows[LE_INDEX][i].filled;
				current_dataset->rows[i].rand_method[LE_INDEX] = 2;
			} else {
				current_dataset->gf_rows[LE_INDEX][i].quality = 0;
				current_dataset->rows[i].rand_method[LE_INDEX] = 1;
			}

			current_dataset->rows[i].rand[H_INDEX] = INVALID_VALUE;
			current_dataset->rows[i].rand_samples_count[H_INDEX] = 0;
			current_dataset->rows[i].rand[LE_INDEX] = INVALID_VALUE;
			current_dataset->rows[i].rand_samples_count[LE_INDEX] = 0;

			if ( ! IS_INVALID_VALUE(current_dataset->rows[i].value[G]) ) {
				current_dataset->gf_rows[G_INDEX][i].quality = 0;
			}
		}

		/* debug ? */
		if ( debug ) {
			printf("saving gapfilled dataset...");
			if ( debug_save_gapfilled(current_dataset) ) {
				puts("ok");
			}
		}

		/* random unc */
		if ( ! no_rand_unc ) {
			printf("computing random uncertainty..."); 
			random_method_1(current_dataset, LE_INDEX);
			if ( ! random_method_2(current_dataset, LE_INDEX) ) {
				free(temp);
				free(EBCcfs_temp);
				free(EBCcfs);
				free(current_dataset->indexes); current_dataset->indexes = NULL;
				free(current_dataset->rows_temp);
				free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
				free(current_dataset->rows_aggr);
				free(current_dataset->rows);
				current_dataset->rows = NULL;		/* mandatory */
				current_dataset->rows_aggr = NULL;	/* mandatory */
				current_dataset->rows_temp = NULL;	/* mandatory */
				continue;
			}

			random_method_1(current_dataset, H_INDEX);
			if ( ! random_method_2(current_dataset, H_INDEX) ) {
				free(temp);
				free(EBCcfs_temp);
				free(EBCcfs);
				free(current_dataset->indexes); current_dataset->indexes = NULL;
				free(current_dataset->rows_temp);
				free(current_dataset->rows_aggr);
				free(current_dataset->rows);
				current_dataset->rows = NULL;		/* mandatory */
				current_dataset->rows_aggr = NULL;	/* mandatory */
				current_dataset->rows_temp = NULL;	/* mandatory */
				continue;
			}
			puts("ok");
		}

		/* update bitmask and reset values for ECBCF */
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			current_dataset->rows[i].ecbcf_mask = 0;

			/* update bitmask */
			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[H]) ) {
				current_dataset->rows[i].ecbcf_mask |= H_VALID;
			}

			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[LE]) ) {
				current_dataset->rows[i].ecbcf_mask |= LE_VALID;
			}

			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[G]) ) {
				current_dataset->rows[i].ecbcf_mask |= G_VALID;
			}

			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[NETRAD]) ) {
				current_dataset->rows[i].ecbcf_mask |= NETRAD_VALID;
			}
			
			current_dataset->rows[i].value[LEcorr] = INVALID_VALUE;
			current_dataset->rows[i].value[LEcorr25] = INVALID_VALUE;
			current_dataset->rows[i].value[LEcorr75] = INVALID_VALUE;
			current_dataset->rows[i].value[Hcorr] = INVALID_VALUE;
			current_dataset->rows[i].value[Hcorr25] = INVALID_VALUE;
			current_dataset->rows[i].value[Hcorr75] = INVALID_VALUE;
			current_dataset->rows[i].value[p25] = INVALID_VALUE;
			current_dataset->rows[i].value[p50] = INVALID_VALUE;
			current_dataset->rows[i].value[p75] = INVALID_VALUE;
			current_dataset->rows[i].ecbcf_samples_count = 0;
			current_dataset->rows[i].ecbcf_method = 0;
		}

		/* computing ecbcf_temp */
		printf("computing ecbcf for midhourly...");
		if ( ! ecbcf_temp_hh(current_dataset, EBCcfs, EBCcfs_temp, temp) ) {
			/* free memory */

			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}
		puts("ok");

		/* debug ? */
		if ( debug ) {
			printf("saving ecbcf midhourly...");
			if ( debug_save_ecbcf_hh(current_dataset, EBCcfs_temp, EBCcfs) ) {
				puts("ok");
			}
		}

		/* apply new ecbcf for hh */
		printf("applying ecbcf method to hh...");
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			/* reset method */
			current_dataset->rows[i].ecbcf_method = 0;
			if ( !ecbcf_hh(current_dataset, i, EBCcfs, EBCcfs_temp, temp, window_size, window_size_method_2_3_hh) ) {
				error = 1;
				break;
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 2 for hh*/
		for ( i = 0; i < current_dataset->rows_count; i++ ) {			
			if ( SECOND == current_dataset->rows[i].ecbcf_method) {
				if ( !ecbcf_hh(current_dataset, i, EBCcfs, EBCcfs_temp, temp, window_size, window_size_method_2_3_hh) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 3 for hh */
		for ( i = 0; i < current_dataset->rows_count; i++ ) {			
			if ( THIRD == current_dataset->rows[i].ecbcf_method) {
				if ( !ecbcf_hh(current_dataset, i, EBCcfs, EBCcfs_temp, temp, window_size, window_size_method_2_3_hh) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}
		puts("ok");

		/* save */
		printf("saving results for midhourly...");
		if ( save_output_midhourly(current_dataset) ) {
			puts("ok");
		}

		/* aggr by day */
		printf("daily aggregation...");
		if ( !aggr_by_days(current_dataset, EBCcfs, EBCcfs_temp) ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}
		puts("ok");

		/* copy...TODO: do not allocate an entire struct for few variables */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			current_dataset->rows_daily[i].rand[LE_INDEX] = current_dataset->rows_aggr[i].rand[LE_INDEX];
			current_dataset->rows_daily[i].rand_samples_count[LE_INDEX] = current_dataset->rows_aggr[i].rand_samples_count[LE_INDEX];
			current_dataset->rows_daily[i].rand[H_INDEX] = current_dataset->rows_aggr[i].rand[H_INDEX];
			current_dataset->rows_daily[i].rand_samples_count[H_INDEX] = current_dataset->rows_aggr[i].rand_samples_count[H_INDEX];
		}

		/* debug mode ? */
		if ( debug ) {
			printf("saving daily aggregation...");
			if ( debug_save_aggr_by_day(current_dataset, EBCcfs, EBCcfs_temp) ) {
				puts("ok");
			}
		}
				
		/* apply ecbcf for daily */
		printf("applying ecbcf methods to daily...");
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( !ecbcf_dd(current_dataset, i, EBCcfs, EBCcfs_temp, temp, window_size_daily, window_size_method_2_3_dd) ) {
				error = 1;
				break;
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 2, daily */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( SECOND == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_dd(current_dataset, i, EBCcfs, EBCcfs_temp, temp, window_size_daily, window_size_method_2_3_dd) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 3, daily */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( THIRD == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_dd(current_dataset, i, EBCcfs, EBCcfs_temp, temp, window_size_daily, window_size_method_2_3_dd) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}
		puts("ok");

		/* saving ecbcf daily */
		printf("saving results for daily...");
		if ( save_output_daily(current_dataset) ) {
			puts("ok");
		}

		/* aggr by week */
		printf("weekly aggregation...");
		if ( !aggr_by_weeks(current_dataset, EBCcfs, EBCcfs_temp) ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 2, weekly */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( SECOND == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_ww(current_dataset, i, EBCcfs, window_size_weekly) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 3, weekly */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( THIRD == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_ww(current_dataset, i, EBCcfs, window_size_weekly) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}
		puts("ok");

		/* debug mode ? */
		if ( debug ) {
			printf("saving weekly aggregation...");
			if ( debug_save_aggr_by_week(current_dataset, EBCcfs, EBCcfs_temp) ) {
				puts("ok");
			}
		}

		/* saving ecbcf weekly */
		printf("saving results for weekly...");
		if ( save_output_weekly(current_dataset) ) {
			puts("ok");
		}

		/* aggr by month */
		printf("monthly aggregation...");
		if ( !aggr_by_months(current_dataset, EBCcfs, EBCcfs_temp) ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 2, monthly */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( SECOND == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_mm(current_dataset, i, EBCcfs, window_size_monthly) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 3, monthly */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( THIRD == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_mm(current_dataset, i, EBCcfs, window_size_monthly) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}
		puts("ok");

		/* debug mode ? */
		if ( debug ) {
			printf("saving monthly aggregation...");
			if ( debug_save_aggr_by_month(current_dataset, EBCcfs, EBCcfs_temp) ) {
				puts("ok");
			}
		}

		/* saving ecbcf monthly */
		printf("saving results for monthly...");
		if ( save_output_monthly(current_dataset) ) {
			puts("ok");
		}

		/* aggr by year */
		printf("yearly aggregation...");
		if ( !aggr_by_years(current_dataset, EBCcfs, EBCcfs_temp) ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 2, yearly */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( SECOND == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_yy(current_dataset, i, EBCcfs) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}

		/* method 3, yearly */
		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			if ( THIRD == current_dataset->rows_aggr[i].ecbcf_method ) {
				if ( !ecbcf_yy(current_dataset, i, EBCcfs) ) {
					error = 1;
					break;
				}
			}
		}

		/* error ? */
		if ( error ) {
			/* free memory */
			free(temp);
			free(EBCcfs_temp);
			free(EBCcfs);
			free(current_dataset->indexes); current_dataset->indexes = NULL;
			free(current_dataset->rows_temp);
			free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
			free(current_dataset->rows_aggr);
			free(current_dataset->rows);
			current_dataset->rows = NULL;		/* mandatory */
			current_dataset->rows_aggr = NULL;	/* mandatory */
			current_dataset->rows_temp = NULL;	/* mandatory */
			continue;
		}
		puts("ok");

		/* debug mode ? */
		if ( debug ) {
			printf("saving yearly aggregation...");
			if ( debug_save_aggr_by_year(current_dataset, EBCcfs, EBCcfs_temp) ) {
				puts("ok");
			}
		}

		/* saving ecbcf yearly */
		printf("saving results for yearly...");
		if ( save_output_yearly(current_dataset) ) {
			puts("ok");
		}

		puts("");

		/* free memory */
		free(temp); temp = NULL;
		free(EBCcfs_temp); EBCcfs_temp = NULL;
		free(EBCcfs); EBCcfs = NULL;
		free(current_dataset->indexes); current_dataset->indexes = NULL;
		free(current_dataset->rows_temp); current_dataset->rows_temp = NULL;
		free(current_dataset->rows_daily); current_dataset->rows_daily = NULL;
		free(current_dataset->rows_aggr); current_dataset->rows_aggr = NULL;
		free(current_dataset->rows); current_dataset->rows = NULL;
		current_dataset->rows = NULL;		/* mandatory */
		current_dataset->rows_aggr = NULL;	/* mandatory */
		current_dataset->rows_temp = NULL;	/* mandatory */
	}

	/* ok */
	return 1;
}

/* */
static int is_valid_filename(const char *const filename) {
	int i;

	/* check for empty string */
	if ( ! filename || ! filename[0] ) {
		return 0;
	}

	/* check filename length */
	for ( i = 0; filename[i]; i++ );
 	if ( INPUT_FILENAME_LEN != i ) {
		return 0;
	}

	/* check fixed symbols */
	if ( ('-' != filename[2]) || ('_' != filename[6]) || ('_' != filename[10]) || ('_' != filename[17]) ) {
		return 0;
	}

	/* check suffix */
	if ( string_n_compare_i(filename+SITE_LEN, "qca_energy", 10) ) {
		return 0;
	}

	/* check for digits */
	if ( !isdigit(filename[18]) ) return 0;
	if ( !isdigit(filename[19]) ) return 0;
	if ( !isdigit(filename[20]) ) return 0;
	if ( !isdigit(filename[21]) ) return 0;
	
	/* */
	return 1;
}

/* */
DATASET *get_datasets(const char *const path, const char *ext, int *const datasets_count) {
	int i;
	int y;
	int gap;
	int assigned;
	int files_found_count;
	int error;
	int file_index;
	YEAR *years_no_leak;
	DD *details;
	DATASET *datasets;
	DATASET *datasets_no_leak;
	FILES *files_found;
	FILE *f;
	
	/* check parameters */
	assert(path && datasets_count);

	/* reset */
	datasets = NULL;
	*datasets_count = 0;

	/* scan path */
	files_found = get_files(path, ext, &files_found_count, &error);
	if ( error || !files_found_count ) {
		puts("no files found!");
		return NULL;
	}

	/* loop on each files found */
	for ( file_index = 0; file_index < files_found_count; file_index++ ) {
		/* check filename */
		if ( !is_valid_filename(files_found[file_index].list[0].name) ) {
			continue;
		}

		/* open file */
		printf("processing %s...", files_found[file_index].list[0].name);
		f = fopen(files_found[file_index].list[0].fullpath, "r");
		if ( !f ) {
			printf("unable to open %s\n", files_found[file_index].list[0].fullpath);
			continue;
		}

		/* get details */
		details = parse_dd(f);
		if ( !details ) {
			free_files(files_found, files_found_count);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}

		/* close file */
		fclose(f);
		
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
				free_files(files_found, files_found_count);
				free_datasets(datasets, *datasets_count);
				return NULL;

			}
			/* */
			datasets = datasets_no_leak;
			datasets[*datasets_count-1].rows = NULL;
			for ( y = 0; y < VARS_TO_FILL; y++ ) {
				datasets[*datasets_count-1].gf_rows[y] = NULL;
			}
			datasets[*datasets_count-1].rows_count = 0;
			datasets[*datasets_count-1].years = NULL;
			datasets[*datasets_count-1].years_count = 0;
			datasets[*datasets_count-1].details = details;

			datasets[*datasets_count-1].rows_aggr = NULL;
			datasets[*datasets_count-1].rows_aggr_count = 0;
			datasets[*datasets_count-1].rows_daily = NULL;	/* dd */
			datasets[*datasets_count-1].rows_temp = NULL;	/* ww-mm-yy */
			datasets[*datasets_count-1].rows_temp_count = 0;
			datasets[*datasets_count-1].indexes = NULL;
			datasets[*datasets_count-1].indexes_count = 0;
			datasets[*datasets_count-1].hourly = (HOURLY_TIMERES == details->timeres);

			/* do the trick ;) */
			i = *datasets_count-1;
		}

		/* check if year is already assigned...? */
		for ( y = 0; y < datasets[i].years_count; y++ ) {
			if ( details->year == datasets[i].years[y].year ) {
				puts(err_out_of_memory);
				free_files(files_found, files_found_count);
				free_datasets(datasets, *datasets_count);
				return NULL;
			}
		}

		/* add year */
		years_no_leak = realloc(datasets[i].years, ++datasets[i].years_count*sizeof*years_no_leak);
		if ( !years_no_leak ) {
			puts(err_out_of_memory);
			free_files(files_found, files_found_count);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}

		/* assign year and compute rows count */
		datasets[i].years = years_no_leak;
		datasets[i].years[datasets[i].years_count-1].year = details->year;
		datasets[i].years[datasets[i].years_count-1].exist = 1;
		datasets[i].years[datasets[i].years_count-1].hle = 0;
		strcpy(datasets[i].years[datasets[i].years_count-1].filename, files_found[file_index].list[0].fullpath); 
		datasets[i].rows_count += ((IS_LEAP_YEAR(details->year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (datasets[i].hourly ? 2 : 1));

		/* free memory */
		if ( assigned ) {
			free_dd(details);
		}

		puts("ok");
	}

	/* free memory */
	free_files(files_found, files_found_count);

	/* sort per year */
	for ( i = 0 ; i < *datasets_count; i++ ) {
		while ( 1 ) {
			qsort(datasets[i].years, datasets[i].years_count, sizeof*datasets[i].years, compare_int);
			/* check for gap */
			gap = 0;
			for ( y = 0; y < datasets[i].years_count-1; y++ ) {
				if ( datasets[i].years[y+1].year-datasets[i].years[y].year > 1 ) {
					gap = 1;
					/* add year */
					years_no_leak = realloc(datasets[i].years, ++datasets[i].years_count*sizeof*years_no_leak);
					if ( !years_no_leak ) {
						puts(err_out_of_memory);
						free_datasets(datasets, *datasets_count);
						return NULL;
					}

					datasets[i].years = years_no_leak;
					datasets[i].years[datasets[i].years_count-1].year = datasets[i].years[y].year+1;
					datasets[i].years[datasets[i].years_count-1].exist = 0;
					datasets[i].years[datasets[i].years_count-1].hle = 0;
					datasets[i].years[datasets[i].years_count-1].filename[0] = '\0';
					datasets[i].rows_count += ((IS_LEAP_YEAR(datasets[i].years[y].year+1) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (datasets[i].hourly ? 2 : 1));
					break;
				}
			}

			if ( !gap ) {
				break;
			}
		}

		/* set daily rows count */
		datasets[i].rows_aggr_count = datasets[i].rows_count / (datasets[i].hourly ? 24 : 48);
	}

	/* ok */
	return datasets;
}
