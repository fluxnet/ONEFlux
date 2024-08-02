/*
	dataset.c

	this file is part of meteo_proc

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
#include "info_swc_hh.h"
#include "info_swc_dd_ww_mm_yy.h"
#include "info_ts_hh.h"
#include "info_ts_dd_ww_mm_yy.h"
#include "info_hh.h"
#include "info_dd.h"
#include "info_ww.h"
#include "info_mm.h"
#include "info_yy.h"
#include "info_nights_days_dd.h"
#include "info_nights_days_ww_mm.h"

/* externs */
extern char *qc_auto_files_path;
extern char *era_files_path;
extern char *output_files_path;
extern char *program_path;

/* constants */
#define ERA_FILE_LEN	15		/* with extension */
#define MET_FILE_LEN	25		/* with extension */
#define FILL_ROWS_MIN	1000
#define DAYS_FOR_GF		15
#define INFO_BUFFER_SIZE	102400
static const int days_per_month[MONTHS] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
static const char *era_values_tokens[] = { "Ta_era", "Pa_era", "VPD_era", "WS_era", "Precip_era", "Rg_era", "LWin_era", "LWincalc_era" };
static const char *era_values_tokens_upd[] = { "Ta_era", "Pa_era", "VPD_era", "WS_era", "P_era", "SW_IN_era", "LW_in_era", "LW_in_calc_era" };
static const char *met_values_tokens[] = { "CO2", "TA", "VPD", "P", "WS", "SW_IN", "LW_IN", "PA", "SW_IN_POT" };

/* */
enum {
	VAR = 0,
	SLOPE,
	INTERCEPT,
	RMSE,
	CORR,

	STAT_VARS
};

/* */
typedef struct {
	char *var;
	PREC slope;
	PREC intercept;
	PREC rmse;
	PREC corr;
} STAT;

/* strings */
static const char dataset_delimiter[] = " ,\r\n";
static const char output_file_hh[] = "%s%s_meteo_hh.csv";
static const char output_file_dd[] = "%s%s_meteo_dd.csv";
static const char output_file_ww[] = "%s%s_meteo_ww.csv";
static const char output_file_mm[] = "%s%s_meteo_mm.csv";
static const char output_file_yy[] = "%s%s_meteo_yy.csv";

static const char output_header_hh[] =	"%s,DTIME,"
										"TA_f,TA_fqc,TA_ERA,TA_m,TA_mqc,"
										"SW_IN_pot,"
										"SW_IN_f,SW_IN_fqc,SW_IN_ERA,SW_IN_m,SW_IN_mqc,"
										"LW_IN_f,LW_IN_fqc,LW_IN_ERA,LW_IN_m,LW_IN_mqc,LW_IN_calc,LW_IN_calc_qc,LW_IN_calc_ERA,LW_IN_calc_m,LW_IN_calc_mqc,"
										"VPD_f,VPD_fqc,VPD_ERA,VPD_m,VPD_mqc,"
										"PA,PA_ERA,PA_m,PA_mqc,"
										"P,P_ERA,P_m,P_mqc,"
										"WS,WS_ERA,WS_m,WS_mqc,"
										"CO2_f,CO2_fqc";
static const char output_format_profile[] = ",%.3f,%g";
static const char output_format_hh[] =	"%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%.3f,%g,"
										"%.3f,%.3f,%.3f,%g,"
										"%.3f,%.3f,%.3f,%g,"
										"%.3f,%g";
static const char output_header_dd[] =	"%s,"
										"TA_f,TA_fqc,TA_f_night,TA_f_night_std,TA_f_night_qc,TA_f_day,TA_f_day_std,TA_f_day_qc,"
										"TA_ERA,TA_ERA_night,TA_ERA_night_std,TA_ERA_day,TA_ERA_day_std,"
										"TA_m,TA_mqc,TA_m_night,TA_m_night_std,TA_m_night_qc,TA_m_day,TA_m_day_std,TA_m_day_qc,"
										"SW_IN_pot,"
										"SW_IN_f,SW_IN_fqc,SW_IN_ERA,SW_IN_m,SW_IN_mqc,"
										"LW_IN_f,LW_IN_fqc,LW_IN_ERA,LW_IN_m,LW_IN_mqc,LW_IN_calc,LW_IN_calc_qc,LW_IN_calc_ERA,LW_IN_calc_m,LW_IN_calc_mqc,"
										"VPD_f,VPD_fqc,VPD_ERA,VPD_m,VPD_mqc,"
										"PA_ERA,PA_m,PA_mqc,"
										"P_ERA,P_m,P_mqc,"
										"WS_ERA,WS_m,WS_mqc,"
										"CO2_f,CO2_fqc";
static const char output_format_dd[] =	"%04d%02d%02d,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%.3f,%.3f,%.3f,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%g";

static const char output_header_ww[] =	"%s,WEEK,"
										"TA_f,TA_fqc,TA_f_night,TA_f_night_std,TA_f_night_qc,TA_f_day,TA_f_day_std,TA_f_day_qc,"
										"TA_ERA,TA_ERA_night,TA_ERA_night_std,TA_ERA_day,TA_ERA_day_std,"
										"TA_m,TA_mqc,TA_m_night,TA_m_night_std,TA_m_night_qc,TA_m_day,TA_m_day_std,TA_m_day_qc,"
										"SW_IN_pot,"
										"SW_IN_f,SW_IN_fqc,SW_IN_ERA,SW_IN_m,SW_IN_mqc,"
										"LW_IN_f,LW_IN_fqc,LW_IN_ERA,LW_IN_m,LW_IN_mqc,LW_IN_calc,LW_IN_calc_qc,LW_IN_calc_ERA,LW_IN_calc_m,LW_IN_calc_mqc,"
										"VPD_f,VPD_fqc,VPD_ERA,VPD_m,VPD_mqc,"
										"PA_ERA,PA_m,PA_mqc,"
										"P_ERA,P_m,P_mqc,"
										"WS_ERA,WS_m,WS_mqc,"
										"CO2_f,CO2_fqc";
static const char output_format_ww[] =	"%d,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%.3f,%.3f,%.3f,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%g";

static const char output_header_mm[] =	"%s,"
										"TA_f,TA_fqc,TA_f_night,TA_f_night_std,TA_f_night_qc,TA_f_day,TA_f_day_std,TA_f_day_qc,"
										"TA_ERA,TA_ERA_night,TA_ERA_night_std,TA_ERA_day,TA_ERA_day_std,"
										"TA_m,TA_mqc,TA_m_night,TA_m_night_std,TA_m_night_qc,TA_m_day,TA_m_day_std,TA_m_day_qc,"
										"SW_IN_pot,"
										"SW_IN_f,SW_IN_fqc,SW_IN_ERA,SW_IN_m,SW_IN_mqc,"
										"LW_IN_f,LW_IN_fqc,LW_IN_ERA,LW_IN_m,LW_IN_mqc,LW_IN_calc,LW_IN_calc_qc,LW_IN_calc_ERA,LW_IN_calc_m,LW_IN_calc_mqc,"
										"VPD_f,VPD_fqc,VPD_ERA,VPD_m,VPD_mqc,"
										"PA_ERA,PA_m,PA_mqc,"
										"P_ERA,P_m,P_mqc,"
										"WS_ERA,WS_m,WS_mqc,"
										"CO2_f,CO2_fqc";
static const char output_format_mm[] =	"%04d%02d,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%.3f,%.3f,%.3f,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%g";

static const char output_header_yy[] =	"%s,"
										"TA_f,TA_fqc,TA_f_night,TA_f_night_std,TA_f_night_qc,TA_f_day,TA_f_day_std,TA_f_day_qc,"
										"TA_ERA,TA_ERA_night,TA_ERA_night_std,TA_ERA_day,TA_ERA_day_std,"
										"TA_m,TA_mqc,TA_m_night,TA_m_night_std,TA_m_night_qc,TA_m_day,TA_m_day_std,TA_m_day_qc,"
										"SW_IN_f,SW_IN_fqc,SW_IN_ERA,SW_IN_m,SW_IN_mqc,"
										"LW_IN_f,LW_IN_fqc,LW_IN_ERA,LW_IN_m,LW_IN_mqc,LW_IN_calc,LW_IN_calc_qc,LW_IN_calc_ERA,LW_IN_calc_m,LW_IN_calc_mqc,"
										"VPD_f,VPD_fqc,VPD_ERA,VPD_m,VPD_mqc,"
										"PA_ERA,PA_m,PA_mqc,"
										"P_ERA,P_m,P_mqc,"
										"WS_ERA,WS_m,WS_mqc,"
										"CO2_f,CO2_fqc";
static const char output_format_yy[] =	"%04d,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%.3f,%.3f,%.3f,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%g,%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%.3f,%g,"
										"%.3f,%g";

static const char output_stat_file[] = "%s%s_meteo_%s_info.txt";
static const char err_no_files_found[] = "no files found.";
static const char err_no_meteo_files_found[] = "no meteo files found.";
static const char err_no_era_files_found[] = "no era files found.";

/* */
static int is_valid_era_filename(const char *const filename) {
	int i;

	/* check for empty string */
	if ( !filename || !filename[0] ) {
		return 0;
	}

	/* check filename length */
	for ( i = 0; filename[i]; i++ );
 	if ( ERA_FILE_LEN != i ) {
		return 0;
	}

	/* 3rd char must be an "-", 7th char must be an underscore */
	if ( ('-' != filename[2]) && ('_' != filename[6]) ) {
		return 0;
	}

	/* check for digits */
	if ( !isdigit(filename[7]) ) return 0;
	if ( !isdigit(filename[8]) ) return 0;
	if ( !isdigit(filename[9]) ) return 0;
	if ( !isdigit(filename[10]) ) return 0;

	/* check for csv extension*/
	return ! string_compare_i(&filename[11], ".csv");
}

/* */
static int is_valid_met_filename(const char *const filename) {
	int i;

	/* check for empty string */
	if ( !filename || !filename[0] ) {
		return 0;
	}

	/* check filename length */
	for ( i = 0; filename[i]; i++ );
 	if ( MET_FILE_LEN != i ) {
		return 0;
	}

	/* check static symbols */
	if ( ('-' != filename[2]) || ('_' != filename[6]) || ('_' != filename[10]) || ('_' != filename[16]) ) {
		return 0;
	}

	/* check suffix */
	if ( string_n_compare_i(filename+SITE_LEN, "qca_meteo", 9) ) {
		return 0;
	}

	/* check for digits */
	if ( !isdigit(filename[17]) ) return 0;
	if ( !isdigit(filename[18]) ) return 0;
	if ( !isdigit(filename[19]) ) return 0;
	if ( !isdigit(filename[20]) ) return 0;

	/* ok */
	return 1;
}

/* */
static int import_era_values(DATASET *const dataset) {
	int i;
	int j;
	int year;
	int rows_count;
	int index;
	int element;
	int assigned;
	int error;
	char *token;
	char *p;
	char buffer[BUFFER_SIZE];
	PREC value;
	FILE *f;

	/* */
	index = 0;
	puts("- get era files...");
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* create filename */
		sprintf(buffer, "%s%s_%d.csv", era_files_path, dataset->site, dataset->years[year].year);

		/* compute rows count */
		rows_count = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_count /= 2;
		}

		printf("  - processing %d year...", dataset->years[year].year);
		if ( !dataset->years[year].exist[ERA_FILES] ) {
			printf("not found. adding null values...");
			for ( i = 0; i < rows_count; i++ ) {
				for ( j = 0; j < ERA_REQUIRED_VALUES; j++ ) {
					dataset->rows[index+i].value[j] = INVALID_VALUE;
				}
			}
		} else {
			/* open file */
			f = fopen(buffer, "r");
			if ( !f ) {
				puts("unable to open file.");
				return 0;
			}

			/* get header */
			if ( ! fgets(buffer, BUFFER_SIZE, f) ) {
				printf("no header ?");
				fclose(f);
				return 0;
			}

			/* check header */
			for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
				if ( i >= SIZEOF_ARRAY(era_values_tokens) ) {
					puts("too many columns.");
					fclose(f);
					return 0;
				}
				if ( string_compare_i(token, era_values_tokens[i]) ) {
					if ( string_compare_i(token, era_values_tokens_upd[i]) ) {
						printf("invalid column! %s instead of %s\n", token, era_values_tokens[i]);
						fclose(f);
						return 0;
					}
				}
			}

			/* get values */
			element = 0;
			while ( fgets(buffer, BUFFER_SIZE, f) ) {
				/* remove carriage return and newline */
				for ( i = 0; i < buffer[i]; i++ ) {
					if ( ('\n' == buffer[i]) || ('\r' == buffer[i]) ) {
						buffer[i] = '\0';
						break;
					}
				}

				/* skip empty lines */
				if ( !buffer[0] ) {
					continue;
				}

				/* prevent too many rows */
				if ( element++ == rows_count ) {
					puts("too many rows!");
					fclose(f);
					return 0;
				}

				assigned = 0;
				error = 0;
				for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
					/* */
					if ( i >= ERA_REQUIRED_VALUES ) {
						puts("too many columns.");
						fclose(f);
						return 0;
					}

					/* convert string to prec */
					value = convert_string_to_prec(token, &error);
					if ( error ) {
						printf("unable to convert value %s at row %d, column %s\n", token, element+1, era_values_tokens[j]);
						fclose(f);
						return 0;
					}

					/* convert nan to invalid value */
					if ( value != value ) {
						value = INVALID_VALUE;
					}
					dataset->rows[index+element-1].value[i] = value;
					++assigned;
				}

				/* check assigned */
				if ( assigned != ERA_REQUIRED_VALUES ) {
					printf("expected %d columns not %d\n", ERA_REQUIRED_VALUES, assigned);
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
		}

		/* update index */
		index += rows_count;

		/* */
		puts("ok");
	}

	/* check rows count */
	if ( index != dataset->rows_count ) {
		printf("rows count should be %d not %d\n", dataset->rows_count, index);
		return 0;
	}

	/* adjust PRECIP */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[PRECIP_ERA]) && (dataset->rows[i].value[PRECIP_ERA] < 0.0) ) {
			dataset->rows[i].value[PRECIP_ERA] = 0.0;
		}
	}

	/* adjust SW_IN */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[SW_IN_ERA]) && (dataset->rows[i].value[SW_IN_ERA] < 0.0) ) {
			dataset->rows[i].value[SW_IN_ERA] = 0.0;
		}
	}

	/* adjust VPD */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[VPD_ERA]) && (dataset->rows[i].value[VPD_ERA] < 0.0) ) {
			dataset->rows[i].value[VPD_ERA] = 0.0;
		}
	}

	/* */
	return 1;
}

/* */
static void stat_free(STAT *s, const int count) {
	int i;

	assert(s);

	for ( i = 0; i < count; i++ ) {
		if ( s[i].var ) {
			free(s[i].var);
		}
	}
	free(s);
}

/* */
static int import_stat(DATASET *const dataset) {
	char buffer[BUFFER_SIZE];
	char *p;
	char *token;
	int i;
	int y;
	int stat_count;
	int error;
	int column_index[STAT_VARS];
	PREC value;
	FILE *f;
	STAT *pstat;
	STAT *pstat_no_leak;
	STAT stat;

	static const char *header[STAT_VARS] = { "Var", "Slope", "Intercept", "RMSE", "Corr" };
	static const char delimiter[] = ",\r\n";
	
	/* */
	assert(dataset);

	/* */
	printf("- get stat file...");

	/* create filename */
	sprintf(buffer, "%sstat30_%s.txt", era_files_path, dataset->site);
	f = fopen(buffer, "rb");
	if ( ! f ) {
		printf("unable to open file: %s\n", buffer);
		return 0;
	}

	/* get header */
	if ( ! get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
		printf("no header ?");
		fclose(f);
		return 0;
	}

	/* reset */
	for ( i = 0; i < STAT_VARS; ++i ) {
		column_index[i] = -1;
	}

	/* parse header */
	for ( i = 0, token = string_tokenizer(buffer, delimiter, &p); token; token = string_tokenizer(NULL, delimiter, &p), ++i ) {
		for ( y = 0; y < STAT_VARS; ++y ) {
			if ( ! string_compare_i(token, header[y]) ) {
				if ( column_index[y] != -1 ) {
					printf("column %s already found at index %d\n", token, column_index[y]+1); 
					fclose(f);
					return 0;
				}
				column_index[y] = i;
			}
		}
	}

	/* check for vars */
	pstat = NULL;
	stat_count = 0;
	for ( i = 0; i < STAT_VARS; ++i ) {
		if ( -1 == column_index[i] ) {
			printf("unable to find column %s\n", token);
			fclose(f);
			return 0;
		}
	}

	/* import values  */
	while ( get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
		/* reset stat */
		stat.var = NULL;
		stat.slope = INVALID_VALUE;
		stat.intercept = INVALID_VALUE;
		stat.rmse = INVALID_VALUE;
		stat.corr = INVALID_VALUE;
		/* parse buffer*/
		for ( i = 0, token = string_tokenizer(buffer, delimiter, &p); token; token = string_tokenizer(NULL, delimiter, &p), ++i ) {
			for ( y = 0; y < STAT_VARS; ++y ) {
				if ( i == column_index[y] ) {
					/* */
					if ( VAR == y ) {
						/* fix var name */
						if ( ! string_compare_i(token, "Ta") ) {
							stat.var = string_copy("TA");
						} else if ( ! string_compare_i(token, "Pa") ) {
							stat.var = string_copy("PA");
						} else if ( ! string_compare_i(token, "Precip") ) {
							stat.var = string_copy("P");
						} else if ( ! string_compare_i(token, "Rg") ) {
							stat.var = string_copy("SW_IN");
						} else if ( ! string_compare_i(token, "LWin") ) {
							stat.var = string_copy("LW_IN");
						} else if ( ! string_compare_i(token, "LWin_calc") ) {
							stat.var = string_copy("LW_IN_calc");
						} else {
							stat.var = string_copy(token);
						}
						if ( ! stat.var ) {
							puts(err_out_of_memory);
							if ( pstat ) stat_free(pstat, stat_count);
							fclose(f);
							return 0;
						}
					} else {
						value = INVALID_VALUE;
						if ( string_compare_i(token, "-") ) {
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf("unable to convert \"%s\"\n", token);
								if ( pstat ) stat_free(pstat, stat_count);
								fclose(f);
								return 0;
							}
						}
						switch ( y ) {
							case SLOPE: stat.slope = value; break;
							case INTERCEPT: stat.intercept = value; break;
							case RMSE: stat.rmse = value; break;
							case CORR:
								stat.corr = value; 
								pstat_no_leak = realloc(pstat, (stat_count+1)*sizeof*pstat_no_leak);
								if ( ! pstat_no_leak ) {
									puts(err_out_of_memory);
									if ( pstat ) stat_free(pstat, stat_count);
									fclose(f);
									return 0;
								}
								pstat = pstat_no_leak;
								pstat[stat_count].var = stat.var;
								pstat[stat_count].slope = stat.slope;
								pstat[stat_count].intercept = stat.intercept;
								pstat[stat_count].rmse = stat.rmse;
								pstat[stat_count].corr = stat.corr;
								++stat_count;
							break;
						}
					}
				}
			}
		}
	}

	/* close file */
	fclose(f);

	/* check imported values */
	if ( ! stat_count ) {
		puts("nothing to import");
		return 0;
	}

	/* create buffer string */
	buffer[0] = '\0';
	/* add header */
	y = 0;
	for ( i = 0; i < STAT_VARS; ++i ) {
		strcat(buffer, header[i]);
		if ( i < STAT_VARS-1 ) {
			strcat(buffer, ",");
		}
	}
	strcat(buffer, "\n");

	/* add rows */
	for ( y = 0; buffer[y]; ++y );
	for ( i = 0; i < stat_count; ++i ) {
		y += sprintf(buffer+y, "%s,", pstat[i].var);
		if ( ! IS_INVALID_VALUE(pstat[i].slope) ) {
			y += sprintf(buffer+y, "%g,", pstat[i].slope);
		} else {
			y += sprintf(buffer+y, "-,");
		}
		if ( ! IS_INVALID_VALUE(pstat[i].intercept) ) {
			y += sprintf(buffer+y, "%g,", pstat[i].intercept);
		} else {
			y += sprintf(buffer+y, "-,");
		}
		if ( ! IS_INVALID_VALUE(pstat[i].rmse) ) {
			y += sprintf(buffer+y, "%g,", pstat[i].rmse);
		} else {
			y += sprintf(buffer+y, "-,");
		}
		if ( ! IS_INVALID_VALUE(pstat[i].corr) ) {
			y += sprintf(buffer+y, "%g\n", pstat[i].corr);
		} else {
			y += sprintf(buffer+y, "-\n");
		}
	}
	stat_free(pstat, stat_count);

	dataset->stat = string_copy(buffer);
	if ( ! dataset->stat ) {
		puts(err_out_of_memory);
		return 0;
	}

	puts("ok");
	return 1;
}

