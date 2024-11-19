/*
	main.c

	This file is part of SW_IN_POT_Calculator that
	calculates the extra-atmosphere potential short-wave
	incoming radiation based on geographical location
	and time.

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../../../compiler.h"
#include "../../../common/common.h"
	
/* constants */
#define PROGRAM_VERSION		"1.01"
#define DEFAULT_EXT			".csv"
#define MAX_FILENAME_SIZE	64

/* strings */
static const char banner[] =	"\nSW_IN_POT Calculator "PROGRAM_VERSION"\n"
								"by Alessio Ribeca\n\n"
								"scientific contact: darpap at unitus dot it\n"
								"technical contact: a dot ribeca at unitus dot it\n\n"
								"DIBAF - University of Tuscia, Viterbo, Italy\n"
								"(builded on "__DATE__" at "__TIME__ " with "COMPILER")\n"
								"(use -h parameter for more information)\n";

/* messages */
static const char msg_usage[] = "usage: SW_IN_POT_Calculator filename YYYY[-YYYY] lat lon zone [hourly]\n\n"
								"mandatory parameters:\n\n"
								"   filename -> output name without extension, format will be "DEFAULT_EXT"\n"
								"   YYYY[-YYYY]  -> year or years. range separated by a minus sign\n"
								"   lat          -> latitude in decimal degree\n"
								"   lon          -> longitude in decimal degree\n"
								"   zone         -> current timezone\n\n"
								"optional parameters:\n\n"
								"   hourly       -> specify 1 to get hourly SW_IN_POT (default is off)\n"
								"   single       -> specify 1 to create one file per year\n"
								"   h            -> show this help\n\n"
								"e.g.:\n\n"
								"   SW_IN_POT_Calculator foo 1996 43.7279 10.2844 1\n\n"
								"       create a file 'foo_1996"DEFAULT_EXT"' for year = 1996, lat = 43.7279, lon = 10.2844 and timezone 1\n\n"
								"   SW_IN_POT_Calculator foo 1996 43.7279 10.2844 1 1\n\n"
								"       create an HOURLY file 'foo_1996"DEFAULT_EXT"' for year = 1996, lat = 43.7279, lon = 10.2844 and timezone 1\n\n"
								"   SW_IN_POT_Calculator foo 1996-2010 43.7279 10.2844 1\n\n"
								"       create a file 'foo_1996_2010"DEFAULT_EXT"' for year = 1996, lat = 43.7279, lon = 10.2844 and timezone 1\n\n"
								"   SW_IN_POT_Calculator foo 1996-2010 43.7279 10.2844 1 0 1\n\n"
								"       create singles files 'foo_XXXX"DEFAULT_EXT"' for lat = 43.7279, lon = 10.2844 and timezone 1 from year 1996 to year 2010\n\n"
								"   SW_IN_POT_Calculator foo 1996-2010 43.7279 10.2844 1 1 1\n\n"
								"       create singles HOURLY files 'foo_XXXX"DEFAULT_EXT"' for lat = 43.7279, lon = 10.2844 and timezone 1 from year 1996 to year 2010"
;
																						
/* errors messages */
extern const char err_out_of_memory[];
static const char err_bad_year[] = "bad year specified: %s. It must be in YYYY or YYYY-YYYY format\n";

