/*
	mds_vars.h

	this file is part of meteo_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef MDS_VARS_H
#define MDS_VARS_H

#include "../../common/common.h"

enum {
	MDS_VAR_TOLERANCE_MIN = 0
	, MDS_VAR_TOLERANCE_MAX

	, MDS_VAR_TOLERANCES_COUNT
};

enum {
	MDS_VAR_OOR_MIN = 0
	, MDS_VAR_OOR_MAX

	, MDS_VAR_OORS_COUNT
};

enum {
	MDS_VAR_TO_FILL = 0
	, MDS_VAR_DRIVER_1
	, MDS_VAR_DRIVER_2A
	, MDS_VAR_DRIVER_2B

	, MDS_VARS_COUNT
};

typedef struct 
{
	/*
		DO NOT CHANGE ORDER
		ADJUSTED FOR BYTES PADDING

		PLEASE NOTE THAT, IN THIS WAY (tolerances[MDS_VARS_COUNT] and oor[MDS_VARS_COUNT])
		WE HAVE TOLERANCES FOR VAR_TO_FILL TOO BUT,
		OF COURSE, THEY WILL BE INVALID_VALUE AND UNUSED
	*/

	PREC tolerances[MDS_VARS_COUNT][MDS_VAR_TOLERANCES_COUNT];
	PREC oors[MDS_VARS_COUNT][MDS_VAR_OORS_COUNT];
	int columns[MDS_VARS_COUNT];
	const char* name[MDS_VARS_COUNT];

} MDS_VAR;

typedef struct 
{
	MDS_VAR* vars;
	int count;

} MDS_VARS;

void Mds_Var_Init(MDS_VAR* var);
void Mds_Var_Clear(MDS_VAR* var);

void Mds_Vars_Init(MDS_VARS* vars);
void Mds_Vars_Clear(MDS_VARS* vars);

#endif /* MDS_VARS_H */
