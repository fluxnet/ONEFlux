/*
	main.c

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
#include "../../../compiler.h"
	
/* constants */
#define PROGRAM_VERSION		"1.0"
const char def_tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1] = {
	"NEE", 
	"SW_IN",
	"TA",
	"VPD",
	TIMESTAMP_STRING,
};

/* static global variables */
static FILES *files;
static int files_count;
static int rows_min = GF_ROWS_MIN;	/* see types.h */

/* global variables */
char *program_path = NULL;	/* required */
char *input_path = NULL;	/* required */
char *output_path = NULL;	/* required */
int hourly_dataset = 0;		/* required */
int *years = NULL;			/* required */
int years_count = 0;		/* required */
DD **details_list = NULL;	/* required */
int has_dtime = 0;			/* required */
int custom_tokens[GF_TOKENS];
PREC swin_tolerance_min = GF_SW_IN_TOLERANCE_MIN;
PREC swin_tolerance_max = GF_SW_IN_TOLERANCE_MAX;
PREC ta_tolerance = GF_TA_TOLERANCE;
PREC vpd_tolerance = GF_VPD_TOLERANCE;

/* strings */
static const char banner[] =	"\ngf_mds "PROGRAM_VERSION"\n"
								"by Alessio Ribeca\n\n"
								"scientific contact: darpap at unitus dot it\n"
								"technical contact: a dot ribeca at unitus dot it\n\n"
								"DIBAF - University of Tuscia, Viterbo, Italy\n"
								"(builded on "__DATE__" at "__TIME__ " with "COMPILER")\n"
								"(use -h parameter for more information)\n";
static const char notes[] = "processed on %s with gf_mds "PROGRAM_VERSION" compiled using "COMPILER" on "__DATE__" at " __TIME__;

/* must have same order of eValues in types.h */
char tokens[GF_TOKENS][GF_TOKEN_LENGTH_MAX+1];
static const char gap_file[] = "%s%smds.csv";
static const char gap_header[] = "TIMESTAMP,%s,FILLED,QC,HAT,SAMPLE,STDDEV,METHOD,QC_HAT,TIMEWINDOW\n";
static const char gap_dtime_header[] = "DTime,%s,FILLED,QC,HAT,SAMPLE,STDDEV,METHOD,QC_HAT,TIMEWINDOW\n";
static const char gap_format[] = "%s,%g,%g,%d,%g,%d,%g,%d,%d,%d\n";
static const char gap_dtime_format[] = "%g,%g,%g,%d,%g,%d,%g,%d,%d,%d\n";

/* messages */
static const char msg_dataset_not_specified[] =
"dataset not specified."
#if defined (_WIN32) || defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
" searching..."
#endif
"\n";
static const char msg_import_dataset[] = "processing: %s%s";
static const char msg_output_path[] = "output path = %s\n\n";
static const char msg_rows_min[] = "rows min = %d\n\n";
static const char msg_tolerances[] =	"%s tolerances = %g, %g\n"
										"%s tolerance = %g\n"
										"%s tolerance = %g\n\n";
