/*
	dataset.h

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef DATASET_H
#define DATASET_H

/* includes */
#include "types.h"

/* structures */
typedef struct {
	int year;
	int exist;
	char filename[BUFFER_SIZE];
	char hle;
} YEAR;

/* */
typedef struct {
	DD *details;
	YEAR *years;
	int years_count;
	ROW *rows;
	GF_ROW *gf_rows[VARS_TO_FILL];
	int rows_count;
	ROW_AGGR *rows_aggr;
	int rows_aggr_count;
	ROW_AGGR *rows_daily;	/* dd */
	ROW_AGGR *rows_temp;	/* ww-mm-yy */
	int rows_temp_count;
	int *indexes;
	int indexes_count;
	int hourly;
} DATASET;

/* prototypes */
DATASET *get_datasets(const char *const path, const char *ext, int *const datasets_count);
int compute_datasets(DATASET *const datasets, const int datasets_count);
void free_datasets(DATASET *datasets, const int datasets_count);

/* */
#endif /* DATASET_H */