/*
	dataset.c

	this file is part of shift_solar_noon

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "dataset.h"
#include "rpot.h"

/* var stuff */
#define VAR_ATTR_SET(var,a)			((var)->attr |= (a))
#define IS_VAR_ATTR_SET(var,a)		(((var)->attr & (a)) == (a))

#define IS_VAR_MAIN(var)			( (0 == (var)->x) && (0 == (var)->y) && (0 == (var)->z))
#define IS_VAR_PROFILE(var)			( (0 == (var)->x) && (0 != (var)->y) && (0 == (var)->z))
#define IS_VAR_LEAF(var)			( (0 != (var)->x) && (0 != (var)->y) && (0 != (var)->z))

#define SD_QUALIFIER	"SD"
#define N_QUALIFIER		"N"

/* enums */
typedef enum {
	NONE_ATTR		= 0,			/* 0  */
	SD_ATTR			= 1 << 0,		/* 1  */		/* var is X_?_SD...if MAIN, ? is not present */
	N_ATTR			= 1 << 1,		/* 2  */		/* var is X_?_N...if MAIN, ? is not present */
	SUPPORT_ATTR	= 1 << 2,		/* 4  */		/* var is "support" type...as RAT from BE-Lcr, used to correct LW_IN and LW_OUT values */
	NO_AGGR_ATTR	= 1 << 3,		/* 8  */		/* var is NOT aggregable */
	AGGR_ATTR		= 1 << 4,		/* 16 */		/* var is (already) aggregated...do not use it anymore! */
	REQ_ATTR		= 1 << 5,		/* 32 */		/* var is requested by user */
	JUNK_ATTR		= 1 << 6,		/* 64 */		/* var is garbage! */
} eVarAttr;

/* strings */
static const char header_delimiter[] = ", \r\n";
static const char dataset_delimiter[] = ",\r\n";

/* please use same order of enum in types.h */
const char *const var_names[] = {
	"CO2",
	"H2O",
	"ZL",
	"FC",
	"FC_SSITC_TEST",		/* QcFc */
	"H",
	"H_SSITC_TEST",			/* QcH */
	"LE",
	"LE_SSITC_TEST",		/* QcLE */
	"USTAR",

	"TR",
	"SB",
	"SC",
	"SLE",					/* SW */

	"SH",					/* SA */
	"P",
	"SW_OUT",
	"SW_IN",
	"NETRAD",
	"SW_DIF",
	"PPFD_IN",
	"APAR",
	"TA",
	"PA",

	"T_CANOPY",				/* Tc */
	"T_BOLE",
	"TS",
	"SWC",
	"G",
	"RH",
	"WD",
	"WS",
	"TAU",
	"LW_IN",
	"NEE",
	"VPD",
	"itpVPD",
	"itpSW_IN",
	"itpPPFD",
	"itpTA",
	"itpTS",
	"itpSWC",
	"itpP",
	"itpRH",
	"FETCH_FILTER",			/* QcFoot */

	/* to add */
	"SWIN_ORIGINAL",
	"PPFD_ORIGINAL",
	"FCSTOR",
	"FCSTORTT",
	"HEIGHT",
	"SW_IN_POT",
	"NEE_SPIKE",
	"LE_SPIKE",
	"H_SPIKE",
	"NIGHT",
	"DAY",			/* DAY must be after NIGHT, see spike.c */
	"SC_NEGLES",
	"TEMP"
};

/* please use same order of enum in types.h */
const char *const var_flag_names[] = {	"NEE",
										"USTAR",
										"MARGINAL_NEE",
										"MARGINAL_LE",
										"MARGINAL_H",
										"SW_IN_FROM_PPFD",
										"SW_IN_VS_SW_IN_POT",
										"PPFD_VS_SW_IN_POT",
										"SW_IN_VS_PPFD",
										"SPIKE_NEE",
										"SPIKE_LE",
										"SPIKE_H",
										"QC2_NEE",
										"QC2_LE",
										"QC2_H",
};