/* */
int main(int argc, char *argv[]) {
	int i;
	int rows_count;
	int error;
	int ret;
	int year;
	int year_start;
	int year_end;
	int single;
	char buffer[MAX_FILENAME_SIZE+1+4+1+4+1+3+1]; /* 1+4+1+4+1+3+1 = _YYYY_YYYY.csv/0 */
	DD details;
	PREC *rpot;
	FILE *f;
	
	/* reset */
	ret = 1; /* defaults to err */
	single = 0;
	details.time_zones = NULL;
	details.timeres = HALFHOURLY_TIMERES;
	rpot = NULL;
	
	/* show text */
	puts(banner);
	
	/* check parameters */
	if ( argc < 6 ) {
		puts(msg_usage);
		goto quit;
	}
	
	/* get filename */
	i = strlen(argv[1]);
	if ( i > MAX_FILENAME_SIZE ) {
		printf("filename is too long. max %d chars.\n", MAX_FILENAME_SIZE);
		goto quit;
	}
	
	/* get year */
	i = strlen(argv[2]);
	if ( 4 == i ) {
		year_start = year_end = convert_string_to_int(argv[2], &error);
		if ( error ) {
			printf(err_bad_year, argv[2]);
			goto quit;
		}
		if ( year_start > year_end ) {
			/* swap */
			year_start ^= year_end;
			year_end ^= year_start;
			year_start ^= year_end;
		}
	} else if ( 9 == i ) {
		if ( 2 != sscanf(argv[2], "%d-%d", &year_start, &year_end) ) {
			printf(err_bad_year, argv[2]);
			goto quit;
		}
	} else {
		printf(err_bad_year, argv[2]);
		goto quit;
	}
	
	/* get lat */
	details.lat = convert_string_to_prec(argv[3], &error);
	if ( error ) {
		printf("bad latitude specified: %s\n", argv[3]);
		goto quit;
	}

	/* get lon */
	details.lon = convert_string_to_prec(argv[4], &error);
	if ( error ) {
		printf("bad longitude specified: %s\n", argv[4]);
		goto quit;
	}
	
	/* alloc memory for one timezone */
	details.time_zones = malloc(sizeof*details.time_zones);
	if ( ! details.time_zones ) {
		puts(err_out_of_memory);
		goto quit;
	}
	details.time_zones_count = 1;

	/* set defaults and get zone */
	details.time_zones->timestamp.MM = 1;
	details.time_zones->timestamp.DD = 1;
	details.time_zones->timestamp.hh = 0;
	details.time_zones->timestamp.mm = 30;
	details.time_zones->timestamp.ss = 0;
	details.time_zones->v = convert_string_to_prec(argv[5], &error);
	if ( error ) {
		printf("bad timezone specified: %s\n", argv[5]);
		goto quit;
	}

	/* summary */
	printf("year = %d", year_start);
		if ( year_start != year_end )
	printf("-%d", year_end); puts("");
	printf("latitude = %g\n", details.lat);
	printf("longitude = %g\n", details.lon);
	printf("timezone = %g\n", details.time_zones[0].v);

	/* hourly ? */
	if ( argc > 6 ) {
		i = convert_string_to_int(argv[6], &error);
		if ( ! error && (1 == i) ) {
			puts("hourly = 1");
			details.timeres = HOURLY_TIMERES;
		}
	}
	
	/* single files ? */
	if ( argc > 7 ) {
		i = convert_string_to_int(argv[7], &error);
		if ( ! error && (1 == i) ) {
			single = 1;
		}
	}
	
	if ( ! single ) {
		i = sprintf(buffer, "%s_%d", argv[1], year_start);
		if ( year_start != year_end )
			sprintf(buffer+i, "_%d", year_end);
		strcat(buffer, ".csv");
		f = fopen(buffer, "w");
		if ( ! f ) {
			printf("unable to create output file: %s\n", buffer);
			goto quit;
		}
		fprintf(f, "%s,SW_IN_POT\n", TIMESTAMP_HEADER);
	}
	
	for ( year = year_start; year <= year_end; ++year ) {
		rows_count = IS_LEAP_YEAR(year) ? 17568 : 17520;
		if ( HOURLY_TIMERES == details.timeres ) {
			rows_count /= 2;
		}

		details.year = year;
		details.time_zones->timestamp.YYYY = details.year;
	
		/* get rpot */
		printf("\ncomputing SW_IN_POT for year %d...", year);
		rpot = get_rpot(&details);
		if ( ! rpot ) goto quit;
			
		if ( single ) {
			sprintf(buffer, "%s_%d.csv", argv[1], year);
			f = fopen(buffer, "w");
			if ( ! f ) {
				printf("unable to create output file: %s\n", buffer);
				goto quit;
			}
			fprintf(f, "%s,SW_IN_POT\n", TIMESTAMP_HEADER);
		}

		for ( i = 0; i < rows_count; i++ ) {
			char* p;

			/* TIMESTAMP_START */
			p = timestamp_start_by_row_s(i, details.year, details.timeres);
			fputs(p, f);
			/* TIMESTAMP_END */
			p = timestamp_end_by_row_s(i, details.year, details.timeres);

			fprintf(f, ",%s,%g\n", p, rpot[i]);
		}
		
		if ( single ) {
			fclose(f);
			printf("ok\nfile %s created successfully\n\n", buffer);
		}
	}

	if ( ! single ) {
		fclose(f);
		printf("ok\nfile %s created successfully\n\n", buffer);
	}

	
	/* ok ! */
	ret = 0;
	
quit:
	if ( rpot ) free(rpot);
	if ( details.time_zones ) free(details.time_zones);
	return ret;
}
