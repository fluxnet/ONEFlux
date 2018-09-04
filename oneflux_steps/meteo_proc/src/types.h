/*
	types.h

	this file is part of meteo_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef TYPES_H
#define TYPES_H

/* includes */
#include "../../common/common.h"

/* enums */
enum {
	TA_ERA,
	PA_ERA,
	VPD_ERA,
	WS_ERA,
	PRECIP_ERA,
	SW_IN_ERA,
	LW_IN_ERA,
	LW_IN_CALC_ERA,
	
	ERA_REQUIRED_VALUES,

	CO2_MET = ERA_REQUIRED_VALUES,
	TA_MET,
	VPD_MET,
	PRECIP_MET,
	WS_MET,
	SW_IN_MET,
	LW_IN_MET,
	PA_MET,
	RPOT_MET,

	MET_VALUES = 9,

	TA_FILLED = RPOT_MET + 1,
	VPD_FILLED,
	SW_IN_FILLED,
	LW_IN_FILLED,
	CO2_FILLED,

	TA_QC,
	VPD_QC,
	SW_IN_QC,
	LW_IN_QC,
	CO2_QC,

	TA_M,
	TA_M_QC,
	VPD_M,
	VPD_M_QC,
	SW_IN_M,
	SW_IN_M_QC,
	LW_IN_M,
	LW_IN_M_QC,
	LW_IN_CALC_M,
	LW_IN_CALC_M_QC,
	PA_M,
	PA_M_QC,
	PRECIP_M,
	PRECIP_M_QC,
	WS_M,
	WS_M_QC,

	TA_F_NIGHT,
	TA_F_NIGHT_STD,
	TA_F_NIGHT_QC,
	TA_F_DAY,
	TA_F_DAY_STD,
	TA_F_DAY_QC,

	TA_M_NIGHT,
	TA_M_NIGHT_STD,
	TA_M_NIGHT_QC,
	TA_M_DAY,
	TA_M_DAY_STD,
	TA_M_DAY_QC,

	TA_ERA_NIGHT,
	TA_ERA_NIGHT_STD,
	TA_ERA_DAY,
	TA_ERA_DAY_STD,

	FPAR,
	CLOUD_COVER,
	R_CLOUD,
	ESAT,
	VP,
	epsA,
	LW_IN_CALC,
	LW_IN_CALC_QC,

	TEMP,

	VALUES
};

/* */
typedef struct {
	char name[BUFFER_SIZE];
	int type;
} FILE_N_T;

/* */
typedef struct {
	char mask;
	PREC value[VALUES];
	PREC similiar;
	PREC stddev;
	PREC nights_count;
	PREC days_count;
} ROW;

/* */
typedef struct {
	PREC value;
	PREC filled;
	PREC qc;
} PROFILE;

/* */
#endif /* TYPES_H */
