/*
	ecbcf.h

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef ECBCF_H
#define ECBCF_H

/* includes */
#include "types.h"
#include "dataset.h"

/* constants */
#define FACTOR 1.5

/* enums */
enum {
	FIRST = 0,
	SECOND,
	THIRD,

	METHODS
};

 /* defines */
#define ECBCF(netrad,g,h,le)	(((netrad)-(g))/((h)+(le)))

/* prototypes */
int ecbcf_temp_hh(DATASET *const dataset, PREC *const ecbcfs, PREC *const ecbcfs_temp, PREC *const temp);
int ecbcf_hh(DATASET *const dataset, const int current_row, PREC *const ECBcfs, PREC *const ECBcfs_temp, PREC *const temp, const int window_size, const int windows_size_alt);
int ecbcf_dd(DATASET *const dataset, const int current_row, PREC *const ECBcfs, PREC *const ECBcfs_temp, PREC *const temp, const int window_size, const int window_size_alt);
int ecbcf_ww(DATASET *const dataset, const int current_row, PREC *const ECBcfs, const int window_size);
int ecbcf_mm(DATASET *const dataset, const int current_row, PREC *const ECBcfs, const int window_size);
int ecbcf_yy(DATASET *const dataset, const int current_row, PREC *const ECBcfs);

/* */
#endif /* ECBCF_H */
