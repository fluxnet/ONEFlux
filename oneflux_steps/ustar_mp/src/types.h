/*
	types.h

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef TYPES_H
#define TYPES_H

/* precision */
#include "../../common/common.h"

/* constants */
#define TOKEN_LENGTH_MAX				32
#define	SWIN_FOR_NIGHT					10.0
#define WINDOWS_SIZE_FOR_FORWARD_MODE	10
#define WINDOWS_SIZE_FOR_FORWARD_MODE_2	10
#define WINDOWS_SIZE_FOR_FORWARD_MODE_3	10
#define WINDOWS_SIZE_FOR_BACK_MODE		6
#define WINDOWS_SIZE_FOR_BACK_MODE_2	6
#define WINDOWS_SIZE_FOR_BACK_MODE_3	6
#define MAX_WINDOW_SIZE_FOR_BACK_MODE	10
#define MAX_WINDOW_SIZE_FOR_BACK_MODE_2	10
#define MAX_WINDOW_SIZE_FOR_BACK_MODE_3	10
#define MIN_VALUE_PERIOD				3000		/* min values for compute u* threshold */
#define MIN_VALUE_SEASON				160			/* min for seasons */
#define TA_CLASS_MIN_SAMPLE				100
#define CORRELATION_CHECK				0.5
#define PERCENTILE_CHECK				90
#define FIRST_USTAR_MEAN_CHECK			0.2
#define USTAR_THRESHOLD_NOT_FOUND		10.0
#define THRESHOLD_CHECK					1.0
#define TA_CLASSES_COUNT				7
#define USTAR_CLASSES_COUNT				20
#define BOOTSTRAPPING_TIMES				100
#define PERCENTILES_COUNT				9
#define TABSPACE						15

/* enumerations */
enum {
	TIME_STAMP = 0,
	NEE,
	TA,
	USTAR,
	SWIN,

	INPUT_VALUES,
};

/* */
enum {
	NEE_VALID	= 1,
	TA_VALID	= 2,
	USTAR_VALID	= 4,
	ALL_VALID	= NEE_VALID|TA_VALID|USTAR_VALID
};

/* structures */
typedef struct {
	int *month;
	int count;
} SEASONS_GROUP;

/* */
typedef struct {
	PREC value[INPUT_VALUES];
	int night;
	int month_per_group;
	TIMESTAMP timestamp;
	int flags;
} ROW_FULL_DETAILS;

/* */
typedef struct {
	char name[PATH_SIZE];
	int flags;
	int rows_count;
} DATASET;

/* */
typedef struct {
	DD **details;
	int details_count;
	ROW_FULL_DETAILS *rows_full_details;
	int rows_full_details_count;
	DATASET *datasets;
	int datasets_count;
	int can_be_grouped;
} UT;

/* */
typedef struct {
	PREC value[INPUT_VALUES];
	int index;
} ROW;

/* */
typedef struct {
	int start;
	int end;
} WINDOW;

#endif /* TYPES_H */
