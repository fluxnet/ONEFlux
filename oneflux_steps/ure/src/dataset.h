/*
	dataset.h

	this file is part of ure - Uncertainty and References Extraction

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
} YEAR;

typedef struct {
	DD *details;
	YEAR *years;
	int years_count;
	PERCENTILE *percentiles_c;
	PERCENTILE *percentiles_y;
	int rows_count;
	int hourly;
	SR *srs;
} DATASET;

/* prototypes */
void free_datasets(DATASET *datasets, const int datasets_count);
DATASET *get_datasets(const char *const path, const int author_index, const int type_index, int *const datasets_count);
int compute_datasets(DATASET *const datasets, const int datasets_count, const int author_index, const int type_index);
int compute_sr_datasets(DATASET *const datasets, const int datasets_count, const int author_index, const int type_index);

/* */
#endif /* DATASET_H */
