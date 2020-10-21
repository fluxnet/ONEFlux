/*
	common.h

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef COMMON_H
#define COMMON_H

/* c++ handling */
#ifdef __cplusplus
	extern "C" {
#endif

/* includes */
#include <math.h>

/* defines stolen to http://www.gnu.org/software/libtool/manual/autoconf/Function-Portability.html */
#ifndef isnan
	# define isnan(x) \
	  (sizeof (x) == sizeof (long double) ? isnan_ld (x) \
	   : sizeof (x) == sizeof (double) ? isnan_d (x) \
	   : isnan_f (x))
#endif

#ifndef isinf
	# define isinf(x) \
	  (sizeof (x) == sizeof (long double) ? isinf_ld (x) \
	   : sizeof (x) == sizeof (double) ? isinf_d (x) \
	   : isinf_f (x))
#endif

/* defines */
#define IS_LEAP_YEAR(x)					(((x) % 4 == 0 && (x) % 100 != 0) || (x) % 400 == 0)
#define SIZEOF_ARRAY(a)					sizeof((a))/sizeof((a)[0])
#define IS_INVALID_VALUE(value)			((INVALID_VALUE==(int)(value)))
#define IS_MISSING_VALUE(value)			((MISSING_VALUE==(int)(value)))
#define IS_VALID_VALUE(value)			(((value)==(value))&&(!isinf((value))))
#define ARE_FLOATS_EQUAL(a,b)			(((a)==(b)))										/* TODO : CHECK IT */
#define IS_FLAG_SET(v, m)				(((v) & (m)) == (m))
#ifndef MAX
#define MAX(a, b)						(((a) > (b)) ? (a) : (b))
#endif
#define ABS(a)							(((a) < 0) ? -(a) : (a))
#define SQUARE(x)						((x)*(x))
#define VARTOSTRING(x)					(#x)
#define PRINT_TOKEN(token)				printf(#token " is %d", token)
#define PRINT_VAR(var)					printf("%s=%d\n",#var,var);
#if defined (_WIN32)
#define FOLDER_DELIMITER '\\'
#else
#define FOLDER_DELIMITER '/'
#endif
#define PREC		double
#define STRTOD		strtod
#define SQRT		sqrt
#define FABS		fabs
/* we add 0.5 so if x is > 0.5 we truncate to next integer */
#define ROUND(x)	((x)>=0?(long)((x)+0.5):(long)((x)-0.5))
#define CEIL		ceil
#ifndef M_PI
#define M_PI	3.141592653589793238462643
#endif

#define BIT_SET(a,b) ((a) |= (1<<(b)))
#define BIT_CLEAR(a,b) ((a) &= ~(1<<(b)))
#define BIT_FLIP(a,b) ((a) ^= (1<<(b)))
#define BIT_CHECK(a,b) ((a) & (1<<(b)))

#define BITMASK_SET(x,y) ((x) |= (y))
#define BITMASK_CLEAR(x,y) ((x) &= (~(y)))
#define BITMASK_FLIP(x,y) ((x) ^= (y))
#define BITMASK_CHECK(x,y) ((x) & (y))

/*
	Converting factor from umolCO2 m-2 s-1 to gC m-2 d-1
	1,000,000 = (from umol to mol)
	12.01 = MW C
	1.03772448 = ((3600s * 24h) / 1,000,000 ) * 12.01
*/
#define CO2TOC	1.03772448

/*
	phi^-1(0.75)=0.674 is the upper quartile of a standard normal distribution,
	and 2*0.674=1.349 is the distance between the two quartiles, also called the interquartile range (IQR).
	Therefore, IQR is an estimator of the standard deviation of a normal distribution. 
*/

#define IQR	1.349

/* enums */
enum {
	JANUARY = 0,
	FEBRUARY,
	MARCH,
	APRIL,
	MAY,
	JUNE,
	JULY,
	AUGUST,
	SEPTEMBER,
	OCTOBER,
	NOVEMBER,
	DECEMBER,

	MONTHS
};

/* gf */
enum {
	GF_TOFILL_VALID		= 1,
	GF_VALUE1_VALID		= 2,	/* was GF_SWIN_VALID */
	GF_VALUE2_VALID		= 4,	/* was GF_TA_VALID */
	GF_VALUE3_VALID		= 8,	/* was GF_VPD_VALID */
	GF_ALL_VALID		= GF_TOFILL_VALID|GF_VALUE1_VALID|GF_VALUE2_VALID|GF_VALUE3_VALID
};

/* gf */
enum {
	GF_ALL_METHOD = 0,
	GF_VALUE1_METHOD,
	GF_TOFILL_METHOD,

	GF_METHODS
};

/* enumeration for details */
enum {
	SITE_DETAIL = 0,
	YEAR_DETAIL,
	LAT_DETAIL,
	LON_DETAIL,
	TIMEZONE_DETAIL,
	HTOWER_DETAIL,
	TIMERES_DETAIL,
	SC_NEGL_DETAIL,
	NOTES_DETAIL,

	DETAILS_SIZE,
};

/* enumeration for time resolution */
enum {
	SPOT_TIMERES = 0,
	QUATERHOURLY_TIMERES,
	HALFHOURLY_TIMERES,
	HOURLY_TIMERES,
	DAILY_TIMERES,
	MONTHLY_TIMERES,

	TIMERES_SIZE
};

/* constants */
#define INVALID_VALUE		-9999
#define MISSING_VALUE		-6999
#define LEAP_YEAR_ROWS		17568
#define YEAR_ROWS			17520
#define BUFFER_SIZE			1024
#define HUGE_BUFFER_SIZE	1024000
#define PATH_SIZE			1024			/* TODO : CHECK IT */
#define FILENAME_SIZE		256				/* TODO : CHECK IT */
#define TOKEN_OPEN			'{'				/* for INFO */
#define TOKEN_CLOSE			'}'				/* for INFO */
#define SITE_LEN			7				/* including null-terminating char */
#define YEAR_LEN			5				/* including null-terminating char */

/* constants for gapfilling */
#define GF_SW_IN_TOLERANCE_MIN			20.0
#define GF_SW_IN_TOLERANCE_MAX			50.0
#define GF_TA_TOLERANCE					2.5
#define GF_VPD_TOLERANCE				5.0
#define GF_TOKEN_LENGTH_MAX				32
#define GF_ROWS_MIN_MIN					0
#define GF_ROWS_MIN						0
#define GF_ROWS_MIN_MAX					10000

/* */
#define TIMESTAMP_STRING		"TIMESTAMP"
#define TIMESTAMP_START_STRING	TIMESTAMP_STRING"_START"
#define TIMESTAMP_END_STRING	TIMESTAMP_STRING"_END"
#define TIMESTAMP_HEADER		TIMESTAMP_START_STRING","TIMESTAMP_END_STRING

/* structures */
typedef struct {
	char name[FILENAME_SIZE+1];
	char path[PATH_SIZE+1];
	char fullpath[PATH_SIZE+1];
} LIST;

/* */
typedef struct {
	LIST *list;
	int count;
} FILES;

/* */
typedef struct {
	char *name;
	int (*f)(char *, char *, void *);
	void *p;
} ARGUMENT;

/* */
typedef struct {
	char *name;
	char *text;
} PART;

/* */
typedef struct {
	char *text;
	int size;
	PART *parts;
	int parts_count;
} INFO;

/* */
typedef struct {
	int YYYY;
	int MM;
	int DD;
	int hh;
	int mm;
	int ss;
} TIMESTAMP;

/* structure for gapfilling */
typedef struct {
	char mask;
	PREC similiar;
	PREC stddev;
	PREC filled;
	int quality;
	int time_window;
	int samples_count;
	int method;
} GF_ROW;

/* structure for timezone */
typedef struct {
	TIMESTAMP timestamp;
	PREC v;
} TIME_ZONE;

/* structure for height */
typedef struct {
	TIMESTAMP timestamp;
	PREC h;
} HEIGHT;

/* structure for sc_negl */
typedef struct {
	TIMESTAMP timestamp;
	int flag;
} SC_NEGL;

/* structure for dataset details */
typedef struct {
	char site[SITE_LEN];
	int year;
	double lat;
	double lon;
	HEIGHT *htower;
	int htower_count;
	TIME_ZONE *time_zones;
	int time_zones_count;
	int timeres;
	SC_NEGL *sc_negles;
	int sc_negles_count;
	char **notes;
	int notes_count;
} DD;

/* extern */
extern const char err_out_of_memory[];

/* prototypes stolen to http://www.gnu.org/software/libtool/manual/autoconf/Function-Portability.html */
int isnan_f  (float       x);
int isnan_d  (double      x);
int isnan_ld (long double x);
int isinf_f  (float       x);
int isinf_d  (double      x);
int isinf_ld (long double x);

/* prototypes */
PREC convert_string_to_prec(const char *const string, int *const error);
int convert_string_to_int(const char *const string, int *const error);
PREC get_standard_deviation(const PREC *const values, const int count);
PREC get_median(const PREC *const values, const int count, int *const error);
PREC get_mean(const PREC *const values, const int count);
FILES *get_files(const char *const program_path, char *string, int *const count, int *const error);
FILES *get_files_again(const char *const program_path, char *string, FILES **files, int *const count, int *const error);
void free_files(FILES *files, const int count);
void init_random_seed(void);
int get_random_number(int max);
int parse_arguments(int argc, char *argv[], const ARGUMENT *const args, const int arg_count);
int string_compare_i(const char *str1, const char *str2);
int string_n_compare_i(const char *str1, const char *str2, const int len);
char *string_copy(const char *const string);
char *string_tokenizer(char *string, const char *delimiters, char **p);
char *get_current_directory(void);
int add_char_to_string(char *const string, char c, const int size);
int mystrcat(char *const string, const char *const string_to_add, const int size);
int file_exists(const char *const file);
int path_exists(const char *const path);
int compare_prec(const void * a, const void * b);
int compare_int(const void * a, const void * b);
char *tokenizer(char *string, char *delimiter, char **p);
PREC get_percentile(const PREC *values, const int n, const float percentile, int *const error);
PREC *get_percentiles(const PREC *values, const int n, const float *const percentiles, const int percentiles_count);
int create_dir(char *Path);
INFO *info_import(const char *const filename);
INFO *info_get(const char *const string);
char *info_get_part_name(const INFO *const info, const int index);
char *info_get_part_by_name(const INFO *const info, const char *const name);
char *info_get_part_by_number(const INFO *const info, const int index);
void info_free(INFO *info);

TIMESTAMP *get_timestamp(const char *const string);
int get_row_by_timestamp(const TIMESTAMP *const t, const int hourly_dataset);
int get_year_from_timestamp_string(const char *const string);
char *get_filename_ext(const char *const filename);

/* */
#define timestamp_start_by_row(r,y,h) timestamp_get_by_row((r),(y),(h),1)
#define timestamp_end_by_row(r,y,h) timestamp_get_by_row((r),(y),(h),0)
TIMESTAMP *timestamp_get_by_row(int row, int yy, const int hourly_dataset, const int start);
#define timestamp_start_by_row_s(r,y,h) timestamp_get_by_row_s((r),(y),(h),1)
#define timestamp_end_by_row_s(r,y,h) timestamp_get_by_row_s((r),(y),(h),0)
char *timestamp_get_by_row_s(int row, int yy, const int hourly_dataset, const int start);

#define timestamp_start_ww_by_row(r,y,h) timestamp_ww_get_by_row((r),(y),(h),1)
#define timestamp_end_ww_by_row(r,y,h) timestamp_ww_get_by_row((r),(y),(h),0)
TIMESTAMP *timestamp_ww_get_by_row(int row, int yy, const int hourly_dataset, int start);
#define timestamp_start_ww_by_row_s(r,y,h) timestamp_get_by_row_s((r),(y),(h),1)
#define timestamp_end_ww_by_row_s(r,y,h) timestamp_get_by_row_s((r),(y),(h),0)
char *timestamp_ww_get_by_row_s(int row, int yy, const int hourly_dataset, const int start);

/* gf */
GF_ROW *gf_mds(		PREC *values,
					const int struct_size,
					const int rows_count,
					const int columns_count,
					const int hourly_dataset,
					PREC value1_tolerance_min,
					PREC value1_tolerance_max,
					PREC value2_tolerance,
					PREC value3_tolerance,
					const int tofill_column,
					const int value1_column,
					const int value2_column,
					const int value3_column,
					const int values_min,
					const int compute_hat,
					int *no_gaps_filled_count
);

GF_ROW *gf_mds_with_qc(	PREC *values,
						const int struct_size,
						const int rows_count,
						const int columns_count,
						const int hourly_dataset,
						PREC value1_tolerance_min,
						PREC value1_tolerance_max,
						PREC value2_tolerance,
						PREC value3_tolerance,
						const int tofill_column,
						const int value1_column,
						const int value2_column,
						const int value3_column,
						const int value1_qc_column,
						const int value2_qc_column,
						const int value3_qc_column,
						const int qc_thrs,
						const int values_min,
						const int compute_hat,
						int *no_gaps_filled_count
);

GF_ROW *gf_mds_with_bounds(	PREC *values,
							const int struct_size,
							const int rows_count,
							const int columns_count,
							const int hourly_dataset,
							PREC value1_tolerance_min,
							PREC value1_tolerance_max,
							PREC value2_tolerance,
							PREC value3_tolerance,
							const int tofill_column,
							const int value1_column,
							const int value2_column,
							const int value3_column,
							const int value1_qc_column,
							const int value2_qc_column,
							const int value3_qc_column,
							const int qc_thrs,
							const int values_min,
							const int compute_hat,
							int start_row,
							int end_row,
							int *no_gaps_filled_count
);
PREC gf_get_similiar_standard_deviation(const GF_ROW *const gf_rows, const int rows_count);
PREC gf_get_similiar_median(const GF_ROW *const gf_rows, const int rows_count, int *const error);

/* temp functions used for G in energy_proc */
GF_ROW *temp_gf_mds(	PREC *values,
						const int struct_size,
						const int rows_count,
						const int columns_count,
						const int hourly_dataset,
						PREC value1_tolerance_min,
						PREC value1_tolerance_max,
						PREC value2_tolerance,
						PREC value3_tolerance,
						const int tofill_column,
						const int value1_column,
						const int value2_column,
						const int value3_column,
						const int value1_qc_column,
						const int value2_qc_column,
						const int value3_qc_column,
						const int qc_thrs,
						const int values_min,
						const int compute_hat,
						int *no_gaps_filled_count
);

/* dataset details */
DD *alloc_dd(void);
void zero_dd(DD *const dd);
DD *parse_dd(FILE *const f);
int write_dd(const DD *const dd, FILE *const f, const char *const notes_to_add);
int write_dds(const DD **const dd, const int count, FILE *const f, const char *const notes_to_add);
void free_dd(DD *dd);
int get_rows_count_by_dd(const DD *const dd);
int get_rows_per_day_by_dd(const DD *const dd);

/* */
char *get_datetime_in_timestamp_format(void);
char *get_timeres_in_string(int timeres);

int get_valid_line_from_file(FILE *const f, char *buffer, const int size);
int get_rows_count_from_file(FILE *const f);
/* */
PREC get_dtime_by_row(const int row, const int hourly);

/* */
PREC *get_rpot(DD *const details);
PREC *get_rpot_with_solar_noon(DD *const details, const int s_n_month, const int s_n_day, int *const solar_noon);

/* */
void check_memory_leak(void);

/* return -2 on error, -1 if not found */
int get_column_of(const char *const buffer, const char *const delimiter, const char * const string);

/* c++ handling */
#ifdef __cplusplus
}
#endif

/* */
#endif /* COMMON_H */
