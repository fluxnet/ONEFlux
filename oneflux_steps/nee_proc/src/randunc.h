/*
	randunc.h

	this file is part of nee_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef RANDUNC_H
#define RANDUNC_H

/* includes */
#include "dataset.h"

/* prototypes */
void random_method_1(RAND_UNC_ROW *const unc_rows, const int unc_rows_count, const int to_rand_index, const int hourly);
int random_method_2(RAND_UNC_ROW *const unc_rows, const int unc_rows_count, const int to_rand_index, const int hourly);

/* */
#endif /* RANDUNC_H */