/* error strings */
static const char err_unable_open_file[] = "unable to open file.";
static const char err_redundancy[] = "redundancy: var \"%s\" already founded at column %d.\n";
static const char err_unable_find_column[] = "unable to find column for \"%s\" var.\n";
static const char err_conversion[] = "error during conversion of \"%s\" value at row %d, column %d.\n";
static const char err_too_many_rows[] = "too many rows.";
static const char err_imported_rows_count[] = "imported rows should be %d, not %d.\n";
static const char err_imported_columns_count[] = "imported columns at row %d should be %d, not %d.\n";
static const char err_unable_get_latitude_longitude[] = "unable to get latitude and longitude.\n";
static const char err_unable_parse_header[] = "unable to parse header.\n";
static const char err_bad_header[] = "bad header.\n";
static const char err_unable_create_aux_file[] = "unable to create aux file.\n";
static const char err_required_var_not_found[] = "required var %s not found in dataset.\n\n";
static const char err_bad_dataset[] = "bad row at %d\n\n";
static const char err_bad_dataset_no_values[] = "no values found.\n";
static const char err_unable_convert_year[] = "unable to convert YEAR at row %d: %s.\n";
static const char err_unable_convert_gap[] = "unable to convert GAP at row %d: %s.\n";
static const char err_unable_convert_doy[] = "unable to convert DOY at row %d: %s.\n";
static const char err_bad_doy[] = "bad DOY at row %d: %s\n";
static const char err_bad_year[] = "bad year found at row %d: must be %d not %d.\n";
static const char err_invalid_co2height[] = "invalid co2height.\n";
static const char err_bad_time_resolution[] = "only dataset with halfhourly or hourly time resolution can be parsed.\n";
static const char err_unable_convert_index[]= "unable to get index from var name: %s\n\n";
static const char field_delimiter[] = ",\r\n";

/* extern error strings */
extern const char err_out_of_memory[];
extern const char err_empty_file[];
extern char *output_path;
extern PREC height;

/* */
VAR *var_new(void) {
	VAR *v;

	v = malloc(sizeof*v);
	if ( v ) {
		v->name = NULL;
		v->x = 0;
		v->y = 0;
		v->z = 0;
		v->attr = NONE_ATTR;
	}
	return v;
}

/* */
void var_free(VAR *v) {
	assert(v);
	if ( v->name) {
		free(v->name);
	}
	free(v);
}

/* */
VAR *var_get(const char *const string) {
	int i;
	int j;
	int digits[3];
	int error;
	int underscoresFound;
	int digitsFound;
	int isSD;
	int isN;
	char *p;
	char buffer[BUFFER_SIZE];
	VAR *var;

	/* */
	assert(string);

	/* reset */
	isSD = 0;
	isN = 0;

	/* */
	var = var_new();
	if ( ! var ) {
		return NULL;
	}

	/* count underscores */
	underscoresFound = 0;
	for ( i = 0; string[i]; ++i ) {
		if ( '_' == string[i] ) {
			++underscoresFound;
		}
	}

	/* no underscores ? */
	if ( ! underscoresFound ) {
		var->name = string_copy(string);
		if ( ! var->name ) {
			var_free(var);
			return NULL;
		}
		return var;
	}

	/* check string length < buffer length */
	if ( i >= BUFFER_SIZE ) {
		var_free(var);
		return NULL;
	}

	/* copy string */
	strcpy(buffer, string);

	/* start from last underscore */
	digitsFound = 0;
	for ( i = underscoresFound; i > 0; --i ) {
		/* get digit (if any) */
		p = strrchr(buffer, '_');
		if ( p ) {
			++p;
			j = convert_string_to_int(p, &error);
			if ( error ) {
				/* check for qualifier */
				if ( ! string_compare_i(p, "SD") ) {
					isSD = 1;
				} else if ( ! string_compare_i(p, "N") ) {
					isN = 1;
				} else {
					break;
				}
			}
			--p;
			*p = '\0';
			if( ! error ) {
				if ( ++digitsFound > 3 ) {
					break;
				}
				digits[digitsFound-1] = j;
			}
		} else {
			break;
		}
	}

	/* check if sd or n */
	if ( isSD ) {
		VAR_ATTR_SET(var, SD_ATTR);
	} else if ( isSD ) {
		VAR_ATTR_SET(var, N_ATTR);
	}

	/* check if digitsFound is 2 or 4 */
	if ( digitsFound && !(digitsFound % 2) ) {
		*p = '_';
	}

	var->name = string_copy(buffer);
	if ( ! var->name ) {
		var_free(var);
		return NULL;
	}
	if ( (1 == digitsFound) || (2 == digitsFound) ) {
		var->y = digits[0];
	} else if ( digitsFound >= 3 )  {
		/* fill in reverse order */
		var->z = digits[0];
		var->y = digits[1];
		var->x = digits[2];
	}
	return var;
}