/* */
int parse_dataset_details(DATASET *const dataset, FILE *const f) {
	int i;
	char site[SITE_LEN];
	DD *dd;
	
	/* get details */
	dd = parse_dd(f);
	if ( !dd ) {
		return 0;
	}

	/* check name */
	if ( string_compare_i(dd->site, dataset->site) ) {
		printf("error: site name on header is %s not %s.", site, dataset->site);
		free_dd(dd);
		return 0;
	}

	/* update values 'cause we need thos for computing rpot on missings years */
	
	/* lat can differ */
	dataset->lat = dd->lat;

	/* lon can differ */
	dataset->lon = dd->lon;

	/* timezone can differ */
	free(dataset->time_zones);
	dataset->time_zones = malloc(dd->time_zones_count*sizeof*dataset->time_zones);
	if ( !dataset->time_zones ) {
		puts(err_out_of_memory);
		free_dd(dd);
		return 0;
	}
	for ( i = 0; i <dd->time_zones_count; i++ ) {
		dataset->time_zones[i].timestamp.YYYY = dd->time_zones[i].timestamp.YYYY;
		dataset->time_zones[i].timestamp.MM = dd->time_zones[i].timestamp.MM;
		dataset->time_zones[i].timestamp.DD = dd->time_zones[i].timestamp.DD;
		dataset->time_zones[i].timestamp.hh = dd->time_zones[i].timestamp.hh;
		dataset->time_zones[i].timestamp.mm = dd->time_zones[i].timestamp.mm;
		dataset->time_zones[i].timestamp.ss = dd->time_zones[i].timestamp.ss;
		dataset->time_zones[i].v = dd->time_zones[i].v;
	}
	dataset->time_zones_count = dd->time_zones_count;

	/* check timeres */
	if ( dataset->timeres != dd->timeres ) {
		puts("error: time resolution differs from previous years.");
		free_dd(dd);
		return 0;
	}

	/* free memory */
	free_dd(dd);

	/* ok */
	return 1;
}

/* */
static int get_dataset_details(DATASET *const dataset) {
	int i;
	FILE *f;
	int flag;
	int year;
	char buffer[BUFFER_SIZE];
	DD *details;

	flag = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		sprintf(buffer, "%s%s_qca_meteo_%d.csv", qc_auto_files_path, dataset->site, dataset->years[year].year);

		f = fopen(buffer, "r");
		if  ( !f ) {
			continue;
		}

		details = parse_dd(f);
		if ( !details ) {
			fclose(f);
			return 0;
		}

		dataset->lat = details->lat;
		dataset->lon = details->lon;
		if ( dataset->time_zones ) {
			free(dataset->time_zones);
		}
		dataset->time_zones = malloc(details->time_zones_count*sizeof*dataset->time_zones);
		if ( !dataset->time_zones ) {
			puts(err_out_of_memory);
			fclose(f);
			return 0;
		}
		for ( i = 0; i <details->time_zones_count; i++ ) {
			dataset->time_zones[i].timestamp.YYYY = details->time_zones[i].timestamp.YYYY;
			dataset->time_zones[i].timestamp.MM = details->time_zones[i].timestamp.MM;
			dataset->time_zones[i].timestamp.DD = details->time_zones[i].timestamp.DD;
			dataset->time_zones[i].timestamp.hh = details->time_zones[i].timestamp.hh;
			dataset->time_zones[i].timestamp.mm = details->time_zones[i].timestamp.mm;
			dataset->time_zones[i].timestamp.ss = details->time_zones[i].timestamp.ss;
			dataset->time_zones[i].v = details->time_zones[i].v;
		}
		dataset->time_zones_count = details->time_zones_count;
		dataset->timeres = details->timeres;
		dataset->hourly = 0;
		if ( HOURLY_TIMERES == details->timeres ) {
			dataset->hourly = 1;
		}

		free_dd(details);
		details = NULL;

		fclose(f);
		flag = 1;
		break;
	}

	return flag;
}

/* */
static int import_meteo_values(DATASET *const dataset) {
	typedef struct {
		int profile;
		int index;
	} COLUMN;

	int i;
	int y;
	int j;
	int index;
	int element;
	int assigned;
	int rows_count;
	int error;
	int year;
	int columns_found_count;
	int columns_index[MET_VALUES];
	int profile;
	int *int_no_leak;
	COLUMN *column_no_leak;
	COLUMN *swc_columns;
	COLUMN *ts_columns;

	int swc_columns_count;
	int ts_columns_count;
	int *ts_profiles;
	int *swc_profiles;
	int ts_profiles_count;
	int swc_profiles_count;
	char *token;
	char *p;
	char buffer[BUFFER_SIZE];
	char buffer2[BUFFER_SIZE];
	PREC value;
	PREC *temp;
	DD details;
	FILE *f;
	TIME_ZONE time_zone;

	/* mandatory */
	swc_columns = NULL;
	ts_columns = NULL;
	swc_columns_count = 0;
	ts_columns_count = 0;
	index = 0;
	puts("- get met files...");

	if ( 1 == dataset->years_count ) {
		printf(" - processing header...");
	} else {
		printf(" - processing headers of %d years (%d-%d)...", dataset->years_count, dataset->years[0].year, dataset->years[dataset->years_count-1].year);
	}

	/* header parsing */
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* reset */
		ts_profiles = NULL;
		swc_profiles = NULL;
		ts_profiles_count = 0;
		swc_profiles_count = 0;

		/* create filename */
		sprintf(buffer, "%s%s_qca_meteo_%d.csv", qc_auto_files_path, dataset->site, dataset->years[year].year);

		/* open file */
		f = fopen(buffer, "r");
		if ( !f ) {
			continue;
		}

		/* parse info header */
		if ( !parse_dataset_details(dataset, f) ) {
			fclose(f);
			return 0;
		}

		/* get header */
		if ( !fgets(buffer, BUFFER_SIZE, f) ) {
			printf("no header ?");
			fclose(f);
			return 0;
		}

		/* parse header */
		for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
			/* check for Ts */
			if ( ! string_n_compare_i(token, "TS_", 3) || ! string_n_compare_i(token, "itpTS_", 6) ) {
				if ( ! string_n_compare_i(token, "TS_", 3) ) {
					/* get profile */
					profile = convert_string_to_int(token+3, &error);
				} else {
					profile = convert_string_to_int(token+6, &error);
				}

				if ( error ) {
					printf("unable to get profile from var %s\n", token);
					free(ts_profiles);
					free(swc_profiles);
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}

				/* check for same profile on header */
				for ( j = 0; j < ts_profiles_count; j++ ) {
					if ( profile == ts_profiles[j] ) {
						printf("profile %d for var TS already found\n", profile);
						free(ts_profiles);
						free(swc_profiles);
						free(swc_columns);		
						free(ts_columns);
						fclose(f);
						return 0;
					}
				}

				/* add profile */
				int_no_leak = realloc(ts_profiles, (ts_profiles_count+1)*sizeof*int_no_leak);
				if ( !int_no_leak ) {
					puts(err_out_of_memory);
					free(ts_profiles);
					free(swc_profiles);
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}
				ts_profiles = int_no_leak;

				/* set profile */
				ts_profiles[ts_profiles_count] = profile;

				/* inc counter */
				++ts_profiles_count;

				/* new profile ? */
				for ( j = 0; j < dataset->ts_count; j++ ) {
					if ( profile == dataset->ts_profiles[j] ) {
						error = 1;
						break;
					}
				}
				if ( error ) {
					error = 0;
					continue;
				}

				/* realloc memory for profiles */
				int_no_leak = realloc(dataset->ts_profiles, (dataset->ts_count+1)*sizeof*int_no_leak);
				if ( !int_no_leak ) {
					puts(err_out_of_memory);
					free(ts_profiles);
					free(swc_profiles);
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}
				dataset->ts_profiles = int_no_leak;

				/* set profile */
				dataset->ts_profiles[dataset->ts_count] = profile;

				/* inc counter */
				++dataset->ts_count;
			} else
			/* check for SWC */
			if ( ! string_n_compare_i(token, "SWC_", 4) || ! string_n_compare_i(token, "itpSWC_", 7) ) {
				if ( ! string_n_compare_i(token, "SWC_", 4) ) {
					/* get profile */
					profile = convert_string_to_int(token+4, &error);
				} else {
					profile = convert_string_to_int(token+7, &error);
				}
				if ( error ) {
					printf("unable to get profile from var %s\n", token);
					free(ts_profiles);
					free(swc_profiles);
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}

				/* check for same profile on header */
				for ( j = 0; j < swc_profiles_count; j++ ) {
					if ( profile == swc_profiles[j] ) {
						printf("profile %d for var SWC already found\n", profile);
						free(ts_profiles);
						free(swc_profiles);
						free(swc_columns);		
						free(ts_columns);
						fclose(f);
						return 0;
					}
				}

				/* add profile */
				int_no_leak = realloc(swc_profiles, (swc_profiles_count+1)*sizeof*int_no_leak);
				if ( !int_no_leak ) {
					puts(err_out_of_memory);
					free(ts_profiles);
					free(swc_profiles);
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}
				swc_profiles = int_no_leak;

				/* set profile */
				swc_profiles[swc_profiles_count] = profile;

				/* inc counter */
				++swc_profiles_count;

				/* new profile ? */
				for ( j = 0; j < dataset->swc_count; j++ ) {
					if ( profile == dataset->swc_profiles[j] ) {
						error = 1;
						break;
					}
				}
				if ( error ) {
					error = 0;
					continue;
				}

				/* realloc memory for profiles */
				int_no_leak = realloc(dataset->swc_profiles, (dataset->swc_count+1)*sizeof*int_no_leak);
				if ( !int_no_leak ) {
					puts(err_out_of_memory);
					free(ts_profiles);
					free(swc_profiles);
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}
				dataset->swc_profiles = int_no_leak;

				/* set profile */
				dataset->swc_profiles[dataset->swc_count] = profile;

				/* inc counter */
				++dataset->swc_count;
			}
		}

		/* */
		free(ts_profiles);
		free(swc_profiles);

		/* */
		fclose(f);
	}
	puts("ok");

	/* alloc memory for ts ? */
	if ( dataset->ts_count ) {
		qsort(dataset->ts_profiles, dataset->ts_count, sizeof*dataset->ts_profiles, compare_int);
		/* row */
		dataset->tss = malloc(dataset->rows_count*sizeof*dataset->tss);
		if ( !dataset->tss ) {
			puts(err_out_of_memory);
			free(swc_columns);		
			free(ts_columns);
			fclose(f);
			return 0;
		}
		for ( i = 0; i < dataset->rows_count; i++ ) {
			dataset->tss[i] = NULL;
		}
		for ( i = 0; i < dataset->rows_count; i++ ) {
			dataset->tss[i] = malloc(dataset->ts_count*sizeof*dataset->tss[i]);
			if ( !dataset->tss[i] ) {
				puts(err_out_of_memory);
				free(swc_columns);		
				free(ts_columns);
				fclose(f);
				return 0;
			}
		}
		for ( i = 0; i < dataset->rows_count; i++ ) {
			for ( j = 0; j < dataset->ts_count; j++ ) {
				dataset->tss[i][j].value = INVALID_VALUE;
				dataset->tss[i][j].filled = INVALID_VALUE;
				dataset->tss[i][j].qc = INVALID_VALUE;			
			}
		}
		/* daily */
		dataset->tss_daily = malloc(dataset->rows_daily_count*sizeof*dataset->tss_daily);
		if ( !dataset->tss_daily ) {
			puts(err_out_of_memory);
			free(swc_columns);		
			free(ts_columns);
			fclose(f);
			return 0;
		}
		for ( i = 0; i < dataset->rows_daily_count; i++ ) {
			dataset->tss_daily[i] = NULL;
		}
		for ( i = 0; i < dataset->rows_daily_count; i++ ) {
			dataset->tss_daily[i] = malloc(dataset->ts_count*sizeof*dataset->tss_daily[i]);
			if ( !dataset->tss_daily[i] ) {
				puts(err_out_of_memory);
				free(swc_columns);		
				free(ts_columns);
				fclose(f);
				return 0;
			}
		}
		for ( i = 0; i < dataset->rows_daily_count; i++ ) {
			for ( j = 0; j < dataset->ts_count; j++ ) {
				dataset->tss_daily[i][j].value = INVALID_VALUE;
				dataset->tss_daily[i][j].filled = INVALID_VALUE;
				dataset->tss_daily[i][j].qc = INVALID_VALUE;			
			}
		}
		/* aggr */
		dataset->tss_aggr = malloc(dataset->rows_aggr_count*sizeof*dataset->tss_aggr);
		if ( !dataset->tss_aggr ) {
			puts(err_out_of_memory);
			free(swc_columns);		
			free(ts_columns);
			fclose(f);
			return 0;
		}
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			dataset->tss_aggr[i] = NULL;
		}
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			dataset->tss_aggr[i] = malloc(dataset->ts_count*sizeof*dataset->tss_aggr[i]);
			if ( !dataset->tss_aggr[i] ) {
				puts(err_out_of_memory);
				free(swc_columns);		
				free(ts_columns);
				fclose(f);
				return 0;
			}
		}
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			for ( j = 0; j < dataset->ts_count; j++ ) {
				dataset->tss_aggr[i][j].value = INVALID_VALUE;
				dataset->tss_aggr[i][j].filled = INVALID_VALUE;
				dataset->tss_aggr[i][j].qc = INVALID_VALUE;			
			}
		}
	}

	/* alloc memory for swcs ? */
	if ( dataset->swc_count ) {
		qsort(dataset->swc_profiles, dataset->swc_count, sizeof*dataset->swc_profiles, compare_int);
		/* row */
		dataset->swcs = malloc(dataset->rows_count*sizeof*dataset->swcs);
		if ( !dataset->swcs ) {
			puts(err_out_of_memory);
			free(swc_columns);
			free(ts_columns);
			fclose(f);
			return 0;
		}
		for ( i = 0; i < dataset->rows_count; i++ ) {
			dataset->swcs[i] = NULL;
		}
		for ( i = 0; i < dataset->rows_count; i++ ) {
			dataset->swcs[i] = malloc(dataset->swc_count*sizeof*dataset->swcs[i]);
			if ( !dataset->swcs[i] ) {
				puts(err_out_of_memory);
				free(swc_columns);		
				free(ts_columns);
				fclose(f);
				return 0;
			}
		}
		for ( i = 0; i < dataset->rows_count; i++ ) {
			for ( j = 0; j < dataset->swc_count; j++ ) {
				dataset->swcs[i][j].value = INVALID_VALUE;
				dataset->swcs[i][j].filled = INVALID_VALUE;
				dataset->swcs[i][j].qc = INVALID_VALUE;			
			}
		}
		/* daily */
		dataset->swcs_daily = malloc(dataset->rows_daily_count*sizeof*dataset->swcs_daily);
		if ( !dataset->swcs_daily ) {
			puts(err_out_of_memory);
			free(swc_columns);		
			free(ts_columns);
			fclose(f);
			return 0;
		}
		for ( i = 0; i < dataset->rows_daily_count; i++ ) {
			dataset->swcs_daily[i] = NULL;
		}
		for ( i = 0; i < dataset->rows_daily_count; i++ ) {
			dataset->swcs_daily[i] = malloc(dataset->swc_count*sizeof*dataset->swcs_daily[i]);
			if ( !dataset->swcs_daily[i] ) {
				puts(err_out_of_memory);
				free(swc_columns);		
				free(ts_columns);
				fclose(f);
				return 0;
			}
		}
		for ( i = 0; i < dataset->rows_daily_count; i++ ) {
			for ( j = 0; j < dataset->swc_count; j++ ) {
				dataset->swcs_daily[i][j].value = INVALID_VALUE;
				dataset->swcs_daily[i][j].filled = INVALID_VALUE;
				dataset->swcs_daily[i][j].qc = INVALID_VALUE;			
			}
		}
		/* aggr */
		dataset->swcs_aggr = malloc(dataset->rows_aggr_count*sizeof*dataset->swcs_aggr);
		if ( !dataset->swcs_aggr ) {
			puts(err_out_of_memory);
			free(swc_columns);		
			free(ts_columns);
			fclose(f);
			return 0;
		}
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			dataset->swcs_aggr[i] = NULL;
		}
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			dataset->swcs_aggr[i] = malloc(dataset->swc_count*sizeof*dataset->swcs_aggr[i]);
			if ( !dataset->swcs_aggr[i] ) {
				puts(err_out_of_memory);
				free(swc_columns);		
				free(ts_columns);
				fclose(f);
				return 0;
			}
		}
		for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
			for ( j = 0; j < dataset->swc_count; j++ ) {
				dataset->swcs_aggr[i][j].value = INVALID_VALUE;
				dataset->swcs_aggr[i][j].filled = INVALID_VALUE;
				dataset->swcs_aggr[i][j].qc = INVALID_VALUE;			
			}
		}
	}

	/* import values */
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* */
		printf("  - processing %d year...", dataset->years[year].year);
		/* create filename */
		sprintf(buffer, "%s%s_qca_meteo_%d.csv", qc_auto_files_path, dataset->site, dataset->years[year].year);

		/* compute rows count */
		rows_count = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_count /= 2;
		}

		/* reset columns */
		for ( i = 0; i < MET_VALUES; i++ ) {
			columns_index[i] = -1;
		}

		/* open file */
		f = fopen(buffer, "r");
		if ( !f ) {
			printf("not found. set null values...");
			for ( i = 0; i < rows_count; i++ ) {
				dataset->rows[index+i].value[TA_MET] = INVALID_VALUE;
				dataset->rows[index+i].value[VPD_MET] = INVALID_VALUE;
				dataset->rows[index+i].value[PRECIP_MET] = INVALID_VALUE;
				dataset->rows[index+i].value[WS_MET] = INVALID_VALUE;
				dataset->rows[index+i].value[SW_IN_MET] = INVALID_VALUE;
				dataset->rows[index+i].value[LW_IN_MET] = INVALID_VALUE;
				dataset->rows[index+i].value[PA_MET] = INVALID_VALUE;
			}

			/* set rpot */
			details.year = dataset->years[year].year;
			details.lat = dataset->lat;
			details.lon = dataset->lon;
			details.time_zones_count = 1;
			if ( 1 == dataset->time_zones_count ) {
				details.time_zones = dataset->time_zones;				
			} else {
				/* set last timezone */
				i = dataset->time_zones_count-1;
				time_zone.timestamp.YYYY = dataset->time_zones[i].timestamp.YYYY;
				time_zone.timestamp.MM = dataset->time_zones[i].timestamp.MM;
				time_zone.timestamp.DD = dataset->time_zones[i].timestamp.DD;
				time_zone.timestamp.hh = dataset->time_zones[i].timestamp.hh;
				time_zone.timestamp.mm = dataset->time_zones[i].timestamp.mm;
				time_zone.timestamp.ss = dataset->time_zones[i].timestamp.ss;
				time_zone.v = dataset->time_zones[i].v;	
				details.time_zones = &time_zone;
			}
			details.timeres = dataset->timeres;
			temp = get_rpot(&details);
			if ( !temp ) {
				return 0;
			}

			/* copy rpots */
			for ( i = 0; i < rows_count; i++ ) {
				dataset->rows[index+i].value[RPOT_MET] = temp[i];
			}

			/* free memory */
			free(temp);

			/* */
			element = i;
		} else {
			/* parse info header */
			if ( !parse_dataset_details(dataset, f) ) {
				fclose(f);
				return 0;
			}

			/* get header */
			if ( !fgets(buffer, BUFFER_SIZE, f) ) {
				printf("no header ?");
				fclose(f);
				return 0;
			}

			/* parse header */
			for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
				for ( y = 0; y < MET_VALUES; y++ ) {
					/* check itp */
					strcpy(buffer2, "itp");
					strcat(buffer2, met_values_tokens[y]);
					if (	! string_compare_i(token, met_values_tokens[y]) ||
							! string_compare_i(token, buffer2) ) {
						/* check if it is already assigned */
						if ( columns_index[y] != -1 ) {
							printf("column %s already found at index %d\n", token, columns_index[y]);
							fclose(f);
							return 0;
						} else {
							columns_index[y] = i;
							/* do not skip, continue searching for redundant columns */
						}
					}
				}

				/* check for TS */
				if ( ! string_n_compare_i(token, "TS_", 3) || ! string_n_compare_i(token, "itpTS_", 6) ) {			
					/* get profile */
					if ( ! string_n_compare_i(token, "TS_", 3) ) {
						profile = convert_string_to_int(token+3, &error);
					} else {
						profile = convert_string_to_int(token+6, &error);
					}
					if ( error ) {
						printf("unable to get profile from var %s\n", token);
						free(swc_columns);		
						free(ts_columns);
						fclose(f);
						return 0;
					}
					/* realloc memory for indexes */
					column_no_leak = realloc(ts_columns, (ts_columns_count+1)*sizeof*column_no_leak);
					if ( !column_no_leak ) {
						puts(err_out_of_memory);
						free(swc_columns);		
						free(ts_columns);
						fclose(f);
						return 0;
					}					
					ts_columns = column_no_leak;
					ts_columns[ts_columns_count].profile = profile;
					ts_columns[ts_columns_count].index = i;

					/* inc columns count */
					++ts_columns_count;
				} else
				/* check for SWC */
				if ( ! string_n_compare_i(token, "SWC_", 4) || ! string_n_compare_i(token, "itpSWC_", 7) ) {
					/* get profile */
					if ( ! string_n_compare_i(token, "SWC_", 4) ) {
						profile = convert_string_to_int(token+4, &error);
					} else {
						profile = convert_string_to_int(token+7, &error);
					}
					if ( error ) {
						printf("unable to get profile from var %s\n", token);
						free(swc_columns);		
						free(ts_columns);
						fclose(f);
						return 0;
					}
					/* realloc memory for indexes */
					column_no_leak = realloc(swc_columns, (swc_columns_count+1)*sizeof*column_no_leak);
					if ( !column_no_leak ) {
						puts(err_out_of_memory);
						free(swc_columns);		
						free(ts_columns);
						fclose(f);
						return 0;
					}
					
					swc_columns = column_no_leak;
					swc_columns[swc_columns_count].profile = profile;
					swc_columns[swc_columns_count].index = i;

					/* inc columns count */
					++swc_columns_count;
				}
			}

			/* check found columns */
			columns_found_count = swc_columns_count+ts_columns_count;
			for (  i = 0; i < MET_VALUES; i++ ) {
				if ( columns_index[i] != -1 ) {
					++columns_found_count;
				}
			}

			if ( !columns_found_count ) {
				puts("no columns found!");
				fclose(f);
				return 0;
			}

			/* check for rpot */
			if ( -1 == columns_index[RPOT_MET-CO2_MET] ) {
				puts("SW_IN_POT not found!");
				free(swc_columns);		
				free(ts_columns);
				fclose(f);
				return 0;
			}

			/* get values */
			element = 0;
			while ( fgets(buffer, BUFFER_SIZE, f) ) {
				/* remove carriage return and newline */
				for ( i = 0; i < buffer[i]; i++ ) {
					if ( ('\n' == buffer[i]) || ('\r' == buffer[i]) ) {
						buffer[i] = '\0';
						break;
					}
				}

				/* skip empty lines */
				if ( !buffer[0] ) {
					continue;
				}

				/* prevent too many rows */
				if ( element++ == rows_count ) {
					puts("too many rows!");
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}

				assigned = 0;
				error = 0;
				for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
					/* check for ts */
					for ( y = 0; y < ts_columns_count; y++ ) {
						if ( i == ts_columns[y].index ) {
							int profile = ts_columns[y].profile;
							/* convert string to prec */
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf("unable to convert value %s at row %d, column TS_%d\n", token, element+1, profile);
								free(swc_columns);		
								free(ts_columns);
								fclose(f);
								break;
							}

							/* convert nan to invalid value */
							if ( value != value ) {
								value = INVALID_VALUE;
							}

							for ( y = 0; y < dataset->ts_count; ++y ) {
								if ( dataset->ts_profiles[y] == profile ) {
									break;
								}
							}

							/* assign value */
							dataset->tss[index+element-1][y].value = value;
							++assigned;

							break;
						}
					}
					/* check for swc */
					for ( y = 0; y < swc_columns_count; y++ ) {
						if ( i == swc_columns[y].index ) {
							int profile = swc_columns[y].profile;
							/* convert string to prec */
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf("unable to convert value %s at row %d, column SWC_%d\n", token, element+1, profile);
								free(swc_columns);		
								free(ts_columns);
								fclose(f);
								break;
							}

							/* convert nan to invalid value */
							if ( value != value ) {
								value = INVALID_VALUE;
							}

							for ( y = 0; y < dataset->ts_count; ++y ) {
								if ( dataset->ts_profiles[y] == profile ) {
									break;
								}
							}

							/* assign value */
							dataset->swcs[index+element-1][y].value = value;
							++assigned;

							break;
						}
					}
					/* check other vars */
					for ( y = 0; y < MET_VALUES; y++ ) {
						if ( i == columns_index[y] ) {
							/* convert string to prec */
							value = convert_string_to_prec(token, &error);
							if ( error ) {
								printf("unable to convert value %s at row %d, column %s\n", token, element+1, met_values_tokens[y]);
								free(swc_columns);		
								free(ts_columns);
								fclose(f);
								break;
							}

							/* convert nan to invalid value */
							if ( value != value ) {
								value = INVALID_VALUE;
							}

							switch ( y ) {
								case 1:	/* TA */
									if ( (value < -50) || (value > 50) ) {
										value = INVALID_VALUE;
									}
								break;

								case 2: /* VPD */
									if ( (value < -5) || (value > 120) ) {
										value = INVALID_VALUE;
									} else if ( !IS_INVALID_VALUE(value) && (value < 0.0) ) {
										value = 0.0;
									}
								break;

								case 3:	/* PRECIP */
									if ( (value < -0.1) || (value > 200) ) {
										value = INVALID_VALUE;
									} else if ( !IS_INVALID_VALUE(value) && (value < 0.0) ) {
										value = 0.0;
									}
								break;

								case 4:	/* WS */
									if ( (value < 0) || (value > 40) ) {
										value = INVALID_VALUE;
									}
								break;

								case 5:	/* SW_IN */
									if ( (value < -50) || (value > 1400) ) {
										value = INVALID_VALUE;
									} else if ( !IS_INVALID_VALUE(value) && (value < 0.0) ) {
										value = 0.0;
									}
								break;

								case 6: /* LW_IN */
									if ( (value < 50) || (value > 700) ) {
										value = INVALID_VALUE;
									}
								break;

								case 7: /* PA */
									if ( (value < 70) || (value > 130) ) {
										value = INVALID_VALUE;
									}
								break;
							}

							/* assign value */
							dataset->rows[index+element-1].value[CO2_MET+y] = value;
							++assigned;
						}
					}
				}

				/* check assigned */
				if ( assigned != columns_found_count ) {
					printf("imported %d value not %d\n", assigned, columns_found_count);
					free(swc_columns);		
					free(ts_columns);
					fclose(f);
					return 0;
				}
			}

			/* close file */
			fclose(f);
		}

		/* free memory */
		free(swc_columns);		
		free(ts_columns);
		swc_columns = NULL;
		ts_columns = NULL;
		swc_columns_count = 0;
		ts_columns_count = 0;

		/* check rows count */
		if ( element != rows_count ) {
			printf("rows count should be %d not %d\n", rows_count, element);
			return 0;
		}

		/* update index */
		index += rows_count;

		/* */
		puts("ok");
	}

	/* check rows count */
	if ( index != dataset->rows_count ) {
		printf("rows count should be %d not %d\n", dataset->rows_count, index);
		return 0;
	}

	/* */
	return 1;
}