static const char msg_ok[] = "ok";
static const char msg_ok_with_gaps_unfilled[] = "ok with %d gaps unfilled.\n";
static const char msg_summary[] = "\n%d file%s founded: %d processed, %d skipped.\n\n";
static const char msg_usage[] =	"This code applies the gapfilling Marginal Distribution Sampling method\n"
								"described in Reichstein et al. 2005 (Global Change Biology).\n\n"
								"Differences respect to the original method are the possibilities to:\n"
								"1) define the name you used to specify the different variables\n"
								"2) process a multi-years dataset\n"
								"3) change the tolerance of the different drivers (see the paper for details)\n\n\n"
								"How to use: gf_mds parameters\n\n"
								"  -input=filename -> file to be processed (optional)\n"
								"    (if not specified all the files in the folder are processed)\n"
								"    use , to separate paths\\files\n"
								"    (e.g. -dataset=ITRoc2003.txt,ITCpz2003.txt will process only these 2 files)\n"
								"    use + to concatenate paths\\files\n"
								"    (e.g. -dataset=ITRo2003.txt+ITRo2004.txt will process the 2 years as one dataset)\n\n"
								"  -output=path where result files are created (optional)\n"
								"    (if not specified the folder with the gf_mds.exe file is used)\n\n"
								"  -hourly -> specify that your file is not halfhourly but hourly\n\n"
								"  -tofill=XXXX -> name of the the variable to be filled as reported in the header of the\n"
								"    input file (max %d chars, default is \"%s\")\n\n"
								"  -sw_in=XXXX -> name of the incoming radiation (W m-2) as reported in the header of the\n"
								"    input file (max %d chars, default is \"%s\")\n\n"
								"  -ta=XXXX -> name of the air temperature (C degree) as reported in the header of the\n"
								"    input file (max %d chars, default is \"%s\")\n\n"
								"  -vpd=XXXX -> name of the vapor pressure deficit (hP) as reported in the header of the\n"
								"    input file (max %d chars, default is \"%s\")\n\n"
								"  -date=XXXX -> name of the date variable as reported in the header of the\n"
								"    input file (max %d chars, default is \"%s\")\n\n"
								"  -sw_int=min,max -> change SW_IN tolerances (default min: %g, default max: %g)\n\n"
								"  -tat=value -> change TA tolerance (default: %g)\n\n"
								"  -vpdt=value -> change VPD tolerance (default: %g)\n\n"
								"  -dtime -> timestamp reported as decimal day of the year\n"
								"    (e.g. 1.02083 for the first half hour of the year) using as variable name DTIME\n"
								"    (can be changed using the -date parameter). Default is OFF and ISODATE is expected\n\n"
								"  -rows_min=value -> set rows min (default: %d)\n\n"
								"  -h -> show this help\n\n"
								"Others driver variables can be used instead of Air temperature and VPD,\nspecifying the name and the new tolerances.\n\n"
								"For example to use Soil Water Content (name swc, expressed as %% 0-100 and with\na tolerance of 5%) instead of "
								"VPD you have to specify:\n\ngf_mds -vpd=swc -vpdt=5\n";
/* errors messages */
extern const char err_out_of_memory[];
const char err_unable_open_file[] = "unable to open file.";
const char err_empty_file[] = "empty file ?";
const char err_not_founded[] = "not founded.";
static const char err_unable_get_current_directory[] = "unable to retrieve current directory.\n";
static const char err_unable_to_register_atexit[] = "unable to register clean-up routine.\n";
static const char err_unable_to_convert_value_for[] = "unable to convert value \"%s\" for %s\n\n";
static const char err_output_path_no_delimiter[] = "output path must terminating with a \"%c\"\n\n";
static const char err_unable_open_output_path[] = "unable to open output path.\n";
static const char err_swin_no_min_max_available[] = "no min and max available in \"%s\" for SW_IN tolerances.\n\n";
static const char err_swin_no_min_tolerance[] = "no min tolerance available for SW_IN\n";
static const char err_swin_no_max_tolerance[] = "no max tolerance available for SW_IN\n";
static const char err_unable_create_gap_file[] = "unable to create gap file.";
static const char err_unable_convert_tolerance[] = "unable to convert tolerance \"%s\" for %s.\n\n";
static const char err_arg_needs_param[] = "%s parameter not specified.\n\n";
static const char err_arg_no_needs_param[] = "%s no needs parameter.\n\n";
static const char err_dataset_already_specified[] = "dataset already specified (%s)! \"%s\" skipped.\n";
static const char err_output_already_specified[] = "output path already specified (%s)! \"%s\" skipped.\n";
static const char err_unable_create_output_filename[] = "unable to create output filename.\n";
static const char err_rows_min[] = "rows_min must be between %d and %d not %d. default value (%d) will be used";

/* */
static void clean_up(void) {
	if ( program_path ) {
		free(program_path);
	}
	if ( files ) {
		free_files(files, files_count);
	}
}

/* */
int get_input_path(char *arg, char *param, void *p) {
	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	if ( input_path ) {
		printf(err_dataset_already_specified, input_path, param);
	} else {
		input_path = param;
	}
	
	/* ok */
	return 1;
}

