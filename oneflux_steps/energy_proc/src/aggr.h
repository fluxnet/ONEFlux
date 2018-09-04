/*
	aggr.h

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef AGGR_H
#define AGGR_H

/* */
#include "dataset.h"

/* */
int aggr_by_days(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp);
int aggr_by_weeks(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp);
int aggr_by_months(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp);
int aggr_by_years(DATASET *const dataset, PREC *const ECBcfs, PREC *const ECBcfs_temp);

/* */
#endif /* AGGR_H */