/* */
static int var_equals(const VAR *const a, const VAR *const b) {
	return ! string_compare_i(a->name, b->name)
			&& (a->x == b->x)
			&& (a->y == b->y)
			&& (a->z == b->z)
			&& (a->attr == b->attr)
	;
}

/* */
char *var_name_f(const VAR *const var) {
	static char buffer[64];

	if ( IS_VAR_ATTR_SET(var, SD_ATTR) ) {
		if ( var->y ) {
			sprintf(buffer, "%s_%d_" SD_QUALIFIER, var->name, var->y);
		} else {
			sprintf(buffer, "%s_" SD_QUALIFIER, var->name);
		}
	} else if ( IS_VAR_ATTR_SET(var, N_ATTR) ) {
		if ( var->y ) {
			sprintf(buffer, "%s_%d_" N_QUALIFIER, var->name, var->y);
		} else {
			sprintf(buffer, "%s_" N_QUALIFIER, var->name);
		}
	} else if ( IS_VAR_PROFILE(var) ) {
		sprintf(buffer, "%s_%d", var->name, var->y);
	} else if ( IS_VAR_LEAF(var) ) {
		sprintf(buffer, "%s_%d_%d_%d", var->name, var->x, var->y, var->z);
	} else { /* MAIN or SUPPORT */
		sprintf(buffer, "%s", var->name);
	}

	return buffer;
}

/* */
static int parse_header(DATASET *const dataset, char *header, const char *const header_delimiter) {
	int i;
	int j;
	char *token;
	char *p;
	VAR *var_no_leak;
	VAR *var;

	for ( i = 0, token = string_tokenizer(header, header_delimiter, &p); token; token = string_tokenizer(NULL, header_delimiter, &p), ++i ) {
		if ( ! string_compare_i(token, TIMESTAMP_START_STRING) ) {
			if ( dataset->has_timestamp_start ) {
				printf("column %s already found.\n", TIMESTAMP_START_STRING);
				return 0;
			}
			dataset->has_timestamp_start = 1;
		} else if ( ! string_compare_i(token, TIMESTAMP_END_STRING) || ! string_compare_i(token, TIMESTAMP_STRING) ) {
			if ( dataset->has_timestamp_end ) {
				printf("column %s already found.\n", TIMESTAMP_END_STRING);
				return 0;
			}
			dataset->has_timestamp_end = 1;
		} else {
			/* check if is a valid var */
			var = var_get(token);
			if ( ! var ) {
				printf("unable to get var: %s\n", token);
				return 0;
			}

			var_no_leak = realloc(dataset->header, ++dataset->columns_count*sizeof*var_no_leak);
			if ( ! var_no_leak ) {
				puts(err_out_of_memory);
				--dataset->columns_count;
				return 0;
			}
			dataset->header = var_no_leak;
			dataset->header[dataset->columns_count-1].name = var->name;
			dataset->header[dataset->columns_count-1].x = var->x;
			dataset->header[dataset->columns_count-1].y = var->y;
			dataset->header[dataset->columns_count-1].z = var->z;
			dataset->header[dataset->columns_count-1].attr = var->attr;
			/* we do not use var_free 'cause name pointer is copied into header...will be freed later */
			free(var);
		}
	}

	/* check if timestamps are found */
	if ( ! dataset->has_timestamp_start && ! dataset->has_timestamp_end ) {
		printf("%s not found!\n", TIMESTAMP_HEADER);
		return 0;
	}
	if ( dataset->has_timestamp_start && ! dataset->has_timestamp_end ) {
		printf("%s not found\n", TIMESTAMP_END_STRING);
		return 0;
	}

	/* check for redundancy */
	for ( i = 0; i < dataset->columns_count; i++ ) {
		for ( j = i; j < dataset->columns_count - 1; j++ ) {
			if ( var_equals(&dataset->header[i], &dataset->header[j+1]) ) {
				printf("vars %s founded at row %d and %d", var_name_f(&dataset->header[i]), i+1, j+1);
				return 0;
			}
		}
	}

	return 1;
}

