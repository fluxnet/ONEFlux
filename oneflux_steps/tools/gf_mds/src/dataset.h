/*
	dataset.h

	this file is part of gf_mds

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: darpap at unitus dot it
*/

#ifndef DATASET_H
#define DATASET_H

/* includes */
#include "types.h"

/* prototypes */
ROW *import_dataset(const LIST *const list, const int count, int *const rows_count);
void free_details_list(DD **details_list, const int count);

#endif /* DATASET_H */
