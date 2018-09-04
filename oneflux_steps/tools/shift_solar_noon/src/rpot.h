/*
	rpot.h

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef RPOT_H
#define RPOT_H

/* includes */
#include "types.h"

/* protypes */
int set_rpot(DATASET *const dataset);
void set_swin_vs_rpot_flag(DATASET *const dataset, const PREC rg_check, const PREC rpot_check, const PREC rg_limit);
void set_ppfd_vs_rpot_flag(DATASET *const dataset, const PREC rg_check, const PREC rpot_check, const PREC rg_limit);
int set_swin_vs_ppfd_flag(DATASET *const dataset, const PREC radiation_check_stddev, const PREC swin_vs_ppfd_threshold);

#endif /* rpot.h */