/* */
static void set_height(DATASET *const dataset) {
	int i;
	int HEIGHT;

	/* get HEIGHT column */
	HEIGHT = get_var_index(dataset, var_names[HEIGHT_INPUT]);
	assert(HEIGHT != -1);

	/* TODO - check for date range */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		dataset->rows[i].value[HEIGHT] = dataset->details->htower[0].h;
	}
}

/* */
int add_var_to_dataset(DATASET *const dataset, const char *const name, const int x, const int y, const int z, const int attr) {
	int i;
	int *pi;
	char *p;
	VAR *var_no_leak;
	PREC *pvalue;

	/* check parameter */
	assert(dataset && name);

	/* copy var name*/
	p = string_copy(name);
	if ( ! p ) {
		return -1;
	}

	/* add var to header */
	var_no_leak = realloc(dataset->header, ++dataset->columns_count*sizeof*var_no_leak);
	if ( !var_no_leak ) {
		--dataset->columns_count;
		return -1;
	}
	dataset->header = var_no_leak;
	dataset->header[dataset->columns_count-1].name = p;
	dataset->header[dataset->columns_count-1].x = x;
	dataset->header[dataset->columns_count-1].y = y;
	dataset->header[dataset->columns_count-1].z = z;
	dataset->header[dataset->columns_count-1].attr = attr;

	/* add var to values */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		pvalue = realloc(dataset->rows[i].value, dataset->columns_count*sizeof*pvalue);
		if ( !pvalue ) {
			/* not really sure about this... */
			free(dataset->header[dataset->columns_count-1].name);
			dataset->header[dataset->columns_count-1].name = NULL;
			/* */
			--dataset->columns_count;
			return -1;
		}
		dataset->rows[i].value = pvalue;
		dataset->rows[i].value[dataset->columns_count-1] = INVALID_VALUE;
	}

	/* add flags */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		pvalue = realloc(dataset->flags[i].value, dataset->columns_count*sizeof*pvalue);
		if ( !pvalue ) {
			/* not really sure about this... */
			free(dataset->header[dataset->columns_count-1].name);
			dataset->header[dataset->columns_count-1].name = NULL;
			/* */
			for ( i = 0; i < dataset->rows_count; i++ ) {
				free(dataset->rows[i].value);
				dataset->rows[i].value = NULL;
			}
			--dataset->columns_count;
			return -1;
		}
		dataset->flags[i].value = pvalue;
		dataset->flags[i].value[dataset->columns_count-1] = INVALID_VALUE;
	}

	/* add missings */
	pi = realloc(dataset->missings, dataset->columns_count*sizeof*pi);
	if ( !pi ) {
		return -1;
	}
	dataset->missings = pi;
	dataset->missings[dataset->columns_count-1] = dataset->rows_count;

	/* ok */
	return dataset->columns_count-1;
}

