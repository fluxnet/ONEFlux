/*
	dataset.h

	this file is part of meteo_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef DATASET_H
#define DATASET_H

/* includes */
#include "types.h"
#include "mds_vars.h"

/* enumerations */
enum {
	ERA_FILES = 0,
	MET_FILES,

	FILES_TYPE
};

/* structures */
typedef struct {
	int year;
	int timeres;
	int exist[FILES_TYPE];
	char filename[BUFFER_SIZE][FILES_TYPE];
} YEAR;

/* */
typedef struct {
	char site[SITE_LEN];

	YEAR *years;
	int years_count;

	double lat;
	double lon;
	TIME_ZONE *time_zones;
	int time_zones_count;
	int timeres;

	ROW *rows;
	int rows_count;

	ROW *rows_daily;
	int rows_daily_count;

	ROW *rows_aggr;
	int rows_aggr_count;

	char *stat;

	int hourly;

	PROFILE **tss;
	PROFILE **swcs;

	PROFILE **tss_daily;
	PROFILE **swcs_daily;

	PROFILE **tss_aggr;
	PROFILE **swcs_aggr;

	int *ts_profiles;
	int *swc_profiles;
	
	int ts_count;
	int swc_count;	
} DATASET;

/* prototypes */
void free_datasets(DATASET *datasets, const int datasets_count);
DATASET *get_datasets(int *const datasets_count);
int compute_datasets(DATASET *const datasets, const int datasets_count, MDS_VARS* mds_vars);

/* */
#endif /* DATASET_H */