/* */
static void compute_ms(const DATASET *const dataset) {
	int i;
	assert(dataset);

	/* can be done using TA_QC 'cause HAT is NEVER computed! ;) */

	/* update qcs */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* TA */
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[TA_MET]) ) {
			dataset->rows[i].value[TA_M] = dataset->rows[i].value[TA_MET];
			dataset->rows[i].value[TA_M_QC] = 0; 
		} else if ( !IS_INVALID_VALUE(dataset->rows[i].value[TA_QC]) ) {
			dataset->rows[i].value[TA_M_QC] = dataset->rows[i].value[TA_QC];
			if ( dataset->rows[i].value[TA_QC] < 2 ) {
				dataset->rows[i].value[TA_M] = dataset->rows[i].value[TA_FILLED];
			} else {
				dataset->rows[i].value[TA_M] = dataset->rows[i].value[TA_ERA];
				dataset->rows[i].value[TA_M_QC] = 2;
			}
		} else {
			dataset->rows[i].value[TA_M] = dataset->rows[i].value[TA_ERA];
			dataset->rows[i].value[TA_M_QC] = 2;
		}

		/* New option added 20160616 to take into account the posibility that ERA is
		not present in a given year (recent years). In this case the data filled using
		MDS are used for the _M and the QC is set as 3. This case applies in fact only
		to the last year because the ERA has no gaps except the last year is not yet
		available
		*/
		if ( IS_INVALID_VALUE(dataset->rows[i].value[TA_M]) ) {
			dataset->rows[i].value[TA_M] = dataset->rows[i].value[TA_FILLED];
			dataset->rows[i].value[TA_M_QC] = 3;
		}

		/* SW_IN */
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[SW_IN_MET]) ) {
			dataset->rows[i].value[SW_IN_M] = dataset->rows[i].value[SW_IN_MET];
			dataset->rows[i].value[SW_IN_M_QC] = 0; 
		} else if ( !IS_INVALID_VALUE(dataset->rows[i].value[SW_IN_QC]) ) {
			dataset->rows[i].value[SW_IN_M_QC] = dataset->rows[i].value[SW_IN_QC];
			if ( dataset->rows[i].value[SW_IN_QC] < 2 ) {
				dataset->rows[i].value[SW_IN_M] = dataset->rows[i].value[SW_IN_FILLED];
			} else {
				dataset->rows[i].value[SW_IN_M] = dataset->rows[i].value[SW_IN_ERA];
				dataset->rows[i].value[SW_IN_M_QC] = 2;
			}
		} else {
			dataset->rows[i].value[SW_IN_M] = dataset->rows[i].value[SW_IN_ERA];
			dataset->rows[i].value[SW_IN_M_QC] = 2;
		}

		/* New option added 20160616 to take into account the posibility that ERA is
		not present in a given year (recent years). In this case the data filled using
		MDS are used for the _M and the QC is set as 3. This case applies in fact only
		to the last year because the ERA has no gaps except the last year is not yet
		available
		*/
		if ( IS_INVALID_VALUE(dataset->rows[i].value[SW_IN_M]) ) {
			dataset->rows[i].value[SW_IN_M] = dataset->rows[i].value[SW_IN_FILLED];
			dataset->rows[i].value[SW_IN_M_QC] = 3;
		}

		/* LW_IN */
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[LW_IN_MET]) ) {
			dataset->rows[i].value[LW_IN_M] = dataset->rows[i].value[LW_IN_MET];
			dataset->rows[i].value[LW_IN_M_QC] = 0; 
		} else if ( !IS_INVALID_VALUE(dataset->rows[i].value[LW_IN_QC]) ) {
			dataset->rows[i].value[LW_IN_M_QC] = dataset->rows[i].value[LW_IN_QC];
			if ( dataset->rows[i].value[LW_IN_QC] < 2 ) {
				dataset->rows[i].value[LW_IN_M] = dataset->rows[i].value[LW_IN_FILLED];
			} else {
				dataset->rows[i].value[LW_IN_M] = dataset->rows[i].value[LW_IN_ERA];
				dataset->rows[i].value[LW_IN_M_QC] = 2;
			}
		} else {
			dataset->rows[i].value[LW_IN_M] = dataset->rows[i].value[LW_IN_ERA];
			dataset->rows[i].value[LW_IN_M_QC] = 2;
		}

		/* New option added 20160616 to take into account the posibility that ERA is
		not present in a given year (recent years). In this case the data filled using
		MDS are used for the _M and the QC is set as 3. This case applies in fact only
		to the last year because the ERA has no gaps except the last year is not yet
		available
		*/
		if ( IS_INVALID_VALUE(dataset->rows[i].value[LW_IN_M]) ) {
			dataset->rows[i].value[LW_IN_M] = dataset->rows[i].value[LW_IN_FILLED];
			dataset->rows[i].value[LW_IN_M_QC] = 3;
		}

		/* VPD */
		if ( !IS_INVALID_VALUE(dataset->rows[i].value[VPD_MET]) ) {
			dataset->rows[i].value[VPD_M] = dataset->rows[i].value[VPD_MET];
			dataset->rows[i].value[VPD_M_QC] = 0; 
		} else if ( !IS_INVALID_VALUE(dataset->rows[i].value[VPD_QC]) ) {
			dataset->rows[i].value[VPD_M_QC] = dataset->rows[i].value[VPD_QC];
			if ( dataset->rows[i].value[VPD_QC] < 2 ) {
				dataset->rows[i].value[VPD_M] = dataset->rows[i].value[VPD_FILLED];
			} else {
				dataset->rows[i].value[VPD_M] = dataset->rows[i].value[VPD_ERA];
				dataset->rows[i].value[VPD_M_QC] = 2;
			}
		} else {
			dataset->rows[i].value[VPD_M] = dataset->rows[i].value[VPD_ERA];
			dataset->rows[i].value[VPD_M_QC] = 2;
		}

		/* New option added 20160616 to take into account the posibility that ERA is
		not present in a given year (recent years). In this case the data filled using
		MDS are used for the _M and the QC is set as 3. This case applies in fact only
		to the last year because the ERA has no gaps except the last year is not yet
		available
		*/
		if ( IS_INVALID_VALUE(dataset->rows[i].value[VPD_M]) ) {
			dataset->rows[i].value[VPD_M] = dataset->rows[i].value[VPD_FILLED];
			dataset->rows[i].value[VPD_M_QC] = 3;
		}

		/* PA */
		/* A condition has been added 20160616: in case ERA in not present the last year,
		the _M is not created for the the whole year (it would be like the original)
		We assume that PA_ERA can be -9999 only the last year of the ERA (in case the
		ERA source data are not yet available)
		*/
		if ( IS_INVALID_VALUE(dataset->rows[i].value[PA_ERA]) ) {
			dataset->rows[i].value[PA_M] = INVALID_VALUE;
			dataset->rows[i].value[PA_M_QC] = INVALID_VALUE;
		} else if ( !IS_INVALID_VALUE(dataset->rows[i].value[PA_MET]) ) {
			dataset->rows[i].value[PA_M] = dataset->rows[i].value[PA_MET];
			dataset->rows[i].value[PA_M_QC] = 0;
		} else {
			dataset->rows[i].value[PA_M] = dataset->rows[i].value[PA_ERA];
			dataset->rows[i].value[PA_M_QC] = 2;
		}
		

		/* PRECIP */
		/* A condition has been added 20160616: in case ERA in not present the last year,
		the _M is not created for the the whole year (it would be like the original)
		We assume that PA_ERA can be -9999 only the last year of the ERA (in case the
		ERA source data are not yet available)
		*/
		if ( IS_INVALID_VALUE(dataset->rows[i].value[PRECIP_ERA]) ) {
			dataset->rows[i].value[PRECIP_M] = INVALID_VALUE;
			dataset->rows[i].value[PRECIP_M_QC] = INVALID_VALUE;
		}
		else if ( !IS_INVALID_VALUE(dataset->rows[i].value[PRECIP_MET]) ) {
			dataset->rows[i].value[PRECIP_M] = dataset->rows[i].value[PRECIP_MET];
			dataset->rows[i].value[PRECIP_M_QC] = 0;
		} else {
			dataset->rows[i].value[PRECIP_M] = dataset->rows[i].value[PRECIP_ERA];
			dataset->rows[i].value[PRECIP_M_QC] = 2;
		}
		

		/* WS */
		/* A condition has been added 20160616: in case ERA in not present the last year,
		the _M is not created for the the whole year (it would be like the original)
		We assume that PA_ERA can be -9999 only the last year of the ERA (in case the
		ERA source data are not yet available)
		*/
		if ( IS_INVALID_VALUE(dataset->rows[i].value[WS_ERA]) ) {
			dataset->rows[i].value[WS_M] = INVALID_VALUE;
			dataset->rows[i].value[WS_M_QC] = INVALID_VALUE;
		}
		else if ( !IS_INVALID_VALUE(dataset->rows[i].value[WS_MET]) ) {
			dataset->rows[i].value[WS_M] = dataset->rows[i].value[WS_MET];
			dataset->rows[i].value[WS_M_QC] = 0;
		} else {
			dataset->rows[i].value[WS_M] = dataset->rows[i].value[WS_ERA];
			dataset->rows[i].value[WS_M_QC] = 2;
		}

	}
}

/* */
static int compute_nights(DATASET *const dataset) {
	int i;
	int z;
	int row;
	int index;
	char is_night;
	int nights_count;
	int days_count;
	PREC nights[48];
	PREC days[48];

	assert(dataset);

	/* */
	z = 48;
	if ( dataset->hourly ) {
		z /= 2;
	}

	index = 0;
	for ( row = 0; row < dataset->rows_count; row += z ) {
		dataset->rows_daily[index].value[TA_F_NIGHT] = 0.0;
		dataset->rows_daily[index].value[TA_F_NIGHT_STD] = 0.0;
		dataset->rows_daily[index].value[TA_F_NIGHT_QC] = 0.0;
		dataset->rows_daily[index].value[TA_F_DAY] = 0.0;
		dataset->rows_daily[index].value[TA_F_DAY_STD] = 0.0;
		dataset->rows_daily[index].value[TA_F_DAY_QC] = 0.0;

		dataset->rows_daily[index].value[TA_M_NIGHT] = 0.0;
		dataset->rows_daily[index].value[TA_M_NIGHT_STD] = 0.0;
		dataset->rows_daily[index].value[TA_M_NIGHT_QC] = 0.0;
		dataset->rows_daily[index].value[TA_M_DAY] = 0.0;
		dataset->rows_daily[index].value[TA_M_DAY_STD] = 0.0;
		dataset->rows_daily[index].value[TA_M_DAY_QC] = 0.0;

		dataset->rows_daily[index].value[TA_ERA_NIGHT] = 0.0;
		dataset->rows_daily[index].value[TA_ERA_NIGHT_STD] = 0.0;
		dataset->rows_daily[index].value[TA_ERA_DAY] = 0.0;
		dataset->rows_daily[index].value[TA_ERA_DAY_STD] = 0.0;

		/* TA_FILLED */
		nights_count = 0;
		days_count = 0;
		for ( i = 0; i < z; i++ ) {
			is_night = 0;
			if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_MET], 0.0) ) {
				is_night = 1;
			}
			if ( !IS_INVALID_VALUE(dataset->rows[row+i].value[TA_FILLED]) ) {
				if ( is_night ) {
					dataset->rows_daily[index].value[TA_F_NIGHT] += dataset->rows[row+i].value[TA_FILLED];
					dataset->rows_daily[index].value[TA_F_NIGHT_QC] += dataset->rows[row+i].value[TA_QC];
					nights[nights_count++] = dataset->rows[row+i].value[TA_FILLED];
				} else {
					dataset->rows_daily[index].value[TA_F_DAY] += dataset->rows[row+i].value[TA_FILLED];
					dataset->rows_daily[index].value[TA_F_DAY_QC] += dataset->rows[row+i].value[TA_QC];
					days[days_count++] = dataset->rows[row+i].value[TA_FILLED];
				}
			}
		}

		assert(nights_count <= z);
		assert(days_count <= z);

		if ( nights_count ) {
			dataset->rows_daily[index].value[TA_F_NIGHT] /= nights_count;
			dataset->rows_daily[index].value[TA_F_NIGHT_QC] /= nights_count;
			dataset->rows_daily[index].value[TA_F_NIGHT_STD] = get_standard_deviation(nights, nights_count);
		} else {
			dataset->rows_daily[index].value[TA_F_NIGHT] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_F_NIGHT_QC] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_F_NIGHT_STD] = INVALID_VALUE;
		}
		if ( days_count ) {
			dataset->rows_daily[index].value[TA_F_DAY] /= days_count;
			dataset->rows_daily[index].value[TA_F_DAY_QC] /= days_count;
			dataset->rows_daily[index].value[TA_F_DAY_STD] = get_standard_deviation(days, days_count);
		} else {
			dataset->rows_daily[index].value[TA_F_DAY] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_F_DAY_QC] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_F_DAY_STD] = INVALID_VALUE;
		}

		/* TA_M */
		nights_count = 0;
		days_count = 0;
		for ( i = 0; i < z; i++ ) {
			is_night = 0;
			if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_MET], 0.0) ) {
				is_night = 1;
			}
			if ( !IS_INVALID_VALUE(dataset->rows[row+i].value[TA_M]) ) {
				if ( is_night ) {
					dataset->rows_daily[index].value[TA_M_NIGHT] += dataset->rows[row+i].value[TA_M];
					dataset->rows_daily[index].value[TA_M_NIGHT_QC] += dataset->rows[row+i].value[TA_M_QC];
					nights[nights_count++] = dataset->rows[row+i].value[TA_M];
				} else {
					dataset->rows_daily[index].value[TA_M_DAY] += dataset->rows[row+i].value[TA_M];
					dataset->rows_daily[index].value[TA_M_DAY_QC] += dataset->rows[row+i].value[TA_M_QC];
					days[days_count++] = dataset->rows[row+i].value[TA_M];
				}
			}
		}

		assert(nights_count <= z);
		assert(days_count <= z);

		if ( nights_count ) {
			dataset->rows_daily[index].value[TA_M_NIGHT] /= nights_count;
			dataset->rows_daily[index].value[TA_M_NIGHT_QC] /= nights_count;
			dataset->rows_daily[index].value[TA_M_NIGHT_STD] = get_standard_deviation(nights, nights_count);
		} else {
			dataset->rows_daily[index].value[TA_M_NIGHT] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_M_NIGHT_QC] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_M_NIGHT_STD] = INVALID_VALUE;
		}
		if ( days_count ) {
			dataset->rows_daily[index].value[TA_M_DAY] /= days_count;
			dataset->rows_daily[index].value[TA_M_DAY_QC] /= days_count;
			dataset->rows_daily[index].value[TA_M_DAY_STD] = get_standard_deviation(days, days_count);
		} else {
			dataset->rows_daily[index].value[TA_M_DAY] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_M_DAY_QC] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_M_DAY_STD] = INVALID_VALUE;
		}

		/* TA_ERA */
		nights_count = 0;
		days_count = 0;
		for ( i = 0; i < z; i++ ) {
			is_night = 0;
			if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_MET], 0.0) ) {
				is_night = 1;
			}
			if ( !IS_INVALID_VALUE(dataset->rows[row+i].value[TA_ERA]) ) {
				if ( is_night ) {
					dataset->rows_daily[index].value[TA_ERA_NIGHT] += dataset->rows[row+i].value[TA_ERA];
					nights[nights_count++] = dataset->rows[row+i].value[TA_ERA];
				} else {
					dataset->rows_daily[index].value[TA_ERA_DAY] += dataset->rows[row+i].value[TA_ERA];
					days[days_count++] = dataset->rows[row+i].value[TA_ERA];
				}
			}
		}

		assert(nights_count <= z);
		assert(days_count <= z);

		if ( nights_count ) {
			dataset->rows_daily[index].value[TA_ERA_NIGHT] /= nights_count;
			dataset->rows_daily[index].value[TA_ERA_NIGHT_STD] = get_standard_deviation(nights, nights_count);
		} else {
			dataset->rows_daily[index].value[TA_ERA_NIGHT] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_ERA_NIGHT_STD] = INVALID_VALUE;
		}
		if ( days_count ) {
			dataset->rows_daily[index].value[TA_ERA_DAY] /= days_count;
			dataset->rows_daily[index].value[TA_ERA_DAY_STD] = get_standard_deviation(days, days_count);
		} else {
			dataset->rows_daily[index].value[TA_ERA_DAY] = INVALID_VALUE;
			dataset->rows_daily[index].value[TA_ERA_DAY_STD] = INVALID_VALUE;
		}

		/* nights count */
		dataset->rows_daily[index].nights_count = 0;
		dataset->rows_daily[index].days_count = 0;
		for ( i = 0; i < z; i++ ) {
			if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_MET], 0.0) ) {
				++dataset->rows_daily[index].nights_count;
			} else {
				++dataset->rows_daily[index].days_count;
			}
		}
		++index;
	}

	return 1;
}