/* */
DATASET *import_dataset(const char *const filename) {
	int i;
	int index;
	int element;
	int old_columns_count;
	char buffer[BUFFER_SIZE*4];
	char *token;
	char *p;
	VAR *var_no_leak;
	int error;
	int assigned;
	FILE *f;
	PREC value;
	DATASET *dataset;

	/* check for null pointers */
	assert(filename);

	/* alloc memory */
	dataset = malloc(sizeof*dataset);
	if ( !dataset ) {
		puts(err_out_of_memory);
		return NULL;
	}
	dataset->details = NULL;
	dataset->header = NULL;
	dataset->columns_count = 0;
	dataset->rows = NULL;
	dataset->rows_count = 0;
	dataset->flags = NULL;
	dataset->flags_count = 0;
	dataset->missings = NULL;
	dataset->meteora = NULL;
	dataset->has_timestamp_start = 0;
	dataset->has_timestamp_end = 0;

	/* open file */
	f = fopen(filename, "r");
	if ( !f ) {
		printf("unable to open %s\n", filename);
		free_dataset(dataset);
		return NULL;
	}

	/* get details */
	dataset->details = parse_dd(f);
	if ( !dataset->details ) {
		free(dataset);
		return NULL;
	}

	/* is leap year ? */
	dataset->leap_year = IS_LEAP_YEAR(dataset->details->year);

	/* get rows count */
	dataset->rows_count = dataset->leap_year ? LEAP_YEAR_ROWS : YEAR_ROWS;

	/* get header */
	if ( ! get_valid_line_from_file(f, buffer, BUFFER_SIZE*4) ) {
		puts("header missing ?");
		free_dataset(dataset);
		fclose(f);
		return NULL;
	}

	/* parse header */
	if ( ! parse_header(dataset, buffer, header_delimiter) ) {
		free_dataset(dataset);
		fclose(f);
		return NULL;
	}

	/* hourly ? */
	if ( HOURLY_TIMERES == dataset->details->timeres ) {
		dataset->rows_count /= 2;
	} else if ( HALFHOURLY_TIMERES != dataset->details->timeres ) {
		puts(err_bad_time_resolution);
		free_dataset(dataset);
		fclose(f);
		return NULL;
	}

	/* remember columns count before we add */
	old_columns_count = dataset->columns_count;

	/* add temporary vars */
	for ( i = DATASET_VALUES; i < INPUT_VALUES; ++i ) {
		var_no_leak = realloc(dataset->header, ++dataset->columns_count*sizeof*var_no_leak);
		if ( !var_no_leak ) {
			puts(err_out_of_memory);
			--dataset->columns_count;
			free_dataset(dataset);
			fclose(f);
			return NULL;
		}
		dataset->header = var_no_leak;
		dataset->header[dataset->columns_count-1].name = string_copy(var_names[i]);
		if ( !dataset->header[dataset->columns_count-1].name ) {
			puts(err_out_of_memory);
			free_dataset(dataset);
			fclose(f);
			return NULL;
		}
		dataset->header[dataset->columns_count-1].x = 1;
		dataset->header[dataset->columns_count-1].y = 1;
		dataset->header[dataset->columns_count-1].z = 1;
		dataset->header[dataset->columns_count-1].attr = NONE_ATTR;
	}

	/* alloc memory for rows */
	dataset->rows = malloc(dataset->rows_count*sizeof*dataset->rows);
	if ( !dataset->rows ) {
		puts(err_out_of_memory);
		free_dataset(dataset);
		fclose(f);
		return NULL;
	}

	for ( i = 0; i < dataset->rows_count; ++i ) {
		dataset->rows[i].value = malloc(dataset->columns_count*sizeof*dataset->rows[i].value);
		if ( !dataset->rows[i].value ) {
			puts(err_out_of_memory);
			dataset->rows_count = i-1;
			free_dataset(dataset);
			fclose(f);
			return NULL;
		}
		for ( index = 0; index < dataset->columns_count; index++ ) {
			dataset->rows[i].value[index] = INVALID_VALUE;
		}
	}

	/* alloc memory for flags... */
	dataset->flags_count = SIZEOF_ARRAY(var_flag_names);
	dataset->flags = malloc(dataset->rows_count*sizeof*dataset->flags);
	if ( !dataset->flags ) {
		puts(err_out_of_memory);
		free_dataset(dataset);
		fclose(f);
		return NULL;
	}

	/* ...and reset flags */
	for ( i = 0; i < dataset->rows_count; ++i ) {
		dataset->flags[i].value = malloc(dataset->flags_count*sizeof*dataset->flags[i].value);
		if ( !dataset->flags[i].value ) {
			puts(err_out_of_memory);
			free_dataset(dataset);
			fclose(f);
			return NULL;
		}
		for ( index = 0; index < dataset->flags_count; ++index ) {
			dataset->flags[i].value[index] = 0.;
		}
	}

	/* alloc memory for missings */
	dataset->missings = malloc(dataset->columns_count*sizeof*dataset->missings);
	if ( !dataset->missings ) {
		puts(err_out_of_memory);
		free_dataset(dataset);
		fclose(f);
		return NULL;
	}
	for ( i = 0; i < dataset->columns_count; ++i ) {
		dataset->missings[i] = 0;
	}

	/* get values */
	element = 0;
	while ( get_valid_line_from_file(f, buffer, BUFFER_SIZE*4) ) {
		/* prevent too many rows */
		if ( element++ == dataset->rows_count ) {
			puts(err_too_many_rows);
			free_dataset(dataset);
			fclose(f);
			return NULL;
		}

		/* */
		assigned = 0;
		index = dataset->has_timestamp_start+dataset->has_timestamp_end; /* how many timestamps we have ? */
		for ( i = 0, token = string_tokenizer(buffer, dataset_delimiter, &p); token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
			/* skip timestamps */
			if ( i < index ) {
				continue;
			}
			/* convert token */
			value = convert_string_to_prec(token, &error);
			if ( error ) {
				printf(err_conversion, token, i+1, element+1);
				free_dataset(dataset);
				fclose(f);
				return NULL;
			}
			/* check for NAN */
			if ( value != value ) {
				value = INVALID_VALUE;
			}

			/* assign value */
			dataset->rows[element-1].value[i-index] = value;

			/* inc counter */
			++assigned;
		}

		/* check imported columns */
		if ( assigned != old_columns_count ) {
			printf(err_imported_columns_count, element, old_columns_count, assigned);
			free_dataset(dataset);
			fclose(f);
			return NULL;
		}
	}

	/* close file */
	fclose(f);

	/* check imported rows */
	if ( element != dataset->rows_count ) {
		printf(err_imported_rows_count, dataset->rows_count, element);
		free_dataset(dataset);
		return NULL;
	}

	/* set height */
	set_height(dataset);

	/* */
	puts("ok");

	/* ok */
	return dataset;
}

