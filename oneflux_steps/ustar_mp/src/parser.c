/*
	parser.c

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <assert.h>
#include "parser.h"

/* defines */
#define IS_COMMA(x)						(((x)==','))
#define IS_SEMICOLON(x)					(((x)==';'))

/* enumerations */
enum {
	digit = 0,
	other
} symbol;

/* eternal global variables */
extern int seasons_group_allow_duplicates;

/* external error strings */
extern const char err_out_of_memory[];

/* error strings */
static const char err_no_string_to_parse[] = "no string to parse.\n";
static const char err_missing_digit[] = "missing digit";
static const char err_numbers_allowed[] = "only numbers from 1 to 12 are allowed. error";
static const char err_month_redudancy[] = "month already specified";
static const char err_invalid_token[] = "invalid token";
static const char err_at_index[] = "%s at index %d\n";
static const char err_format[] = "%*s\n";

/* */
static void show_error(const char *const msg, const char *const string, int i) {
	printf(err_at_index, msg, i+1);
	puts(string);
	printf(err_format, i+1, "^");
}

/* */
void free_seasons_group(SEASONS_GROUP *seasons_group, const int seasons_group_count) {
	if ( seasons_group ) {
		int i;

		for ( i = 0; i < seasons_group_count; i++ ) {
			free(seasons_group[i].month);
			seasons_group[i].month = NULL;
		}
		free(seasons_group);
	}
}

/* */ 
SEASONS_GROUP *parse_seasons_group(const char *const string, int *const seasons_group_count) {
	int i;
	int y;
	int j;
	int z;
	int string_len;
	int digits_count;
	int error;
	int current_month;
	int current_index;
	int group_count;
	char c[3];
	int expected_symbol;
	SEASONS_GROUP *seasons_group;
	int *month_no_leak;

	/* check for parameters */
	assert(string && seasons_group_count);

	/* check groups by counting ; occurrences */
	/* and compute string length */
	string_len = 0;
	*seasons_group_count = 0;
	for ( i = 0; string[i]; i++ ) {
		if ( IS_SEMICOLON(string[i]) ) {
			++*seasons_group_count;
		}
		++string_len;
	}

	/* fix groups count*/
	++*seasons_group_count;

	/* check string length */
	if ( !string_len ) {
		puts(err_no_string_to_parse);
		return NULL;
	}

	/* alloc memory */
	seasons_group = malloc(*seasons_group_count*sizeof*seasons_group);
	if ( !seasons_group ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* reset */
	for ( i = 0; i < *seasons_group_count; i++ ) {
		seasons_group[i].month = NULL;
		seasons_group[i].count = 0;
	}

	/* first expected token is a digit */
	expected_symbol = digit;

	/* loop */
	current_index = 0;
	group_count = 0;
	z = 0; /* keep track of current group */
	for ( i = 0; string[i]; i++ ) {
		switch ( expected_symbol ) {
			case digit:
				/* check if is a digit */
				if ( !isdigit(string[i]) ) {
					show_error(err_missing_digit, string, i);
					free_seasons_group(seasons_group, *seasons_group_count);
					return NULL;
				}

				/* count digits */
				digits_count = 0;
				for ( y = i; string[y]; y++) {
					if ( isdigit(string[y]) ) {
						++digits_count;
					} else {
						break;
					}
				}

				/* check digits */
				if ( digits_count > 2 ) {
					show_error(err_numbers_allowed, string, i);
					free_seasons_group(seasons_group, *seasons_group_count);
					return NULL;
				}

				/* get digits */
				strncpy(c, string+i, digits_count);
				c[digits_count] = '\0';

				/* convert digit */
				current_month = convert_string_to_int(c, &error);
				if ( error ) {
					show_error(err_missing_digit, string, i);
					free_seasons_group(seasons_group, *seasons_group_count);
					return NULL;
				}

				/* check value */
				if ( current_month <= 0 || current_month > 12 ) {
					show_error(err_numbers_allowed, string, i);
					free_seasons_group(seasons_group, *seasons_group_count);
					return NULL;
				}

				/* fix month to zero-base index */
				--current_month;

				/* check if month is already setted*/
				if ( !seasons_group_allow_duplicates ) {
					for ( y = 0; y < z; y++ ) {
						for ( j = 0; j < seasons_group[y].count; j++ ) {
							if ( current_month == seasons_group[y].month[j]) {
								show_error(err_month_redudancy, string, i);
								free_seasons_group(seasons_group, *seasons_group_count);
								return NULL;
							}
						}
					}
				}

				/* alloc memory */
				month_no_leak = realloc(seasons_group[z].month, (++seasons_group[z].count)*sizeof*month_no_leak);
				if ( !month_no_leak ) {
					puts(err_out_of_memory);
					free_seasons_group(seasons_group, *seasons_group_count);
					return NULL;
				}

				/* set month */
				seasons_group[z].month = month_no_leak;
				seasons_group[z].month[seasons_group[z].count-1] = current_month;

				/* next token */
				expected_symbol = other;

				/* adjust counter */
				if ( digits_count > 1 ) {
					i += (digits_count-1);
				}
			break;

			default:
				if ( IS_COMMA(string[i]) ) {
					/* next token */
					expected_symbol = digit;
				} else if ( IS_SEMICOLON(string[i]) ) {
					/* inc seasons */
					++z;
					/* next token */
					expected_symbol = digit;
				} else {
					show_error(err_invalid_token, string, i);
					return 0;
				}
		}
	}

	/* check */
	if ( digit == expected_symbol ) {
		show_error(err_invalid_token, string, i-1);
		free_seasons_group(seasons_group, *seasons_group_count);
		return NULL;
	}

	/* fix groups count */
	*seasons_group_count = z+1;

	/* return pointer */
	return seasons_group;
}
