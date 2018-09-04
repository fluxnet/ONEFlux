/*
	bootstrapping.h

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef BOOTSTRAPPING_H
#define BOOTSTRAPPING_H

/* includes */
#include "types.h"

/* prototypes */
int bootstrapping(	FILE *const f,
					const ROW_FULL_DETAILS *const rows, const int rows_count, const int bootstrapping_count,
					PREC *const threshold_forward_mode_container,
					PREC *const threshold_forward_mode_2_container,
					PREC *const threshold_forward_mode_3_container,
					PREC *const threshold_back_mode_container,
					PREC *const threshold_back_mode_2_container,
					PREC *const threshold_back_mode_3_container,
					PREC *const threshold_high_forward_mode_container,
					PREC *const threshold_high_forward_mode_2_container,
					PREC *const threshold_high_forward_mode_3_container,
					PREC *const threshold_high_back_mode_container,
					PREC *const threshold_high_back_mode_2_container,
					PREC *const threshold_high_back_mode_3_container,
					PREC *const threshold_valid_forward_mode_container,
					PREC *const threshold_valid_forward_mode_2_container,
					PREC *const threshold_valid_forward_mode_3_container,
					PREC *const threshold_valid_back_mode_container,
					PREC *const threshold_valid_back_mode_2_container,
					PREC *const threshold_valid_back_mode_3_container);

#endif /* BOOTSTRAPPING_H */