/* */
int get_output_path(char *arg, char *param, void *p) {
	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	if ( output_path ) {
		printf(err_output_already_specified, output_path, param);
	} else {
		output_path = param;
	}
	
	/* ok */
	return 1;
}

/* */
int set_hourly_dataset(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	hourly_dataset = 1;

	/* ok */
	return 1;
}

/* */
static int set_token(char *arg, char *param, void *p) {
	int i;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	i = (int)p;
	assert(i < GF_TOKENS);

	strncpy(tokens[i], param, GF_TOKEN_LENGTH_MAX-1);
	tokens[i][GF_TOKEN_LENGTH_MAX-1] = '\0';
	custom_tokens[i] = 1;

	/* ok */
	return 1;
}

/* */
int set_swin_tolerances(char *arg, char *param, void *p) {
	int error;
	PREC min;
	PREC max;
	char *t;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	/* check for comma */
	t = strrchr(param, ',');
	if ( !t ) {
		printf(err_swin_no_min_max_available, param);
		return 0;
	}

	/* get min */
	*t = 0;
	if ( !param[0] ) {
		puts(err_swin_no_min_tolerance);
		return 0;
	}
	min = convert_string_to_prec(param, &error);
	if ( error ) {
		printf(err_unable_convert_tolerance, param, "SW_IN");
		return 0;
	}

	/* get max */
	++t;
	if ( !t[0] ) {
		puts(err_swin_no_max_tolerance);
		return 0;
	}
	max = convert_string_to_prec(t, &error);
	if ( error ) {
		printf(err_unable_convert_tolerance, param, "SW_IN");
		return 0;
	}

	/* */
	swin_tolerance_min = min;
	swin_tolerance_max = max;

	/* ok */
	return 1;
}

/* */
int set_prec_value(char *arg, char *param, void *p) {
	int error;
	PREC v;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}

	v = convert_string_to_prec(param, &error);
	if ( error ) {
		printf(err_unable_to_convert_value_for, param, arg);
		return 0;
	}

	/* */
	*((PREC *)p) = v;

	/* ok */
	return 1;
}

/* */
static int set_int_value(char *arg, char *param, void *p) {
	int i;
	int error;

	if ( !param ) {
		printf(err_arg_needs_param, arg);
		return 0;
	}
	i = convert_string_to_int(param, &error);
	if ( error ) {
		printf(err_unable_to_convert_value_for, param, arg);
		return 0;
	}

	/* set value */
	*((int *)p) = i;

	/* ok */
	return 1;
}

/* */
static int set_flag(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	/* enable */
	*((int *)p) = 1;

	/* ok */
	return 1;
}

/* */
int show_help(char *arg, char *param, void *p) {
	if ( param ) {
		printf(err_arg_no_needs_param, arg);
		return 0;
	}

	printf(msg_usage,
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_TOFILL],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_SWIN],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_TA],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_VPD],
						GF_TOKEN_LENGTH_MAX,
						def_tokens[GF_ROW_INDEX],
						swin_tolerance_min,
						swin_tolerance_max,
						ta_tolerance,
						vpd_tolerance,
						rows_min
	);

	/* must return error */
	return 0;
}

