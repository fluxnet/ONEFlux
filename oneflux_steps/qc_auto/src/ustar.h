/*
	ustar.h

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef USTAR_H
#define USTAR_H

/* includes */
#include "types.h"

/* prototypes */
int set_ustar_flag(DATASET *const dataset, const PREC ustar_check_stddev);

#endif /* USTAR_H */
