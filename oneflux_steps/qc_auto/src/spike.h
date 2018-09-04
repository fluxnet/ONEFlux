/*
	spike.h

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef SPIKE_H
#define SPIKE_H

/* includes */
#include "types.h"

/* prototypes */
int set_night_and_day(DATASET *const dataset);
int set_spikes(DATASET *const dataset, const char *const var_name, const PREC zfc, const char *const flag_name, const int result, const int window);
void set_spikes_2(DATASET *const dataset, const char *const var_name, const char *const flag_name, const PREC threshold);

/* */
#endif /* SPIKE_H */
