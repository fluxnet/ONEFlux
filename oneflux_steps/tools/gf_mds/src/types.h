/*
	types.h

	this file is part of gf_mds

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: darpap at unitus dot it
*/

#ifndef TYPES_H
#define TYPES_H

/* includes */
#include "../../../common/common.h"

/* defines */
#define DTIME_TO_ROW(x)					(int)(((x*48)-48)+0.5)
#define DTIME_TO_ROW_HOURLY(x)			(int)(((x*24)-24)+0.5)

/* enums */
enum {
	GF_TOFILL = 0,
	GF_SWIN,
	GF_TA,
	GF_VPD,
	GF_ROW_INDEX,

	GF_REQUIRED_DATASET_VALUES,

	GF_TOKENS = GF_REQUIRED_DATASET_VALUES,
};

/* structures */
typedef struct {
	PREC value[GF_REQUIRED_DATASET_VALUES];
	int assigned;
} ROW;

/* */
#endif /* TYPES_H */
