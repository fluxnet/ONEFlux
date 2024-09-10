/*
	dataset.c

	this file is part of nee_proc

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <assert.h>
#include "dataset.h"
#include "randunc.h"
#include "info_hh.h"
#include "info_dd.h"
#include "info_ww.h"
#include "info_mm.h"
#include "info_yy.h"
#include "info_utem.h"
#include "info_model_efficiency.h"

/* enum */
typedef enum {
	HH_TR = 0,
	DD_TR,
	WW_TR,
	MM_TR,
	YY_TR,

	TRS
} eTimeRes;


/* externs */
extern char *qc_auto_files_path;
extern char *ustar_mp_files_path;
extern char *ustar_cp_files_path;
extern char *meteo_files_path;
extern char *output_files_path;
extern int no_rand_unc;
extern int use_met_gf;
extern int mef_save;
extern int percentiles_save;
extern int compute_nee_flags;
extern int qc_gf_threshold;

/* constants */
#define QC_AUTO_FILENAME_LEN		23		/* including extension */
#define USTAR_MP_SKIP				219
#define	VALUES_PER_CLASSES_COUNT	100
static const float percentiles_test_1[PERCENTILES_COUNT_1] = { 5, 16, 25, 50, 75, 84, 95 };
static const float percentiles_test_2[PERCENTILES_COUNT_2] = {
																1.25,
																3.75,
																6.25,
																8.75,
																11.25,
																13.75,
																16.25,
																18.75,
																21.25,
																23.75,
																26.25,
																28.75,
																31.25,
																33.75,
																36.25,
																38.75,
																41.25,
																43.75,
																46.25,
																48.75,
																51.25,
																53.75,
																56.25,
																58.75,
																61.25,
																63.75,
																66.25,
																68.75,
																71.25,
																73.75,
																76.25,
																78.75,
																81.25,
																83.75,
																86.25,
																88.75,
																91.25,
																93.75,
																96.25,
																98.75,
																50
};
const int days_per_month[MONTHS] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

/* strings */
static const char dataset_delimiter[] = ",\r\n";
static const char *methods[METHODS] = { "ustar_mp", "ustar_cp" };
static const char output_file_hh[] = "%s%s_NEE_hh.csv";
static const char output_file_dd[] = "%s%s_NEE_dd.csv";
static const char output_file_ww[] = "%s%s_NEE_ww.csv";
static const char output_file_mm[] = "%s%s_NEE_mm.csv";
static const char output_file_yy[] = "%s%s_NEE_yy.csv";
static const char header_file_hh[] = "%s,DTIME,night,";
static const char header_file_dd[] = "%s,DOY,";
static const char header_file_ww[] = "%s,WEEK,";
static const char header_file_mm[] = "%s,";
static const char header_file_yy[] = "%s,";
#if 0 /* new naming convention */
static const char *types[TYPES] = { "hh_vut",
									"dd_vut",
									"ww_vut",
									"mm_vut",
									"yy_vut",
									"hh_cut",
									"dd_cut",
									"ww_cut",
									"mm_cut",
									"yy_cut"
};
#else
static const char *types[TYPES] = { "hh_y",
									"dd_y",
									"ww_y",
									"mm_y",
									"yy_y",
									"hh_c",
									"dd_c",
									"ww_c",
									"mm_c",
									"yy_c"
};
#endif

static const char *input_columns_tokens[INPUT_VALUES] = { "NEE", "VPD", "SW_IN_POT", "USTAR", "TA", "SW_IN" };

#if 0 /* new naming convention */
static const char output_var_1_rand_unc_hh[] =	"NEE_VUT_REF,NEE_VUT_REF_QC,"
												"NEE_VUT_REF_RANDUNC,NEE_VUT_REF_RANDUNC_METHOD,NEE_VUT_REF_RANDUNC_N,"
												"NEE_VUT_REF_JOINTUNC,"
												"NEE_VUT_USTAR50,NEE_VUT_USTAR50_QC,"
												"NEE_VUT_USTAR50_RANDUNC,NEE_VUT_USTAR50_RANDUNC_METHOD,NEE_VUT_USTAR50_RANDUNC_N,"
												"NEE_VUT_USTAR50_JOINTUNC,"
												"NEE_VUT_MEAN,NEE_VUT_MEAN_QC,"
												"NEE_VUT_SE,";
static const char output_var_2_rand_unc_hh[] =	",NEE_CUT_REF,NEE_CUT_REF_QC,"
												"NEE_CUT_REF_RANDUNC,NEE_CUT_REF_RANDUNC_METHOD,NEE_CUT_REF_RANDUNC_N,"
												"NEE_CUT_REF_JOINTUNC,"
												"NEE_CUT_USTAR50,NEE_CUT_USTAR50_QC,"
												"NEE_CUT_USTAR50_RANDUNC,NEE_CUT_USTAR50_RANDUNC_METHOD,NEE_CUT_USTAR50_RANDUNC_N,"
												"NEE_CUT_USTAR50_JOINTUNC,"
												"NEE_CUT_MEAN,NEE_CUT_MEAN_QC,"
												"NEE_CUT_SE,";
static const char output_var_1[] =	"NEE_VUT_REF,NEE_VUT_REF_QC,"
									"NEE_VUT_USTAR50,NEE_VUT_USTAR50_QC,"
									"NEE_VUT_MEAN,NEE_VUT_MEAN_QC,"
									"NEE_VUT_SE,";
static const char output_var_2[] =	",NEE_CUT_REF,NEE_CUT_REF_QC,"
									"NEE_CUT_USTAR50,NEE_CUT_USTAR50_QC,"
									"NEE_CUT_MEAN,NEE_CUT_MEAN_QC,"
									"NEE_CUT_SE,";

static const char output_var_1_rand_unc[] =	"NEE_VUT_REF,NEE_VUT_REF_QC,"
											"NEE_VUT_REF_RANDUNC,NEE_VUT_REF_JOINTUNC,"
											"NEE_VUT_USTAR50,NEE_VUT_USTAR50_QC,"
											"NEE_VUT_USTAR50_RANDUNC,NEE_VUT_USTAR50_JOINTUNC,"
											"NEE_VUT_MEAN,NEE_VUT_MEAN_QC,"
											"NEE_VUT_SE,";
static const char output_var_2_rand_unc[] =	",NEE_CUT_REF,NEE_CUT_REF_QC,"
											"NEE_CUT_REF_RANDUNC,NEE_CUT_REF_JOINTUNC,"
											"NEE_CUT_USTAR50,NEE_CUT_USTAR50_QC,"
											"NEE_CUT_USTAR50_RANDUNC,NEE_CUT_USTAR50_JOINTUNC,"
											"NEE_CUT_MEAN,NEE_CUT_MEAN_QC,"
											"NEE_CUT_SE,";

static const char header_file_night_no_rand_unc[] = ",NIGHT_D,DAY_D,";
static const char header_file_night[] = ",NIGHT_D,DAY_D,NIGHT_RANDUNC_N,DAY_RANDUNC_N,";
static const char header_file_night_year[] = "NIGHT_RANDUNC_N,DAY_RANDUNC_N,";

static const char header_file_night_y_no_rand_unc[] =	"NEE_VUT_REF_NIGHT,NEE_VUT_REF_NIGHT_SD,NEE_VUT_REF_NIGHT_QC,"
														"NEE_VUT_REF_DAY,NEE_VUT_REF_DAY_SD,NEE_VUT_REF_DAY_QC,"
														"NEE_VUT_USTAR50_NIGHT,NEE_VUT_USTAR50_NIGHT_SD,NEE_VUT_USTAR50_NIGHT_QC,"
														"NEE_VUT_USTAR50_DAY,NEE_VUT_USTAR50_DAY_SD,NEE_VUT_USTAR50_DAY_QC,"
														"NEE_VUT_05_NIGHT,NEE_VUT_05_NIGHT_QC,NEE_VUT_16_NIGHT,NEE_VUT_16_NIGHT_QC,"
														"NEE_VUT_25_NIGHT,NEE_VUT_25_NIGHT_QC,NEE_VUT_50_NIGHT,NEE_VUT_50_NIGHT_QC,"
														"NEE_VUT_75_NIGHT,NEE_VUT_75_NIGHT_QC,NEE_VUT_84_NIGHT,NEE_VUT_84_NIGHT_QC,"
														"NEE_VUT_95_NIGHT,NEE_VUT_95_NIGHT_QC,"
														"NEE_VUT_05_DAY,NEE_VUT_05_DAY_QC,NEE_VUT_16_DAY,NEE_VUT_16_DAY_QC,"
														"NEE_VUT_25_DAY,NEE_VUT_25_DAY_QC,NEE_VUT_50_DAY,NEE_VUT_50_DAY_QC,"
														"NEE_VUT_75_DAY,NEE_VUT_75_DAY_QC,NEE_VUT_84_DAY,NEE_VUT_84_DAY_QC,"
														"NEE_VUT_95_DAY,NEE_VUT_95_DAY_QC";
static const char header_file_night_c_no_rand_unc[] =
														",NEE_CUT_REF_NIGHT,NEE_CUT_REF_NIGHT_SD,NEE_CUT_REF_NIGHT_QC,"
														"NEE_CUT_REF_DAY,NEE_CUT_REF_DAY_SD,NEE_CUT_REF_DAY_QC,"
														"NEE_CUT_USTAR50_NIGHT,NEE_CUT_USTAR50_NIGHT_SD,NEE_CUT_USTAR50_NIGHT_QC,"
														"NEE_CUT_USTAR50_DAY,NEE_CUT_USTAR50_DAY_SD,NEE_CUT_USTAR50_DAY_QC,"
														"NEE_CUT_05_NIGHT,NEE_CUT_05_NIGHT_QC,NEE_CUT_16_NIGHT,NEE_CUT_16_NIGHT_QC,"
														"NEE_CUT_25_NIGHT,NEE_CUT_25_NIGHT_QC,NEE_CUT_50_NIGHT,NEE_CUT_50_NIGHT_QC,"
														"NEE_CUT_75_NIGHT,NEE_CUT_75_NIGHT_QC,NEE_CUT_84_NIGHT,NEE_CUT_84_NIGHT_QC,"
														"NEE_CUT_95_NIGHT,NEE_CUT_95_NIGHT_QC,"
														"NEE_CUT_05_DAY,NEE_CUT_05_DAY_QC,NEE_CUT_16_DAY,NEE_CUT_16_DAY_QC,"
														"NEE_CUT_25_DAY,NEE_CUT_25_DAY_QC,NEE_CUT_50_DAY,NEE_CUT_50_DAY_QC,"
														"NEE_CUT_75_DAY,NEE_CUT_75_DAY_QC,NEE_CUT_84_DAY,NEE_CUT_84_DAY_QC,"
														"NEE_CUT_95_DAY,NEE_CUT_95_DAY_QC\n";

static const char header_file_night_y[] =	"NEE_VUT_REF_NIGHT,NEE_VUT_REF_NIGHT_SD,NEE_VUT_REF_NIGHT_QC,NEE_VUT_REF_NIGHT_RANDUNC,NEE_VUT_REF_NIGHT_JOINTUNC,"
											"NEE_VUT_REF_DAY,NEE_VUT_REF_DAY_SD,NEE_VUT_REF_DAY_QC,NEE_VUT_REF_DAY_RANDUNC,NEE_VUT_REF_DAY_JOINTUNC,"
											"NEE_VUT_USTAR50_NIGHT,NEE_VUT_USTAR50_NIGHT_SD,NEE_VUT_USTAR50_NIGHT_QC,NEE_VUT_USTAR50_NIGHT_RANDUNC,NEE_VUT_USTAR50_NIGHT_JOINTUNC,"
											"NEE_VUT_USTAR50_DAY,NEE_VUT_USTAR50_DAY_SD,NEE_VUT_USTAR50_DAY_QC,NEE_VUT_USTAR50_DAY_RANDUNC,NEE_VUT_USTAR50_DAY_JOINTUNC,"
											"NEE_VUT_05_NIGHT,NEE_VUT_05_NIGHT_QC,NEE_VUT_16_NIGHT,NEE_VUT_16_NIGHT_QC,"
											"NEE_VUT_25_NIGHT,NEE_VUT_25_NIGHT_QC,NEE_VUT_50_NIGHT,NEE_VUT_50_NIGHT_QC,"
											"NEE_VUT_75_NIGHT,NEE_VUT_75_NIGHT_QC,NEE_VUT_84_NIGHT,NEE_VUT_84_NIGHT_QC,"
											"NEE_VUT_95_NIGHT,NEE_VUT_95_NIGHT_QC,"
											"NEE_VUT_05_DAY,NEE_VUT_05_DAY_QC,NEE_VUT_16_DAY,NEE_VUT_16_DAY_QC,"
											"NEE_VUT_25_DAY,NEE_VUT_25_DAY_QC,NEE_VUT_50_DAY,NEE_VUT_50_DAY_QC,"
											"NEE_VUT_75_DAY,NEE_VUT_75_DAY_QC,NEE_VUT_84_DAY,NEE_VUT_84_DAY_QC,"
											"NEE_VUT_95_DAY,NEE_VUT_95_DAY_QC";

static const char header_file_night_c[] =
											",NEE_CUT_REF_NIGHT,NEE_CUT_REF_NIGHT_SD,NEE_CUT_REF_NIGHT_QC,NEE_CUT_REF_NIGHT_RANDUNC,NEE_CUT_REF_NIGHT_JOINTUNC,"
											"NEE_CUT_REF_DAY,NEE_CUT_REF_DAY_SD,NEE_CUT_REF_DAY_QC,NEE_CUT_REF_DAY_RANDUNC,NEE_CUT_REF_DAY_JOINTUNC,"
											"NEE_CUT_USTAR50_NIGHT,NEE_CUT_USTAR50_NIGHT_SD,NEE_CUT_USTAR50_NIGHT_QC,NEE_CUT_USTAR50_NIGHT_RANDUNC,NEE_CUT_USTAR50_NIGHT_JOINTUNC,"
											"NEE_CUT_USTAR50_DAY,NEE_CUT_USTAR50_DAY_SD,NEE_CUT_USTAR50_DAY_QC,NEE_CUT_USTAR50_DAY_RANDUNC,NEE_CUT_USTAR50_DAY_JOINTUNC,"
											"NEE_CUT_05_NIGHT,NEE_CUT_05_NIGHT_QC,NEE_CUT_16_NIGHT,NEE_CUT_16_NIGHT_QC,"
											"NEE_CUT_25_NIGHT,NEE_CUT_25_NIGHT_QC,NEE_CUT_50_NIGHT,NEE_CUT_50_NIGHT_QC,"
											"NEE_CUT_75_NIGHT,NEE_CUT_75_NIGHT_QC,NEE_CUT_84_NIGHT,NEE_CUT_84_NIGHT_QC,"
											"NEE_CUT_95_NIGHT,NEE_CUT_95_NIGHT_QC,"
											"NEE_CUT_05_DAY,NEE_CUT_05_DAY_QC,NEE_CUT_16_DAY,NEE_CUT_16_DAY_QC,"
											"NEE_CUT_25_DAY,NEE_CUT_25_DAY_QC,NEE_CUT_50_DAY,NEE_CUT_50_DAY_QC,"
											"NEE_CUT_75_DAY,NEE_CUT_75_DAY_QC,NEE_CUT_84_DAY,NEE_CUT_84_DAY_QC,"
											"NEE_CUT_95_DAY,NEE_CUT_95_DAY_QC\n";

static const char ustar_threshold_c[] = "- NEE_CUT_USTAR50: u* threshold %g\n";
static const char ustar_threshold_y_one_year[] = "- NEE_VUT_USTAR50: u* threshold %g\n";
static const char ustar_threshold_y[] = "- NEE_VUT_USTAR50, year %d: u* threshold %g\n";

static const char model_efficiency_c[] = "NEE_CUT_REF = filtered using the ustar percentile %g (ustar value: %g)\n";
static const char model_efficiency_y_one_year[] = "NEE_VUT_REF filtered using the ustar percentile %g (ustar value: %g)\n";
static const char model_efficiency_y[] = "NEE_VUT_REF filtered on year %d using the ustar percentile %g (ustar value: %g)\n";
#else
static const char output_var_1_rand_unc_hh[] =	"NEE_ref_y,NEE_ref_qc_y,"
												"NEE_ref_randUnc_y,NEE_ref_randUnc_method_y,NEE_ref_randUnc_n_y,"
												"NEE_ref_joinUnc_y,"
												"NEE_ust50_y,NEE_ust50_qc_y,"
												"NEE_ust50_randUnc_y,NEE_ust50_randUnc_method_y,NEE_ust50_randUnc_n_y,"
												"NEE_ust50_joinUnc_y,"
												"NEE_mean_y,NEE_mean_qc_y,"
												"NEE_SE_y,";
static const char output_var_2_rand_unc_hh[] =	",NEE_ref_c,NEE_ref_qc_c,"
												"NEE_ref_randUnc_c,NEE_ref_randUnc_method_c,NEE_ref_randUnc_n_c,"
												"NEE_ref_joinUnc_c,"
												"NEE_ust50_c,NEE_ust50_qc_c,"
												"NEE_ust50_randUnc_c,NEE_ust50_randUnc_method_c,NEE_ust50_randUnc_n_c,"
												"NEE_ust50_joinUnc_c,"
												"NEE_mean_c,NEE_mean_qc_c,"
												"NEE_SE_c,";
static const char output_var_1[] =	"NEE_ref_y,NEE_ref_qc_y,"
									"NEE_ust50_y,NEE_ust50_qc_y,"
									"NEE_mean_y,NEE_mean_qc_y,"
									"NEE_SE_y,";
static const char output_var_2[] =	",NEE_ref_c,NEE_ref_qc_c,"
									"NEE_ust50_c,NEE_ust50_qc_c,"
									"NEE_mean_c,NEE_mean_qc_c,"
									"NEE_SE_c,";

static const char output_var_1_rand_unc[] =	"NEE_ref_y,NEE_ref_qc_y,"
											"NEE_ref_randUnc_y,NEE_ref_joinUnc_y,"
											"NEE_ust50_y,NEE_ust50_qc_y,"
											"NEE_ust50_randUnc_y,NEE_ust50_joinUnc_y,"
											"NEE_mean_y,NEE_mean_qc_y,"
											"NEE_SE_y,";
static const char output_var_2_rand_unc[] =	",NEE_ref_c,NEE_ref_qc_c,"
											"NEE_ref_randUnc_c,NEE_ref_joinUnc_c,"
											"NEE_ust50_c,NEE_ust50_qc_c,"
											"NEE_ust50_randUnc_c,NEE_ust50_joinUnc_c,"
											"NEE_mean_c,NEE_mean_qc_c,"
											"NEE_SE_c,";

static const char header_file_night_no_rand_unc[] = ",night_d,day_d,";
static const char header_file_night[] = ",night_d,day_d,night_randUnc_n,day_randUnc_n,";
static const char header_file_night_year[] = "night_randUnc_n,day_randUnc_n,";

static const char header_file_night_y_no_rand_unc[] =	"NEE_ref_night_y,NEE_ref_night_std_y,NEE_ref_night_qc_y,"
														"NEE_ref_day_y,NEE_ref_day_std_y,NEE_ref_day_qc_y,"
														"NEE_ust50_night_y,NEE_ust50_night_std_y,NEE_ust50_night_qc_y,"
														"NEE_ust50_day_y,NEE_ust50_day_std_y,NEE_ust50_day_qc_y,"
														"NEE_night_05_y,NEE_night_05_qc_y,NEE_night_16_y,NEE_night_16_qc_y,"
														"NEE_night_25_y,NEE_night_25_qc_y,NEE_night_50_y,NEE_night_50_qc_y,"
														"NEE_night_75_y,NEE_night_75_qc_y,NEE_night_84_y,NEE_night_84_qc_y,"
														"NEE_night_95_y,NEE_night_95_qc_y,"
														"NEE_day_05_y,NEE_day_05_qc_y,NEE_day_16_y,NEE_day_16_qc_y,"
														"NEE_day_25_y,NEE_day_25_qc_y,NEE_day_50_y,NEE_day_50_qc_y,"
														"NEE_day_75_y,NEE_day_75_qc_y,NEE_day_84_y,NEE_day_84_qc_y,"
														"NEE_day_95_y,NEE_day_95_qc_y";
static const char header_file_night_c_no_rand_unc[] =
														",NEE_ref_night_c,NEE_ref_night_std_c,NEE_ref_night_qc_c,"
														"NEE_ref_day_c,NEE_ref_day_std_c,NEE_ref_day_qc_c,"
														"NEE_ust50_night_c,NEE_ust50_night_std_c,NEE_ust50_night_qc_c,"
														"NEE_ust50_day_c,NEE_ust50_day_std_c,NEE_ust50_day_qc_c,"
														"NEE_night_05_c,NEE_night_05_qc_c,NEE_night_16_c,NEE_night_16_qc_c,"
														"NEE_night_25_c,NEE_night_25_qc_c,NEE_night_50_c,NEE_night_50_qc_c,"
														"NEE_night_75_c,NEE_night_75_qc_c,NEE_night_84_c,NEE_night_84_qc_c,"
														"NEE_night_95_c,NEE_night_95_qc_c,"
														"NEE_day_05_c,NEE_day_05_qc_c,NEE_day_16_c,NEE_day_16_qc_c,"
														"NEE_day_25_c,NEE_day_25_qc_c,NEE_day_50_c,NEE_day_50_qc_c,"
														"NEE_day_75_c,NEE_day_75_qc_c,NEE_day_84_c,NEE_day_84_qc_c,"
														"NEE_day_95_c,NEE_day_95_qc_c\n";

static const char header_file_night_y[] =	"NEE_ref_night_y,NEE_ref_night_std_y,NEE_ref_night_qc_y,NEE_ref_night_randUnc_y,NEE_ref_night_joinUnc_y,"
											"NEE_ref_day_y,NEE_ref_day_std_y,NEE_ref_day_qc_y,NEE_ref_day_randUnc_y,NEE_ref_day_joinUnc_y,"
											"NEE_ust50_night_y,NEE_ust50_night_std_y,NEE_ust50_night_qc_y,NEE_ust50_night_randUnc_y,NEE_ust50_night_joinUnc_y,"
											"NEE_ust50_day_y,NEE_ust50_day_std_y,NEE_ust50_day_qc_y,NEE_ust50_day_randUnc_y,NEE_ust50_day_joinUnc_y,"
											"NEE_night_05_y,NEE_night_05_qc_y,NEE_night_16_y,NEE_night_16_qc_y,"
											"NEE_night_25_y,NEE_night_25_qc_y,NEE_night_50_y,NEE_night_50_qc_y,"
											"NEE_night_75_y,NEE_night_75_qc_y,NEE_night_84_y,NEE_night_84_qc_y,"
											"NEE_night_95_y,NEE_night_95_qc_y,"
											"NEE_day_05_y,NEE_day_05_qc_y,NEE_day_16_y,NEE_day_16_qc_y,"
											"NEE_day_25_y,NEE_day_25_qc_y,NEE_day_50_y,NEE_day_50_qc_y,"
											"NEE_day_75_y,NEE_day_75_qc_y,NEE_day_84_y,NEE_day_84_qc_y,"
											"NEE_day_95_y,NEE_day_95_qc_y";

static const char header_file_night_c[] =
											",NEE_ref_night_c,NEE_ref_night_std_c,NEE_ref_night_qc_c,NEE_ref_night_randUnc_c,NEE_ref_night_joinUnc_c,"
											"NEE_ref_day_c,NEE_ref_day_std_c,NEE_ref_day_qc_c,NEE_ref_day_randUnc_c,NEE_ref_day_joinUnc_c,"
											"NEE_ust50_night_c,NEE_ust50_night_std_c,NEE_ust50_night_qc_c,NEE_ust50_night_randUnc_c,NEE_ust50_night_joinUnc_c,"
											"NEE_ust50_day_c,NEE_ust50_day_std_c,NEE_ust50_day_qc_c,NEE_ust50_day_randUnc_c,NEE_ust50_day_joinUnc_c,"
											"NEE_night_05_c,NEE_night_05_qc_c,NEE_night_16_c,NEE_night_16_qc_c,"
											"NEE_night_25_c,NEE_night_25_qc_c,NEE_night_50_c,NEE_night_50_qc_c,"
											"NEE_night_75_c,NEE_night_75_qc_c,NEE_night_84_c,NEE_night_84_qc_c,"
											"NEE_night_95_c,NEE_night_95_qc_c,"
											"NEE_day_05_c,NEE_day_05_qc_c,NEE_day_16_c,NEE_day_16_qc_c,"
											"NEE_day_25_c,NEE_day_25_qc_c,NEE_day_50_c,NEE_day_50_qc_c,"
											"NEE_day_75_c,NEE_day_75_qc_c,NEE_day_84_c,NEE_day_84_qc_c,"
											"NEE_day_95_c,NEE_day_95_qc_c\n";

static const char ustar_threshold_c[] = "- NEE_ust50_c: u* threshold %g\n";
static const char ustar_threshold_y_one_year[] = "- NEE_ust50_y: u* threshold %g\n";
static const char ustar_threshold_y[] = "- NEE_ust50_y, year %d: u* threshold %g\n";

static const char model_efficiency_c[] = "NEE_ref_c = filtered using the ustar percentile %g (ustar value: %g)\n";
static const char model_efficiency_y_one_year[] = "NEE_ref_y filtered using the ustar percentile %g (ustar value: %g)\n";
static const char model_efficiency_y[] = "NEE_ref_y filtered on year %d using the ustar percentile %g (ustar value: %g)\n";
#endif

static const char *time_resolution[TRS] = { "hh", "dd", "ww", "mm", "yy" };

/* todo : implement a better comparison for equality */
static int compare_value_qc(const void * a, const void * b) {
	if ( ((VALUE_QC *)a)->value < ((VALUE_QC *)b)->value ) {
		return -1;
	} else if ( ((VALUE_QC *)a)->value > ((VALUE_QC *)b)->value ) {
		return 1;
	} else {
		return 0;
	}
}

/* */
static PREC compute_join(const PREC a, const PREC b, const PREC c) {
	if ( ! IS_INVALID_VALUE(a) && ! IS_INVALID_VALUE(b) && ! IS_INVALID_VALUE(c) ) {
		return (SQRT(((a)*(a))+(((c-b)/2)*((c-b)/2))));
	} else {
		return INVALID_VALUE;
	}
}

/* */
static int get_meteo(DATASET *const dataset) {
	int i;
	int y;
	int element;
	int index;
	int start_year;
	int rows_count;
	int _TA;
	int _VPD;
	int _SWIN;
	int TA_QC;
	int VPD_QC;
	int SWIN_QC;
	int error;
	int current_row;
	char buffer[BUFFER_SIZE];
	char *token;
	char *p;
	FILE *f;
	TIMESTAMP *t;
	PREC value;
	DD details;

	/* */
	assert(dataset);

	/* check if file exists */
	sprintf(buffer, "%s%s_meteo_hh.csv", meteo_files_path, dataset->details->site);
	f = fopen(buffer, "r");
	if ( !f ) {
		/* no found, ok*/
		puts("nothing found.");
		return 1;
	}

	/* get header */
	if ( !fgets(buffer, BUFFER_SIZE, f) ) {
		puts("missing header ?");
		fclose(f);
		return 0;
	}

	/* parse header */
	_TA = -1;
	_SWIN = -1;
	_VPD = -1;
	for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
		if ( ! string_compare_i(token, "TA_m") ) {
			_TA = i;
		} else if ( ! string_compare_i(token, "SW_IN_m") ) {
			_SWIN = i;
		} else if ( ! string_compare_i(token, "VPD_m") ) {
			_VPD = i;
		} else if ( ! string_compare_i(token, "TA_mqc") ) {
			TA_QC = i;
		} else if ( ! string_compare_i(token, "SW_IN_mqc") ) {
			SWIN_QC = i;
		} else if ( ! string_compare_i(token, "VPD_mqc") ) {
			VPD_QC = i;
		}
	}

	/* how many vars we've found */
	i = 0;
	if ( _TA != -1 ) ++i;
	if ( _SWIN != -1 ) ++i;
	if ( _VPD != -1 ) ++i;

	/* nothing found! */
	if ( !i ) {
		puts("nothing found!");
		fclose(f);
		return 1;
	}

	/* check indexes */
	if ( !((_TA < _SWIN) && (_SWIN < _VPD)) ) {
		puts("bad indexes for columns.");
		fclose(f);
		return 0;
	}

	/* get starting year */
	if ( !fgets(buffer, BUFFER_SIZE, f) ) {
		puts("bad file.");
		fclose(f);
		return 0;
	}

	/* get timestamp */
	t = get_timestamp(string_tokenizer(buffer, dataset_delimiter, &p));
	if ( ! t ) {
		puts("bad file.");
		fclose(f);
		return 0;
	}
	start_year = t->YYYY;
	free(t);
	if ( start_year > dataset->years[0].year ) {
		puts("nothing found!");
		fclose(f);
		return 1;
	}

	/* set timeres */
	details.timeres = dataset->details->timeres;

	/* skip rows */
	index = 0;	
	for ( i = start_year;  i < dataset->years[0].year; i++ ) {
		details.year = i;
		index += get_rows_count_by_dd(&details);
	}
	fseek(f, 0, SEEK_SET);
	for ( i = 0; i < index + 1; i++ ) { /* +1 for skip header */
		if ( !get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
			puts("bad file.");
			fclose(f);
			return 0;
		}
	}
	puts("found");

	/* get values */
	index = 0;
	for ( y = 0; y < dataset->years_count; y++ ) {	
		printf("#%02d importing meteo %d...", y+1, dataset->years[y].year);

		element = 0;
		details.year = dataset->years[y].year;
		rows_count = get_rows_count_by_dd(&details);
		if ( !rows_count ) {
			printf("bad rows count for year %d\n", details.year);
			fclose(f);
			return 0;
		}
		while ( fgets(buffer, BUFFER_SIZE, f) ) {
			for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), i++ ) {
				if ( ! i ) {
					// skip timestamp start
					continue;
				} else if ( 1 == i ) {
					// get timestamp
					t = get_timestamp(token);
					if ( ! t ) {
						fclose(f);
						return 0;
					}

					/* check year */
					if ( details.year != t->YYYY ) {
						/* check for last row */
						if ( !(	(t->YYYY == details.year+1) &&
								(1 == t->MM) &&
								(1 == t->DD) &&
								(0 == t->hh) &&
								(0 == t->mm)) ) {
									printf("bad row: %s\n", token);
							free(t);
							fclose(f);
							return 0;

						}
					}

					current_row = get_row_by_timestamp(t, dataset->details->timeres);
					free(t);
					if ( element != current_row ) {
						printf("bad timestamp: %s", token);
						fclose(f);
						return 0;
					}							
				} else {
					value = convert_string_to_prec(token, &error);
					if ( error ) {
						printf("unable to convert value %s at row %d, column %d\n", token, current_row+1, i+1);
						fclose(f);
						return 0;
					}
					
					if ( i == _TA ) {
						dataset->rows[index+current_row].value[TA_VALUE] = value;
					} else if ( i == _SWIN ) {
						dataset->rows[index+current_row].value[SWIN_VALUE] = value;
					} else if ( i == _VPD ) {
						dataset->rows[index+current_row].value[VPD_VALUE] = value;
					} else if ( i == TA_QC ) {
						dataset->rows[index+current_row].value[TA_QC_VALUE] = value;
					} else if ( i == SWIN_QC ) {
						dataset->rows[index+current_row].value[SWIN_QC_VALUE] = value;
					} else if ( i == VPD_QC ) {
						dataset->rows[index+current_row].value[VPD_QC_VALUE] = value;
					}
				}
			}
			
			if ( ++element == rows_count ) {
				break;
			}
		}
		puts("ok");
		index += rows_count;
	}

	/* */
	fclose(f);
	
	/* ok */
	return 1;
}

/* using Model Efficiency, on error returns -1 */
int get_reference(const DATASET *const dataset, const NEE_MATRIX *const nee_matrix, const int rows_count, const int type) {
	int i;
	int j;
	int row;
	int column;
	int mean_count;
	int square_count;
	int rows_per_day;
	PREC mean;
	PREC square;
	PREC variance;
	PREC sum;
	ME *mes;
	PREC *mess;
	char buffer[256];
	FILE *f;

	/* */
	rows_per_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;

	/* alloc memory */
	mes = malloc((PERCENTILES_COUNT_2-1)*sizeof*mes);
	if ( !mes ) {
		puts(err_out_of_memory);
		return -1;
	}

	/* alloc memory */
	mess = malloc((PERCENTILES_COUNT_2-1)*sizeof*mess);
	if ( !mess ) {
		puts(err_out_of_memory);
		free(mes);
		return -1;
	}

	/* reset */
	for ( i = 0; i < PERCENTILES_COUNT_2-1; i++ ) {
		for ( j = 0; j < PERCENTILES_COUNT_2-1; j++ ) {
			mes[i].value[j] = INVALID_VALUE;
		}
	}

	/* check for missing years */
	j = 0;
	for ( i = 0; i < dataset->years_count; i++ ) {
		if ( !dataset->years[i].exist ) {
			j = 1;
			break;
		}
	}

	if ( !j ) {
		/* */
		for ( column = 0; column < PERCENTILES_COUNT_2-1; column++ ) {
			mean = 0.0;
			mean_count = 0;
			for ( row = 0; row < rows_count; row++ ) {
				if ( ! IS_INVALID_VALUE(nee_matrix[row].nee[column]) ) {
					mean += nee_matrix[row].nee[column];
					++mean_count;
				}
			}
			if ( mean_count ) {
				mean /= mean_count;
			}
			square = 0.0;
			square_count = 0;
			for ( row = 0; row < rows_count; row++ ) {
				if ( ! IS_INVALID_VALUE(nee_matrix[row].nee[column]) ) {
					square += SQUARE(nee_matrix[row].nee[column] - mean);
					++square_count;
				}
			}
			if ( square_count ) {
				variance = square / square_count;
			} else {
				printf("unable to get variance for column %d\n", column);
				free(mess);
				free(mes);
				return -1;
			}

			for ( i = 0; i < PERCENTILES_COUNT_2-1; i++ ) {
				sum = 0.0;
				for ( j = 0; j < rows_count; j++ ) {
					sum += (nee_matrix[j].nee[column] - nee_matrix[j].nee[i])*(nee_matrix[j].nee[column] - nee_matrix[j].nee[i]);
				}
				sum /= rows_count;
				sum /= variance;

				mes[column].value[i] = 1 - sum;
			}
		}
	} else {
		int k;
		int z;
		int index;
		int index2;
		int ex_rows_count; /* ex stands for EXistent! */
		NEE_MATRIX *ex;

		/* get rows count */
		ex_rows_count = 0;
		for ( i = 0; i < dataset->years_count; i++ ) {
			if ( dataset->years[i].exist ) {
				z = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

				/* */
				if ( HOURLY_TIMERES == dataset->details->timeres ) {
					z /= 2;
				}
				
				/* */
				if ( (DD_Y == type) || (DD_C == type) ) z /= rows_per_day;

				if ( (WW_Y == type) || (WW_C == type) ) z = 52;
				if ( (MM_Y == type) || (MM_C == type) ) z = 12;
				if ( (YY_Y == type) || (YY_C == type) ) z = 1;
				ex_rows_count += z;		
			}
		}

		/* alloc memory */
		ex = malloc(ex_rows_count*sizeof*ex);
		if ( !ex ) {
			puts(err_out_of_memory);
			free(mess);
			free(mes);
			return -1;
		}

		/* build-up dataset */
		index = 0;
		index2 = 0;
		for ( i = 0; i < dataset->years_count; i++ ) {
			k = IS_LEAP_YEAR(dataset->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			/* */
			if ( HOURLY_TIMERES == dataset->details->timeres ) {
				k /= 2;
			}

			/* */
			if ( (DD_Y == type) || (DD_C == type) ) k /= rows_per_day;
			if ( (WW_Y == type) || (WW_C == type) ) k = 52;
			if ( (MM_Y == type) || (MM_C == type) ) k = 12;
			if ( (YY_Y == type) || (YY_C == type) ) k = 1;
			if ( dataset->years[i].exist ) {			
				for ( z = 0; z < k; z++ ) {
					for ( j = 0; j < PERCENTILES_COUNT_2; j++ ) {
						ex[index+z].nee[j] = nee_matrix[index2+z].nee[j];
					}
				}
				index += k;
				index2 += k;
			} else {
				index2 += k;
			}
		}

		/* */
		for ( column = 0; column < PERCENTILES_COUNT_2-1; column++ ) {
			mean = 0.0;
			mean_count = 0;
			for ( row = 0; row < ex_rows_count; row++ ) {
				if ( ! IS_INVALID_VALUE(ex[row].nee[column]) ) {
					mean += ex[row].nee[column];
					++mean_count;
				}
			}
			if ( mean_count ) {
				mean /= mean_count;
			}
			square = 0.0;
			square_count = 0;
			for ( row = 0; row < ex_rows_count; row++ ) {
				if ( ! IS_INVALID_VALUE(ex[row].nee[column]) ) {
					square += SQUARE(ex[row].nee[column] - mean);
					++square_count;
				}
			}
			if ( square_count ) {
				variance = square / square_count;
			} else {
				printf("unable to get variance for column %d\n", column);
				free(mess);
				free(mes);
				free(ex);
				return -1;
			}

			for ( i = 0; i < PERCENTILES_COUNT_2-1; i++ ) {
				sum = 0.0;
				for ( j = 0; j < ex_rows_count; j++ ) {
					sum += (ex[j].nee[column] - ex[j].nee[i])*(ex[j].nee[column] - ex[j].nee[i]);
				}
				sum /= ex_rows_count;
				sum /= variance;

				mes[column].value[i] = 1 - sum;
			}
		}

		/* free memory */
		free(ex);
	}

	/* get selected */
	for ( column = 0; column < PERCENTILES_COUNT_2-1; column++ ) {
		mess[column] = 0.0;
		for ( row = 0; row < PERCENTILES_COUNT_2-1; row++ ) {	
			mess[column] += mes[row].value[column];
		}
	}

	column = 0;
	sum = mess[0]; /* used as start point */
	for ( i = 0; i < PERCENTILES_COUNT_2-1; i++ ) {
		if ( mess[i] > sum ) {
			sum = mess[i];
			column = i;
		}
	}

	/* save mess ? */
	if ( mef_save ) {
		if ( dataset->years_count > 1 ) {
			sprintf(buffer, "%s%s_mef_matrix_%s_%d_%d.csv", output_files_path, dataset->details->site, types[type], dataset->years[0].year, dataset->years[dataset->years_count-1].year);
		} else {
			sprintf(buffer, "%s%s_mef_matrix_%s_%d.csv", output_files_path, dataset->details->site, types[type], dataset->years[0].year);		
		}
		f = fopen(buffer, "w");
		if ( f ) {
			for ( i = 0; i < PERCENTILES_COUNT_2-1; i++ ) {
				for ( j = 0; j < PERCENTILES_COUNT_2-1; j++ ) {
					fprintf(f, "%g", mes[i].value[j]);
					if ( j < PERCENTILES_COUNT_2-1-1 ) {
						fputs(",", f);
					}
				}
				fputs("\n", f);
			}
			fclose(f);
		} else {
			printf("unable to save %s\n", buffer);
		}
	}

	/* free memory */
	free(mess);
	free(mes);

	/* */
	return column;
}

/* */
PREC get_percentile_and_qc(const PREC *values, const PREC *qcs, const int n, const float percentile, PREC *const qc, int *const error) {
	int i;
	int index;
	int n_valid;
	PREC r;
	VALUE_QC *value_qc;

	/* check parameters */
	assert(values && qcs && qc && error);

	/* reset */
	*error = 0;

	/* */
	if ( !n ) {
		return 0.0;
	} else if ( 1 == n ) {
		/* changed on January 10, 2014 by Dario requests */
		*qc = qcs[0];
		return values[0];
		/*
		if ( IS_INVALID_VALUE(values[0]) ) {
			*error = 1;
			return 0.0;
		} else {
			*qc = qcs[0];
			return values[0];
		}
		*/
	}

	/* percentile MUST be a value between 0 and 100 */
	if ( percentile < 0.0 || percentile > 100.0 ) {
		*error = 1;
		return 0.0;
	}

	/* alloc memory for nee_qc */
	value_qc = malloc(n*sizeof*value_qc);
	if ( !value_qc ) {
		*error = 1;
		return 0.0;
	}

	n_valid = 0;
	for ( i = 0; i < n; i++ ) {
		if ( !IS_INVALID_VALUE(values[i]) ) {
			value_qc[n_valid].value = values[i];
			value_qc[n_valid++].qc = qcs[i];
		}
	}

	if ( !n_valid ) {
		free(value_qc);
		/* changed on January 10, 2014 by Dario requests */
		 return INVALID_VALUE /* 0.0 */;
	}

	qsort(value_qc, n_valid, sizeof*value_qc, compare_value_qc);

	index = ROUND((percentile / 100.0) * n_valid);
	if ( --index < 0 ) {
		index = 0;
	}
	if ( index >= n_valid ) {
		r = value_qc[n_valid-1].value;
		*qc = value_qc[n_valid-1].qc;
		free(value_qc);
		return r;
	}

	/* */
	r = value_qc[index].value;
	*qc = value_qc[index].qc;

	/* */
	free(value_qc);

	/* */
	return r;
}

/* */
P_MATRIX *process_nee_matrix(const DATASET *const dataset, const NEE_MATRIX *const nee_matrix, const int rows_count, int *ref, const int type) {
	int i;
	int row;
	int percentile;
	int error;
	PREC *temp;
	PREC *temp2;
	P_MATRIX *p_matrix;

	/* check paramenters */
	assert(nee_matrix && ref);
	
	/* alloc memory, -1 'cause we don't use 50% in this computation */
	temp = malloc((PERCENTILES_COUNT_2-1)*sizeof*temp);
	if ( !temp ) {
		puts(err_out_of_memory);
		return NULL;
	}

	temp2 = malloc((PERCENTILES_COUNT_2-1)*sizeof*temp2);
	if ( !temp2 ) {
		puts(err_out_of_memory);
		free(temp);
		return NULL;
	}

	/* */
	p_matrix = malloc(rows_count*sizeof*p_matrix);
	if ( !p_matrix ) {
		puts(err_out_of_memory);
		free(temp2);
		free(temp);
		return NULL;
	}

	
	/*
		In the annual time aggregation if the site has only 1 year
		the calculation of the Model Efficiency is impossible or it doesn't make sense.
		For this reason in these cases the REF is set at the same percentile selected in the monthly files.
	*/
	if ( (YY_Y == type) && (1 == dataset->years_count) )  {
		/* ref remains same of monthly aggregation */
	} else {
		/* get references */
		*ref = get_reference(dataset, nee_matrix, rows_count, type);
		if ( -1 == *ref ) {
			free(p_matrix);
			free(temp2);
			free(temp);
			return 0;
		}
	}

	/* compute percentile matrix */
	for ( row = 0; row < rows_count; row++ ) {
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2-1; percentile++ ) {
			temp[percentile] = nee_matrix[row].nee[percentile];
			temp2[percentile] = nee_matrix[row].qc[percentile];
		}
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			p_matrix[row].value[percentile] = get_percentile_and_qc(temp, temp2, PERCENTILES_COUNT_2-1, percentiles_test_1[percentile], &p_matrix[row].qc[percentile], &error);			
			if ( error ) {
				printf("unable to compute %g%% percentile.", percentiles_test_1[percentile]);
				return NULL;
			}
		}
		p_matrix[row].mean = get_mean(temp, PERCENTILES_COUNT_2-1);
		if ( (HH_Y == type) || (HH_C == type) ) {
			for ( i = 0; i < PERCENTILES_COUNT_2-1; i++ ) {
				if ( temp2[i] < 2 ) {
					temp2[i] = 1;
				} else {
					temp2[i] = 0;
				}
			}
		}
		p_matrix[row].mean_qc = get_mean(temp2, PERCENTILES_COUNT_2-1);
		p_matrix[row].std_err = get_standard_deviation(temp, PERCENTILES_COUNT_2-1);
		p_matrix[row].std_err /= 6.324555320336759; /* sqrt(PERCENTILES_COUNT2-1) */
	}

	/* free memory */
	free(temp2);
	free(temp);

	/* ok */
	return p_matrix;
}

/* */
static int import_uts(const char *const filename, PREC *const ust, const int method, const int index, char **perror) {
	int i;
	int error;
	FILE *f;
	char buffer[BUFFER_SIZE];
	static char err[BUFFER_SIZE];

	err[0] = '\0';
	*perror = err;

	/* check method */
	if ( (method < 0) || (method >= METHODS) ) {
		strcpy(err, "bad method specified");
		return 0;
	}

	/* open file */
	f = fopen(filename, "r");
	if ( !f ) {
		strcpy(err, "file not found");
		return 0;
	}

	/* skip rows on ustar_mp */
	if ( USTAR_MP == method ) {
		error = 0;
		
	#if 1
		// PLEASE NOTE:
		// FOLLOWING CODE SKIP "USTAR_MP_SKIP" ROWS AND THEN CHECK FOR " forward mode 2" string!
		// MORE FAST BUT LESS ROBUST THAN THE DISABLED ONES!
		// ENABLED FOR CONSISTENCY!
		// Alessio - June 27, 2022
		for ( i = 0; i < USTAR_MP_SKIP; i++ ) {
			if ( !fgets(buffer, BUFFER_SIZE, f) ) {
				sprintf(err, "bad %s file", methods[method]);
				error = 1;
				break;
			}
		}

		if ( error ) {
			fclose(f);
			return 0;
		}

		for ( i = 0; buffer[i]; i++ ) {
			if ( ('\r' == buffer[i]) || ('\n' == buffer[i]) ) {
				buffer[i] = '\0';
				break;
			}
		}

		if ( string_compare_i(buffer, " forward mode 2") ) {
			sprintf(err, "bad %s file", methods[method]);
			fclose(f);
			return 0;
		}
	#else
		// PLEASE NOTE:
		// FOLLOWING CODE CHECK EACH ROWS FOR " forward mode 2" string!
		// MORE SLOW BUT MORE ROBUST THAN THE ENABLED ONES!
		// DISABLED FOR CONSISTENCY!
		// Alessio - June 27, 2022
		{
			int flag = 0;
			while ( fgets(buffer, BUFFER_SIZE, f) ) {
				for ( i = 0; buffer[i]; i++ ) {
					if ( ('\r' == buffer[i]) || ('\n' == buffer[i]) ) {
						buffer[i] = '\0';
						break;
					}
				}

				if ( ! string_compare_i(buffer, " forward mode 2") ) {
					flag = 1;
					break;
				}
			}

			if ( ! flag ) {
				sprintf(err, "bad %s file", methods[method]);
				fclose(f);
				return 0;
			}
		}
	#endif
	}

	/* read file */
	error = 0;
	for ( i = 0; i < BOOTSTRAPPING_TIMES; i++ ) {
		/* BUFFER_SIZE is big so no buffer overflow should occurs */
		if ( EOF == fscanf(f, "%s", buffer) ) {
			sprintf(err, "bad %s file!", methods[method]);
			error = 1;
			break;
		}

		if ( ! string_compare_i(buffer, "nan") ) {
			ust[i+index] = INVALID_VALUE;
		} else {
			ust[i+index] = convert_string_to_prec(buffer, &error);
			if ( error ) {
				sprintf(err, "bad %s file: %s at row %d\n", methods[method], buffer, i+1);
				break;
			}

			/* check for NaN */
			if( ust[i+index] != ust[i+index] ) {
				ust[i+index] = INVALID_VALUE;
			}
		}
	}

	if ( error ) {
		fclose(f);
		return 0;
	}
	
	/* close file */
	fclose(f);

	/* */
	return 1;
}

/* */
static int is_valid_filename(const char *const filename) {
	int i;

	/* check for empty string */
	if ( !filename || !filename[0] ) {
		return 0;
	}

	/* get filename length */
	for ( i = 0; filename[i]; i++ );
 	if ( QC_AUTO_FILENAME_LEN != i ) {
		return 0;
	}

	/* check static symbols */
	if ( ('-' != filename[2]) || ('_' != filename[6]) || ('_' != filename[10]) || ('_' != filename[14])  ) {
		return 0;
	}

	/* check suffix */
	if ( string_n_compare_i(filename+SITE_LEN, "qca_nee", 7) ) {
		return 0;
	}

	/* check for digits */
	if ( !isdigit(filename[15]) ) return 0;
	if ( !isdigit(filename[16]) ) return 0;
	if ( !isdigit(filename[17]) ) return 0;
	if ( !isdigit(filename[18]) ) return 0;
	
	/* ok */
	return 1;
}

/* */
void clear_dataset(DATASET* dataset) {
	if ( dataset ) {
		if ( dataset->umna_count ) {
			free(dataset->umna);
			dataset->umna = NULL;
		}
		if ( dataset->details ) {
			free_dd(dataset->details);
			dataset->details = NULL;
		}
		if ( dataset->gf_rows ) {
			free(dataset->gf_rows);
			dataset->gf_rows = NULL;
		}
		if ( dataset->rows ) {
			free(dataset->rows);
			dataset->rows = NULL;
		}
		if ( dataset->years ) {
			free(dataset->years);
			dataset->years = NULL;
		}
	}
}

/* */
void free_datasets(DATASET *datasets, const int datasets_count) {
	int i;

	/* */
	for ( i = 0; i < datasets_count; i++ ) {
		clear_dataset(&datasets[i]);
	}
	free(datasets);
}

/* */
int get_uts_c(const char *const site, const YEAR *const years, const int years_count, PREC *uts, int *const uts_count) {
	int i;
	int year;
	char *err;
	char buffer[BUFFER_SIZE];

	/* check parameters */
	assert(uts && uts_count && years);

	/* */
	err = NULL;

	/* */
	if ( !years || !years_count ) {
		return 0;
	}

	/* */
	*uts_count = 0;
	for ( year = 0; year < years_count; year++ ) {
		/* */
		if ( years[year].exist ) {
			/* get ustar_mp u* thresholds  */
			sprintf(buffer, "%s%s_usmp_%d.txt", ustar_mp_files_path, site, years[year].year);
			i = import_uts(buffer, uts, USTAR_MP, *uts_count, &err);
			if ( ! i ) {
				printf("%d -> unable to get ustar_mp u* thresholds: %s\n", years[year].year, err);
			} else {
				*uts_count += BOOTSTRAPPING_TIMES;
			}
		}
		/* get ustar_cp u* thresholds  */
		sprintf(buffer, "%s%s_uscp_%d.txt", ustar_cp_files_path, site, years[year].year);
		i = import_uts(buffer, uts, USTAR_CP, *uts_count, &err);
		if ( i ) {
			*uts_count += BOOTSTRAPPING_TIMES;
		} else {
			printf("%d -> unable to get ustar_cp u* thresholds: %s\n", years[year].year, err);
		}
	}

	/* ok */
	return 1;
}

/* */
int add_umna(DATASET *const dataset, const int year, const int method) {
	int i;
	USTAR_METHOD_NOT_APPLIED *umna_no_leak;

	for ( i = 0; i < dataset->umna_count; ++i ) {
		if ( year == dataset->umna[i].year ) {
			dataset->umna[i].method |= method;
			return 1;
		}
	}

	umna_no_leak = realloc(dataset->umna, (dataset->umna_count+1)*sizeof*umna_no_leak);
	if ( ! umna_no_leak ) {
		return 0;
	}
	dataset->umna = umna_no_leak;
	dataset->umna[dataset->umna_count].method = method;
	dataset->umna[dataset->umna_count].year = year;
	++dataset->umna_count;
	return 1;
}

/* */
int get_uts_y(DATASET *const dataset, const int year, PREC *uts, int *const uts_count) {
	char *err;
	char buffer[BUFFER_SIZE];
	int i;
	int index;
	
	/* check parameters */
	assert(dataset && uts && uts_count);

	/* */
	err = NULL;

	/* */
	if ( ! dataset->years_count ) {
		return 0;
	}

	/* get year */
	index = -1;
	for ( i = 0; i < dataset->years_count; i++ ) {
		if ( year == dataset->years[i].year ) {
			index = i;
			break;
		}
	}
	if ( -1 == index ) {
		printf("unable to get thresholds: year %d has not been imported!\n", year);
		return 0;
	}

	/* reset */
	*uts_count = 0;

	/* get previous year */
	if ( index-1 >= 0 ) {
		/* */
		if ( dataset->years[index-1].exist ) {
			/* get ustar_mp u* thresholds for year before */
			sprintf(buffer, "%s%s_usmp_%d.txt", ustar_mp_files_path, dataset->details->site, year-1); 
			/* */
			i = import_uts(buffer, uts, USTAR_MP, *uts_count, &err);
			if ( ! i ) {
				printf("%d -> unable to get ustar_mp u* thresholds: %s\n", year-1, err);
				if ( ! add_umna(dataset, dataset->years[index-1].year, USTAR_MP_METHOD) ) {
					puts(err_out_of_memory);
					return 0;
				}
			} else {
				*uts_count += BOOTSTRAPPING_TIMES;
			}
		}
		/* get ustar_cp u* thresholds for year before */
		sprintf(buffer, "%s%s_uscp_%d.txt", ustar_cp_files_path, dataset->details->site, year-1);
		i = import_uts(buffer, uts, USTAR_CP, *uts_count, &err);
		if ( i ) {
			*uts_count += BOOTSTRAPPING_TIMES;
		} else {
			printf("%d -> unable to get ustar_cp u* thresholds: %s\n", year-1, err);
			if ( ! add_umna(dataset, dataset->years[index-1].year, USTAR_CP_METHOD) ) {
				puts(err_out_of_memory);
				return 0;
			}
		}
	}

	/* */
	if ( dataset->years[index].exist ) {
		/* get ustar_mp u* thresholds for year */
		sprintf(buffer, "%s%s_usmp_%d.txt", ustar_mp_files_path, dataset->details->site, year); 
		i = import_uts(buffer, uts, USTAR_MP, *uts_count, &err);
		if ( !i ) {
			printf("%d -> unable to get ustar_mp u* thresholds: %s\n", year, err);
			if ( ! add_umna(dataset, dataset->years[index].year, USTAR_MP_METHOD) ) {
				puts(err_out_of_memory);
				return 0;
			}
		} else {
			*uts_count += BOOTSTRAPPING_TIMES;
		}
	}
	/* get ustar_cp u* thresholds for year */
	sprintf(buffer, "%s%s_uscp_%d.txt", ustar_cp_files_path, dataset->details->site, year);
	i = import_uts(buffer, uts, USTAR_CP, *uts_count, &err);
	if ( i ) {
		*uts_count += BOOTSTRAPPING_TIMES;
	} else {
		printf("%d -> unable to get ustar_cp u* thresholds: %s\n", year, err);
		if ( ! add_umna(dataset, dataset->years[index].year, USTAR_CP_METHOD) ) {
			puts(err_out_of_memory);
			return 0;
		}
	}

	/* get year after */
	if ( index+1 < dataset->years_count ) {
		/* */
		if ( dataset->years[index+1].exist ) {
			/* get ustar_mp u* thresholds for year after*/
			sprintf(buffer, "%s%s_usmp_%d.txt", ustar_mp_files_path, dataset->details->site, year+1); 
			i = import_uts(buffer, uts, USTAR_MP, *uts_count, &err);
			/* */
			if ( !i ) {
				printf("%d -> unable to get ustar_mp u* thresholds: %s\n", year+1, err);
				if ( ! add_umna(dataset, dataset->years[index+1].year, USTAR_MP_METHOD) ) {
					puts(err_out_of_memory);
					return 0;
				}
			} else {
				*uts_count += BOOTSTRAPPING_TIMES;
			}
		}
		/* get ustar_cp u* thresholds for year after */
		sprintf(buffer, "%s%s_uscp_%d.txt", ustar_cp_files_path, dataset->details->site, year+1);
		i = import_uts(buffer, uts, USTAR_CP, *uts_count, &err);
		if ( i ) {
			*uts_count += BOOTSTRAPPING_TIMES;
		} else {
			printf("%d -> unable to get ustar_cp u* thresholds: %s\n", year+1, err);
			if ( ! add_umna(dataset, dataset->years[index+1].year, USTAR_CP_METHOD) ) {
				puts(err_out_of_memory);
				return 0;
			}
		}
	}

	if ( ! *uts_count ) {
		return 0;
	}

	/* ok */
	return 1;
}

/* */
ROW_NIGHT *compute_nights(DATASET *const dataset,
			  const NEE_MATRIX *const nee_matrix_y,
			  const NEE_MATRIX *const nee_matrix_c,
			  const int ref_y,
			  const int ref_c,
			  const RAND_UNC_ROW* const unc_rows
			  ) {
	int row;
	int i;
	int ii;
	int y;
	int index;
	int rows_count;
	PREC value;
	PREC qc;
	PREC *nights;
	PREC *days;
	PREC nights_qc;
	PREC days_qc;
	ROW_NIGHT *rows_night;
	int night_d;
	int day_d;
	int error;
	int rows_per_day;
	
	rows_per_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;

	/* compute rows count */
	rows_count = dataset->rows_count / rows_per_day;

	/* alloc memory */
	nights = malloc(rows_count*sizeof*nights);
	if ( !nights ) {
		puts(err_out_of_memory);
		return NULL;
	}
	days = malloc(rows_count*sizeof*days);
	if ( !days ) {
		puts(err_out_of_memory);
		free(nights);
		return NULL;
	}
	rows_night = malloc(rows_count*sizeof*rows_night);
	if ( !rows_night ) {
		puts(err_out_of_memory);
		free(days);
		free(nights);
		return NULL;
	}

	/* loop */
	index = 0;

	/* */
	for ( row = 0; row < dataset->rows_count; row += rows_per_day ) {
		/* loop on each var to compute */
		for ( y = 0; y < NIGHT_RAND_VALUES; y++ ) {
			/* do not compute _c if years count is less than 3 */
			if ( (dataset->years_count < 3) &&
					((NEE_REF_C == y) || (NEE_UST50_C == y) || (NEE_REF_C_RAND == y) || (NEE_UST50_C_RAND == y)) ) {
				continue;
			}
			rows_night[index].night[y] = 0.0;
			rows_night[index].night_qc[y] = 0.0;
			if ( y < NIGHT_QC_VALUES ) {
				rows_night[index].night_std[y] = INVALID_VALUE;
			}
			rows_night[index].day[y] = 0.0;
			rows_night[index].day_qc[y] = 0.0;
			if ( y < NIGHT_QC_VALUES ) {
				rows_night[index].day_std[y] = INVALID_VALUE;
			}

			night_d = 0;
			day_d = 0;

			for ( i = 0; i < rows_per_day; i++ ) {
				switch ( y ) {
					case NEE_REF_Y:
						value = nee_matrix_y[row+i].nee[ref_y];
						qc = nee_matrix_y[row+i].qc[ref_y];
					break;

					case NEE_UST50_Y:
						value = nee_matrix_y[row+i].nee[PERCENTILES_COUNT_2-1];
						qc = nee_matrix_y[row+i].qc[PERCENTILES_COUNT_2-1];
					break;

					case NEE_REF_C:
						value = nee_matrix_c[row+i].nee[ref_c];
						qc = nee_matrix_c[row+i].qc[ref_c];
					break;

					case NEE_UST50_C:
						value = nee_matrix_c[row+i].nee[PERCENTILES_COUNT_2-1];
						qc = nee_matrix_c[row+i].qc[PERCENTILES_COUNT_2-1];
					break;

					case NEE_REF_Y_RAND:
						value = unc_rows[row+i].rand[NEE_REF_Y_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_REF_Y_UNC];
					break;

					case NEE_UST50_Y_RAND:
						value = unc_rows[row+i].rand[NEE_UST50_Y_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_UST50_Y_UNC];
					break;

					case NEE_REF_C_RAND:
						value = unc_rows[row+i].rand[NEE_REF_C_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_REF_C_UNC];
					break;

					case NEE_UST50_C_RAND:
						value = unc_rows[row+i].rand[NEE_UST50_C_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_UST50_C_UNC];
					break;
				}

				/* night ? */
				if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_VALUE], 0.0) ) {
					if ( !IS_INVALID_VALUE(value) ) {
						rows_night[index].night[y] += value;
						nights[night_d++] = value;
						rows_night[index].night_qc[y] += qc;
					}				
				} else {
					if ( !IS_INVALID_VALUE(value) ) {
						rows_night[index].day[y] += value;
						days[day_d++] = value;
						rows_night[index].day_qc[y] += qc;
					}
				}
			}

			/* compute stuff */
			if ( night_d ) {
				if ( y < NIGHT_QC_VALUES ) {
					rows_night[index].night[y] /= night_d;
					rows_night[index].night_std[y] = get_standard_deviation(nights, night_d);
				} else {
					rows_night[index].night[y] = SQRT(rows_night[index].night[y]) / night_d;
					rows_night[index].night_d_rand[y-NIGHT_QC_VALUES] = night_d;
				}
				rows_night[index].night_qc[y] /= night_d;
			} else {
				rows_night[index].night[y] = INVALID_VALUE;
				rows_night[index].night_d_rand[y-NIGHT_QC_VALUES] = 0;
			}

			if ( day_d ) {
				if ( y < NIGHT_QC_VALUES ) {
					rows_night[index].day[y] /= day_d;
					rows_night[index].day_std[y] = get_standard_deviation(days, day_d);
				} else {
					rows_night[index].day[y] = SQRT(rows_night[index].day[y]) / day_d;
					rows_night[index].day_d_rand[y-NIGHT_QC_VALUES] = day_d;
				}
				rows_night[index].day_qc[y] /= day_d;
			} else {
				rows_night[index].day[y] = INVALID_VALUE;
				rows_night[index].day_d_rand[y-NIGHT_QC_VALUES] = 0;
			}
		}

		/* assign night and day */
		rows_night[index].night_d = night_d;
		rows_night[index].day_d = day_d;

		rows_night[index].night_total = 0;
		rows_night[index].day_total = 0;

		/* */
		for ( i = 0; i < rows_per_day; i++ ) {
			if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_VALUE], 0.0) ) {
				++rows_night[index].night_total;
			} else {
				++rows_night[index].day_total;
			}
		}

		/* ... per y */
		for ( y = 0; y < PERCENTILES_COUNT_2; y++ ) {
			night_d = 0;
			day_d = 0;
			nights[0] = 0.0;
			days[0] = 0.0;
			nights_qc = 0.0;
			days_qc = 0.0;

			/* */
			for ( i = 0; i < rows_per_day; i++ ) {
				value = nee_matrix_y[row+i].nee[y];
				qc = nee_matrix_y[row+i].qc[y];

				/* night ? */
				if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_VALUE], 0.0) ) {
					if ( !IS_INVALID_VALUE(value) ) {
						nights[0] += value;
						nights_qc += qc;
						++night_d;
					}				
				} else {
					if ( !IS_INVALID_VALUE(value) ) {
						days[0] += value;
						days_qc += qc;
						++day_d;
					}
				}
			}
			if ( night_d ) {
				rows_night[index].night_columns_y[y] = nights[0] / night_d;
				rows_night[index].night_qc_columns_y[y] = nights_qc / night_d;
			} else {
				rows_night[index].night_columns_y[y] = INVALID_VALUE;
				rows_night[index].night_qc_columns_y[y] = INVALID_VALUE;
			}
			if ( day_d ) {
				rows_night[index].day_columns_y[y] = days[0] / day_d;
				rows_night[index].day_qc_columns_y[y] = days_qc / day_d;
			} else {
				rows_night[index].day_columns_y[y] = INVALID_VALUE;
				rows_night[index].day_qc_columns_y[y] = INVALID_VALUE;
			}
		}

		/* computing percentiles for y, night */
		for ( ii = NEE_05_Y; ii <= NEE_95_Y; ii++ ) {
			if ( night_d ) {
				rows_night[index].night[ii] = get_percentile_and_qc(rows_night[index].night_columns_y, rows_night[index].night_qc_columns_y
												, PERCENTILES_COUNT_2-1, percentiles_test_1[ii-NEE_05_Y]
												/* +7 for indexing QC */
												, &rows_night[index].night[ii+7], &error);
			} else {
				rows_night[index].night[ii] = INVALID_VALUE;
				rows_night[index].night[ii+7] = INVALID_VALUE;
			}
			if ( error ) {
				printf("unable to get night %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				free(days);
				free(nights);
				free(rows_night);
				return NULL;
			}
		}

		/* computing percentiles for y, day */
		for ( ii = NEE_05_Y; ii <= NEE_95_Y; ii++ ) {
			if ( day_d ) {
				rows_night[index].day[ii] = get_percentile_and_qc(rows_night[index].day_columns_y, rows_night[index].day_qc_columns_y
												, PERCENTILES_COUNT_2-1, percentiles_test_1[ii-NEE_05_Y]
												/* +7 for indexing QC */
												, &rows_night[index].day[ii+7], &error);
			} else {
				rows_night[index].day[ii] = INVALID_VALUE;
				rows_night[index].day[ii+7] = INVALID_VALUE;
			}
			if ( error ) {
				printf("unable to get day %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				free(days);
				free(nights);
				free(rows_night);
				return NULL;
			}
		}
		
		/* ... per c */
		if ( (dataset->years_count > 2) ) {			
			for ( y = 0; y < PERCENTILES_COUNT_2; y++ ) {
				night_d = 0;
				day_d = 0;
				nights[0] = 0.0;
				days[0] = 0.0;
				nights_qc = 0.0;
				days_qc = 0.0;

				/* */
				for ( i = 0; i < rows_per_day; i++ ) {
					value = nee_matrix_c[row+i].nee[y];
					qc = nee_matrix_c[row+i].qc[y];
 
					/* night ? */
					if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_VALUE], 0.0) ) {
						if ( !IS_INVALID_VALUE(value) ) {
							nights[0] += value;
							nights_qc += qc;
							++night_d;
						}				
					} else {
						if ( !IS_INVALID_VALUE(value) ) {
							days[0] += value;
							days_qc += qc;
							++day_d;
						}
					}
				}
				if ( night_d ) {
					rows_night[index].night_columns_c[y] = nights[0] / night_d;
					rows_night[index].night_qc_columns_c[y] = nights_qc / night_d;
				} else {
					rows_night[index].night_columns_c[y] = INVALID_VALUE;
					rows_night[index].night_qc_columns_c[y] = INVALID_VALUE;
				}
				if ( day_d ) {
					rows_night[index].day_columns_c[y] = days[0] / day_d;
					rows_night[index].day_qc_columns_c[y] = days_qc / day_d;
				} else {
					rows_night[index].day_columns_c[y] = INVALID_VALUE;
					rows_night[index].day_qc_columns_c[y] = INVALID_VALUE;
				}
			}

			/* computing percentiles for c, night */
			for ( ii = NEE_05_C; ii <= NEE_95_C; ii++ ) {
				if ( night_d ) {
					rows_night[index].night[ii] = get_percentile_and_qc(rows_night[index].night_columns_c, rows_night[index].night_qc_columns_c
													, PERCENTILES_COUNT_2-1, percentiles_test_1[ii-NEE_05_C]
													/* +7 for indexing QC */
													, &rows_night[index].night[ii+7], &error);
				} else {
					rows_night[index].night[ii] = INVALID_VALUE;
					rows_night[index].night[ii+7] = INVALID_VALUE;
				}
				if ( error ) {
					printf("unable to get night %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					free(days);
					free(nights);
					free(rows_night);
					return NULL;
				}
			}

			/* computing percentiles for c, day */
			for ( ii = NEE_05_C; ii <= NEE_95_C; ii++ ) {
				if ( day_d ) {
					rows_night[index].day[ii] = get_percentile_and_qc(rows_night[index].day_columns_c, rows_night[index].day_qc_columns_c
													, PERCENTILES_COUNT_2-1, percentiles_test_1[ii-NEE_05_C]
													/* +7 for indexing QC */
													, &rows_night[index].day[ii+7], &error);
				} else {
					rows_night[index].day[ii] = INVALID_VALUE;
					rows_night[index].day[ii+7] = INVALID_VALUE;
				}
				if ( error ) {
					printf("unable to get day %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					free(days);
					free(nights);
					free(rows_night);
					return NULL;
				}
			}
		}

		/* */
		++index;
	}

	/* free memory */
	free(days);
	free(nights);

	/* ok */
	return rows_night;
}

/* */
static int compute_night_rand(const DATASET *const dataset, ROW_NIGHT *const rows_night, const RAND_UNC_ROW *const unc_rows) {
	int i;
	int y;
	int row;
	int rows_per_day;
	int night_d;
	int day_d;
	int index;
	PREC value;
	PREC qc;
	PREC *nights;
	PREC *days;
	int rows_count;
	
	rows_per_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;

	/* compute rows count */
	rows_count = dataset->rows_count / rows_per_day;

	/* alloc memory */
	nights = malloc(rows_count*sizeof*nights);
	if ( ! nights ) {
		puts(err_out_of_memory);
		return 0;
	}
	days = malloc(rows_count*sizeof*days);
	if ( ! days ) {
		puts(err_out_of_memory);
		free(nights);
		return 0;
	}

	rows_per_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;
	
	index = 0;
	for ( row = 0; row < dataset->rows_count; row += rows_per_day ) {
		/* loop on each var to compute */
		for ( y = NIGHT_QC_VALUES; y < NIGHT_RAND_VALUES; y++ ) {
			/* do not compute _c if years count is less than 3 */
			if ( (dataset->years_count < 3) &&
					((NEE_REF_C == y) || (NEE_UST50_C == y) || (NEE_REF_C_RAND == y) || (NEE_UST50_C_RAND == y)) ) {
				continue;
			}
			rows_night[index].night[y] = 0.0;
			rows_night[index].night_qc[y] = 0.0;
			if ( y < NIGHT_QC_VALUES ) {
				rows_night[index].night_std[y] = INVALID_VALUE;
			}
			rows_night[index].day[y] = 0.0;
			rows_night[index].day_qc[y] = 0.0;
			if ( y < NIGHT_QC_VALUES ) {
				rows_night[index].day_std[y] = INVALID_VALUE;
			}

			night_d = 0;
			day_d = 0;

			for ( i = 0; i < rows_per_day; i++ ) {
				switch ( y ) {
					case NEE_REF_Y_RAND:
						value = unc_rows[row+i].rand[NEE_REF_Y_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_REF_Y_UNC];
					break;

					case NEE_UST50_Y_RAND:
						value = unc_rows[row+i].rand[NEE_UST50_Y_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_UST50_Y_UNC];
					break;

					case NEE_REF_C_RAND:
						value = unc_rows[row+i].rand[NEE_REF_C_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_REF_C_UNC];
					break;

					case NEE_UST50_C_RAND:
						value = unc_rows[row+i].rand[NEE_UST50_C_UNC];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
						}
						qc = unc_rows[row+i].qc[NEE_UST50_C_UNC];
					break;
				}

				/* night ? */
				if ( ARE_FLOATS_EQUAL(dataset->rows[row+i].value[RPOT_VALUE], 0.0) ) {
					if ( !IS_INVALID_VALUE(value) ) {
						rows_night[index].night[y] += value;
						nights[night_d++] = value;
						rows_night[index].night_qc[y] += qc;
					}				
				} else {
					if ( !IS_INVALID_VALUE(value) ) {
						rows_night[index].day[y] += value;
						days[day_d++] = value;
						rows_night[index].day_qc[y] += qc;
					}
				}
			}

			/* compute stuff */
			if ( night_d ) {
				rows_night[index].night[y] = SQRT(rows_night[index].night[y]) / night_d;
				rows_night[index].night_d_rand[y-NIGHT_QC_VALUES] = night_d;
				rows_night[index].night_qc[y] /= night_d;
			} else {
				rows_night[index].night[y] = INVALID_VALUE;
				rows_night[index].night_d_rand[y-NIGHT_QC_VALUES] = 0;
			}

			if ( day_d ) {
				rows_night[index].day[y] = SQRT(rows_night[index].day[y]) / day_d;
				rows_night[index].day_d_rand[y-NIGHT_QC_VALUES] = day_d;
				rows_night[index].day_qc[y] /= day_d;
			} else {
				rows_night[index].day[y] = INVALID_VALUE;
				rows_night[index].day_d_rand[y-NIGHT_QC_VALUES] = 0;
			}
		}
		++index;
	}
	free(days);
	free(nights);
	return 1;
}

/* */
static void rand_unc_dd(RAND_UNC_ROW *const unc_rows, RAND_UNC_ROW *const unc_rows_aggr, const int rows_count, const int years_count, const int hourly) {
	int i;
	int j;
	int day;
	int rows_per_day;

	assert(unc_rows && unc_rows_aggr);

	rows_per_day = hourly ? 24 : 48;

	/* loop on each row */
	day = 0;
	for ( i = 0; i < rows_count; i += rows_per_day ) {
		unc_rows_aggr[day].rand[NEE_REF_Y_UNC] = 0.0;
		unc_rows_aggr[day].rand[NEE_UST50_Y_UNC] = 0.0;
		unc_rows_aggr[day].samples_count[NEE_REF_Y_UNC] = 0;
		unc_rows_aggr[day].samples_count[NEE_UST50_Y_UNC] = 0;
		if ( years_count > 2 ) {
			unc_rows_aggr[day].rand[NEE_REF_C_UNC] = 0.0;
			unc_rows_aggr[day].rand[NEE_UST50_C_UNC] = 0.0;
			unc_rows_aggr[day].samples_count[NEE_REF_C_UNC] = 0;
			unc_rows_aggr[day].samples_count[NEE_UST50_C_UNC] = 0;
		}
		for ( j = 0; j < rows_per_day; j++ ) {
			if ( !IS_INVALID_VALUE(unc_rows[i+j].rand[NEE_REF_Y_UNC]) ) {
				unc_rows_aggr[day].rand[NEE_REF_Y_UNC] += (unc_rows[i+j].rand[NEE_REF_Y_UNC] * unc_rows[i+j].rand[NEE_REF_Y_UNC]);
				++unc_rows_aggr[day].samples_count[NEE_REF_Y_UNC];
			}
			if ( !IS_INVALID_VALUE(unc_rows[i+j].rand[NEE_UST50_Y_UNC]) ) {
				unc_rows_aggr[day].rand[NEE_UST50_Y_UNC] += (unc_rows[i+j].rand[NEE_UST50_Y_UNC] * unc_rows[i+j].rand[NEE_UST50_Y_UNC]);
				++unc_rows_aggr[day].samples_count[NEE_UST50_Y_UNC];
			}
			if ( years_count > 2 ) {
				if ( !IS_INVALID_VALUE(unc_rows[i+j].rand[NEE_REF_C_UNC]) ) {
					unc_rows_aggr[day].rand[NEE_REF_C_UNC] += (unc_rows[i+j].rand[NEE_REF_C_UNC] * unc_rows[i+j].rand[NEE_REF_C_UNC]);
					++unc_rows_aggr[day].samples_count[NEE_REF_C_UNC];
				}
				if ( !IS_INVALID_VALUE(unc_rows[i+j].rand[NEE_UST50_C_UNC]) ) {
					unc_rows_aggr[day].rand[NEE_UST50_C_UNC] += (unc_rows[i+j].rand[NEE_UST50_C_UNC] * unc_rows[i+j].rand[NEE_UST50_C_UNC]);
					++unc_rows_aggr[day].samples_count[NEE_UST50_C_UNC];
				}
			}
		}
		if ( unc_rows_aggr[day].samples_count[NEE_REF_Y_UNC] ) {
			unc_rows_aggr[day].rand[NEE_REF_Y_UNC] = SQRT(unc_rows_aggr[day].rand[NEE_REF_Y_UNC]) / unc_rows_aggr[day].samples_count[NEE_REF_Y_UNC];
			unc_rows_aggr[day].rand[NEE_REF_Y_UNC] *= CO2TOC;
		} else {
			unc_rows_aggr[day].rand[NEE_REF_Y_UNC] = INVALID_VALUE;
		}

		if ( unc_rows_aggr[day].samples_count[NEE_UST50_Y_UNC] ) {
			unc_rows_aggr[day].rand[NEE_UST50_Y_UNC] = SQRT(unc_rows_aggr[day].rand[NEE_UST50_Y_UNC]) / unc_rows_aggr[day].samples_count[NEE_UST50_Y_UNC];
			unc_rows_aggr[day].rand[NEE_UST50_Y_UNC] *= CO2TOC;
		} else {
			unc_rows_aggr[day].rand[NEE_UST50_Y_UNC] = INVALID_VALUE;
		}

		if ( years_count > 2 ) {
			if ( unc_rows_aggr[day].samples_count[NEE_REF_C_UNC] ) {
				unc_rows_aggr[day].rand[NEE_REF_C_UNC] = SQRT(unc_rows_aggr[day].rand[NEE_REF_C_UNC]) / unc_rows_aggr[day].samples_count[NEE_REF_C_UNC];
				unc_rows_aggr[day].rand[NEE_REF_C_UNC] *= CO2TOC;
			} else {
				unc_rows_aggr[day].rand[NEE_REF_C_UNC] = INVALID_VALUE;
			}

			if ( unc_rows_aggr[day].samples_count[NEE_UST50_C_UNC] ) {
				unc_rows_aggr[day].rand[NEE_UST50_C_UNC] = SQRT(unc_rows_aggr[day].rand[NEE_UST50_C_UNC]) / unc_rows_aggr[day].samples_count[NEE_UST50_C_UNC];
				unc_rows_aggr[day].rand[NEE_UST50_C_UNC] *= CO2TOC;
			} else {
				unc_rows_aggr[day].rand[NEE_UST50_C_UNC] = INVALID_VALUE;
			}
		}
		++day;
	}
}

/*
	The aggregation of RANDUNC is based on the daily values.
	RANDUNC_WW = SQRT(SUM(RANDUNC_HH)^2)/NUM_HH
	the calculation is based on half hourly data, to start from the daily the equation changes in:
	RANDUNC_WW = SQRT[(SUM(RANDUNC_HH_DAY1)^2)+(SUM(RANDUNC_HH_DAY2)^2)+...+(SUM(RANDUNC_HH_DAY7)^2)]/(NUM_HH_DAY1+NUM_HH_DAY2+...+NUM_HH_DAY7)

	since the daily RANDUNC is also:
	RANDUNC_DD = SQRT(SUM(RANDUNC_HH)^2)/NUM_HH

	we ca say that:
	(SUM(RANDUNC_HH)^2)=(RANDUNC_DD^2)*(NUM_HH^2)

	merging the two we obtain that:
	RANDUNC_WW = SQRT[(SUM((RANDUNC_DD_DAY1^2)*(NUM_HH_DAY1^2)))+(SUM((RANDUNC_DD_DAY2^2)*(NUM_HH_DAY2^2)))+...+((SUM((RANDUNC_DD_DAY7^2)*(NUM_HH_DAY7^2))))]/(NUM_HH_DAY1+NUM_HH_DAY2+...+NUM_HH_DAY7)

	This is the equation used in the code. The same applied to all the other aggregations.
*/
static void rand_unc_ww(RAND_UNC_ROW *const unc_rows_aggr, RAND_UNC_ROW *const unc_rows_temp, const int rows_count, const int start_year, const int years_count) {
	int i;
	int k;
	int w;
	int week;
	int days_per_week;
	int year;
	PREC value;

	k = 0;
	w = 0;
	year = start_year;
	while ( k < rows_count ) {
		days_per_week = 7;
		for ( week = 0; week < 52; week++ ) {
			/* fix for last week */
			if ( 52 - 1 == week ) {
				days_per_week = (IS_LEAP_YEAR(year) ? 366 : 365) - 51*7;
			}
			/* */
			unc_rows_temp[week+w].rand[NEE_REF_Y_UNC] = 0.0;
			unc_rows_temp[week+w].rand[NEE_UST50_Y_UNC] = 0.0;
			unc_rows_temp[week+w].samples_count[NEE_REF_Y_UNC] = 0;
			unc_rows_temp[week+w].samples_count[NEE_UST50_Y_UNC] = 0;
			if ( years_count > 2 ) {
				unc_rows_temp[week+w].rand[NEE_REF_C_UNC] = 0.0;
				unc_rows_temp[week+w].rand[NEE_UST50_C_UNC] = 0.0;
				unc_rows_temp[week+w].samples_count[NEE_REF_C_UNC] = 0;
				unc_rows_temp[week+w].samples_count[NEE_UST50_C_UNC] = 0;
			}
			for ( i = 0; i < days_per_week; i++ ) {
				if ( ! IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_REF_Y_UNC]) ) {
					value = unc_rows_aggr[i+k].rand[NEE_REF_Y_UNC];
					value *= value;
					value *= (unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC]*unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC]);
					unc_rows_temp[week+w].rand[NEE_REF_Y_UNC] += value;
					unc_rows_temp[week+w].samples_count[NEE_REF_Y_UNC] += unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC];
				}
				if ( ! IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_UST50_Y_UNC]) ) {
					value = unc_rows_aggr[i+k].rand[NEE_UST50_Y_UNC];
					value *= value;
					value *= (unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC]*unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC]);
					unc_rows_temp[week+w].rand[NEE_UST50_Y_UNC] += value;
					unc_rows_temp[week+w].samples_count[NEE_UST50_Y_UNC] += unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC];
				}
				if ( years_count > 2 ) {
					if ( ! IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_REF_C_UNC]) ) {
						value = unc_rows_aggr[i+k].rand[NEE_REF_C_UNC];
						value *= value;
						value *= (unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC]*unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC]);
						unc_rows_temp[week+w].rand[NEE_REF_C_UNC] += value;
						unc_rows_temp[week+w].samples_count[NEE_REF_C_UNC] += unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC];
					}
					if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_UST50_C_UNC]) ) {
						value = unc_rows_aggr[i+k].rand[NEE_UST50_C_UNC];
						value *= value;
						value *= (unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC]*unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC]);
						unc_rows_temp[week+w].rand[NEE_UST50_C_UNC] += value;
						unc_rows_temp[week+w].samples_count[NEE_UST50_C_UNC] += unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC];
					}
				}
			}
			if ( unc_rows_temp[week+w].samples_count[NEE_REF_Y_UNC] ) {
				unc_rows_temp[week+w].rand[NEE_REF_Y_UNC] = SQRT(unc_rows_temp[week+w].rand[NEE_REF_Y_UNC]) / unc_rows_temp[week+w].samples_count[NEE_REF_Y_UNC];
			} else {
				unc_rows_temp[week+w].rand[NEE_REF_Y_UNC] = INVALID_VALUE;
			}

			if ( unc_rows_temp[week+w].samples_count[NEE_UST50_Y_UNC] ) {
				unc_rows_temp[week+w].rand[NEE_UST50_Y_UNC] = SQRT(unc_rows_temp[week+w].rand[NEE_UST50_Y_UNC]) / unc_rows_temp[week+w].samples_count[NEE_UST50_Y_UNC];
			} else {
				unc_rows_temp[week+w].rand[NEE_UST50_Y_UNC] = INVALID_VALUE;
			}

			if ( years_count > 2 ) {
				if ( unc_rows_temp[week+w].samples_count[NEE_REF_C_UNC] ) {
					unc_rows_temp[week+w].rand[NEE_REF_C_UNC] = SQRT(unc_rows_temp[week+w].rand[NEE_REF_C_UNC]) / unc_rows_temp[week+w].samples_count[NEE_REF_C_UNC];
				} else {
					unc_rows_temp[week+w].rand[NEE_REF_C_UNC] = INVALID_VALUE;
				}

				if ( unc_rows_temp[week+w].samples_count[NEE_UST50_C_UNC] ) {
					unc_rows_temp[week+w].rand[NEE_UST50_C_UNC] = SQRT(unc_rows_temp[week+w].rand[NEE_UST50_C_UNC]) / unc_rows_temp[week+w].samples_count[NEE_UST50_C_UNC];
				} else {
					unc_rows_temp[week+w].rand[NEE_UST50_C_UNC] = INVALID_VALUE;
				}
			}
			k += days_per_week;
		}
		++year;
		w += 52;
	}
}

/* 
	please see rand_unc_ww for infos
*/
static void rand_unc_mm(RAND_UNC_ROW *const unc_rows_aggr, RAND_UNC_ROW *const unc_rows_temp, const int rows_count, const int start_year, const int years_count) {
	int i;
	int k;
	int m;
	int month;
	int days_per_month_count;
	int year;
	PREC value;

	k = 0;
	year = start_year;
	m = 0;
	while ( k < rows_count ) {
		for ( month = 0; month < 12; month++ ) {
			/* compute days per month count */
			days_per_month_count = days_per_month[month];
			if ( (FEBRUARY == month) && IS_LEAP_YEAR(year) ) {
				++days_per_month_count;
			}

			/* */
			unc_rows_temp[month+m].rand[NEE_REF_Y_UNC] = 0.0;
			unc_rows_temp[month+m].rand[NEE_UST50_Y_UNC] = 0.0;
			unc_rows_temp[month+m].samples_count[NEE_REF_Y_UNC] = 0;
			unc_rows_temp[month+m].samples_count[NEE_UST50_Y_UNC] = 0;
			if ( years_count > 2 ) {
				unc_rows_temp[month+m].rand[NEE_REF_C_UNC] = 0.0;
				unc_rows_temp[month+m].rand[NEE_UST50_C_UNC] = 0.0;
				unc_rows_temp[month+m].samples_count[NEE_REF_C_UNC] = 0;
				unc_rows_temp[month+m].samples_count[NEE_UST50_C_UNC] = 0;
			}
			for ( i = 0; i < days_per_month_count; i++ ) {
				if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_REF_Y_UNC]) ) {
					value = unc_rows_aggr[i+k].rand[NEE_REF_Y_UNC];
					value *= value;
					value *= (unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC]*unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC]);
					unc_rows_temp[month+m].rand[NEE_REF_Y_UNC] += value;
					unc_rows_temp[month+m].samples_count[NEE_REF_Y_UNC] += unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC];
				}
				if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_UST50_Y_UNC]) ) {
					value = unc_rows_aggr[i+k].rand[NEE_UST50_Y_UNC];
					value *= value;
					value *= (unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC]*unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC]);
					unc_rows_temp[month+m].rand[NEE_UST50_Y_UNC] += value;
					unc_rows_temp[month+m].samples_count[NEE_UST50_Y_UNC] += unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC];
				}
				if ( years_count > 2 ) {
					if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_REF_C_UNC]) ) {
						value = unc_rows_aggr[i+k].rand[NEE_REF_C_UNC];
						value *= value;
						value *= (unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC]*unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC]);
						unc_rows_temp[month+m].rand[NEE_REF_C_UNC] += value;
						unc_rows_temp[month+m].samples_count[NEE_REF_C_UNC] += unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC];
					}
					if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_UST50_C_UNC]) ) {
						value = unc_rows_aggr[i+k].rand[NEE_UST50_C_UNC];
						value *= value;
						value *= (unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC]*unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC]);
						unc_rows_temp[month+m].rand[NEE_UST50_C_UNC] += value;
						unc_rows_temp[month+m].samples_count[NEE_UST50_C_UNC] += unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC];
					}
				}
			}
			if ( unc_rows_temp[month+m].samples_count[NEE_REF_Y_UNC] ) {
				unc_rows_temp[month+m].rand[NEE_REF_Y_UNC] = SQRT(unc_rows_temp[month+m].rand[NEE_REF_Y_UNC]) / unc_rows_temp[month+m].samples_count[NEE_REF_Y_UNC];
			} else {
				unc_rows_temp[month+m].rand[NEE_REF_Y_UNC] = INVALID_VALUE;
			}

			if ( unc_rows_temp[month+m].samples_count[NEE_UST50_Y_UNC] ) {
				unc_rows_temp[month+m].rand[NEE_UST50_Y_UNC] = SQRT(unc_rows_temp[month+m].rand[NEE_UST50_Y_UNC]) / unc_rows_temp[month+m].samples_count[NEE_UST50_Y_UNC];
			} else {
				unc_rows_temp[month+m].rand[NEE_UST50_Y_UNC] = INVALID_VALUE;
			}

			if ( years_count > 2 ) {
				if ( unc_rows_temp[month+m].samples_count[NEE_REF_C_UNC] ) {
					unc_rows_temp[month+m].rand[NEE_REF_C_UNC] = SQRT(unc_rows_temp[month+m].rand[NEE_REF_C_UNC]) / unc_rows_temp[month+m].samples_count[NEE_REF_C_UNC];
				} else {
					unc_rows_temp[month+m].rand[NEE_REF_C_UNC] = INVALID_VALUE;
				}

				if ( unc_rows_temp[month+m].samples_count[NEE_UST50_C_UNC] ) {
					unc_rows_temp[month+m].rand[NEE_UST50_C_UNC] = SQRT(unc_rows_temp[month+m].rand[NEE_UST50_C_UNC]) / unc_rows_temp[month+m].samples_count[NEE_UST50_C_UNC];
				} else {
					unc_rows_temp[month+m].rand[NEE_UST50_C_UNC] = INVALID_VALUE;
				}
			}
			k += days_per_month_count;
		}
		++year;
		m += 12;
	}
}

/* 
	please see rand_unc_ww for infos
*/
static void rand_unc_yy(RAND_UNC_ROW *const unc_rows_aggr, RAND_UNC_ROW *const unc_rows_temp, const int rows_count, const int start_year, const int years_count) {
	int i;
	int k;
	int rows_per_year_count;
	int year;
	int year_index;
	PREC value;

	k = 0;
	year_index = 0;
	year = start_year;
	while ( k < rows_count ) {
		rows_per_year_count = IS_LEAP_YEAR(year) ? 366: 365;

		/* */
		unc_rows_temp[year_index].rand[NEE_REF_Y_UNC] = 0.0;
		unc_rows_temp[year_index].rand[NEE_UST50_Y_UNC] = 0.0;
		unc_rows_temp[year_index].samples_count[NEE_REF_Y_UNC] = 0;
		unc_rows_temp[year_index].samples_count[NEE_UST50_Y_UNC] = 0;
		if ( years_count > 2 ) {
			unc_rows_temp[year_index].rand[NEE_REF_C_UNC] = 0.0;
			unc_rows_temp[year_index].rand[NEE_UST50_C_UNC] = 0.0;
			unc_rows_temp[year_index].samples_count[NEE_REF_C_UNC] = 0;
			unc_rows_temp[year_index].samples_count[NEE_UST50_C_UNC] = 0;
		}
		for ( i = 0; i < rows_per_year_count; i++ ) {
			if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_REF_Y_UNC]) ) {
				value = unc_rows_aggr[i+k].rand[NEE_REF_Y_UNC];
				value *= value;
				value *= (unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC]*unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC]);
				unc_rows_temp[year_index].rand[NEE_REF_Y_UNC] += value;
				unc_rows_temp[year_index].samples_count[NEE_REF_Y_UNC] += unc_rows_aggr[i+k].samples_count[NEE_REF_Y_UNC];
			}
			if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_UST50_Y_UNC]) ) {
				value = unc_rows_aggr[i+k].rand[NEE_UST50_Y_UNC];
				value *= value;
				value *= (unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC]*unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC]);
				unc_rows_temp[year_index].rand[NEE_UST50_Y_UNC] += value;
				unc_rows_temp[year_index].samples_count[NEE_UST50_Y_UNC] += unc_rows_aggr[i+k].samples_count[NEE_UST50_Y_UNC];
			}
			if ( years_count > 2 ) {
				if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_REF_C_UNC]) ) {
					value = unc_rows_aggr[i+k].rand[NEE_REF_C_UNC];
					value *= value;
					value *= (unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC]*unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC]);
					unc_rows_temp[year_index].rand[NEE_REF_C_UNC] += value;
					unc_rows_temp[year_index].samples_count[NEE_REF_C_UNC] += unc_rows_aggr[i+k].samples_count[NEE_REF_C_UNC];
				}
				if ( !IS_INVALID_VALUE(unc_rows_aggr[i+k].rand[NEE_UST50_C_UNC]) ) {
					value = unc_rows_aggr[i+k].rand[NEE_UST50_C_UNC];
					value *= value;
					value *= (unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC]*unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC]);
					unc_rows_temp[year_index].rand[NEE_UST50_C_UNC] += value;
					unc_rows_temp[year_index].samples_count[NEE_UST50_C_UNC] += unc_rows_aggr[i+k].samples_count[NEE_UST50_C_UNC];
				}
			}
		}
		if ( unc_rows_temp[year_index].samples_count[NEE_REF_Y_UNC] ) {
			unc_rows_temp[year_index].rand[NEE_REF_Y_UNC] = SQRT(unc_rows_temp[year_index].rand[NEE_REF_Y_UNC]) / unc_rows_temp[year_index].samples_count[NEE_REF_Y_UNC];
			unc_rows_temp[year_index].rand[NEE_REF_Y_UNC] *= rows_per_year_count;
		} else {
			unc_rows_temp[year_index].rand[NEE_REF_Y_UNC] = INVALID_VALUE;
		}

		if ( unc_rows_temp[year_index].samples_count[NEE_UST50_Y_UNC] ) {
			unc_rows_temp[year_index].rand[NEE_UST50_Y_UNC] = SQRT(unc_rows_temp[year_index].rand[NEE_UST50_Y_UNC]) / unc_rows_temp[year_index].samples_count[NEE_UST50_Y_UNC];
			unc_rows_temp[year_index].rand[NEE_UST50_Y_UNC] *= rows_per_year_count;
		} else {
			unc_rows_temp[year_index].rand[NEE_UST50_Y_UNC] = INVALID_VALUE;
		}

		if ( years_count > 2 ) {
			if ( unc_rows_temp[year_index].samples_count[NEE_REF_C_UNC] ) {
				unc_rows_temp[year_index].rand[NEE_REF_C_UNC] = SQRT(unc_rows_temp[year_index].rand[NEE_REF_C_UNC]) / unc_rows_temp[year_index].samples_count[NEE_REF_C_UNC];
				unc_rows_temp[year_index].rand[NEE_REF_C_UNC] *= rows_per_year_count;
			} else {
				unc_rows_temp[year_index].rand[NEE_REF_C_UNC] = INVALID_VALUE;
			}

			if ( unc_rows_temp[year_index].samples_count[NEE_UST50_C_UNC] ) {
				unc_rows_temp[year_index].rand[NEE_UST50_C_UNC] = SQRT(unc_rows_temp[year_index].rand[NEE_UST50_C_UNC]) / unc_rows_temp[year_index].samples_count[NEE_UST50_C_UNC];
				unc_rows_temp[year_index].rand[NEE_UST50_C_UNC] *= rows_per_year_count;
			} else {
				unc_rows_temp[year_index].rand[NEE_UST50_C_UNC] = INVALID_VALUE;
			}
		}
		k += rows_per_year_count;
		++year_index;
		++year;
	}
}

/* */
int save_info(const DATASET *const dataset, const char *const path, const eTimeRes timeres, const int ref_y, const int ref_c, PERCENTILE_Y *percentiles_y, PREC *percentiles_c) {
	const char *p;
	char buffer[BUFFER_SIZE];
	int i;
	FILE *f;

	/* get info */
	p = NULL;
	switch ( timeres ) {
		case HH_TR: p = info_hh; break;
		case DD_TR: p = info_dd; break;
		case WW_TR: p = info_ww; break;
		case MM_TR: p = info_mm; break;
		case YY_TR: p = info_yy; break;
		default: assert(0 && "bad time resolution specified.");
	}

	/* save info */
	sprintf(buffer, "%s%s_NEE_%s_info.txt", path, dataset->details->site, time_resolution[timeres]);
	f = fopen(buffer, "w");
	if  ( ! f ) {
		puts("unable to create info file.");
		return 0;
	}

	/* write vars details stuff */
	fputs(p, f);

	/* write u* stuff */
	if ( dataset->umna_count ) {
		fputs(info_utem, f);
		for ( i = 0; i < dataset->umna_count; ++i ) {
			fprintf(f, "%d,", dataset->umna[i].year);
			if ( USTAR_MP_METHOD == dataset->umna[i].method ) {
				fputs("MP\n", f);
			} else if ( USTAR_CP_METHOD == dataset->umna[i].method ) {
				fputs("CP\n", f);
			} else {
				fputs("MP+CP\n", f);
			}
		}
	}

	/* write u* threshold used */
	fputs("\nUSTAR THRESHOLDS USED IN NEE_ust50:\n", f);
	if ( dataset->years_count >= 3 ) {
		/* u* threshold used */
		fprintf(f, ustar_threshold_c, percentiles_c[PERCENTILES_COUNT_2-1]);
		for ( i = 0; i < dataset->years_count; i++ ) {
			fprintf(f, ustar_threshold_y, dataset->years[i].year, percentiles_y[i].value[PERCENTILES_COUNT_2-1]);
		}
		/* model efficiency */
		fputs(info_model_efficiency, f);
		fprintf(f, model_efficiency_c, percentiles_test_2[ref_c], percentiles_c[ref_c]);
		for ( i = 0; i < dataset->years_count; i++ ) {
			fprintf(f, model_efficiency_y, dataset->years[i].year, percentiles_test_2[ref_y], percentiles_y[i].value[ref_y]);
		}
	} else {
		/* u* threshold used */
		fprintf(f, ustar_threshold_y_one_year, percentiles_y[0].value[PERCENTILES_COUNT_2-1]);
		/* model efficiency */
		fputs(info_model_efficiency, f);
		fprintf(f, model_efficiency_y_one_year, percentiles_test_2[ref_y], percentiles_y[0].value[ref_y]);
	}
	fputs("\n", f);

	/* */
	fclose(f);

	/* save aux */
	sprintf(buffer, "%s%s_AUX_NEE_%s.csv", path, dataset->details->site, time_resolution[timeres]);
	f = fopen(buffer, "w");
	if  ( ! f ) {
		puts("unable to create aux file.");
		return 0;
	}
	fputs("VARIABLE,YEAR,PERCENTILE,THRESHOLD\n", f);
	if ( dataset->years_count >= 3 ) {
		fprintf(f, "NEE_CUT_USTAR50,-9999,-9999,%g\n", percentiles_c[PERCENTILES_COUNT_2-1]);
	}
	for ( i = 0; i < dataset->years_count; i++ ) {
		fprintf(f, "NEE_VUT_USTAR50,%d,-9999,%g\n", dataset->years[i].year, percentiles_y[i].value[PERCENTILES_COUNT_2-1]);
	}
	if ( dataset->years_count >= 3 ) {
		fprintf(f, "NEE_CUT_REF,-9999,%g,%g\n", percentiles_test_2[ref_c], percentiles_c[ref_c]);
	}
	for ( i = 0; i < dataset->years_count; i++ ) {
		fprintf(f, "NEE_VUT_REF,%d,%g,%g\n", dataset->years[i].year, percentiles_test_2[ref_y], percentiles_y[i].value[ref_y]);
	}
	fclose(f);

	/* */
	return 1;
}

/* */
int save_nee_matrix(const NEE_MATRIX *const m, const DATASET *const d, int type) {
	char *p;
	char buffer[BUFFER_SIZE];
#if 0 /* new naming convention */
	char tr[7] = "vut_";
#else
	char tr[5] = "y_";
#endif
	int i;
	int y;
	int j;
	int percentile;
	int row;
	int rows_per_day;
	FILE *f;
	TIMESTAMP *t;

	assert(m && ((type >= 0) && (type < TYPES)));

	rows_per_day = (HOURLY_TIMERES == d->details->timeres) ? 24 : 48;

	if ( type >= HH_C ) tr[0] = 'c';
	if ( type >= 5 ) type -= 5;
#if 0 /* new naming convention */
	strcpy(tr+4, time_resolution[type]);
	tr[6] = '\0';
#else
	strcpy(tr+2, time_resolution[type]);
	tr[4] = '\0';
#endif

	sprintf(buffer, "%s%s_NEE_percentiles_%s.csv", output_files_path, d->details->site, tr);
	f = fopen(buffer, "w");
	if ( !f ) {
		printf("unable to create %s\n\n", buffer);
		return 0;
	}
	switch ( type ) {
		case HH_TR:
		case WW_TR:
			p = TIMESTAMP_HEADER;
		break;

		default:
			p = TIMESTAMP_STRING;
	}
	fprintf(f, "%s,", p);
	for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
		fprintf(f, "%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
		if ( percentile < PERCENTILES_COUNT_2-1 ) {
			fputs(",", f);
		}
	}
	fputs("\n", f);
	j = 0;
	for ( i = 0; i < d->years_count; ++i ) {
		switch ( type ) {
			case HH_TR:
			case DD_TR:
				y = IS_LEAP_YEAR(d->years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
				if ( HOURLY_TIMERES == d->details->timeres ) {
					y /= 2;
				}
				if ( DD_TR == type ) y /= rows_per_day;
			break;

			case WW_TR:
				y = 52;
			break;

			case MM_TR:
				y = 12;
			break;

			case YY_TR:
				y = 1;
			break;
		}
		
		for ( row = 0; row < y; row++ ) {
			switch ( type ) {
				case HH_TR:
					t = timestamp_start_by_row(row, d->years[i].year, d->details->timeres);
					fprintf(f, "%04d%02d%02d%02d%02d,", t->YYYY, t->MM, t->DD, t->hh, t->mm);
					t = timestamp_end_by_row(row, d->years[i].year, d->details->timeres);
					fprintf(f, "%04d%02d%02d%02d%02d,", t->YYYY, t->MM, t->DD, t->hh, t->mm);
				break;

				case DD_TR:
					t = timestamp_start_by_row(row*rows_per_day, d->years[i].year, d->details->timeres);
					fprintf(f, "%04d%02d%02d,", t->YYYY, t->MM, t->DD);					
				break;

				case WW_TR:
					/* timestamp_start */
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, d->years[i].year, d->details->timeres, 1));
					/* timestamp_end */
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, d->years[i].year, d->details->timeres, 0));
				break;

				case MM_TR:
					fprintf(f, "%04d%02d,", d->years[i].year, row+1);
				break;

				case YY_TR:
					fprintf(f, "%d,", d->years[i].year);
				break;
			}

			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, "%g,%g", m[j+row].nee[percentile], m[j+row].qc[percentile]);
				if ( percentile < PERCENTILES_COUNT_2-1 ) {
					fputs(",", f);
				}
			}
			fputs("\n", f);
		}
		j += y;
	}

	fclose(f);

	return 1;
}

/* */
static void update_ref(const DATASET *const dataset
					   , ROW_NIGHT *const rows_night_daily
					   , const int daily_rows_count
					   , NEE_MATRIX *nee_matrix_y
					   , NEE_MATRIX *nee_matrix_c
					   , const int ref_y
					   , const int ref_c) {
	int i;
	int index;
	int row_daily;
	int rows_per_day;
	PREC value;
	PREC nights[48];
	PREC days[48];
	int nights_count;
	int days_count;

	rows_per_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;

	/* night & day y */
	for ( row_daily = 0; row_daily < daily_rows_count; ++row_daily ) {
		rows_night_daily[row_daily].night[NEE_REF_Y] = rows_night_daily[row_daily].night_columns_y[ref_y];
		rows_night_daily[row_daily].night_qc[NEE_REF_Y] = rows_night_daily[row_daily].night_qc_columns_y[ref_y];
		rows_night_daily[row_daily].day[NEE_REF_Y] = rows_night_daily[row_daily].day_columns_y[ref_y];
		rows_night_daily[row_daily].day_qc[NEE_REF_Y] = rows_night_daily[row_daily].day_qc_columns_y[ref_y];

		/* update std */
		nights_count = 0;
		days_count = 0;
		for ( i = 0; i < rows_per_day; i++ ) {
			/* night ? */
			index = row_daily*rows_per_day+i;
			value = nee_matrix_y[index].nee[ref_y];
			if ( ARE_FLOATS_EQUAL(dataset->rows[index].value[RPOT_VALUE], 0.0) ) {
				if ( ! IS_INVALID_VALUE(value) ) {
					nights[nights_count++] = value;
				}				
			} else {
				if ( ! IS_INVALID_VALUE(value) ) {
					days[days_count++] = value;				
				}
			}
		}

		if ( nights_count ) {
			rows_night_daily[row_daily].night_std[NEE_REF_Y] = get_standard_deviation(nights, nights_count);
		} else {
			rows_night_daily[row_daily].night_std[NEE_REF_Y] = INVALID_VALUE;
		}

		if ( days_count ) {
			rows_night_daily[row_daily].day_std[NEE_REF_Y] = get_standard_deviation(days, days_count);
		} else {
			rows_night_daily[row_daily].day_std[NEE_REF_Y] = INVALID_VALUE;
		}
	}

	/* night & day c */
	if ( dataset->years_count >= 3 ) {
		for ( row_daily = 0; row_daily < daily_rows_count; ++row_daily ) {
			rows_night_daily[row_daily].night[NEE_REF_C] = rows_night_daily[row_daily].night_columns_c[ref_c];
			rows_night_daily[row_daily].night_qc[NEE_REF_C] = rows_night_daily[row_daily].night_qc_columns_c[ref_c];
			rows_night_daily[row_daily].day[NEE_REF_C] = rows_night_daily[row_daily].day_columns_c[ref_c];
			rows_night_daily[row_daily].day_qc[NEE_REF_C] = rows_night_daily[row_daily].day_qc_columns_c[ref_c];

			/* update std */
			nights_count = 0;
			days_count = 0;
			for ( i = 0; i < rows_per_day; i++ ) {
				/* night ? */
				index = row_daily*rows_per_day+i;
				value = nee_matrix_c[index].nee[ref_c];
				if ( ARE_FLOATS_EQUAL(dataset->rows[index].value[RPOT_VALUE], 0.0) ) {
					if ( ! IS_INVALID_VALUE(value) ) {
						nights[nights_count++] = value;
					}				
				} else {
					if ( ! IS_INVALID_VALUE(value) ) {
						days[days_count++] = value;
					
					}
				}
			}

			if ( nights_count ) {
				rows_night_daily[row_daily].night_std[NEE_REF_C] = get_standard_deviation(nights, nights_count);
			} else {
				rows_night_daily[row_daily].night_std[NEE_REF_C] = INVALID_VALUE;
			}

			if ( days_count ) {
				rows_night_daily[row_daily].day_std[NEE_REF_C] = get_standard_deviation(days, days_count);
			} else {
				rows_night_daily[row_daily].day_std[NEE_REF_C] = INVALID_VALUE;
			}
		}
	}
}


/* update ww percentiles and qcs */
static int update_ww(const DATASET *dataset, const ROW_NIGHT *const rows_daily, const int rows_daily_count, ROW_NIGHT *const rows_weekly, const int rows_weekly_count) {
	int i;
	int ii;
	int j;
	int y;
	int z;
	int row;
	int index;
	int element;
	int rows_per_day;
	int year;
	int percentile;
	int error;
	PREC percentiles[PERCENTILES_COUNT_2-1];
	PREC qcs[PERCENTILES_COUNT_2-1];

	assert(dataset && rows_daily && rows_daily_count && rows_weekly && rows_weekly_count);

	rows_per_day = (HOURLY_TIMERES == dataset->details->timeres) ? 24 : 48;

	j = 0;
	index = 0;
	element = 0;
	for ( year = 0; year < dataset->years_count; year++ ) {
		y = IS_LEAP_YEAR(dataset->years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
		if ( HOURLY_TIMERES == dataset->details->timeres  ) {
			y /= 2;
		}
		y /= rows_per_day;

		for ( i = 0; i < 51; i++ ) {
			row = i*7;
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2-1; percentile++ ) {
				rows_weekly[index+i].night_columns_y[percentile] = 0.0;
				rows_weekly[index+i].day_columns_y[percentile] = 0.0;
				rows_weekly[index+i].night_qc_columns_y[percentile] = 0.0;
				rows_weekly[index+i].day_qc_columns_y[percentile] = 0.0;
				if ( dataset->years_count >= 3 ) {
					rows_weekly[index+i].night_columns_c[percentile] = 0.0;
					rows_weekly[index+i].day_columns_c[percentile] = 0.0;
					rows_weekly[index+i].night_qc_columns_c[percentile] = 0.0;
					rows_weekly[index+i].day_qc_columns_c[percentile] = 0.0;
				}
				for ( j = 0; j < 7; j++ ) {
					rows_weekly[index+i].night_columns_y[percentile] += rows_daily[element+row+j].night_columns_y[percentile];
					rows_weekly[index+i].day_columns_y[percentile] += rows_daily[element+row+j].day_columns_y[percentile];
					rows_weekly[index+i].night_qc_columns_y[percentile] += rows_daily[element+row+j].night_qc_columns_y[percentile];
					rows_weekly[index+i].day_qc_columns_y[percentile] += rows_daily[element+row+j].day_qc_columns_y[percentile];
					if ( dataset->years_count >= 3 ) {
						rows_weekly[index+i].night_columns_c[percentile] += rows_daily[element+row+j].night_columns_c[percentile];
						rows_weekly[index+i].day_columns_c[percentile] += rows_daily[element+row+j].day_columns_c[percentile];
						rows_weekly[index+i].night_qc_columns_c[percentile] += rows_daily[element+row+j].night_qc_columns_c[percentile];
						rows_weekly[index+i].day_qc_columns_c[percentile] += rows_daily[element+row+j].day_qc_columns_c[percentile];
					}
				}
				rows_weekly[index+i].night_columns_y[percentile] /= 7;
				rows_weekly[index+i].day_columns_y[percentile] /= 7;
				rows_weekly[index+i].night_qc_columns_y[percentile] /= 7;
				rows_weekly[index+i].day_qc_columns_y[percentile] /= 7;
				if ( dataset->years_count >= 3 ) {
					rows_weekly[index+i].night_columns_c[percentile] /= 7;
					rows_weekly[index+i].day_columns_c[percentile] /= 7;
					rows_weekly[index+i].night_qc_columns_c[percentile] /= 7;
					rows_weekly[index+i].day_qc_columns_c[percentile] /= 7;
				}
			}
		}
		row += j; /* 51*7 */; 
		z = y-row;
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2-1; percentile++ ) {
			rows_weekly[index+i].night_columns_y[percentile] = 0.0;
				rows_weekly[index+i].day_columns_y[percentile] = 0.0;
				rows_weekly[index+i].night_qc_columns_y[percentile] = 0.0;
				rows_weekly[index+i].day_qc_columns_y[percentile] = 0.0;
				if ( dataset->years_count >= 3 ) {
					rows_weekly[index+i].night_columns_c[percentile] = 0.0;
					rows_weekly[index+i].day_columns_c[percentile] = 0.0;
					rows_weekly[index+i].night_qc_columns_c[percentile] = 0.0;
					rows_weekly[index+i].day_qc_columns_c[percentile] = 0.0;
				}
			for ( j = 0; j < z; j++ ) {
				rows_weekly[index+i].night_columns_y[percentile] += rows_daily[element+row+j].night_columns_y[percentile];
				rows_weekly[index+i].day_columns_y[percentile] += rows_daily[element+row+j].day_columns_y[percentile];
				rows_weekly[index+i].night_qc_columns_y[percentile] += rows_daily[element+row+j].night_qc_columns_y[percentile];
				rows_weekly[index+i].day_qc_columns_y[percentile] += rows_daily[element+row+j].day_qc_columns_y[percentile];
				if ( dataset->years_count >= 3 ) {
					rows_weekly[index+i].night_columns_c[percentile] += rows_daily[element+row+j].night_columns_c[percentile];
					rows_weekly[index+i].day_columns_c[percentile] += rows_daily[element+row+j].day_columns_c[percentile];
					rows_weekly[index+i].night_qc_columns_c[percentile] += rows_daily[element+row+j].night_qc_columns_c[percentile];
					rows_weekly[index+i].day_qc_columns_c[percentile] += rows_daily[element+row+j].day_qc_columns_c[percentile];
				}
			}
			rows_weekly[index+i].night_columns_y[percentile] /= z;
			rows_weekly[index+i].day_columns_y[percentile] /= z;
			rows_weekly[index+i].night_qc_columns_y[percentile] /= z;
			rows_weekly[index+i].day_qc_columns_y[percentile] /= z;
			if ( dataset->years_count >= 3 ) {
				rows_weekly[index+i].night_columns_c[percentile] /= z;
				rows_weekly[index+i].day_columns_c[percentile] /= z;
				rows_weekly[index+i].night_qc_columns_c[percentile] /= z;
				rows_weekly[index+i].day_qc_columns_c[percentile] /= z;
			}
		}

		/* */
		index += 52;
		element += y;
	}

	/* compute percentiles */
	for ( i = 0; i < rows_weekly_count; ++i ) {
		/* vut */
		for ( ii = NEE_05_Y; ii <= NEE_95_Y; ii++ ) {
			/* night */
			for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
				percentiles[y] = rows_weekly[i].night_columns_y[y];
				qcs[y] = rows_weekly[i].night_qc_columns_y[y];
			}
			rows_weekly[i].night[ii] = get_percentile_and_qc(percentiles
															, qcs
															, PERCENTILES_COUNT_2-1
															, percentiles_test_1[ii-NEE_05_Y]
															/* +7 for indexing QC */
															, &rows_weekly[i].night[ii+7], &error);
			if ( error ) {
				printf("unable to get night ww %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				return 0;
			}

			/* day */
			for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
				percentiles[y] = rows_weekly[i].day_columns_y[y];
				qcs[y] = rows_weekly[i].day_qc_columns_y[y];
			}
			rows_weekly[i].day[ii] = get_percentile_and_qc(percentiles
															, qcs
															, PERCENTILES_COUNT_2-1
															, percentiles_test_1[ii-NEE_05_Y]
															/* +7 for indexing QC */
															, &rows_weekly[i].day[ii+7], &error);
			if ( error ) {
				printf("unable to get day ww %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				return 0;
			}
		}

		/* cut */
		if ( dataset->years_count >= 3 ) {
			for ( ii = NEE_05_C; ii <= NEE_95_C; ii++ ) {
				/* night */
				for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
					percentiles[y] = rows_weekly[i].night_columns_c[y];
					qcs[y] = rows_weekly[i].night_qc_columns_c[y];
				}
				rows_weekly[i].night[ii] = get_percentile_and_qc(percentiles
																, qcs
																, PERCENTILES_COUNT_2-1
																, percentiles_test_1[ii-NEE_05_C]
																/* +7 for indexing QC */
																, &rows_weekly[i].night[ii+7], &error);
				if ( error ) {
					printf("unable to get night ww %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					return 0;
				}

				/* day */
				for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
					percentiles[y] = rows_weekly[i].day_columns_c[y];
					qcs[y] = rows_weekly[i].day_qc_columns_c[y];
				}
				rows_weekly[i].day[ii] = get_percentile_and_qc(percentiles
																, qcs
																, PERCENTILES_COUNT_2-1
																, percentiles_test_1[ii-NEE_05_C]
																/* +7 for indexing QC */
																, &rows_weekly[i].day[ii+7], &error);
				if ( error ) {
					printf("unable to get day ww %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					return 0;
				}
			}
		}
	}
	return 1;
}

/* update mm percentiles and qcs */
static int update_mm(const DATASET *dataset, const ROW_NIGHT *const rows_daily, const int rows_daily_count, ROW_NIGHT *const rows_monthly, const int rows_monthly_count) {
	int i;
	int ii;
	int j;
	int y;
	int z;
	int row;
	int index;
	int year;
	int percentile;
	int error;
	PREC percentiles[PERCENTILES_COUNT_2-1];
	PREC qcs[PERCENTILES_COUNT_2-1];

	assert(dataset && rows_daily && rows_daily_count && rows_monthly && rows_monthly_count);

	index = 0;
	year = dataset->years[0].year;
	for ( row = 0; row < rows_daily_count; ) {
		for ( i = 0; i < 12; i++ ) {
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2-1; percentile++ ) {
				rows_monthly[index+i].night_columns_y[percentile] = 0.0;
				rows_monthly[index+i].day_columns_y[percentile] = 0.0;
				rows_monthly[index+i].night_qc_columns_y[percentile] = 0.0;
				rows_monthly[index+i].day_qc_columns_y[percentile] = 0.0;
				if ( dataset->years_count >= 3 ) {
					rows_monthly[index+i].night_columns_c[percentile] = 0.0;
					rows_monthly[index+i].day_columns_c[percentile] = 0.0;
					rows_monthly[index+i].night_qc_columns_c[percentile] = 0.0;
					rows_monthly[index+i].day_qc_columns_c[percentile] = 0.0;
				}
				z = days_per_month[i];
				if ( (1 == i) && IS_LEAP_YEAR(year) ) {
					++z;
				}
				for ( j = 0; j < z; j++ ) {
					rows_monthly[index+i].night_columns_y[percentile] += rows_daily[row+j].night_columns_y[percentile];
					rows_monthly[index+i].day_columns_y[percentile] += rows_daily[row+j].day_columns_y[percentile];
					rows_monthly[index+i].night_qc_columns_y[percentile] += rows_daily[row+j].night_qc_columns_y[percentile];
					rows_monthly[index+i].day_qc_columns_y[percentile] += rows_daily[row+j].day_qc_columns_y[percentile];
					if ( dataset->years_count >= 3 ) {
						rows_monthly[index+i].night_columns_c[percentile] += rows_daily[row+j].night_columns_c[percentile];
						rows_monthly[index+i].day_columns_c[percentile] += rows_daily[row+j].day_columns_c[percentile];
						rows_monthly[index+i].night_qc_columns_c[percentile] += rows_daily[row+j].night_qc_columns_c[percentile];
						rows_monthly[index+i].day_qc_columns_c[percentile] += rows_daily[row+j].day_qc_columns_c[percentile];
					}
				}
				rows_monthly[index+i].night_columns_y[percentile] /= z;
				rows_monthly[index+i].day_columns_y[percentile] /= z;
				rows_monthly[index+i].night_qc_columns_y[percentile] /= z;
				rows_monthly[index+i].day_qc_columns_y[percentile] /= z;
				if ( dataset->years_count >= 3 ) {
					rows_monthly[index+i].night_columns_c[percentile] /= z;
					rows_monthly[index+i].day_columns_c[percentile] /= z;
					rows_monthly[index+i].night_qc_columns_c[percentile] /= z;
					rows_monthly[index+i].day_qc_columns_c[percentile] /= z;
				}
			}
			row += z;
		}
		++year;
		index += i;
	}

	/* compute percentiles */
	for ( i = 0; i < rows_monthly_count; ++i ) {
		/* vut */
		for ( ii = NEE_05_Y; ii <= NEE_95_Y; ii++ ) {
			/* night */
			for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
				percentiles[y] = rows_monthly[i].night_columns_y[y];
				qcs[y] = rows_monthly[i].night_qc_columns_y[y];
			}
			rows_monthly[i].night[ii] = get_percentile_and_qc(percentiles
															, qcs
															, PERCENTILES_COUNT_2-1
															, percentiles_test_1[ii-NEE_05_Y]
															/* +7 for indexing QC */
															, &rows_monthly[i].night[ii+7], &error);
			if ( error ) {
				printf("unable to get night mm %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				return 0;
			}

			/* day */
			for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
				percentiles[y] = rows_monthly[i].day_columns_y[y];
				qcs[y] = rows_monthly[i].day_qc_columns_y[y];
			}
			rows_monthly[i].day[ii] = get_percentile_and_qc(percentiles
															, qcs
															, PERCENTILES_COUNT_2-1
															, percentiles_test_1[ii-NEE_05_Y]
															/* +7 for indexing QC */
															, &rows_monthly[i].day[ii+7], &error);
			if ( error ) {
				printf("unable to get day mm %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				return 0;
			}
		}

		/* cut */
		if ( dataset->years_count >= 3 ) {
			for ( ii = NEE_05_C; ii <= NEE_95_C; ii++ ) {
				/* night */
				for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
					percentiles[y] = rows_monthly[i].night_columns_c[y];
					qcs[y] = rows_monthly[i].night_qc_columns_c[y];
				}
				rows_monthly[i].night[ii] = get_percentile_and_qc(percentiles
																, qcs
																, PERCENTILES_COUNT_2-1
																, percentiles_test_1[ii-NEE_05_C]
																/* +7 for indexing QC */
																, &rows_monthly[i].night[ii+7], &error);
				if ( error ) {
					printf("unable to get night mm %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					return 0;
				}

				/* day */
				for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
					percentiles[y] = rows_monthly[i].day_columns_c[y];
					qcs[y] = rows_monthly[i].day_qc_columns_c[y];
				}
				rows_monthly[i].day[ii] = get_percentile_and_qc(percentiles
																, qcs
																, PERCENTILES_COUNT_2-1
																, percentiles_test_1[ii-NEE_05_C]
																/* +7 for indexing QC */
																, &rows_monthly[i].day[ii+7], &error);
				if ( error ) {
					printf("unable to get day mm %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					return 0;
				}
			}
		}
	}
	return 1;
}


/* update yy percentiles and qcs */
static int update_yy(const DATASET *dataset, const ROW_NIGHT *const rows_daily, const int rows_daily_count, ROW_NIGHT *const rows_yearly, const int rows_yearly_count) {
	int i;
	int ii;
	int j;
	int y;
	int row;
	int index;
	int year;
	int percentile;
	int error;
	PREC percentiles[PERCENTILES_COUNT_2-1];
	PREC qcs[PERCENTILES_COUNT_2-1];

	assert(dataset && rows_daily && rows_daily_count && rows_yearly && rows_yearly_count);

	index = 0;
	year = dataset->years[0].year;
	for ( row = 0; row < rows_daily_count; ) {
		y = IS_LEAP_YEAR(year) ? 366 : 365;
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2-1; percentile++ ) {
			rows_yearly[index].night_columns_y[percentile] = 0.0;
			rows_yearly[index].day_columns_y[percentile] = 0.0;
			rows_yearly[index].night_qc_columns_y[percentile] = 0.0;
			rows_yearly[index].day_qc_columns_y[percentile] = 0.0;
			if ( dataset->years_count >= 3 ) {
				rows_yearly[index].night_columns_c[percentile] = 0.0;
				rows_yearly[index].day_columns_c[percentile] = 0.0;
				rows_yearly[index].night_qc_columns_c[percentile] = 0.0;
				rows_yearly[index].day_qc_columns_c[percentile] = 0.0;
			}
			for ( j = 0; j < y; j++ ) {
				rows_yearly[index].night_columns_y[percentile] += rows_daily[row+j].night_columns_y[percentile];
				rows_yearly[index].day_columns_y[percentile] += rows_daily[row+j].day_columns_y[percentile];
				rows_yearly[index].night_qc_columns_y[percentile] += rows_daily[row+j].night_qc_columns_y[percentile];
				rows_yearly[index].day_qc_columns_y[percentile] += rows_daily[row+j].day_qc_columns_y[percentile];
				if ( dataset->years_count >= 3 ) {
					rows_yearly[index].night_columns_c[percentile] += rows_daily[row+j].night_columns_c[percentile];
					rows_yearly[index].day_columns_c[percentile] += rows_daily[row+j].day_columns_c[percentile];
					rows_yearly[index].night_qc_columns_c[percentile] += rows_daily[row+j].night_qc_columns_c[percentile];
					rows_yearly[index].day_qc_columns_c[percentile] += rows_daily[row+j].day_qc_columns_c[percentile];
				}
			}
			rows_yearly[index].night_columns_y[percentile] /= y;
			rows_yearly[index].day_columns_y[percentile] /= y;
			rows_yearly[index].night_qc_columns_y[percentile] /= y;
			rows_yearly[index].day_qc_columns_y[percentile] /= y;
			if ( dataset->years_count >= 3 ) {
				rows_yearly[index].night_columns_c[percentile] /= y;
				rows_yearly[index].day_columns_c[percentile] /= y;
				rows_yearly[index].night_qc_columns_c[percentile] /= y;
				rows_yearly[index].day_qc_columns_c[percentile] /= y;
			}
		}
		row += y;
		++year;
		++index;
	}
		
	/* compute percentiles */
	for ( i = 0; i < rows_yearly_count; ++i ) {
		/* vut */
		for ( ii = NEE_05_Y; ii <= NEE_95_Y; ii++ ) {
			/* night */
			for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
				percentiles[y] = rows_yearly[i].night_columns_y[y];
				qcs[y] = rows_yearly[i].night_qc_columns_y[y];
			}
			rows_yearly[i].night[ii] = get_percentile_and_qc(percentiles
															, qcs
															, PERCENTILES_COUNT_2-1
															, percentiles_test_1[ii-NEE_05_Y]
															/* +7 for indexing QC */
															, &rows_yearly[i].night[ii+7], &error);
			if ( error ) {
				printf("unable to get night yy %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				return 0;
			}

			/* day */
			for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
				percentiles[y] = rows_yearly[i].day_columns_y[y];
				qcs[y] = rows_yearly[i].day_qc_columns_y[y];
			}
			rows_yearly[i].day[ii] = get_percentile_and_qc(percentiles
															, qcs
															, PERCENTILES_COUNT_2-1
															, percentiles_test_1[ii-NEE_05_Y]
															/* +7 for indexing QC */
															, &rows_yearly[i].day[ii+7], &error);
			if ( error ) {
				printf("unable to get day yy %g %%percentile for y!\n", percentiles_test_1[ii-NEE_05_Y]);
				return 0;
			}
		}

		/* cut */
		if ( dataset->years_count >= 3 ) {
			for ( ii = NEE_05_C; ii <= NEE_95_C; ii++ ) {
				/* night */
				for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
					percentiles[y] = rows_yearly[i].night_columns_c[y];
					qcs[y] = rows_yearly[i].night_qc_columns_c[y];
				}
				rows_yearly[i].night[ii] = get_percentile_and_qc(percentiles
																, qcs
																, PERCENTILES_COUNT_2-1
																, percentiles_test_1[ii-NEE_05_C]
																/* +7 for indexing QC */
																, &rows_yearly[i].night[ii+7], &error);
				if ( error ) {
					printf("unable to get night yy %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					return 0;
				}

				/* day */
				for ( y = 0; y < PERCENTILES_COUNT_2-1; ++y ) {
					percentiles[y] = rows_yearly[i].day_columns_c[y];
					qcs[y] = rows_yearly[i].day_qc_columns_c[y];
				}
				rows_yearly[i].day[ii] = get_percentile_and_qc(percentiles
																, qcs
																, PERCENTILES_COUNT_2-1
																, percentiles_test_1[ii-NEE_05_C]
																/* +7 for indexing QC */
																, &rows_yearly[i].day[ii+7], &error);
				if ( error ) {
					printf("unable to get day yy %g %%percentile for c!\n", percentiles_test_1[ii-NEE_05_C]);
					return 0;
				}
			}
		}
	}
	return 1;
}

/* */
static int compute_rand_unc(const DATASET *const dataset
							, RAND_UNC_ROW *unc_rows
							, NEE_MATRIX *nee_matrix_y
							, NEE_MATRIX *nee_matrix_c
							, const int ref_y
							, const int ref_c) {
	int i;

	/* build-up dataset */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		unc_rows[i].mask = 0;
		unc_rows[i].rand[NEE_REF_Y_UNC] = INVALID_VALUE;
		unc_rows[i].rand[NEE_UST50_Y_UNC] = INVALID_VALUE;
		unc_rows[i].rand[NEE_REF_C_UNC] = INVALID_VALUE;
		unc_rows[i].rand[NEE_UST50_C_UNC] = INVALID_VALUE;

		unc_rows[i].value[NEE_REF_Y_UNC] = nee_matrix_y[i].nee[ref_y];
		unc_rows[i].qc[NEE_REF_Y_UNC] = nee_matrix_y[i].qc[ref_y];

		unc_rows[i].value[NEE_UST50_Y_UNC] = nee_matrix_y[i].nee[PERCENTILES_COUNT_2-1];
		unc_rows[i].qc[NEE_UST50_Y_UNC] = nee_matrix_y[i].qc[PERCENTILES_COUNT_2-1];

		if ( dataset->years_count >= 3 ) {
			unc_rows[i].value[NEE_REF_C_UNC] = nee_matrix_c[i].nee[ref_c];
			unc_rows[i].qc[NEE_REF_C_UNC] = nee_matrix_c[i].qc[ref_c];

			unc_rows[i].value[NEE_UST50_C_UNC] = nee_matrix_c[i].nee[PERCENTILES_COUNT_2-1];
			unc_rows[i].qc[NEE_UST50_C_UNC] = nee_matrix_c[i].qc[PERCENTILES_COUNT_2-1];
		}

		/* update mask */
		if ( !IS_INVALID_VALUE(unc_rows[i].value[NEE_REF_Y_UNC]) ) {
			unc_rows[i].mask |= GF_TOFILL_VALID;
		}

		unc_rows[i].value[SWIN_UNC] = dataset->rows[i].value[SWIN_VALUE];
		if ( !IS_INVALID_VALUE(unc_rows[i].value[SWIN_UNC]) ) {
			unc_rows[i].mask |= GF_VALUE1_VALID;
		}
		unc_rows[i].value[TA_UNC] = dataset->rows[i].value[TA_VALUE];
		if ( !IS_INVALID_VALUE(unc_rows[i].value[TA_UNC]) ) {
			unc_rows[i].mask |= GF_VALUE2_VALID;
		}
		unc_rows[i].value[VPD_UNC] = dataset->rows[i].value[VPD_VALUE];
		if ( !IS_INVALID_VALUE(unc_rows[i].value[VPD_UNC]) ) {
			unc_rows[i].mask |= GF_VALUE3_VALID;
		}

		/* set methods */
		unc_rows[i].method[NEE_REF_Y_UNC] = 1;
		if ( unc_rows[i].qc[NEE_REF_Y_UNC] ) {
			unc_rows[i].method[NEE_REF_Y_UNC] = 2;
		}

		unc_rows[i].method[NEE_UST50_Y_UNC] = 1;
		if ( unc_rows[i].qc[NEE_UST50_Y_UNC] ) {
			unc_rows[i].method[NEE_UST50_Y_UNC] = 2;
		}

		if ( dataset->years_count >= 3 ) {
			unc_rows[i].method[NEE_REF_C_UNC] = 1;
			if ( unc_rows[i].qc[NEE_REF_C_UNC] ) {
				unc_rows[i].method[NEE_REF_C_UNC] = 2;
			}

			unc_rows[i].method[NEE_UST50_C_UNC] = 1;
			if ( unc_rows[i].qc[NEE_UST50_C_UNC] ) {
				unc_rows[i].method[NEE_UST50_C_UNC] = 2;
			}
		}
	}
	
	/* compute random uncertainty */
	random_method_1(unc_rows, dataset->rows_count, NEE_REF_Y_UNC, HOURLY_TIMERES == dataset->details->timeres);
	if ( ! random_method_2(unc_rows, dataset->rows_count, NEE_REF_Y_UNC, HOURLY_TIMERES == dataset->details->timeres) ) {
		return 0;
	}

	/* update mask */
	for ( i = 0; i < dataset->rows_count; i++ ) {
		/* clear bit */
		unc_rows[i].mask &= ~(GF_TOFILL_VALID);
		/* set */
		if ( ! IS_INVALID_VALUE(unc_rows[i].value[NEE_UST50_Y_UNC]) ) {
			unc_rows[i].mask |= GF_TOFILL_VALID;
		}
	}

	random_method_1(unc_rows, dataset->rows_count, NEE_UST50_Y_UNC, HOURLY_TIMERES == dataset->details->timeres);
	if ( ! random_method_2(unc_rows, dataset->rows_count, NEE_UST50_Y_UNC, HOURLY_TIMERES == dataset->details->timeres) ) {
		return 0;
	}

	if ( dataset->years_count >= 3 ) {
		/* update mask */
		for ( i = 0; i < dataset->rows_count; i++ ) {
			/* clear bit */
			unc_rows[i].mask &= ~(GF_TOFILL_VALID);
			/* set */
			if ( ! IS_INVALID_VALUE(unc_rows[i].value[NEE_REF_C_UNC]) ) {
				unc_rows[i].mask |= GF_TOFILL_VALID;
			}
		}
		random_method_1(unc_rows, dataset->rows_count, NEE_REF_C_UNC, HOURLY_TIMERES == dataset->details->timeres);
		if ( ! random_method_2(unc_rows, dataset->rows_count, NEE_REF_C_UNC, HOURLY_TIMERES == dataset->details->timeres) ) {
			return 0;
		}

		/* update mask */
		for ( i = 0; i < dataset->rows_count; i++ ) {
			/* clear bit */
			unc_rows[i].mask &= ~(GF_TOFILL_VALID);
			/* set */
			if ( !IS_INVALID_VALUE(unc_rows[i].value[NEE_UST50_C_UNC]) ) {
				unc_rows[i].mask |= GF_TOFILL_VALID;
			}
		}
		/*
		{
			FILE *f = fopen("unc_matrix_c.csv", "w");
			if ( f ) {
				int i;

				fprintf(f, "ROW,REF,REF_QC,UST,UST_QC,MASK,SWIN,TA,VPD,REF_MET,UST_MET\n");
				for ( i = 0; i < dataset->rows_count; ++i ) {
					fprintf(f, "%d,%g,%d,%g,%d,%d,%g,%g,%g,%d,%d\n"
						, i+1
						, unc_rows[i].value[NEE_REF_C_UNC]
						, unc_rows[i].qc[NEE_REF_C_UNC]
						, unc_rows[i].value[NEE_UST50_C_UNC]
						, unc_rows[i].qc[NEE_UST50_C_UNC]
						, unc_rows[i].mask
						, unc_rows[i].value[SWIN_UNC]
						, unc_rows[i].value[TA_UNC]
						, unc_rows[i].value[VPD_UNC]
						, unc_rows[i].method[NEE_REF_C_UNC]
						, unc_rows[i].method[NEE_UST50_C_UNC]
					);
				}
				fclose(f);
			}
		}
		*/

		random_method_1(unc_rows, dataset->rows_count, NEE_UST50_C_UNC, HOURLY_TIMERES == dataset->details->timeres);
		if ( ! random_method_2(unc_rows, dataset->rows_count, NEE_UST50_C_UNC, HOURLY_TIMERES == dataset->details->timeres) ) {
			return 0;
		}
	}

	/*
	{
		FILE *f = fopen("unc_matrix_c_after.csv", "w");
		if ( f ) {
			int i;

			fprintf(f, "ROW,REF,REF_QC,UST,UST_QC,MASK,SWIN,TA,VPD,REF_MET,UST_MET\n");
			for ( i = 0; i < dataset->rows_count; ++i ) {
				fprintf(f, "%d,%g,%d,%g,%d,%d,%g,%g,%g,%d,%d\n"
					, i+1
					, unc_rows[i].value[NEE_REF_C_UNC]
					, unc_rows[i].qc[NEE_REF_C_UNC]
					, unc_rows[i].value[NEE_UST50_C_UNC]
					, unc_rows[i].qc[NEE_UST50_C_UNC]
					, unc_rows[i].mask
					, unc_rows[i].value[SWIN_UNC]
					, unc_rows[i].value[TA_UNC]
					, unc_rows[i].value[VPD_UNC]
					, unc_rows[i].method[NEE_REF_C_UNC]
					, unc_rows[i].method[NEE_UST50_C_UNC]
				);
			}
			fclose(f);
		}
	}
	*/
	return 1;
}

/* */
static void change_qcs(NEE_MATRIX *const nee_matrix, const int rows_count) {
	int i;
	int y;

	for ( i = 0; i < rows_count; ++i ) {
		for ( y = 0; y < PERCENTILES_COUNT_2; ++y ) {
			if ( nee_matrix[i].qc[y] < 2 ) {
				nee_matrix[i].qc[y] = 1;
			} else {
				nee_matrix[i].qc[y] = 0;
			}
		}
	}
}

/* */
static void revert_qcs(NEE_MATRIX *const nee_matrix, const int rows_count) {
	int i;
	int y;

	assert(nee_matrix);

	for ( i = 0; i < rows_count; ++i ) {
		for ( y = 0; y < PERCENTILES_COUNT_2; ++y ) {
			nee_matrix[i].qc[y] = nee_matrix[i].qc_ori[y];
		}
	}
}

/* */
int compute_datasets(DATASET *const datasets, const int datasets_count) {
	int i;
	int j;
	int y;
	int z;
	int row;
	int dataset;
	int year;
	int rows_count;
	int index;
	int element;
	int assigned;
	int error;
	int uts_count;
	int percentile;
	int ref_y_old;
	int ref_c_old;
	int ref_y;
	int ref_c;
	int daily_rows_count;
	int weekly_rows_count;
	int monthly_rows_count;
	int nights_rand_sum;
	int days_rand_sum;
	int is_leap;
	int exists;
	int columns_index[INPUT_VALUES];
	int columns_found_count;
	int rows_per_day;
	int no_gaps_filled_count;
	int on_error;
	int valid_values_count_night;
	int valid_values_count_day;
	char buffer[BUFFER_SIZE];
	char buffer2[BUFFER_SIZE];
	char *p;
	char *token;
	PREC value;
	FILE *f;
	PREC nee_ref_joinUnc_y;
	PREC nee_ust50_joinUnc_y;
	PREC nee_ref_night_joinUnc_y;
	PREC nee_ref_day_joinUnc_y;
	PREC nee_ust50_night_joinUnc_y;
	PREC nee_ust50_day_joinUnc_y;
	PREC nee_ref_joinUnc_c;
	PREC nee_ust50_joinUnc_c;
	PREC nee_ref_night_joinUnc_c;
	PREC nee_ref_day_joinUnc_c;
	PREC nee_ust50_night_joinUnc_c;
	PREC nee_ust50_day_joinUnc_c;
	ROW_COPY *rows_copy;
	PREC *uts;
	PREC *percentiles_c;
	PERCENTILE_Y *percentiles_y;
	NEE_MATRIX *nee_matrix_y;
	NEE_MATRIX *nee_matrix_y_daily;
	NEE_MATRIX *nee_matrix_y_weekly;
	NEE_MATRIX *nee_matrix_y_monthly;
	NEE_MATRIX *nee_matrix_y_yearly;
	NEE_MATRIX *nee_matrix_c = NULL;			/* mandatory */
	NEE_MATRIX *nee_matrix_c_daily = NULL;		/* mandatory */
	NEE_MATRIX *nee_matrix_c_weekly = NULL;		/* mandatory */
	NEE_MATRIX *nee_matrix_c_monthly = NULL;	/* mandatory */
	NEE_MATRIX *nee_matrix_c_yearly = NULL;		/* mandatory */
	P_MATRIX *p_matrix_y;
	P_MATRIX *p_matrix_c = NULL;		/* mandatory */
	ROW_NIGHT *rows_night_daily;
	ROW_NIGHT *rows_night_weekly;
	ROW_NIGHT *rows_night_monthly;
	ROW_NIGHT *rows_night_yearly;
	RAND_UNC_ROW *unc_rows = NULL;		/* mandatory */
	RAND_UNC_ROW *unc_rows_aggr = NULL;	/* mandatory */
	RAND_UNC_ROW *unc_rows_temp = NULL;	/* mandatory */
	NEE_FLAG *nee_flags_y = NULL;	/* mandatory */
	NEE_FLAG *nee_flags_c = NULL;	/* mandatory */
	DD *details;
	TIMESTAMP *t;

	/* alloc memory */
	percentiles_c = malloc(PERCENTILES_COUNT_2*sizeof*percentiles_c);
	if ( !percentiles_c ) {
		puts(err_out_of_memory);
		return 0;
	}
	
	/* loop on each dataset */
	for ( dataset = 0; dataset < datasets_count; dataset++ ) {
		/* reset */
		on_error = 0;

		/* */
		rows_per_day = (HOURLY_TIMERES == datasets[dataset].details->timeres) ? 24 : 48;

		percentiles_y = malloc(datasets[dataset].years_count*sizeof*percentiles_y);
		if ( !percentiles_y ) {
			puts(err_out_of_memory);
			free(percentiles_c);
			return 0;
		}

		/* show */
		printf("processing %s, %d year%s:\n\n",	datasets[dataset].details->site,
												datasets[dataset].years_count,
												((datasets[dataset].years_count > 1) ? "s" : "")
		);

		/* allocate memory */
		nee_matrix_y = malloc(datasets[dataset].rows_count*sizeof*nee_matrix_y);
		if ( !nee_matrix_y ) {
			puts(err_out_of_memory);
			free(percentiles_c);
			free(percentiles_y);
			return 0;
		}

		if ( datasets[dataset].years_count >= 3 ) {
			nee_matrix_c = malloc(datasets[dataset].rows_count*sizeof*nee_matrix_c);
			if ( !nee_matrix_c ) {
				puts(err_out_of_memory);
				free(nee_matrix_y);
				free(percentiles_y);
				free(percentiles_c);
				return 0;
			}
		}

		rows_copy = malloc(datasets[dataset].rows_count*sizeof*rows_copy);
		if ( !rows_copy ) {
			puts(err_out_of_memory);
			free(nee_matrix_y);
			free(percentiles_y);
			free(percentiles_c);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			return 0;
		}

		datasets[dataset].rows = malloc(datasets[dataset].rows_count*sizeof*datasets[dataset].rows);
		if ( !datasets[dataset].rows ) {
			puts(err_out_of_memory);
			free(nee_matrix_y);
			free(percentiles_y);
			free(percentiles_c);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			free(rows_copy);
			return 0;
		}
		
		/* alloc memory for ust */
		i = datasets[dataset].years_count;
		if ( i < 3 ) {
			i = 3; /* this is for use uts with _y method that requires 600 rows max */
		}
		uts = malloc(BOOTSTRAPPING_TIMES*2*i*sizeof*uts);
		if ( !uts ) {
			puts(err_out_of_memory);
			free(nee_matrix_y);
			free(percentiles_y);
			free(percentiles_c);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			free(rows_copy);
			return 0;
		}

		/* alloc memory for unc */
		if ( ! no_rand_unc ) {
			unc_rows = malloc(datasets[dataset].rows_count*sizeof*unc_rows);
			if  ( !unc_rows ) {
				puts(err_out_of_memory);
				free(uts);
				free(nee_matrix_y);
				free(percentiles_y);
				free(percentiles_c);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
				}
				free(rows_copy);
				return 0;
			}

			/* */
			unc_rows_aggr = malloc((datasets[dataset].rows_count/rows_per_day)*sizeof*unc_rows_aggr);
			if  ( !unc_rows_aggr ) {
				puts(err_out_of_memory);
				free(unc_rows);
				free(uts);
				free(nee_matrix_y);
				free(percentiles_y);
				free(percentiles_c);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
				}
				free(rows_copy);
				return 0;
			}

			unc_rows_temp = malloc(datasets[dataset].years_count*52*sizeof*unc_rows_temp);
			if  ( !unc_rows_temp ) {
				puts(err_out_of_memory);
				free(unc_rows_aggr);
				free(unc_rows);
				free(uts);
				free(nee_matrix_y);
				free(percentiles_y);
				free(percentiles_c);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
				}
				free(rows_copy);
				return 0;
			}
		}

		/* alloc memory for ustar flags */
		if ( compute_nee_flags ) {
			nee_flags_y = malloc(datasets[dataset].rows_count*sizeof*nee_flags_y);
			if ( !nee_flags_y ) {
				puts(err_out_of_memory);
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(uts);
				free(nee_matrix_y);
				free(percentiles_y);
				free(percentiles_c);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
				}
				free(rows_copy);
				return 0;
			}

			if ( datasets[dataset].years_count >= 3 ) {
				nee_flags_c = malloc(datasets[dataset].rows_count*sizeof*nee_flags_c);
				if ( !nee_flags_c ) {
					puts(err_out_of_memory);
					free(nee_flags_y);
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(uts);
					free(nee_matrix_y);
					free(percentiles_y);
					free(percentiles_c);
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_matrix_c);
					}
					free(rows_copy);
					return 0;
				}
			}
		}

		/* reset index */
		index = 0;
		/* loop on each year */
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			/* show */
			printf("#%02d importing %d...", year+1, datasets[dataset].years[year].year);
			/* leap year ? */
			is_leap = IS_LEAP_YEAR(datasets[dataset].years[year].year);
			/* compute rows count */
			rows_count = is_leap ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
				rows_count /= 2;
			}

			/* database exists ? */
			if ( ! datasets[dataset].years[year].exist ) {
				/* adding null values */
				for ( i = 0; i < rows_count; i++ ) {
					/* set INVALID_VALUE each value */
					for ( y = 0; y < DATASET_VALUES; y++ ) {
						datasets[dataset].rows[index+i].value[y] = INVALID_VALUE;
					}
					/* set year */
					datasets[dataset].rows[index+i].value[YEAR_VALUE] = datasets[dataset].years[year].year;
					/* set rpot taken from first year */
					datasets[dataset].rows[index+i].value[RPOT_VALUE] = datasets[dataset].rows[i].value[RPOT_VALUE];
				}
				/* adjust rpot for leap year */
				if ( is_leap ) {
					if ( IS_LEAP_YEAR(datasets[dataset].years[0].year) ) {
						if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
							for ( i = YEAR_ROWS / 2; i < LEAP_YEAR_ROWS / 2; i++ ) {
								datasets[dataset].rows[index+i].value[RPOT_VALUE] = datasets[dataset].rows[i].value[RPOT_VALUE];
							}
						} else {
							for ( i = YEAR_ROWS; i < LEAP_YEAR_ROWS; i++ ) {
								datasets[dataset].rows[index+i].value[RPOT_VALUE] = datasets[dataset].rows[i].value[RPOT_VALUE];
							}
						}
					} else {
						if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
							/* doubled last day */
							for ( i = YEAR_ROWS / 2; i < LEAP_YEAR_ROWS / 2; i++ ) {
								datasets[dataset].rows[index+i].value[RPOT_VALUE] = datasets[dataset].rows[index-rows_per_day+i].value[RPOT_VALUE];
							}
						} else {
							/* doubled last day */
							for ( i = YEAR_ROWS; i < LEAP_YEAR_ROWS; i++ ) {
								datasets[dataset].rows[index+i].value[RPOT_VALUE] = datasets[dataset].rows[index-rows_per_day+i].value[RPOT_VALUE];
							}
						}
					}
				}
				/* alert */
				puts("ok (nothing found, null year added)");
			} else {
				/* build-up filename */
				sprintf(buffer, "%s%s_qca_nee_%d.csv", qc_auto_files_path, datasets[dataset].details->site, datasets[dataset].years[year].year);

				/* open file */
				f = fopen(buffer, "r");
				if ( !f ) {
					printf("unable to open %s\n\n", buffer);
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					free(percentiles_y);
					free(uts);
					free(rows_copy);
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_matrix_c);
					}
					on_error = 1;
					break;
				}

				/* skip details */
				details = parse_dd(f);
				if ( !details ) {
					fclose(f);
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					free(percentiles_y);
					free(uts);
					free(rows_copy);
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_matrix_c);
					}
					on_error = 1;
					break;
				}
				free_dd(details);

				/* parse header */
				if ( ! get_valid_line_from_file(f, buffer, BUFFER_SIZE) ) {
					puts("no header found!");
					fclose(f);
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					free(percentiles_y);
					free(uts);
					free(rows_copy);
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_matrix_c);
					}
					on_error = 1;
					break;
				}

				/*  check for timestamps */
				i = get_column_of(buffer, dataset_delimiter, TIMESTAMP_START_STRING);
				if ( -2 == i ) {
					puts(err_out_of_memory);
					fclose(f);
					return 0;
				} else if ( -1 == i ) {
					/*  check for timestamp */
					i = get_column_of(buffer, dataset_delimiter, TIMESTAMP_STRING);
					if ( -2 == i ) {
						puts(err_out_of_memory);
						fclose(f);
						return 0;
					} else if ( -1 == i ) {
						puts("no valid header found.");
						fclose(f);
						return 0;
					}
				} else {
					i = get_column_of(buffer, dataset_delimiter, TIMESTAMP_END_STRING);
					if ( -2 == i ) {
						puts(err_out_of_memory);
						fclose(f);
						return 0;
					} else if ( -1 == i ) {
						printf("unable to find %s column\n", TIMESTAMP_END_STRING);
						fclose(f);
						return 0;
					}
				}

				/* reset columns */
				for ( i = 0; i < INPUT_VALUES; i++ ) {
					columns_index[i] = -1;
				}
				
				/* parse header */
				columns_found_count = 0;
				for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
					for ( y = 0; y < INPUT_VALUES; y++ ) {
						/* create itp name */
						strcpy(buffer2, "itp");
						strcat(buffer2, input_columns_tokens[y]);
						if ( ! string_compare_i(token, input_columns_tokens[y]) || ! string_compare_i(token, buffer2) ) {
							// check if it is already assigned
							if ( columns_index[y] != -1 ) {
								printf("column %s already found at index %d\n", token, columns_index[y]);
								fclose(f);
								if ( compute_nee_flags ) {
									if ( datasets[dataset].years_count >= 3 ) {
										free(nee_flags_c);
									}
									free(nee_flags_y);
								}
								free(unc_rows_temp);
								free(unc_rows_aggr);
								free(unc_rows);
								free(nee_matrix_y);
								free(percentiles_y);
								free(uts);
								free(rows_copy);
								if ( datasets[dataset].years_count >= 3 ) {
									free(nee_matrix_c);
								}
								on_error = 1;
								break;
							} else {
								columns_index[y] = i;
								++columns_found_count;
								// do not skip, continue searching for redundant columns
							}
						}
					}
					if ( on_error ) {
						break;
					}
				}

				if ( on_error ) {
					break;
				}

				/* check imported values */
				if ( columns_found_count != INPUT_VALUES ) {
					for ( i = 0; i < INPUT_VALUES; i++ ) {
						if ( -1 == columns_index[i] ) {
							/* VPD can be missing */
							if ( VPD == i ) {
								continue;
							}
							printf("var %s is missing.\n\n", input_columns_tokens[i]);
							fclose(f);
							if ( compute_nee_flags ) {
								if ( datasets[dataset].years_count >= 3 ) {
									free(nee_flags_c);
								}
								free(nee_flags_y);
							}
							free(unc_rows_temp);
							free(unc_rows_aggr);
							free(unc_rows);
							free(nee_matrix_y);
							free(percentiles_y);
							free(uts);
							free(rows_copy);
							if ( datasets[dataset].years_count >= 3 ) {
								free(nee_matrix_c);
							}
							on_error = 1;
							break;
						}
					}
					if ( 1 == on_error ) {
						break;
					}
				}
					
				/* loop on each row */
				element = 0;
				while ( fgets(buffer, BUFFER_SIZE, f) ) {
					/* remove carriage return and newline */
					for ( i = 0; buffer[i]; i++ ) {
						if ( ('\n' == buffer[i]) || ('\r' == buffer[i]) ) {
							buffer[i] = '\0';
							break;
						}
					}

					/* skip empty lines */
					if ( !buffer[0] ) {
						continue;
					}

					/* prevent too many rows */
					if ( element++ == rows_count ) {
						printf("too many rows for %s, %d", datasets[dataset].details->site, datasets[dataset].years[year].year);
						fclose(f);
						if ( compute_nee_flags ) {
							if ( datasets[dataset].years_count >= 3 ) {
								free(nee_flags_c);
							}
							free(nee_flags_y);
						}
						free(unc_rows_temp);
						free(unc_rows_aggr);
						free(unc_rows);
						free(nee_matrix_y);
						free(percentiles_y);
						free(uts);
						free(rows_copy);
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_matrix_c);
						}
						on_error = 1;
						break;
					}

					/* reset values */
					for ( i = 0; i < REQUIRED_DATASET_VALUES; i++ ) {
						datasets[dataset].rows[index+element-1].value[i] = INVALID_VALUE;
					}
					datasets[dataset].rows[index+element-1].value[TA_QC_VALUE] = INVALID_VALUE;
					datasets[dataset].rows[index+element-1].value[SWIN_QC_VALUE] = INVALID_VALUE;
					datasets[dataset].rows[index+element-1].value[VPD_QC_VALUE] = INVALID_VALUE;

					assigned = 0;
					for ( token = string_tokenizer(buffer, dataset_delimiter, &p), i = 0; token; token = string_tokenizer(NULL, dataset_delimiter, &p), ++i ) {
						for ( y = 0; y < INPUT_VALUES; y++ ) {
							if ( i == columns_index[y] ) {
								/* convert string to prec */
								value = convert_string_to_prec(token, &error);
								if ( error ) {
									printf("unable to convert value %s at row %d, column %d\n", token, element+1, i+1);
									fclose(f);
									if ( compute_nee_flags ) {
										if ( datasets[dataset].years_count >= 3 ) {
											free(nee_flags_c);
										}
										free(nee_flags_y);
									}
									free(unc_rows_temp);
									free(unc_rows_aggr);
									free(unc_rows);
									free(nee_matrix_y);
									free(percentiles_y);
									free(uts);
									free(rows_copy);
									if ( datasets[dataset].years_count >= 3 ) {
										free(nee_matrix_c);
									}
									on_error = 1;
									break;
								}

								/* convert NaN to invalid value */
								if ( value != value ) {
									value = INVALID_VALUE;
								}

								datasets[dataset].rows[index+element-1].value[y] = value;
								++assigned;
							}
						}
						if ( on_error ) {
							break;
						}
					}
					if ( on_error ) {
						break;
					}		

					/* check assigned */
					if ( assigned != columns_found_count ) {
						printf("expected %d columns not %d\n", columns_found_count, assigned);
						fclose(f);
						if ( compute_nee_flags ) {
							if ( datasets[dataset].years_count >= 3 ) {
								free(nee_flags_c);
							}
							free(nee_flags_y);
						}
						free(unc_rows_temp);
						free(unc_rows_aggr);
						free(unc_rows);
						free(nee_matrix_y);
						free(percentiles_y);
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_matrix_c);
						}
						free(uts);
						free(rows_copy);						
						on_error = 1;
						break;
					}

					/* set year */
					datasets[dataset].rows[index+element-1].value[YEAR_VALUE] = datasets[dataset].years[year].year;
				}

				if ( on_error ) {
					break;
				}

				/* close file */
				fclose(f);

				/* check rows count */
				if ( element != rows_count ) {
					printf("rows count should be %d not %d\n", rows_count, element);
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_matrix_c);
					}
					free(percentiles_y);
					free(uts);
					free(rows_copy);
					on_error = 1;
					break;
				}

				/* ok */
				puts("ok");
			}

			/* update index */
			index += rows_count;
		}

		/* */
		if ( on_error ) {
			continue;
		}

		/*
		{
			FILE *f = fopen("dataset_dump.csv", "w");
			if ( f ) {
				fprintf(f, "TA,SWIN,VPD\n");
				for ( i = 0; i < datasets[dataset].rows_count; i++ ) {
					fprintf(f, "%g,%g,%g\n",	datasets[dataset].rows[i].value[TA_VALUE],
												datasets[dataset].rows[i].value[SWIN_VALUE],
												datasets[dataset].rows[i].value[VPD_VALUE]);
				}
				fclose(f);
			}
		}
		*/
		
		/* get meteos */
		if ( use_met_gf ) {
			printf("### checking meteos...");
			if ( !get_meteo(&datasets[dataset]) ) {
				continue;
			}
		}

		/* update rows copy */
		for ( i = 0; i < datasets[dataset].rows_count; i++ ) {
			for ( y = 0; y < DATASET_VALUES; y++ ) {
				rows_copy[i].row.value[y] = datasets[dataset].rows[i].value[y];
			}
		}

		/*
		{
			FILE *f = fopen("dataset_dump_w_meteo.csv", "w");
			if ( f ) {
				fprintf(f, "TA,SWIN,VPD\n");
				for ( i = 0; i < datasets[dataset].rows_count; i++ ) {
					fprintf(f, "%g,%g,%g\n",	datasets[dataset].rows[i].value[TA_VALUE],
												datasets[dataset].rows[i].value[SWIN_VALUE],
												datasets[dataset].rows[i].value[VPD_VALUE]);
				}
				fclose(f);
			}
		}
		*/
		
		/*
		* 
		* do _y stuff
		*
		*/

		/* loop for each percentile */
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
			/* reset */
			index = 0;
			/* loop for each year */
			for ( year = 0; year < datasets[dataset].years_count; year++ ) {
				/* get rows count */
				rows_count = IS_LEAP_YEAR(datasets[dataset].years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

				if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
					rows_count /= 2;
				}

				/* get uts */
				percentiles_y[year].value[percentile] = INVALID_VALUE;
				if ( get_uts_y(&datasets[dataset], datasets[dataset].years[year].year, uts, &uts_count) ) {
					/* get percentile */
					percentiles_y[year].value[percentile] = get_percentile(uts, uts_count, percentiles_test_2[percentile], &error);
					if ( error ) {
						printf("unable to get percentile for %d in y method.\n", datasets[dataset].years[year].year);
						if ( compute_nee_flags ) {
							if ( datasets[dataset].years_count >= 3 ) {
								free(nee_flags_c);
							}
							free(nee_flags_y);
						}
						free(unc_rows_temp);
						free(unc_rows_aggr);
						free(unc_rows);
						free(nee_matrix_y);
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_matrix_c);
						}
						free(percentiles_y);
						free(uts);
						free(rows_copy);
						on_error = 1;
						break;
					}
					printf("%d -> filtering for %g (%g%%)...", datasets[dataset].years[year].year, percentiles_y[year].value[percentile], percentiles_test_2[percentile]);

					/* apply percentile */
					element = 0;
					for ( row = 0; row < rows_count; row++ ) {
						if ( compute_nee_flags ) {
							nee_flags_y[index+row].value[percentile] = 0;
						}
						if ( datasets[dataset].rows[index+row].value[USTAR_VALUE] < percentiles_y[year].value[percentile] ) {
							if ( !IS_INVALID_VALUE(datasets[dataset].rows[index+row].value[NEE_VALUE]) ) {
								datasets[dataset].rows[index+row].value[NEE_VALUE] = INVALID_VALUE;
								++element;
							}
							/* flag for the USTAR filtering (also in the else if below): flag=0  for data not filtered,
							flag=1 for the first value of a period removed due to low USTAR, flag=2 for hh removed due to
							low USTAR but with also the previous hh removed, flag=3 for hh of high ustar removed because at
							the end of the low USTAR period*/
							if ( compute_nee_flags ) {
								nee_flags_y[index+row].value[percentile] = 1;	
								if ( row && ((nee_flags_y[index+row-1].value[percentile] >= 1) && (nee_flags_y[index+row-1].value[percentile] < 3)) ) {
									++nee_flags_y[index+row].value[percentile];
								}
							}
							/* filter out also the first value after a low turbulence period (even if just one hh) */
							if ( row < rows_count-1 ) {
								if ( !IS_INVALID_VALUE(datasets[dataset].rows[index+row+1].value[NEE_VALUE]) ) {
									datasets[dataset].rows[index+row+1].value[NEE_VALUE] = INVALID_VALUE;
									++element;
								}
							}
						} else if ( compute_nee_flags && row && ((1 == nee_flags_y[index+row-1].value[percentile]) || (2 == nee_flags_y[index+row-1].value[percentile])) ) {
							nee_flags_y[index+row].value[percentile] = 3;
						}
					}
					printf("%g NEE values removed.\n", (PREC)element/rows_count);
				} else {
					printf("%d -> filtering is not possible\n", datasets[dataset].years[year].year);
				}

				/* update */
				index += rows_count;
			}

			if ( on_error ) {
				break;
			}

			/* gapfilling */
			printf("     -> gf...");
			datasets[dataset].gf_rows = gf_mds(	datasets[dataset].rows->value,
												sizeof(ROW),
												datasets[dataset].rows_count,
												REQUIRED_DATASET_VALUES,
												(HOURLY_TIMERES == datasets[dataset].details->timeres) ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
												GF_DRIVER_1_TOLERANCE_MIN,
												GF_DRIVER_1_TOLERANCE_MAX,
												GF_DRIVER_2A_TOLERANCE_MIN,
												GF_DRIVER_2A_TOLERANCE_MAX,
												GF_DRIVER_2B_TOLERANCE_MIN,
												GF_DRIVER_2B_TOLERANCE_MAX,
												NEE_VALUE,
												SWIN_VALUE,
												TA_VALUE,
												VPD_VALUE,
												SWIN_QC_VALUE,
												TA_QC_VALUE,
												VPD_QC_VALUE,
												qc_gf_threshold,
												qc_gf_threshold,
												qc_gf_threshold,
												GF_ROWS_MIN,
												1,
												-1,
												-1,
												&no_gaps_filled_count,
												0,
												0,
												0,
												NULL,
												0);
			if ( !datasets[dataset].gf_rows ) {
				if ( compute_nee_flags ) {
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_flags_c);
					}
					free(nee_flags_y);
				}
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(nee_matrix_y);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
				}
				free(percentiles_y);
				free(uts);
				free(rows_copy);
				on_error = 1;
				break;
			}

			if ( no_gaps_filled_count ) {
				printf("unable to gf! for %d row%s\n", no_gaps_filled_count, (no_gaps_filled_count>1) ? "s":"");
				if ( compute_nee_flags ) {
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_flags_c);
					}
					free(nee_flags_y);
				}
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(nee_matrix_y);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
				}
				free(percentiles_y);
				free(uts);
				free(rows_copy);
				on_error = 1;
				break;
			}
			puts("ok");

			for ( row = 0; row < datasets[dataset].rows_count; ++row ) {
				nee_matrix_y[row].nee[percentile] = (IS_FLAG_SET(datasets[dataset].gf_rows[row].mask, GF_TOFILL_VALID) ? datasets[dataset].rows[row].value[NEE_VALUE] : datasets[dataset].gf_rows[row].filled);
				nee_matrix_y[row].hat[percentile] = datasets[dataset].gf_rows[row].filled;
				nee_matrix_y[row].qc[percentile] = (IS_FLAG_SET(datasets[dataset].gf_rows[row].mask, GF_TOFILL_VALID) ? 0 : datasets[dataset].gf_rows[row].quality);
				/* backup for further use */
				nee_matrix_y[row].qc_ori[percentile] = nee_matrix_y[row].qc[percentile];
			}

			/* reset */
			for ( i = 0; i < datasets[dataset].rows_count; i++ ) {
				for ( y = 0; y < DATASET_VALUES; y++ ) {
					datasets[dataset].rows[i].value[y] = rows_copy[i].row.value[y];
				}
			}
			free(datasets[dataset].gf_rows);
			datasets[dataset].gf_rows = NULL;
		}

		if ( on_error ) {
			continue;
		}

		/* save _y percentiles */
		printf("saving y u* percentiles...");
		sprintf(buffer, "%s%s_USTAR_percentiles_y.csv", output_files_path, datasets[dataset].details->site);
		f = fopen(buffer, "w");
		if ( !f ) {
			puts("unable to create file!\n");
			if ( compute_nee_flags ) {
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_flags_c);
				}
				free(nee_flags_y);
			}
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			free(percentiles_y);
			free(uts);
			free(rows_copy);
			continue;
		}
		fprintf(f, "%s,", TIMESTAMP_STRING);
		for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
			fprintf(f, "%g", percentiles_test_2[percentile]);
			if ( percentile < PERCENTILES_COUNT_2-1 ) {
				fputs(",", f);
			}
		}
		fputs("\n", f);
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			fprintf(f, "%d,", datasets[dataset].years[year].year);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, "%g", percentiles_y[year].value[percentile]);
				if ( percentile < PERCENTILES_COUNT_2-1 ) {
					fputs(",", f);
				}
			}
			fputs("\n", f);
		}
		fclose(f);
		puts("ok");

		/*
		*
		*	do _c stuff
		*
		*/

		if ( datasets[dataset].years_count >= 3 ) {
			/* get uts_c */
			if ( datasets[dataset].years_count >= 3 ) {
				if ( !get_uts_c(datasets[dataset].details->site, datasets[dataset].years, datasets[dataset].years_count, uts, &uts_count) ) {
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					free(percentiles_y);
					free(nee_matrix_c);
					free(uts);
					free(rows_copy);
					continue;
				}
			}

			/* get percentiles */
			for ( i = 0; i < PERCENTILES_COUNT_2; i++ ) {
				percentiles_c[i] = get_percentile(uts, uts_count, percentiles_test_2[i], &error);
				if ( error ) {
					puts("unable to get percentile");
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					free(nee_matrix_c);
					free(percentiles_y);
					free(uts);
					free(rows_copy);
					on_error = 1;
					break;
				}
			}

			if ( on_error ) {
				continue;
			}

			/* get percentiles */
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {	
				/* show info */		
				printf("filtering for %g (%g%%)...", percentiles_c[percentile], percentiles_test_2[percentile]);
				/* apply threshold */
				element = 0;
				/* */
				for ( row = 0; row < datasets[dataset].rows_count; row++ ) {
					if ( compute_nee_flags ) {
						nee_flags_c[row].value[percentile] = 0;
					}

					if ( datasets[dataset].rows[row].value[USTAR_VALUE] < percentiles_c[percentile] ) {
						if ( !IS_INVALID_VALUE(datasets[dataset].rows[row].value[NEE_VALUE]) ) {
							datasets[dataset].rows[row].value[NEE_VALUE] = INVALID_VALUE;
							++element;
						}
						/* flag for the USTAR filtering (also in the else if below): flag=0  for data not filtered,
							flag=1 for the first value of a period removed due to low USTAR, flag=2 for hh removed due to
							low USTAR but with also the previous hh removed, flag=3 for hh of high ustar removed because at
							the end of the low USTAR period
						*/
						if ( compute_nee_flags ) {
							nee_flags_c[row].value[percentile] = 1;	
							if ( row && ((nee_flags_c[row-1].value[percentile] >= 1) && (nee_flags_c[row-1].value[percentile] < 3)) ) {
								++nee_flags_c[row].value[percentile];
							}
						}
						/* filter out also the first value after a low turbulence period (even if just one hh) */
						if ( row < datasets[dataset].rows_count-1 ) {
							if ( !IS_INVALID_VALUE(datasets[dataset].rows[row+1].value[NEE_VALUE]) ) {
								datasets[dataset].rows[row+1].value[NEE_VALUE] = INVALID_VALUE;
								++element;
							}
						}
					}  else if ( compute_nee_flags && row && ((1 == nee_flags_c[row-1].value[percentile]) || (2 == nee_flags_c[row-1].value[percentile])) ) {
						nee_flags_c[row].value[percentile] = 3;
					}
				}
				printf("%g NEE values removed.", (PREC)element / datasets[dataset].rows_count);

				/* gapfilling */
				printf(" gf...");
				free(datasets[dataset].gf_rows);
				datasets[dataset].gf_rows = gf_mds(	datasets[dataset].rows->value,
													sizeof(ROW),
													datasets[dataset].rows_count,
													REQUIRED_DATASET_VALUES,
													(HOURLY_TIMERES == datasets[dataset].details->timeres) ? HOURLY_TIMERES : HALFHOURLY_TIMERES,
													GF_DRIVER_1_TOLERANCE_MIN,
													GF_DRIVER_1_TOLERANCE_MAX,
													GF_DRIVER_2A_TOLERANCE_MIN,
													GF_DRIVER_2A_TOLERANCE_MAX,
													GF_DRIVER_2B_TOLERANCE_MIN,
													GF_DRIVER_2B_TOLERANCE_MAX,
													NEE_VALUE,
													SWIN_VALUE,
													TA_VALUE,
													VPD_VALUE,
													SWIN_QC_VALUE,
													TA_QC_VALUE,
													VPD_QC_VALUE,
													qc_gf_threshold,
													qc_gf_threshold,
													qc_gf_threshold,
													GF_ROWS_MIN,
													1,
													-1,
													-1,
													&no_gaps_filled_count,
													0,
													0,
													0,
													NULL,
													0);
				if ( !datasets[dataset].gf_rows ) {
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_matrix_c);
					}
					free(percentiles_y);
					free(uts);
					free(rows_copy);
					on_error = 1;
					break;
				}

				if ( no_gaps_filled_count ) {
					printf("unable to gf for %d row%s\n", no_gaps_filled_count, (no_gaps_filled_count>1) ? "s":"");
					if ( compute_nee_flags ) {
						if ( datasets[dataset].years_count >= 3 ) {
							free(nee_flags_c);
						}
						free(nee_flags_y);
					}
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					if ( datasets[dataset].years_count >= 3 ) {
						free(nee_matrix_c);
					}
					free(percentiles_y);
					free(uts);
					free(rows_copy);
					on_error = 1;
					break;
				}
				puts("ok");

				for ( row = 0; row < datasets[dataset].rows_count; ++row ) {
					nee_matrix_c[row].nee[percentile] = (IS_FLAG_SET(datasets[dataset].gf_rows[row].mask, GF_TOFILL_VALID) ? datasets[dataset].rows[row].value[NEE_VALUE] : datasets[dataset].gf_rows[row].filled);
					nee_matrix_c[row].hat[percentile] = datasets[dataset].gf_rows[row].filled;
					nee_matrix_c[row].qc[percentile] = (IS_FLAG_SET(datasets[dataset].gf_rows[row].mask, GF_TOFILL_VALID) ? 0 : datasets[dataset].gf_rows[row].quality);
					/* backup for further use */
					nee_matrix_c[row].qc_ori[percentile] = nee_matrix_c[row].qc[percentile];
				}

				/* reset */
				for ( i = 0; i < datasets[dataset].rows_count; i++ ) {
					for ( y = 0; y < DATASET_VALUES; y++ ) {
						datasets[dataset].rows[i].value[y] = rows_copy[i].row.value[y];
					}
				}
				free(datasets[dataset].gf_rows);
				datasets[dataset].gf_rows = NULL;
			}
		} else {
			nee_matrix_c = NULL;
		}

		/* free memory */
		free(rows_copy);
		free(uts);
		rows_copy = NULL;
		uts = NULL;

		if ( on_error ) {
			continue;
		}

		/* save _c percentiles */
		if ( datasets[dataset].years_count >= 3 ) {
			printf("saving c u* percentiles...");
			if ( datasets[dataset].years_count > 1 ) {
				sprintf(buffer, "%s%s_%d_%d_USTAR_percentiles_c.csv",	output_files_path,
																		datasets[dataset].details->site, 
																		datasets[dataset].years[0].year, 
																		datasets[dataset].years[datasets[dataset].years_count-1].year
				);
			} else {
				sprintf(buffer, "%s%s_%d_USTAR_percentiles_c.csv",	output_files_path,
																		datasets[dataset].details->site, 
																		datasets[dataset].years[0].year
				);
			}
			f = fopen(buffer, "w");
			if ( !f ) {
				puts("unable to create file!\n\n");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(nee_matrix_y);
				free(percentiles_y);
				free(nee_matrix_c);
				continue;
			}
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, "%g", percentiles_test_2[percentile]);
				if ( percentile < PERCENTILES_COUNT_2-1 ) {
					fputs(",", f);
				}
			}
			fputs("\n", f);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, "%g", percentiles_c[percentile]);
				if ( percentile < PERCENTILES_COUNT_2-1 ) {
					fputs(",", f);
				}
			}
			fclose(f);
			puts("ok");
		}

		/* saving y nee matrix */
		if ( ! save_nee_matrix(nee_matrix_y, &datasets[dataset], HH_Y) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(nee_matrix_y);
			free(percentiles_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			continue;
		}

		/* saving c nee matrix */
		if ( datasets[dataset].years_count >= 3 ) {
			if ( ! save_nee_matrix(nee_matrix_c, &datasets[dataset], HH_C) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(nee_matrix_y);
				free(nee_matrix_c);
				free(percentiles_y);
				continue;
			}
		}

		/* process nee_matrix y */
		p_matrix_y = process_nee_matrix(&datasets[dataset], nee_matrix_y, datasets[dataset].rows_count, &ref_y, HH_Y);
		ref_y_old = ref_y;
		if ( ! p_matrix_y ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			continue;
		}

		/* process nee_matrix c */
		ref_c = -1;
		ref_c_old = -1;
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_nee_matrix(&datasets[dataset], nee_matrix_c, datasets[dataset].rows_count, &ref_c, HH_C);
			ref_c_old = ref_c;
			if ( !p_matrix_c ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(p_matrix_y);
				free(nee_matrix_y);
				free(nee_matrix_c);
				continue;
			}
		}

		if ( compute_nee_flags ) {
			FILE *f;

			printf("saving nee flags...");
			sprintf(buffer, "%snee_flags.txt", output_files_path);
			f = fopen(buffer, "w");
			if ( !f ) {
				puts("unable to create file for nee flags!\n");
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_flags_c);
				}
				free(nee_flags_y);
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(nee_matrix_y);
				free(percentiles_y);
				free(nee_matrix_c);
				continue;
			}

			/* write header */
			if ( datasets[dataset].years_count >= 3 ) {
				fprintf(f, "%s,NEE_FLAG_Y_REF,NEE_FLAG_Y_UST50,NEE_FLAG_C_REF,NEE_FLAG_C_UST50\n", TIMESTAMP_HEADER);
			} else {
				fprintf(f, "%s,NEE_FLAG_Y_REF,NEE_FLAG_Y_UST50\n", TIMESTAMP_HEADER);
			}

			j = 0;
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

				if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
					y /= 2;
				}

				for ( row = 0; row < y; row++ ) {
					t = timestamp_start_by_row(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
					fprintf(f, "%04d%02d%02d%02d%02d,", t->YYYY, t->MM, t->DD, t->hh, t->mm);
					t = timestamp_end_by_row(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
					fprintf(f, "%04d%02d%02d%02d%02d,", t->YYYY, t->MM, t->DD, t->hh, t->mm);
					fprintf(f, "%d,%d", nee_flags_y[j+row].value[ref_y], nee_flags_y[j+row].value[PERCENTILES_COUNT_2-1]);
					if ( datasets[dataset].years_count >= 3 ) {
						fprintf(f, ",%d,%d", nee_flags_c[j+row].value[ref_c], nee_flags_c[j+row].value[PERCENTILES_COUNT_2-1]);
					}
					fputs("\n", f);
				}

				if ( on_error ) {
					break;
				}

				j += y;
			}

			if ( on_error ) {
				continue;
			}
			fclose(f);

			/* free memory */
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_flags_c);
			}
			free(nee_flags_y);

			/* */
			puts("ok");
		}

		/* random uncertainty */
		if ( ! no_rand_unc ) {
			printf("computing random uncertainty...");
			if ( ! compute_rand_unc(&datasets[dataset], unc_rows, nee_matrix_y, nee_matrix_c, ref_y, ref_c) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(p_matrix_y);
				free(nee_matrix_y);
				free(p_matrix_c);
				free(nee_matrix_c);
				continue;
			}
			puts("ok");
		}

		/* save output hh */
		printf("saving hh...");
		sprintf(buffer, output_file_hh, output_files_path, datasets[dataset].details->site);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n\n", buffer);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			continue;
		}

		/* write header hh */
		fprintf(f, header_file_hh, TIMESTAMP_HEADER);
		if ( no_rand_unc ) {
			fputs(output_var_1, f);
		} else {
			fputs(output_var_1_rand_unc_hh, f);
		}
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "NEE_%02g_y,NEE_%02g_qc_y", percentiles_test_1[percentile],percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(output_var_2, f);
			} else {
				fputs(output_var_2_rand_unc_hh, f);
			}
			for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
				fprintf(f, "NEE_%02g_c,NEE_%02g_qc_c", percentiles_test_1[percentile],percentiles_test_1[percentile]);
				if ( percentile < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}
		}
		fputs("\n", f);

		/* write values hh */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
				y /= 2;
			}

			year = datasets[dataset].years[i].year;
			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < y; row++ ) {
				/* timestamp start */
				t = timestamp_start_by_row(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
				fprintf(f, "%04d%02d%02d%02d%02d,", t->YYYY, t->MM, t->DD, t->hh, t->mm);
				/* timestamp end */
				t = timestamp_end_by_row(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
				fprintf(f, "%04d%02d%02d%02d%02d,", t->YYYY, t->MM, t->DD, t->hh, t->mm);
				/* dtime */
				fprintf(f, "%g,", get_dtime_by_row(row, (HOURLY_TIMERES == datasets[dataset].details->timeres)));
				/* rpot */
				fprintf(f, "%d,", ARE_FLOATS_EQUAL(datasets[dataset].rows[j+row].value[RPOT_VALUE], 0.0) ? 1 : 0);
				/* */
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
																nee_matrix_y[j+row].nee[ref_y],
																nee_matrix_y[j+row].qc[ref_y],
																nee_matrix_y[j+row].nee[PERCENTILES_COUNT_2-1],
																nee_matrix_y[j+row].qc[PERCENTILES_COUNT_2-1],
																p_matrix_y[j+row].mean,
																p_matrix_y[j+row].mean_qc,
																p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",		(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_joinUnc_y = compute_join(unc_rows[j+row].rand[NEE_REF_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						nee_ust50_joinUnc_y = compute_join(unc_rows[j+row].rand[NEE_UST50_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						fprintf(f, "%g,%g,%g,%d,%d,%g,%g,%g,%g,%d,%d,%g,%g,%g,%g,",
																nee_matrix_y[j+row].nee[ref_y],
																nee_matrix_y[j+row].qc[ref_y],
																unc_rows[j+row].rand[NEE_REF_Y_UNC],
																unc_rows[j+row].method[NEE_REF_Y_UNC],
																unc_rows[j+row].samples_count[NEE_REF_Y_UNC],
																nee_ref_joinUnc_y,
																nee_matrix_y[j+row].nee[PERCENTILES_COUNT_2-1],
																nee_matrix_y[j+row].qc[PERCENTILES_COUNT_2-1],
																unc_rows[j+row].rand[NEE_UST50_Y_UNC],
																unc_rows[j+row].method[NEE_UST50_Y_UNC],
																unc_rows[j+row].samples_count[NEE_UST50_Y_UNC],
																nee_ust50_joinUnc_y,
																p_matrix_y[j+row].mean,
																p_matrix_y[j+row].mean_qc,
																p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%d,%d,%g,%g,%g,%g,%d,%d,%g,%g,%g,%g,",
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																INVALID_VALUE,
																INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																INVALID_VALUE,
																INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
						);
					}
				}
				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g,%g", p_matrix_y[j+row].value[z], p_matrix_y[j+row].qc[z]);
					} else {
						fprintf(f, "%g,%g", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
					}
					if ( z < PERCENTILES_COUNT_1-1 ) {
						fputs(",", f);
					}
				}
				if ( datasets[dataset].years_count >= 3 ) {
					if ( no_rand_unc ) {
						if ( exists ) {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,",
																nee_matrix_c[j+row].nee[ref_c],
																nee_matrix_c[j+row].qc[ref_c],
																nee_matrix_c[j+row].nee[PERCENTILES_COUNT_2-1],
																nee_matrix_c[j+row].qc[PERCENTILES_COUNT_2-1],
																p_matrix_c[j+row].mean,
																p_matrix_c[j+row].mean_qc,
																p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,",
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
							);
						}
					} else  {
						if ( exists ) {
							nee_ref_joinUnc_c = compute_join(unc_rows[j+row].rand[NEE_REF_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							nee_ust50_joinUnc_c = compute_join(unc_rows[j+row].rand[NEE_UST50_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							fprintf(f, ",%g,%g,%g,%d,%d,%g,%g,%g,%g,%d,%d,%g,%g,%g,%g,",
																nee_matrix_c[j+row].nee[ref_c],
																nee_matrix_c[j+row].qc[ref_c],
																unc_rows[j+row].rand[NEE_REF_C_UNC],
																unc_rows[j+row].method[NEE_REF_C_UNC],
																unc_rows[j+row].samples_count[NEE_REF_C_UNC],
																nee_ref_joinUnc_c,
																nee_matrix_c[j+row].nee[PERCENTILES_COUNT_2-1],
																nee_matrix_c[j+row].qc[PERCENTILES_COUNT_2-1],
																unc_rows[j+row].rand[NEE_UST50_C_UNC],
																unc_rows[j+row].method[NEE_UST50_C_UNC],
																unc_rows[j+row].samples_count[NEE_UST50_C_UNC],
																nee_ust50_joinUnc_c,
																p_matrix_c[j+row].mean,
																p_matrix_c[j+row].mean_qc,
																p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, ",%g,%g,%g,%d,%d,%g,%g,%g,%g,%d,%d,%g,%g,%g,%g,",
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																INVALID_VALUE,
																INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																INVALID_VALUE,
																INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
							);
						}
					}
					for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
						if ( exists ) {
							fprintf(f, "%g,%g", p_matrix_c[j+row].value[z], p_matrix_c[j+row].qc[z]);
						} else {
							fprintf(f, "%g,%g", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
						}
						if ( z < PERCENTILES_COUNT_1-1 ) {
							fputs(",", f);
						}
					}
				}
				fputs("\n", f);
			}

			if ( on_error ) {
				break;
			}
			j += y;
		}

		if ( on_error ) {
			continue;
		}

		/* close file */
		fclose(f);

		/* save info */
		if ( ! save_info(&datasets[dataset], output_files_path, HH_TR, ref_y, ref_c, percentiles_y, percentiles_c) ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c);
			}
			continue;
		}
		
		puts("ok");

		/*
		*
		*	daily
		*
		*/

		printf("computing dd...");

		/* compute daily rows */
		daily_rows_count = datasets[dataset].rows_count / rows_per_day;

		/* alloc memory for daily */
		nee_matrix_y_daily = malloc(daily_rows_count*sizeof*nee_matrix_y_daily);
		if ( !nee_matrix_y_daily ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c);
			}
			continue;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			nee_matrix_c_daily = malloc(daily_rows_count*sizeof*nee_matrix_c_daily);
			if ( !nee_matrix_c_daily ) {
				puts(err_out_of_memory);
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y_daily);
				free(p_matrix_c);
				free(p_matrix_y);
				free(nee_matrix_y);
				free(nee_matrix_c);
				continue;
			}
		}
		/* change qc for y and c */
		change_qcs(nee_matrix_y, datasets[dataset].rows_count);
		if ( datasets[dataset].years_count >= 3 ) {
			change_qcs(nee_matrix_c, datasets[dataset].rows_count);
		}

		/* compute dd */
		index = 0;
		for ( row = 0; row < datasets[dataset].rows_count; row += rows_per_day ) {
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				nee_matrix_y_daily[index].nee[percentile] = 0.0;
				nee_matrix_y_daily[index].qc[percentile] = 0.0;
				if ( datasets[dataset].years_count >= 3 ) {
					nee_matrix_c_daily[index].nee[percentile] = 0.0;
					nee_matrix_c_daily[index].qc[percentile] = 0.0;
				}
				for ( i = 0; i < rows_per_day; i++ ) {
					nee_matrix_y_daily[index].nee[percentile] += nee_matrix_y[row+i].nee[percentile];
					nee_matrix_y_daily[index].qc[percentile] += nee_matrix_y[row+i].qc[percentile];
					if ( datasets[dataset].years_count >= 3 ) {
						nee_matrix_c_daily[index].nee[percentile] += nee_matrix_c[row+i].nee[percentile];
						nee_matrix_c_daily[index].qc[percentile] += nee_matrix_c[row+i].qc[percentile];
					}
				}
				nee_matrix_y_daily[index].nee[percentile] /= rows_per_day;
				nee_matrix_y_daily[index].nee[percentile] *= CO2TOC;
				nee_matrix_y_daily[index].qc[percentile] /= rows_per_day;
				if ( datasets[dataset].years_count >= 3 ) {
					nee_matrix_c_daily[index].nee[percentile] /= rows_per_day;
					nee_matrix_c_daily[index].nee[percentile] *= CO2TOC;
					nee_matrix_c_daily[index].qc[percentile] /= rows_per_day;
				}
			}
			++index;
		}
		if ( index != daily_rows_count ) {
			printf("daily rows should be %d not %d", daily_rows_count, index);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c);
				free(nee_matrix_c_daily);
			}
			continue;
		}

		/* free memory */
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
		}
		free(p_matrix_y);
		
		/* update */
		rows_count = daily_rows_count;

		/* saving y nee dd matrix */
		if ( percentiles_save ) {
			if ( ! save_nee_matrix(nee_matrix_y_daily, &datasets[dataset], DD_Y) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				free(percentiles_y);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
				}
				continue;
			}

			/* saving c nee dd matrix */
			if ( datasets[dataset].years_count >= 3 ) {
				if ( ! save_nee_matrix(nee_matrix_c_daily, &datasets[dataset], DD_C) ) {
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(nee_matrix_y);
					free(nee_matrix_y_daily);
					free(nee_matrix_c);
					free(nee_matrix_c_daily);
					free(percentiles_y);
					continue;
				}
			}
		}

		/* get p_matrix */
		p_matrix_y = process_nee_matrix(&datasets[dataset], nee_matrix_y_daily, rows_count, &ref_y, DD_Y);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for daily y");
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(nee_matrix_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
				free(nee_matrix_c_daily);
			}
			continue;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_nee_matrix(&datasets[dataset], nee_matrix_c_daily, rows_count, &ref_c, DD_C);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for daily c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				free(nee_matrix_c);
				free(nee_matrix_c_daily);
				continue;
			}
		}		

		/* ref changed ? */
		if ( (ref_y_old != ref_y) || (ref_c_old != ref_c) ) {
			/* revert back qcs */
			revert_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				revert_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}

			/* compute random again */
			if ( ! compute_rand_unc(&datasets[dataset], unc_rows, nee_matrix_y, nee_matrix_c, ref_y, ref_c) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
					free(nee_matrix_c_daily);
				}
				continue;
			}

			/* change qcs */
			change_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				change_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}
			ref_y_old = ref_y;
			ref_c_old = ref_c;
		}

		/* get night! */
		rows_night_daily = compute_nights(&datasets[dataset], nee_matrix_y, nee_matrix_c, ref_y, ref_c, unc_rows);
		if ( ! rows_night_daily ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(nee_matrix_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
				free(nee_matrix_c_daily);
			}
			continue;
		}

		/* rand unc dd */
		if ( ! no_rand_unc ) {
			rand_unc_dd(unc_rows, unc_rows_aggr, datasets[dataset].rows_count, datasets[dataset].years_count, (HOURLY_TIMERES == datasets[dataset].details->timeres));
		}

		/* save output dd */
		printf("ok\nsaving dd...");
		sprintf(buffer, output_file_dd, output_files_path, datasets[dataset].details->site);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n\n", buffer);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(nee_matrix_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
				free(nee_matrix_c_daily);
			}
			continue;
		}

		/* write header dd */
		fprintf(f, header_file_dd, TIMESTAMP_STRING);
		if ( no_rand_unc ) {
			fputs(output_var_1, f);
		} else {
			fputs(output_var_1_rand_unc, f);
		}
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "NEE_%02g_y,NEE_%02g_qc_y", percentiles_test_1[percentile],percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(output_var_2, f);
			} else {
				fputs(output_var_2_rand_unc, f);
			}
			for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
				fprintf(f, "NEE_%02g_c,NEE_%02g_qc_c", percentiles_test_1[percentile],percentiles_test_1[percentile]);
				if ( percentile < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}
		}
		if ( no_rand_unc ) {
			fputs(header_file_night_no_rand_unc, f);
			fputs(header_file_night_y_no_rand_unc, f);
		} else {
			fputs(header_file_night, f);
			fputs(header_file_night_y, f);
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(header_file_night_c_no_rand_unc, f);
			} else {
				fputs(header_file_night_c, f);
			}
		} else {
			fputs("\n", f);
		}

		/* write values dd */
		j = 0;
		element = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
				y /= 2;
			}

			/* */
			y /= rows_per_day;

			/* */
			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < y; row++ ) {
				t = timestamp_end_by_row(row*((HOURLY_TIMERES == datasets[dataset].details->timeres) ? 24 : 48), datasets[dataset].years[i].year, datasets[dataset].details->timeres);
				fprintf(f, "%04d%02d%02d,%d,",		t->YYYY,
													t->MM,
													t->DD,
													row+1			
				);

				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_y_daily[j+row].nee[ref_y],
															nee_matrix_y_daily[j+row].qc[ref_y],
															nee_matrix_y_daily[j+row].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_y_daily[j+row].qc[PERCENTILES_COUNT_2-1],
															p_matrix_y[j+row].mean,
															p_matrix_y[j+row].mean_qc,
															p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_joinUnc_y = compute_join(unc_rows_aggr[j+row].rand[NEE_REF_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						nee_ust50_joinUnc_y = compute_join(unc_rows_aggr[j+row].rand[NEE_UST50_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
																		nee_matrix_y_daily[j+row].nee[ref_y],
																		nee_matrix_y_daily[j+row].qc[ref_y],
																		unc_rows_aggr[j+row].rand[NEE_REF_Y_UNC],
																		nee_ref_joinUnc_y,
																		nee_matrix_y_daily[j+row].nee[PERCENTILES_COUNT_2-1],
																		nee_matrix_y_daily[j+row].qc[PERCENTILES_COUNT_2-1],
																		unc_rows_aggr[j+row].rand[NEE_UST50_Y_UNC],
																		nee_ust50_joinUnc_y,
																		p_matrix_y[j+row].mean,
																		p_matrix_y[j+row].mean_qc,
																		p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE,
																		(PREC)INVALID_VALUE
						);
					}
				}
				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g,%g,", p_matrix_y[j+row].value[z], p_matrix_y[j+row].qc[z]);
					} else {
						fprintf(f, "%g,%g,", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
					}
				}

				if ( datasets[dataset].years_count >= 3 ) {
					if ( no_rand_unc ) {
						if ( exists ) {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
																nee_matrix_c_daily[j+row].nee[ref_c],
																nee_matrix_c_daily[j+row].qc[ref_c],
																nee_matrix_c_daily[j+row].nee[PERCENTILES_COUNT_2-1],
																nee_matrix_c_daily[j+row].qc[PERCENTILES_COUNT_2-1],
																p_matrix_c[j+row].mean,
																p_matrix_c[j+row].mean_qc,
																p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
							);
						}
					} else {
						if ( exists ) {
							nee_ref_joinUnc_c = compute_join(unc_rows_aggr[j+row].rand[NEE_REF_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							nee_ust50_joinUnc_c = compute_join(unc_rows_aggr[j+row].rand[NEE_UST50_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
																			nee_matrix_c_daily[j+row].nee[ref_c],
																			nee_matrix_c_daily[j+row].qc[ref_c],
																			unc_rows_aggr[j+row].rand[NEE_REF_C_UNC],
																			nee_ref_joinUnc_c,
																			nee_matrix_c_daily[j+row].nee[PERCENTILES_COUNT_2-1],
																			nee_matrix_c_daily[j+row].qc[PERCENTILES_COUNT_2-1],
																			unc_rows_aggr[j+row].rand[NEE_UST50_C_UNC],
																			nee_ust50_joinUnc_c,
																			p_matrix_c[j+row].mean,
																			p_matrix_c[j+row].mean_qc,
																			p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE,
																			(PREC)INVALID_VALUE
							);
						}
					}
					for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
						if ( exists ) {
							fprintf(f, "%g,%g,", p_matrix_c[j+row].value[z], p_matrix_c[j+row].qc[z]);
						} else {
							fprintf(f, "%g,%g,",(PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
						}
					}
				}
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,",
															rows_night_daily[j+row].night_total,
															rows_night_daily[j+row].day_total
						);
					} else {
						fprintf(f, "%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,",
															rows_night_daily[j+row].night_total,
															rows_night_daily[j+row].day_total,
															rows_night_daily[j+row].night_d,
															rows_night_daily[j+row].day_d
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				}
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
																rows_night_daily[j+row].night[NEE_REF_Y],
																rows_night_daily[j+row].night_std[NEE_REF_Y],
																rows_night_daily[j+row].night_qc[NEE_REF_Y],
																rows_night_daily[j+row].day[NEE_REF_Y],
																rows_night_daily[j+row].day_std[NEE_REF_Y],
																rows_night_daily[j+row].day_qc[NEE_REF_Y],
																rows_night_daily[j+row].night[NEE_UST50_Y],
																rows_night_daily[j+row].night_std[NEE_UST50_Y],
																rows_night_daily[j+row].night_qc[NEE_UST50_Y],
																rows_night_daily[j+row].day[NEE_UST50_Y],
																rows_night_daily[j+row].day_std[NEE_UST50_Y],
																rows_night_daily[j+row].day_qc[NEE_UST50_Y],
																rows_night_daily[j+row].night[NEE_05_Y],
																rows_night_daily[j+row].night[NEE_05_QC_Y],
																rows_night_daily[j+row].night[NEE_16_Y],
																rows_night_daily[j+row].night[NEE_16_QC_Y],
																rows_night_daily[j+row].night[NEE_25_Y],
																rows_night_daily[j+row].night[NEE_25_QC_Y],
																rows_night_daily[j+row].night[NEE_50_Y],
																rows_night_daily[j+row].night[NEE_50_QC_Y],
																rows_night_daily[j+row].night[NEE_75_Y],
																rows_night_daily[j+row].night[NEE_75_QC_Y],
																rows_night_daily[j+row].night[NEE_84_Y],
																rows_night_daily[j+row].night[NEE_84_QC_Y],
																rows_night_daily[j+row].night[NEE_95_Y],
																rows_night_daily[j+row].night[NEE_95_QC_Y],
																rows_night_daily[j+row].day[NEE_05_Y],
																rows_night_daily[j+row].day[NEE_05_QC_Y],
																rows_night_daily[j+row].day[NEE_16_Y],
																rows_night_daily[j+row].day[NEE_16_QC_Y],
																rows_night_daily[j+row].day[NEE_25_Y],
																rows_night_daily[j+row].day[NEE_25_QC_Y],
																rows_night_daily[j+row].day[NEE_50_Y],
																rows_night_daily[j+row].day[NEE_50_QC_Y],
																rows_night_daily[j+row].day[NEE_75_Y],
																rows_night_daily[j+row].day[NEE_75_QC_Y],
																rows_night_daily[j+row].day[NEE_84_Y],
																rows_night_daily[j+row].day[NEE_84_QC_Y],
																rows_night_daily[j+row].day[NEE_95_Y],
																rows_night_daily[j+row].day[NEE_95_QC_Y]
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_night_joinUnc_y = compute_join(rows_night_daily[j+row].night[NEE_REF_Y_RAND],rows_night_daily[j+row].night[NEE_16_Y],rows_night_daily[j+row].night[NEE_84_Y]);
						nee_ref_day_joinUnc_y = compute_join(rows_night_daily[j+row].day[NEE_REF_Y_RAND],rows_night_daily[j+row].day[NEE_16_Y],rows_night_daily[j+row].day[NEE_84_Y]);
						nee_ust50_night_joinUnc_y = compute_join(rows_night_daily[j+row].night[NEE_UST50_Y_RAND],rows_night_daily[j+row].night[NEE_16_Y],rows_night_daily[j+row].night[NEE_84_Y]);
						nee_ust50_day_joinUnc_y = compute_join(rows_night_daily[j+row].day[NEE_UST50_Y_RAND],rows_night_daily[j+row].day[NEE_16_Y],rows_night_daily[j+row].day[NEE_84_Y]);
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														rows_night_daily[j+row].night[NEE_REF_Y],
														rows_night_daily[j+row].night_std[NEE_REF_Y],
														rows_night_daily[j+row].night_qc[NEE_REF_Y],
														rows_night_daily[j+row].night[NEE_REF_Y_RAND],
														nee_ref_night_joinUnc_y,
														rows_night_daily[j+row].day[NEE_REF_Y],
														rows_night_daily[j+row].day_std[NEE_REF_Y],
														rows_night_daily[j+row].day_qc[NEE_REF_Y],
														rows_night_daily[j+row].day[NEE_REF_Y_RAND],
														nee_ref_day_joinUnc_y,
														rows_night_daily[j+row].night[NEE_UST50_Y],
														rows_night_daily[j+row].night_std[NEE_UST50_Y],
														rows_night_daily[j+row].night_qc[NEE_UST50_Y],
														rows_night_daily[j+row].night[NEE_UST50_Y_RAND],
														nee_ust50_night_joinUnc_y,
														rows_night_daily[j+row].day[NEE_UST50_Y],
														rows_night_daily[j+row].day_std[NEE_UST50_Y],
														rows_night_daily[j+row].day_qc[NEE_UST50_Y],
														rows_night_daily[j+row].day[NEE_UST50_Y_RAND],
														nee_ust50_day_joinUnc_y,
														rows_night_daily[j+row].night[NEE_05_Y],
														rows_night_daily[j+row].night[NEE_05_QC_Y],
														rows_night_daily[j+row].night[NEE_16_Y],
														rows_night_daily[j+row].night[NEE_16_QC_Y],
														rows_night_daily[j+row].night[NEE_25_Y],
														rows_night_daily[j+row].night[NEE_25_QC_Y],
														rows_night_daily[j+row].night[NEE_50_Y],
														rows_night_daily[j+row].night[NEE_50_QC_Y],
														rows_night_daily[j+row].night[NEE_75_Y],
														rows_night_daily[j+row].night[NEE_75_QC_Y],
														rows_night_daily[j+row].night[NEE_84_Y],
														rows_night_daily[j+row].night[NEE_84_QC_Y],
														rows_night_daily[j+row].night[NEE_95_Y],
														rows_night_daily[j+row].night[NEE_95_QC_Y],
														rows_night_daily[j+row].day[NEE_05_Y],
														rows_night_daily[j+row].day[NEE_05_QC_Y],
														rows_night_daily[j+row].day[NEE_16_Y],
														rows_night_daily[j+row].day[NEE_16_QC_Y],
														rows_night_daily[j+row].day[NEE_25_Y],
														rows_night_daily[j+row].day[NEE_25_QC_Y],
														rows_night_daily[j+row].day[NEE_50_Y],
														rows_night_daily[j+row].day[NEE_50_QC_Y],
														rows_night_daily[j+row].day[NEE_75_Y],
														rows_night_daily[j+row].day[NEE_75_QC_Y],
														rows_night_daily[j+row].day[NEE_84_Y],
														rows_night_daily[j+row].day[NEE_84_QC_Y],
														rows_night_daily[j+row].day[NEE_95_Y],
														rows_night_daily[j+row].day[NEE_95_QC_Y]
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
						);
					}
				}

				if ( datasets[dataset].years_count >= 3 ) {
					if ( no_rand_unc ) {
						if ( exists ) {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														rows_night_daily[j+row].night[NEE_REF_C],
														rows_night_daily[j+row].night_std[NEE_REF_C],
														rows_night_daily[j+row].night_qc[NEE_REF_C],
														rows_night_daily[j+row].day[NEE_REF_C],
														rows_night_daily[j+row].day_std[NEE_REF_C],
														rows_night_daily[j+row].day_qc[NEE_REF_C],
														rows_night_daily[j+row].night[NEE_UST50_C],
														rows_night_daily[j+row].night_std[NEE_UST50_C],
														rows_night_daily[j+row].night_qc[NEE_UST50_C],
														rows_night_daily[j+row].day[NEE_UST50_C],
														rows_night_daily[j+row].day_std[NEE_UST50_C],
														rows_night_daily[j+row].day_qc[NEE_UST50_C],
														rows_night_daily[j+row].night[NEE_05_C],
														rows_night_daily[j+row].night[NEE_05_QC_C],
														rows_night_daily[j+row].night[NEE_16_C],
														rows_night_daily[j+row].night[NEE_16_QC_C],
														rows_night_daily[j+row].night[NEE_25_C],
														rows_night_daily[j+row].night[NEE_25_QC_C],
														rows_night_daily[j+row].night[NEE_50_C],
														rows_night_daily[j+row].night[NEE_50_QC_C],
														rows_night_daily[j+row].night[NEE_75_C],
														rows_night_daily[j+row].night[NEE_75_QC_C],
														rows_night_daily[j+row].night[NEE_84_C],
														rows_night_daily[j+row].night[NEE_84_QC_C],
														rows_night_daily[j+row].night[NEE_95_C],
														rows_night_daily[j+row].night[NEE_95_QC_C],
														rows_night_daily[j+row].day[NEE_05_C],
														rows_night_daily[j+row].day[NEE_05_QC_C],
														rows_night_daily[j+row].day[NEE_16_C],
														rows_night_daily[j+row].day[NEE_16_QC_C],
														rows_night_daily[j+row].day[NEE_25_C],
														rows_night_daily[j+row].day[NEE_25_QC_C],
														rows_night_daily[j+row].day[NEE_50_C],
														rows_night_daily[j+row].day[NEE_50_QC_C],
														rows_night_daily[j+row].day[NEE_75_C],
														rows_night_daily[j+row].day[NEE_75_QC_C],
														rows_night_daily[j+row].day[NEE_84_C],
														rows_night_daily[j+row].day[NEE_84_QC_C],
														rows_night_daily[j+row].day[NEE_95_C],
														rows_night_daily[j+row].day[NEE_95_QC_C]
							);
						} else {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
							);
						}
					} else {
						if ( exists ) {
							nee_ref_night_joinUnc_c = compute_join(rows_night_daily[j+row].night[NEE_REF_C_RAND],rows_night_daily[j+row].night[NEE_16_C],rows_night_daily[j+row].night[NEE_84_C]);
							nee_ref_day_joinUnc_c = compute_join(rows_night_daily[j+row].day[NEE_REF_C_RAND],rows_night_daily[j+row].day[NEE_16_C],rows_night_daily[j+row].day[NEE_84_C]);
							nee_ust50_night_joinUnc_c = compute_join(rows_night_daily[j+row].night[NEE_UST50_C_RAND],rows_night_daily[j+row].night[NEE_16_C],rows_night_daily[j+row].night[NEE_84_C]);
							nee_ust50_day_joinUnc_c = compute_join(rows_night_daily[j+row].day[NEE_UST50_C_RAND],rows_night_daily[j+row].day[NEE_16_C],rows_night_daily[j+row].day[NEE_84_C]);
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														rows_night_daily[j+row].night[NEE_REF_C],
														rows_night_daily[j+row].night_std[NEE_REF_C],
														rows_night_daily[j+row].night_qc[NEE_REF_C],
														rows_night_daily[j+row].night[NEE_REF_C_RAND],
														nee_ref_night_joinUnc_c,
														rows_night_daily[j+row].day[NEE_REF_C],
														rows_night_daily[j+row].day_std[NEE_REF_C],
														rows_night_daily[j+row].day_qc[NEE_REF_C],
														rows_night_daily[j+row].day[NEE_REF_C_RAND],
														nee_ref_day_joinUnc_c,
														rows_night_daily[j+row].night[NEE_UST50_C],
														rows_night_daily[j+row].night_std[NEE_UST50_C],
														rows_night_daily[j+row].night_qc[NEE_UST50_C],
														rows_night_daily[j+row].night[NEE_UST50_C_RAND],
														nee_ust50_night_joinUnc_c,
														rows_night_daily[j+row].day[NEE_UST50_C],
														rows_night_daily[j+row].day_std[NEE_UST50_C],
														rows_night_daily[j+row].day_qc[NEE_UST50_C],
														rows_night_daily[j+row].day[NEE_UST50_C_RAND],
														nee_ust50_day_joinUnc_c,
														rows_night_daily[j+row].night[NEE_05_C],
														rows_night_daily[j+row].night[NEE_05_QC_C],
														rows_night_daily[j+row].night[NEE_16_C],
														rows_night_daily[j+row].night[NEE_16_QC_C],
														rows_night_daily[j+row].night[NEE_25_C],
														rows_night_daily[j+row].night[NEE_25_QC_C],
														rows_night_daily[j+row].night[NEE_50_C],
														rows_night_daily[j+row].night[NEE_50_QC_C],
														rows_night_daily[j+row].night[NEE_75_C],
														rows_night_daily[j+row].night[NEE_75_QC_C],
														rows_night_daily[j+row].night[NEE_84_C],
														rows_night_daily[j+row].night[NEE_84_QC_C],
														rows_night_daily[j+row].night[NEE_95_C],
														rows_night_daily[j+row].night[NEE_95_QC_C],
														rows_night_daily[j+row].day[NEE_05_C],
														rows_night_daily[j+row].day[NEE_05_QC_C],
														rows_night_daily[j+row].day[NEE_16_C],
														rows_night_daily[j+row].day[NEE_16_QC_C],
														rows_night_daily[j+row].day[NEE_25_C],
														rows_night_daily[j+row].day[NEE_25_QC_C],
														rows_night_daily[j+row].day[NEE_50_C],
														rows_night_daily[j+row].day[NEE_50_QC_C],
														rows_night_daily[j+row].day[NEE_75_C],
														rows_night_daily[j+row].day[NEE_75_QC_C],
														rows_night_daily[j+row].day[NEE_84_C],
														rows_night_daily[j+row].day[NEE_84_QC_C],
														rows_night_daily[j+row].day[NEE_95_C],
														rows_night_daily[j+row].day[NEE_95_QC_C]
							);
						} else {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
							);
						}
					}
				} else {
					fputs("\n", f);
				}
			}
			if ( on_error ) {
				break;
			}
			j += y;

			/* */
			element += ((IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (HOURLY_TIMERES == datasets[dataset].details->timeres ? 2 : 1));
		}
		if ( on_error ) {
			continue;
		}

		/* close file */
		fclose(f);

		/* free memory */
		free(p_matrix_y);
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
		}

		/* save info */
		if ( ! save_info(&datasets[dataset], output_files_path, DD_TR, ref_y, ref_c, percentiles_y, percentiles_c) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c);
			}
			continue;
		}
		puts("ok");

		/*
		* 
		* weekly
		*
		*/

		printf("computing ww...");

		weekly_rows_count = 52 * datasets[dataset].years_count;
		nee_matrix_y_weekly = malloc(weekly_rows_count*sizeof*nee_matrix_y_weekly);
		if ( !nee_matrix_y_weekly ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_daily);
			free(percentiles_y);		
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_daily);
			}
			continue;
		}

		if ( datasets[dataset].years_count >= 3 ) {		
			nee_matrix_c_weekly = malloc(weekly_rows_count*sizeof*nee_matrix_c_weekly);
			if ( !nee_matrix_c_weekly ) {
				puts(err_out_of_memory);
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_daily);
				free(nee_matrix_y_weekly);
				free(percentiles_y);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				continue;
			}
		}

		/* */
		rows_night_weekly = malloc(weekly_rows_count*sizeof*rows_night_weekly);
		if ( !rows_night_weekly ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_weekly);
			free(rows_night_daily);
			free(nee_matrix_y_weekly);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_weekly);
				free(nee_matrix_c_daily);
			}
			continue;
		}

		/* compute ww */
		j = 0;
		index = 0;
		element = 0;
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;

			if ( HOURLY_TIMERES == datasets[dataset].details->timeres  ) {
				y /= 2;
			}

			/* */
			y /= rows_per_day;

			for ( i = 0; i < 51; i++ ) {
				row = i*7;
				for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
					nee_matrix_y_weekly[index+i].nee[percentile] = 0.0;
					nee_matrix_y_weekly[index+i].qc[percentile] = 0.0;
					if ( datasets[dataset].years_count >= 3 ) {
						nee_matrix_c_weekly[index+i].nee[percentile] = 0.0;
						nee_matrix_c_weekly[index+i].qc[percentile] = 0.0;
					}
					for ( j = 0; j < 7; j++ ) {
						nee_matrix_y_weekly[index+i].nee[percentile] += nee_matrix_y_daily[element+row+j].nee[percentile];
						nee_matrix_y_weekly[index+i].qc[percentile] += nee_matrix_y_daily[element+row+j].qc[percentile];
						if ( datasets[dataset].years_count >= 3 ) {
							nee_matrix_c_weekly[index+i].nee[percentile] += nee_matrix_c_daily[element+row+j].nee[percentile];
							nee_matrix_c_weekly[index+i].qc[percentile] += nee_matrix_c_daily[element+row+j].qc[percentile];
						}
					}
					nee_matrix_y_weekly[index+i].nee[percentile] /= 7;
					nee_matrix_y_weekly[index+i].qc[percentile] /= 7;
					if ( datasets[dataset].years_count >= 3 ) {
						nee_matrix_c_weekly[index+i].nee[percentile] /= 7;
						nee_matrix_c_weekly[index+i].qc[percentile] /= 7;
					}
				}
			}
			row += j; /* 51*7 */; 
			z = y-row;
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				nee_matrix_y_weekly[index+i].nee[percentile] = 0.0;
				nee_matrix_y_weekly[index+i].qc[percentile] = 0.0;
				if ( datasets[dataset].years_count >= 3 ) {
					nee_matrix_c_weekly[index+i].nee[percentile] = 0.0;
					nee_matrix_c_weekly[index+i].qc[percentile] = 0.0;
				}
				for ( j = 0; j < z; j++ ) {
					nee_matrix_y_weekly[index+i].nee[percentile] += nee_matrix_y_daily[element+row+j].nee[percentile];
					nee_matrix_y_weekly[index+i].qc[percentile] += nee_matrix_y_daily[element+row+j].qc[percentile];
					if ( datasets[dataset].years_count >= 3 ) {
						nee_matrix_c_weekly[index+i].nee[percentile] += nee_matrix_c_daily[element+row+j].nee[percentile];
						nee_matrix_c_weekly[index+i].qc[percentile] += nee_matrix_c_daily[element+row+j].qc[percentile];
					}
				}
				nee_matrix_y_weekly[index+i].nee[percentile] /= z;
				nee_matrix_y_weekly[index+i].qc[percentile] /= z;
				if ( datasets[dataset].years_count >= 3 ) {
					nee_matrix_c_weekly[index+i].nee[percentile] /= z;
					nee_matrix_c_weekly[index+i].qc[percentile] /= z;
				}
			}

			/* */
			index += 52;
			element += y;
		}

		/* saving y nee ww matrix */
		if ( percentiles_save ) {
			if ( ! save_nee_matrix(nee_matrix_y_weekly, &datasets[dataset], WW_Y) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_y_weekly);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c_weekly);
					free(nee_matrix_c_daily);
				}
				continue;
			}

			/* saving c nee ww matrix */
			if ( datasets[dataset].years_count >= 3 ) {
				if ( ! save_nee_matrix(nee_matrix_c_weekly, &datasets[dataset], WW_C) ) {
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(rows_night_weekly);
					free(rows_night_daily);
					free(percentiles_y);
					free(nee_matrix_y_weekly);
					free(nee_matrix_y_daily);
					free(nee_matrix_c_weekly);
					free(nee_matrix_c_daily);
					continue;
				}
			}
		}

		/* get p_matrix */
		p_matrix_y = process_nee_matrix(&datasets[dataset], nee_matrix_y_weekly, weekly_rows_count, &ref_y, WW_Y);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for weekly y");
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_weekly);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_weekly);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_weekly);
				free(nee_matrix_c_daily);
			}
			continue;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_nee_matrix(&datasets[dataset], nee_matrix_c_weekly, weekly_rows_count, &ref_c, WW_C);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for weekly c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
		}

		/* save dd percentiles for night and day */
		/*if ( percentiles_save ) {
			j = 0;
			sprintf(buffer, "%s_NEE_percentiles_y_night_dd.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for dd night y");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_STRING);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
				if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
					y /= 2;
				}
				y /= rows_per_day;
				for ( row = 0; row < y; row++ ) {
					t = timestamp_end_by_row(row*((HOURLY_TIMERES == datasets[dataset].details->timeres) ? 24 : 48)
								, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
					fprintf(f, "%04d%02d%02d", t->YYYY, t->MM, t->DD);
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_daily[j+row].night_columns_y[z]
											, rows_night_daily[j+row].night_qc_columns_y[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);

			j = 0;
			sprintf(buffer, "%s_NEE_percentiles_y_day_dd.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for dd day y");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_STRING);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
				if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
					y /= 2;
				}
				y /= rows_per_day;
				for ( row = 0; row < y; row++ ) {
					t = timestamp_end_by_row(row*((HOURLY_TIMERES == datasets[dataset].details->timeres) ? 24 : 48)
								, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
					fprintf(f, "%04d%02d%02d", t->YYYY, t->MM, t->DD);
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_daily[j+row].day_columns_y[z]
											, rows_night_daily[j+row].day_qc_columns_y[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);

			j = 0;
			sprintf(buffer, "%s_NEE_percentiles_c_night_dd.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for dd night c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_STRING);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
				if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
					y /= 2;
				}
				y /= rows_per_day;
				for ( row = 0; row < y; row++ ) {
					t = timestamp_end_by_row(row*((HOURLY_TIMERES == datasets[dataset].details->timeres) ? 24 : 48)
								, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
					fprintf(f, "%04d%02d%02d", t->YYYY, t->MM, t->DD);
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_daily[j+row].night_columns_c[z]
											, rows_night_daily[j+row].night_qc_columns_c[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);

			j = 0;
			sprintf(buffer, "%s_NEE_percentiles_c_day_dd.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for dd day c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_STRING);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				y = IS_LEAP_YEAR(datasets[dataset].years[i].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
				if ( HOURLY_TIMERES == datasets[dataset].details->timeres ) {
					y /= 2;
				}
				y /= rows_per_day;
				for ( row = 0; row < y; row++ ) {
					t = timestamp_end_by_row(row*((HOURLY_TIMERES == datasets[dataset].details->timeres) ? 24 : 48)
								, datasets[dataset].years[i].year, datasets[dataset].details->timeres);
					fprintf(f, "%04d%02d%02d", t->YYYY, t->MM, t->DD);
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_daily[j+row].day_columns_c[z]
											, rows_night_daily[j+row].day_qc_columns_c[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);
		}*/

		/* update ref stuff */
		update_ref(&datasets[dataset], rows_night_daily, daily_rows_count, nee_matrix_y, nee_matrix_c, ref_y, ref_c);

		/* ref changed ? */
		if ( (ref_y_old != ref_y) || (ref_c_old != ref_c) ) {
			/* revert back qcs */
			revert_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				revert_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}

			/* compute random again */
			if ( ! compute_rand_unc(&datasets[dataset], unc_rows, nee_matrix_y, nee_matrix_c, ref_y, ref_c) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
					free(nee_matrix_c_daily);
				}
				continue;
			}

			/* change qcs */
			change_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				change_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}

			if ( ! compute_night_rand(&datasets[dataset], rows_night_daily, unc_rows) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
					free(nee_matrix_c_daily);
				}
				continue;
			}
			rand_unc_dd(unc_rows, unc_rows_aggr, datasets[dataset].rows_count, datasets[dataset].years_count, (HOURLY_TIMERES == datasets[dataset].details->timeres));
			ref_y_old = ref_y;
			ref_c_old = ref_c;
		}
	
		/* aggr ww nights */
		j = 0;
		index = 0;
		element = 0;
		for ( year = 0; year < datasets[dataset].years_count; year++ ) {
			y = IS_LEAP_YEAR(datasets[dataset].years[year].year) ? LEAP_YEAR_ROWS : YEAR_ROWS;
			if ( HOURLY_TIMERES == datasets[dataset].details->timeres  ) {
				y /= 2;
			}

			/* */
			y /= rows_per_day;

			for ( i = 0; i < 51; i++ ) {
				row = i*7;
				rows_night_weekly[index+i].night_total = 0;
				rows_night_weekly[index+i].day_total = 0;
				for ( j = 0; j < 7; j++ ) {
					rows_night_weekly[index+i].night_total += rows_night_daily[element+row+j].night_total;
					rows_night_weekly[index+i].day_total += rows_night_daily[element+row+j].day_total;
				}
				rows_night_weekly[index+i].night_total /= 7;
				rows_night_weekly[index+i].day_total /= 7;
				for ( percentile = 0; percentile < NIGHT_VALUES; percentile++ ) {
					/* do not compute _c if years count is less than 3 */
					if ( (datasets[dataset].years_count < 3) &&
							((NEE_REF_C == percentile) || (NEE_UST50_C == percentile) || (NEE_REF_C_RAND == percentile) || (NEE_UST50_C_RAND == percentile) ||
							(NEE_05_C == percentile) || (NEE_05_QC_C == percentile) || (NEE_16_C == percentile) || (NEE_16_QC_C == percentile) ||
							(NEE_25_C == percentile) || (NEE_25_QC_C == percentile) || (NEE_50_C == percentile) || (NEE_50_QC_C == percentile) ||
							(NEE_75_C == percentile) || (NEE_75_QC_C == percentile) ||
							(NEE_84_C == percentile) || (NEE_84_QC_C == percentile) || (NEE_95_C == percentile) || (NEE_95_QC_C == percentile))
							) {
						continue;
					}
					nights_rand_sum = 0;
					days_rand_sum = 0;
					rows_night_weekly[index+i].night[percentile] = 0.0;
					rows_night_weekly[index+i].night_d = 0;
					if ( percentile < NIGHT_QC_VALUES ) {
						rows_night_weekly[index+i].night_std[percentile] = 0.0;
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_weekly[index+i].night_qc[percentile] = 0.0;
					}
					rows_night_weekly[index+i].day[percentile] = 0.0;
					rows_night_weekly[index+i].day_d = 0;
					if ( percentile < NIGHT_QC_VALUES ) {
						rows_night_weekly[index+i].day_std[percentile] = 0.0;
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_weekly[index+i].day_qc[percentile] = 0.0;
					}
					valid_values_count_night = 0;
					valid_values_count_day = 0;
					for ( j = 0; j < 7; j++ ) {
						if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
							if ( ! IS_INVALID_VALUE(rows_night_daily[element+row+j].night[percentile]) ) {
								rows_night_weekly[index+i].night[percentile] += rows_night_daily[element+row+j].night[percentile];
								++valid_values_count_night;
							}
							rows_night_weekly[index+i].night_d += rows_night_daily[element+row+j].night_d;
						} else {
							value = rows_night_daily[element+row+j].night[percentile];
							if ( ! IS_INVALID_VALUE(value) ) {
								value *= value;
								value *= (rows_night_daily[element+row+j].night_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[element+row+j].night_d_rand[percentile-NIGHT_QC_VALUES]);
								rows_night_weekly[index+i].night[percentile] += value;
								nights_rand_sum += rows_night_daily[element+row+j].night_d_rand[percentile-NIGHT_QC_VALUES];
							}
						}
						if ( (percentile < NIGHT_QC_VALUES) && ! IS_INVALID_VALUE(rows_night_daily[element+row+j].night_std[percentile]) ) {
							rows_night_weekly[index+i].night_std[percentile] += rows_night_daily[element+row+j].night_std[percentile];
						}
						if ( percentile < NIGHT_RAND_VALUES ) {
							rows_night_weekly[index+i].night_qc[percentile] += rows_night_daily[element+row+j].night_qc[percentile];
						}
						if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
							if ( ! IS_INVALID_VALUE(rows_night_daily[element+row+j].day[percentile]) ) {
								rows_night_weekly[index+i].day[percentile] += rows_night_daily[element+row+j].day[percentile];
								++valid_values_count_day;
							}
							rows_night_weekly[index+i].day_d += rows_night_daily[element+row+j].day_d;
						} else {
							value = rows_night_daily[element+row+j].day[percentile];
							if ( !IS_INVALID_VALUE(value) ) {
								value *= value;
								value *= (rows_night_daily[element+row+j].day_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[element+row+j].day_d_rand[percentile-NIGHT_QC_VALUES]);
								rows_night_weekly[index+i].day[percentile] += value;
								days_rand_sum += rows_night_daily[element+row+j].day_d_rand[percentile-NIGHT_QC_VALUES];
							}
						}
						if ( (percentile < NIGHT_QC_VALUES) && ! IS_INVALID_VALUE(rows_night_daily[element+row+j].day_std[percentile]) ) {
							rows_night_weekly[index+i].day_std[percentile] += rows_night_daily[element+row+j].day_std[percentile];

						}
						if ( percentile < NIGHT_RAND_VALUES ) {
							rows_night_weekly[index+i].day_qc[percentile] += rows_night_daily[element+row+j].day_qc[percentile];
						}
					}

					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( valid_values_count_night ) {
							rows_night_weekly[index+i].night[percentile] /= valid_values_count_night;
							rows_night_weekly[index+i].night_d /= valid_values_count_night;
						}
					} else {
						if ( nights_rand_sum ) {
							rows_night_weekly[index+i].night[percentile] = SQRT(rows_night_weekly[index+i].night[percentile]) / nights_rand_sum;
						} else {
							rows_night_weekly[index+i].night[percentile] = INVALID_VALUE;
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_night ) {
						rows_night_weekly[index+i].night_std[percentile] /= valid_values_count_night;
					}
					if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_night ) {
						rows_night_weekly[index+i].night_qc[percentile] /= valid_values_count_night;
					}
					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( valid_values_count_day ) {
							rows_night_weekly[index+i].day[percentile] /= valid_values_count_day;
							rows_night_weekly[index+i].day_d /= valid_values_count_day;
						}
					} else {
						if ( days_rand_sum ) {
							rows_night_weekly[index+i].day[percentile] = SQRT(rows_night_weekly[index+i].day[percentile]) / days_rand_sum;
						} else {
							rows_night_weekly[index+i].day[percentile] = INVALID_VALUE;
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_day ) {
						rows_night_weekly[index+i].day_std[percentile] /= valid_values_count_day;
					}
					if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_day ) {
						rows_night_weekly[index+i].day_qc[percentile] /= valid_values_count_day;
					}
				}
			}
			row += j; /* 51*7 */; 
			z = y-row;
			rows_night_weekly[index+i].night_total = 0;
			rows_night_weekly[index+i].day_total = 0;
			for ( j = 0; j < z; j++ ) {
				rows_night_weekly[index+i].night_total += rows_night_daily[element+row+j].night_total;
				rows_night_weekly[index+i].day_total += rows_night_daily[element+row+j].day_total;
			}
			rows_night_weekly[index+i].night_total /= z;
			rows_night_weekly[index+i].day_total /= z;
			for ( percentile = 0; percentile < NIGHT_VALUES; percentile++ ) {
				/* do not compute _c if years count is less than 3 */
				if ( (datasets[dataset].years_count < 3) &&
						((NEE_REF_C == percentile) || (NEE_UST50_C == percentile) || (NEE_REF_C_RAND == percentile) || (NEE_UST50_C_RAND == percentile) ||
						(NEE_05_C == percentile) || (NEE_05_QC_C == percentile) || (NEE_16_C == percentile) || (NEE_16_QC_C == percentile) ||
						(NEE_25_C == percentile) || (NEE_25_QC_C == percentile) || (NEE_50_C == percentile) || (NEE_50_QC_C == percentile) ||
						(NEE_75_C == percentile) || (NEE_75_QC_C == percentile) ||
						(NEE_84_C == percentile) || (NEE_84_QC_C == percentile) || (NEE_95_C == percentile) || (NEE_95_QC_C == percentile))
						) {
					continue;
				}

				nights_rand_sum = 0;
				days_rand_sum = 0;
				rows_night_weekly[index+i].night[percentile] = 0.0;
				rows_night_weekly[index+i].night_d = 0;
				if ( percentile < NIGHT_QC_VALUES ) {
					rows_night_weekly[index+i].night_std[percentile] = 0.0;
				}
				if ( percentile < NIGHT_RAND_VALUES ) {
					rows_night_weekly[index+i].night_qc[percentile] = 0.0;
				}
				rows_night_weekly[index+i].day[percentile] = 0.0;
				rows_night_weekly[index+i].day_d = 0;
				if ( percentile < NIGHT_QC_VALUES ) {
					rows_night_weekly[index+i].day_std[percentile] = 0.0;
				}
				if ( percentile < NIGHT_RAND_VALUES ) {
					rows_night_weekly[index+i].day_qc[percentile] = 0.0;
				}
				valid_values_count_night = 0;
				valid_values_count_day = 0;
				for ( j = 0; j < z; j++ ) {
					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( ! IS_INVALID_VALUE(rows_night_daily[element+row+j].night[percentile]) ) {
							rows_night_weekly[index+i].night[percentile] += rows_night_daily[element+row+j].night[percentile];
							++valid_values_count_night;
						}
						rows_night_weekly[index+i].night_d += rows_night_daily[element+row+j].night_d;
					} else {
						value = rows_night_daily[element+row+j].night[percentile];
						if ( ! IS_INVALID_VALUE(value) ) {
							value *= value;
							value *= (rows_night_daily[element+row+j].night_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[element+row+j].night_d_rand[percentile-NIGHT_QC_VALUES]);
							rows_night_weekly[index+i].night[percentile] += value;
							nights_rand_sum += rows_night_daily[element+row+j].night_d_rand[percentile-NIGHT_QC_VALUES];
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) && ! IS_INVALID_VALUE(rows_night_daily[element+row+j].night_std[percentile])  ) {
						rows_night_weekly[index+i].night_std[percentile] += rows_night_daily[element+row+j].night_std[percentile];
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_weekly[index+i].night_qc[percentile] += rows_night_daily[element+row+j].night_qc[percentile];
					}
					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( ! IS_INVALID_VALUE(rows_night_daily[element+row+j].day[percentile]) ) {
							rows_night_weekly[index+i].day[percentile] += rows_night_daily[element+row+j].day[percentile];
							++valid_values_count_day;
						}
						rows_night_weekly[index+i].day_d += rows_night_daily[element+row+j].day_d;
					} else {
						value = rows_night_daily[element+row+j].day[percentile];
						if ( ! IS_INVALID_VALUE(value) ) {
							value *= value;
							value *= (rows_night_daily[element+row+j].day_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[element+row+j].day_d_rand[percentile-NIGHT_QC_VALUES]);
							rows_night_weekly[index+i].day[percentile] += value;
							days_rand_sum += rows_night_daily[element+row+j].day_d_rand[percentile-NIGHT_QC_VALUES];
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) &&  ! IS_INVALID_VALUE(rows_night_daily[element+row+j].day_std[percentile]) ) {
						rows_night_weekly[index+i].day_std[percentile] += rows_night_daily[element+row+j].day_std[percentile];
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_weekly[index+i].day_qc[percentile] += rows_night_daily[element+row+j].day_qc[percentile];
					}
				}
				if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
					if ( valid_values_count_night ) {
						rows_night_weekly[index+i].night[percentile] /= valid_values_count_night;
						rows_night_weekly[index+i].night_d /= valid_values_count_night;
					}
				} else {
					if( nights_rand_sum ) {
						rows_night_weekly[index+i].night[percentile] = SQRT(rows_night_weekly[index+i].night[percentile]) / nights_rand_sum;
					} else {
						rows_night_weekly[index+i].night[percentile] = INVALID_VALUE;
					}
				}
				if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_night ) {
					rows_night_weekly[index+i].night_std[percentile] /= valid_values_count_night;
				}
				if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_night ) {
					rows_night_weekly[index+i].night_qc[percentile] /= valid_values_count_night;
				}
				if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
					if ( valid_values_count_day ) {
						rows_night_weekly[index+i].day[percentile] /= valid_values_count_day;
						rows_night_weekly[index+i].day_d /= valid_values_count_day;
					}
				} else {
					if ( days_rand_sum ) {
						rows_night_weekly[index+i].day[percentile] = SQRT(rows_night_weekly[index+i].day[percentile]) / days_rand_sum;
					} else {
						rows_night_weekly[index+i].day[percentile] = INVALID_VALUE;
					}
				}
				if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_day ) {
					rows_night_weekly[index+i].day_std[percentile] /= valid_values_count_day;
				}
				if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_day ) {
					rows_night_weekly[index+i].day_qc[percentile] /= valid_values_count_day;
				}
			}
			/* */
			index += 52;
			element += y;
		}
		
		/* update percentile and qc*/
		if ( ! update_ww(&datasets[dataset], rows_night_daily, daily_rows_count, rows_night_weekly, weekly_rows_count) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_weekly);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_c_weekly);
			free(nee_matrix_y_weekly);
			free(nee_matrix_c_daily);
			free(nee_matrix_y_daily);
			free(p_matrix_y);
			continue;
		}

		/* save ww percentiles for night and day */
		/*
		if ( percentiles_save ) {
			j = 0;
			y = 52;
			sprintf(buffer, "%s_NEE_percentiles_y_night_ww.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for ww night y");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_HEADER);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				for ( row = 0; row < y; row++ ) {
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 1));
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 0));
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_weekly[j+row].night_columns_y[z]
											, rows_night_weekly[j+row].night_qc_columns_y[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);

			j = 0;
			sprintf(buffer, "%s_NEE_percentiles_y_day_ww.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for ww day y");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_HEADER);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				for ( row = 0; row < y; row++ ) {
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 1));
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 0));
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_weekly[j+row].day_columns_y[z]
											, rows_night_weekly[j+row].day_qc_columns_y[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);

			j = 0;
			sprintf(buffer, "%s_NEE_percentiles_c_night_ww.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for ww night c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_HEADER);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				for ( row = 0; row < y; row++ ) {
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 1));
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 0));
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_weekly[j+row].night_columns_c[z]
											, rows_night_weekly[j+row].night_qc_columns_c[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);

			j = 0;
			sprintf(buffer, "%s_NEE_percentiles_c_day_ww.csv", datasets[dataset].details->site);
			f = fopen(buffer, "w");
			if ( ! f ) {
				puts("unable to save nee percentiles for ww day c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_weekly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_weekly);
				free(nee_matrix_y_weekly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
			fprintf(f, "%s", TIMESTAMP_HEADER);
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				fprintf(f, ",%g,%g_qc", percentiles_test_2[percentile], percentiles_test_2[percentile]);
			}
			fputs("\n", f);
			for ( i = 0; i < datasets[dataset].years_count; i++ ) {
				for ( row = 0; row < y; row++ ) {
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 1));
					fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 0));
					for ( z = 0; z < PERCENTILES_COUNT_2; ++z ) {
						fprintf(f, ",%g,%g", rows_night_weekly[j+row].day_columns_c[z]
											, rows_night_weekly[j+row].day_qc_columns_c[z]);
					}
					fputs("\n", f);
				}
				j += y;
			}
			fclose(f);
		}
		*/

		/* rand unc ww */
		if ( ! no_rand_unc ) {
			rand_unc_ww(unc_rows_aggr, unc_rows_temp, datasets[dataset].rows_count / rows_per_day, datasets[dataset].years[0].year, datasets[dataset].years_count);
		}

		printf("ok\nsaving ww...");

		/* save output ww */
		sprintf(buffer, output_file_ww, output_files_path, datasets[dataset].details->site);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n\n", buffer);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_weekly);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_weekly);
			free(nee_matrix_y_daily);
			free(p_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_weekly);
				free(nee_matrix_c_daily);
			}
			continue;
		}

		/* write header ww */
		fprintf(f, header_file_ww, TIMESTAMP_HEADER);
		if ( no_rand_unc ) {
			fputs(output_var_1, f);
		} else {
			fputs(output_var_1_rand_unc, f);
		}
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "NEE_%02g_y,NEE_%02g_qc_y", percentiles_test_1[percentile],percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(output_var_2, f);
			} else {
				fputs(output_var_2_rand_unc, f);
			}
			for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
				fprintf(f, "NEE_%02g_c,NEE_%02g_qc_c", percentiles_test_1[percentile],percentiles_test_1[percentile]);
				if ( percentile < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}
		}
		if ( no_rand_unc ) {
			fputs(header_file_night_no_rand_unc, f);
			fputs(header_file_night_y_no_rand_unc, f);
		} else {
			fputs(header_file_night, f);
			fputs(header_file_night_y, f);
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(header_file_night_c_no_rand_unc, f);
			} else {
				fputs(header_file_night_c, f);
			}
		} else {
			fputs("\n", f);
		}

		/* write values ww */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < 52; row++ ) {
				/* timestamp_start */
				fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 1));
				/* timestamp_end */
				fprintf(f, "%s,", timestamp_ww_get_by_row_s(row, datasets[dataset].years[i].year, datasets[dataset].details->timeres, 0));
				/* week */
				fprintf(f, "%d,", row+1);
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_y_weekly[j+row].nee[ref_y],
															nee_matrix_y_weekly[j+row].qc[ref_y],
															nee_matrix_y_weekly[j+row].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_y_weekly[j+row].qc[PERCENTILES_COUNT_2-1],
															p_matrix_y[j+row].mean,
															p_matrix_y[j+row].mean_qc,
															p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_joinUnc_y = compute_join(unc_rows_temp[j+row].rand[NEE_REF_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						nee_ust50_joinUnc_y = compute_join(unc_rows_temp[j+row].rand[NEE_UST50_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_y_weekly[j+row].nee[ref_y],
															nee_matrix_y_weekly[j+row].qc[ref_y],
															unc_rows_temp[j+row].rand[NEE_REF_Y_UNC],
															nee_ref_joinUnc_y,
															nee_matrix_y_weekly[j+row].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_y_weekly[j+row].qc[PERCENTILES_COUNT_2-1],
															unc_rows_temp[j+row].rand[NEE_UST50_Y_UNC],
															nee_ust50_joinUnc_y,
															p_matrix_y[j+row].mean,
															p_matrix_y[j+row].mean_qc,
															p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				}
				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g,%g,", p_matrix_y[j+row].value[z], p_matrix_y[j+row].qc[z]);
					} else {
						fprintf(f, "%g,%g,", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
					}
				}

				if ( datasets[dataset].years_count >= 3 ) {
					if ( no_rand_unc ) {
						if ( exists ) {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
																nee_matrix_c_weekly[j+row].nee[ref_c],
																nee_matrix_c_weekly[j+row].qc[ref_c],
																nee_matrix_c_weekly[j+row].nee[PERCENTILES_COUNT_2-1],
																nee_matrix_c_weekly[j+row].qc[PERCENTILES_COUNT_2-1],
																p_matrix_c[j+row].mean,
																p_matrix_c[j+row].mean_qc,
																p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
							);
						}
					} else {
						if ( exists ) {
							nee_ref_joinUnc_c = compute_join(unc_rows_temp[j+row].rand[NEE_REF_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							nee_ust50_joinUnc_c = compute_join(unc_rows_temp[j+row].rand[NEE_UST50_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
																nee_matrix_c_weekly[j+row].nee[ref_c],
																nee_matrix_c_weekly[j+row].qc[ref_c],
																unc_rows_temp[j+row].rand[NEE_REF_C_UNC],
																nee_ref_joinUnc_c,
																nee_matrix_c_weekly[j+row].nee[PERCENTILES_COUNT_2-1],
																nee_matrix_c_weekly[j+row].qc[PERCENTILES_COUNT_2-1],
																unc_rows_temp[j+row].rand[NEE_UST50_C_UNC],
																nee_ust50_joinUnc_c,
																p_matrix_c[j+row].mean,
																p_matrix_c[j+row].mean_qc,
																p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE,
																(PREC)INVALID_VALUE
							);
						}
					}
					for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
						if ( exists ) {
							fprintf(f, "%g,%g,", p_matrix_c[j+row].value[z], p_matrix_c[j+row].qc[z]);
						} else {
							fprintf(f, "%g,%g,", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
						}
					}
				}
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,",
															rows_night_weekly[j+row].night_total,
															rows_night_weekly[j+row].day_total
						);
					} else {
						fprintf(f, "%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,",
															rows_night_weekly[j+row].night_total,
															rows_night_weekly[j+row].day_total,
															rows_night_weekly[j+row].night_d,
															rows_night_weekly[j+row].day_d
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				}
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														rows_night_weekly[j+row].night[NEE_REF_Y],
														rows_night_weekly[j+row].night_std[NEE_REF_Y],
														rows_night_weekly[j+row].night_qc[NEE_REF_Y],
														rows_night_weekly[j+row].day[NEE_REF_Y],
														rows_night_weekly[j+row].day_std[NEE_REF_Y],
														rows_night_weekly[j+row].day_qc[NEE_REF_Y],
														rows_night_weekly[j+row].night[NEE_UST50_Y],
														rows_night_weekly[j+row].night_std[NEE_UST50_Y],
														rows_night_weekly[j+row].night_qc[NEE_UST50_Y],
														rows_night_weekly[j+row].day[NEE_UST50_Y],
														rows_night_weekly[j+row].day_std[NEE_UST50_Y],
														rows_night_weekly[j+row].day_qc[NEE_UST50_Y],
														rows_night_weekly[j+row].night[NEE_05_Y],
														rows_night_weekly[j+row].night[NEE_05_QC_Y],
														rows_night_weekly[j+row].night[NEE_16_Y],
														rows_night_weekly[j+row].night[NEE_16_QC_Y],
														rows_night_weekly[j+row].night[NEE_25_Y],
														rows_night_weekly[j+row].night[NEE_25_QC_Y],
														rows_night_weekly[j+row].night[NEE_50_Y],
														rows_night_weekly[j+row].night[NEE_50_QC_Y],
														rows_night_weekly[j+row].night[NEE_75_Y],
														rows_night_weekly[j+row].night[NEE_75_QC_Y],
														rows_night_weekly[j+row].night[NEE_84_Y],
														rows_night_weekly[j+row].night[NEE_84_QC_Y],
														rows_night_weekly[j+row].night[NEE_95_Y],
														rows_night_weekly[j+row].night[NEE_95_QC_Y],
														rows_night_weekly[j+row].day[NEE_05_Y],
														rows_night_weekly[j+row].day[NEE_05_QC_Y],
														rows_night_weekly[j+row].day[NEE_16_Y],
														rows_night_weekly[j+row].day[NEE_16_QC_Y],
														rows_night_weekly[j+row].day[NEE_25_Y],
														rows_night_weekly[j+row].day[NEE_25_QC_Y],
														rows_night_weekly[j+row].day[NEE_50_Y],
														rows_night_weekly[j+row].day[NEE_50_QC_Y],
														rows_night_weekly[j+row].day[NEE_75_Y],
														rows_night_weekly[j+row].day[NEE_75_QC_Y],
														rows_night_weekly[j+row].day[NEE_84_Y],
														rows_night_weekly[j+row].day[NEE_84_QC_Y],
														rows_night_weekly[j+row].day[NEE_95_Y],
														rows_night_weekly[j+row].day[NEE_95_QC_Y]
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_night_joinUnc_y = compute_join(rows_night_weekly[j+row].night[NEE_REF_Y_RAND],rows_night_weekly[j+row].night[NEE_16_Y],rows_night_weekly[j+row].night[NEE_84_Y]);
						nee_ref_day_joinUnc_y = compute_join(rows_night_weekly[j+row].day[NEE_REF_Y_RAND],rows_night_weekly[j+row].day[NEE_16_Y],rows_night_weekly[j+row].day[NEE_84_Y]);
						nee_ust50_night_joinUnc_y = compute_join(rows_night_weekly[j+row].night[NEE_UST50_Y_RAND],rows_night_weekly[j+row].night[NEE_16_Y],rows_night_weekly[j+row].night[NEE_84_Y]);
						nee_ust50_day_joinUnc_y = compute_join(rows_night_weekly[j+row].day[NEE_UST50_Y_RAND],rows_night_weekly[j+row].day[NEE_16_Y],rows_night_weekly[j+row].day[NEE_84_Y]);
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														rows_night_weekly[j+row].night[NEE_REF_Y],
														rows_night_weekly[j+row].night_std[NEE_REF_Y],
														rows_night_weekly[j+row].night_qc[NEE_REF_Y],
														rows_night_weekly[j+row].night[NEE_REF_Y_RAND],
														nee_ref_night_joinUnc_y,
														rows_night_weekly[j+row].day[NEE_REF_Y],
														rows_night_weekly[j+row].day_std[NEE_REF_Y],
														rows_night_weekly[j+row].day_qc[NEE_REF_Y],
														rows_night_weekly[j+row].day[NEE_REF_Y_RAND],
														nee_ref_day_joinUnc_y,
														rows_night_weekly[j+row].night[NEE_UST50_Y],
														rows_night_weekly[j+row].night_std[NEE_UST50_Y],
														rows_night_weekly[j+row].night_qc[NEE_UST50_Y],
														rows_night_weekly[j+row].night[NEE_UST50_Y_RAND],
														nee_ust50_night_joinUnc_y,
														rows_night_weekly[j+row].day[NEE_UST50_Y],
														rows_night_weekly[j+row].day_std[NEE_UST50_Y],
														rows_night_weekly[j+row].day_qc[NEE_UST50_Y],
														rows_night_weekly[j+row].day[NEE_UST50_Y_RAND],
														nee_ust50_day_joinUnc_y,
														rows_night_weekly[j+row].night[NEE_05_Y],
														rows_night_weekly[j+row].night[NEE_05_QC_Y],
														rows_night_weekly[j+row].night[NEE_16_Y],
														rows_night_weekly[j+row].night[NEE_16_QC_Y],
														rows_night_weekly[j+row].night[NEE_25_Y],
														rows_night_weekly[j+row].night[NEE_25_QC_Y],
														rows_night_weekly[j+row].night[NEE_50_Y],
														rows_night_weekly[j+row].night[NEE_50_QC_Y],
														rows_night_weekly[j+row].night[NEE_75_Y],
														rows_night_weekly[j+row].night[NEE_75_QC_Y],
														rows_night_weekly[j+row].night[NEE_84_Y],
														rows_night_weekly[j+row].night[NEE_84_QC_Y],
														rows_night_weekly[j+row].night[NEE_95_Y],
														rows_night_weekly[j+row].night[NEE_95_QC_Y],
														rows_night_weekly[j+row].day[NEE_05_Y],
														rows_night_weekly[j+row].day[NEE_05_QC_Y],
														rows_night_weekly[j+row].day[NEE_16_Y],
														rows_night_weekly[j+row].day[NEE_16_QC_Y],
														rows_night_weekly[j+row].day[NEE_25_Y],
														rows_night_weekly[j+row].day[NEE_25_QC_Y],
														rows_night_weekly[j+row].day[NEE_50_Y],
														rows_night_weekly[j+row].day[NEE_50_QC_Y],
														rows_night_weekly[j+row].day[NEE_75_Y],
														rows_night_weekly[j+row].day[NEE_75_QC_Y],
														rows_night_weekly[j+row].day[NEE_84_Y],
														rows_night_weekly[j+row].day[NEE_84_QC_Y],
														rows_night_weekly[j+row].day[NEE_95_Y],
														rows_night_weekly[j+row].day[NEE_95_QC_Y]
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
						);
					}
				}

				if ( datasets[dataset].years_count >= 3 ) {
					if ( no_rand_unc ) {
						if ( exists ) {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														rows_night_weekly[j+row].night[NEE_REF_C],
														rows_night_weekly[j+row].night_std[NEE_REF_C],
														rows_night_weekly[j+row].night_qc[NEE_REF_C],
														rows_night_weekly[j+row].day[NEE_REF_C],
														rows_night_weekly[j+row].day_std[NEE_REF_C],
														rows_night_weekly[j+row].day_qc[NEE_REF_C],
														rows_night_weekly[j+row].night[NEE_UST50_C],
														rows_night_weekly[j+row].night_std[NEE_UST50_C],
														rows_night_weekly[j+row].night_qc[NEE_UST50_C],
														rows_night_weekly[j+row].day[NEE_UST50_C],
														rows_night_weekly[j+row].day_std[NEE_UST50_C],
														rows_night_weekly[j+row].day_qc[NEE_UST50_C],
														rows_night_weekly[j+row].night[NEE_05_C],
														rows_night_weekly[j+row].night[NEE_05_QC_C],
														rows_night_weekly[j+row].night[NEE_16_C],
														rows_night_weekly[j+row].night[NEE_16_QC_C],
														rows_night_weekly[j+row].night[NEE_25_C],
														rows_night_weekly[j+row].night[NEE_25_QC_C],
														rows_night_weekly[j+row].night[NEE_50_C],
														rows_night_weekly[j+row].night[NEE_50_QC_C],
														rows_night_weekly[j+row].night[NEE_75_C],
														rows_night_weekly[j+row].night[NEE_75_QC_C],
														rows_night_weekly[j+row].night[NEE_84_C],
														rows_night_weekly[j+row].night[NEE_84_QC_C],
														rows_night_weekly[j+row].night[NEE_95_C],
														rows_night_weekly[j+row].night[NEE_95_QC_C],
														rows_night_weekly[j+row].day[NEE_05_C],
														rows_night_weekly[j+row].day[NEE_05_QC_C],
														rows_night_weekly[j+row].day[NEE_16_C],
														rows_night_weekly[j+row].day[NEE_16_QC_C],
														rows_night_weekly[j+row].day[NEE_25_C],
														rows_night_weekly[j+row].day[NEE_25_QC_C],
														rows_night_weekly[j+row].day[NEE_50_C],
														rows_night_weekly[j+row].day[NEE_50_QC_C],
														rows_night_weekly[j+row].day[NEE_75_C],
														rows_night_weekly[j+row].day[NEE_75_QC_C],
														rows_night_weekly[j+row].day[NEE_84_C],
														rows_night_weekly[j+row].day[NEE_84_QC_C],
														rows_night_weekly[j+row].day[NEE_95_C],
														rows_night_weekly[j+row].day[NEE_95_QC_C]
							);
						} else {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
							);
						}
					} else {
						if ( exists ) {
							nee_ref_night_joinUnc_c = compute_join(rows_night_weekly[j+row].night[NEE_REF_C_RAND],rows_night_weekly[j+row].night[NEE_16_C],rows_night_weekly[j+row].night[NEE_84_C]);
							nee_ref_day_joinUnc_c = compute_join(rows_night_weekly[j+row].day[NEE_REF_C_RAND],rows_night_weekly[j+row].day[NEE_16_C],rows_night_weekly[j+row].day[NEE_84_C]);
							nee_ust50_night_joinUnc_c = compute_join(rows_night_weekly[j+row].night[NEE_UST50_C_RAND],rows_night_weekly[j+row].night[NEE_16_C],rows_night_weekly[j+row].night[NEE_84_C]);
							nee_ust50_day_joinUnc_c = compute_join(rows_night_weekly[j+row].day[NEE_UST50_C_RAND],rows_night_weekly[j+row].day[NEE_16_C],rows_night_weekly[j+row].day[NEE_84_C]);
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														rows_night_weekly[j+row].night[NEE_REF_C],
														rows_night_weekly[j+row].night_std[NEE_REF_C],
														rows_night_weekly[j+row].night_qc[NEE_REF_C],
														rows_night_weekly[j+row].night[NEE_REF_C_RAND],
														nee_ref_night_joinUnc_c,
														rows_night_weekly[j+row].day[NEE_REF_C],
														rows_night_weekly[j+row].day_std[NEE_REF_C],
														rows_night_weekly[j+row].day_qc[NEE_REF_C],
														rows_night_weekly[j+row].day[NEE_REF_C_RAND],
														nee_ref_day_joinUnc_c,
														rows_night_weekly[j+row].night[NEE_UST50_C],
														rows_night_weekly[j+row].night_std[NEE_UST50_C],
														rows_night_weekly[j+row].night_qc[NEE_UST50_C],
														rows_night_weekly[j+row].night[NEE_UST50_C_RAND],
														nee_ust50_night_joinUnc_c,
														rows_night_weekly[j+row].day[NEE_UST50_C],
														rows_night_weekly[j+row].day_std[NEE_UST50_C],
														rows_night_weekly[j+row].day_qc[NEE_UST50_C],
														rows_night_weekly[j+row].day[NEE_UST50_C_RAND],
														nee_ust50_day_joinUnc_c,
														rows_night_weekly[j+row].night[NEE_05_C],
														rows_night_weekly[j+row].night[NEE_05_QC_C],
														rows_night_weekly[j+row].night[NEE_16_C],
														rows_night_weekly[j+row].night[NEE_16_QC_C],
														rows_night_weekly[j+row].night[NEE_25_C],
														rows_night_weekly[j+row].night[NEE_25_QC_C],
														rows_night_weekly[j+row].night[NEE_50_C],
														rows_night_weekly[j+row].night[NEE_50_QC_C],
														rows_night_weekly[j+row].night[NEE_75_C],
														rows_night_weekly[j+row].night[NEE_75_QC_C],
														rows_night_weekly[j+row].night[NEE_84_C],
														rows_night_weekly[j+row].night[NEE_84_QC_C],
														rows_night_weekly[j+row].night[NEE_95_C],
														rows_night_weekly[j+row].night[NEE_95_QC_C],
														rows_night_weekly[j+row].day[NEE_05_C],
														rows_night_weekly[j+row].day[NEE_05_QC_C],
														rows_night_weekly[j+row].day[NEE_16_C],
														rows_night_weekly[j+row].day[NEE_16_QC_C],
														rows_night_weekly[j+row].day[NEE_25_C],
														rows_night_weekly[j+row].day[NEE_25_QC_C],
														rows_night_weekly[j+row].day[NEE_50_C],
														rows_night_weekly[j+row].day[NEE_50_QC_C],
														rows_night_weekly[j+row].day[NEE_75_C],
														rows_night_weekly[j+row].day[NEE_75_QC_C],
														rows_night_weekly[j+row].day[NEE_84_C],
														rows_night_weekly[j+row].day[NEE_84_QC_C],
														rows_night_weekly[j+row].day[NEE_95_C],
														rows_night_weekly[j+row].day[NEE_95_QC_C]
							);
						} else {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
							);
						}
					}
				} else {
					fputs("\n", f);
				}
			}
			j += 52;
		}

		/* close file */
		fclose(f);

		/* free memory */
		free(rows_night_weekly);
		free(p_matrix_y);
		free(nee_matrix_y_weekly);
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
			free(nee_matrix_c_weekly);
		}
		
		/* save info ww */
		if ( ! save_info(&datasets[dataset], output_files_path, WW_TR, ref_y, ref_c, percentiles_y, percentiles_c) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c);
			}
			continue;
		}
		puts("ok");

		/*
		* 
		* monthly
		*
		*/

		printf("computing mm...");

		monthly_rows_count = 12 * datasets[dataset].years_count;
		nee_matrix_y_monthly = malloc(monthly_rows_count*sizeof*nee_matrix_y_monthly);
		if ( !nee_matrix_y_monthly ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_daily);
			}
			continue;
		}

		if ( datasets[dataset].years_count >= 3 ) {
			nee_matrix_c_monthly = malloc(monthly_rows_count*sizeof*nee_matrix_c_monthly);
			if ( !nee_matrix_c_monthly ) {
				puts(err_out_of_memory);
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_daily);
				free(nee_matrix_y_monthly);
				free(percentiles_y);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				continue;
			}
		}

		rows_night_monthly = malloc(monthly_rows_count*sizeof*rows_night_monthly);
		if ( !rows_night_monthly ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			free(nee_matrix_y_monthly);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_daily);
				free(nee_matrix_c_monthly);
			}
			continue;
		}

		/* compute mm */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			for ( i = 0; i < 12; i++ ) {
				for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
					nee_matrix_y_monthly[index+i].nee[percentile] = 0.0;
					nee_matrix_y_monthly[index+i].qc[percentile] = 0.0;
					if ( datasets[dataset].years_count >= 3 ) {
						nee_matrix_c_monthly[index+i].nee[percentile] = 0.0;
						nee_matrix_c_monthly[index+i].qc[percentile] = 0.0;
					}
					z = days_per_month[i];
					if ( (1 == i) && IS_LEAP_YEAR(year) ) {
						++z;
					}
					for ( j = 0; j < z; j++ ) {
						nee_matrix_y_monthly[index+i].nee[percentile] += nee_matrix_y_daily[row+j].nee[percentile];
						nee_matrix_y_monthly[index+i].qc[percentile] += nee_matrix_y_daily[row+j].qc[percentile];
						if ( datasets[dataset].years_count >= 3 ) {
							nee_matrix_c_monthly[index+i].nee[percentile] += nee_matrix_c_daily[row+j].nee[percentile];
							nee_matrix_c_monthly[index+i].qc[percentile] += nee_matrix_c_daily[row+j].qc[percentile];
						}
					}
					nee_matrix_y_monthly[index+i].nee[percentile] /= z;
					nee_matrix_y_monthly[index+i].qc[percentile] /= z;
					if ( datasets[dataset].years_count >= 3 ) {
						nee_matrix_c_monthly[index+i].nee[percentile] /= z;
						nee_matrix_c_monthly[index+i].qc[percentile] /= z;
					}
				}
				row += z;
			}
			++year;
			index += i;
		}

		/* saving y nee mm matrix */
		if ( percentiles_save ) {
			if ( ! save_nee_matrix(nee_matrix_y_monthly, &datasets[dataset], MM_Y) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_daily);
				free(rows_night_monthly);
				free(percentiles_y);
				free(nee_matrix_y_daily);
				free(nee_matrix_y_monthly);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c_daily);
					free(nee_matrix_c_monthly);
				}
				continue;
			}

			/* saving c nee mm matrix */
			if ( datasets[dataset].years_count >= 3 ) {
				if ( ! save_nee_matrix(nee_matrix_c_monthly, &datasets[dataset], MM_C) ) {
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(rows_night_weekly);
					free(rows_night_daily);
					free(percentiles_y);
					free(nee_matrix_y_weekly);
					free(nee_matrix_y_daily);
					free(nee_matrix_c_weekly);
					free(nee_matrix_c_daily);
					continue;
				}
			}
		}

		/* get p_matrix */
		p_matrix_y = process_nee_matrix(&datasets[dataset], nee_matrix_y_monthly, monthly_rows_count, &ref_y, MM_Y);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for monthly y");
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_daily);
			free(rows_night_monthly);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			free(nee_matrix_y_monthly);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_daily);
				free(nee_matrix_c_monthly);
			}
			continue;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_nee_matrix(&datasets[dataset], nee_matrix_c_monthly, monthly_rows_count, &ref_c, MM_C);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for monthly c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_monthly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_monthly);
				free(nee_matrix_y_monthly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
		}

		/* update ref stuff */
		update_ref(&datasets[dataset], rows_night_daily, daily_rows_count, nee_matrix_y, nee_matrix_c, ref_y, ref_c);

		/* ref changed ? */
		if ( (ref_y_old != ref_y) || (ref_c_old != ref_c) ) {
			/* revert back qcs */
			revert_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				revert_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}

			/* compute random again */
			if ( ! compute_rand_unc(&datasets[dataset], unc_rows, nee_matrix_y, nee_matrix_c, ref_y, ref_c) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
					free(nee_matrix_c_daily);
				}
				continue;
			}

			/* change qcs */
			change_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				change_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}

			rand_unc_dd(unc_rows, unc_rows_aggr, datasets[dataset].rows_count, datasets[dataset].years_count, (HOURLY_TIMERES == datasets[dataset].details->timeres));
			ref_y_old = ref_y;
			ref_c_old = ref_c;
		}

		/* aggr mm nights */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			for ( i = 0; i < 12; i++ ) {
				z = days_per_month[i];
				if ( (1 == i) && IS_LEAP_YEAR(year) ) {
					++z;
				}
				rows_night_monthly[index+i].night_total = 0;
				rows_night_monthly[index+i].day_total = 0;
				for ( j = 0; j < z; j++ ) {
					rows_night_monthly[index+i].night_total += rows_night_daily[row+j].night_total;
					rows_night_monthly[index+i].day_total += rows_night_daily[row+j].day_total;
				}
				rows_night_monthly[index+i].night_total /= j;
				rows_night_monthly[index+i].day_total /= j;
				for ( percentile = 0; percentile < NIGHT_VALUES; percentile++ ) {
					/* do not compute _c if years count is less than 3 */
					if ( (datasets[dataset].years_count < 3) &&
							((NEE_REF_C == percentile) || (NEE_UST50_C == percentile) || (NEE_REF_C_RAND == percentile) || (NEE_UST50_C_RAND == percentile) ||
							(NEE_05_C == percentile) || (NEE_05_QC_C == percentile) || (NEE_16_C == percentile) || (NEE_16_QC_C == percentile) ||
							(NEE_25_C == percentile) || (NEE_25_QC_C == percentile) || (NEE_50_C == percentile) || (NEE_50_QC_C == percentile) ||
							(NEE_75_C == percentile) || (NEE_75_QC_C == percentile) ||
							(NEE_84_C == percentile) || (NEE_84_QC_C == percentile) || (NEE_95_C == percentile) || (NEE_95_QC_C == percentile))
							) {
						continue;
					}
					nights_rand_sum = 0;
					days_rand_sum = 0;
					rows_night_monthly[index+i].night[percentile] = 0.0;
					rows_night_monthly[index+i].night_d = 0;
					if ( percentile < NIGHT_QC_VALUES ) {
						rows_night_monthly[index+i].night_std[percentile] = 0.0;
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_monthly[index+i].night_qc[percentile] = 0.0;
					}
					rows_night_monthly[index+i].day[percentile] = 0.0;
					rows_night_monthly[index+i].day_d = 0;
					if ( percentile < NIGHT_QC_VALUES ) {
						rows_night_monthly[index+i].day_std[percentile] = 0.0;
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_monthly[index+i].day_qc[percentile] = 0.0;
					}
					valid_values_count_night = 0;
					valid_values_count_day = 0;

					for ( j = 0; j < z; j++ ) {
						if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
							if ( ! IS_INVALID_VALUE(rows_night_daily[row+j].night[percentile]) ) {
								rows_night_monthly[index+i].night[percentile] += rows_night_daily[row+j].night[percentile];
								++valid_values_count_night;
							}
							rows_night_monthly[index+i].night_d += rows_night_daily[row+j].night_d;
						} else {
							value = rows_night_daily[row+j].night[percentile];
							if ( !IS_INVALID_VALUE(value) ) {
								value *= value;
								value *= (rows_night_daily[row+j].night_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[row+j].night_d_rand[percentile-NIGHT_QC_VALUES]);
								rows_night_monthly[index+i].night[percentile] += value;
								nights_rand_sum += rows_night_daily[row+j].night_d_rand[percentile-NIGHT_QC_VALUES];
							}
						}
						if ( (percentile < NIGHT_QC_VALUES) && ! IS_INVALID_VALUE(rows_night_daily[row+j].night_std[percentile])  ) {
							rows_night_monthly[index+i].night_std[percentile] += rows_night_daily[row+j].night_std[percentile];
						}
						if ( percentile < NIGHT_RAND_VALUES ) {
							rows_night_monthly[index+i].night_qc[percentile] += rows_night_daily[row+j].night_qc[percentile];
						}
						if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
							if ( ! IS_INVALID_VALUE(rows_night_daily[row+j].day[percentile]) ) {
								rows_night_monthly[index+i].day[percentile] += rows_night_daily[row+j].day[percentile];
								++valid_values_count_day;
							}
							rows_night_monthly[index+i].day_d += rows_night_daily[row+j].day_d;
						} else {
							value = rows_night_daily[row+j].day[percentile];
							if ( !IS_INVALID_VALUE(value) ) {
								value *= value;
								value *= (rows_night_daily[row+j].day_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[row+j].day_d_rand[percentile-NIGHT_QC_VALUES]);
								rows_night_monthly[index+i].day[percentile] += value;
								days_rand_sum += rows_night_daily[row+j].day_d_rand[percentile-NIGHT_QC_VALUES];
							}
						}
						if ( (percentile < NIGHT_QC_VALUES) && ! IS_INVALID_VALUE(rows_night_daily[row+j].day_std[percentile]) ) {
							rows_night_monthly[index+i].day_std[percentile] += rows_night_daily[row+j].day_std[percentile];
						}
						if ( percentile < NIGHT_RAND_VALUES ) {
							rows_night_monthly[index+i].day_qc[percentile] += rows_night_daily[row+j].day_qc[percentile];
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( valid_values_count_night ) {
							rows_night_monthly[index+i].night[percentile] /= valid_values_count_night;
							rows_night_monthly[index+i].night_d /= valid_values_count_night;
						}
					} else {
						if ( nights_rand_sum ) {
							rows_night_monthly[index+i].night[percentile] = SQRT(rows_night_monthly[index+i].night[percentile]) / nights_rand_sum;
						} else {
							rows_night_monthly[index+i].night[percentile] = INVALID_VALUE;
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_night ) {
						rows_night_monthly[index+i].night_std[percentile] /= valid_values_count_night;						
					}
					if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_night ) {
						rows_night_monthly[index+i].night_qc[percentile] /= valid_values_count_night;
					}
					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( valid_values_count_day ) {
							rows_night_monthly[index+i].day[percentile] /= valid_values_count_day;
							rows_night_monthly[index+i].day_d /= valid_values_count_day;
						}
					} else {
						if ( days_rand_sum ) {
							rows_night_monthly[index+i].day[percentile] = SQRT(rows_night_monthly[index+i].day[percentile]) / days_rand_sum;
						} else {
							rows_night_monthly[index+i].day[percentile] = INVALID_VALUE;
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_day ) {
						rows_night_monthly[index+i].day_std[percentile] /= valid_values_count_day;
					}
					if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_day ) {
						rows_night_monthly[index+i].day_qc[percentile] /= valid_values_count_day;
					}
				}

				/* */
				row += z;
			}

			/* */
			++year;
			index += i;
		}

		if ( ! update_mm(&datasets[dataset], rows_night_daily, daily_rows_count, rows_night_monthly, monthly_rows_count) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_daily);
			free(rows_night_monthly);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y_daily);
			free(nee_matrix_y_monthly);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c_daily);
				free(nee_matrix_c_monthly);
			}
			continue;
		}

		/* rand unc mm */
		if ( ! no_rand_unc ) {
			rand_unc_mm(unc_rows_aggr, unc_rows_temp, datasets[dataset].rows_count / rows_per_day, datasets[dataset].years[0].year, datasets[dataset].years_count);
		}
		printf("ok\nsaving mm...");

		/* save output mm */
		sprintf(buffer, output_file_mm, output_files_path, datasets[dataset].details->site);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n\n", buffer);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_daily);
			free(rows_night_monthly);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y_daily);
			free(nee_matrix_y_monthly);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c_daily);
				free(nee_matrix_c_monthly);
			}
			continue;
		}

		/* write header mm */
		fprintf(f, header_file_mm, TIMESTAMP_STRING);
		if ( no_rand_unc ) {
			fputs(output_var_1, f);
		} else {
			fputs(output_var_1_rand_unc, f);
		}
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "NEE_%02g_y,NEE_%02g_qc_y", percentiles_test_1[percentile],percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(output_var_2, f);
			} else {
				fputs(output_var_2_rand_unc, f);
			}
			for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
				fprintf(f, "NEE_%02g_c,NEE_%02g_qc_c", percentiles_test_1[percentile],percentiles_test_1[percentile]);
				if ( percentile < PERCENTILES_COUNT_1-1 ) {
					fputs(",", f);
				}
			}
		}
		
		if ( no_rand_unc ) {
			fputs(header_file_night_no_rand_unc, f);
			fputs(header_file_night_y_no_rand_unc, f);
		} else {
			fputs(header_file_night, f);
			fputs(header_file_night_y, f);
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(header_file_night_c_no_rand_unc, f);
			} else {
				fputs(header_file_night_c, f);
			}
		} else {
			fputs("\n", f);
		}

		/* write values mm */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			exists = datasets[dataset].years[i].exist;
			for ( row = 0; row < 12; row++ ) {
				fprintf(f, "%04d%02d,",				datasets[dataset].years[i].year,
													row+1
				);

				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_y_monthly[j+row].nee[ref_y],
															nee_matrix_y_monthly[j+row].qc[ref_y],
															nee_matrix_y_monthly[j+row].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_y_monthly[j+row].qc[PERCENTILES_COUNT_2-1],
															p_matrix_y[j+row].mean,
															p_matrix_y[j+row].mean_qc,
															p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_joinUnc_y = compute_join(unc_rows_temp[j+row].rand[NEE_REF_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						nee_ust50_joinUnc_y = compute_join(unc_rows_temp[j+row].rand[NEE_UST50_Y_UNC], p_matrix_y[j+row].value[1], p_matrix_y[j+row].value[5]);
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_y_monthly[j+row].nee[ref_y],
															nee_matrix_y_monthly[j+row].qc[ref_y],
															unc_rows_temp[j+row].rand[NEE_REF_Y_UNC],
															nee_ref_joinUnc_y,
															nee_matrix_y_monthly[j+row].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_y_monthly[j+row].qc[PERCENTILES_COUNT_2-1],
															unc_rows_temp[j+row].rand[NEE_UST50_Y_UNC],
															nee_ust50_joinUnc_y,
															p_matrix_y[j+row].mean,
															p_matrix_y[j+row].mean_qc,
															p_matrix_y[j+row].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				}
				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g,%g,", p_matrix_y[j+row].value[z], p_matrix_y[j+row].qc[z]);
					} else {
						fprintf(f, "%g,%g,", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
					}
				}
				if ( datasets[dataset].years_count >= 3 ) {
					if ( no_rand_unc ) {
						if ( exists ) {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_c_monthly[j+row].nee[ref_c],
															nee_matrix_c_monthly[j+row].qc[ref_c],
															nee_matrix_c_monthly[j+row].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_c_monthly[j+row].qc[PERCENTILES_COUNT_2-1],
															p_matrix_c[j+row].mean,
															p_matrix_c[j+row].mean_qc,
															p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
							);
						}
					} else {
						if ( exists ) {
							nee_ref_joinUnc_c = compute_join(unc_rows_temp[j+row].rand[NEE_REF_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							nee_ust50_joinUnc_c = compute_join(unc_rows_temp[j+row].rand[NEE_UST50_C_UNC], p_matrix_c[j+row].value[1], p_matrix_c[j+row].value[5]);
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_c_monthly[j+row].nee[ref_c],
															nee_matrix_c_monthly[j+row].qc[ref_c],
															unc_rows_temp[j+row].rand[NEE_REF_C_UNC],
															nee_ref_joinUnc_c,
															nee_matrix_c_monthly[j+row].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_c_monthly[j+row].qc[PERCENTILES_COUNT_2-1],
															unc_rows_temp[j+row].rand[NEE_UST50_C_UNC],
															nee_ust50_joinUnc_c,
															p_matrix_c[j+row].mean,
															p_matrix_c[j+row].mean_qc,
															p_matrix_c[j+row].std_err
							);
						} else {
							fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
							);
						}
					}
					for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
						if ( exists ) {
							fprintf(f, "%g,%g,", p_matrix_c[j+row].value[z], p_matrix_c[j+row].qc[z]);
						} else {
							fprintf(f, "%g,%g,", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
						}
					}
				}
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,",
															rows_night_monthly[j+row].night_total,
															rows_night_monthly[j+row].day_total
						);
					} else {
						fprintf(f, "%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,",
															rows_night_monthly[j+row].night_total,
															rows_night_monthly[j+row].day_total,
															rows_night_monthly[j+row].night_d,
															rows_night_monthly[j+row].day_d
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				}
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														rows_night_monthly[j+row].night[NEE_REF_Y],
														rows_night_monthly[j+row].night_std[NEE_REF_Y],
														rows_night_monthly[j+row].night_qc[NEE_REF_Y],
														rows_night_monthly[j+row].day[NEE_REF_Y],
														rows_night_monthly[j+row].day_std[NEE_REF_Y],
														rows_night_monthly[j+row].day_qc[NEE_REF_Y],
														rows_night_monthly[j+row].night[NEE_UST50_Y],
														rows_night_monthly[j+row].night_std[NEE_UST50_Y],
														rows_night_monthly[j+row].night_qc[NEE_UST50_Y],
														rows_night_monthly[j+row].day[NEE_UST50_Y],
														rows_night_monthly[j+row].day_std[NEE_UST50_Y],
														rows_night_monthly[j+row].day_qc[NEE_UST50_Y],
														rows_night_monthly[j+row].night[NEE_05_Y],
														rows_night_monthly[j+row].night[NEE_05_QC_Y],
														rows_night_monthly[j+row].night[NEE_16_Y],
														rows_night_monthly[j+row].night[NEE_16_QC_Y],
														rows_night_monthly[j+row].night[NEE_25_Y],
														rows_night_monthly[j+row].night[NEE_25_QC_Y],
														rows_night_monthly[j+row].night[NEE_50_Y],
														rows_night_monthly[j+row].night[NEE_50_QC_Y],
														rows_night_monthly[j+row].night[NEE_75_Y],
														rows_night_monthly[j+row].night[NEE_75_QC_Y],
														rows_night_monthly[j+row].night[NEE_84_Y],
														rows_night_monthly[j+row].night[NEE_84_QC_Y],
														rows_night_monthly[j+row].night[NEE_95_Y],
														rows_night_monthly[j+row].night[NEE_95_QC_Y],
														rows_night_monthly[j+row].day[NEE_05_Y],
														rows_night_monthly[j+row].day[NEE_05_QC_Y],
														rows_night_monthly[j+row].day[NEE_16_Y],
														rows_night_monthly[j+row].day[NEE_16_QC_Y],
														rows_night_monthly[j+row].day[NEE_25_Y],
														rows_night_monthly[j+row].day[NEE_25_QC_Y],
														rows_night_monthly[j+row].day[NEE_50_Y],
														rows_night_monthly[j+row].day[NEE_50_QC_Y],
														rows_night_monthly[j+row].day[NEE_75_Y],
														rows_night_monthly[j+row].day[NEE_75_QC_Y],
														rows_night_monthly[j+row].day[NEE_84_Y],
														rows_night_monthly[j+row].day[NEE_84_QC_Y],
														rows_night_monthly[j+row].day[NEE_95_Y],
														rows_night_monthly[j+row].day[NEE_95_QC_Y]
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_night_joinUnc_y = compute_join(rows_night_monthly[j+row].night[NEE_REF_Y_RAND],rows_night_monthly[j+row].night[NEE_16_Y],rows_night_monthly[j+row].night[NEE_84_Y]);
						nee_ref_day_joinUnc_y = compute_join(rows_night_monthly[j+row].day[NEE_REF_Y_RAND],rows_night_monthly[j+row].day[NEE_16_Y],rows_night_monthly[j+row].day[NEE_84_Y]);
						nee_ust50_night_joinUnc_y = compute_join(rows_night_monthly[j+row].night[NEE_UST50_Y_RAND],rows_night_monthly[j+row].night[NEE_16_Y],rows_night_monthly[j+row].night[NEE_84_Y]);
						nee_ust50_day_joinUnc_y = compute_join(rows_night_monthly[j+row].day[NEE_UST50_Y_RAND],rows_night_monthly[j+row].day[NEE_16_Y],rows_night_monthly[j+row].day[NEE_84_Y]);
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														rows_night_monthly[j+row].night[NEE_REF_Y],
														rows_night_monthly[j+row].night_std[NEE_REF_Y],
														rows_night_monthly[j+row].night_qc[NEE_REF_Y],
														rows_night_monthly[j+row].night[NEE_REF_Y_RAND],
														nee_ref_night_joinUnc_y,
														rows_night_monthly[j+row].day[NEE_REF_Y],
														rows_night_monthly[j+row].day_std[NEE_REF_Y],
														rows_night_monthly[j+row].day_qc[NEE_REF_Y],
														rows_night_monthly[j+row].day[NEE_REF_Y_RAND],
														nee_ref_day_joinUnc_y,
														rows_night_monthly[j+row].night[NEE_UST50_Y],
														rows_night_monthly[j+row].night_std[NEE_UST50_Y],
														rows_night_monthly[j+row].night_qc[NEE_UST50_Y],
														rows_night_monthly[j+row].night[NEE_UST50_Y_RAND],
														nee_ust50_night_joinUnc_y,
														rows_night_monthly[j+row].day[NEE_UST50_Y],
														rows_night_monthly[j+row].day_std[NEE_UST50_Y],
														rows_night_monthly[j+row].day_qc[NEE_UST50_Y],
														rows_night_monthly[j+row].day[NEE_UST50_Y_RAND],
														nee_ust50_day_joinUnc_y,
														rows_night_monthly[j+row].night[NEE_05_Y],
														rows_night_monthly[j+row].night[NEE_05_QC_Y],
														rows_night_monthly[j+row].night[NEE_16_Y],
														rows_night_monthly[j+row].night[NEE_16_QC_Y],
														rows_night_monthly[j+row].night[NEE_25_Y],
														rows_night_monthly[j+row].night[NEE_25_QC_Y],
														rows_night_monthly[j+row].night[NEE_50_Y],
														rows_night_monthly[j+row].night[NEE_50_QC_Y],
														rows_night_monthly[j+row].night[NEE_75_Y],
														rows_night_monthly[j+row].night[NEE_75_QC_Y],
														rows_night_monthly[j+row].night[NEE_84_Y],
														rows_night_monthly[j+row].night[NEE_84_QC_Y],
														rows_night_monthly[j+row].night[NEE_95_Y],
														rows_night_monthly[j+row].night[NEE_95_QC_Y],
														rows_night_monthly[j+row].day[NEE_05_Y],
														rows_night_monthly[j+row].day[NEE_05_QC_Y],
														rows_night_monthly[j+row].day[NEE_16_Y],
														rows_night_monthly[j+row].day[NEE_16_QC_Y],
														rows_night_monthly[j+row].day[NEE_25_Y],
														rows_night_monthly[j+row].day[NEE_25_QC_Y],
														rows_night_monthly[j+row].day[NEE_50_Y],
														rows_night_monthly[j+row].day[NEE_50_QC_Y],
														rows_night_monthly[j+row].day[NEE_75_Y],
														rows_night_monthly[j+row].day[NEE_75_QC_Y],
														rows_night_monthly[j+row].day[NEE_84_Y],
														rows_night_monthly[j+row].day[NEE_84_QC_Y],
														rows_night_monthly[j+row].day[NEE_95_Y],
														rows_night_monthly[j+row].day[NEE_95_QC_Y]
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
						);
					}
				}

				if ( datasets[dataset].years_count >= 3 ) {
					if ( no_rand_unc ) {
						if ( exists ) {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														rows_night_monthly[j+row].night[NEE_REF_C],
														rows_night_monthly[j+row].night_std[NEE_REF_C],
														rows_night_monthly[j+row].night_qc[NEE_REF_C],
														rows_night_monthly[j+row].day[NEE_REF_C],
														rows_night_monthly[j+row].day_std[NEE_REF_C],
														rows_night_monthly[j+row].day_qc[NEE_REF_C],
														rows_night_monthly[j+row].night[NEE_UST50_C],
														rows_night_monthly[j+row].night_std[NEE_UST50_C],
														rows_night_monthly[j+row].night_qc[NEE_UST50_C],
														rows_night_monthly[j+row].day[NEE_UST50_C],
														rows_night_monthly[j+row].day_std[NEE_UST50_C],
														rows_night_monthly[j+row].day_qc[NEE_UST50_C],
														rows_night_monthly[j+row].night[NEE_05_C],
														rows_night_monthly[j+row].night[NEE_05_QC_C],
														rows_night_monthly[j+row].night[NEE_16_C],
														rows_night_monthly[j+row].night[NEE_16_QC_C],
														rows_night_monthly[j+row].night[NEE_25_C],
														rows_night_monthly[j+row].night[NEE_25_QC_C],
														rows_night_monthly[j+row].night[NEE_50_C],
														rows_night_monthly[j+row].night[NEE_50_QC_C],
														rows_night_monthly[j+row].night[NEE_75_C],
														rows_night_monthly[j+row].night[NEE_75_QC_C],
														rows_night_monthly[j+row].night[NEE_84_C],
														rows_night_monthly[j+row].night[NEE_84_QC_C],
														rows_night_monthly[j+row].night[NEE_95_C],
														rows_night_monthly[j+row].night[NEE_95_QC_C],
														rows_night_monthly[j+row].day[NEE_05_C],
														rows_night_monthly[j+row].day[NEE_05_QC_C],
														rows_night_monthly[j+row].day[NEE_16_C],
														rows_night_monthly[j+row].day[NEE_16_QC_C],
														rows_night_monthly[j+row].day[NEE_25_C],
														rows_night_monthly[j+row].day[NEE_25_QC_C],
														rows_night_monthly[j+row].day[NEE_50_C],
														rows_night_monthly[j+row].day[NEE_50_QC_C],
														rows_night_monthly[j+row].day[NEE_75_C],
														rows_night_monthly[j+row].day[NEE_75_QC_C],
														rows_night_monthly[j+row].day[NEE_84_C],
														rows_night_monthly[j+row].day[NEE_84_QC_C],
														rows_night_monthly[j+row].day[NEE_95_C],
														rows_night_monthly[j+row].day[NEE_95_QC_C]
							);
						} else {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
							);
						}
					} else {
						if ( exists ) {
							nee_ref_night_joinUnc_c = compute_join(rows_night_monthly[j+row].night[NEE_REF_C_RAND],rows_night_monthly[j+row].night[NEE_16_C],rows_night_monthly[j+row].night[NEE_84_C]);
							nee_ref_day_joinUnc_c = compute_join(rows_night_monthly[j+row].day[NEE_REF_C_RAND],rows_night_monthly[j+row].day[NEE_16_C],rows_night_monthly[j+row].day[NEE_84_C]);
							nee_ust50_night_joinUnc_c = compute_join(rows_night_monthly[j+row].night[NEE_UST50_C_RAND],rows_night_monthly[j+row].night[NEE_16_C],rows_night_monthly[j+row].night[NEE_84_C]);
							nee_ust50_day_joinUnc_c = compute_join(rows_night_monthly[j+row].day[NEE_UST50_C_RAND],rows_night_monthly[j+row].day[NEE_16_C],rows_night_monthly[j+row].day[NEE_84_C]);
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														rows_night_monthly[j+row].night[NEE_REF_C],
														rows_night_monthly[j+row].night_std[NEE_REF_C],
														rows_night_monthly[j+row].night_qc[NEE_REF_C],
														rows_night_monthly[j+row].night[NEE_REF_C_RAND],
														nee_ref_night_joinUnc_c,
														rows_night_monthly[j+row].day[NEE_REF_C],
														rows_night_monthly[j+row].day_std[NEE_REF_C],
														rows_night_monthly[j+row].day_qc[NEE_REF_C],
														rows_night_monthly[j+row].day[NEE_REF_C_RAND],
														nee_ref_day_joinUnc_c,
														rows_night_monthly[j+row].night[NEE_UST50_C],
														rows_night_monthly[j+row].night_std[NEE_UST50_C],
														rows_night_monthly[j+row].night_qc[NEE_UST50_C],
														rows_night_monthly[j+row].night[NEE_UST50_C_RAND],
														nee_ust50_night_joinUnc_c,
														rows_night_monthly[j+row].day[NEE_UST50_C],
														rows_night_monthly[j+row].day_std[NEE_UST50_C],
														rows_night_monthly[j+row].day_qc[NEE_UST50_C],
														rows_night_monthly[j+row].day[NEE_UST50_C_RAND],
														nee_ust50_day_joinUnc_c,
														rows_night_monthly[j+row].night[NEE_05_C],
														rows_night_monthly[j+row].night[NEE_05_QC_C],
														rows_night_monthly[j+row].night[NEE_16_C],
														rows_night_monthly[j+row].night[NEE_16_QC_C],
														rows_night_monthly[j+row].night[NEE_25_C],
														rows_night_monthly[j+row].night[NEE_25_QC_C],
														rows_night_monthly[j+row].night[NEE_50_C],
														rows_night_monthly[j+row].night[NEE_50_QC_C],
														rows_night_monthly[j+row].night[NEE_75_C],
														rows_night_monthly[j+row].night[NEE_75_QC_C],
														rows_night_monthly[j+row].night[NEE_84_C],
														rows_night_monthly[j+row].night[NEE_84_QC_C],
														rows_night_monthly[j+row].night[NEE_95_C],
														rows_night_monthly[j+row].night[NEE_95_QC_C],
														rows_night_monthly[j+row].day[NEE_05_C],
														rows_night_monthly[j+row].day[NEE_05_QC_C],
														rows_night_monthly[j+row].day[NEE_16_C],
														rows_night_monthly[j+row].day[NEE_16_QC_C],
														rows_night_monthly[j+row].day[NEE_25_C],
														rows_night_monthly[j+row].day[NEE_25_QC_C],
														rows_night_monthly[j+row].day[NEE_50_C],
														rows_night_monthly[j+row].day[NEE_50_QC_C],
														rows_night_monthly[j+row].day[NEE_75_C],
														rows_night_monthly[j+row].day[NEE_75_QC_C],
														rows_night_monthly[j+row].day[NEE_84_C],
														rows_night_monthly[j+row].day[NEE_84_QC_C],
														rows_night_monthly[j+row].day[NEE_95_C],
														rows_night_monthly[j+row].day[NEE_95_QC_C]
							);
						} else {
							fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE,
														(PREC)INVALID_VALUE
							);
						}
					}
				} else {
					fputs("\n", f);
				}
			}
			j += 12;
		}

		/* close file */
		fclose(f);

		/* free memory */
		free(rows_night_monthly);
		free(p_matrix_y);
		free(nee_matrix_y_monthly);
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
			free(nee_matrix_c_monthly);
		}
		
		/* save info mm */
		if ( ! save_info(&datasets[dataset], output_files_path, MM_TR, ref_y, ref_c, percentiles_y, percentiles_c) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c);
			}
			continue;
		}
		puts("ok");

		/*
		* 
		* yearly
		*
		*/

		printf("computing yy...");

		nee_matrix_y_yearly = malloc(datasets[dataset].years_count*sizeof*nee_matrix_y_yearly);
		if ( !nee_matrix_y_yearly ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_daily);
				free(nee_matrix_c);
			}
			continue;
		}

		if ( datasets[dataset].years_count >= 3 ) {
			nee_matrix_c_yearly = malloc(datasets[dataset].years_count*sizeof*nee_matrix_c_yearly);
			if ( !nee_matrix_c_yearly ) {
				puts(err_out_of_memory);
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_daily);
				free(nee_matrix_y_yearly);
				free(percentiles_y);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				continue;
			}
		}

		rows_night_yearly = malloc(datasets[dataset].years_count*sizeof*rows_night_yearly);
		if ( !rows_night_yearly ) {
			puts(err_out_of_memory);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(nee_matrix_y_yearly);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_yearly);
				free(nee_matrix_c_daily);
				free(nee_matrix_c);
			}
			continue;
		}

		/* compute yy */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			y = IS_LEAP_YEAR(year) ? 366 : 365;
			for ( percentile = 0; percentile < PERCENTILES_COUNT_2; percentile++ ) {
				nee_matrix_y_yearly[index].nee[percentile] = 0.0;
				nee_matrix_y_yearly[index].qc[percentile] = 0.0;
				if ( datasets[dataset].years_count >= 3 ) {
					nee_matrix_c_yearly[index].nee[percentile] = 0.0;
					nee_matrix_c_yearly[index].qc[percentile] = 0.0;
				}
				for ( j = 0; j < y; j++ ) {
					nee_matrix_y_yearly[index].nee[percentile] += nee_matrix_y_daily[row+j].nee[percentile];
					nee_matrix_y_yearly[index].qc[percentile] += nee_matrix_y_daily[row+j].qc[percentile];
					if ( datasets[dataset].years_count >= 3 ) {
						nee_matrix_c_yearly[index].nee[percentile] += nee_matrix_c_daily[row+j].nee[percentile];
						nee_matrix_c_yearly[index].qc[percentile] += nee_matrix_c_daily[row+j].qc[percentile];
					}
				}
				nee_matrix_y_yearly[index].qc[percentile] /= y;
				if ( datasets[dataset].years_count >= 3 ) {
					nee_matrix_c_yearly[index].qc[percentile] /= y;
				}
			}
			row += y;
			++year;
			++index;
		}

		/* saving y nee yy matrix */
		if ( percentiles_save ) {
			if ( ! save_nee_matrix(nee_matrix_y_yearly, &datasets[dataset], YY_Y) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_yearly);
				free(nee_matrix_y_yearly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c_yearly);
					free(nee_matrix_c_daily);
					free(nee_matrix_c);
				}
				continue;
			}

			/* saving c nee yy matrix */
			if ( datasets[dataset].years_count >= 3 ) {
				if ( ! save_nee_matrix(nee_matrix_c_yearly, &datasets[dataset], YY_C) ) {
					free(unc_rows_temp);
					free(unc_rows_aggr);
					free(unc_rows);
					free(rows_night_yearly);
					free(rows_night_daily);
					free(percentiles_y);
					free(nee_matrix_c_yearly);
					free(nee_matrix_y_yearly);
					free(nee_matrix_c_daily);
					free(nee_matrix_y_daily);
					free(p_matrix_y);
					continue;
				}
			}
		}

		/* get p_matrix */
		p_matrix_y = process_nee_matrix(&datasets[dataset], nee_matrix_y_yearly, datasets[dataset].years_count, &ref_y, YY_Y);
		if ( !p_matrix_y ) {
			puts("unable to get p_matrix for yearly y");
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_yearly);
			free(nee_matrix_y_yearly);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c_yearly);
				free(nee_matrix_c_daily);
				free(nee_matrix_c);
			}
			continue;
		}
		if ( datasets[dataset].years_count >= 3 ) {
			p_matrix_c = process_nee_matrix(&datasets[dataset], nee_matrix_c_yearly, datasets[dataset].years_count, &ref_c, YY_C);
			if ( !p_matrix_c ) {
				puts("unable to get p_matrix for yearly c");
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(rows_night_yearly);
				free(rows_night_daily);
				free(percentiles_y);
				free(nee_matrix_c_yearly);
				free(nee_matrix_y_yearly);
				free(nee_matrix_c_daily);
				free(nee_matrix_y_daily);
				free(p_matrix_y);
				continue;
			}
		}

		/* update ref stuff */
		update_ref(&datasets[dataset], rows_night_daily, daily_rows_count, nee_matrix_y, nee_matrix_c, ref_y, ref_c);

		/* ref changed ? */
		if ( (ref_y_old != ref_y) || (ref_c_old != ref_c) ) {
			/* revert back qcs */
			revert_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				revert_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}

			/* compute random again */
			if ( ! compute_rand_unc(&datasets[dataset], unc_rows, nee_matrix_y, nee_matrix_c, ref_y, ref_c) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
					free(nee_matrix_c_daily);
				}
				continue;
			}

			/* change qcs */
			change_qcs(nee_matrix_y, datasets[dataset].rows_count);
			if ( datasets[dataset].years_count >= 3 ) {
				change_qcs(nee_matrix_c, datasets[dataset].rows_count);
			}

			if ( ! compute_night_rand(&datasets[dataset], rows_night_daily, unc_rows) ) {
				free(unc_rows_temp);
				free(unc_rows_aggr);
				free(unc_rows);
				free(percentiles_y);
				free(nee_matrix_y);
				free(nee_matrix_y_daily);
				if ( datasets[dataset].years_count >= 3 ) {
					free(nee_matrix_c);
					free(nee_matrix_c_daily);
				}
				continue;
			}
			rand_unc_dd(unc_rows, unc_rows_aggr, datasets[dataset].rows_count, datasets[dataset].years_count, (HOURLY_TIMERES == datasets[dataset].details->timeres));
			ref_y_old = ref_y;
			ref_c_old = ref_c;
		}

		/* aggr yy night */
		index = 0;
		year = datasets[dataset].years[0].year;
		for ( row = 0; row < rows_count; ) {
			y = IS_LEAP_YEAR(year) ? 366 : 365;
			rows_night_yearly[index].night_total = 0;
			rows_night_yearly[index].day_total = 0;
			for ( j = 0; j < y; j++ ) {
				rows_night_yearly[index].night_total += rows_night_daily[row+j].night_total;
				rows_night_yearly[index].day_total += rows_night_daily[row+j].day_total;
			}
			rows_night_yearly[index].night_total /= y;
			rows_night_yearly[index].day_total /= y;
			for ( percentile = 0; percentile < NIGHT_VALUES; percentile++ ) {
				/* do not compute _c if years count is less than 3 */
				if ( (datasets[dataset].years_count < 3) &&
							((NEE_REF_C == percentile) || (NEE_UST50_C == percentile) || (NEE_REF_C_RAND == percentile) || (NEE_UST50_C_RAND == percentile) ||
							(NEE_05_C == percentile) || (NEE_05_QC_C == percentile) || (NEE_16_C == percentile) || (NEE_16_QC_C == percentile) ||
							(NEE_25_C == percentile) || (NEE_25_QC_C == percentile) || (NEE_50_C == percentile) || (NEE_50_QC_C == percentile) ||
							(NEE_75_C == percentile) || (NEE_75_QC_C == percentile) ||
							(NEE_84_C == percentile) || (NEE_84_QC_C == percentile) || (NEE_95_C == percentile) || (NEE_95_QC_C == percentile))
							) {
					continue;
				}
				nights_rand_sum = 0;
				days_rand_sum = 0;
				rows_night_yearly[index].night[percentile] = 0.0;
				rows_night_yearly[index].night_d = 0;
				if ( percentile < NIGHT_QC_VALUES ) {
					rows_night_yearly[index].night_std[percentile] = 0.0;
				}
				if ( percentile < NIGHT_RAND_VALUES ) {
					rows_night_yearly[index].night_qc[percentile] = 0.0;
				}
				rows_night_yearly[index].day[percentile] = 0.0;
				rows_night_yearly[index].day_d = 0;
				if ( percentile < NIGHT_QC_VALUES ) {
					rows_night_yearly[index].day_std[percentile] = 0.0;
				}
				if ( percentile < NIGHT_RAND_VALUES ) {
					rows_night_yearly[index].day_qc[percentile] = 0.0;
				}
				valid_values_count_night = 0;
				valid_values_count_day = 0;

				for ( j = 0; j < y; j++ ) {
					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( ! IS_INVALID_VALUE(rows_night_daily[row+j].night[percentile]) ) {
							rows_night_yearly[index].night[percentile] += rows_night_daily[row+j].night[percentile];
							++valid_values_count_night;
						}
						rows_night_yearly[index].night_d += rows_night_daily[row+j].night_d;
					} else {
						value = rows_night_daily[row+j].night[percentile];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
							value *= (rows_night_daily[row+j].night_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[row+j].night_d_rand[percentile-NIGHT_QC_VALUES]);
							rows_night_yearly[index].night[percentile] += value;
							nights_rand_sum += rows_night_daily[row+j].night_d_rand[percentile-NIGHT_QC_VALUES];
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) && ! IS_INVALID_VALUE(rows_night_daily[row+j].night_std[percentile]) ) {
						rows_night_yearly[index].night_std[percentile] += rows_night_daily[row+j].night_std[percentile];
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_yearly[index].night_qc[percentile] += rows_night_daily[row+j].night_qc[percentile];
					}
					if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
						if ( ! IS_INVALID_VALUE(rows_night_daily[row+j].day[percentile]) ) {
							rows_night_yearly[index].day[percentile] += rows_night_daily[row+j].day[percentile];
							++valid_values_count_day;
						}
						rows_night_yearly[index].day_d += rows_night_daily[row+j].day_d;
					} else {
						value = rows_night_daily[row+j].day[percentile];
						if ( !IS_INVALID_VALUE(value) ) {
							value *= value;
							value *= (rows_night_daily[row+j].day_d_rand[percentile-NIGHT_QC_VALUES] * rows_night_daily[row+j].day_d_rand[percentile-NIGHT_QC_VALUES]);
							rows_night_yearly[index].day[percentile] += value;
							days_rand_sum += rows_night_daily[row+j].day_d_rand[percentile-NIGHT_QC_VALUES];
						}
					}
					if ( (percentile < NIGHT_QC_VALUES) && ! IS_INVALID_VALUE(rows_night_daily[row+j].day_std[percentile]) ) {
						rows_night_yearly[index].day_std[percentile] += rows_night_daily[row+j].day_std[percentile];
					}
					if ( percentile < NIGHT_RAND_VALUES ) {
						rows_night_yearly[index].day_qc[percentile] += rows_night_daily[row+j].day_qc[percentile];
					}
				}
				if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
					if ( valid_values_count_night ) {
						rows_night_yearly[index].night[percentile] /= valid_values_count_night;
						rows_night_yearly[index].night_d /= valid_values_count_night;
					}
				} else {
					if ( nights_rand_sum ) {
						rows_night_yearly[index].night[percentile] = SQRT(rows_night_yearly[index].night[percentile]) / nights_rand_sum;
					} else {
						rows_night_yearly[index].night[percentile] = INVALID_VALUE;
					}
				}
				if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_night ) {
					rows_night_yearly[index].night_std[percentile] /= valid_values_count_night;
				}
				if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_night ) {
					rows_night_yearly[index].night_qc[percentile] /= valid_values_count_night;
				}
				if ( (percentile < NIGHT_QC_VALUES) || (percentile >= NIGHT_RAND_VALUES) ) {
					if ( valid_values_count_day ) {
						rows_night_yearly[index].day[percentile] /= valid_values_count_day;
						rows_night_yearly[index].day_d /= valid_values_count_day;
					}
				} else {
					if ( days_rand_sum ) {
						rows_night_yearly[index].day[percentile] = SQRT(rows_night_yearly[index].day[percentile]) / days_rand_sum;
					} else {
						rows_night_yearly[index].day[percentile] = INVALID_VALUE;
					}
				}
				if ( (percentile < NIGHT_QC_VALUES) && valid_values_count_day ) {
					rows_night_yearly[index].day_std[percentile] /= valid_values_count_day;
				}
				if ( (percentile < NIGHT_RAND_VALUES) && valid_values_count_day ) {
					rows_night_yearly[index].day_qc[percentile] /= valid_values_count_day;
				}
			}

			/* */
			row += y;
			++year;
			++index;
		}

		if ( ! update_yy(&datasets[dataset], rows_night_daily, daily_rows_count, rows_night_yearly, datasets[dataset].years_count) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_yearly);
			free(nee_matrix_y_yearly);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c_yearly);
				free(nee_matrix_c_daily);
				free(nee_matrix_c);
			}
			continue;
		}

		/* rand unc yy */
		if ( !no_rand_unc ) {
			rand_unc_yy(unc_rows_aggr, unc_rows_temp, datasets[dataset].rows_count / rows_per_day, datasets[dataset].years[0].year, datasets[dataset].years_count);
		}
		printf("ok\nsaving yy...");

		/* save output yy */
		sprintf(buffer, output_file_yy, output_files_path, datasets[dataset].details->site);
		f = fopen(buffer, "w");
		if ( !f ) {
			printf("unable to create %s\n\n", buffer);
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(rows_night_yearly);
			free(nee_matrix_y_yearly);
			free(rows_night_daily);
			free(percentiles_y);
			free(nee_matrix_y_daily);
			if ( datasets[dataset].years_count >= 3 ) {
				free(p_matrix_c);
				free(nee_matrix_c_yearly);
				free(nee_matrix_c_daily);
				free(nee_matrix_c);
			}
			continue;
		}

		/* write header yy */
		fprintf(f, header_file_yy, TIMESTAMP_STRING);
		if ( no_rand_unc ) {
			fputs(output_var_1, f);
		} else {
			fputs(output_var_1_rand_unc, f);
		}
		for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
			fprintf(f, "NEE_%02g_y,NEE_%02g_qc_y", percentiles_test_1[percentile],percentiles_test_1[percentile]);
			if ( percentile < PERCENTILES_COUNT_1-1 ) {
				fputs(",", f);
			}
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(output_var_2, f);
			} else {
				fputs(output_var_2_rand_unc, f);
			}
			for ( percentile = 0; percentile < PERCENTILES_COUNT_1; percentile++ ) {
				fprintf(f, "NEE_%02g_c,NEE_%02g_qc_c", percentiles_test_1[percentile],percentiles_test_1[percentile]);
				fputs(",", f);
			}
		} else {
			fputs(",", f);
		}
		if ( no_rand_unc ) {
			fputs(header_file_night_y_no_rand_unc, f);
		} else {
			if ( !no_rand_unc ) {
				fputs(header_file_night_year, f);
			}
			fputs(header_file_night_y, f);
		}
		if ( datasets[dataset].years_count >= 3 ) {
			if ( no_rand_unc ) {
				fputs(header_file_night_c_no_rand_unc, f);
			} else {
				fputs(header_file_night_c, f);
			}
		} else {
			fputs("\n", f);
		}

		/* write values yy */
		j = 0;
		for ( i = 0; i < datasets[dataset].years_count; i++ ) {
			exists = datasets[dataset].years[i].exist;
			fprintf(f, "%d,", datasets[dataset].years[i].year);
			if ( no_rand_unc ) {
				if ( exists ) {
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
													nee_matrix_y_yearly[i].nee[ref_y],
													nee_matrix_y_yearly[i].qc[ref_y],
													nee_matrix_y_yearly[i].nee[PERCENTILES_COUNT_2-1],
													nee_matrix_y_yearly[i].qc[PERCENTILES_COUNT_2-1],
													p_matrix_y[i].mean,
													p_matrix_y[i].mean_qc,
													p_matrix_y[i].std_err
					);
				} else {
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
					);
				}
			} else {
				if ( exists ) {
					nee_ref_joinUnc_y = compute_join(unc_rows_temp[i].rand[NEE_REF_Y_UNC], p_matrix_y[i].value[1], p_matrix_y[i].value[5]);
					nee_ust50_joinUnc_y = compute_join(unc_rows_temp[i].rand[NEE_UST50_Y_UNC], p_matrix_y[i].value[1], p_matrix_y[i].value[5]);
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
													nee_matrix_y_yearly[i].nee[ref_y],
													nee_matrix_y_yearly[i].qc[ref_y],
													unc_rows_temp[i].rand[NEE_REF_Y_UNC],
													nee_ref_joinUnc_y,
													nee_matrix_y_yearly[i].nee[PERCENTILES_COUNT_2-1],
													nee_matrix_y_yearly[i].qc[PERCENTILES_COUNT_2-1],
													unc_rows_temp[i].rand[NEE_UST50_Y_UNC],
													nee_ust50_joinUnc_y,
													p_matrix_y[i].mean,
													p_matrix_y[i].mean_qc,
													p_matrix_y[i].std_err
					);
				} else {
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
					);
				}
			}
			for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
				if ( exists ) {
					fprintf(f, "%g,%g,", p_matrix_y[i].value[z], p_matrix_y[i].qc[z]);
				} else {
					fprintf(f, "%g,%g,", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
				}
			}
			if ( datasets[dataset].years_count >= 3 ) {
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_c_yearly[i].nee[ref_c],
															nee_matrix_c_yearly[i].qc[ref_c],
															nee_matrix_c_yearly[i].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_c_yearly[i].qc[PERCENTILES_COUNT_2-1],
															p_matrix_c[i].mean,
															p_matrix_c[i].mean_qc,
															p_matrix_c[i].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_joinUnc_c = compute_join(unc_rows_temp[i].rand[NEE_REF_C_UNC], p_matrix_c[i].value[1], p_matrix_c[i].value[5]);
						nee_ust50_joinUnc_c = compute_join(unc_rows_temp[i].rand[NEE_UST50_C_UNC], p_matrix_c[i].value[1], p_matrix_c[i].value[5]);
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															nee_matrix_c_yearly[i].nee[ref_c],
															nee_matrix_c_yearly[i].qc[ref_c],
															unc_rows_temp[i].rand[NEE_REF_C_UNC],
															nee_ref_joinUnc_c,
															nee_matrix_c_yearly[i].nee[PERCENTILES_COUNT_2-1],
															nee_matrix_c_yearly[i].qc[PERCENTILES_COUNT_2-1],
															unc_rows_temp[i].rand[NEE_UST50_C_UNC],
															nee_ust50_joinUnc_c,
															p_matrix_c[i].mean,
															p_matrix_c[i].mean_qc,
															p_matrix_c[i].std_err
						);
					} else {
						fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,",
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE,
															(PREC)INVALID_VALUE
						);
					}
				}
				for ( z = 0; z < PERCENTILES_COUNT_1; z++ ) {
					if ( exists ) {
						fprintf(f, "%g,%g,", p_matrix_c[i].value[z], p_matrix_c[i].qc[z]);
					} else {
						fprintf(f, "%g,%g,", (PREC)INVALID_VALUE, (PREC)INVALID_VALUE);
					}
				}
			}

			if ( no_rand_unc ) {
				if ( exists ) {
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
													rows_night_yearly[i].night[NEE_REF_Y],
													rows_night_yearly[i].night_std[NEE_REF_Y],
													rows_night_yearly[i].night_qc[NEE_REF_Y],
													rows_night_yearly[i].day[NEE_REF_Y],
													rows_night_yearly[i].day_std[NEE_REF_Y],
													rows_night_yearly[i].day_qc[NEE_REF_Y],
													rows_night_yearly[i].night[NEE_UST50_Y],
													rows_night_yearly[i].night_std[NEE_UST50_Y],
													rows_night_yearly[i].night_qc[NEE_UST50_Y],
													rows_night_yearly[i].day[NEE_UST50_Y],
													rows_night_yearly[i].day_std[NEE_UST50_Y],
													rows_night_yearly[i].day_qc[NEE_UST50_Y],
													rows_night_yearly[i].night[NEE_05_Y],
													rows_night_yearly[i].night[NEE_05_QC_Y],
													rows_night_yearly[i].night[NEE_16_Y],
													rows_night_yearly[i].night[NEE_16_QC_Y],
													rows_night_yearly[i].night[NEE_25_Y],
													rows_night_yearly[i].night[NEE_25_QC_Y],
													rows_night_yearly[i].night[NEE_50_Y],
													rows_night_yearly[i].night[NEE_50_QC_Y],
													rows_night_yearly[i].night[NEE_75_Y],
													rows_night_yearly[i].night[NEE_75_QC_Y],
													rows_night_yearly[i].night[NEE_84_Y],
													rows_night_yearly[i].night[NEE_84_QC_Y],
													rows_night_yearly[i].night[NEE_95_Y],
													rows_night_yearly[i].night[NEE_95_QC_Y],
													rows_night_yearly[i].day[NEE_05_Y],
													rows_night_yearly[i].day[NEE_05_QC_Y],
													rows_night_yearly[i].day[NEE_16_Y],
													rows_night_yearly[i].day[NEE_16_QC_Y],
													rows_night_yearly[i].day[NEE_25_Y],
													rows_night_yearly[i].day[NEE_25_QC_Y],
													rows_night_yearly[i].day[NEE_50_Y],
													rows_night_yearly[i].day[NEE_50_QC_Y],
													rows_night_yearly[i].day[NEE_75_Y],
													rows_night_yearly[i].day[NEE_75_QC_Y],
													rows_night_yearly[i].day[NEE_84_Y],
													rows_night_yearly[i].day[NEE_84_QC_Y],
													rows_night_yearly[i].day[NEE_95_Y],
													rows_night_yearly[i].day[NEE_95_QC_Y]
					);
				} else {
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE,
												(PREC)INVALID_VALUE
					);
				}
			} else {
				if ( exists ) {
					nee_ref_night_joinUnc_y = compute_join(rows_night_yearly[i].night[NEE_REF_Y_RAND],rows_night_yearly[i].night[NEE_16_Y],rows_night_yearly[i].night[NEE_84_Y]);
					nee_ref_day_joinUnc_y = compute_join(rows_night_yearly[i].day[NEE_REF_Y_RAND],rows_night_yearly[i].day[NEE_16_Y],rows_night_yearly[i].day[NEE_84_Y]);
					nee_ust50_night_joinUnc_y = compute_join(rows_night_yearly[i].night[NEE_UST50_Y_RAND],rows_night_yearly[i].night[NEE_16_Y],rows_night_yearly[i].night[NEE_84_Y]);
					nee_ust50_day_joinUnc_y = compute_join(rows_night_yearly[i].day[NEE_UST50_Y_RAND],rows_night_yearly[i].day[NEE_16_Y],rows_night_yearly[i].day[NEE_84_Y]);
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
													rows_night_yearly[i].night_d,
													rows_night_yearly[i].day_d,
													rows_night_yearly[i].night[NEE_REF_Y],
													rows_night_yearly[i].night_std[NEE_REF_Y],
													rows_night_yearly[i].night_qc[NEE_REF_Y],
													rows_night_yearly[i].night[NEE_REF_Y_RAND],
													nee_ref_night_joinUnc_y,
													rows_night_yearly[i].day[NEE_REF_Y],
													rows_night_yearly[i].day_std[NEE_REF_Y],
													rows_night_yearly[i].day_qc[NEE_REF_Y],
													rows_night_yearly[i].day[NEE_REF_Y_RAND],
													nee_ref_day_joinUnc_y,
													rows_night_yearly[i].night[NEE_UST50_Y],
													rows_night_yearly[i].night_std[NEE_UST50_Y],
													rows_night_yearly[i].night_qc[NEE_UST50_Y],
													rows_night_yearly[i].night[NEE_UST50_Y_RAND],
													nee_ust50_night_joinUnc_y,
													rows_night_yearly[i].day[NEE_UST50_Y],
													rows_night_yearly[i].day_std[NEE_UST50_Y],
													rows_night_yearly[i].day_qc[NEE_UST50_Y],
													rows_night_yearly[i].day[NEE_UST50_Y_RAND],
													nee_ust50_day_joinUnc_y,
													rows_night_yearly[i].night[NEE_05_Y],
													rows_night_yearly[i].night[NEE_05_QC_Y],
													rows_night_yearly[i].night[NEE_16_Y],
													rows_night_yearly[i].night[NEE_16_QC_Y],
													rows_night_yearly[i].night[NEE_25_Y],
													rows_night_yearly[i].night[NEE_25_QC_Y],
													rows_night_yearly[i].night[NEE_50_Y],
													rows_night_yearly[i].night[NEE_50_QC_Y],
													rows_night_yearly[i].night[NEE_75_Y],
													rows_night_yearly[i].night[NEE_75_QC_Y],
													rows_night_yearly[i].night[NEE_84_Y],
													rows_night_yearly[i].night[NEE_84_QC_Y],
													rows_night_yearly[i].night[NEE_95_Y],
													rows_night_yearly[i].night[NEE_95_QC_Y],
													rows_night_yearly[i].day[NEE_05_Y],
													rows_night_yearly[i].day[NEE_05_QC_Y],
													rows_night_yearly[i].day[NEE_16_Y],
													rows_night_yearly[i].day[NEE_16_QC_Y],
													rows_night_yearly[i].day[NEE_25_Y],
													rows_night_yearly[i].day[NEE_25_QC_Y],
													rows_night_yearly[i].day[NEE_50_Y],
													rows_night_yearly[i].day[NEE_50_QC_Y],
													rows_night_yearly[i].day[NEE_75_Y],
													rows_night_yearly[i].day[NEE_75_QC_Y],
													rows_night_yearly[i].day[NEE_84_Y],
													rows_night_yearly[i].day[NEE_84_QC_Y],
													rows_night_yearly[i].day[NEE_95_Y],
													rows_night_yearly[i].day[NEE_95_QC_Y]
					);
				} else {
					fprintf(f, "%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
					);
				}
			}

			if ( datasets[dataset].years_count >= 3 ) {
				if ( no_rand_unc ) {
					if ( exists ) {
						fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
													rows_night_yearly[i].night[NEE_REF_C],
													rows_night_yearly[i].night_std[NEE_REF_C],
													rows_night_yearly[i].night_qc[NEE_REF_C],
													rows_night_yearly[i].day[NEE_REF_C],
													rows_night_yearly[i].day_std[NEE_REF_C],
													rows_night_yearly[i].day_qc[NEE_REF_C],
													rows_night_yearly[i].night[NEE_UST50_C],
													rows_night_yearly[i].night_std[NEE_UST50_C],
													rows_night_yearly[i].night_qc[NEE_UST50_C],
													rows_night_yearly[i].day[NEE_UST50_C],
													rows_night_yearly[i].day_std[NEE_UST50_C],
													rows_night_yearly[i].day_qc[NEE_UST50_C],
													rows_night_yearly[i].night[NEE_05_C],
													rows_night_yearly[i].night[NEE_05_QC_C],
													rows_night_yearly[i].night[NEE_16_C],
													rows_night_yearly[i].night[NEE_16_QC_C],
													rows_night_yearly[i].night[NEE_25_C],
													rows_night_yearly[i].night[NEE_25_QC_C],
													rows_night_yearly[i].night[NEE_50_C],
													rows_night_yearly[i].night[NEE_50_QC_C],
													rows_night_yearly[i].night[NEE_75_C],
													rows_night_yearly[i].night[NEE_75_QC_C],
													rows_night_yearly[i].night[NEE_84_C],
													rows_night_yearly[i].night[NEE_84_QC_C],
													rows_night_yearly[i].night[NEE_95_C],
													rows_night_yearly[i].night[NEE_95_QC_C],
													rows_night_yearly[i].day[NEE_05_C],
													rows_night_yearly[i].day[NEE_05_QC_C],
													rows_night_yearly[i].day[NEE_16_C],
													rows_night_yearly[i].day[NEE_16_QC_C],
													rows_night_yearly[i].day[NEE_25_C],
													rows_night_yearly[i].day[NEE_25_QC_C],
													rows_night_yearly[i].day[NEE_50_C],
													rows_night_yearly[i].day[NEE_50_QC_C],
													rows_night_yearly[i].day[NEE_75_C],
													rows_night_yearly[i].day[NEE_75_QC_C],
													rows_night_yearly[i].day[NEE_84_C],
													rows_night_yearly[i].day[NEE_84_QC_C],
													rows_night_yearly[i].day[NEE_95_C],
													rows_night_yearly[i].day[NEE_95_QC_C]
						);
					} else {
						fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
						);
					}
				} else {
					if ( exists ) {
						nee_ref_night_joinUnc_c = compute_join(rows_night_yearly[i].night[NEE_REF_C_RAND],rows_night_yearly[i].night[NEE_16_C],rows_night_yearly[i].night[NEE_84_C]);
						nee_ref_day_joinUnc_c = compute_join(rows_night_yearly[i].day[NEE_REF_C_RAND],rows_night_yearly[i].day[NEE_16_C],rows_night_yearly[i].day[NEE_84_C]);
						nee_ust50_night_joinUnc_c = compute_join(rows_night_yearly[i].night[NEE_UST50_C_RAND],rows_night_yearly[i].night[NEE_16_C],rows_night_yearly[i].night[NEE_84_C]);
						nee_ust50_day_joinUnc_c = compute_join(rows_night_yearly[i].day[NEE_UST50_C_RAND],rows_night_yearly[i].day[NEE_16_C],rows_night_yearly[i].day[NEE_84_C]);
						fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
													rows_night_yearly[i].night[NEE_REF_C],
													rows_night_yearly[i].night_std[NEE_REF_C],
													rows_night_yearly[i].night_qc[NEE_REF_C],
													rows_night_yearly[i].night[NEE_REF_C_RAND],
													nee_ref_night_joinUnc_c,
													rows_night_yearly[i].day[NEE_REF_C],
													rows_night_yearly[i].day_std[NEE_REF_C],
													rows_night_yearly[i].day_qc[NEE_REF_C],
													rows_night_yearly[i].day[NEE_REF_C_RAND],
													nee_ref_day_joinUnc_c,
													rows_night_yearly[i].night[NEE_UST50_C],
													rows_night_yearly[i].night_std[NEE_UST50_C],
													rows_night_yearly[i].night_qc[NEE_UST50_C],
													rows_night_yearly[i].night[NEE_UST50_C_RAND],
													nee_ust50_night_joinUnc_c,
													rows_night_yearly[i].day[NEE_UST50_C],
													rows_night_yearly[i].day_std[NEE_UST50_C],
													rows_night_yearly[i].day_qc[NEE_UST50_C],
													rows_night_yearly[i].day[NEE_UST50_C_RAND],
													nee_ust50_day_joinUnc_c,
													rows_night_yearly[i].night[NEE_05_C],
													rows_night_yearly[i].night[NEE_05_QC_C],
													rows_night_yearly[i].night[NEE_16_C],
													rows_night_yearly[i].night[NEE_16_QC_C],
													rows_night_yearly[i].night[NEE_25_C],
													rows_night_yearly[i].night[NEE_25_QC_C],
													rows_night_yearly[i].night[NEE_50_C],
													rows_night_yearly[i].night[NEE_50_QC_C],
													rows_night_yearly[i].night[NEE_75_C],
													rows_night_yearly[i].night[NEE_75_QC_C],
													rows_night_yearly[i].night[NEE_84_C],
													rows_night_yearly[i].night[NEE_84_QC_C],
													rows_night_yearly[i].night[NEE_95_C],
													rows_night_yearly[i].night[NEE_95_QC_C],
													rows_night_yearly[i].day[NEE_05_C],
													rows_night_yearly[i].day[NEE_05_QC_C],
													rows_night_yearly[i].day[NEE_16_C],
													rows_night_yearly[i].day[NEE_16_QC_C],
													rows_night_yearly[i].day[NEE_25_C],
													rows_night_yearly[i].day[NEE_25_QC_C],
													rows_night_yearly[i].day[NEE_50_C],
													rows_night_yearly[i].day[NEE_50_QC_C],
													rows_night_yearly[i].day[NEE_75_C],
													rows_night_yearly[i].day[NEE_75_QC_C],
													rows_night_yearly[i].day[NEE_84_C],
													rows_night_yearly[i].day[NEE_84_QC_C],
													rows_night_yearly[i].day[NEE_95_C],
													rows_night_yearly[i].day[NEE_95_QC_C]
						);
					} else {
						fprintf(f, ",%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g,%g\n",
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE,
													(PREC)INVALID_VALUE
						);
					}
				}
			} else {
				fputs("\n", f);
			}
		}
		
		/* close file */
		fclose(f);

		/* free memory */
		free(rows_night_yearly);
		free(p_matrix_y);
		free(nee_matrix_y_yearly);
		if ( datasets[dataset].years_count >= 3 ) {
			free(p_matrix_c);
			free(nee_matrix_c_yearly);
		}
		
		/* save info yy */
		if ( ! save_info(&datasets[dataset], output_files_path, YY_TR, ref_y, ref_c, percentiles_y, percentiles_c) ) {
			free(unc_rows_temp);
			free(unc_rows_aggr);
			free(unc_rows);
			free(percentiles_y);
			free(p_matrix_y);
			free(nee_matrix_y);
			if ( datasets[dataset].years_count >= 3 ) {
				free(nee_matrix_c);
			}
			continue;
		}
		puts("ok\n");

		/* free memory */
		free(unc_rows_temp);
		free(unc_rows_aggr);
		free(unc_rows);
		free(rows_night_daily);
		free(percentiles_y);
		free(nee_matrix_y_daily);
		free(nee_matrix_y);
		if ( datasets[dataset].years_count >= 3 ) {
			free(nee_matrix_c_daily);
			free(nee_matrix_c);
		}

		clear_dataset(&datasets[dataset]);
	}

	/* free memory */
	free(percentiles_c);

	/* ok */
	return 1;
}

/* */
DATASET *get_datasets(const char *const path, int *const datasets_count) {
	int i;
	int skipped;
	int y;
	int gap;
	int error;
	int assigned;
	int file_index;
	int files_found_count;
	FILE *f;
	FILES *files_found;
	DD *details;
	YEAR *years_no_leak;
	DATASET *datasets;
	DATASET *datasets_no_leak;
	
	/* check parameters */
	assert(path && datasets_count);

	/* reset */
	datasets = NULL;
	*datasets_count = 0;

	/* scan path */
	files_found = get_files(path, "*.csv", &files_found_count, &error);
	if ( error || !files_found_count ) {
		puts("no files found!");
		return NULL;
	}

	/* loop on each files found */
	skipped = 0;
	for ( file_index = 0; file_index < files_found_count; file_index++ ) {
		/* check filename */
		if ( !is_valid_filename(files_found[file_index].list[0].name) ) {
			++skipped;
			continue;
		}

		/* open file */
		f = fopen(files_found[file_index].list[0].fullpath, "r");
		if ( !f ) {
			printf("unable to open %s\n", files_found[file_index].list[0].fullpath);
			continue;
		}

		/* get details */
		details = parse_dd(f);
		if ( !details ) {
			free_files(files_found, files_found_count);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}

		/* close file */
		fclose(f);

		/* check if site is already assigned */
		assigned = 0;
		for ( i = 0; i < *datasets_count; i++ ) {
			if ( ! string_compare_i(datasets[i].details->site, details->site) ) {
				assigned = 1;
				break;
			}
		}

		/* not assigned ? add site! */
		if ( !assigned ) {
			datasets_no_leak = realloc(datasets, ++*datasets_count*sizeof*datasets_no_leak);
			if ( !datasets_no_leak ) {
				puts(err_out_of_memory);
				free_datasets(datasets, *datasets_count);
				return NULL;

			}
			/* */
			datasets = datasets_no_leak;
			datasets[*datasets_count-1].rows = NULL;
			datasets[*datasets_count-1].gf_rows = NULL;
			datasets[*datasets_count-1].rows_count = 0;
			datasets[*datasets_count-1].years = NULL;
			datasets[*datasets_count-1].years_count = 0;
			datasets[*datasets_count-1].details = details;
			datasets[*datasets_count-1].umna = NULL;
			datasets[*datasets_count-1].umna_count = 0;

			/* check timeres */
			if ( datasets[*datasets_count-1].years_count > 1 ) {
				if ( datasets[*datasets_count-1].details->timeres != details->timeres ) {
					puts("different time resolution between years!");
					free_files(files_found, files_found_count);
					free_datasets(datasets, *datasets_count);
					return NULL;
				}
			}
			
			/* do the trick ;) */
			i = *datasets_count-1;
		}

		/* check if year is already assigned and if timeres is different */
		for ( y = 0; y < datasets[i].years_count; y++ ) {
			if ( details->year == datasets[i].years[y].year ) {
				puts(err_out_of_memory);
				free_files(files_found, files_found_count);
				free_datasets(datasets, *datasets_count);
				return NULL;
			}
		}

		/* add year */
		years_no_leak = realloc(datasets[i].years, ++datasets[i].years_count*sizeof*years_no_leak);
		if ( !years_no_leak ) {
			puts(err_out_of_memory);
			free_datasets(datasets, *datasets_count);
			return NULL;
		}

		/* assign year and compute rows count */
		datasets[i].years = years_no_leak;
		datasets[i].years[datasets[i].years_count-1].year = details->year;
		datasets[i].years[datasets[i].years_count-1].exist = 1;
		datasets[i].rows_count += ((IS_LEAP_YEAR(details->year) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (HOURLY_TIMERES == datasets[i].details->timeres  ? 2 : 1));

		/* free memory */
		if ( assigned ) {
			free_dd(details);
		}
	}

	/* free memory */
	free_files(files_found, files_found_count);
	files_found_count -= skipped;

	/* check imported files */
	if ( ! files_found_count ) {
		printf("no files found!");
		if ( skipped ) 
			printf(" (%d file%s skipped)", skipped, (skipped > 1) ? "s" : "");
		puts("");
		return NULL;
	}

	/* sort per year */
	for ( i = 0 ; i < *datasets_count; i++ ) {
		while ( 1 ) {
			qsort(datasets[i].years,  datasets[i].years_count, sizeof*datasets[i].years, compare_int);
			/* check for gap */
			gap = 0;
			for ( y = 0; y < datasets[i].years_count-1; y++ ) {
				if ( datasets[i].years[y+1].year - datasets[i].years[y].year > 1 ) {
					gap = 1;
					/* add year */
					years_no_leak = realloc(datasets[i].years, ++datasets[i].years_count*sizeof*years_no_leak);
					if ( !years_no_leak ) {
						puts(err_out_of_memory);
						free_datasets(datasets, *datasets_count);
						return NULL;
					}

					datasets[i].years = years_no_leak;
					datasets[i].years[datasets[i].years_count-1].year = datasets[i].years[y].year + 1;
					datasets[i].years[datasets[i].years_count-1].exist = 0;
					datasets[i].rows_count += ((IS_LEAP_YEAR(datasets[i].years[y].year + 1) ? LEAP_YEAR_ROWS : YEAR_ROWS) / (HOURLY_TIMERES == datasets[i].details->timeres  ? 2 : 1));
					break;
				}
			}

			if ( !gap ) {
				break;
			}
		}
	}

	/* ok */
	return datasets;
}
