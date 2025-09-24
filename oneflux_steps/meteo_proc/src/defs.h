/*
	defs.h

	this file is part of meteo_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef DEFS_H
#define DEFS_H

enum {
	TA_DEF_VAR,
	SW_IN_DEF_VAR,
	LW_IN_DEF_VAR,
	VPD_DEF_VAR,
	CO2_DEF_VAR,
	TS_DEF_VAR,
	SWC_DEF_VAR,

	DEF_VARS_COUNT
};

extern const char* sz_defs[DEF_VARS_COUNT];

#endif /* DEFS_H */
