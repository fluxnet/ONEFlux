/*
	ustar.h

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef USTAR_H
#define USTAR_H

/* includes */
#include "types.h"

/*  prototypes */
int ustar_threshold(ROW *const rows, const int rows_count, const int days,
					unsigned char *const threshold_forward_mode_percentiled,
					unsigned char *const threshold_forward_mode_2_percentiled,
					unsigned char *const threshold_forward_mode_3_percentiled,
					unsigned char *const threshold_back_mode_percentiled,
					unsigned char *const threshold_back_mode_2_percentiled,
					unsigned char *const threshold_back_mode_3_percentiled,
					PREC *const threshold_forward_mode_container,
					PREC *const threshold_forward_mode_2_container,
					PREC *const threshold_forward_mode_3_container,
					PREC *const threshold_back_mode_container,
					PREC *const threshold_back_mode_2_container,
					PREC *const threshold_back_mode_3_container,
					PREC *const ustar_mean,
					PREC *const fx_mean,
					WINDOW *const ta_window,
					WINDOW *const ustar_window);

PREC median_ustar_threshold(const PREC *const values, const int element, const int season, int *const p_error);

#endif /* USTAR_H */
