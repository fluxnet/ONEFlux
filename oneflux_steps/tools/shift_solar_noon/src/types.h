/*
	types.h

	this file is part of qc_auto

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef TYPES_H
#define TYPES_H

/* precision */
#include "../../../common/common.h"

/* constants */
#define MARGINALS_WINDOW				5
#define MARGINALS_WINDOW_HOURLY			3
#define SPIKE_THRESHOLD_NEE				6.0
#define SPIKE_THRESHOLD_LE				100.0
#define SPIKE_THRESHOLD_H				100.0
#define SWIN_CHECK						50.0
#define RPOT_CHECK						200.0
#define SWIN_LIMIT						0.15
#define RADIATION_CHECK					11000
#define RADIATION_CHECK_STDDEV			5.0
#define SWINVSPPFD_THRESHOLD			0.01
#define USTAR_CHECK						9000
#define USTAR_CHECK_STDDEV				4.0
#define SPIKES_WINDOW					624
#define SPIKES_WINDOW_HOURLY			312
#define LOWVAR_THRESHOLD				0.001
#define STORAGE_RANGE_MAX				50.0
#define STORAGE_RANGE_MIN				-80.0
#define FCSTOR							TAU
#define	CO2TOP							QCFC	
#define CO2HEIGHT						QCH
#define GAP								QCLE
#define LOWVAR_MIN_VALUES				6
#define LOWVAR_STDDEV_VALUES			10
#define LOWVAR_WINDOW					624
#define SPIKE_THRESHOLD_1				6.0
#define SPIKE_CHECK_1					4.0
#define SPIKE_CHECK_2					5.5
#define SPIKE_CHECK_3					7.0
#define SPIKE_CHECK_1_RETURN			1
#define SPIKE_CHECK_2_RETURN			2
#define SPIKE_CHECK_3_RETURN			3
#define VPD_RANGE_MIN					-5
#define VPD_RANGE_MAX					120
#define LWIN_RANGE_MIN					50
#define LWIN_RANGE_MAX					700

/* enums */
enum {
	CO2_INPUT = 0,
	H2O_INPUT,
	ZL_INPUT,
	FC_INPUT,
	QCFC_INPUT,
	H_INPUT,
	QCH_INPUT,
	LE_INPUT,
	QCLE_INPUT,
	USTAR_INPUT,
	TR_INPUT,
	SB_INPUT,
	SC_INPUT,
	SW_INPUT,
	SA_INPUT,
	P_INPUT,
	SWOUT_INPUT,
	SWIN_INPUT,
	NETRAD_INPUT,
	SWDIF_INPUT,
	PPFD_INPUT,
	APAR_INPUT,
	TA_INPUT,
	PA_INPUT,
	TC_INPUT,
	TBOLE_INPUT,
	TS_INPUT,
	SWC_INPUT,
	G_INPUT,
	RH_INPUT,
	WD_INPUT,
	WS_INPUT,
	TAU_INPUT,
	LWIN_INPUT,
	NEE_INPUT,
	VPD_INPUT,
	itpVPD_INPUT,
	itpSWIN_INPUT,
	itpPPFD_INPUT,
	itpTA_INPUT,
	itpTS_INPUT,
	itpSWC_INPUT,
	itpP_INPUT,
	itpRH_INPUT,
	QCFOOT_INPUT,
	DATASET_VALUES,

	SWIN_ORIGINAL = DATASET_VALUES,
	PPFD_ORIGINAL,
	FCSTOR_INPUT,
	FCSTORTT_INPUT,
	HEIGHT_INPUT,
	RPOT_INPUT,
	NEE_SPIKE_INPUT,
	LE_SPIKE_INPUT,
	H_SPIKE_INPUT,
	NIGHT_INPUT,
	DAY_INPUT,		/* DAY must be after NIGHT, see spike.c */
	SC_NEGL_INPUT,
	TEMP_INPUT,

	INPUT_VALUES
};

/* */
enum {
	NEE_FLAG_INPUT,
	USTAR_FLAG_INPUT,
	MARGINAL_NEE_FLAG_INPUT,
	MARGINAL_LE_FLAG_INPUT,
	MARGINAL_H_FLAG_INPUT,
	SWIN_FROM_PPFD_FLAG_INPUT,
	SWIN_VS_RPOT_FLAG_INPUT,
	PPFD_VS_RPOT_FLAG_INPUT,
	SWIN_VS_PPFD_FLAG_INPUT,
	SPIKE_NEE_FLAG_INPUT,
	SPIKE_LE_FLAG_INPUT,
	SPIKE_H_FLAG_INPUT,
	QC2_NEE_FLAG_INPUT,
	QC2_LE_FLAG_INPUT,
	QC2_H_FLAG_INPUT,

	FLAG_INPUT_VALUES
};

/* */
enum {
	LWIN_CALC = 0,
	FPAR,
	CLOUD_COVER,
	R_CLOUD,
	ESAT,
	VP,
	epsA,

	METEORA_VALUES
};
	
/* structures */
typedef struct {
	char *name;
	int x;
	int y;
	int z;
	int attr;
} VAR;

/* */
typedef struct {
	int start;
	int end;
} PERIOD;

/* */
typedef struct {
	PREC value1;
	PREC value2;
	int index;
} SPIKE;

/* */
typedef struct {
	PREC *value;
} ROW;

/* */
typedef struct {
	PREC *value;
} FLAG;

/* */
typedef struct {
	PREC value[METEORA_VALUES];
} METEORA;

/* */
typedef struct {
	DD *details;

	int leap_year;

	VAR *header;
	int columns_count;

	ROW *rows;
	int rows_count;

	FLAG *flags;
	int flags_count;

	int *missings;

	METEORA *meteora;

	int has_timestamp_start;
	int has_timestamp_end;
} DATASET;

/* */
#endif /* COMMON_H */