/* */
int main(int argc, char *argv[]) {
	int i;
	int y;
	int z;
	int j;
	int k;
	int w;
	int error;
	int rows_count;
	int files_processed_count;
	int files_not_processed_count;
	int total_files_count;
	int no_gaps_filled_count;
	char buffer[BUFFER_SIZE];
	char filename[FILENAME_SIZE];
	char *p;
	char *string;
	FILE *f;
	ROW *rows;
	GF_ROW *gf_rows;
	const ARGUMENT args[] = {
		{ "input", get_input_path, NULL },
		{ "output", get_output_path, NULL },
		{ "hourly", set_hourly_dataset, NULL },
		{ "tofill", set_token, (void *)GF_TOFILL },
		{ "ta", set_token, (void *)GF_TA },
		{ "sw_in", set_token, (void *)GF_SWIN },
		{ "vpd", set_token, (void *)GF_VPD },
		{ "date", set_token, (void *)GF_ROW_INDEX },
		{ "sw_int", set_swin_tolerances, NULL },
		{ "tat", set_prec_value, &ta_tolerance },
		{ "vpdt", set_prec_value, &vpd_tolerance },
		{ "rows_min", set_int_value, &rows_min },
		{ "dtime", set_flag, &has_dtime },
		{ "h", show_help, NULL },
		{ "?", show_help, NULL },
		{ "help", show_help, NULL },
	};
	
	/* show banner */
	puts(banner);

	/* register atexit */
	if ( -1 == atexit(clean_up) ) {
		puts(err_unable_to_register_atexit);
		return 1;
	}

	/* reset */
	for ( i = 0; i < GF_TOKENS; i++ ) {
		custom_tokens[i] = 0;
	}

	/* parse arguments */
	if ( !parse_arguments(argc, argv, args, SIZEOF_ARRAY(args)) ) {
		return 1;
	}

	/* get program path */
	program_path = get_current_directory();
	if ( !program_path ) {
		puts(err_unable_get_current_directory);
		return 1;
	}

	/* dataset specified ? */
	if ( !input_path ) {
		puts(msg_dataset_not_specified);
		input_path = program_path;
	}

	/* output path specified ? */
	if ( output_path ) {
		/* check if last char is a FOLDER_DELIMITER */
		if ( output_path[strlen(output_path)-1] != FOLDER_DELIMITER ) {
			printf(err_output_path_no_delimiter, FOLDER_DELIMITER);
			return 1;
		}

		/* check if output path exists */
		if ( !path_exists(output_path) ) {
			puts(err_unable_open_output_path);
			return 1;
		}
	} else {
		output_path = program_path;
	}

	/* get files */
	files = get_files(program_path, input_path, &files_count, &error);
	if ( error ) {
		return 1;
	}

	/* show output path */
	printf(msg_output_path, output_path);

	/* show rows min */
	if ( (rows_min < GF_ROWS_MIN_MIN) || (rows_min > GF_ROWS_MIN_MAX) ) {
		printf(err_rows_min, GF_ROWS_MIN_MIN, GF_ROWS_MIN_MAX, rows_min, GF_ROWS_MIN);
		rows_min = GF_ROWS_MIN;
	} else {
		printf(msg_rows_min, rows_min);
	}

	/* assign columns names */
	for ( i = 0; i < GF_TOKENS; i++ ) {
		if ( !custom_tokens[i] ) {
			strncpy(tokens[i], def_tokens[i], GF_TOKEN_LENGTH_MAX-1);
			tokens[i][GF_TOKEN_LENGTH_MAX-1] = '\0';
		}
	}

	/* show tolerances */
	printf(msg_tolerances,
							tokens[GF_SWIN],
							swin_tolerance_min,
							swin_tolerance_max,
							tokens[GF_TA],
							ta_tolerance,
							tokens[GF_VPD],
							vpd_tolerance
	);

	/* reset */
	files_processed_count = 0;
	files_not_processed_count = 0;
	total_files_count = 0;

	/* loop for searching file */
	for ( z = 0; z < files_count; z++) {
		/* inc total files founded */
		total_files_count += files[z].count;

		/* processing and create output filename */
		filename[0] = '\0';
		for ( i = 0; i < files[z].count; i++ ) {
			if ( !i ) {
				printf(msg_import_dataset, files[z].list[i].name, (files[z].count>1) ? "+" : "...");
			} else {
				printf(files[z].list[i].name);
				if ( files[z].count-1 == i ) {
					printf("...");
				} else {
					printf("+");
				}
			}
			string = string_copy(files[z].list[i].name);
			if ( !string ) {
				puts(err_out_of_memory);
				return 1;
			}

			/* check for extension */
			p = strrchr(string, '.');
			if ( p ) {
				/* remove extension */
				*p = '\0';
			}

			/* add to filename */
			if ( !mystrcat(filename, string, FILENAME_MAX) && '\0' == filename[0]) {
				puts(err_unable_create_output_filename);
				files_not_processed_count += files[z].count;
				free(string);
				continue;
			}

			/* add underscore */
			if ( !add_char_to_string(filename, '_', FILENAME_MAX) && '\0' == filename[0]) {
				puts(err_unable_create_output_filename);
				files_not_processed_count += files[z].count;
				free(string);
				continue;
			}

			/* free memory */
			free(string);
		}

		/* import dataset */
		rows = import_dataset(files[z].list, files[z].count, &rows_count); 
		if ( !rows ) {
			free(years);
			files_not_processed_count += files[z].count;
			continue;
		}

		/* gf */
		gf_rows = gf_mds(rows->value, sizeof(ROW), rows_count, GF_REQUIRED_DATASET_VALUES, hourly_dataset, swin_tolerance_min, swin_tolerance_max, ta_tolerance, vpd_tolerance, GF_TOFILL, GF_SWIN, GF_TA, GF_VPD, rows_min, 1, &no_gaps_filled_count);
		if ( !gf_rows ) {
			free(years);
			free(rows);
			files_not_processed_count += files[z].count;
			continue;
		}

		/* create output file */
		sprintf(buffer, gap_file, output_path, filename);
		f = fopen(buffer, "w");
		if ( !f ) {
			puts(err_unable_create_gap_file);
			free(years);
			free(rows);
			free_details_list(details_list, files[z].count);
			files_not_processed_count += files[z].count;
			continue;
		}

		/* write details */
		if ( details_list && details_list[0] ) {
			sprintf(buffer, notes, get_datetime_in_timestamp_format());
			write_dds(details_list, files[z].count, f, buffer);
		}

		/* write header */
		if ( !IS_INVALID_VALUE(years[0]) ) {
			fprintf(f, gap_header, tokens[GF_TOFILL]);
		} else {
			fprintf(f, gap_dtime_header, tokens[GF_TOFILL]);
		}
		
		/* write values */
		for ( y = 0; y < files[z].count; y++ ) {
			if ( !IS_INVALID_VALUE(years[y]) ) {
				y = 0;
				w = 0;
				j = IS_LEAP_YEAR(years[y]) ? LEAP_YEAR_ROWS : YEAR_ROWS;
				if ( hourly_dataset ) {
					j /= 2;
				}
				/* */
				for ( i = 0; i < rows_count; i++ ) {
					if ( i == j ) {
						++y;
						k = IS_LEAP_YEAR(years[y]) ? LEAP_YEAR_ROWS : YEAR_ROWS;
						if ( hourly_dataset ) {
							k /= 2;
						}
						j += k;
						k = IS_LEAP_YEAR(years[y-1]) ? LEAP_YEAR_ROWS : YEAR_ROWS;
						if ( hourly_dataset ) {
							k /= 2;
						}
						w += k;
					}
					fprintf(f, gap_format,
											timestamp_end_by_row_s(i-w, years[y], hourly_dataset),
											rows[i].value[GF_TOFILL],
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? rows[i].value[GF_TOFILL] : gf_rows[i].filled,
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality,
											gf_rows[i].filled,									
											gf_rows[i].samples_count,
											gf_rows[i].stddev,
											gf_rows[i].method,
											gf_rows[i].quality,
											gf_rows[i].time_window
					);
				}
			} else {
				for ( i = 0; i < rows_count; i++ ) {
					fprintf(f, gap_dtime_format,
											get_dtime_by_row(i, hourly_dataset),
											rows[i].value[GF_TOFILL],
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? rows[i].value[GF_TOFILL] : gf_rows[i].filled,
											IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ? 0 : gf_rows[i].quality,
											gf_rows[i].filled,									
											gf_rows[i].samples_count,
											gf_rows[i].stddev,
											gf_rows[i].method,
											gf_rows[i].quality,
											gf_rows[i].time_window
					);
				}
			}
		}

		/* close file */
		fclose(f);

		/* free memory */
		free(gf_rows);
		free(years);
		free(rows);
		if ( details_list ) {
			free_details_list(details_list, files[z].count);
		}

		/* increment processed files count */
		files_processed_count += files[z].count;

		/* */
		if ( !no_gaps_filled_count ) {
			puts(msg_ok);
		} else {
			printf(msg_ok_with_gaps_unfilled, no_gaps_filled_count);
		}
	}

	/* summary */
	printf(msg_summary,
						total_files_count,
						total_files_count > 1 ? "s" : "",
						files_processed_count,
						files_not_processed_count
	);

	/* memory freeded on return */
	return 0;
}
