/*
	mds_vars.c

	this file is part of meteo_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include "mds_vars.h"
#include <stdlib.h> /* for free */

void Mds_Var_Init(MDS_VAR* var) {
	int i;
	for ( i = MDS_VAR_TO_FILL; i < MDS_VARS_COUNT; ++i ) {
		var->name[i] = NULL;
		var->columns[i] = -1;
		var->tolerances[i][MDS_VAR_TOLERANCE_MIN] = INVALID_VALUE;
		var->tolerances[i][MDS_VAR_TOLERANCE_MAX] = INVALID_VALUE;
		var->oors[i][MDS_VAR_OOR_MIN] = INVALID_VALUE;
		var->oors[i][MDS_VAR_OOR_MAX] = INVALID_VALUE;
	}
}

void Mds_Var_Clear(MDS_VAR* var) {
	int i;
	for ( i = MDS_VAR_TO_FILL; i < MDS_VARS_COUNT; ++i ) {
		if ( var->name[i] ) {
			free((void*)var->name[i]);
		}
	}
	Mds_Var_Init(var);
}

/*
void Mds_Var_Free(MDS_VAR* var) {
	Mds_Var_Clear(var);
	free(var);
}
*/

void Mds_Vars_Init(MDS_VARS* vars) {
	vars->vars = NULL;
	vars->count = 0;
}

void Mds_Vars_Clear(MDS_VARS* vars) {
	int i;
	for ( i = 0; i < vars->count; ++i ) {
		Mds_Var_Clear(&vars->vars[i]);
	}
	free(vars->vars);
	Mds_Vars_Init(vars);
}

/*
void Mds_Vars_Free(MDS_VARS* vars) {
	Mds_Vars_Clear(vars);
	free(vars);
}
*/