/* */
void free_dataset(DATASET *dataset) {
	if ( dataset ) {
		int i;

		free_dd(dataset->details);

		if ( dataset->header ) {
			for ( i = 0; i < dataset->columns_count; ++i ) {
				if ( dataset->header[i].name ) {
					free(dataset->header[i].name);
				}
			}
			free(dataset->header);
		}

		if ( dataset->rows ) {
			for ( i = 0; i < dataset->rows_count; ++i ){
				free(dataset->rows[i].value);
			}
			free(dataset->rows);
		}

		if ( dataset->flags ) {
			for ( i = 0; i < dataset->rows_count; ++i ){
				free(dataset->flags[i].value);
			}
			free(dataset->flags);
		}

		if ( dataset->missings ) {
			free(dataset->missings);
		}

		if ( dataset->meteora ) {
			free(dataset->meteora);
		}

		free(dataset);
	}
}

/* */
int get_var_index(const DATASET *const dataset, const char *const name) {
	int i;

	/* prevent errors */
	if (	! string_compare_i(name, var_names[SWC_INPUT]) ||
			! string_compare_i(name, var_names[TS_INPUT]) ) {
		assert(!"get_var_index must not be used on SWC and TS!");
	}

	for ( i = 0; i < dataset->columns_count; i++ ) {
		if (	! string_compare_i(dataset->header[i].name, name)
				&& (1 == dataset->header[i].x) 
				&& (1 == dataset->header[i].y) 
				&& (1 == dataset->header[i].z) ) {
			return i;
		}
		if (	! string_compare_i(dataset->header[i].name, name)
				&& (0 == dataset->header[i].x) 
				&& (1 == dataset->header[i].y) 
				&& (0 == dataset->header[i].z) ) {
			return i;
		}
	}

	return -1;
}

/* on memory error, count is -1*/
int *get_var_indexes(const DATASET *const dataset, const char *const name, int *const count) {
	int i;
	int *indexes;
	int *temp;

	assert(dataset && name && count);

	indexes = NULL;
	*count = 0;

	for ( i = 0; i < dataset->columns_count; ++i ) {
		if ( ! string_compare_i(dataset->header[i].name, name) ) {
			temp = realloc(indexes, ++*count*sizeof*temp);
			if ( ! temp ) {
				puts(err_out_of_memory);
				free(indexes);
				*count = -1;
				return NULL;
			}
			indexes = temp;
			indexes[*count-1] = i;
		}
	}

	return indexes;
}

/* */
int get_flag_index(const DATASET *const dataset, const char *const name) {
	int i;

	for ( i = 0; i < dataset->flags_count; ++i ) {
		if ( ! string_compare_i(var_flag_names[i], name) ) {
			return i;
		}
	}

	return -1;
}