/* */
static int compute_calc(DATASET *const dataset) {
	int i;
	int y;
	int z;
	const PREC sigma = 5.6696e-8;
	const PREC T0 = 273.15;
	const PREC Tstroke = 36;
	const PREC ESTAR = 611;
	const PREC A = 17.27;
	PREC value;
	int valids_count;
	int years_rows_count;
	int index;

	/* */
	z = 48;
	if ( dataset->hourly ) {
		z /= 2;
	}

	for ( i = 0; i < dataset->rows_count; i += z ) {
		value = 0.0;
		valids_count = 0;
		for ( y = 0; y < z; y++ ) {
			dataset->rows[i+y].value[FPAR] = INVALID_VALUE;
			if ( !ARE_FLOATS_EQUAL(dataset->rows[i+y].value[RPOT_MET], 0.0) && !IS_INVALID_VALUE(dataset->rows[i+y].value[SW_IN_FILLED]) ) {
				dataset->rows[i+y].value[FPAR] = dataset->rows[i+y].value[SW_IN_FILLED] / dataset->rows[i+y].value[RPOT_MET];
				if ( dataset->rows[i+y].value[FPAR] < 0.0 ) {
					dataset->rows[i+y].value[FPAR] = 0.0;
				}
				value += dataset->rows[i+y].value[FPAR];
				++valids_count;
			}
		}
		if ( valids_count )  {
			value /= valids_count; /* mean */
			for ( y = 0; y < z; y++ ) {
				if ( ARE_FLOATS_EQUAL(dataset->rows[i+y].value[RPOT_MET], 0.0) ) {
					assert(dataset->rows[i+y].value[FPAR] == INVALID_VALUE);
					dataset->rows[i+y].value[FPAR] = value;
				}
			}
		}
	}

	index = 0;
	for ( y = 0; y < dataset->years_count; y++ ) {
		years_rows_count = IS_LEAP_YEAR(dataset->years[y].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			years_rows_count /= 2;
		}
		value = 0.0;
		valids_count = 0;
		for ( i = 0; i < years_rows_count; i++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows[index+i].value[FPAR]) ) {
				value += dataset->rows[index+i].value[FPAR];
				++valids_count;
			}
		}

		if ( valids_count && (valids_count != years_rows_count) ) {
			value /= valids_count;
			for ( i = 0; i < years_rows_count; i++ ) {
				if ( IS_INVALID_VALUE(dataset->rows[index+i].value[FPAR]) ) {
					dataset->rows[index+i].value[FPAR] = value;
				}
			}
		}

		index += years_rows_count;
	}

	for ( i = 0; i < dataset->rows_count; i++ ) {
		if (	IS_INVALID_VALUE(dataset->rows[i].value[FPAR]) ||
				IS_INVALID_VALUE(dataset->rows[i].value[TA_FILLED]) ||
				IS_INVALID_VALUE(dataset->rows[i].value[VPD_FILLED]) ) {
			dataset->rows[i].value[LW_IN_CALC] = INVALID_VALUE;
			continue;
		}
		
		/* Cloud cover and cloud correction factor Eq. (3) */
		dataset->rows[i].value[CLOUD_COVER] = 1.0 - (dataset->rows[i].value[FPAR] - 0.5) / 0.4;
		if ( dataset->rows[i].value[CLOUD_COVER] > 1.0 ) {
			dataset->rows[i].value[CLOUD_COVER] = 1.0;
		}
		if ( dataset->rows[i].value[CLOUD_COVER] < 0.0 ) {
			dataset->rows[i].value[CLOUD_COVER] = 0.0;
		}
		dataset->rows[i].value[R_CLOUD] = 1 + 0.22 * SQUARE(dataset->rows[i].value[CLOUD_COVER]);

		/* Saturation and actual Vapour pressure [3], and associated  emissivity Eq. (2) */
		dataset->rows[i].value[ESAT] = ESTAR * exp(A*((dataset->rows[i].value[TA_FILLED]/((dataset->rows[i].value[TA_FILLED]+T0)-Tstroke))));
		
		dataset->rows[i].value[VP] = dataset->rows[i].value[ESAT] - dataset->rows[i].value[VPD_FILLED] * 100;

		if ( dataset->rows[i].value[VP] < 0.0 ) {
			dataset->rows[i].value[VP] = 3.3546e-004;
		}

		dataset->rows[i].value[epsA] = 0.64 * pow(dataset->rows[i].value[VP] / (dataset->rows[i].value[TA_FILLED]+T0), 0.14285714);

		/* Longwave radiation flux downward Eq. (1) */
		dataset->rows[i].value[LW_IN_CALC] = dataset->rows[i].value[R_CLOUD] * dataset->rows[i].value[epsA] * sigma * pow(dataset->rows[i].value[TA_FILLED]+T0, 4);
		if ( (dataset->rows[i].value[LW_IN_CALC] < 10.0) || (dataset->rows[i].value[LW_IN_CALC] > 1000.0) )  {
			dataset->rows[i].value[LW_IN_CALC] = INVALID_VALUE;
		}
	}

	/* qc */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		if ( ! IS_INVALID_VALUE(dataset->rows[i].value[LW_IN_CALC]) ) {
			dataset->rows[i].value[LW_IN_CALC_QC] = dataset->rows[i].value[SW_IN_QC];
			if ( dataset->rows[i].value[TA_QC] > dataset->rows[i].value[LW_IN_CALC_QC] ) {
				dataset->rows[i].value[LW_IN_CALC_QC] = dataset->rows[i].value[TA_QC];
			}
			if ( dataset->rows[i].value[VPD_QC] > dataset->rows[i].value[LW_IN_CALC_QC] ) {
				dataset->rows[i].value[LW_IN_CALC_QC] = dataset->rows[i].value[VPD_QC];
			}
		}
	}

	return 1;
}

/* */
static int compute_dd(DATASET *const dataset) {
	int i;
	int y;
	int index;
	int row;
	int valids_count;
	int qc_valids_count;
	int rows_per_day;

	assert(dataset);

	/* */
	rows_per_day = 48;
	if ( dataset->hourly ) {
		rows_per_day /= 2;
	}

	/* change qc 'cause X_QC can be INVALID_VALUE */
	for ( row = 0; row < dataset->rows_count; row++ ) {
		if ( (dataset->rows[row].value[TA_QC] >= 0) && (dataset->rows[row].value[TA_QC] < 2) ) {
			dataset->rows[row].value[TA_QC] = 1;
		} else {
			dataset->rows[row].value[TA_QC] = 0;
		}

		if ( (dataset->rows[row].value[VPD_QC] >= 0) && (dataset->rows[row].value[VPD_QC] < 2) ) {
			dataset->rows[row].value[VPD_QC] = 1;
		} else {
			dataset->rows[row].value[VPD_QC] = 0;
		}

		if ( (dataset->rows[row].value[SW_IN_QC] >= 0) && (dataset->rows[row].value[SW_IN_QC] < 2) ) {
			dataset->rows[row].value[SW_IN_QC] = 1;
		} else {
			dataset->rows[row].value[SW_IN_QC] = 0;
		}

		if ( (dataset->rows[row].value[LW_IN_QC] >= 0) && (dataset->rows[row].value[LW_IN_QC] < 2) ) {
			dataset->rows[row].value[LW_IN_QC] = 1;
		} else {
			dataset->rows[row].value[LW_IN_QC] = 0;
		}

		if ( (dataset->rows[row].value[CO2_QC] >= 0) && (dataset->rows[row].value[CO2_QC] < 2) ) {
			dataset->rows[row].value[CO2_QC] = 1;
		} else {
			dataset->rows[row].value[CO2_QC] = 0;
		}

		if ( (dataset->rows[row].value[TA_M_QC] >= 0) && (dataset->rows[row].value[TA_M_QC] < 2) ) {
			dataset->rows[row].value[TA_M_QC] = 1;
		} else {
			dataset->rows[row].value[TA_M_QC] = 0;
		}

		if ( (dataset->rows[row].value[VPD_M_QC] >= 0) && (dataset->rows[row].value[VPD_M_QC] < 2) ) {
			dataset->rows[row].value[VPD_M_QC] = 1;
		} else {
			dataset->rows[row].value[VPD_M_QC] = 0;
		}

		if ( (dataset->rows[row].value[SW_IN_M_QC] >= 0) && (dataset->rows[row].value[SW_IN_M_QC] < 2) ) {
			dataset->rows[row].value[SW_IN_M_QC] = 1;
		} else {
			dataset->rows[row].value[SW_IN_M_QC] = 0;
		}

		if ( (dataset->rows[row].value[LW_IN_M_QC] >= 0) && (dataset->rows[row].value[LW_IN_M_QC] < 2) ) {
			dataset->rows[row].value[LW_IN_M_QC] = 1;
		} else {
			dataset->rows[row].value[LW_IN_M_QC] = 0;
		}

		/* if QC is INVALID_VALUE is 'cause ERA is not imported so we left it INVALID_VALUE */
		if ( ! IS_INVALID_VALUE(dataset->rows[row].value[PA_M_QC]) ) {
			if ( (dataset->rows[row].value[PA_M_QC] >= 0) && (dataset->rows[row].value[PA_M_QC] < 2) ) {
				dataset->rows[row].value[PA_M_QC] = 1;
			} else {
				dataset->rows[row].value[PA_M_QC] = 0;
			}
		}

		/* if QC is INVALID_VALUE is 'cause ERA is not imported so we left it INVALID_VALUE */
		if ( ! IS_INVALID_VALUE(dataset->rows[row].value[PRECIP_M_QC]) ) {
			if ( (dataset->rows[row].value[PRECIP_M_QC] >= 0) && (dataset->rows[row].value[PRECIP_M_QC] < 2) ) {
				dataset->rows[row].value[PRECIP_M_QC] = 1;
			} else {
				dataset->rows[row].value[PRECIP_M_QC] = 0;
			}
		}

		/* if QC is INVALID_VALUE is 'cause ERA is not imported so we left it INVALID_VALUE */
		if ( ! IS_INVALID_VALUE(dataset->rows[row].value[WS_M_QC]) ) {
			if ( (dataset->rows[row].value[WS_M_QC] >= 0) && (dataset->rows[row].value[WS_M_QC] < 2) ) {
				dataset->rows[row].value[WS_M_QC] = 1;
			} else {
				dataset->rows[row].value[WS_M_QC] = 0;
			}
		}

		if ( (dataset->rows[row].value[LW_IN_CALC_QC] >= 0) && (dataset->rows[row].value[LW_IN_CALC_QC] < 2) ) {
			dataset->rows[row].value[LW_IN_CALC_QC] = 1;
		} else {
			dataset->rows[row].value[LW_IN_CALC_QC] = 0;
		}

		if ( (dataset->rows[row].value[LW_IN_CALC_M_QC] >= 0) && (dataset->rows[row].value[LW_IN_CALC_M_QC] < 2) ) {
			dataset->rows[row].value[LW_IN_CALC_M_QC] = 1;
		} else {
			dataset->rows[row].value[LW_IN_CALC_M_QC] = 0;
		}

		/* TS */
		for ( i = 0; i < dataset->ts_count; i++ ) {
			if ( (dataset->tss[row][i].qc >= 0) && (dataset->tss[row][i].qc < 2) ) {
				dataset->tss[row][i].qc = 1;
			} else {
				dataset->tss[row][i].qc = 0;
			}
		}

		/* SWC */
		for ( i = 0; i < dataset->swc_count; i++ ) {
			if ( (dataset->swcs[row][i].qc >= 0) && (dataset->swcs[row][i].qc < 2) ) {
				dataset->swcs[row][i].qc = 1;
			} else {
				dataset->swcs[row][i].qc = 0;
			}
		}
	}

	/* aggregate to day */
	index = 0;
	for ( row = 0; row < dataset->rows_count; row += rows_per_day ) {
		/* aggr ERA */
		for ( y = 0; y < ERA_REQUIRED_VALUES; y++ ) {
			valids_count = 0;
			dataset->rows_daily[index].value[y] = 0.0;
			for ( i = 0; i < rows_per_day; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows[row+i].value[y]) ) {
					dataset->rows_daily[index].value[y] += dataset->rows[row+i].value[y];
					++valids_count;
				}
			}
			if ( valids_count == rows_per_day ) {
				if ( PRECIP_ERA != y ) { /* PRECIP MUST BE SUM, NOT MEAN */
					dataset->rows_daily[index].value[y] /= valids_count;
				}
			} else {
				dataset->rows_daily[index].value[y] = INVALID_VALUE;
			}
		}

		/* aggr RPOT */
		valids_count = 0;
		dataset->rows_daily[index].value[RPOT_MET] = 0.0;
		for ( i = 0; i < rows_per_day; i++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows[row+i].value[RPOT_MET]) ) {
				dataset->rows_daily[index].value[RPOT_MET] += dataset->rows[row+i].value[RPOT_MET];
				++valids_count;
			}
		}
		if ( valids_count == rows_per_day ) {
			dataset->rows_daily[index].value[RPOT_MET] /= valids_count;
		} else {
			dataset->rows_daily[index].value[RPOT_MET] = INVALID_VALUE;
		}

		/*	aggr FILLED, QCs, M and QCs 
			if there is one invalid values (i.e. impossible to fill in the gapfilling) the whole day is set as -9999
		*/

		for ( y = TA_FILLED; y < TA_F_NIGHT; y++ ) {
			valids_count = 0;
			dataset->rows_daily[index].value[y] = 0.0;
			for ( i = 0; i < rows_per_day; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows[row+i].value[y]) ) {
					dataset->rows_daily[index].value[y] += dataset->rows[row+i].value[y];
					++valids_count;
				}
			}
			if ( valids_count == rows_per_day ) {
				if ( PRECIP_M != y ) {	/* PRECIP MUST BE SUM, NOT MEAN */
					dataset->rows_daily[index].value[y] /= valids_count;
				}
			} else {
				dataset->rows_daily[index].value[y] = INVALID_VALUE;
			}
		}

		/* aggr CALC */
		for ( y = LW_IN_CALC; y <= LW_IN_CALC_QC; y++ ) {
			valids_count = 0;
			dataset->rows_daily[index].value[y] = 0.0;
			for ( i = 0; i < rows_per_day; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows[row+i].value[y]) ) {
					dataset->rows_daily[index].value[y] += dataset->rows[row+i].value[y];
					++valids_count;
				}
			}
			if ( valids_count == rows_per_day ) {
				dataset->rows_daily[index].value[y] /= valids_count;
			} else {
				dataset->rows_daily[index].value[y] = INVALID_VALUE;
			}
		}

		/* aggr Ts */
		for ( y = 0; y < dataset->ts_count; y++ ) {
			valids_count = 0;
			qc_valids_count = 0;
			dataset->tss_daily[index][y].filled = 0.0;
			dataset->tss_daily[index][y].qc = 0.0;
			for ( i = 0; i < rows_per_day; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->tss[row+i][y].filled) ) {
					dataset->tss_daily[index][y].filled += dataset->tss[row+i][y].filled;
					++valids_count;
				}

				if ( !IS_INVALID_VALUE(dataset->tss[row+i][y].qc) ) {
					dataset->tss_daily[index][y].qc += dataset->tss[row+i][y].qc;
					++qc_valids_count;
				}
			}
			if ( valids_count == rows_per_day ) {
				dataset->tss_daily[index][y].filled /= valids_count;
			} else {
				dataset->tss_daily[index][y].filled = INVALID_VALUE;
			}
			if ( qc_valids_count == rows_per_day ) {
				dataset->tss_daily[index][y].qc /= qc_valids_count;
			} else {
				dataset->tss_daily[index][y].qc = INVALID_VALUE;
			}
		}

		/* aggr SWC */
		for ( y = 0; y < dataset->swc_count; y++ ) {
			valids_count = 0;
			qc_valids_count = 0;
			dataset->swcs_daily[index][y].filled = 0.0;
			dataset->swcs_daily[index][y].qc = 0.0;
			for ( i = 0; i < rows_per_day; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->swcs[row+i][y].filled) ) {
					dataset->swcs_daily[index][y].filled += dataset->swcs[row+i][y].filled;
					++valids_count;
				}
				if ( !IS_INVALID_VALUE(dataset->swcs[row+i][y].qc) ) {
					dataset->swcs_daily[index][y].qc += dataset->swcs[row+i][y].qc;
					++qc_valids_count;
				}
			}
			if ( valids_count == rows_per_day ) {
				dataset->swcs_daily[index][y].filled /= valids_count;
			} else {
				dataset->swcs_daily[index][y].filled = INVALID_VALUE;
			}
			if ( qc_valids_count == rows_per_day ) {
				dataset->swcs_daily[index][y].qc /= qc_valids_count;
			} else {
				dataset->swcs_daily[index][y].qc = INVALID_VALUE;
			}
		}

		++index;
	}

	if ( index != dataset->rows_daily_count ) {
		printf("error: index should be %d not %d\n", dataset->rows_daily_count, index); 
		return 0;
	}

	/* fix qc */
	for ( i = 0; i < dataset->rows_daily_count; i++ ) {
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[TA_M]) ) dataset->rows_daily[i].value[TA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[VPD_M]) ) dataset->rows_daily[i].value[VPD_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[SW_IN_M]) ) dataset->rows_daily[i].value[SW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[LW_IN_M]) ) dataset->rows_daily[i].value[LW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[PA_M]) ) dataset->rows_daily[i].value[PA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[PRECIP_M]) ) dataset->rows_daily[i].value[PRECIP_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[WS_M]) ) dataset->rows_daily[i].value[WS_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[TA_FILLED]) ) dataset->rows_daily[i].value[TA_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[VPD_FILLED]) ) dataset->rows_daily[i].value[VPD_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[SW_IN_FILLED]) ) dataset->rows_daily[i].value[SW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[LW_IN_FILLED]) ) dataset->rows_daily[i].value[LW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[CO2_FILLED]) ) dataset->rows_daily[i].value[CO2_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_daily[i].value[LW_IN_CALC]) ) dataset->rows_daily[i].value[LW_IN_CALC_QC] = INVALID_VALUE;

		/* Ts */
		for ( y = 0; y < dataset->ts_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->tss_daily[i][y].filled) ) {
				dataset->tss_daily[i][y].qc = INVALID_VALUE;
			}
		}
		
		/* SWC */
		for ( y = 0; y < dataset->swc_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->swcs_daily[i][y].filled) ) {
				dataset->swcs_daily[i][y].qc = INVALID_VALUE;
			}
		}
	}

	/* compute nights */
	if ( !compute_nights(dataset) ) {
		return 0;
	}

	/* */
	return 1;
}

