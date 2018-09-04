/*
	dataset.h

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef DATASET_H
#define DATASET_H

/* includes */
#include "types.h"

/* prototypes */
UT *import_dataset(const LIST *const filelist, const int list_count);
void free_ut(UT *ut);

#endif /* DATASET_H */
