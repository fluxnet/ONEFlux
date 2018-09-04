/*
	types.h

	this file is part of ure - Uncertainty and References Extraction

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef TYPES_H
#define TYPES_H

/* includes */
#include "../../common/common.h"

/* constants */
#define TOKEN_LENGTH_MAX		32
#define ROWS_MIN_MIN			0
#define ROWS_MIN				3000
#define ROWS_MIN_MAX			10000
#define PERCENTILES_COUNT_1		7
#define PERCENTILES_COUNT_2		41
#define YEAR_LEN				5		/* INCLUDING TERMINATING NULL */
#define BOOTSTRAPPING_TIMES		100
#define NEE_MATRIX_TEMP_COLUMNS	BOOTSTRAPPING_TIMES*3

/* enums */
enum {
	TYPE_GPP = 0,
	TYPE_RECO,

	TYPES_SUFFIX
};

/* enum */
enum {
	AUTHOR_NT = 0,
	AUTHOR_DT,
	AUTHOR_SR,

	AUTHORS_SUFFIX
};

/* */
enum {
	FWD2 = 0,
	BARR,

	METHODS
};

/* */
enum {
	HH_TIMERES = 0,
	DD_TIMERES,
	WW_TIMERES,
	MM_TIMERES,
	YY_TIMERES,

	TIMERES
};

/* */
enum {
	HH_Y = 0,
	DD_Y,
	WW_Y,
	MM_Y,
	YY_Y,

	HH_C,
	DD_C,
	WW_C,
	MM_C,
	YY_C,

	TYPES
};

/* */
enum {
	NEE_VALUE = 0,
	VPD_VALUE,
	RPOT_VALUE,
	USTAR_VALUE,
	TA_VALUE,
	RH_VALUE,
	SWIN_VALUE,

	REQUIRED_DATASET_VALUES,

	YEAR_VALUE = REQUIRED_DATASET_VALUES,

	DATASET_VALUES
};

/* */
enum {
	NEE_REF_Y_UNC = 0,
	NEE_UST50_Y_UNC,
	NEE_REF_C_UNC,
	NEE_UST50_C_UNC,

	UNC_QC_VALUES,

	SWIN_UNC = UNC_QC_VALUES,
	TA_UNC,
	VPD_UNC,

	UNC_VALUES
};

/* */
enum {
	NEE_REF_Y = 0,
	NEE_UST50_Y,
	NEE_REF_C,
	NEE_UST50_C,

	NIGHT_QC_VALUES,

	NEE_REF_Y_RAND = NIGHT_QC_VALUES,
	NEE_UST50_Y_RAND,
	NEE_REF_C_RAND,
	NEE_UST50_C_RAND,

	NIGHT_RAND_VALUES,

	NEE_05_Y = NIGHT_RAND_VALUES,
	NEE_16_Y,
	NEE_25_Y,
	NEE_50_Y,
	NEE_75_Y,
	NEE_84_Y,
	NEE_95_Y,

	NEE_05_QC_Y,
	NEE_16_QC_Y,
	NEE_25_QC_Y,
	NEE_50_QC_Y,
	NEE_75_QC_Y,
	NEE_84_QC_Y,
	NEE_95_QC_Y,

	NEE_05_C,
	NEE_16_C,
	NEE_25_C,
	NEE_50_C,
	NEE_75_C,
	NEE_84_C,
	NEE_95_C,

	NEE_05_QC_C,
	NEE_16_QC_C,
	NEE_25_QC_C,
	NEE_50_QC_C,
	NEE_75_QC_C,
	NEE_84_QC_C,
	NEE_95_QC_C,
	
	NIGHT_VALUES,
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

/* */
typedef struct {
	PREC value[DATASET_VALUES];
	int assigned;
} ROW;

/* */
typedef struct {
	ROW row;
	GF_ROW gf_row;
} ROW_COPY;

/* */
typedef struct {
	PREC night[NIGHT_VALUES];
	PREC night_d;						/* beware: this is NIGHT_RANDUNC_N */
	PREC night_total;					/* beware: this is NIGHT_D */
	PREC night_std[NIGHT_QC_VALUES];
	PREC night_qc[NIGHT_RAND_VALUES];
	PREC day[NIGHT_VALUES];
	PREC day_d;							/* beware: this is DAY_RANDUNC_N */
	PREC day_total;						/* beware: this is DAY_D */
	PREC day_std[NIGHT_QC_VALUES];
	PREC day_qc[NIGHT_RAND_VALUES];
	int night_d_rand[NIGHT_QC_VALUES];
	int day_d_rand[NIGHT_QC_VALUES];
} ROW_NIGHT;

/* */
typedef struct {
	PREC value[PERCENTILES_COUNT_2];
	PREC hat[PERCENTILES_COUNT_2];
	PREC qc[PERCENTILES_COUNT_2];
} MATRIX;

/* */
typedef struct {
	PREC value;
	PREC qc;
} NEE_QC;

/* */
typedef struct {
	PREC value[PERCENTILES_COUNT_1];
	PREC mean;
	PREC std_err;
} P_MATRIX;

/* */
typedef struct {
	PREC value[PERCENTILES_COUNT_2-1]; /* removing 50% */
} ME;

/* */
typedef struct {
	PREC value[PERCENTILES_COUNT_2];
} PERCENTILE_Y;

/* */
typedef struct {
	PREC value[PERCENTILES_COUNT_2];
} PERCENTILE;

/* */
typedef struct {
	PREC value[DIFF_VALUES];
} DIFF;

/* */
typedef struct {
	char mask;
	PREC value[UNC_VALUES];
	int qc[UNC_QC_VALUES];
	PREC rand[UNC_VALUES];
	PREC similiar;
	int samples_count[UNC_VALUES];
	int method[UNC_VALUES];
} RAND_UNC_ROW;

/* */
typedef struct {
	int value[PERCENTILES_COUNT_2];
} NEE_FLAG;

/* */
typedef struct {
	PREC reco;
	int qc;
	int tn;
	PREC reco_n;
} SR;

/* */
#endif /* TYPES_H */