/* */
static int compute_ww(DATASET *const dataset) {
	int i;
	int y;
	int index;
	int year;
	int rows_per_day;
	int rows_per_year;
	int days_per_week;
	int k;
	int week;
	int valids_count;
	int qc_valids_count;

	assert(dataset);

	/* */
	rows_per_day = 48;
	if ( dataset->hourly ) {
		rows_per_day /= 2;
	}

	index = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* get rows_per_year count */
		rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_per_year /= 2;
		}
		rows_per_year /= rows_per_day;

		/* loop for weeks */
		days_per_week = 7;
		k = 0;
		for ( week = 0; week < 52; week++ ) {
			/* fix for last week */
			if ( 52 - 1 == week ) {
				days_per_week = (IS_LEAP_YEAR(dataset->years[year].year) ? 366 : 365) - 51*7;
			}
			/* aggr ERA */
			for ( y = 0; y < ERA_REQUIRED_VALUES; y++ ) {
				valids_count = 0;
				dataset->rows_aggr[week+(year*52)].value[y] = 0.0;
				for ( i = 0; i < days_per_week; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].value[y]) ) {
						dataset->rows_aggr[week+(year*52)].value[y] += dataset->rows_daily[index+k+i].value[y];
						++valids_count;
					}
				}
				if ( valids_count == days_per_week ) {
					dataset->rows_aggr[week+(year*52)].value[y] /= valids_count;
				} else {
					dataset->rows_aggr[week+(year*52)].value[y] = INVALID_VALUE;
				}
			}

			/* aggr RPOT */
			valids_count = 0;
			dataset->rows_aggr[week+(year*52)].value[RPOT_MET] = 0.0;
			for ( i = 0; i < days_per_week; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].value[RPOT_MET]) ) {
					dataset->rows_aggr[week+(year*52)].value[RPOT_MET] += dataset->rows_daily[index+k+i].value[RPOT_MET];
					++valids_count;
				}
			}
			if ( valids_count == days_per_week ) {
				dataset->rows_aggr[week+(year*52)].value[RPOT_MET] /= valids_count;
			} else {
				dataset->rows_aggr[week+(year*52)].value[RPOT_MET] = INVALID_VALUE;
			}

			/*	aggr FILLED, QCs, M, CALC and QCs
				if there is one invalid values (i.e. impossible to fill in the gapfilling) the whole day is set as -9999
			*/
			for ( y = TA_FILLED; y < VALUES; y++ ) {
				/* do not aggregate temp values !*/
				if (	( y == FPAR ) ||
						( y == CLOUD_COVER ) ||
						( y == R_CLOUD ) ||
						( y == ESAT ) ||
						( y == VP ) ||
						( y == epsA ) ) {
					continue;
				}
				valids_count = 0;
				dataset->rows_aggr[week+(year*52)].value[y] = 0.0;
				for ( i = 0; i < days_per_week; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].value[y]) ) {
						dataset->rows_aggr[week+(year*52)].value[y] += dataset->rows_daily[index+k+i].value[y];
						++valids_count;
					}
				}
				if ( valids_count == days_per_week ) {
					dataset->rows_aggr[week+(year*52)].value[y] /= valids_count;
				} else {
					dataset->rows_aggr[week+(year*52)].value[y] = INVALID_VALUE;
				}
			}

			/* aggr Ts */
			for ( y = 0; y < dataset->ts_count; y++ ) {
				valids_count = 0;
				qc_valids_count = 0;
				dataset->tss_aggr[week+(year*52)][y].filled = 0.0;
				dataset->tss_aggr[week+(year*52)][y].qc = 0.0;
				for ( i = 0; i < days_per_week; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->tss_daily[index+k+i][y].filled) ) {
						dataset->tss_aggr[week+(year*52)][y].filled += dataset->tss_daily[index+k+i][y].filled;
						++valids_count;
					}
					if ( !IS_INVALID_VALUE(dataset->tss_daily[index+k+i][y].qc) ) {
						dataset->tss_aggr[week+(year*52)][y].qc += dataset->tss_daily[index+k+i][y].qc;
						++qc_valids_count;
					}
				}
				if ( valids_count == days_per_week ) {
					dataset->tss_aggr[week+(year*52)][y].filled /= valids_count;
				} else {
					dataset->tss_aggr[week+(year*52)][y].filled = INVALID_VALUE;
				}
				if ( qc_valids_count == days_per_week ) {
					dataset->tss_aggr[week+(year*52)][y].qc /= qc_valids_count;
				} else {
					dataset->tss_aggr[week+(year*52)][y].qc = INVALID_VALUE;
				}
			}

			/* aggr SWC */
			for ( y = 0; y < dataset->swc_count; y++ ) {
				valids_count = 0;
				qc_valids_count = 0;
				dataset->swcs_aggr[week+(year*52)][y].filled = 0.0;
				dataset->swcs_aggr[week+(year*52)][y].qc = 0.0;
				for ( i = 0; i < days_per_week; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->swcs_daily[index+k+i][y].filled) ) {
						dataset->swcs_aggr[week+(year*52)][y].filled += dataset->swcs_daily[index+k+i][y].filled;
						++valids_count;
					}
					if ( !IS_INVALID_VALUE(dataset->swcs_daily[index+k+i][y].qc) ) {
						dataset->swcs_aggr[week+(year*52)][y].qc += dataset->swcs_daily[index+k+i][y].qc;
						++qc_valids_count;
					}
				}
				if ( valids_count == days_per_week ) {
					dataset->swcs_aggr[week+(year*52)][y].filled /= valids_count;
				} else {
					dataset->swcs_aggr[week+(year*52)][y].filled = INVALID_VALUE;
				}
				if ( qc_valids_count == days_per_week ) {
					dataset->swcs_aggr[week+(year*52)][y].qc /= qc_valids_count;
				} else {
					dataset->swcs_aggr[week+(year*52)][y].qc = INVALID_VALUE;
				}
			}

			/* aggr nights and days */
			dataset->rows_aggr[week+(year*52)].nights_count = 0;
			dataset->rows_aggr[week+(year*52)].days_count = 0;
			for ( i = 0; i < days_per_week; i++ ) {
				dataset->rows_aggr[week+(year*52)].nights_count += dataset->rows_daily[index+k+i].nights_count;
				dataset->rows_aggr[week+(year*52)].days_count += dataset->rows_daily[index+k+i].days_count;
			}
			dataset->rows_aggr[week+(year*52)].nights_count /= days_per_week;
			dataset->rows_aggr[week+(year*52)].days_count /= days_per_week;

			/* */
			k += days_per_week;
		}
		index += rows_per_year;
	}

	/* fix qc */
	for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[TA_M]) ) dataset->rows_aggr[i].value[TA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[VPD_M]) ) dataset->rows_aggr[i].value[VPD_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[SW_IN_M]) ) dataset->rows_aggr[i].value[SW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_M]) ) dataset->rows_aggr[i].value[LW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[PA_M]) ) dataset->rows_aggr[i].value[PA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[PRECIP_M]) ) dataset->rows_aggr[i].value[PRECIP_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[WS_M]) ) dataset->rows_aggr[i].value[WS_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[TA_FILLED]) ) dataset->rows_aggr[i].value[TA_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[VPD_FILLED]) ) dataset->rows_aggr[i].value[VPD_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[SW_IN_FILLED]) ) dataset->rows_aggr[i].value[SW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_FILLED]) ) dataset->rows_aggr[i].value[LW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[CO2_FILLED]) ) dataset->rows_aggr[i].value[CO2_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_CALC]) ) dataset->rows_aggr[i].value[LW_IN_CALC_QC] = INVALID_VALUE;
		
		/* Ts */
		for ( y = 0; y < dataset->ts_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->tss_aggr[i][y].filled) ) {
				dataset->tss_aggr[i][y].qc = INVALID_VALUE;
			}
		}

		/* SWC */
		for ( y = 0; y < dataset->swc_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->swcs_aggr[i][y].filled) ) {
				dataset->swcs_aggr[i][y].qc = INVALID_VALUE;
			}
		}
	}

	return 1;
}

/* */
static int compute_mm(DATASET *const dataset) {
	int i;
	int y;
	int index;
	int month;
	int year;
	int rows_per_day;
	int rows_per_year;
	int days_per_month_count;
	int k;
	int valids_count;
	int qc_valids_count;

	assert(dataset);

	/* */
	rows_per_day = 48;
	if ( dataset->hourly ) {
		rows_per_day /= 2;
	}

	/* */
	index = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* get rows_per_year count */
		rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_per_year /= 2;
		}
		rows_per_year /= rows_per_day;

		/* loop for months */
		k = 0;
		for ( month = 0; month < 12; month++ ) {
			/* compute days per month count */
			days_per_month_count = days_per_month[month];
			if ( (FEBRUARY == month) && IS_LEAP_YEAR(dataset->years[year].year) ) {
				++days_per_month_count;
			}
			/* aggr ERA */
			for ( y = 0; y < ERA_REQUIRED_VALUES; y++ ) {
				valids_count = 0;
				dataset->rows_aggr[month+(year*12)].value[y] = 0.0;
				for ( i = 0; i < days_per_month_count; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].value[y]) ) {
						dataset->rows_aggr[month+(year*12)].value[y] += dataset->rows_daily[index+k+i].value[y];
						++valids_count;
					}
				}
				if ( valids_count == days_per_month_count ) {
					dataset->rows_aggr[month+(year*12)].value[y] /= valids_count;
				} else {
					dataset->rows_aggr[month+(year*12)].value[y] = INVALID_VALUE;
				}
			}

			/* aggr RPOT */
			valids_count = 0;
			dataset->rows_aggr[month+(year*12)].value[RPOT_MET] = 0.0;
			for ( i = 0; i < days_per_month_count; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].value[RPOT_MET]) ) {
					dataset->rows_aggr[month+(year*12)].value[RPOT_MET] += dataset->rows_daily[index+k+i].value[RPOT_MET];
					++valids_count;
				}
			}
			if ( valids_count == days_per_month_count ) {
				dataset->rows_aggr[month+(year*12)].value[RPOT_MET] /= days_per_month_count;
			} else {
				dataset->rows_aggr[month+(year*12)].value[RPOT_MET] = INVALID_VALUE;
			}

			/*	aggr FILLED, QCs, M, CALC and QCs
				if there is one invalid values (i.e. impossible to fill in the gapfilling) the whole day is set as -9999
			*/
			for ( y = TA_FILLED; y < VALUES; y++ ) {
				/* do not aggregate temp values !*/
				if (	(y == FPAR) ||
						( y == CLOUD_COVER) ||
						( y == R_CLOUD ) ||
						( y == ESAT ) ||
						( y == VP ) ||
						( y == epsA ) ) {
							continue;
				}
				valids_count = 0;
				dataset->rows_aggr[month+(year*12)].value[y] = 0.0;
				for ( i = 0; i < days_per_month_count; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->rows_daily[index+k+i].value[y]) ) {
						dataset->rows_aggr[month+(year*12)].value[y] += dataset->rows_daily[index+k+i].value[y];
						++valids_count;
					}
				}
				if ( valids_count == days_per_month_count ) {
					dataset->rows_aggr[month+(year*12)].value[y] /= valids_count;
				} else {
					dataset->rows_aggr[month+(year*12)].value[y] = INVALID_VALUE;
				}
			}

			/* aggr Ts */
			for ( y = 0; y < dataset->ts_count; y++ ) {
				valids_count = 0;
				qc_valids_count = 0;
				dataset->tss_aggr[month+(year*12)][y].filled = 0.0;
				dataset->tss_aggr[month+(year*12)][y].qc = 0.0;
				for ( i = 0; i < days_per_month_count; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->tss_daily[index+k+i][y].filled) ) {
						dataset->tss_aggr[month+(year*12)][y].filled += dataset->tss_daily[index+k+i][y].filled;
						++valids_count;
					}
					if ( !IS_INVALID_VALUE(dataset->tss_daily[index+k+i][y].qc) ) {
						dataset->tss_aggr[month+(year*12)][y].qc += dataset->tss_daily[index+k+i][y].qc;
						++qc_valids_count;
					}
				}
				if ( valids_count == days_per_month_count ) {
					dataset->tss_aggr[month+(year*12)][y].filled /= valids_count;
				} else {
					dataset->tss_aggr[month+(year*12)][y].filled = INVALID_VALUE;
				}
				if ( qc_valids_count == days_per_month_count ) {
					dataset->tss_aggr[month+(year*12)][y].qc /= qc_valids_count;
				} else {
					dataset->tss_aggr[month+(year*12)][y].qc = INVALID_VALUE;
				}
			}

			/* aggr SWC */
			for ( y = 0; y < dataset->swc_count; y++ ) {
				valids_count = 0;
				qc_valids_count = 0;
				dataset->swcs_aggr[month+(year*12)][y].filled = 0.0;
				dataset->swcs_aggr[month+(year*12)][y].qc = 0.0;
				for ( i = 0; i < days_per_month_count; i++ ) {
					if ( !IS_INVALID_VALUE(dataset->swcs_daily[index+k+i][y].filled) ) {
						dataset->swcs_aggr[month+(year*12)][y].filled += dataset->swcs_daily[index+k+i][y].filled;
						++valids_count;
					}
					if ( !IS_INVALID_VALUE(dataset->swcs_daily[index+k+i][y].qc) ) {
						dataset->swcs_aggr[month+(year*12)][y].qc += dataset->swcs_daily[index+k+i][y].qc;
						++qc_valids_count;
					}
				}
				if ( valids_count == days_per_month_count ) {
					dataset->swcs_aggr[month+(year*12)][y].filled /= valids_count;
				} else {
					dataset->swcs_aggr[month+(year*12)][y].filled = INVALID_VALUE;
				}
				if ( qc_valids_count == days_per_month_count ) {
					dataset->swcs_aggr[month+(year*12)][y].qc /= qc_valids_count;
				} else {
					dataset->swcs_aggr[month+(year*12)][y].qc = INVALID_VALUE;
				}
			}

			/* aggr nights and days */
			dataset->rows_aggr[month+(year*12)].nights_count = 0;
			dataset->rows_aggr[month+(year*12)].days_count = 0;
			for ( i = 0; i < days_per_month_count; i++ ) {
				dataset->rows_aggr[month+(year*12)].nights_count += dataset->rows_daily[index+k+i].nights_count;
				dataset->rows_aggr[month+(year*12)].days_count += dataset->rows_daily[index+k+i].days_count;
			}
			dataset->rows_aggr[month+(year*12)].nights_count /= days_per_month_count;
			dataset->rows_aggr[month+(year*12)].days_count /= days_per_month_count;

			/* */
			k += days_per_month_count;
		}
		index += rows_per_year;
	}

	dataset->rows_aggr_count = dataset->years_count*12;

	/* fix qc */
	for ( i = 0; i < dataset->rows_aggr_count; i++ ) {
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[TA_M]) ) dataset->rows_aggr[i].value[TA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[VPD_M]) ) dataset->rows_aggr[i].value[VPD_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[SW_IN_M]) ) dataset->rows_aggr[i].value[SW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_M]) ) dataset->rows_aggr[i].value[LW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[PA_M]) ) dataset->rows_aggr[i].value[PA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[PRECIP_M]) ) dataset->rows_aggr[i].value[PRECIP_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[WS_M]) ) dataset->rows_aggr[i].value[WS_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[TA_FILLED]) ) dataset->rows_aggr[i].value[TA_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[VPD_FILLED]) ) dataset->rows_aggr[i].value[VPD_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[SW_IN_FILLED]) ) dataset->rows_aggr[i].value[SW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_FILLED]) ) dataset->rows_aggr[i].value[LW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[CO2_FILLED]) ) dataset->rows_aggr[i].value[CO2_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_CALC]) ) dataset->rows_aggr[i].value[LW_IN_CALC_QC] = INVALID_VALUE;

		/* Ts */
		for ( y = 0; y < dataset->ts_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->tss_aggr[i][y].filled) ) {
				dataset->tss_aggr[i][y].qc = INVALID_VALUE;
			}
		}

		/* SWC */
		for ( y = 0; y < dataset->swc_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->swcs_aggr[i][y].filled) ) {
				dataset->swcs_aggr[i][y].qc = INVALID_VALUE;
			}
		}
	}

	return 1;
}

/* */
static int compute_yy(DATASET *const dataset) {
	int i;
	int y;
	int index;
	int year;
	int rows_per_day;
	int rows_per_year;
	int valids_count;
	int qc_valids_count;

	assert(dataset);

	/* */
	rows_per_day = 48;
	if ( dataset->hourly ) {
		rows_per_day /= 2;
	}

	/* */
	index = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		/* get rows_per_year count */
		rows_per_year = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			rows_per_year /= 2;
		}
		rows_per_year /= rows_per_day;
		
		/* aggr ERA */
		for ( y = 0; y < ERA_REQUIRED_VALUES; y++ ) {
			valids_count = 0;
			dataset->rows_aggr[year].value[y] = 0.0;
			for ( i = 0; i < rows_per_year; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows_daily[index+i].value[y]) ) {
					dataset->rows_aggr[year].value[y] += dataset->rows_daily[index+i].value[y];
					++valids_count;
				}
			}
			if ( valids_count == rows_per_year ) {
				if ( PRECIP_ERA != y ) { /* PRECIP MUST BE SUM, NOT MEAN */
					dataset->rows_aggr[year].value[y] /= valids_count;
				}
			} else {
				dataset->rows_aggr[year].value[y] = INVALID_VALUE;
			}
		}

		/* aggr RPOT */
		valids_count = 0;
		dataset->rows_aggr[year].value[RPOT_MET] = 0.0;
		for ( i = 0; i < rows_per_year; i++ ) {
			if ( !IS_INVALID_VALUE(dataset->rows_daily[index+i].value[RPOT_MET]) ) {
				dataset->rows_aggr[year].value[RPOT_MET] += dataset->rows_daily[index+i].value[RPOT_MET];
				++valids_count;
			}
		}
		if ( valids_count == rows_per_year ) {
			dataset->rows_aggr[year].value[RPOT_MET] /= valids_count;
		} else {
			dataset->rows_aggr[year].value[RPOT_MET] = INVALID_VALUE;
		}

		/*	aggr FILLED, QCs, M, CALC and QCs
			if there is one invalid values (i.e. impossible to fill in the gapfilling) the whole day is set as -9999
		*/
		for ( y = TA_FILLED; y < VALUES; y++ ) {
			/* do not aggregate temp values !*/
			if (	(y == FPAR) ||
					( y == CLOUD_COVER) ||
					( y == R_CLOUD ) ||
					( y == ESAT ) ||
					( y == VP ) ||
					( y == epsA ) ) {
						continue;
			}
			valids_count = 0;
			dataset->rows_aggr[year].value[y] = 0.0;
			for ( i = 0; i < rows_per_year; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->rows_daily[index+i].value[y]) ) {
					dataset->rows_aggr[year].value[y] += dataset->rows_daily[index+i].value[y];
					++valids_count;
				}
			}
			if ( valids_count == rows_per_year ) {
				if ( PRECIP_M != y ) { /* PRECIP MUST BE SUM, NOT MEAN */
					dataset->rows_aggr[year].value[y] /= valids_count;
				}
			} else {
				dataset->rows_aggr[year].value[y] = INVALID_VALUE;
			}
		}

		/* aggr Ts */
		for ( y  = 0; y < dataset->ts_count; y++ ) {
			valids_count = 0;
			qc_valids_count = 0;
			dataset->tss_aggr[year][y].filled = 0.0;
			dataset->tss_aggr[year][y].qc = 0.0;
			for ( i = 0; i < rows_per_year; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->tss_daily[index+i][y].filled) ) {
					dataset->tss_aggr[year][y].filled += dataset->tss_daily[index+i][y].filled;
					++valids_count;
				}
				if ( !IS_INVALID_VALUE(dataset->tss_daily[index+i][y].qc) ) {
					dataset->tss_aggr[year][y].qc += dataset->tss_daily[index+i][y].qc;
					++qc_valids_count;
				}
			}
			if ( valids_count == rows_per_year ) {
				dataset->tss_aggr[year][y].filled /= valids_count;
			} else {
				dataset->tss_aggr[year][y].filled = INVALID_VALUE;
			}
			if ( qc_valids_count == rows_per_year ) {
				dataset->tss_aggr[year][y].qc /= qc_valids_count;
			} else {
				dataset->tss_aggr[year][y].qc = INVALID_VALUE;
			}
		}

		/* aggr SWC */
		for ( y  = 0; y < dataset->swc_count; y++ ) {
			valids_count = 0;
			qc_valids_count = 0;
			dataset->swcs_aggr[year][y].filled = 0.0;
			dataset->swcs_aggr[year][y].qc = 0.0;
			for ( i = 0; i < rows_per_year; i++ ) {
				if ( !IS_INVALID_VALUE(dataset->swcs_daily[index+i][y].filled) ) {
					dataset->swcs_aggr[year][y].filled += dataset->swcs_daily[index+i][y].filled;
					++valids_count;
				}
				if ( !IS_INVALID_VALUE(dataset->swcs_daily[index+i][y].qc) ) {
					dataset->swcs_aggr[year][y].qc += dataset->swcs_daily[index+i][y].qc;
					++qc_valids_count;
				}
			}
			if ( valids_count == rows_per_year ) {
				dataset->swcs_aggr[year][y].filled /= valids_count;
			} else {
				dataset->swcs_aggr[year][y].filled = INVALID_VALUE;
			}
			if ( qc_valids_count == rows_per_year ) {
				dataset->swcs_aggr[year][y].qc /= qc_valids_count;
			} else {
				dataset->swcs_aggr[year][y].qc = INVALID_VALUE;
			}
		}

		/* */
		index += rows_per_year;
	}

	/* fix qc */
	for ( i = 0; i < dataset->years_count; i++ ) {
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[TA_M]) ) dataset->rows_aggr[i].value[TA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[VPD_M]) ) dataset->rows_aggr[i].value[VPD_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[SW_IN_M]) ) dataset->rows_aggr[i].value[SW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_M]) ) dataset->rows_aggr[i].value[LW_IN_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[PA_M]) ) dataset->rows_aggr[i].value[PA_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[PRECIP_M]) ) dataset->rows_aggr[i].value[PRECIP_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[WS_M]) ) dataset->rows_aggr[i].value[WS_M_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[TA_FILLED]) ) dataset->rows_aggr[i].value[TA_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[VPD_FILLED]) ) dataset->rows_aggr[i].value[VPD_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[SW_IN_FILLED]) ) dataset->rows_aggr[i].value[SW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_FILLED]) ) dataset->rows_aggr[i].value[LW_IN_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[CO2_FILLED]) ) dataset->rows_aggr[i].value[CO2_QC] = INVALID_VALUE;
		if ( IS_INVALID_VALUE(dataset->rows_aggr[i].value[LW_IN_CALC]) ) dataset->rows_aggr[i].value[LW_IN_CALC_QC] = INVALID_VALUE;

		/* Ts */
		for ( y = 0; y < dataset->ts_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->tss_aggr[i][y].filled) ) {
				dataset->tss_aggr[i][y].qc = INVALID_VALUE;
			}
		}

		/* SWC */
		for ( y = 0; y < dataset->swc_count; y++ ) {
			if ( IS_INVALID_VALUE(dataset->swcs_aggr[i][y].filled) ) {
				dataset->swcs_aggr[i][y].qc = INVALID_VALUE;
			}
		}
	}

	return 1;
}

