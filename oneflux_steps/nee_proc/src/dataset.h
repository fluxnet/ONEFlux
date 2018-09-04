/*
	dataset.h

	this file is part of nee_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef DATASET_H
#define DATASET_H

/* includes */
#include "types.h"

/* enums */
enum {
	USTAR_NO_METHOD = 0,		/* 0 */
	USTAR_MP_METHOD = 1 << 0,	/* 1 */
	USTAR_CP_METHOD = 1 << 1,	/* 2 */
};

/* structures */
typedef struct {
	int year;
	int exist;
} YEAR;

/* */
typedef struct {
	int year;
	int method;
} USTAR_METHOD_NOT_APPLIED;

typedef struct {
	DD *details;
	YEAR *years;
	int years_count;
	ROW *rows;
	GF_ROW *gf_rows;
	int rows_count;
	USTAR_METHOD_NOT_APPLIED *umna;
	int umna_count;
} DATASET;

/* prototypes */
void free_datasets(DATASET *datasets, const int datasets_count);
DATASET *get_datasets(const char *const path, int *const datasets_count);
int compute_datasets(DATASET *const datasets, const int datasets_count);

/* */
#endif /* DATASET_H */
