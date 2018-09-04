/*
	dataset.h

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef DATASET_H
#define DATASET_H

/* includes */
#include "types.h"

/* prototypes */
DATASET *import_dataset(const char *const filename);
void free_dataset(DATASET *dataset);
int get_var_index(const DATASET *const dataset, const char *const name);
int get_flag_index(const DATASET *const dataset, const char *const name);
int *get_var_indexes(const DATASET *const dataset, const char *const name, int *const count);
int add_var_to_dataset(DATASET *const dataset, const char *const var);

/* */
#endif /* DATASET_H */