/* */
static int save_dataset_hh(const DATASET *const dataset) {
	char *p;
	char *huge_buffer;
	char buffer[BUFFER_SIZE];
	int i;
	int j;
	int y;
	int row;
	int profile;
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_hh, output_files_path, dataset->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_hh, TIMESTAMP_HEADER);
	for ( profile = 0; profile < dataset->ts_count; profile++ ) {
		fprintf(f, ",TS_%d_f,TS_%d_fqc", dataset->ts_profiles[profile], dataset->ts_profiles[profile]);
	}
	for ( profile = 0; profile < dataset->swc_count; profile++ ) {
		fprintf(f, ",SWC_%d_f,SWC_%d_fqc", dataset->swc_profiles[profile], dataset->swc_profiles[profile]);
	}
	fputs("\n", f);

	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			y /= 2;
		}
		for ( row = 0; row < y; row++ ) {
			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(row, dataset->years[i].year, dataset->timeres); 
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(row, dataset->years[i].year, dataset->timeres); 
			fprintf(f, ",%s,", p);
			/* write values */
			fprintf(f, output_format_hh,
										get_dtime_by_row(row, dataset->hourly),

										dataset->rows[j+row].value[TA_FILLED],
										dataset->rows[j+row].value[TA_QC],
										dataset->rows[j+row].value[TA_ERA],
										dataset->rows[j+row].value[TA_M],
										dataset->rows[j+row].value[TA_M_QC],

										dataset->rows[j+row].value[RPOT_MET],

										dataset->rows[j+row].value[SW_IN_FILLED],
										dataset->rows[j+row].value[SW_IN_QC],
										dataset->rows[j+row].value[SW_IN_ERA],
										dataset->rows[j+row].value[SW_IN_M],
										dataset->rows[j+row].value[SW_IN_M_QC],

										dataset->rows[j+row].value[LW_IN_FILLED],
										dataset->rows[j+row].value[LW_IN_QC],
										dataset->rows[j+row].value[LW_IN_ERA],
										dataset->rows[j+row].value[LW_IN_M],
										IS_INVALID_VALUE(dataset->rows[j+row].value[LW_IN_M]) ? INVALID_VALUE : dataset->rows[j+row].value[LW_IN_M_QC],
										dataset->rows[j+row].value[LW_IN_CALC],
										dataset->rows[j+row].value[LW_IN_CALC_QC],
										dataset->rows[j+row].value[LW_IN_CALC_ERA],
										dataset->rows[j+row].value[LW_IN_CALC_M],
										dataset->rows[j+row].value[LW_IN_CALC_M_QC],

										dataset->rows[j+row].value[VPD_FILLED],
										dataset->rows[j+row].value[VPD_QC],
										dataset->rows[j+row].value[VPD_ERA],
										dataset->rows[j+row].value[VPD_M],
										dataset->rows[j+row].value[VPD_M_QC],

										dataset->rows[j+row].value[PA_MET],
										dataset->rows[j+row].value[PA_ERA],
										dataset->rows[j+row].value[PA_M],
										dataset->rows[j+row].value[PA_M_QC],

										dataset->rows[j+row].value[PRECIP_MET],
										dataset->rows[j+row].value[PRECIP_ERA],
										dataset->rows[j+row].value[PRECIP_M],
										dataset->rows[j+row].value[PRECIP_M_QC],

										dataset->rows[j+row].value[WS_MET],
										dataset->rows[j+row].value[WS_ERA],
										dataset->rows[j+row].value[WS_M],
										dataset->rows[j+row].value[WS_M_QC],

										dataset->rows[j+row].value[CO2_FILLED],
										dataset->rows[j+row].value[CO2_QC]
			);

			/* Ts */
			for ( profile = 0; profile < dataset->ts_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->tss[j+row][profile].filled,
													dataset->tss[j+row][profile].qc
				);
			}
	
			/* SWC */
			for ( profile = 0; profile < dataset->swc_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->swcs[j+row][profile].filled,
													dataset->swcs[j+row][profile].qc
				);
			}

			fputs("\n", f);
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* alloc memory for huge buffer */
	huge_buffer = malloc(INFO_BUFFER_SIZE*sizeof*huge_buffer);
	if ( !huge_buffer ) {
		puts(err_out_of_memory);
		return 0;
	}
	huge_buffer[0] = '\0';

	/* save stat */
	sprintf(buffer, output_stat_file, output_files_path, dataset->site, "hh");
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create info file!");
		free(huge_buffer);
		return 0;
	}
	for ( i = 0; i < dataset->ts_count; i++ ) {
		sprintf(buffer, info_ts_hh, dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	for ( i = 0; i < dataset->swc_count; i++ ) {
		sprintf(buffer, info_swc_hh, dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	strcat(huge_buffer, "\n");
	fprintf(f, info_hh, huge_buffer);
	fputs(dataset->stat, f);
	fclose(f);

	/* free memory */
	free(huge_buffer);

	/* ok */
	return 1;
}

/* */
static int save_dataset_dd(const DATASET *const dataset) {
	int i;
	int j;
	int y;
	int row;
	int profile;
	char buffer[BUFFER_SIZE];
	char *huge_buffer;
	FILE *f;
	TIMESTAMP *t;

	/* create output file */
	sprintf(buffer, output_file_dd, output_files_path, dataset->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_dd, TIMESTAMP_STRING);
	for ( profile = 0; profile < dataset->ts_count; profile++ ) {
		fprintf(f, ",TS_%d_f,TS_%d_fqc", dataset->ts_profiles[profile], dataset->ts_profiles[profile]);
	}
	for ( profile = 0; profile < dataset->swc_count; profile++ ) {
		fprintf(f, ",SWC_%d_f,SWC_%d_fqc", dataset->swc_profiles[profile], dataset->swc_profiles[profile]);
	}
	fputs(",night_d,day_d\n", f);

	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		y = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( dataset->hourly ) {
			y /= 2;
		}
		y /= (dataset->hourly ? 24 : 48);
		for ( row = 0; row < y; row++ ) {
			t = timestamp_end_by_row(row*(dataset->hourly ? 24 : 48), dataset->years[i].year, dataset->timeres);
			/* write values */
			fprintf(f, output_format_dd,
										t->YYYY,
										t->MM,
										t->DD,

										dataset->rows_daily[j+row].value[TA_FILLED],
										dataset->rows_daily[j+row].value[TA_QC],
										dataset->rows_daily[j+row].value[TA_F_NIGHT],
										dataset->rows_daily[j+row].value[TA_F_NIGHT_STD],
										dataset->rows_daily[j+row].value[TA_F_NIGHT_QC],
										dataset->rows_daily[j+row].value[TA_F_DAY],
										dataset->rows_daily[j+row].value[TA_F_DAY_STD],
										dataset->rows_daily[j+row].value[TA_F_DAY_QC],
										dataset->rows_daily[j+row].value[TA_ERA],
										dataset->rows_daily[j+row].value[TA_ERA_NIGHT],
										dataset->rows_daily[j+row].value[TA_ERA_NIGHT_STD],
										dataset->rows_daily[j+row].value[TA_ERA_DAY],
										dataset->rows_daily[j+row].value[TA_ERA_DAY_STD],
										dataset->rows_daily[j+row].value[TA_M],
										dataset->rows_daily[j+row].value[TA_M_QC],
										dataset->rows_daily[j+row].value[TA_M_NIGHT],
										dataset->rows_daily[j+row].value[TA_M_NIGHT_STD],
										dataset->rows_daily[j+row].value[TA_M_NIGHT_QC],
										dataset->rows_daily[j+row].value[TA_M_DAY],
										dataset->rows_daily[j+row].value[TA_M_DAY_STD],
										dataset->rows_daily[j+row].value[TA_M_DAY_QC],

										dataset->rows_daily[j+row].value[RPOT_MET],

										dataset->rows_daily[j+row].value[SW_IN_FILLED],
										dataset->rows_daily[j+row].value[SW_IN_QC],
										dataset->rows_daily[j+row].value[SW_IN_ERA],
										dataset->rows_daily[j+row].value[SW_IN_M],
										dataset->rows_daily[j+row].value[SW_IN_M_QC],

										dataset->rows_daily[j+row].value[LW_IN_FILLED],
										dataset->rows_daily[j+row].value[LW_IN_QC],
										dataset->rows_daily[j+row].value[LW_IN_ERA],
										dataset->rows_daily[j+row].value[LW_IN_M],
										dataset->rows_daily[j+row].value[LW_IN_M_QC],
										dataset->rows_daily[j+row].value[LW_IN_CALC],
										dataset->rows_daily[j+row].value[LW_IN_CALC_QC],
										dataset->rows_daily[j+row].value[LW_IN_CALC_ERA],
										dataset->rows_daily[j+row].value[LW_IN_CALC_M],
										dataset->rows_daily[j+row].value[LW_IN_CALC_M_QC],
										
										dataset->rows_daily[j+row].value[VPD_FILLED],
										dataset->rows_daily[j+row].value[VPD_QC],
										dataset->rows_daily[j+row].value[VPD_ERA],
										dataset->rows_daily[j+row].value[VPD_M],
										dataset->rows_daily[j+row].value[VPD_M_QC],

										dataset->rows_daily[j+row].value[PA_ERA],
										dataset->rows_daily[j+row].value[PA_M],
										dataset->rows_daily[j+row].value[PA_M_QC],

										dataset->rows_daily[j+row].value[PRECIP_ERA],
										dataset->rows_daily[j+row].value[PRECIP_M],
										dataset->rows_daily[j+row].value[PRECIP_M_QC],

										dataset->rows_daily[j+row].value[WS_ERA],
										dataset->rows_daily[j+row].value[WS_M],
										dataset->rows_daily[j+row].value[WS_M_QC],

										dataset->rows_daily[j+row].value[CO2_FILLED],
										dataset->rows_daily[j+row].value[CO2_QC]
			);

			/* Ts */
			for ( profile = 0; profile < dataset->ts_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->tss_daily[j+row][profile].filled,
													dataset->tss_daily[j+row][profile].qc
				);
			}
	
			/* SWC */
			for ( profile = 0; profile < dataset->swc_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->swcs_daily[j+row][profile].filled,
													dataset->swcs_daily[j+row][profile].qc
				);
			}

			/* nights and days */
			fprintf(f, ",%g,%g\n", dataset->rows_daily[j+row].nights_count, dataset->rows_daily[j+row].days_count);
		}
		j += y;
	}

	/* close file */
	fclose(f);

	/* alloc memory for huge buffer */
	huge_buffer = malloc(INFO_BUFFER_SIZE*sizeof*huge_buffer);
	if ( !huge_buffer ) {
		puts(err_out_of_memory);
		return 0;
	}
	huge_buffer[0] = '\0';

	/* save stat */
	sprintf(buffer, output_stat_file, output_files_path, dataset->site, "dd");
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create info file!");
		free(huge_buffer);
		return 0;
	}
	for ( i = 0; i < dataset->ts_count; i++ ) {
		sprintf(buffer, info_ts_dd_ww_mm_yy, dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	for ( i = 0; i < dataset->swc_count; i++ ) {
		sprintf(buffer, info_swc_dd_ww_mm_yy, dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	strcat(huge_buffer, info_nights_days_dd);
	strcat(huge_buffer, "\n");
	fprintf(f, info_dd, huge_buffer);
	fputs(dataset->stat, f);
	fclose(f);

	/* free memory */
	free(huge_buffer);

	/* ok */
	return 1;
}

/* */
static int save_dataset_ww(const DATASET *const dataset) {
	char *p;
	char *huge_buffer;
	char buffer[BUFFER_SIZE];
	int i;
	int j;
	int row;
	int year;
	int profile;
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_ww, output_files_path, dataset->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_ww, TIMESTAMP_HEADER);
	for ( profile = 0; profile < dataset->ts_count; profile++ ) {
		fprintf(f, ",TS_%d_f,TS_%d_fqc", dataset->ts_profiles[profile], dataset->ts_profiles[profile]);
	}
	for ( profile = 0; profile < dataset->swc_count; profile++ ) {
		fprintf(f, ",SWC_%d_f,SWC_%d_fqc", dataset->swc_profiles[profile], dataset->swc_profiles[profile]);
	}
	fputs(",night_d,day_d\n", f);
	
	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		for ( row = 0; row < 52; row++ ) {
			/* write timestamp_start */
			p = timestamp_ww_get_by_row_s(row, year, dataset->timeres, 1);
			fprintf(f, "%s,", p);
			/* write timestamp_end */
			p = timestamp_ww_get_by_row_s(row, year, dataset->timeres, 0);
			fprintf(f, "%s,", p);
			/* write values */
			fprintf(f, output_format_ww,
										row+1,
										dataset->rows_aggr[j+row].value[TA_FILLED],
										dataset->rows_aggr[j+row].value[TA_QC],
										dataset->rows_aggr[j+row].value[TA_F_NIGHT],
										dataset->rows_aggr[j+row].value[TA_F_NIGHT_STD],
										dataset->rows_aggr[j+row].value[TA_F_NIGHT_QC],
										dataset->rows_aggr[j+row].value[TA_F_DAY],
										dataset->rows_aggr[j+row].value[TA_F_DAY_STD],
										dataset->rows_aggr[j+row].value[TA_F_DAY_QC],
										dataset->rows_aggr[j+row].value[TA_ERA],
										dataset->rows_aggr[j+row].value[TA_ERA_NIGHT],
										dataset->rows_aggr[j+row].value[TA_ERA_NIGHT_STD],
										dataset->rows_aggr[j+row].value[TA_ERA_DAY],
										dataset->rows_aggr[j+row].value[TA_ERA_DAY_STD],
										dataset->rows_aggr[j+row].value[TA_M],
										dataset->rows_aggr[j+row].value[TA_M_QC],
										dataset->rows_aggr[j+row].value[TA_M_NIGHT],
										dataset->rows_aggr[j+row].value[TA_M_NIGHT_STD],
										dataset->rows_aggr[j+row].value[TA_M_NIGHT_QC],
										dataset->rows_aggr[j+row].value[TA_M_DAY],
										dataset->rows_aggr[j+row].value[TA_M_DAY_STD],
										dataset->rows_aggr[j+row].value[TA_M_DAY_QC],

										dataset->rows_aggr[j+row].value[RPOT_MET],

										dataset->rows_aggr[j+row].value[SW_IN_FILLED],
										dataset->rows_aggr[j+row].value[SW_IN_QC],
										dataset->rows_aggr[j+row].value[SW_IN_ERA],

										dataset->rows_aggr[j+row].value[SW_IN_M],
										dataset->rows_aggr[j+row].value[SW_IN_M_QC],

										dataset->rows_aggr[j+row].value[LW_IN_FILLED],
										dataset->rows_aggr[j+row].value[LW_IN_QC],
										dataset->rows_aggr[j+row].value[LW_IN_ERA],
										dataset->rows_aggr[j+row].value[LW_IN_M],
										dataset->rows_aggr[j+row].value[LW_IN_M_QC],
										dataset->rows_aggr[j+row].value[LW_IN_CALC],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_QC],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_ERA],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_M],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_M_QC],
										
										dataset->rows_aggr[j+row].value[VPD_FILLED],
										dataset->rows_aggr[j+row].value[VPD_QC],
										dataset->rows_aggr[j+row].value[VPD_ERA],
										dataset->rows_aggr[j+row].value[VPD_M],
										dataset->rows_aggr[j+row].value[VPD_M_QC],

										dataset->rows_aggr[j+row].value[PA_ERA],
										dataset->rows_aggr[j+row].value[PA_M],
										dataset->rows_aggr[j+row].value[PA_M_QC],

										dataset->rows_aggr[j+row].value[PRECIP_ERA],
										dataset->rows_aggr[j+row].value[PRECIP_M],
										dataset->rows_aggr[j+row].value[PRECIP_M_QC],

										dataset->rows_aggr[j+row].value[WS_ERA],
										dataset->rows_aggr[j+row].value[WS_M],
										dataset->rows_aggr[j+row].value[WS_M_QC],

										dataset->rows_aggr[j+row].value[CO2_FILLED],
										dataset->rows_aggr[j+row].value[CO2_QC]
			);

			/* Ts */
			for ( profile = 0; profile < dataset->ts_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->tss_aggr[j+row][profile].filled,
													dataset->tss_aggr[j+row][profile].qc
				);
			}
	
			/* SWC */
			for ( profile = 0; profile < dataset->swc_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->swcs_aggr[j+row][profile].filled,
													dataset->swcs_aggr[j+row][profile].qc
				);
			}

			/* nights and days */
			fprintf(f, ",%g,%g\n", dataset->rows_aggr[j+row].nights_count, dataset->rows_aggr[j+row].days_count);
		}
		j += 52;
	}

	/* close file */
	fclose(f);

	/* alloc memory for huge buffer */
	huge_buffer = malloc(INFO_BUFFER_SIZE*sizeof*huge_buffer);
	if ( !huge_buffer ) {
		puts(err_out_of_memory);
		return 0;
	}
	huge_buffer[0] = '\0';

	/* save stat */
	sprintf(buffer, output_stat_file, output_files_path, dataset->site, "ww");
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create info file!");
		free(huge_buffer);
		return 0;
	}
		for ( i = 0; i < dataset->ts_count; i++ ) {
		sprintf(buffer, info_ts_dd_ww_mm_yy, dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	for ( i = 0; i < dataset->swc_count; i++ ) {
		sprintf(buffer, info_swc_dd_ww_mm_yy, dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	strcat(huge_buffer, info_nights_days_ww_mm);
	strcat(huge_buffer, "\n");
	fprintf(f, info_ww, huge_buffer);
	fputs(dataset->stat, f);
	fclose(f);

	/* free memory */
	free(huge_buffer);

	/* ok */
	return 1;
}

/* */
static int save_dataset_mm(const DATASET *const dataset) {
	int i;
	int j;
	int row;
	int year;
	int profile;
	char buffer[BUFFER_SIZE];
	char *huge_buffer;
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_mm, output_files_path, dataset->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_mm, TIMESTAMP_STRING);
	for ( profile = 0; profile < dataset->ts_count; profile++ ) {
		fprintf(f, ",TS_%d_f,TS_%d_fqc", dataset->ts_profiles[profile], dataset->ts_profiles[profile]);
	}
	for ( profile = 0; profile < dataset->swc_count; profile++ ) {
		fprintf(f, ",SWC_%d_f,SWC_%d_fqc", dataset->swc_profiles[profile], dataset->swc_profiles[profile]);
	}
	fputs(",night_d,day_d\n", f);
	
	/* write results */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		for ( row = 0; row < 12; row++ ) {
			/* write values */
			fprintf(f, output_format_mm,
										year,
										row+1,
										dataset->rows_aggr[j+row].value[TA_FILLED],
										dataset->rows_aggr[j+row].value[TA_QC],
										dataset->rows_aggr[j+row].value[TA_F_NIGHT],
										dataset->rows_aggr[j+row].value[TA_F_NIGHT_STD],
										dataset->rows_aggr[j+row].value[TA_F_NIGHT_QC],
										dataset->rows_aggr[j+row].value[TA_F_DAY],
										dataset->rows_aggr[j+row].value[TA_F_DAY_STD],
										dataset->rows_aggr[j+row].value[TA_F_DAY_QC],
										dataset->rows_aggr[j+row].value[TA_ERA],
										dataset->rows_aggr[j+row].value[TA_ERA_NIGHT],
										dataset->rows_aggr[j+row].value[TA_ERA_NIGHT_STD],
										dataset->rows_aggr[j+row].value[TA_ERA_DAY],
										dataset->rows_aggr[j+row].value[TA_ERA_DAY_STD],
										dataset->rows_aggr[j+row].value[TA_M],
										dataset->rows_aggr[j+row].value[TA_M_QC],
										dataset->rows_aggr[j+row].value[TA_M_NIGHT],
										dataset->rows_aggr[j+row].value[TA_M_NIGHT_STD],
										dataset->rows_aggr[j+row].value[TA_M_NIGHT_QC],
										dataset->rows_aggr[j+row].value[TA_M_DAY],
										dataset->rows_aggr[j+row].value[TA_M_DAY_STD],
										dataset->rows_aggr[j+row].value[TA_M_DAY_QC],

										dataset->rows_aggr[j+row].value[RPOT_MET],

										dataset->rows_aggr[j+row].value[SW_IN_FILLED],
										dataset->rows_aggr[j+row].value[SW_IN_QC],
										dataset->rows_aggr[j+row].value[SW_IN_ERA],
										dataset->rows_aggr[j+row].value[SW_IN_M],
										dataset->rows_aggr[j+row].value[SW_IN_M_QC],

										dataset->rows_aggr[j+row].value[LW_IN_FILLED],
										dataset->rows_aggr[j+row].value[LW_IN_QC],
										dataset->rows_aggr[j+row].value[LW_IN_ERA],
										dataset->rows_aggr[j+row].value[LW_IN_M],
										dataset->rows_aggr[j+row].value[LW_IN_M_QC],
										dataset->rows_aggr[j+row].value[LW_IN_CALC],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_QC],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_ERA],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_M],
										dataset->rows_aggr[j+row].value[LW_IN_CALC_M_QC],

										dataset->rows_aggr[j+row].value[VPD_FILLED],
										dataset->rows_aggr[j+row].value[VPD_QC],
										dataset->rows_aggr[j+row].value[VPD_ERA],
										dataset->rows_aggr[j+row].value[VPD_M],
										dataset->rows_aggr[j+row].value[VPD_M_QC],

										dataset->rows_aggr[j+row].value[PA_ERA],
										dataset->rows_aggr[j+row].value[PA_M],
										dataset->rows_aggr[j+row].value[PA_M_QC],

										dataset->rows_aggr[j+row].value[PRECIP_ERA],
										dataset->rows_aggr[j+row].value[PRECIP_M],
										dataset->rows_aggr[j+row].value[PRECIP_M_QC],

										dataset->rows_aggr[j+row].value[WS_ERA],
										dataset->rows_aggr[j+row].value[WS_M],
										dataset->rows_aggr[j+row].value[WS_M_QC],

										dataset->rows_aggr[j+row].value[CO2_FILLED],
										dataset->rows_aggr[j+row].value[CO2_QC]
			);

			/* Ts */
			for ( profile = 0; profile < dataset->ts_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->tss_aggr[j+row][profile].filled,
													dataset->tss_aggr[j+row][profile].qc
				);
			}
	
			/* SWC */
			for ( profile = 0; profile < dataset->swc_count; profile++ ) {
				fprintf(f, output_format_profile,	dataset->swcs_aggr[j+row][profile].filled,
													dataset->swcs_aggr[j+row][profile].qc
				);
			}

			/* nights and days */
			fprintf(f, ",%g,%g\n", dataset->rows_aggr[j+row].nights_count, dataset->rows_aggr[j+row].days_count);
		}
		j += 12;
	}

	/* close file */
	fclose(f);

	/* alloc memory for huge buffer */
	huge_buffer = malloc(INFO_BUFFER_SIZE*sizeof*huge_buffer);
	if ( !huge_buffer ) {
		puts(err_out_of_memory);
		return 0;
	}
	huge_buffer[0] = '\0';

	/* save stat */
	sprintf(buffer, output_stat_file, output_files_path, dataset->site, "mm");
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create info file!");
		free(huge_buffer);
		return 0;
	}
	for ( i = 0; i < dataset->ts_count; i++ ) {
		sprintf(buffer, info_ts_dd_ww_mm_yy, dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	for ( i = 0; i < dataset->swc_count; i++ ) {
		sprintf(buffer, info_swc_dd_ww_mm_yy, dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	strcat(huge_buffer, info_nights_days_ww_mm);
	strcat(huge_buffer, "\n");
	fprintf(f, info_mm, huge_buffer);
	fputs(dataset->stat, f);
	fclose(f);

	/* free memory */
	free(huge_buffer);

	/* ok */
	return 1;
}

/* */
static int save_dataset_yy(const DATASET *const dataset) {
	int i;
	int year;
	int profile;
	char buffer[BUFFER_SIZE];
	char *huge_buffer;
	FILE *f;

	/* create output file */
	sprintf(buffer, output_file_yy, output_files_path, dataset->site);
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create output file!");
		return 0;
	}

	/* write header */
	fprintf(f, output_header_yy, TIMESTAMP_STRING);
	for ( profile = 0; profile < dataset->ts_count; profile++ ) {
		fprintf(f, ",TS_%d_f,TS_%d_fqc", dataset->ts_profiles[profile], dataset->ts_profiles[profile]);
	}
	for ( profile = 0; profile < dataset->swc_count; profile++ ) {
		fprintf(f, ",SWC_%d_f,SWC_%d_fqc", dataset->swc_profiles[profile], dataset->swc_profiles[profile]);
	}
	fputs("\n", f);
	
	/* write results */
	for ( i = 0; i < dataset->years_count; i++ ) {
		year = dataset->years[i].year;
		/* write values */
		fprintf(f, output_format_yy,
									year,
									dataset->rows_aggr[i].value[TA_FILLED],
									dataset->rows_aggr[i].value[TA_QC],
									dataset->rows_aggr[i].value[TA_F_NIGHT],
									dataset->rows_aggr[i].value[TA_F_NIGHT_STD],
									dataset->rows_aggr[i].value[TA_F_NIGHT_QC],
									dataset->rows_aggr[i].value[TA_F_DAY],
									dataset->rows_aggr[i].value[TA_F_DAY_STD],
									dataset->rows_aggr[i].value[TA_F_DAY_QC],
									dataset->rows_aggr[i].value[TA_ERA],
									dataset->rows_aggr[i].value[TA_ERA_NIGHT],
									dataset->rows_aggr[i].value[TA_ERA_NIGHT_STD],
									dataset->rows_aggr[i].value[TA_ERA_DAY],
									dataset->rows_aggr[i].value[TA_ERA_DAY_STD],
									dataset->rows_aggr[i].value[TA_M],
									dataset->rows_aggr[i].value[TA_M_QC],
									dataset->rows_aggr[i].value[TA_M_NIGHT],
									dataset->rows_aggr[i].value[TA_M_NIGHT_STD],
									dataset->rows_aggr[i].value[TA_M_NIGHT_QC],
									dataset->rows_aggr[i].value[TA_M_DAY],
									dataset->rows_aggr[i].value[TA_M_DAY_STD],
									dataset->rows_aggr[i].value[TA_M_DAY_QC],

									dataset->rows_aggr[i].value[SW_IN_FILLED],
									dataset->rows_aggr[i].value[SW_IN_QC],
									dataset->rows_aggr[i].value[SW_IN_ERA],
									dataset->rows_aggr[i].value[SW_IN_M],
									dataset->rows_aggr[i].value[SW_IN_M_QC],

									dataset->rows_aggr[i].value[LW_IN_FILLED],
									dataset->rows_aggr[i].value[LW_IN_QC],
									dataset->rows_aggr[i].value[LW_IN_ERA],
									dataset->rows_aggr[i].value[LW_IN_M],
									dataset->rows_aggr[i].value[LW_IN_M_QC],
									dataset->rows_aggr[i].value[LW_IN_CALC],
									dataset->rows_aggr[i].value[LW_IN_CALC_QC],
									dataset->rows_aggr[i].value[LW_IN_CALC_ERA],
									dataset->rows_aggr[i].value[LW_IN_CALC_M],
									dataset->rows_aggr[i].value[LW_IN_CALC_M_QC],
									
									dataset->rows_aggr[i].value[VPD_FILLED],
									dataset->rows_aggr[i].value[VPD_QC],
									dataset->rows_aggr[i].value[VPD_ERA],
									dataset->rows_aggr[i].value[VPD_M],
									dataset->rows_aggr[i].value[VPD_M_QC],

									dataset->rows_aggr[i].value[PA_ERA],
									dataset->rows_aggr[i].value[PA_M],
									dataset->rows_aggr[i].value[PA_M_QC],

									dataset->rows_aggr[i].value[PRECIP_ERA],
									dataset->rows_aggr[i].value[PRECIP_M],
									dataset->rows_aggr[i].value[PRECIP_M_QC],

									dataset->rows_aggr[i].value[WS_ERA],
									dataset->rows_aggr[i].value[WS_M],
									dataset->rows_aggr[i].value[WS_M_QC],

									dataset->rows_aggr[i].value[CO2_FILLED],
									dataset->rows_aggr[i].value[CO2_QC]
		);

		/* TS */
		for ( profile = 0; profile < dataset->ts_count; profile++ ) {
			fprintf(f, output_format_profile,	dataset->tss_aggr[i][profile].filled,
												dataset->tss_aggr[i][profile].qc
			);
		}

		/* SWC */
		for ( profile = 0; profile < dataset->swc_count; profile++ ) {
			fprintf(f, output_format_profile,	dataset->swcs_aggr[i][profile].filled,
												dataset->swcs_aggr[i][profile].qc
			);
		}

		fputs("\n", f);
	}

	/* close file */
	fclose(f);

	/* alloc memory for huge buffer */
	huge_buffer = malloc(INFO_BUFFER_SIZE*sizeof*huge_buffer);
	if ( !huge_buffer ) {
		puts(err_out_of_memory);
		return 0;
	}
	huge_buffer[0] = '\0';

	/* save stat */
	sprintf(buffer, output_stat_file, output_files_path, dataset->site, "yy");
	f = fopen(buffer, "w");
	if ( !f ) {
		puts("unable to create info file!");
		free(huge_buffer);
		return 0;
	}
	for ( i = 0; i < dataset->ts_count; i++ ) {
		sprintf(buffer, info_ts_dd_ww_mm_yy, dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i], dataset->ts_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	for ( i = 0; i < dataset->swc_count; i++ ) {
		sprintf(buffer, info_swc_dd_ww_mm_yy, dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i], dataset->swc_profiles[i]);
		strcat(huge_buffer, buffer);
	}
	strcat(huge_buffer, "\n");
	fprintf(f, info_yy, huge_buffer);
	fputs(dataset->stat, f);
	fclose(f);

	/* free memory */
	free(huge_buffer);

	/* ok */
	return 1;
}

/* */
static void free_dataset(DATASET *dataset) {
	int i;

	if ( dataset ) {

		/* free Tss */
		if ( dataset->ts_count ) {
			/*
				we do not use dataset->rows_aggr_count
				but dataset->years_count * 52 because
				dataset->rows_aggr_count change during computing and 
				number of allocated row is dataset->years_count * 52
				please see row 4076 of this source
			*/
			for ( i = 0; i < dataset->years_count * 52; i++ ) {
				free(dataset->tss_aggr[i]);
			}
			free(dataset->tss_aggr);
			dataset->tss_aggr = NULL;

			for ( i = 0; i < dataset->rows_daily_count; i++ ) {
				free(dataset->tss_daily[i]);
			}
			free(dataset->tss_daily);
			dataset->tss_daily = NULL;
			for ( i = 0; i < dataset->rows_count; i++ ) {
				free(dataset->tss[i]);
			}
			free(dataset->tss);
			dataset->tss = NULL;
			free(dataset->ts_profiles);
			dataset->ts_profiles = NULL;
			dataset->ts_count = 0;
		}

		/* free SWCs */
		if ( dataset->swc_count ) {
			for ( i = 0; i < dataset->years_count * 52; i++ ) {
				free(dataset->swcs_aggr[i]);
			}
			free(dataset->swcs_aggr);
			dataset->swcs_aggr = NULL;
			for ( i = 0; i < dataset->rows_daily_count; i++ ) {
				free(dataset->swcs_daily[i]);
			}
			free(dataset->swcs_daily);
			dataset->swcs_daily = NULL;
			for ( i = 0; i < dataset->rows_count; i++ ) {
				free(dataset->swcs[i]);
			}
			free(dataset->swcs);
			dataset->swcs = NULL;
			free(dataset->swc_profiles);
			dataset->swc_profiles = NULL;
			dataset->swc_count = 0;
		}
		free(dataset->time_zones);
		free(dataset->years);
		free(dataset->stat);
		free(dataset->rows_aggr);
		free(dataset->rows_daily);
		free(dataset->rows);
		dataset->years = NULL;
		dataset->stat = NULL;
		dataset->rows_aggr = NULL;
		dataset->rows_daily = NULL;
		dataset->rows = NULL;
	}
}

/* */
void free_datasets(DATASET *datasets, const int datasets_count) {
	int i;

	for ( i = 0; i < datasets_count; i++ ) {
		free_dataset(&datasets[i]);
	}
	free(datasets);
}

/* */
DATASET *get_datasets(int *const datasets_count) {
	int i;
	int y;
	int gap;
	int year;
	int error;
	int assigned;
	int type;
	int file;
	int files_temp_count;
	int files_count;
	YEAR *years_no_leak;
	char site[SITE_LEN];
	char year_c[YEAR_LEN];
	char buffer[BUFFER_SIZE];
	FILE *f;
	FILES *files_temp;
	FILE_N_T *files;
	FILE_N_T *files_no_leak;
	DATASET *datasets;
	DATASET *datasets_no_leak;
	DD *details;

	/* check parameters */
	assert(datasets_count);

	/* reset */
	datasets = NULL;
	*datasets_count = 0;
	files = NULL;
	files_count = 0;

	/* scan path */
	files_temp = get_files(qc_auto_files_path, "*.csv", &files_temp_count, &error);
	if ( error ) {
		return NULL;
	} else if ( !files_temp_count ) {
		puts(err_no_meteo_files_found);
		return NULL;
	}

	/* scan path again! */
	i = files_temp_count;
	files_temp = get_files_again(era_files_path, "*.csv", &files_temp, &files_temp_count, &error);
	if ( error ) {
		free_files(files_temp, files_temp_count);
		return NULL;
	}

	/* loop on each files found */
	for ( file = 0; file < files_temp_count; file++ ) {
		/* check filename */
		if ( is_valid_era_filename(files_temp[file].list[0].name) ) {
			type = ERA_FILES;
		} else if ( is_valid_met_filename(files_temp[file].list[0].name) ) {
			type = MET_FILES;
		} else {
			continue;
		}

		files_no_leak = realloc(files, ++files_count*sizeof*files_no_leak);
		if ( !files_no_leak ) {
			puts(err_out_of_memory);
			free_files(files_temp, files_temp_count);
			free(files);
			return 0;
		}
		files = files_no_leak;
		strcpy(files[files_count-1].name, files_temp[file].list[0].name);
		files[files_count-1].type = type;
	}

	/* free memory */
	free_files(files_temp, files_temp_count);

	/* check for non files found */
	if ( !files_count ) {
		puts(err_no_files_found);
		return NULL;
	}
	
	/* loop on each files found */
	for ( file = 0; file < files_count; file++ ) {
		type = files[file].type;
		if ( ERA_FILES == type ) {
			/* get site */
			strncpy(site, files[file].name, SITE_LEN-1);
			/* get year (string) */
			strncpy(year_c, files[file].name + SITE_LEN, YEAR_LEN - 1);
		} else { /* MET_FILES */
			/* open file */
			sprintf(buffer, "%s%s", qc_auto_files_path, files[file].name);
			f = fopen(buffer, "r");
			if ( !f ) {
				printf("unable to open file: %s\n", files[file].name);
				free(files);
				return NULL;
			}

			/* parse details */
			details = parse_dd(f);
			if ( !details ) {
				fclose(f);
				free(files);
				return NULL;
			}

			/* get site */
			strncpy(site, details->site, SITE_LEN-1);
			/* get year (string) */
			sprintf(year_c, "%d", details->year);

			/* free */
			free_dd(details);
			details = NULL;
					
			/* close file */
			fclose(f);
		}

		site[SITE_LEN - 1] = '\0';
		year_c[YEAR_LEN-1] = '\0';

		/* convert year string to int */
		year = convert_string_to_int(year_c, &error);
		if ( error ) {
			printf("unable to convert year for %s\n\n", files[file].name);
			free_datasets(datasets, *datasets_count);
			free(files);
			return NULL;
		}
		
		/* check if site is already assigned */
		assigned = 0;
		for ( i = 0; i < *datasets_count; i++ ) {
			if ( ! string_compare_i(datasets[i].site, site) ) {
				assigned = 1;
				break;
			}
		}

		/* not assigned ? add site! */
		if ( !assigned ) {
			datasets_no_leak = realloc(datasets, (*datasets_count+1)*sizeof*datasets_no_leak);
			if ( !datasets_no_leak ) {
				puts(err_out_of_memory);
				free_datasets(datasets, *datasets_count);
				free(files);
				return NULL;

			}
			/* */
			datasets = datasets_no_leak;
			datasets[*datasets_count].rows = NULL;
			datasets[*datasets_count].rows_count = 0;
			datasets[*datasets_count].rows_daily = NULL;
			datasets[*datasets_count].rows_daily_count = 0;
			datasets[*datasets_count].rows_aggr = NULL;
			datasets[*datasets_count].rows_aggr_count = 0;		
			strcpy(datasets[*datasets_count].site, site);
			datasets[*datasets_count].years = NULL;
			datasets[*datasets_count].years_count = 0;
			datasets[*datasets_count].time_zones = NULL;
			datasets[*datasets_count].time_zones_count = 0;
			datasets[*datasets_count].stat = NULL;
			datasets[*datasets_count].tss = NULL;
			datasets[*datasets_count].swcs = NULL;
			datasets[*datasets_count].ts_profiles = NULL;
			datasets[*datasets_count].swc_profiles = NULL;
			datasets[*datasets_count].ts_count = 0;
			datasets[*datasets_count].swc_count = 0;

			/* do the trick ;) */
			i = *datasets_count;

			/* inc counter */
			++*datasets_count;
		}

		/* check if year is already assigned...? */
		assigned = 0;
		for ( y = 0; y < datasets[i].years_count; y++ ) {
			if ( year == datasets[i].years[y].year ) {
				datasets[i].years[y].exist[type] = 1;
				assigned = 1;
				break;
			}
		}

		if ( !assigned ) {
			/* add year */
			years_no_leak = realloc(datasets[i].years, (datasets[i].years_count+1)*sizeof*years_no_leak);
			if ( !years_no_leak ) {
				puts(err_out_of_memory);
				free_datasets(datasets, *datasets_count);
				free(files);
				return NULL;
			}

			/* assign year and compute rows count */
			datasets[i].years = years_no_leak;
			datasets[i].years[datasets[i].years_count].year = year;
			datasets[i].years[datasets[i].years_count].exist[ERA_FILES] = 0;
			datasets[i].years[datasets[i].years_count].exist[MET_FILES] = 0;
			datasets[i].years[datasets[i].years_count].exist[type] = 1;
			datasets[i].rows_count += IS_LEAP_YEAR(year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			/* inc counter */
			++datasets[i].years_count;
		}
	}

	/* free memory */
	free(files);
	files = NULL;

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
					years_no_leak = realloc(datasets[i].years, (datasets[i].years_count+1)*sizeof*years_no_leak);
					if ( !years_no_leak ) {
						puts(err_out_of_memory);
						free_datasets(datasets, *datasets_count);
						return NULL;
					}

					datasets[i].years = years_no_leak;
					datasets[i].years[datasets[i].years_count].year = datasets[i].years[y].year+1;
					datasets[i].years[datasets[i].years_count].exist[ERA_FILES] = 0;
					datasets[i].years[datasets[i].years_count].exist[MET_FILES] = 0;
					datasets[i].rows_count += IS_LEAP_YEAR(datasets[i].years[y].year+1) ? LEAP_YEAR_ROWS : YEAR_ROWS;
					++datasets[i].years_count;
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

/* */
int check_met_files(DATASET *const dataset) {
	int count;
	int year;
	char buffer[BUFFER_SIZE];

	count = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		sprintf(buffer, "%s%s_qca_meteo_%d.csv", qc_auto_files_path, dataset->site, dataset->years[year].year);
		if ( file_exists(buffer) ) {
			++count;
		}
	}
	return count;
}

/* */
int compute_datasets(DATASET *const datasets, const int datasets_count) {
	int i;
	int j;
	int dataset;
	int start_row;
	int end_row;
	int not_gf_count;
	int rows_per_day;
	int profile;
	DATASET *current_dataset;
	GF_ROW *gf_rows;

	/* loop on each dataset */
	for ( dataset = 0; dataset < datasets_count; dataset++ ) {
		/* set pointers */
		current_dataset = &datasets[dataset];

		/* msg */
		printf("processing %s, %d years...\n",	current_dataset->site,
												current_dataset->years_count
		);

		/* check if has any met files */
		if ( !check_met_files(current_dataset) ) {
			puts("MET files not found.");
			continue;
		}

		/* fill dataset details */
		if ( !get_dataset_details(current_dataset) ) {
			return 0;
		}

		if ( current_dataset->hourly ) {
			current_dataset->rows_count /= 2;
		}

		/* alloc memory for rows */
		current_dataset->rows = malloc(current_dataset->rows_count*sizeof*current_dataset->rows);
		if ( !current_dataset->rows ) {
			puts(err_out_of_memory);
			free_datasets(datasets, datasets_count);
			return 0;
		}

		/* alloc memory for daily */
		current_dataset->rows_daily_count = current_dataset->rows_count / (current_dataset->hourly ? 24 : 48);
		current_dataset->rows_daily = malloc(current_dataset->rows_daily_count*sizeof*current_dataset->rows_daily);
		if ( !current_dataset->rows_daily ) {
			puts(err_out_of_memory);
			free_datasets(datasets, datasets_count);
			return 0;
		}

		/* alloc memory for aggr */
		current_dataset->rows_aggr_count = current_dataset->years_count * 52;
		current_dataset->rows_aggr = malloc(current_dataset->rows_aggr_count*sizeof*current_dataset->rows_aggr);
		if ( !current_dataset->rows_aggr ) {
			puts(err_out_of_memory);
			free_datasets(datasets, datasets_count);
			return 0;
		}

		/* reset values */
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			for ( j = 0; j < VALUES; j++ ) {
				current_dataset->rows[i].value[j] = INVALID_VALUE;
			}
			/* not used, but we cleared at 0 */
			current_dataset->rows[i].nights_count = 0;
			current_dataset->rows[i].days_count = 0;
		}

		for ( i = 0; i < current_dataset->rows_daily_count; i++ ) {
			for ( j = 0; j < VALUES; j++ ) {
				current_dataset->rows_daily[i].value[j] = INVALID_VALUE;
			}
			current_dataset->rows_daily[i].nights_count = 0;
			current_dataset->rows_daily[i].days_count = 0;
		}

		for ( i = 0; i < current_dataset->rows_aggr_count; i++ ) {
			for ( j = 0; j < VALUES; j++ ) {
				current_dataset->rows_aggr[i].value[j] = INVALID_VALUE;
			}
			current_dataset->rows_aggr[i].nights_count = 0;
			current_dataset->rows_aggr[i].days_count = 0;
		}
		
		/* get era values */
		if ( !import_era_values(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}

		/* get stat file */
		if ( ! import_stat(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}

		/* import meteo values */
		if ( !import_meteo_values(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}

		/* compute rows per day */
		rows_per_day = 48;
		if ( current_dataset->hourly ) {
			rows_per_day /= 2;
		}
		
		/* gapfilling TA */
		printf("- gapfilling TA...");

		/* compute start and end row */
		start_row = -1;
		end_row = -1;
 		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[TA_MET]) ) {
				start_row = i;
				break;
			}
		}
		if ( -1 == start_row ) {
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[TA_FILLED] = INVALID_VALUE;
				current_dataset->rows[i].value[TA_QC] = INVALID_VALUE;
			}
			puts("ok but is missing!");
		} else {
			for ( i = current_dataset->rows_count - 1; i >= 0 ; i-- ) {
				if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[TA_MET]) ) {
					end_row = i;
					break;
				}
			}
			if ( start_row == end_row ) {
				puts("only one valid value for TA!");
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			/* adjust bounds */
			start_row -= (DAYS_FOR_GF*rows_per_day);
			if ( start_row < 0 ) {
				start_row = 0;
			}

			end_row += (DAYS_FOR_GF*rows_per_day);
			if ( end_row > current_dataset->rows_count ) {
				end_row = current_dataset->rows_count;
			}
		
			gf_rows = gf_mds(	current_dataset->rows->value,
								sizeof(ROW),
								current_dataset->rows_count,
								VALUES,
								current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
								GF_DRIVER_1_TOLERANCE_MIN,
								GF_DRIVER_1_TOLERANCE_MAX,
								GF_DRIVER_2A_TOLERANCE_MIN,
								GF_DRIVER_2A_TOLERANCE_MAX,
								GF_DRIVER_2B_TOLERANCE_MIN,
								GF_DRIVER_2B_TOLERANCE_MAX,
								TA_MET,
								SW_IN_MET,
								TA_MET,
								VPD_MET,
								-1,
								-1,
								-1,
								INVALID_VALUE,
								INVALID_VALUE,
								INVALID_VALUE,
								GF_ROWS_MIN,
								0,
								start_row,
								end_row,
								&not_gf_count,
								0,
								0,
								0,
								NULL,
								0

			);

			if ( !gf_rows ) {
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			if ( !not_gf_count ) {
				puts("ok");
			} else {
				printf("ok (%d values unfilled)\n", not_gf_count); 
			}

			/* copy gf values and qc */
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[TA_FILLED] = current_dataset->rows[i].value[TA_MET];
				current_dataset->rows[i].value[TA_QC] = INVALID_VALUE;
				if ( (i >= start_row) && (i <= end_row) ) {
					current_dataset->rows[i].value[TA_FILLED] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? current_dataset->rows[i].value[TA_MET] : gf_rows[i].filled;
					current_dataset->rows[i].value[TA_QC] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality;
				}
			}

			/* free memory */
			free(gf_rows);
			gf_rows = NULL;
		}

		/* gapfilling SW_IN */
		printf("- gapfilling SW_IN...");

		/* compute start and end row */
		start_row = -1;
		end_row = -1;
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[SW_IN_MET]) ) {
				start_row = i;
				break;
			}
		}
		if ( -1 == start_row ) {
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[SW_IN_FILLED] = INVALID_VALUE;
				current_dataset->rows[i].value[SW_IN_QC] = INVALID_VALUE;
			}
			puts("ok but is missing!");
		} else {
			for ( i = current_dataset->rows_count - 1; i >= 0 ; i-- ) {
				if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[SW_IN_MET]) ) {
					end_row = i;
					break;
				}
			}
			if ( start_row == end_row ) {
				puts("only one valid value for SW_IN!");
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			/* adjust bounds */
			start_row -= (DAYS_FOR_GF*rows_per_day);
			if ( start_row < 0 ) {
				start_row = 0;
			}

			end_row += (DAYS_FOR_GF*rows_per_day);
			if ( end_row > current_dataset->rows_count ) {
				end_row = current_dataset->rows_count;
			}
		
			gf_rows = gf_mds(	current_dataset->rows->value,
								sizeof(ROW),
								current_dataset->rows_count,
								VALUES,
								current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
								GF_DRIVER_1_TOLERANCE_MIN,
								GF_DRIVER_1_TOLERANCE_MAX,
								GF_DRIVER_2A_TOLERANCE_MIN,
								GF_DRIVER_2A_TOLERANCE_MAX,
								GF_DRIVER_2B_TOLERANCE_MIN,
								GF_DRIVER_2B_TOLERANCE_MAX,
								SW_IN_MET,
								SW_IN_MET,
								TA_MET,
								VPD_MET,
								-1,
								-1,
								-1,
								INVALID_VALUE,
								INVALID_VALUE,
								INVALID_VALUE,
								GF_ROWS_MIN,
								0,
								start_row,
								end_row,
								&not_gf_count,
								0,
								0,
								0,
								NULL,
								0
			);

			if ( !gf_rows ) {
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			if ( !not_gf_count ) {
				puts("ok");
			} else {
				printf("ok (%d values unfilled)\n", not_gf_count); 
			}

			/* copy gf values and qc */
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[SW_IN_FILLED] = current_dataset->rows[i].value[SW_IN_MET];
				current_dataset->rows[i].value[SW_IN_QC] = INVALID_VALUE;
				if ( (i >= start_row) && (i <= end_row) ) {
					current_dataset->rows[i].value[SW_IN_FILLED] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? current_dataset->rows[i].value[SW_IN_MET] : gf_rows[i].filled;
					current_dataset->rows[i].value[SW_IN_QC] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality;
				}
			}

			/* free memory */
			free(gf_rows);
			gf_rows = NULL;
		}

		/* gapfilling LW_IN */
		printf("- gapfilling LW_IN...");

		/* compute start and end row */
		start_row = -1;
		end_row = -1;
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[LW_IN_MET]) ) {
				start_row = i;
				break;
			}
		}
		if ( -1 == start_row ) {
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[LW_IN_FILLED] = INVALID_VALUE;
				current_dataset->rows[i].value[LW_IN_QC] = INVALID_VALUE;				
			}
			puts("ok but is missing!");
		} else  {
			for ( i = current_dataset->rows_count - 1; i >= 0 ; i-- ) {
				if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[LW_IN_MET]) ) {
					end_row = i;
					break;
				}
			}
			if ( start_row == end_row ) {
				puts("only one valid value for LW_IN!");
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			/* adjust bounds */
			start_row -= (DAYS_FOR_GF*rows_per_day);
			if ( start_row < 0 ) {
				start_row = 0;
			}

			end_row += (DAYS_FOR_GF*rows_per_day);
			if ( end_row > current_dataset->rows_count ) {
				end_row = current_dataset->rows_count;
			}
		
			gf_rows = gf_mds(	current_dataset->rows->value,
								sizeof(ROW),
								current_dataset->rows_count,
								VALUES,
								current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
								GF_DRIVER_1_TOLERANCE_MIN,
								GF_DRIVER_1_TOLERANCE_MAX,
								GF_DRIVER_2A_TOLERANCE_MIN,
								GF_DRIVER_2A_TOLERANCE_MAX,
								GF_DRIVER_2B_TOLERANCE_MIN,
								GF_DRIVER_2B_TOLERANCE_MAX,
								LW_IN_MET,
								SW_IN_MET,
								TA_MET,
								VPD_MET,
								-1,
								-1,
								-1,
								INVALID_VALUE,
								INVALID_VALUE,
								INVALID_VALUE,
								GF_ROWS_MIN,
								0,
								start_row,
								end_row,
								&not_gf_count,
								0,
								0,
								0,
								NULL,
								0
			);

			if ( !gf_rows ) {
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			if ( !not_gf_count ) {
				puts("ok");
			} else {
				printf("ok (%d values unfilled)\n", not_gf_count); 
			}

			/* copy gf values and qc */
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[LW_IN_FILLED] = current_dataset->rows[i].value[LW_IN_MET];
				current_dataset->rows[i].value[LW_IN_QC] = INVALID_VALUE;
				if ( (i >= start_row) && (i <= end_row) ) {
					current_dataset->rows[i].value[LW_IN_FILLED] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? current_dataset->rows[i].value[LW_IN_MET] : gf_rows[i].filled;
					current_dataset->rows[i].value[LW_IN_QC] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality;
				}
			}

			/* free memory */
			free(gf_rows);
			gf_rows = NULL;
		}

		/* gapfilling VPD */
		printf("- gapfilling VPD...");

		/* compute start and end row */
		start_row = -1;
		end_row = -1;
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[VPD_MET]) ) {
				start_row = i;
				break;
			}
		}
		if ( -1 == start_row ) {
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[VPD_FILLED] = INVALID_VALUE;
				current_dataset->rows[i].value[VPD_QC] = INVALID_VALUE;
			}
			puts("ok but is missing!");
		} else {
			for ( i = current_dataset->rows_count - 1; i >= 0 ; i-- ) {
				if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[VPD_MET]) ) {
					end_row = i;
					break;
				}
			}
			if ( start_row == end_row ) {
				puts("only one valid value for VPD!");
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			/* adjust bounds */
			start_row -= (DAYS_FOR_GF*rows_per_day);
			if ( start_row < 0 ) {
				start_row = 0;
			}

			end_row += (DAYS_FOR_GF*rows_per_day);
			if ( end_row > current_dataset->rows_count ) {
				end_row = current_dataset->rows_count;
			}
		
			gf_rows = gf_mds(	current_dataset->rows->value,
								sizeof(ROW),
								current_dataset->rows_count,
								VALUES,
								current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
								GF_DRIVER_1_TOLERANCE_MIN,
								GF_DRIVER_1_TOLERANCE_MAX,
								GF_DRIVER_2A_TOLERANCE_MIN,
								GF_DRIVER_2A_TOLERANCE_MAX,
								GF_DRIVER_2B_TOLERANCE_MIN,
								GF_DRIVER_2B_TOLERANCE_MAX,
								VPD_MET,
								SW_IN_MET,
								TA_MET,
								VPD_MET,
								-1,
								-1,
								-1,
								INVALID_VALUE,
								INVALID_VALUE,
								INVALID_VALUE,
								GF_ROWS_MIN,
								0,
								start_row,
								end_row,
								&not_gf_count,
								0,
								0,
								0,
								NULL,
								0
			);

			if ( !gf_rows ) {
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			if ( !not_gf_count ) {
				puts("ok");
			} else {
				printf("ok (%d values unfilled)\n", not_gf_count); 
			}

			/* copy gf values and qc */
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[VPD_FILLED] = current_dataset->rows[i].value[VPD_MET];
				current_dataset->rows[i].value[VPD_QC] = INVALID_VALUE;
				if ( (i >= start_row) && (i <= end_row) ) {
					current_dataset->rows[i].value[VPD_FILLED] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? current_dataset->rows[i].value[VPD_MET] : gf_rows[i].filled;
					current_dataset->rows[i].value[VPD_QC] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality;
				}
			}

			/* free memory */
			free(gf_rows);
			gf_rows = NULL;
		}

		/* gapfilling CO2 */
		printf("- gapfilling CO2...");

		/* compute start and end row */
		start_row = -1;
		end_row = -1;
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[CO2_MET]) ) {
				start_row = i;
				break;
			}
		}
		if ( -1 == start_row ) {
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[CO2_FILLED] = INVALID_VALUE;
				current_dataset->rows[i].value[CO2_QC] = INVALID_VALUE;
			}
			puts("ok but is missing!");
		} else {
			for ( i = current_dataset->rows_count - 1; i >= 0 ; i-- ) {
				if ( !IS_INVALID_VALUE(current_dataset->rows[i].value[CO2_MET]) ) {
					end_row = i;
					break;
				}
			}
			if ( start_row == end_row ) {
				puts("only one valid value for CO2!");
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			/* adjust bounds */
			start_row -= (DAYS_FOR_GF*rows_per_day);
			if ( start_row < 0 ) {
				start_row = 0;
			}

			end_row += (DAYS_FOR_GF*rows_per_day);
			if ( end_row > current_dataset->rows_count ) {
				end_row = current_dataset->rows_count;
			}
		
			gf_rows = gf_mds(	current_dataset->rows->value,
								sizeof(ROW),
								current_dataset->rows_count,
								VALUES,
								current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
								GF_DRIVER_1_TOLERANCE_MIN,
								GF_DRIVER_1_TOLERANCE_MAX,
								GF_DRIVER_2A_TOLERANCE_MIN,
								GF_DRIVER_2A_TOLERANCE_MAX,
								GF_DRIVER_2B_TOLERANCE_MIN,
								GF_DRIVER_2B_TOLERANCE_MAX,
								CO2_MET,
								SW_IN_MET,
								TA_MET,
								VPD_MET,
								-1,
								-1,
								-1,
								INVALID_VALUE,
								INVALID_VALUE,
								INVALID_VALUE,
								GF_ROWS_MIN,
								0,
								start_row,
								end_row,
								&not_gf_count,
								0,
								0,
								0,
								NULL,
								0
			);

			if ( !gf_rows ) {
				/* free memory */
				free_dataset(current_dataset);
				continue;
			}

			if ( !not_gf_count ) {
				puts("ok");
			} else {
				printf("ok (%d values unfilled)\n", not_gf_count); 
			}

			/* copy gf values and qc */
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				current_dataset->rows[i].value[CO2_FILLED] = current_dataset->rows[i].value[CO2_MET];
				current_dataset->rows[i].value[CO2_QC] = INVALID_VALUE;
				if ( (i >= start_row) && (i <= end_row) ) {
					current_dataset->rows[i].value[CO2_FILLED] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? current_dataset->rows[i].value[CO2_MET] : gf_rows[i].filled;
					current_dataset->rows[i].value[CO2_QC] = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality;
				}
			}

			/* free memory */
			free(gf_rows);
			gf_rows = NULL;
		}

		/* Ts filling */
		for ( profile = 0; profile < current_dataset->ts_count; profile++ ) {
			printf("- gapfilling TS_%d...", current_dataset->ts_profiles[profile]);

			/* compute start and end row */
			start_row = -1;
			end_row = -1;
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				if ( !IS_INVALID_VALUE(current_dataset->tss[i][profile].value) ) {
					start_row = i;
					break;
				}
			}
			if ( -1 == start_row ) {
				puts("ok but is missing!");
			} else {
				for ( i = current_dataset->rows_count - 1; i >= 0 ; i-- ) {
					if ( !IS_INVALID_VALUE(current_dataset->tss[i][profile].value) ) {
						end_row = i;
						break;
					}
				}
				if ( start_row == end_row ) {
					printf("only one valid value for TS_%d\n!", current_dataset->ts_profiles[profile]);
					/* free memory */
					free_dataset(current_dataset);
					continue;
				}

				/* adjust bounds */
				start_row -= (DAYS_FOR_GF*rows_per_day);
				if ( start_row < 0 ) {
					start_row = 0;
				}

				end_row += (DAYS_FOR_GF*rows_per_day);
				if ( end_row > current_dataset->rows_count ) {
					end_row = current_dataset->rows_count;
				}

				/* copy values */
				for ( i = 0; i < current_dataset->rows_count; i++) {
					current_dataset->rows[i].value[TEMP] = current_dataset->tss[i][profile].value;
				}
			
				/* do gf */
				gf_rows = gf_mds(	current_dataset->rows->value,
									sizeof(ROW),
									current_dataset->rows_count,
									VALUES,
									current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
									GF_DRIVER_1_TOLERANCE_MIN,
									GF_DRIVER_1_TOLERANCE_MAX,
									GF_DRIVER_2A_TOLERANCE_MIN,
									GF_DRIVER_2A_TOLERANCE_MAX,
									GF_DRIVER_2B_TOLERANCE_MIN,
									GF_DRIVER_2B_TOLERANCE_MAX,
									TEMP,
									SW_IN_MET,
									TA_MET,
									VPD_MET,
									-1,
									-1,
									-1,
									INVALID_VALUE,
									INVALID_VALUE,
									INVALID_VALUE,
									GF_ROWS_MIN,
									0,
									start_row,
									end_row,
									&not_gf_count,
									0,
									0,
									0,
									NULL,
									0
				);

				if ( !gf_rows ) {
					/* free memory */
					free_dataset(current_dataset);
					continue;
				}

				if ( !not_gf_count ) {
					puts("ok");
				} else {
					printf("ok (%d values unfilled)\n", not_gf_count); 
				}

				/* copy gf values and qc */
				for ( i = 0; i < current_dataset->rows_count; i++ ) {
					current_dataset->tss[i][profile].filled = current_dataset->tss[i][profile].value;
					current_dataset->tss[i][profile].qc = INVALID_VALUE;
					if ( (i >= start_row) && (i <= end_row) ) {
						current_dataset->tss[i][profile].filled = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? current_dataset->tss[i][profile].value : gf_rows[i].filled;
						current_dataset->tss[i][profile].qc = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality;
					}
				}

				/* free memory */
				free(gf_rows);
				gf_rows = NULL;
			}
		}

		/* SWC filling */
		for ( profile = 0; profile < current_dataset->swc_count; profile++ ) {
			printf("- gapfilling SWC_%d...", current_dataset->swc_profiles[profile]);

			/* compute start and end row */
			start_row = -1;
			end_row = -1;
			for ( i = 0; i < current_dataset->rows_count; i++ ) {
				if ( !IS_INVALID_VALUE(current_dataset->swcs[i][profile].value) ) {
					start_row = i;
					break;
				}
			}
			if ( -1 == start_row ) {
				puts("ok but is missing!");
			} else {
				for ( i = current_dataset->rows_count - 1; i >= 0 ; i-- ) {
					if ( !IS_INVALID_VALUE(current_dataset->swcs[i][profile].value) ) {
						end_row = i;
						break;
					}
				}
				if ( start_row == end_row ) {
					printf("only one valid value for TS_%d\n!", current_dataset->swc_profiles[profile]);
					/* free memory */
					free_dataset(current_dataset);
					continue;
				}

				/* adjust bounds */
				start_row -= (DAYS_FOR_GF*rows_per_day);
				if ( start_row < 0 ) {
					start_row = 0;
				}

				end_row += (DAYS_FOR_GF*rows_per_day);
				if ( end_row > current_dataset->rows_count ) {
					end_row = current_dataset->rows_count;
				}

				/* copy values */
				for ( i = 0; i < current_dataset->rows_count; i++) {
					current_dataset->rows[i].value[TEMP] = current_dataset->swcs[i][profile].value;
				}
			
				/* do gf */
				gf_rows = gf_mds(	current_dataset->rows->value,
									sizeof(ROW),
									current_dataset->rows_count,
									VALUES,
									current_dataset->hourly ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
									GF_DRIVER_1_TOLERANCE_MIN,
									GF_DRIVER_1_TOLERANCE_MAX,
									GF_DRIVER_2A_TOLERANCE_MIN,
									GF_DRIVER_2A_TOLERANCE_MAX,
									GF_DRIVER_2B_TOLERANCE_MIN,
									GF_DRIVER_2B_TOLERANCE_MAX,
									TEMP,
									SW_IN_MET,
									TA_MET,
									VPD_MET,
									-1,
									-1,
									-1,
									INVALID_VALUE,
									INVALID_VALUE,
									INVALID_VALUE,
									GF_ROWS_MIN,
									0,
									start_row,
									end_row,
									&not_gf_count,
									0,
									0,
									0,
									NULL,
									0

				);

				if ( !gf_rows ) {
					/* free memory */
					free_dataset(current_dataset);
					continue;
				}

				if ( !not_gf_count ) {
					puts("ok");
				} else {
					printf("ok (%d values unfilled)\n", not_gf_count); 
				}

				/* copy gf values and qc */
				for ( i = 0; i < current_dataset->rows_count; i++ ) {
					current_dataset->swcs[i][profile].filled = current_dataset->swcs[i][profile].value;
					current_dataset->swcs[i][profile].qc = INVALID_VALUE;
					if ( (i >= start_row) && (i <= end_row) ) {
						current_dataset->swcs[i][profile].filled = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? current_dataset->swcs[i][profile].value : gf_rows[i].filled;
						current_dataset->swcs[i][profile].qc = IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality;
					}
				}

				/* free memory */
				free(gf_rows);
				gf_rows = NULL;
			}
		}
			
		/* computing m */
		printf("- computing ms and qcs...");
		compute_ms(current_dataset);
		puts("ok");

		/* computing calc */
		printf("- computing calc...");
		compute_calc(current_dataset);
		puts("ok");

		/* computing calc m */
		for ( i = 0; i < current_dataset->rows_count; i++ ) {
			if ( ! IS_INVALID_VALUE(current_dataset->rows[i].value[LW_IN_CALC_QC])
					&& current_dataset->rows[i].value[LW_IN_CALC_QC] < 2 ) {
				current_dataset->rows[i].value[LW_IN_CALC_M] = current_dataset->rows[i].value[LW_IN_CALC];
				current_dataset->rows[i].value[LW_IN_CALC_M_QC] = current_dataset->rows[i].value[LW_IN_CALC_QC];
			} else {
				current_dataset->rows[i].value[LW_IN_CALC_M] = current_dataset->rows[i].value[LW_IN_CALC_ERA];
				current_dataset->rows[i].value[LW_IN_CALC_M_QC] = 2;
			}

			/*
				New option added 20160616 to take into account the possibility that ERA is
				not present in a given year (recent years). In this case the data filled using
				MDS are used for the _M and the QC is set as 3
				if LW_IN_CALC_M is still INVALID_VALUE, LW_IN_CALC and LW_IN_CALC_M_QC are set to 3
			*/
			if ( IS_INVALID_VALUE(current_dataset->rows[i].value[LW_IN_CALC_M]) ) {
				current_dataset->rows[i].value[LW_IN_CALC_M] = current_dataset->rows[i].value[LW_IN_CALC];
				current_dataset->rows[i].value[LW_IN_CALC_M_QC] = 3;
			}
		}

		/* saving hh */
		printf("- saving hh...");
		if ( !save_dataset_hh(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");

		/* */
		printf("- computing daily...");
		if ( !compute_dd(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");

		/* saving dd */
		printf("- saving daily...");
		if ( !save_dataset_dd(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");

		/* */
		printf("- computing weekly...");
		if ( ! compute_ww(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");

		/* saving ww */
		printf("- saving weekly...");
		if ( ! save_dataset_ww(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");
	
		/* */
		printf("- computing monthly...");
		if ( !compute_mm(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");

		/* saving mm */
		printf("- saving monthly..");
		if ( !save_dataset_mm(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");

		/* */
		printf("- computing yearly...");
		if ( !compute_yy(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok");

		/* saving yy */
		printf("- saving yearly..");
		if ( ! save_dataset_yy(current_dataset) ) {
			/* free memory */
			free_dataset(current_dataset);
			continue;
		}
		puts("ok\n");

		/* free memory */
		free_dataset(current_dataset);
	}

	/* free memory */
	free(datasets);

	/* ok */
	return 1;
}
