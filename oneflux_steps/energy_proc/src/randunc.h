/*
	randunc.h

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef RANDUNC_H
#define RANDUNC_H

/* includes */
#include "dataset.h"

/* prototypes */
void random_method_1(DATASET *const dataset, const int to_rand_index);
int random_method_2(DATASET *const dataset, const int to_rand_index);

/* */
#endif /* RANDUNC_H */

