/*
	types.h

	this file is part of energy_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef TYPES_H
#define TYPES_H

/* includes */
#include "../../common/common.h"

/* constants */
#define WINDOW_SIZE					30
#define WINDOW_SIZE_DAILY			14
#define WINDOW_SIZE_WEEKLY			4
#define WINDOW_SIZE_MONTHLY			2
#define MIN_WINDOW_SIZE				1
#define MAX_WINDOW_SIZE				90
#define MAX_WINDOW_SIZE_DAILY		50
#define WINDOW_SIZE_METHOD_2_3_HH	10
#define WINDOW_SIZE_METHOD_2_3_DD	10
#define SAMPLES_COUNT				1
#define MIN_SAMPLES_COUNT			1
#define MAX_SAMPLES_COUNT			24
#define QC_GF_THRESHOLD				0

/* enums */
enum {
	H_INPUT = 0,
	LE_INPUT,
	SWIN_INPUT,
	TA_INPUT,
	RH_INPUT,
	NETRAD_INPUT,
	G_INPUT,
	VPD_INPUT,

	/* flags */
	FLAG_SPIKE_H_INPUT,
	FLAG_QC_H_INPUT,
	FLAG_SPIKE_LE_INPUT,
	FLAG_QC_LE_INPUT,
			
	INPUT_VALUES
};

/* please do not change this order...otherwise randunc function will be messed up! */
enum {
	H = 0,
	LE,
	SWIN,
	TA,
	RH,
	NETRAD,
	G,
	VPD,
	DATASET_VALUES_TO_AGGR,

	LEcorr = DATASET_VALUES_TO_AGGR,
	LEcorr25,
	LEcorr75,
	Hcorr,
	Hcorr25,
	Hcorr75,

	p25,
	p50,
	p75,

	SWIN_QC_GF,
	TA_QC_GF,
	VPD_QC_GF,

	G_FILLED,

	DATASET_VALUES
};

/* */
enum {
	H_DATASET		= 1,
	LE_DATASET		= 2,

	H_LE_DATASET	= H_DATASET|LE_DATASET
};

/* */
enum {
	H_VALID			= 1,
	LE_VALID		= 2,
	G_VALID			= 4,
	NETRAD_VALID	= 8,
	ECBCF_ALL_VALID	= H_VALID|LE_VALID|G_VALID|NETRAD_VALID
};

/* please do not change this order...otherwise randunc function will be messed up! */
enum {
	H_INDEX = 0,
	LE_INDEX,
	G_INDEX,

	VARS_TO_FILL,

	ECBCF_INDEX = VARS_TO_FILL,

	SAMPLES
};

/* */
enum {
	ORIG = 0,
	REL_DIFF,
	ABS_DIFF,

	DIFF_VALUES
};

/* */
enum {
	diff_class_p5 = 0,
	diff_class_p10,
	diff_class_p25,
	diff_class_p50,
	diff_class_p75,
	diff_class_p90,
	diff_class_p95,

	DIFF_CLASS_PERCENTILES_COUNT
};

/* structures */
typedef struct {
	PREC value[DATASET_VALUES];
	char ecbcf_mask;
	int ecbcf_samples_count;
	int ecbcf_method;
	PREC rand[VARS_TO_FILL];
	int rand_samples_count[VARS_TO_FILL];
	int rand_method[VARS_TO_FILL];
} ROW;

/* */
typedef struct {
	PREC value[DATASET_VALUES];
	char mask;
	PREC quality[VARS_TO_FILL];
	PREC h_mean;	/* aggregated value starting from  hh */
	PREC le_mean;	/* aggregated value starting from  hh */
	PREC n;
	PREC ecbcf_samples_count;
	int ecbcf_method;
	PREC rand[VARS_TO_FILL];
	int rand_samples_count[VARS_TO_FILL];
} ROW_AGGR;

/* */
typedef struct {
	PREC value[DIFF_VALUES];
} DIFF;

/* */
#endif /* TYPES_H */
