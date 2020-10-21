/*
	common.c

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

/* includes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <time.h>
#include <errno.h>
#include <assert.h>
#include "common.h"

/* os dependant */
#if defined (_WIN32)
#ifndef STRICT
#define STRICT
#endif /* STRICT */
#ifndef WIN32_MEAN_AND_LEAN
#define WIN32_MEAN_AND_LEAN
#endif /* WIN32_MEAN_AND_LEAN */
#include <windows.h>
/* for memory leak */
#ifdef _DEBUG
#define _CRTDBG_MAP_ALLOC
#include <stdlib.h>
#include <crtdbg.h>
#endif /* _DEBUG */
#pragma comment(lib, "kernel32.lib")
static WIN32_FIND_DATA wfd;
static HANDLE handle;
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
#include <unistd.h>
#include <dirent.h>
#include <sys/param.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
static DIR *dir;
static struct dirent *dit;
#endif

/*
	note on August 17, 2011 removed space in delimiters 'cause path with
	spaces e.g.: c:\documents and settings .... will not be handled correctly
*/
static const char comma_delimiter[] = ",";
static const char plus_delimiter[] = "+";
static const char filter[] = "*.*";
static const char dd_field_delimiter[] = ",\r\n";
static const char *dds[DETAILS_SIZE] = { "site", "year", "lat", "lon", "timezone", "htower", "timeres", "sc_negl", "notes" };
static const char *timeress[TIMERES_SIZE] = { "spot", "quaterhourly", "halfhourly", "hourly", "daily", "monthly" };

/* error strings */
static const char err_unable_open_path[] = "unable to open path: %s\n\n";
static const char err_unable_open_file[] = "unable to open file: %s\n\n";
static const char err_path_too_big[] = "specified path \"%s\" is too big.\n\n";
static const char err_filename_too_big[] = "filename \"%s\" is too big.\n\n";
static const char err_empty_argument[] = "empty argument\n";
static const char err_unknown_argument[] = "unknown argument: \"%s\"\n\n";
static const char err_gf_too_less_values[] = "too few valid values to apply gapfilling\n";
static const char err_wildcards_with_no_extension_used[] = "wildcards with no extension used\n";

/* external strings */
const char err_out_of_memory[] = "out of memory";

/* stolen to http://www.gnu.org/software/libtool/manual/autoconf/Function-Portability.html */
int isnan_f  (float       x) { return x != x; }
int isnan_d  (double      x) { return x != x; }
int isnan_ld (long double x) { return x != x; }
int isinf_f  (float       x) { return !isnan (x) && isnan (x - x); }
int isinf_d  (double      x) { return !isnan (x) && isnan (x - x); }
int isinf_ld (long double x) { return !isnan (x) && isnan (x - x); }

/* stolen to http://www.codeproject.com/Articles/10606/Folder-Utility-Create-Path-Remove-Folder-Remove-Al */
int create_dir(char *Path) {
#if defined (_WIN32)
	char DirName[256];
	char* p = Path;
	char* q = DirName;

	while ( *p ) {
		if ( ('\\' == *p) || ('/' == *p) ) {
			if ( ':' != *(p-1) ) {
				if ( !path_exists(DirName) ) {
					if ( !CreateDirectory(DirName, NULL) ) {
						return 0;
					}
				}
			}
		}
		*q++ = *p++;
		*q = '\0';
	}
	if ( !path_exists(DirName)) {
		return CreateDirectory(DirName, NULL);
	} else {
		return 1;
	}
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
	if ( -1 == mkdir(Path,0777) ) {
		return 0;
	} else {
		return 1;
	}
#else
	return 0;
#endif
}

char *get_filename_ext(const char *const filename) {
	char *p;

	p = strrchr(filename, '.');
	if ( p ) ++p;
	return p;
}

/* */
static int scan_path(const char *const path) {
#if defined (_WIN32)
	handle = FindFirstFile(path, &wfd);
	if ( INVALID_HANDLE_VALUE == handle ) {
		return 0;
	}
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
	dir = opendir(path);
	if ( !dir ) {
		return 0;
	}
#endif
	/* ok */
	return 1;
}

/* */
static int get_files_from_path(const char *const path, FILES **files, int *const count, const int grouped) {
	int i;
	FILES *files_no_leak;
	LIST *list_no_leak;
#if defined (_WIN32)
	do {
		if ( !IS_FLAG_SET(wfd.dwFileAttributes, FILE_ATTRIBUTE_DIRECTORY) ) {
			/* check length */
			i = strlen(wfd.cFileName);
			if ( i > FILENAME_SIZE ) {
				printf(err_filename_too_big, wfd.cFileName);
				free_files(*files, *count);
				return 0;
			}

			if ( !grouped ) {
				/* alloc memory */
				files_no_leak = realloc(*files, (++*count)*sizeof*files_no_leak);
				if ( !files_no_leak ) {
					puts(err_out_of_memory);
					free_files(*files, *count-1);
					return 0;
				}

				/* assign pointer */
				*files = files_no_leak;
				(*files)[*count-1].list = NULL;
				(*files)[*count-1].count = 1;
			}

			/* allocate memory for list */
			list_no_leak = realloc((*files)[*count-1].list, (grouped ? ++(*files)[*count-1].count : 1) * sizeof*list_no_leak);
			if ( !list_no_leak ) {
				puts(err_out_of_memory);
				free_files(*files, *count);
				return 0;
			}
			(*files)[*count-1].list = list_no_leak;

			/* assign evalues */
			strncpy((*files)[*count-1].list[(*files)[*count-1].count-1].name, wfd.cFileName, i);
			(*files)[*count-1].list[(*files)[*count-1].count-1].name[i] = '\0';

			strcpy((*files)[*count-1].list[(*files)[*count-1].count-1].path, path);

			strcpy((*files)[*count-1].list[(*files)[*count-1].count-1].fullpath, path);
			if ( !mystrcat((*files)[*count-1].list[(*files)[*count-1].count-1].fullpath, wfd.cFileName, PATH_SIZE) ) {
				printf(err_filename_too_big, wfd.cFileName);
				free_files(*files, *count);
				return 0;
			}
		}
	} while ( FindNextFile(handle, &wfd) );

	/* close handle */
	FindClose(handle);
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
	for ( ; ; ) {
		dit = readdir(dir);
		if ( !dit ) {
			closedir(dir);
			return 1;
		}

		if ( dit->d_type == DT_REG ) {
			/* check length */
			i = strlen(dit->d_name);
			if ( i >= FILENAME_SIZE ) {
				printf(err_filename_too_big, dit->d_name);
				free_files(*files, *count);
				return 0;
			}

			if ( !grouped ) {
				/* alloc memory */
				files_no_leak = realloc(*files, (++*count)*sizeof*files_no_leak);
				if ( !files_no_leak ) {
					puts(err_out_of_memory);
					free_files(*files, *count-1);
					return 0;
				}

				/* assign pointer */
				*files = files_no_leak;
				(*files)[*count-1].list = NULL;
				(*files)[*count-1].count = 1;
			}

			/* allocate memory for list */
			list_no_leak = realloc((*files)[*count-1].list, (grouped ? ++(*files)[*count-1].count : 1) * sizeof*list_no_leak);
			if ( !list_no_leak ) {
				puts(err_out_of_memory);
				free_files(*files, *count);
				return 0;
			}
			(*files)[*count-1].list = list_no_leak;

			/* assign evalues */
			strncpy((*files)[*count-1].list[(*files)[*count-1].count-1].name, dit->d_name, i);
			(*files)[*count-1].list[(*files)[*count-1].count-1].name[i] = '\0';

			strcpy((*files)[*count-1].list[(*files)[*count-1].count-1].path, path);

			strcpy((*files)[*count-1].list[(*files)[*count-1].count-1].fullpath, path);
			if ( !mystrcat((*files)[*count-1].list[(*files)[*count-1].count-1].fullpath, dit->d_name, PATH_SIZE) ) {
				printf(err_filename_too_big, dit->d_name);
				free_files(*files, *count);
				return 0;
			}
		}
	}
	/* close handle */
	closedir(dir);
#endif

	/* ok */
	return 1;
}

/*
	free_files
*/
void free_files(FILES *files, const int count) {
	if ( files ) {
		int i;
		for ( i = 0 ; i < count; i++ ) {
			free(files[i].list);
		}
		free(files);
	}
}

/*
	CHECK: on ubuntu fopen erroneously open a path (maybe a bug on NTFS partition driver ?)
*/
FILES *get_files(const char *const program_path, char *string, int *const count, int *const error) {
	int i;
	int y;
	int plusses_count;
	int token_length;
	char *token_by_comma;
	char *token_by_plus;
	char *p;
	char *p2;
	char *p3;

	FILE *f;
	FILES *files;
	FILES *files_no_leak;
    LIST *list_no_leak;

	/* check parameters */
	assert(string && count && error);

	/* reset */
	files = NULL;
	*count = 0;
	*error = 0;

	/* loop for each commas */
	for ( token_by_comma = string_tokenizer(string, comma_delimiter, &p); token_by_comma; token_by_comma = string_tokenizer(NULL, comma_delimiter, &p) ) {
		/* get token length */
		for ( token_length = 0; token_by_comma[token_length]; token_length++ );

		/* if length is 0 skip to next token */
		if ( !token_length ) {
			continue;
		}

		/* scan for plusses */
		plusses_count = 0;
		for ( y = 0; y < token_length; y++ ) {
			if ( plus_delimiter[0] == token_by_comma[y] ) {
				/* check if next char is a plus too */
				if ( y < token_length-1 ) {
					if ( plus_delimiter[0] == token_by_comma[y+1] ) {
						++y;
						continue;
					}
				}

				/* plus found! */
				++plusses_count;
			}
		}

		/* no grouping */
		if ( !plusses_count ) {
			/* token is a path ? */
			if ( token_by_comma[token_length-1] == FOLDER_DELIMITER ) {
			#if defined (_WIN32)
				/* add length of filter */
				for ( i = 0; filter[i]; i++ );
				token_length += i;
			#endif

				/* add null terminating char */
				++token_length;

				/* alloc memory */
				p2 = malloc(token_length*sizeof*p2);
				if ( !p2 ) {
					puts(err_out_of_memory);
					*error = 1;
					free_files(files, *count);
					return NULL;
				}

				/* copy token */
				strcpy(p2, token_by_comma);

			#if defined (_WIN32)
				/* add filter at end */
				strcat(p2, filter);
			#endif

				/* scan path */
				if ( !scan_path(p2) ) {
					printf(err_unable_open_path, p2);
					*error = 1;
					free(p2);
					free_files(files, *count);
					return NULL;
				}

				/* get files */
				if ( !get_files_from_path(token_by_comma, &files, count, 0) ) {
					printf(err_unable_open_path, token_by_comma);
					*error = 1;
					free(p2);
					free_files(files, *count);
					return NULL;
				}

				/* free memory */
				free(p2);
			} else {
				/* check for wildcard */
				if ( '*' == token_by_comma[0] ) {
					if ( token_length < 2 ) {
						puts(err_wildcards_with_no_extension_used);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* add length of filter */
					for ( i = 0; program_path[i]; i++ );
					token_length += i;

					/* add null terminating char */
					++token_length;

					/* alloc memory */
					p2 = malloc(token_length*sizeof*p2);
					if ( !p2 ) {
						puts(err_out_of_memory);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* copy token */
					strcpy(p2, program_path);

					#if defined (_WIN32)
						/* add filter at end */
						strcat(p2, token_by_comma);
					#endif

					/* scan path */
					if ( !scan_path(p2) ) {
						printf(err_unable_open_path, p2);
						*error = 1;
						free(p2);
						free_files(files, *count);
						return NULL;
					}

					/* get files */
					if ( !get_files_from_path(program_path, &files, count, 0) ) {
						printf(err_unable_open_path, token_by_comma);
						*error = 1;
						free(p2);
						free_files(files, *count);
						return NULL;
					}

					/* free memory */
					free(p2);
				} else {
					/* check if we can simply open token_by_comma */
					f = fopen(token_by_comma, "r");
					if ( !f ) {
						printf(err_unable_open_file, token_by_comma);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* close file */
					fclose(f);

					/* allocate memory */
					files_no_leak = realloc(files, (++*count)*sizeof*files_no_leak);
					if ( !files_no_leak ) {
						puts(err_out_of_memory);
						free_files(files, *count-1);
						*error = 1;
						return NULL;
					}

					/* assign memory */
					files = files_no_leak;

					/* allocate memory for 1 file */
					files[*count-1].count = 1;
					files[*count-1].list = malloc(sizeof*files[*count-1].list);
					if ( !files[*count-1].list ) {
						puts(err_out_of_memory);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* check if token has a FOLDER_DELIMITER */
					p2 = strrchr(token_by_comma, FOLDER_DELIMITER);
					if ( p2 ) {
						/* skip FOLDER_DELIMITER */
						++p2;
						/* get length */
						y = strlen(p2);

						/* check filename length */
						if ( y > FILENAME_SIZE ) {
							printf(err_filename_too_big, p2);
							*error = 1;
							free_files(files, *count);
							return NULL;
						}

						/* assign values */
						strncpy(files[*count-1].list->name, p2, y);
						files[*count-1].list->name[y] = '\0';

						strcpy(files[*count-1].list->fullpath, token_by_comma);
						*p2 = '\0';

						strcpy(files[*count-1].list->path, token_by_comma);
					} else {
						/* assign values */
						strcpy(files[*count-1].list->name, token_by_comma);
						if ( program_path ) {
							strcpy(files[*count-1].list->path, program_path);
							strcpy(files[*count-1].list->fullpath, program_path);
							if ( !mystrcat(files[*count-1].list->fullpath, token_by_comma, PATH_SIZE) ) {
								printf(err_filename_too_big, token_by_comma);
								free_files(files, *count);
								return 0;
							}
						} else {
							strcpy(files[*count-1].list->path, token_by_comma);
							strcpy(files[*count-1].list->fullpath, token_by_comma);
						}
					}
				}
			}
		} else {
			/* alloc memory */
			files_no_leak = realloc(files, (++*count)*sizeof*files_no_leak);
			if ( !files_no_leak ) {
				puts(err_out_of_memory);
				free_files(files, *count-1);
				return 0;
			}

			/* assign pointer */
			files = files_no_leak;
			files[*count-1].list = NULL;
			files[*count-1].count = 0;

			/* loop for each plus */
			for ( token_by_plus = string_tokenizer(token_by_comma, plus_delimiter, &p2); token_by_plus; token_by_plus = string_tokenizer(NULL, plus_delimiter, &p2) ) {
				/* get token length */
				i = strlen(token_by_plus);
				/* token is a path ? */
				if ( token_by_plus[token_length-1] == FOLDER_DELIMITER ) {
					/* add length of filter */
					token_length += strlen(filter);

					/* add null terminating char */
					++token_length;

					/* alloc memory */
					p3 = malloc(i*sizeof*p3);
					if ( !p3 ) {
						puts(err_out_of_memory);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* copy token */
					strcpy(p3, token_by_plus);

					/* add filter at end */
					strcat(p3, filter);

					/* scan path */
					if ( !scan_path(p3) ) {
						printf(err_unable_open_path, p3);
						*error = 1;
						free(p3);
						free_files(files, *count);
						return NULL;
					}

					/* get files */
					if ( !get_files_from_path(token_by_plus, &files, count, 1) ) {
						printf(err_unable_open_path, token_by_plus);
						*error = 1;
						free(p3);
						free_files(files, *count);
						return NULL;
					}

					/* free memory */
					free(p3);
				} else {
					/* check if we can simply open path */
					f = fopen(token_by_plus, "r");
					if ( !f ) {
						printf(err_unable_open_file, token_by_plus);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* close file */
					fclose(f);

					/* check length */
					if ( token_length >= PATH_SIZE ) {
						printf(err_path_too_big, token_by_plus);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* allocate memory */
					++files[*count-1].count;
					list_no_leak = realloc(files[*count-1].list, files[*count-1].count*sizeof*list_no_leak);
					if ( !list_no_leak ) {
						puts(err_out_of_memory);
						*error = 1;
						free_files(files, *count);
						return NULL;
					}

					/* assign pointer */
					files[*count-1].list = list_no_leak;

					/* check if token has a FOLDER_DELIMITER */
					p3 = strrchr(token_by_comma, FOLDER_DELIMITER);
					if ( p3 ) {
						/* skip FOLDER_DELIMITER */
						++p3;

						/* get length */
						y = strlen(p3);

						/* check filename length */
						if ( y > FILENAME_SIZE ) {
							printf(err_filename_too_big, p3);
							*error = 1;
							free_files(files, *count);
							return NULL;
						}

						/* assign values */
						strncpy(files[*count-1].list[files[*count-1].count-1].name, p3, y);
						files[*count-1].list->name[y] = '\0';

						strcpy(files[*count-1].list[files[*count-1].count-1].fullpath, token_by_plus);
						*p3 = '\0';

						strcpy(files[*count-1].list[files[*count-1].count-1].path, token_by_plus);

					} else {
						/* check length */
						if ( i > FILENAME_SIZE ) {
							printf(err_filename_too_big, token_by_plus);
							*error = 1;
							free_files(files, *count);
							return NULL;
						}

						/* assign values */
						strcpy(files[*count-1].list[files[*count-1].count-1].name, token_by_plus);
						if ( program_path ) {
							strcpy(files[*count-1].list[files[*count-1].count-1].path, program_path);
							strcpy(files[*count-1].list[files[*count-1].count-1].fullpath, program_path);
							if ( !mystrcat(files[*count-1].list[files[*count-1].count-1].fullpath, token_by_plus, PATH_SIZE) ) {
								printf(err_filename_too_big, token_by_plus);
								free_files(files, *count);
								return 0;
							}
						} else {
							strcpy(files[*count-1].list[files[*count-1].count-1].path, token_by_plus);
							strcpy(files[*count-1].list[files[*count-1].count-1].fullpath, token_by_plus);
						}
					}
				}
			}
		}
	}

	/* ok */
	return files;
}

/* */
FILES *get_files_again(const char *const program_path, char *string, FILES **files, int *const count, int *const error) {
	int i;
	int temp_files_count;
	FILES *temp_files;
	FILES *files_no_leak;

	/* get files */
	temp_files = get_files(program_path, string, &temp_files_count, error);
	if ( !temp_files_count ) {
		return *files;
	}

	/* */
	files_no_leak = realloc(*files, (*count+temp_files_count)*sizeof*files_no_leak);
	if ( !files_no_leak ) {
		puts(err_out_of_memory);
		*error = 1;
		free_files(temp_files, temp_files_count);
		return *files;
	}
	*files = files_no_leak;

	/* */
	for ( i = 0; i < temp_files_count; i++ ) {
		(*files)[i+*count].count = temp_files[i].count;
		(*files)[i+*count].list = temp_files[i].list;
	}
	*count += temp_files_count;

	free(temp_files);

	/* ok */
	return *files;
}

/* */
PREC convert_string_to_prec(const char *const string, int *const error) {
	PREC value;
	char *p;

	/* reset */
	*error = 0;

	if ( !string ) {
		*error = 1;
		return 0.0;
	}

	errno = 0;

	value = (PREC)STRTOD(string, &p);
	STRTOD(p, NULL);
	if ( string == p || *p || errno ) {
		*error = 1;
	}

	return value;
}

/* */
void init_random_seed(void) {
	srand((unsigned int)time(NULL));
}

/* */
int get_random_number(int max) {
	/* taken from http://c-faq.com/lib/randrange.html */
	return (rand() / (RAND_MAX / max + 1));
}

/* */
static int check_for_argument(const char *const string , const char *const pattern, char **param) {
	char *pptr = NULL;
	char *sptr = NULL;
	char *start = NULL;

	/* reset */
	*param = NULL;

	for ( start = (char *)string; *start; start++ ) {
	    /* find start of pattern in string */
	    for ( ; (*start && (toupper(*start) != toupper(*pattern))); start++)
	          ;
	    if (start != string+1 )
	          return 0;

	    pptr = (char *)pattern;
	    sptr = (char *)start;

	    while (toupper(*sptr) == toupper(*pptr)) {
			sptr++;
			pptr++;

			/* if end of pattern then pattern was found */
			if ( !*pptr ) {
				if ( !*sptr ) {
					return 1;
				} else
				/* check for next char to be an '=' */
				if ( *sptr == '=' ) {
					if ( *(++sptr) ) {
						*param = sptr;
					}
					return 1;
				}

				return 0;
	    	}
		}
	}

	return 0;
}

/* */
int parse_arguments(int argc, char *argv[], const ARGUMENT *const args, const int arg_count) {
	int i;
	int ok;
	char *param;

	/* */
	while ( argc > 1 ) {
		/* check for arguments */
		if ( ( '-' != argv[1][0]) && ( '/' != argv[1][0]) ) {
			if ( '\0' == argv[1][0] ) {
				puts(err_empty_argument);
			} else {
				printf(err_unknown_argument, argv[1]);
			}
			return 0;
		}

		/* */
		ok = 0;
		for ( i = 0; i < arg_count; i++ ) {
			if ( check_for_argument(argv[1], args[i].name, &param) ) {
				ok = 1;

				/* check if function is present */
				assert(args[i].f);

				/* call function */
				if ( !args[i].f(args[i].name, param, args[i].p) ) {
					return 0;
				}

				break;
			}
		}

		/* */
		if ( !ok ) {
			printf(err_unknown_argument, argv[1]+1);
			return 0;
		}

		/* */
		++argv;
		--argc;
	}

	/* ok */
	return 1;
}

/* */
int string_compare_i(const char *str1, const char *str2) {
	register signed char __res;

	/* added on April 23, 2013 */
	if ( (NULL == str1) && (NULL == str2 ) ) {
		return 0;
	}
	if ( NULL == str1 ) {
		return 1;
	}
	if ( NULL == str2 ) {
		return -1;
	}

	/* */
	while ( 1 ) {
		if ( (__res = toupper( *str1 ) - toupper( *str2++ )) != 0 || !*str1++ ) {
			break;
		}
	}

	/* returns an integer greater than, equal to, or less than zero */
	return __res;
}

/* */
int string_n_compare_i(const char *str1, const char *str2, const int len) {
	int i;
	register signed char __res;

	if ( len <= 0 ) {
		return -1;
	}

	/* added on April 23, 2013 */
	if ( (NULL == str1) && (NULL == str2 ) ) {
		return 0;
	}
	if ( NULL == str1 ) {
		return 1;
	}
	if ( NULL == str2 ) {
		return -1;
	}

	/* */
	i = 0;
	while ( 1 ) {
		if ( (__res = toupper( *str1 ) - toupper( *str2++ )) != 0 || !*str1++ ) {
			break;
		}
		if ( ++i >= len ) {
			break;
		}
	}

	/* returns an integer greater than, equal to, or less than zero */
	return __res;
}

/* */
char *string_copy(const char *const string) {
	int i;
	int len;
	char *p;

	/* check for null pointer */
	if ( ! string ) {
		return NULL;
	}

	/* get length of string */
	for ( len = 0; string[len]; len++ );

	/* allocate memory */
	p = malloc(len+1);
	if ( ! p ) {
		return NULL;
	}

	/* copy ! */
	for ( i = 0; i < len; i++ ) {
		p[i] = string[i];
	}
	p[len] = '\0';

	return p;
}

/* stolen to wikipedia */
char *string_tokenizer(char *string, const char *delimiters, char **p) {
	char *sbegin;
	char *send;

	sbegin = string ? string : *p;
	sbegin += strspn(sbegin, delimiters);
	if ( *sbegin == '\0') {
		*p = "";
		return NULL;
	}

	send = sbegin + strcspn(sbegin, delimiters);
	if ( *send != '\0') {
		*send++ = '\0';
	}
	*p = send;

	return sbegin;
}

/* */
int convert_string_to_int(const char *const string, int *const error) {
	int value = 0;
	char *p = NULL;

	/* reset */
	*error = 0;

	if ( !string ) {
		*error = 1;
		return 0;
	}

	errno = 0;
	value = (int)strtod(string, &p);
	strtod(p, NULL);
	if ( string == p || *p || errno ) {
		*error = 1;
	}

	return value;
}

/* */
char *get_current_directory(void) {
	char *p;
#if defined (_WIN32)
	p = malloc((MAX_PATH+1)*sizeof *p);
	if ( !p ) {
		return NULL;
	}
	if ( !GetModuleFileName(NULL, p, MAX_PATH) ) {
		free(p);
		return NULL;
	}
	p[(strrchr(p, '\\')-p)+1] = '\0';
	return p;
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
	int len;
	p = malloc((MAXPATHLEN+1)*sizeof *p);
	if ( !p ) {
		return NULL;
	}
	if ( !getcwd(p, MAXPATHLEN) ) {
		free(p);
		return NULL;
	}
	/* check if last chars is a FOLDER_DELIMITER */
	len = strlen(p);
	if ( !len ) {
		free(p);
		return NULL;
	}
	if ( p[len-1] != FOLDER_DELIMITER ) {
		if ( !add_char_to_string(p, FOLDER_DELIMITER, MAXPATHLEN) ) {
			free(p);
			return NULL;
		}
	}
	return p;
#else
	return NULL;
#endif
}

/* */
int add_char_to_string(char *const string, char c, const int size) {
	int i;

	/* check for null pointer */
	if ( !string ) {
		return 0;
	}

	/* compute length */
	for ( i = 0; string[i]; i++ );

	/* check length */
	if ( i >= size-1 ) {
		return 0;
	}

	/* add char */
	string[i] = c;
	string[i+1] = '\0';

	/* */
	return 1;
}

/* */
int mystrcat(char *const string, const char *const string_to_add, const int size) {
	int i;
	int y;

	/* check for null pointer */
	if ( !string || !string_to_add ) {
		return 0;
	}

	/* compute lenghts */
	for ( i = 0; string[i]; i++ );
	for ( y = 0; string_to_add[y]; y++ );

	/* check length */
	if ( i >= size-y-1 ) {
		return 0;
	}

	strcat(string, string_to_add);

	/* */
	return 1;
}

/* */
int path_exists(const char *const path) {
#if defined (_WIN32)
	DWORD dwResult;
#endif
	if ( !path ) {
		return 0;
	}
#if defined (_WIN32)
	dwResult = GetFileAttributes(path);
	if (dwResult != INVALID_FILE_ATTRIBUTES && (dwResult & FILE_ATTRIBUTE_DIRECTORY)) {
		return 1;
	}
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
	if ( !access(path, W_OK) ) {
		return 1;
	}
#endif
	return 0;
}

/* */
int file_exists(const char *const file) {
#if defined (_WIN32)
	DWORD dwResult;
#endif
	if ( !file ) {
		return 0;
	}
#if defined (_WIN32)
	dwResult = GetFileAttributes(file);
	if (dwResult != INVALID_FILE_ATTRIBUTES && !(dwResult & FILE_ATTRIBUTE_NORMAL)) {
		return 1;
	}
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
	if ( !access(file, W_OK) ) {
		return 1;
	}
#endif
	return 0;
}

/* */
PREC get_mean(const PREC *const values, const int count) {
	int i;
	PREC mean;

	/* check for null pointer */
	assert(values && count);

	/* */
	if ( 1 == count ) {
		return values[0];
	}

	/* compute mean */
	mean = 0.0;
	for ( i = 0; i < count; i++ ) {
		if ( IS_INVALID_VALUE(values[i]) ) {
			return INVALID_VALUE;
		}
		mean += values[i];
	}
	mean /= count;

	/* check for NAN */
	if ( mean != mean ) {
		mean = INVALID_VALUE;
	}

	/* ok */
	return mean;
}

/* */
PREC get_standard_deviation(const PREC *const values, const int count) {
	int i;
	PREC mean;
	PREC sum;
	PREC sum2;

	/* check for null pointer */
	assert(values && count);

	/* */
	if ( 1 == count ) {
		return INVALID_VALUE;
	}

	/* get mean */
	mean = get_mean(values, count);
	if ( IS_INVALID_VALUE(mean) ) {
		return INVALID_VALUE;
	}

	/* compute stddev */
	sum = 0.0;
	sum2 = 0.0;
	for ( i = 0; i < count; i++ ) {
		sum = (values[i] - mean);
		sum *= sum;
		sum2 += sum;
	}
	sum2 /= count-1;
	sum2 = (PREC)SQRT(sum2);

	/* check for NAN */
	if ( sum2 != sum2 ) {
		sum2 = INVALID_VALUE;
	}

	/* ok */
	return sum2;
}

/* */
PREC get_median(const PREC *const values, const int count, int *const error) {
	int i;
	int median_count;
	PREC *p_median;
	PREC *median_no_leak;
	PREC result;

	/* check for null pointer */
	assert(values);

	/* reset */
	*error = 0;

	/* get valid values */
	p_median = NULL;
	median_count = 0;
	for ( i = 0; i < count; i++ ) {
		if ( !IS_INVALID_VALUE(values[i]) ) {
			median_no_leak = realloc(p_median, ++median_count*sizeof *median_no_leak);
			if ( !median_no_leak ) {
				*error = 1;
				free(p_median);
				return 0;
			}

			p_median = median_no_leak;
			p_median[median_count-1] = values[i];
		}
	}

	if ( !median_count ) {
		return INVALID_VALUE;
	} else if ( 1 == median_count ) {
		result = p_median[0];
		free(p_median);
		return result;
	}

	/* sort values */
	qsort(p_median, median_count, sizeof *p_median, compare_prec);

	/* get median */
	if ( median_count & 1 ) {
		result = p_median[((median_count+1)/2)-1];
	} else {
		result = ((p_median[(median_count/2)-1] + p_median[median_count/2]) / 2);
	}

	/* free memory */
	free(p_median);

	/* check for NAN */
	if ( result != result ) {
		result = INVALID_VALUE;
	}

	/* */
	return result;
}

/* todo : implement a better comparison for equality */
int compare_prec(const void * a, const void * b) {
	if ( *(PREC *)a < *(PREC *)b ) {
		return -1;
	} else if ( *(PREC *)a > *(PREC *)b ) {
		return 1;
	} else {
		return 0;
	}
}

/* */
int compare_int(const void *a, const void *b) {
	return ( *(int *)a - *(int *)b );
}

/* */
int timestampSort(const void *a, const void *b) {
	TIMESTAMP *ta;
	TIMESTAMP *tb;
	
	ta = (TIMESTAMP *)a;
	tb = (TIMESTAMP *)b;

	if ( ta->YYYY == tb->YYYY )
		if ( ta->MM == tb->MM )
			if ( ta->DD == tb->DD )
				if ( ta->hh == tb->hh )
					if ( ta->mm == tb->mm )
						if ( ta->ss == tb->ss ) return 0;
						else return (ta->ss > tb->ss) ? 1 : -1;
					else return (ta->mm > tb->mm) ? 1 : -1;
				else return (ta->hh > tb->hh) ? 1 : -1;
			else return (ta->DD > tb->DD) ? 1 : -1;
		else return (ta->MM > tb->MM) ? 1 : -1;
	else return (ta->YYYY > tb->YYYY) ? 1 : -1;
}

/* */
static int compare_time_zones(const void *a, const void *b) {
	return timestampSort(&((TIME_ZONE *)a)->timestamp, &((TIME_ZONE *)b)->timestamp);
}

/* */
static int compare_htower(const void *a, const void *b) {
	return timestampSort(&((HEIGHT *)a)->timestamp, &((HEIGHT *)b)->timestamp);
}

/* */
static int compare_sc_negles(const void *a, const void *b) {
	return timestampSort(&((SC_NEGL *)a)->timestamp, &((SC_NEGL *)b)->timestamp);
}

/* */
char *tokenizer(char *string, char *delimiter, char **p) {
	int i;
	int j;
	int c;
	char *_p;

	/* */
	if ( string ) {
		*p = string;
		_p = string;
	} else {
		_p = *p;
		if ( !_p ) {
			return NULL;
		}
	}

	/* */
	c = 0;
	for (i = 0; _p[i]; i++) {
		for (j = 0; delimiter[j]; j++) {
			if ( _p[i] == delimiter[j] ) {
				*p += c + 1;
				_p[i] = '\0';
				return _p;
			} else {
				++c;
			}
		}
	}

	/* */
	*p = NULL;
	return _p;
}

/* */
PREC get_percentile(const PREC *values, const int n, const float percentile, int *const error) {
	int i;
	int y;
	int index;
	PREC r;
	PREC *v;

	/* check parameters */
	assert(values && error);

	/* reset */
	*error = 0;

	/* */
	if ( !n ) {
		return 0.0;
	} else if ( 1 == n ) {
		if ( IS_INVALID_VALUE(values[0]) ) {
			*error = 1;
			return 0.0;
		} else {
			return values[0];
		}
	}

	/* percentile MUST be a value between 0 and 100*/
	if ( percentile < 0.0 || percentile > 100.0 ) {
		*error = 1;
		return 0.0;
	}

	/* */
	v = malloc(n*sizeof*v);
	if ( !v ) {
		*error = 1;
		return 0.0;
	}

	/* */
	y = 0;
	for ( i = 0; i < n; i++ ) {
		if ( !IS_INVALID_VALUE(values[i]) ) {
			v[y++] = values[i];
		}
	}
	if ( !y ) {
		free(v);
		*error = 1;
		return 0.0;
	}

	/* */
	qsort(v, y, sizeof *v, compare_prec);

	/*
		- changed on May 20, 2013
			FROM index = ROUND((percentile / 100.0) * y + 0.5);
			TO index = (percentile / 100) * y;

		- changed again Nov 4, 2013
			added ROUND where 0.5 is added to perc*y and then truncated to the integer.
			E.g.: perc 50 of 5 values is INTEGER[((50/100)*5)+0.5] = 3
	*/
	index = ROUND((percentile / 100) * y);
	if ( --index < 0 ) {
		index = 0;
	}

	if ( index >= y ) {
		return v[y-1];
	}

	/* */
	r = v[index];

    /* */
	free(v);

	/* */
	return r;
}

/* */
PREC *get_percentiles(const PREC *values, const int n, const float *const percentiles, const int percentiles_count) {
	int i;
	int y;
	int index;
	PREC *v;
	PREC *arr;

	/* check parameters */
	assert(values && n && percentiles && percentiles_count);

	/* check percentiles */
	for ( i = 0; i < percentiles_count; i++ ) {
		/* percentile MUST be a value between 0 and 100*/
		if ( percentiles[i] < 0.0 || percentiles[i] > 100.0 ) {
			return NULL;
		}
	}

	/* alloc memory */
	arr = malloc(percentiles_count*sizeof*arr);
	if ( !arr ) {
		return 0;
	}

	/* 1 row of dataset ?*/
	if ( 1 == n ) {
		if ( IS_INVALID_VALUE(values[0]) ) {
			free(arr);
			return NULL;
		}
		for ( i = 0; i < percentiles_count; i++ ) {
			arr[i] = values[0];
		}
		return arr;
	}

	/* */
	v = malloc(n*sizeof*v);
	if ( !v ) {
		free(arr);
		return NULL;
	}

	/* build-up dataset without invalid_values */
	y = 0;
	for ( i = 0; i < n; i++ ) {
		if ( !IS_INVALID_VALUE(values[i]) ) {
			v[y++] = values[i];
		}
	}
	if ( !y ) {
		free(v);
		free(arr);
		return NULL;
	}

	/* sort array */
	qsort(v, y, sizeof *v, compare_prec);

	/* loop on each percentile */
	for ( i = 0; i < percentiles_count; i++ ) {
		/*
		- changed on May 20, 2013
			FROM index = ROUND((percentile / 100.0) * y + 0.5);
			TO index = (percentile / 100) * y;

		- changed again Nov 4, 2013
			added ROUND where 0.5 is added to perc*y and then truncated to the integer.
			E.g.: perc 50 of 5 values is INTEGER[((50/100)*5)+0.5] = 3
		*/
		index = ROUND((percentiles[i] / 100) * y);
		if ( --index < 0 ) {
			index = 0;
		}

		if ( index >= y ) {
			arr[i] = v[y-1];
		} else {
			arr[i] = v[index];
		}
	}

	/* free memory */
	free(v);

	/* */
	return arr;
}

/*
*
* INFO STUFF
*
*/

typedef enum {
	INFO_NO_ERROR = 0,
	INFO_UNBALANCED_OPEN_TOKEN,
	INFO_UNBALANCED_CLOSE_TOKEN,
	INFO_OUT_OF_MEMORY,
	INFO_NO_PARTS_FOUND

} INFO_ERROR;

/* */
static INFO_ERROR info_parse(INFO *const info) {
	int i;
	int token_open;
	PART *parts_no_leak;

	assert(info);

	token_open = 0;
	for ( i = 0; info->text[i]; i++ ) {
		switch ( info->text[i] ) {
			case TOKEN_OPEN:
				if ( token_open ) {
					return INFO_UNBALANCED_OPEN_TOKEN;
				}
				parts_no_leak = realloc(info->parts, ++info->parts_count*sizeof*parts_no_leak);
				if ( ! parts_no_leak ) {
					--info->parts_count;
					return INFO_OUT_OF_MEMORY;
				}
				info->text[i] = '\0';
				info->parts = parts_no_leak;
				info->parts[info->parts_count-1].name = &info->text[i+1];
				token_open = 1;
			break;

			case TOKEN_CLOSE:
				if ( ! token_open ) {
					return INFO_UNBALANCED_OPEN_TOKEN;
				}
				info->text[i] = '\0';
				info->parts[info->parts_count-1].text = &info->text[i+1];
				if ( '\r' == info->parts[info->parts_count-1].text[0] ) {
					++info->parts[info->parts_count-1].text;
				}
				if ( '\n' == info->parts[info->parts_count-1].text[0] ) {
					++info->parts[info->parts_count-1].text;
				}
				token_open = 0;
			break;

		}
	}

	if ( token_open ) {
		return INFO_UNBALANCED_CLOSE_TOKEN;
	}

	if ( ! info->parts_count ) {
		return INFO_NO_PARTS_FOUND;
	}

	return INFO_NO_ERROR;
}

/* */
INFO *info_import(const char *const filename) {
	FILE *f;
	INFO *info;
	INFO_ERROR err;

	if ( !filename || !filename[0] ) {
		return NULL;
	}

	info = malloc(sizeof*info);
	if ( ! info ) {
		printf("out of memory during parse of %s\n", filename);
		return NULL;
	}
	info->text = NULL;
	info->parts = NULL;
	info->parts_count = 0;

	f = fopen(filename, "rb");
	if ( !f ) {
		printf("unable to open %s\n", filename);
		info_free(info);
		return NULL;
	}
	fseek(f, 0, SEEK_END);
	info->size = ftell(f);
	fseek(f, 0, SEEK_SET);
	info->text = malloc(info->size+1);
	if ( !info->text ) {
		printf("%s\n", err_out_of_memory);
		fclose(f);
		info_free(info);
		return NULL;
	}

	if ( info->size != fread(info->text, sizeof*info->text, info->size, f) ) {
		printf("unable to read file: %s\n", filename);
		fclose(f);
		info_free(info);
		return NULL;
	}
	fclose(f);
	info->text[info->size] = '\0';

	/* parse info */
	err = info_parse(info);
	switch ( err ) {
		case INFO_NO_ERROR:
			/* do nothing */
		break;

		case INFO_UNBALANCED_OPEN_TOKEN:
		case INFO_UNBALANCED_CLOSE_TOKEN:
			printf("unbalanced %s token for %s\n", (INFO_UNBALANCED_OPEN_TOKEN == err) ? "open" : "close", filename);
		break;
		
		case INFO_OUT_OF_MEMORY:
			printf("out of memory during parse of %s\n", filename);
		break;

		case INFO_NO_PARTS_FOUND:
			printf("no parts found on %s\n", filename);
		break;
	}

	if ( INFO_NO_ERROR != err ) {
		info_free(info);
		info = NULL;
	}

	return info;
}

/* */
INFO *info_get(const char *const string) {
	INFO *info;
	INFO_ERROR err;

	assert(string);

	info = malloc(sizeof*info);
	if ( ! info ) {
		puts("out of memory during parse of info");
		return NULL;
	}
	info->text = NULL;
	info->parts = NULL;
	info->parts_count = 0;

	/* copy string */
	info->text = string_copy(string);
	if ( ! info->text ) {
		puts("out of memory during parse of info");
		info_free(info);
		return NULL;
	}

	/* get string length */
	for ( info->size = 0; info->text[info->size]; info->size++ );

	/* parse info */
	err = info_parse(info);
	switch ( err ) {
		case INFO_NO_ERROR:
			/* do nothing */
		break;

		case INFO_UNBALANCED_OPEN_TOKEN:
		case INFO_UNBALANCED_CLOSE_TOKEN:
			printf("unbalanced %s token for info\n", (INFO_UNBALANCED_OPEN_TOKEN == err) ? "open" : "close");
		break;
		
		case INFO_OUT_OF_MEMORY:
			puts("out of memory during parse of info");
		break;

		case INFO_NO_PARTS_FOUND:
			puts("no parts found on info");
		break;
	}

	if ( INFO_NO_ERROR != err ) {
		info_free(info);
		info = NULL;
	}

	return info;
}

/* */
char *info_get_part_name(const INFO *const info, const int index) {
	if ( (index >= 0) && (index < info->parts_count) ) {
		return info->parts[index].name;
	} else {
		return NULL;
	}
}

/* */
char *info_get_part_by_name(const INFO *const info, const char *const name) {
	int i;

	for ( i = 0; i < info->parts_count; i++ ) {
		if ( ! string_compare_i(info->parts[i].name, name) ) {
			return info->parts[i].text;
		}
	}
	return NULL;
}

/* */
char *info_get_part_by_number(const INFO *const info, const int index) {
	if ( (index >= 0) && (index < info->parts_count) ) {
		return info->parts[index].text;
	} else {
		return NULL;
	}
}

/* */
void info_free(INFO *info) {
	if ( info ) {
		free(info->parts);
		free(info->text);
		free(info);
	}
}

/*
*
* END INFO STUFF
*
*/

/* */
TIMESTAMP *get_timestamp(const char *const string) {
	int i;
	int j;
	int index;
	int error;
	char *p;
	char token[5];
	TIMESTAMP *t;
	const char *field[] = { "year", "month", "day", "hour", "minute", "second" };
	const int field_size[] = { 4, 2, 2, 2, 2, 2 };

	t = malloc(sizeof*t);
	if ( ! t ) {
		puts(err_out_of_memory);
		return NULL;
	}
	t->YYYY = 0;
	t->MM = 0;
	t->DD = 0;
	t->hh = 0;
	t->mm = 0;
	t->ss = 0;

	for ( i = 0; string[i]; i++ );
	if ( (i < 0) || (i > 14) || (i & 1) ) {
		printf("bad length for %s\n", TIMESTAMP_STRING);
		return NULL;
	}

	p = (char *)string;
	index = 0;
	while ( 1 ) {
		i = 0;
		while ( i < field_size[index] ) {
			token[i++] = *p++;
		}
		if ( i != field_size[index] ) {
			printf("bad field '%s' on %s\n\n", field[index], string);
			free(t);
			return NULL;
		}
		token[field_size[index]] = '\0';
		j = convert_string_to_int(token, &error);
		if ( error ) {
			printf("bad value '%s' for field '%s' on %s\n\n", token, field[index], string);
			free(t);
			return NULL;
		}

		switch ( index ) {
			case 0:	/* year */
				t->YYYY = j;
			break;

			case 1: /* month */
				t->MM = j;
			break;

			case 2: /* day */
				t->DD = j;
			break;

			case 3: /* hour */
				t->hh = j;
			break;

			case 4: /* minute */
				t->mm = j;
			break;

			case 5: /* second */
				t->ss = j;
			break;
		}
		++index;
		if ( ! *p ) {
			return t;
		}
	}
}

/* */
int get_row_by_timestamp(const TIMESTAMP *const t, const int hourly_dataset) {
	int i;
	int y;
	int rows_per_day;
	int rows_per_hour;
	const int days_in_month[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

	/* */
	if ( ! t ) {
		return -1;
	}

	/* */
	rows_per_day = 48;
	if ( hourly_dataset ) {
		rows_per_day = 24;
	}
	rows_per_hour = 2;
	if ( hourly_dataset ) {
		rows_per_hour = 1;
	}

	/* check for last row */
	if (	(1 == t->DD) &&
			(1 == t->MM) &&
			(0 == t->hh) &&
			(0 == t->mm) ) {
		if ( IS_LEAP_YEAR(t->YYYY-1) ) {
			i = LEAP_YEAR_ROWS;
		} else {
			i = YEAR_ROWS;
		}
		if ( hourly_dataset ) {
			i /= 2;
		}
	} else {
		i = 0;
		for (y = 0; y < t->MM - 1; y++ ) {
			i += days_in_month[y];
		}

		/* leap year ? */
		if ( IS_LEAP_YEAR(t->YYYY) && ((t->MM - 1) > 1) ) {
			++i;
		}

		/* */
		i += t->DD - 1;
		i *= rows_per_day;
		i += t->hh * rows_per_hour;
		if ( t->mm > 0 ) {
			++i;
		}
	}

	/* return zero based index */
	return --i;
}

/* */
int get_year_from_timestamp_string(const char *const string) {
	int year;
	TIMESTAMP *t;

	if ( ! string || ! string[0] ) {
		return -1;
	}

	t = get_timestamp(string);
	if ( ! t ) {
		return -1;
	}

	year = t->YYYY;
	free(t);

	return year;

}

/* */
TIMESTAMP *timestamp_get_by_row(int row, int yy, const int hourly_dataset, const int start) {
	int i;
	int is_leap;
	int rows_per_day;
	int days_per_month[12] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
	static TIMESTAMP t = { 0 };

	/* reset */
	t.YYYY = yy;
	t.ss = 0;

	/* leap year ? */
	is_leap = IS_LEAP_YEAR(yy);
	if ( is_leap ) {
		++days_per_month[1];
	}

	/* inc row...we used 1 based index */
	if ( ! start ) {
		++row;
	}
	
	/* compute rows per day */
	rows_per_day = hourly_dataset ? 24: 48;
	
	/* get day and month */
	t.DD = row / rows_per_day;
	for ( i = 0, t.MM = 0; t.MM < 12; ++t.MM ) {
		i += days_per_month[t.MM];
		if ( t.DD <= i ) {
			t.DD -= i - days_per_month[t.MM];
			break;
		}
	}
	if ( ++t.DD > days_per_month[t.MM] ) {
		t.DD = 1;
		if ( ++t.MM > 11 ) {
			t.MM = 0;
			++t.YYYY;
		}
	}
	++t.MM;

	/* get hour */
	if ( hourly_dataset ) {
		t.hh = row % rows_per_day;
		t.mm = 0;
	} else {
		t.hh = (row % rows_per_day) / 2;
		/* even row ? */
		if ( row & 1 ) {
			t.mm = 30;
		} else {
			t.mm = 0;
		}
	}

	/* ok */
	return &t;
}

/* */
char *timestamp_get_by_row_s(int row, int yy, const int hourly_dataset, const int start) {
	TIMESTAMP *t;
	static char buffer[12+1] = { 0 };

	t = timestamp_get_by_row(row, yy, hourly_dataset, start);
	sprintf(buffer, "%04d%02d%02d%02d%02d", t->YYYY, t->MM, t->DD, t->hh, t->mm);
	return buffer;
}

/* */
TIMESTAMP *timestamp_ww_get_by_row(int row, int year, const int hourly_dataset, int start) {
	int i;
	int last;

	/* */
	assert((row >= 0) &&(row < 52));

	/* */
	last = (52-1 == row);
	i = 7 * (hourly_dataset ? 24 : 48);
	row *= i;

	/* */
	if ( ! start ) {
		if ( last ) {
			row = IS_LEAP_YEAR(year) ? 17568 : 17520;
			if ( hourly_dataset ) {
				row /= 2;
			}
		} else {
			row += i;
		}
		start = 1;
		--row;
	}

	/* */
	return timestamp_get_by_row(row, year, hourly_dataset, start);
}

/* */
char *timestamp_ww_get_by_row_s(int row, int yy, const int hourly_dataset, const int start) {
	TIMESTAMP *t;
	static char buffer[8+1] = { 0 };

	t = timestamp_ww_get_by_row(row, yy, hourly_dataset, start);
	sprintf(buffer, "%04d%02d%02d", t->YYYY, t->MM, t->DD);
	return buffer;
}

/* private function for gapfilling */
static PREC gf_get_similiar_mean(const GF_ROW *const gf_rows, const int rows_count) {
 	int i;
	PREC mean;

	/* check parameter */
	assert(gf_rows);

	/* get mean */
	mean = 0.0;
	for ( i = 0; i < rows_count; i++ ) {
		mean += gf_rows[i].similiar;
	}
	mean /= rows_count;

	/* check for NAN */
	if ( mean != mean ) {
		mean = INVALID_VALUE;
	}

	/* */
	return mean;
}

/* gapfilling */
PREC gf_get_similiar_standard_deviation(const GF_ROW *const gf_rows, const int rows_count) {
	int i;
	PREC mean;
	PREC sum;
	PREC sum2;

	/* check parameter */
	assert(gf_rows);

	/* get mean */
	mean = gf_get_similiar_mean(gf_rows, rows_count);
	if ( IS_INVALID_VALUE(mean) ) {
		return INVALID_VALUE;
	}

	/* compute standard deviation */
	sum = 0.0;
	sum2 = 0.0;
	for ( i = 0; i < rows_count; i++ ) {
		sum = (gf_rows[i].similiar - mean);
		sum *= sum;
		sum2 += sum;
	}
	sum2 /= rows_count-1;
	sum2 = (PREC)SQRT(sum2);

	/* check for NAN */
	if ( sum2 != sum2 ) {
		sum2 = INVALID_VALUE;
	}

	/* */
	return sum2;
}

/* gapfilling */
PREC gf_get_similiar_median(const GF_ROW *const gf_rows, const int rows_count, int *const error) {
	int i;
	PREC *p_median;
	PREC result;

	/* check for null pointer */
	assert(gf_rows);

	/* reset */
	*error = 0;

	if ( !rows_count ) {
		return INVALID_VALUE;
	} else if ( 1 == rows_count ) {
		return gf_rows[0].similiar;
	}

	/* get valid values */
	p_median = malloc(rows_count*sizeof*p_median);
	if ( !p_median ) {
		*error = 1;
		return INVALID_VALUE;
	}
	for ( i = 0; i < rows_count; i++ ) {
		p_median[i] = gf_rows[i].similiar;
	}

	/* sort values */
	qsort(p_median, rows_count, sizeof *p_median, compare_prec);

	/* get median */
	if ( rows_count & 1 ) {
		result = p_median[((rows_count+1)/2)-1];
	} else {
		result = ((p_median[(rows_count/2)-1] + p_median[rows_count/2]) / 2);
	}

	/* free memory */
	free(p_median);

	/* check for NAN */
	if ( result != result ) {
		result = INVALID_VALUE;
	}

	/* */
	return result;
}

/* private function for gapfilling */
static int gapfill(	PREC *values,
					const int struct_size,
					GF_ROW *const gf_rows,
					const int start_window,
					const int end_window,
					const int current_row,
					const int start,
					const int end,
					const int step,
					const int method,
					const int hourly_dataset,
					const PREC value1_tolerance_min,
					const PREC value1_tolerance_max,
					const PREC value2_tolerance,
					const PREC value3_tolerance,
					const int tofill_column,
					const int value1_column,
					const int value2_column,
					const int value3_column) {
	int i;
	int y;
	int j;
	int z;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int samples_count;
	PREC value1_tolerance;
	PREC *window_current_values;
	PREC *row_current_values;

	/* check parameter */
	assert(values && gf_rows && (method >=0 && method < GF_METHODS));

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	samples_count = 0;
	value1_tolerance = 0.0;

	/* j is and index checker for hourly method */
	if ( hourly_dataset ) {
		j = 3;
	} else {
		j = 5;
	}

	/* */
	i = start;
	if ( GF_TOFILL_METHOD == method ) {
		z = hourly_dataset ? 24 : 48;
	} else {
		z = 1;
	}
	while ( i <= end ) {
		/* reset */
		samples_count = 0;

		/* compute window */
		window = 48 * i;
		if ( hourly_dataset ) {
			window /= 2;
		}

		/* get window start index */
		window_start = current_row - window;
		if ( GF_TOFILL_METHOD == method ) {
			if ( hourly_dataset ) {
				window_start -= 1;
			} else {
				window_start -= 2;
			}
		}

		if ( GF_TOFILL_METHOD != method ) {
			/* fix for recreate markus code */
			++window_start;
		}

		/* get window end index */
		window_end = current_row + window;
		if (GF_TOFILL_METHOD == method ) {
			if ( hourly_dataset ) {
				window_end += 2;
			} else {
				window_end += 3;
			}
		}

		/*	fix bounds for first two methods
			cause in hour method (NEE_METHOD) a window start at -32 and window end at 69,
			it will be fixed to window start at 0 and this is an error...
		*/
		if ( GF_TOFILL_METHOD != method ) {
			if ( window_start < 0 ) {
				window_start = 0;
			}

			if ( window_end > end_window ) {
				window_end = end_window;
			}

			/* modified on June 25, 2013 */
			/* compute tolerance for value1 */
			if ( IS_INVALID_VALUE(value1_tolerance_min) ) {
				value1_tolerance = value1_tolerance_max;
			} else if ( IS_INVALID_VALUE(value1_tolerance_max) ) {
				value1_tolerance = value1_tolerance_min;
			} else {
				value1_tolerance = ((PREC *)(((char *)values)+current_row*struct_size))[value1_column];
				if ( value1_tolerance < value1_tolerance_min ) {
					value1_tolerance = value1_tolerance_min;
				} else if ( value1_tolerance > value1_tolerance_max ) {
					value1_tolerance = value1_tolerance_max;
				}
			}
		}

		/* loop through window */
		for ( window_current = window_start; window_current < window_end; window_current += z ) {
			window_current_values = ((PREC *)(((char *)values)+window_current*struct_size));
			row_current_values = ((PREC *)(((char *)values)+current_row*struct_size));

			switch ( method ) {
				case GF_ALL_METHOD:
					if ( IS_FLAG_SET(gf_rows[window_current].mask, GF_ALL_VALID) ) {
						if (
								(FABS(window_current_values[value2_column]-row_current_values[value2_column]) < value2_tolerance) &&
								(FABS(window_current_values[value1_column]-row_current_values[value1_column]) < value1_tolerance) &&
								(FABS(window_current_values[value3_column]-row_current_values[value3_column]) < value3_tolerance)
							) {
							gf_rows[samples_count++].similiar = window_current_values[tofill_column];
						}
					}
				break;

				case GF_VALUE1_METHOD:
					if ( IS_FLAG_SET(gf_rows[window_current].mask, (GF_TOFILL_VALID|GF_VALUE1_VALID)) ) {
						if ( FABS(window_current_values[value1_column]-row_current_values[value1_column]) < value1_tolerance ) {
							gf_rows[samples_count++].similiar = window_current_values[tofill_column];
						}
					}
				break;

				case GF_TOFILL_METHOD:
					for ( y = 0; y < j; y++ ) {
						if ( ((window_current+y) < 0) || (window_current+y) >= end_window ) {
							continue;
						}
						if ( IS_FLAG_SET(gf_rows[window_current+y].mask, GF_TOFILL_VALID) ) {
							gf_rows[samples_count++].similiar = ((PREC *)(((char *)values)+((window_current+y)*struct_size)))[tofill_column];
						}
					}
				break;
			}
		}

		if ( samples_count > 1 ) {
			/* set mean */
			gf_rows[current_row].filled = gf_get_similiar_mean(gf_rows, samples_count);

			/* set standard deviation */
			gf_rows[current_row].stddev = gf_get_similiar_standard_deviation(gf_rows, samples_count);

			/* set method */
			gf_rows[current_row].method = method + 1;

			/* set time-window */
			gf_rows[current_row].time_window = i * 2;

			/* fix hour method timewindow */
			if ( GF_TOFILL_METHOD == method ) {
				++gf_rows[current_row].time_window;
			}

			/* set samples */
			gf_rows[current_row].samples_count = samples_count;

			/* ok */
			return 1;
		}

		/* inc loop */
		i += step;

		/* break if window bigger than  */
		if ( (window_start < start_window) && (window_end > end_window) ) {
			break;
		}
	}

	/* */
	return 0;
}

/* DEV version */
static int dev_mds_gf(	PREC *values,
				const int struct_size,
				GF_ROW *const gf_rows,
				const int start_window,
				const int end_window,
				const int current_row,
				const int hourly_dataset,
				const PREC value1_tolerance_min,
				const PREC value1_tolerance_max,
				const PREC value2_tolerance,
				const PREC value3_tolerance,
				const int tofill_column,
				const int value1_column,
				const int value2_column,
				const int value3_column) {
	int i;
	int y;
	int j;
	int z;
	int window;
	int window_start;
	int window_end;
	int window_current;
	int samples_count;
	int current_method;
	int start;
	int end;
	int step;
	int method;
	PREC value1_tolerance;
	PREC *window_current_values;
	PREC *row_current_values;

	struct {
		int start;
		int end;
		int step;
		int method;
	}  mds[] = {
		{  7, 14, 7, GF_ALL_METHOD }
		, { 7, 7, 7, GF_VALUE1_METHOD }
		, { 0, 2, 1, GF_TOFILL_METHOD }
		, { 21, 77, 7, GF_ALL_METHOD }
		, { 14, 77, 7, GF_VALUE1_METHOD }
		, { 3, 0, 3, GF_TOFILL_METHOD }
	};

	/* check parameter */
	assert(values && gf_rows);

	/* reset */
	window = 0;
	window_start = 0;
	window_end = 0;
	window_current = 0;
	samples_count = 0;
	value1_tolerance = 0.0;
	
	/* fix last method */
	mds[5].end = end_window + 1;

	/* j is and index checker for hourly method */
	if ( hourly_dataset ) {
		j = 3;
	} else {
		j = 5;
	}

	/* */
	current_method = 0;
	while ( current_method < SIZEOF_ARRAY(mds) ) {
		start = mds[current_method].start;
		end = mds[current_method].end;
		step = mds[current_method].step;
		method = mds[current_method].method;

		i = start;
		if ( GF_TOFILL_METHOD == method ) {
			z = hourly_dataset ? 24 : 48;
		} else {
			z = 1;
		}
		while ( i <= end ) {
			/* reset */
			samples_count = 0;

			/* compute window */
			window = 48 * i;
			if ( hourly_dataset ) {
				window /= 2;
			}

			/* get window start index */
			window_start = current_row - window;
			if ( GF_TOFILL_METHOD == method ) {
				if ( hourly_dataset ) {
					window_start -= 1;
				} else {
					window_start -= 2;
				}
			}

			if ( GF_TOFILL_METHOD != method ) {
				/* fix for recreate markus code */
				++window_start;
			}

			/* get window end index */
			window_end = current_row + window;
			if (GF_TOFILL_METHOD == method ) {
				if ( hourly_dataset ) {
					window_end += 2;
				} else {
					window_end += 3;
				}
			}

			/*	fix bounds for first two methods
				cause in hour method (NEE_METHOD) a window start at -32 and window end at 69,
				it will be fixed to window start at 0 and this is an error...
			*/
			if ( GF_TOFILL_METHOD != method ) {
				if ( window_start < 0 ) {
					window_start = 0;
				}

				if ( window_end > end_window ) {
					window_end = end_window;
				}

				/* modified on June 25, 2013 */
				/* compute tolerance for value1 */
				if ( IS_INVALID_VALUE(value1_tolerance_min) ) {
					value1_tolerance = value1_tolerance_max;
				} else if ( IS_INVALID_VALUE(value1_tolerance_max) ) {
					value1_tolerance = value1_tolerance_min;
				} else {
					value1_tolerance = ((PREC *)(((char *)values)+current_row*struct_size))[value1_column];
					if ( value1_tolerance < value1_tolerance_min ) {
						value1_tolerance = value1_tolerance_min;
					} else if ( value1_tolerance > value1_tolerance_max ) {
						value1_tolerance = value1_tolerance_max;
					}
				}
			}

			/* loop through window */
			for ( window_current = window_start; window_current < window_end; window_current += z ) {
				window_current_values = ((PREC *)(((char *)values)+window_current*struct_size));
				row_current_values = ((PREC *)(((char *)values)+current_row*struct_size));

				switch ( method ) {
					case GF_ALL_METHOD:
						if ( IS_FLAG_SET(gf_rows[window_current].mask, GF_ALL_VALID) ) {
							if (
									(FABS(window_current_values[value2_column]-row_current_values[value2_column]) < value2_tolerance) &&
									(FABS(window_current_values[value1_column]-row_current_values[value1_column]) < value1_tolerance) &&
									(FABS(window_current_values[value3_column]-row_current_values[value3_column]) < value3_tolerance)
								) {
								gf_rows[samples_count++].similiar = window_current_values[tofill_column];
							}
						}
					break;

					case GF_VALUE1_METHOD:
						if ( IS_FLAG_SET(gf_rows[window_current].mask, (GF_TOFILL_VALID|GF_VALUE1_VALID)) ) {
							if ( FABS(window_current_values[value1_column]-row_current_values[value1_column]) < value1_tolerance ) {
								gf_rows[samples_count++].similiar = window_current_values[tofill_column];
							}
						}
					break;

					case GF_TOFILL_METHOD:
						for ( y = 0; y < j; y++ ) {
							if ( ((window_current+y) < 0) || (window_current+y) >= end_window ) {
								continue;
							}
							if ( IS_FLAG_SET(gf_rows[window_current+y].mask, GF_TOFILL_VALID) ) {
								gf_rows[samples_count++].similiar = ((PREC *)(((char *)values)+((window_current+y)*struct_size)))[tofill_column];
							}
						}
					break;
				}
			}

			if ( samples_count > 1 ) {
				/* set mean */
				gf_rows[current_row].filled = gf_get_similiar_mean(gf_rows, samples_count);

				/* set standard deviation */
				gf_rows[current_row].stddev = gf_get_similiar_standard_deviation(gf_rows, samples_count);

				/* set method */
				gf_rows[current_row].method = method + 1;

				/* set time-window */
				gf_rows[current_row].time_window = i * 2;

				/* fix hour method timewindow */
				if ( GF_TOFILL_METHOD == method ) {
					++gf_rows[current_row].time_window;
				}

				/* set samples */
				gf_rows[current_row].samples_count = samples_count;

				/* ok */
				return 1;
			}

			/* inc loop */
			i += step;

			/* break if window bigger than  */
			if ( (window_start < start_window) && (window_end > end_window) ) {
				break;
			}
		}
		++current_method;
	}

	/* */
	return 0;
}

/* */
GF_ROW *dev_gf_mds_with_bounds(	PREC *values,
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
							int *no_gaps_filled_count) {
	int i;
	int c;
	int valids_count;
	GF_ROW *gf_rows;

	/* */
	assert(values && rows_count && no_gaps_filled_count);

	/* reset */
	*no_gaps_filled_count = 0;
	if ( start_row < 0  ) {
		start_row = 0;
	}
	if ( -1 == end_row ) {
		end_row = rows_count;
	} else if ( end_row > rows_count ) {
		end_row = rows_count;
	}

	/* allocate memory */
	gf_rows = malloc(rows_count*sizeof*gf_rows);
	if ( !gf_rows ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* reset */
	for ( i = 0; i < rows_count; i++ ) {
		gf_rows[i].mask = 0;
		gf_rows[i].similiar = INVALID_VALUE;
		gf_rows[i].stddev = INVALID_VALUE;
		gf_rows[i].filled = INVALID_VALUE;
		gf_rows[i].quality = INVALID_VALUE;
		gf_rows[i].time_window = 0;
		gf_rows[i].samples_count = 0;
		gf_rows[i].method = 0;
	}

	/* update mask and count valids TO FILL */
	valids_count = 0;
	for ( i = start_row; i < end_row; i++ ) {
		for ( c = 0; c < columns_count; c++ ) {
			if ( !IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[c]) ) {
				if ( tofill_column == c ) {
					gf_rows[i].mask |= GF_TOFILL_VALID;
				} else if ( value1_column == c ) {
					gf_rows[i].mask |= GF_VALUE1_VALID;
				} else if ( value2_column == c ) {
					gf_rows[i].mask |= GF_VALUE2_VALID;
				} else if ( value3_column == c ) {
					gf_rows[i].mask |= GF_VALUE3_VALID;
				}
			}
		}

		/* check for QC */
		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value1_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value1_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value1_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE1_VALID;
			}
		}

		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value2_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value2_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value2_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE2_VALID;
			}
		}

		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value3_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value3_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value3_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE3_VALID;
			}
		}

		if ( IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ) {
			++valids_count;
		}
	}

	if ( valids_count < values_min ) {
		puts(err_gf_too_less_values);
		free(gf_rows);
		return NULL;
	}

	/* */
	if ( IS_INVALID_VALUE(value1_tolerance_min) && IS_INVALID_VALUE(value1_tolerance_max) ) {
		value1_tolerance_min = GF_SW_IN_TOLERANCE_MIN;
		value1_tolerance_max = GF_SW_IN_TOLERANCE_MAX;
	}

	/* */
	if ( IS_INVALID_VALUE(value2_tolerance) ) {
		value2_tolerance = GF_TA_TOLERANCE;
	}

	/* */
	if ( IS_INVALID_VALUE(value3_tolerance) ) {
		value3_tolerance = GF_VPD_TOLERANCE;
	}

	/* loop for each row */
	for ( i = start_row; i < end_row; i++ ) {
		/* copy value from TOFILL to FILLED */
		gf_rows[i].filled = ((PREC *)(((char *)values)+i*struct_size))[tofill_column];

		/* compute hat ? */
		if ( !IS_INVALID_VALUE(gf_rows[i].filled) && !compute_hat ) {
			continue;
		}

		/*	fill
			Added 20140422: if a gap is impossible to fill, e.g. if with MDV there are no data in the whole dataset acquired in a range +/- one hour,
			the data point is not filled and the qc is set to -9999
		*/
		if ( ! dev_mds_gf(values, struct_size, gf_rows, start_row, end_row, i, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) ) {
			++*no_gaps_filled_count;
			continue;

		}
		
		/* compute quality */
		gf_rows[i].quality =	(gf_rows[i].method > 0) +
								((gf_rows[i].method == 1 && gf_rows[i].time_window > 14) || (gf_rows[i].method == 2 && gf_rows[i].time_window > 14) || (gf_rows[i].method == 3 && gf_rows[i].time_window > 1)) +
								((gf_rows[i].method == 1 && gf_rows[i].time_window > 56) || (gf_rows[i].method == 2 && gf_rows[i].time_window > 28) || (gf_rows[i].method == 3 && gf_rows[i].time_window > 5));
	}

	/* ok */
	return gf_rows;
}

/* */
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
							int *no_gaps_filled_count) {
	int i;
	int c;
	int valids_count;
	GF_ROW *gf_rows;

	/* */
	assert(values && rows_count && no_gaps_filled_count);

	/* reset */
	*no_gaps_filled_count = 0;
	if ( start_row < 0  ) {
		start_row = 0;
	}
	if ( -1 == end_row ) {
		end_row = rows_count;
	} else if ( end_row > rows_count ) {
		end_row = rows_count;
	}

	/* allocate memory */
	gf_rows = malloc(rows_count*sizeof*gf_rows);
	if ( !gf_rows ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* reset */
	for ( i = 0; i < rows_count; i++ ) {
		gf_rows[i].mask = 0;
		gf_rows[i].similiar = INVALID_VALUE;
		gf_rows[i].stddev = INVALID_VALUE;
		gf_rows[i].filled = INVALID_VALUE;
		gf_rows[i].quality = INVALID_VALUE;
		gf_rows[i].time_window = 0;
		gf_rows[i].samples_count = 0;
		gf_rows[i].method = 0;
	}

	/* update mask and count valids TO FILL */
	valids_count = 0;
	for ( i = start_row; i < end_row; i++ ) {
		for ( c = 0; c < columns_count; c++ ) {
			if ( !IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[c]) ) {
				if ( tofill_column == c ) {
					gf_rows[i].mask |= GF_TOFILL_VALID;
				} else if ( value1_column == c ) {
					gf_rows[i].mask |= GF_VALUE1_VALID;
				} else if ( value2_column == c ) {
					gf_rows[i].mask |= GF_VALUE2_VALID;
				} else if ( value3_column == c ) {
					gf_rows[i].mask |= GF_VALUE3_VALID;
				}
			}
		}

		/* check for QC */
		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value1_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value1_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value1_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE1_VALID;
			}
		}

		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value2_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value2_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value2_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE2_VALID;
			}
		}

		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value3_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value3_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value3_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE3_VALID;
			}
		}

		if ( IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ) {
			++valids_count;
		}
	}

	if ( valids_count < values_min ) {
		puts(err_gf_too_less_values);
		free(gf_rows);
		return NULL;
	}

	/* */
	if ( IS_INVALID_VALUE(value1_tolerance_min) && IS_INVALID_VALUE(value1_tolerance_max) ) {
		value1_tolerance_min = GF_SW_IN_TOLERANCE_MIN;
		value1_tolerance_max = GF_SW_IN_TOLERANCE_MAX;
	}

	/* */
	if ( IS_INVALID_VALUE(value2_tolerance) ) {
		value2_tolerance = GF_TA_TOLERANCE;
	}

	/* */
	if ( IS_INVALID_VALUE(value3_tolerance) ) {
		value3_tolerance = GF_VPD_TOLERANCE;
	}

	/* loop for each row */
	for ( i = start_row; i < end_row; i++ ) {
		/* copy value from TOFILL to FILLED */
		gf_rows[i].filled = ((PREC *)(((char *)values)+i*struct_size))[tofill_column];

		/* compute hat ? */
		if ( !IS_INVALID_VALUE(gf_rows[i].filled) && !compute_hat ) {
			continue;
		}

		/*	fill
			Added 20140422: if a gap is impossible to fill, e.g. if with MDV there are no data in the whole dataset acquired in a range +/- one hour,
			the data point is not filled and the qc is set to -9999
		*/
		if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 7, 14, 7, GF_ALL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
			if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 7, 7, 7, GF_VALUE1_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
				if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 0, 2, 1, GF_TOFILL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
					if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 21, 77, 7, GF_ALL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
						if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 14, 77, 7, GF_VALUE1_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
							if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 3, end_row + 1, 3, GF_TOFILL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) ) {
								++*no_gaps_filled_count;
								continue;
							}

		/* compute quality */
		gf_rows[i].quality =	(gf_rows[i].method > 0) +
								((gf_rows[i].method == 1 && gf_rows[i].time_window > 14) || (gf_rows[i].method == 2 && gf_rows[i].time_window > 14) || (gf_rows[i].method == 3 && gf_rows[i].time_window > 1)) +
								((gf_rows[i].method == 1 && gf_rows[i].time_window > 56) || (gf_rows[i].method == 2 && gf_rows[i].time_window > 28) || (gf_rows[i].method == 3 && gf_rows[i].time_window > 5));
	}

	/* ok */
	return gf_rows;
}

/* */
GF_ROW *gf_mds(PREC *values, const int struct_size, const int rows_count, const int columns_count, const int hourly_dataset,
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
																									int *no_gaps_filled_count) {
	return gf_mds_with_bounds(	values,
								struct_size,
								rows_count,
								columns_count,
								hourly_dataset,
								value1_tolerance_min,
								value1_tolerance_max,
								value2_tolerance,
								value3_tolerance,
								tofill_column,
								value1_column,
								value2_column,
								value3_column,
								-1,
								-1,
								-1,
								INVALID_VALUE,
								values_min,
								compute_hat,
								-1,
								-1,
								no_gaps_filled_count
	);
}

/* */
GF_ROW *gf_mds_with_qc(PREC *values, const int struct_size, const int rows_count, const int columns_count, const int hourly_dataset,
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
																										int *no_gaps_filled_count) {
	return gf_mds_with_bounds(	values,
								struct_size,
								rows_count,
								columns_count,
								hourly_dataset,
								value1_tolerance_min,
								value1_tolerance_max,
								value2_tolerance,
								value3_tolerance,
								tofill_column,
								value1_column,
								value2_column,
								value3_column,
								value1_qc_column,
								value2_qc_column,
								value3_qc_column,
								qc_thrs,
								values_min,
								compute_hat,
								-1,
								-1,
								no_gaps_filled_count
	);
}

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
						int *no_gaps_filled_count) {
	int i;
	int c;
	int start_row = -1;
	int end_row = -1;
	int valids_count;
	GF_ROW *gf_rows;

	/* */
	assert(values && rows_count && no_gaps_filled_count);

	/* reset */
	*no_gaps_filled_count = 0;
	if ( start_row < 0  ) {
		start_row = 0;
	}
	if ( -1 == end_row ) {
		end_row = rows_count;
	} else if ( end_row > rows_count ) {
		end_row = rows_count;
	}

	/* allocate memory */
	gf_rows = malloc(rows_count*sizeof*gf_rows);
	if ( !gf_rows ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* reset */
	for ( i = 0; i < rows_count; i++ ) {
		gf_rows[i].mask = 0;
		gf_rows[i].similiar = INVALID_VALUE;
		gf_rows[i].stddev = INVALID_VALUE;
		gf_rows[i].filled = INVALID_VALUE;
		gf_rows[i].quality = INVALID_VALUE;
		gf_rows[i].time_window = 0;
		gf_rows[i].samples_count = 0;
		gf_rows[i].method = 0;
	}

	/* update mask and count valids TO FILL */
	valids_count = 0;
	for ( i = start_row; i < end_row; i++ ) {
		for ( c = 0; c < columns_count; c++ ) {
			if ( !IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[c]) ) {
				if ( tofill_column == c ) {
					gf_rows[i].mask |= GF_TOFILL_VALID;
				} else if ( value1_column == c ) {
					gf_rows[i].mask |= GF_VALUE1_VALID;
				} else if ( value2_column == c ) {
					gf_rows[i].mask |= GF_VALUE2_VALID;
				} else if ( value3_column == c ) {
					gf_rows[i].mask |= GF_VALUE3_VALID;
				}
			}
		}

		/* check for QC */
		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value1_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value1_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value1_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE1_VALID;
			}
		}

		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value2_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value2_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value2_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE2_VALID;
			}
		}

		if (	!IS_INVALID_VALUE(qc_thrs) &&
				(value3_qc_column != -1) &&
				!IS_INVALID_VALUE(((PREC *)(((char *)values)+i*struct_size))[value3_qc_column]) ) {
			if ( ((PREC *)(((char *)values)+i*struct_size))[value3_qc_column] > qc_thrs ) {
				gf_rows[i].mask &= ~GF_VALUE3_VALID;
			}
		}

		if ( IS_FLAG_SET(gf_rows[i].mask, GF_TOFILL_VALID) ) {
			++valids_count;
		}
	}

	if ( valids_count < values_min ) {
		puts(err_gf_too_less_values);
		free(gf_rows);
		return NULL;
	}

	/* */
	if ( IS_INVALID_VALUE(value1_tolerance_min) && IS_INVALID_VALUE(value1_tolerance_max) ) {
		value1_tolerance_min = GF_SW_IN_TOLERANCE_MIN;
		value1_tolerance_max = GF_SW_IN_TOLERANCE_MAX;
	}

	/* */
	if ( IS_INVALID_VALUE(value2_tolerance) ) {
		value2_tolerance = GF_TA_TOLERANCE;
	}

	/* */
	if ( IS_INVALID_VALUE(value3_tolerance) ) {
		value3_tolerance = GF_VPD_TOLERANCE;
	}

	/* loop for each row */
	for ( i = start_row; i < end_row; i++ ) {
		/* copy value from TOFILL to FILLED */
		gf_rows[i].filled = ((PREC *)(((char *)values)+i*struct_size))[tofill_column];

		/* compute hat ? */
		if ( !IS_INVALID_VALUE(gf_rows[i].filled) && !compute_hat ) {
			continue;
		}

		/*	fill
			Added 20140422: if a gap is impossible to fill, e.g. if with MDV there are no data in the whole dataset acquired in a range +/- one hour,
			the data point is not filled and the qc is set to -9999
		*/
		if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 7, 14, 7, GF_ALL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
			if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 7, 7, 7, GF_VALUE1_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
				if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 0, 2, 1, GF_TOFILL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
					if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 21, 77, 7, GF_ALL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
						if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 14, 77, 7, GF_VALUE1_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) )
							if ( !gapfill(values, struct_size, gf_rows, start_row, end_row, i, 3, 91, 3, GF_TOFILL_METHOD, hourly_dataset, value1_tolerance_min, value1_tolerance_max, value2_tolerance, value3_tolerance, tofill_column, value1_column, value2_column, value3_column) ) {
								++*no_gaps_filled_count;
								continue;
							}

		/* compute quality */
		gf_rows[i].quality =	(gf_rows[i].method > 0) +
								((gf_rows[i].method == 1 && gf_rows[i].time_window > 14) || (gf_rows[i].method == 2 && gf_rows[i].time_window > 14) || (gf_rows[i].method == 3 && gf_rows[i].time_window > 1)) +
								((gf_rows[i].method == 1 && gf_rows[i].time_window > 56) || (gf_rows[i].method == 2 && gf_rows[i].time_window > 28) || (gf_rows[i].method == 3 && gf_rows[i].time_window > 5));
	}

	/* ok */
	return gf_rows;
}

/* private function for parse_dd */
static int parse_time_zone(DD *const dd, char *const string) {
	int i;
	PREC v;
	int check;
	int error;
	char *token;
	char *p;
	char *temp;
	TIME_ZONE *time_zone;
	TIMESTAMP *t;

	/* timezone can be specified without timestamp, so we check if delimiter are present */
	temp = string_copy(string);
	if ( !temp ) {
		puts(err_out_of_memory);
		return 0;
	}
	token = string_tokenizer(temp, dd_field_delimiter, &p);
	if ( '\0' == p[0] ) {
		v = convert_string_to_prec(token, &error);
		if ( error ) {
			return 0;
		}
		dd->time_zones = malloc(sizeof*dd->time_zones);
		if ( !dd->time_zones ) {
			puts(err_out_of_memory);
			return 0;
		}
		dd->time_zones[0].timestamp.YYYY = dd->year;
		dd->time_zones[0].timestamp.MM = 1;
		dd->time_zones[0].timestamp.DD = 1;
		dd->time_zones[0].timestamp.hh = (HOURLY_TIMERES == dd->timeres) ? 1 : 0;
		dd->time_zones[0].timestamp.mm = (HOURLY_TIMERES == dd->timeres) ? 0 : 30;
		dd->time_zones[0].timestamp.ss = 0;
		dd->time_zones[0].v = v;
		dd->time_zones_count = 1;
		check = 0;
	} else {
		check = 0;
		t = NULL;
		for ( i = 0, token = string_tokenizer(string, dd_field_delimiter, &p); token; token = string_tokenizer(NULL, dd_field_delimiter, &p), ++i ) {
			if ( i & 1 ) {
				v = convert_string_to_prec(token, &error);
				if ( error ) {
					free(t);
					return 0;
				}
				time_zone = realloc(dd->time_zones, ++dd->time_zones_count*sizeof*time_zone);
				if ( !time_zone ) {
					puts(err_out_of_memory);
					--dd->time_zones_count;
					free(t);
					return 0;
				}
				dd->time_zones = time_zone;
				dd->time_zones[dd->time_zones_count-1].v = v;
				dd->time_zones[dd->time_zones_count-1].timestamp.YYYY = t->YYYY;
				dd->time_zones[dd->time_zones_count-1].timestamp.MM = t->MM;
				dd->time_zones[dd->time_zones_count-1].timestamp.DD = t->DD;
				dd->time_zones[dd->time_zones_count-1].timestamp.hh = t->hh;
				dd->time_zones[dd->time_zones_count-1].timestamp.mm = t->mm;
				dd->time_zones[dd->time_zones_count-1].timestamp.ss = t->ss;
				free(t);
				t = NULL;
			} else {
				t = get_timestamp(token);
				if  ( ! t ) {
					return 0;
				}
			}
			++check;
		}
		free(t);
	}

	/* */
	free(temp);

	/* */
	if( ! dd->time_zones_count ) {
		return 0;
	}

	/* */
	return !(check & 1);
}

/* private function for parse_dd */
static int parse_htower(DD *const dd, char *const string) {
	int i;
	PREC h;
	int check;
	int error;
	char *token;
	char *p;
	HEIGHT *htower;
	TIMESTAMP *t;

	check = 0;
	t = NULL;
	for ( i = 0, token = string_tokenizer(string, dd_field_delimiter, &p); token; token = string_tokenizer(NULL, dd_field_delimiter, &p), ++i ) {
		if ( i & 1 ) {
			h = convert_string_to_prec(token, &error);
			if ( error ) {
				free(t);
				return 0;
			}
			htower = realloc(dd->htower, ++dd->htower_count*sizeof*htower);
			if ( !htower ) {
				puts(err_out_of_memory);
				--dd->htower_count;
				free(t);
				return 0;
			}
			dd->htower = htower;
			dd->htower[dd->htower_count-1].h = h;
			dd->htower[dd->htower_count-1].timestamp.YYYY = t->YYYY;
			dd->htower[dd->htower_count-1].timestamp.MM = t->MM;
			dd->htower[dd->htower_count-1].timestamp.DD = t->DD;
			dd->htower[dd->htower_count-1].timestamp.hh = t->hh;
			dd->htower[dd->htower_count-1].timestamp.mm = t->mm;
			dd->htower[dd->htower_count-1].timestamp.ss = t->ss;
			free(t);
			t = NULL;
		} else {
			t = get_timestamp(token);
			if  ( ! t ) {
				return 0;
			}
		}
		++check;
	}
	free(t);

	/* */
	if( !dd->htower_count ) {
		return 0;
	}

	/* */
	return !(check & 1);
}

/* private function for parse_dd */
static int parse_sc_negles(DD *const dd, char *const string) {
	int i;
	int flag;
	int check;
	int error;
	char *token;
	char *p;
	SC_NEGL *sc_negles;
	TIMESTAMP *t;

	/* Sc_negl can be specified without timestamp, so we check if delimiter are present */
	token = string_tokenizer(string, dd_field_delimiter, &p);
	if ( '\0' == p[0] ) {
		flag = convert_string_to_int(token, &error);
		if ( error ) {
			return 0;
		}
		if ( (flag < 0) || (flag > 1) ) {
			printf("bad Sc_negl specified: %d\n", flag);
			return 0;
		}
		sc_negles = malloc(sizeof*sc_negles);
		if ( !sc_negles ) {
			puts(err_out_of_memory);
			return 0;
		}
		dd->sc_negles = sc_negles;
		dd->sc_negles[0].flag = flag;
		dd->sc_negles[0].timestamp.YYYY = dd->year;
		dd->sc_negles[0].timestamp.MM = 1;
		dd->sc_negles[0].timestamp.DD = 1;
		dd->sc_negles[0].timestamp.hh = (HOURLY_TIMERES == dd->timeres) ? 1 : 0;
		dd->sc_negles[0].timestamp.mm = (HOURLY_TIMERES == dd->timeres) ? 0 : 30;
		dd->sc_negles[0].timestamp.ss = 0;
		dd->sc_negles_count = 1;
		check  = 0;
	} else {
		check = 0;
		t = NULL;
		for ( i = 0, token = string_tokenizer(string, dd_field_delimiter, &p); token; token = string_tokenizer(NULL, dd_field_delimiter, &p), ++i ) {
			if ( i & 1 ) {
				flag = convert_string_to_int(token, &error);
				if ( error ) {
					free(t);
					return 0;
				}
				sc_negles = realloc(dd->sc_negles, ++dd->sc_negles_count*sizeof*sc_negles);
				if ( !sc_negles ) {
					puts(err_out_of_memory);
					--dd->sc_negles_count;
					free(t);
					return 0;
				}
				dd->sc_negles = sc_negles;
				dd->sc_negles[dd->sc_negles_count-1].flag = flag;
				dd->sc_negles[dd->sc_negles_count-1].timestamp.YYYY = t->YYYY;
				dd->sc_negles[dd->sc_negles_count-1].timestamp.MM = t->MM;
				dd->sc_negles[dd->sc_negles_count-1].timestamp.DD = t->DD;
				dd->sc_negles[dd->sc_negles_count-1].timestamp.hh = t->hh;
				dd->sc_negles[dd->sc_negles_count-1].timestamp.mm = t->mm;
				dd->sc_negles[dd->sc_negles_count-1].timestamp.ss = t->ss;
				free(t);
				t = NULL;
			} else {
				t = get_timestamp(token);
				if  ( ! t ) {
					return 0;
				}
			}
			++check;
		}
		free(t);
	}

	/* */
	if( !dd->sc_negles_count ) {
		return 0;
	}

	/* */
	return !(check & 1);
}


/* private function for parse_dd */
static int parse_timeres(DD *const dd, const char *const string) {
	int i;

	for ( i = 0; i < TIMERES_SIZE; i++ ) {
		if ( ! string_compare_i(string, timeress[i]) ) {
			dd->timeres = i;
			return 1;
		}
	}

	/* error */
	return 0;
}

/* */
void zero_dd(DD *const dd) {
	if ( dd ) {
		dd->site[0] = '\0';
		dd->year = -1;
		dd->lat = .0;
		dd->lon = .0;
		dd->time_zones = NULL;
		dd->time_zones_count = 0;
		dd->timeres = SPOT_TIMERES;
		dd->htower = NULL;
		dd->htower_count = 0;
		dd->sc_negles = NULL;
		dd->sc_negles_count = 0;
		dd->notes = NULL;
		dd->notes_count = 0;
	}
}

/* */
DD *alloc_dd(void) {
	DD *details;

	details = malloc(sizeof*details);
	if ( !details ) {
		puts(err_out_of_memory);
	} else {
		zero_dd(details);
	}
	return details;
}


/* */
void free_dd(DD *dd) {
	int i;

	if ( dd ) {
		free(dd->sc_negles);
		free(dd->htower);
		free(dd->time_zones);
		for ( i = 0; i < dd->notes_count; i++ ) {
			free(dd->notes[i]);
		}
		free(dd->notes);
		free(dd);
	}
}

/* */
DD *parse_dd(FILE *const f) {
	int i;
	int error;
	int index;
	double v;
	char *buffer;
	char *token;
	char *p;
	char **ppchar_no_leak;
	DD *dd;

	/* */
	assert(f);

	/* */
	buffer = malloc(HUGE_BUFFER_SIZE*sizeof*buffer);
	if ( !buffer ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* */
	dd = malloc(sizeof*dd);
	if ( !dd ) {
		puts(err_out_of_memory);
		free(buffer);
		return NULL;
	}
	zero_dd(dd);

	/* parse dataset details */
	index = 0;
	while ( get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE) ) {
		token = string_tokenizer(buffer, dd_field_delimiter, &p);
		/*
		if ( (SC_NEGL_DETAIL == index) && mystricmp(token, dds[index]) ) {
			++index;
		}
		*/
		if ( string_compare_i(token, dds[index]) ) {
			if ( (NOTES_DETAIL == index ) && ( dd->notes_count >= 1) ) {
				break;
			}
			printf("no '%s' keyword found.\n", dds[index]);
			free(buffer);
			free_dd(dd);
			return NULL;
		}

		/* */
		switch ( index ) {
			case SITE_DETAIL:
				token = string_tokenizer(NULL, dd_field_delimiter, &p);
				for ( i = 0; token[i]; i++ );
				if ( (i != SITE_LEN-1) || token[2] != '-' ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return 0;
				}
				strcpy(dd->site, token);
				dd->site[SITE_LEN-1] = '\0';
			break;

			case YEAR_DETAIL:
				token = string_tokenizer(NULL, dd_field_delimiter, &p);
				i = convert_string_to_int(token, &error);
				if ( error ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return NULL;
				}
				dd->year = i;
			break;

			case LAT_DETAIL:
				token = string_tokenizer(NULL, dd_field_delimiter, &p);
				v = convert_string_to_prec(token, &error);
				if ( error ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return NULL;
				}
				dd->lat = v;
			break;

			case LON_DETAIL:
				token = string_tokenizer(NULL, dd_field_delimiter, &p);
				v = convert_string_to_prec(token, &error);
				if ( error ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return NULL;
				}
				dd->lon = v;
			break;

			case TIMEZONE_DETAIL:
				if ( !parse_time_zone(dd, p) ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return NULL;
				}
			break;

			case HTOWER_DETAIL:
				if ( !parse_htower(dd, p) ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return NULL;
				}
			break;

			case TIMERES_DETAIL:
				token = string_tokenizer(NULL, dd_field_delimiter, &p);
				if ( !parse_timeres(dd, token) ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return NULL;
				}
			break;

			case SC_NEGL_DETAIL:
				if ( ! parse_sc_negles(dd, p) ) {
					printf("bad '%s' specified\n", dds[index]);
					free(buffer);
					free_dd(dd);
					return NULL;
				}
			break;

			case NOTES_DETAIL:
				token = string_tokenizer(NULL, dd_field_delimiter, &p);
				ppchar_no_leak = realloc(dd->notes, ++dd->notes_count*sizeof*dd->notes);
				if ( !ppchar_no_leak ) {
					puts(err_out_of_memory);
					--dd->notes_count;
					free(buffer);
					free_dd(dd);
					return NULL;
				}
				dd->notes = ppchar_no_leak;
				dd->notes[dd->notes_count-1] = string_copy(token);
				if ( !dd->notes[dd->notes_count-1] ) {
					puts(err_out_of_memory);
					--dd->notes_count;
					free(buffer);
					free_dd(dd);
					return NULL;
				}
			break;
		}

		if ( index < NOTES_DETAIL ) {
			++index;
		}
	}

	/* rewind file */
	fseek(f, 0, SEEK_SET);

	/* */
	index = DETAILS_SIZE - 1 + dd->notes_count;
	for ( i = 0; i < index; i++ ) {
		get_valid_line_from_file(f, buffer, HUGE_BUFFER_SIZE);
	}

	/* free memory */
	free(buffer);

	/* sort timestamps */
	qsort(dd->time_zones, dd->time_zones_count, sizeof *dd->time_zones, compare_time_zones);
	qsort(dd->htower, dd->htower_count, sizeof *dd->htower, compare_htower);
	qsort(dd->sc_negles, dd->sc_negles_count, sizeof *dd->sc_negles, compare_sc_negles);
	
	/* ok */
	return dd;
}

int write_dd(const DD *const dd, FILE *const f, const char *const notes_to_add) {
	int i;

	/* */
	assert(dd && f);

	/* */
	fprintf(f, "%s,%s\n", dds[SITE_DETAIL], dd->site);
	fprintf(f, "%s,%d\n", dds[YEAR_DETAIL], dd->year);
	fprintf(f, "%s,%g\n", dds[LAT_DETAIL], dd->lat);
	fprintf(f, "%s,%g\n", dds[LON_DETAIL], dd->lon);
	fprintf(f, "%s", dds[TIMEZONE_DETAIL]);
	for ( i = 0; i < dd->time_zones_count; i++ ) {
		fprintf(f, ",%04d%02d%02d%02d%02d,%g",	dd->time_zones[i].timestamp.YYYY,
												dd->time_zones[i].timestamp.MM,
												dd->time_zones[i].timestamp.DD,
												dd->time_zones[i].timestamp.hh,
												dd->time_zones[i].timestamp.mm,
												dd->time_zones[i].v
		);
	}
	fputs("\n", f);
	fprintf(f, "%s", dds[HTOWER_DETAIL]);
	for ( i = 0; i < dd->htower_count; i++ ) {
		fprintf(f, ",%04d%02d%02d%02d%02d,%g",	dd->htower[i].timestamp.YYYY,
												dd->htower[i].timestamp.MM,
												dd->htower[i].timestamp.DD,
												dd->htower[i].timestamp.hh,
												dd->htower[i].timestamp.mm,
												dd->htower[i].h
		);
	}
	fputs("\n", f);
	fprintf(f, "%s,%s\n", dds[TIMERES_DETAIL], timeress[dd->timeres]);

	fprintf(f, "%s,%d", dds[SC_NEGL_DETAIL], dd->sc_negles[0].flag);
	/*
	for ( i = 0; i < dd->sc_negles_count; i++ ) {
		fprintf(f, ",%04d%02d%02d%02d%02d,%d",	dd->sc_negles[i].timestamp.YYYY,
												dd->sc_negles[i].timestamp.MM,
												dd->sc_negles[i].timestamp.DD,
												dd->sc_negles[i].timestamp.hh,
												dd->sc_negles[i].timestamp.mm,
												dd->sc_negles[i].flag
		);
	}
	*/
	fputs("\n", f);

	if ( notes_to_add ) {
		fprintf(f, "%s,%s\n", dds[NOTES_DETAIL], notes_to_add);
	}
	for ( i = 0; i < dd->notes_count; i++ ) {
		fprintf(f, "%s,%s\n", dds[NOTES_DETAIL], dd->notes[i]);
	}

	/* ok */
	return 1;
}

/* */
int write_dds(const DD **const dd, const int count, FILE *const f, const char *const notes_to_add) {
	int i;
	int y;

	/* */
	assert(dd && f);

	/* */
	fputs(dds[SITE_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			fprintf(f, ",%s", dd[y]->site);
		}
	}
	fputs("\n", f);

	fputs(dds[YEAR_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			fprintf(f, ",%d", dd[y]->year);
		}
	}
	fputs("\n", f);

	fputs(dds[LAT_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			fprintf(f, ",%g", dd[y]->lat);
		}
	}
	fputs("\n", f);

	fputs(dds[LON_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			fprintf(f, ",%g", dd[y]->lon);
		}
	}
	fputs("\n", f);

	fputs(dds[TIMEZONE_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			for ( i = 0; i < dd[y]->time_zones_count; i++ ) {
				fprintf(f, ",%04d%02d%02d%02d%02d,%g",	dd[y]->time_zones[i].timestamp.YYYY,
														dd[y]->time_zones[i].timestamp.MM,
														dd[y]->time_zones[i].timestamp.DD,
														dd[y]->time_zones[i].timestamp.hh,
														dd[y]->time_zones[i].timestamp.mm,
														dd[y]->time_zones[i].v
				);
			}
		}
	}
	fputs("\n", f);

	fputs(dds[HTOWER_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			for ( i = 0; i < dd[y]->htower_count; i++ ) {
				fprintf(f, ",%04d%02d%02d%02d%02d,%g",	dd[y]->htower[i].timestamp.YYYY,
														dd[y]->htower[i].timestamp.MM,
														dd[y]->htower[i].timestamp.DD,
														dd[y]->htower[i].timestamp.hh,
														dd[y]->htower[i].timestamp.mm,
														dd[y]->htower[i].h
				);
			}
		}
	}
	fputs("\n", f);

	fputs(dds[TIMERES_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			fprintf(f, ",%s", timeress[dd[y]->timeres]);
		}
	}
	fputs("\n", f);

	fputs(dds[SC_NEGL_DETAIL], f);
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			for ( i = 0; i < dd[y]->sc_negles_count; i++ ) {
				fprintf(f, ",%04d%02d%02d%02d%02d,%d",	dd[y]->sc_negles[i].timestamp.YYYY,
														dd[y]->sc_negles[i].timestamp.MM,
														dd[y]->sc_negles[i].timestamp.DD,
														dd[y]->sc_negles[i].timestamp.hh,
														dd[y]->sc_negles[i].timestamp.mm,
														dd[y]->sc_negles[i].flag
				);
			}
		}
	}
	fputs("\n", f);

	/* write notes to add */
	if ( notes_to_add ) {
		fprintf(f, "notes,%s\n", notes_to_add);
	}

	/* write notes */
	for ( y = 0; y < count; y++ ) {
		if ( dd[y]->site ) {
			for ( i = 0; i < dd[y]->notes_count; i++ ) {
				fprintf(f, "notes,%s\n", dd[y]->notes[i]);
			}
		}
	}

	/* ok */
	return 1;
}

/* */
char *get_datetime_in_timestamp_format(void) {
	const char timestamp_format[] = "%04d%02d%02d%02d%02d%02d";
	static char buffer[14 + 1];
#if defined (_WIN32)
	SYSTEMTIME st;

	GetLocalTime(&st);
	sprintf(buffer, timestamp_format,	st.wYear,
										st.wMonth,
										st.wDay,
										st.wHour,
										st.wMinute,
										st.wSecond
	);
#elif defined (linux) || defined (__linux) || defined (__linux__) || defined (__APPLE__)
    struct timeval tval;
    struct tm *time;
    if (gettimeofday(&tval, NULL) != 0) {
        fprintf(stderr, "Fail of gettimeofday\n");
        return buffer;
    }
    time = localtime(&tval.tv_sec);
    if (time == NULL) {
        fprintf(stderr, "Fail of localtime\n");
        return buffer;
    }

    sprintf(buffer, timestamp_format,
            time->tm_year + 1900,
            time->tm_mon,
            time->tm_mday,
            time->tm_hour,
            time->tm_min,
            time->tm_sec
	);
#endif
	return buffer;
}

/* */
char *get_timeres_in_string(int timeres) {
	if ( (timeres < 0) || (timeres >= TIMERES_SIZE) ) {
		return NULL;
	}

	switch ( timeres ) {
		case SPOT_TIMERES: return "spot";
		case QUATERHOURLY_TIMERES: return "quaterhourly";
		case HALFHOURLY_TIMERES: return "halfhourly";
		case HOURLY_TIMERES: return "hourly";
		case DAILY_TIMERES: return "daily";
		case MONTHLY_TIMERES: return "monthly";
		default: return NULL;
	}
}

/* */
int get_valid_line_from_file(FILE *const f, char *buffer, const int size) {
	int i;

	if ( !f || !buffer || !size ) {
		return 0;
	}

	buffer[0] = '\0';
	while ( 1 ) {
		if ( ! fgets(buffer, size, f) ) {
			return 0;
		}

		/* remove carriage return and newline */
		for ( i = 0; buffer[i]; i++ ) {
			if ( ('\r' == buffer[i]) || ('\n' == buffer[i]) ) {
				buffer[i] = '\0';
				break;
			}
		}

		/* skip empty line */
		if ( buffer[0] != '\0' ) {
			break;
		}
	}
	return 1;
}

/* */
int get_rows_count_from_file( FILE *const f) {
	int i;
	int rows_count;
	char buffer[HUGE_BUFFER_SIZE];

	if ( !f ) {
		return -1;
	}

	rows_count = 0;
	while ( 1 ) {
		if ( !fgets(buffer, HUGE_BUFFER_SIZE, f) ) {
			break;
		}

		/* remove carriage return and newline */
		for ( i = 0; buffer[i]; i++ ) {
			if ( ('\r' == buffer[i]) || ('\n' == buffer[i]) ) {
				buffer[i] = '\0';
				break;
			}
		}

		/* skip empty line */
		if ( '\0' == buffer[0] ) {
			continue;
		}

		++rows_count;
	}
	return rows_count;
}

/* */
int get_rows_count_by_dd(const DD *const dd) {
	int leap_year;

	assert(dd);

	leap_year = IS_LEAP_YEAR(dd->year);
	switch ( dd->timeres ) {
		case QUATERHOURLY_TIMERES:	return 24*4*(365+leap_year);
		case HALFHOURLY_TIMERES:	return 24*2*(365+leap_year);
		case HOURLY_TIMERES:		return 24*(365+leap_year);
		case DAILY_TIMERES:			return 365+leap_year;
		case MONTHLY_TIMERES:		return 12;
		default:					return 0;
	}
}

/* */
int get_rows_per_day_by_dd(const DD *const dd) {
	assert(dd);

	switch ( dd->timeres ) {
		case QUATERHOURLY_TIMERES:	return 24*4;
		case HALFHOURLY_TIMERES:	return 24*2;
		case HOURLY_TIMERES:		return 24;
		case DAILY_TIMERES:			return 1;
		default:					return 0;
	}
}

/* row is zero based index */
PREC get_dtime_by_row(const int row, const int hourly) {
	int i;
	PREC d;
	int row_per_day;
	int row_max;
	const PREC decimal_part_dtime[] = {
		0.02083,
		0.04167,
		0.0625,
		0.08333,
		0.10417,
		0.125,
		0.14583,
		0.16667,
		0.1875,
		0.20833,
		0.22917,
		0.25,
		0.27083,
		0.29167,
		0.3125,
		0.33333,
		0.35417,
		0.375,
		0.39583,
		0.41667,
		0.4375,
		0.45833,
		0.47917,
		0.5,
		0.52083,
		0.54167,
		0.5625,
		0.58333,
		0.60417,
		0.625,
		0.64583,
		0.66667,
		0.6875,
		0.70833,
		0.72917,
		0.75,
		0.77083,
		0.79167,
		0.8125,
		0.83333,
		0.85417,
		0.875,
		0.89583,
		0.91667,
		0.9375,
		0.95833,
		0.97917,
		1,
	};

	row_max = LEAP_YEAR_ROWS;
	if ( hourly ) {
		row_max /= 2;
	}

	assert((row >= 0) && ( row < row_max));

	row_per_day = hourly ? 24 : 48;

	d = (int)row / row_per_day + 1;
	i = row % row_per_day;
	if ( hourly ) {
		i *= 2;
		++i;
	}

	return d + decimal_part_dtime[i];
}

/*

	NOON COMPUTATION BLOCK
	contains functions from IDL code by Ankur Desai...
	original notes reports:

	;Sunrise, Sunset, Solar noon calculator
	;Source: http://www.srrb.noaa.gov/highlights/sunrise/sunrise.html
	;Converted to IDL by Ankur Desai, 7 April 2003

*/

/* */
static double calcJD(int year, int month, int day) {
	double A;
	double B;
	double JD;

	if ( month <= 2 ) {
		year -= 1;
		month += 12;
	}

	A = floor((double)year/100);
	B = 2 - A + floor((double)A/4);
	JD = floor(365.25*(year + 4716)) + floor(30.6001*(month+1)) + day + B - 1524.5;

	/* */
	return JD;
}

/* convert radian angle to degrees */
static double radToDeg(const double angleRad) {
	return (180.0 * angleRad / M_PI);
}

/* convert degree angle to radians */
static double degToRad(const double angleDeg) {
	return (M_PI * angleDeg / 180.0);
}

/* */
static double calcTimeJulianCent(const double jd) {
	return (jd - 2451545.0) / 36525.0;
}

/* */
static double calcJDFromJulianCent(const double t) {
	return t * 36525.0 + 2451545.0;
}

/* */
static double calcGeomMeanLongSun(const double t) {
	double L0;

	L0 = 280.46646 + t * (36000.76983 + 0.0003032 * t);
	while ( L0 > 360.0 ) {
	    L0 -= 360.0;
	}

	while ( L0 < 0.0 ) {
	    L0 += 360.0;
	}

	return L0;	/* in degrees */
}

/* */
static double calcGeomMeanAnomalySun(const double t) {
	return 357.52911 + t * (35999.05029 - 0.0001537 * t);		/* in degrees */
}

/* */
static double calcEccentricityEarthOrbit(const double t) {
	return 0.016708634 - t * (0.000042037 + 0.0000001267 * t);	/* unitless */
}

/* */
static double calcMeanObliquityOfEcliptic(const double t) {
	double seconds;
	double e0;

    seconds = 21.448 - t*(46.8150 + t*(0.00059 - t*(0.001813)));
    e0 = 23.0 + (26.0 + (seconds/60.0))/60.0;

    return e0;		/* in degrees */
}

/* */
static double calcObliquityCorrection(const double t) {
	double e0;
	double omega;
	double e;

	e0 = calcMeanObliquityOfEcliptic(t);
	omega = 125.04 - 1934.136 * t;
	e = e0 + 0.00256 * cos(degToRad(omega));

	return e;		/* in degrees */
}

/* */
static double calcEquationOfTime(const double t) {
	double epsilon;
	double l0;
	double e;
	double m;
	double y;
	double sin2l0;
	double sinm;
	double cos2l0;
	double sin4l0;
	double sin2m;
	double Etime;

	epsilon = calcObliquityCorrection(t);
	l0 = calcGeomMeanLongSun(t);
	e = calcEccentricityEarthOrbit(t);
	m = calcGeomMeanAnomalySun(t);
	y = tan(degToRad(epsilon)/2.0);
	y *= y;

	sin2l0 = sin(2.0 * degToRad(l0));
	sinm = sin(degToRad(m));
	cos2l0 = cos(2.0 * degToRad(l0));
	sin4l0 = sin(4.0 * degToRad(l0));
	sin2m  = sin(2.0 * degToRad(m));

	Etime = y * sin2l0 - 2.0 * e * sinm + 4.0 * e * y * sinm * cos2l0
			- 0.5 * y * y * sin4l0 - 1.25 * e * e * sin2m;

	return radToDeg(Etime)*4.0;		/* in minutes of time */
}

/* */
static double calcSolNoonUTC(const double t, const double longitude) {
	double tnoon;
	double eqTime;
	double solNoonUTC;
	double newt;

	/* First pass uses approximate solar noon to calculate eqtime */
	tnoon = calcTimeJulianCent(calcJDFromJulianCent(t) + longitude/360.0);
	eqTime = calcEquationOfTime(tnoon);
	solNoonUTC = 720 + (longitude * 4) - eqTime;	/* min */

	newt = calcTimeJulianCent(calcJDFromJulianCent(t) -0.5 + solNoonUTC/1440.0);

	eqTime = calcEquationOfTime(newt);
	solNoonUTC = 720 + (longitude * 4) - eqTime;	/* min */

	return solNoonUTC;
}

/* */
static void get_solar_noon(const int year, const int month, const int day, const double longitude, const double zone, const int day_saving, int *const hour, int *const minute, int *const second) {
	double floatHour;
	double floatMinute;
	double floatSec;
	double jd;
	double t;
	double noon;

	jd = calcJD(year, month, day);
	t = calcTimeJulianCent(jd);

	noon = calcSolNoonUTC(t, longitude) - (60 * zone) + (60 * day_saving);

	floatHour = noon / 60.0;
	*hour = (int)floor(floatHour);
	floatMinute = 60.0 * (floatHour - floor(floatHour));
	*minute = (int)floor(floatMinute);
	floatSec = 60.0 * (floatMinute - floor(floatMinute));
	*second = (int)floor(floatSec + 0.5);
	if ( *second > 59 ) {
		*second = 0;
		*minute += 1;
	}
}

/*

	END OF NOON COMPUTATION BLOCK

*/


/*

	RPOT COMPUTATION BLOCK

*/

/* */
static void get_month_and_day_by_row(const int row, const int year, int *const month, int *const day) {
	int monthdays;
	int is_leap;
	int days_in_month[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

	/* reset */
	*day = 0;
	*month = 0;
	monthdays = 0;

	is_leap = IS_LEAP_YEAR(year);

	/* check */
	if ( (row <= 0) || (row > 365 + is_leap) ) {
		return;
	}

	/* */
	if ( is_leap ) {
		++days_in_month[1];
	}

	/* */
	while ( row > monthdays ) {
		monthdays += days_in_month[(*month)++];
	}
    *day = row - monthdays + days_in_month[*month-1];
}

/* */
static void shift(double *rpots_daily, const int hroz) {
	int i;
	int y;
	int row;

	if ( 720 == hroz ) {
		return;
	}

	row = hroz - 720;

	if ( row > 0 ) {
		for ( i = 0; i < row; i++ ) {
			for ( y = 1440-1; y > 0; y-- ) {
				rpots_daily[y] = rpots_daily[y-1];
			}
			rpots_daily[y] = 0;
		}
	} else {
		row *= -1;
		for ( i = 0; i < row; i++ ) {
			for ( y = 1; y < 1440; y++ ) {
				rpots_daily[y-1] = rpots_daily[y];
			}
			rpots_daily[y-1] = 0;
		}
	}
}

/* */
static int shift_by_2(double *rpots_daily, const int rpots_daily_count, const int hroz, const int hroz2, const int new_tz_index) {
	int i;
	int y;
	int row;
	double *shift2;

	/* alloc memory */
	shift2 = malloc(rpots_daily_count*sizeof*shift2);
	if ( !shift2 ) {
		puts(err_out_of_memory);
		return 0;
	}

	/* copy values */
	for ( i = 0; i < rpots_daily_count; i++ ) {
		shift2[i] = rpots_daily[i];
	}

	if ( 720 != hroz ) {
		row = hroz - 720;

		if ( row > 0 ) {
			for ( i = 0; i < row; i++ ) {
				for ( y = 1440-1; y > 0; y-- ) {
					rpots_daily[y] = rpots_daily[y-1];
				}
				rpots_daily[y] = 0;
			}
		} else {
			row *= -1;
			for ( i = 0; i < row; i++ ) {
				for ( y = 1; y < 1440; y++ ) {
					rpots_daily[y-1] = rpots_daily[y];
				}
				rpots_daily[y-1] = 0;
			}
		}
	}

	if ( 720 != hroz2 ) {
		row = hroz2 - 720;

		if ( row > 0 ) {
			for ( i = 0; i < row; i++ ) {
				for ( y = 1440-1; y > 0; y-- ) {
					shift2[y] = shift2[y-1];
				}
				shift2[y] = 0;
			}
		} else {
			row *= -1;
			for ( i = 0; i < row; i++ ) {
				for ( y = 1; y < 1440; y++ ) {
					shift2[y-1] = shift2[y];
				}
				shift2[y-1] = 0;
			}
		}
	}

	/* aggregate */
	for ( i = new_tz_index; i < rpots_daily_count; i++ ) {
		rpots_daily[i] = shift2[i];
	}

	/* free memory */
	free(shift2);
	
	/* ok */
	return 1;
}

/* based on rg_pot function on ECOFRUNC.PRO (markus code ?) */
static double get_daily_rpot(const double latitude, const double longitude, const int d_, const double t_) {
	double localstandardtime;
	double localapparentsolartime;
	double tthet;
	double signedLAS;
	double omega;
	double decl_rad;
	double lat_rad;
	double theta_rad;
	double Rpot;
	double Rpot_h;

	const double pi = 3.141592654;
	const double solarconst = 1376.;

	localstandardtime = t_;
	tthet = 2.*pi*(d_-1.) / 365.;

	localapparentsolartime = localstandardtime;
	signedLAS = 12.-localapparentsolartime;
	signedLAS = fabs(signedLAS);

	omega = -15.*signedLAS;
	decl_rad = 0.006918-0.399912*cos(tthet)+0.070257*sin(tthet)-0.006758*cos(2*tthet)+0.000907*sin(2*tthet)-0.002697*cos(3*tthet)+0.00148*sin(3*tthet);
	lat_rad = latitude*pi/180.;

	theta_rad = acos(sin(decl_rad)*sin(lat_rad)+cos(decl_rad)*cos(lat_rad)*cos(omega*pi/180.));

	Rpot = solarconst*(1.00011+0.034221*cos(tthet)+0.00128*sin(tthet)+0.000719*cos(2*tthet)+0.000077*sin(2*tthet));
	Rpot_h = Rpot*cos(theta_rad);

	return (Rpot_h > 0) ? Rpot_h : 0.0;
}

/* */
PREC *get_rpot_with_solar_noon(DD *const details, const int s_n_month, const int s_n_day, int *const solar_noon) {
	int i;
	int y;
	int row;
	int hour;
	int minute;
	int second;
	int day;
	int month;
	int year;
	int rows_per_day;
	int rows_count;
	int rpot_rows_count;
	int aggr_rows;
	int hroz;
	int hroz2;
	int day_saving;
	int time_zone_next_index;
	float time_zone;
	double longitude;
	double doy;
	double hrs;
	double mean;
	double *rpots_daily;
	double *rpots;

	/* */
	assert(details);

	/* reset */
	if ( solar_noon ) {
		*solar_noon = INVALID_VALUE;
	}

	/* 60 * 24...rpot is computed for each minute */
	rows_per_day = 1440;

	year = details->year;
	time_zone = details->time_zones[0].v * -1;
	longitude = details->lon * -1;
	day_saving = 0;

	rows_count = IS_LEAP_YEAR(details->year) ? 366 : 365;
	aggr_rows = (HOURLY_TIMERES == details->timeres) ? 60: 30;
	rpot_rows_count = rows_count * rows_per_day / aggr_rows;

	/* */
	rpots = malloc(rpot_rows_count*sizeof*rpots);
	if ( !rpots ) {
		puts(err_out_of_memory);
		return NULL;
	}

	/* */
	rpots_daily = malloc(sizeof*rpots_daily*rows_per_day);
	if ( !rpots_daily ) {
		puts(err_out_of_memory);
		free(rpots);
		return NULL;
	}

	/* */
	time_zone_next_index = (details->time_zones_count > 1) ? 1: 0;
	for ( row = 0; row < rows_count; row++ ) {
		for ( i = 0; i < rows_per_day; i++ ) {
			doy = ((double)(row*rows_per_day+i) / rows_per_day) + 1;
			hrs = (double)((row*rows_per_day+i) % rows_per_day) / 60.;
			rpots_daily[i] = get_daily_rpot(details->lat, longitude, doy, hrs);
		}

		get_month_and_day_by_row(row+1, year, &month, &day);

		if (	time_zone_next_index &&
				(details->time_zones[time_zone_next_index].timestamp.MM == month) &&
				(details->time_zones[time_zone_next_index].timestamp.DD == day) ) {
			get_solar_noon(year, month, day, longitude, time_zone, day_saving, &hour, &minute, &second);
			hroz = 60*hour+minute;
			time_zone = details->time_zones[time_zone_next_index].v * -1;
			i = 60*details->time_zones[time_zone_next_index].timestamp.hh+details->time_zones[time_zone_next_index].timestamp.mm;
			if ( ++time_zone_next_index >= details->time_zones_count ) {
				time_zone_next_index = 0;
			}
			get_solar_noon(year, month, day, longitude, time_zone, day_saving, &hour, &minute, &second);
			if ( solar_noon && (s_n_month == month) && (s_n_day == day) ) {
				*solar_noon = hour * 10000 + minute * 100 + second;
			}
			hroz2 = 60*hour+minute;			
			shift_by_2(rpots_daily, rows_per_day, hroz, hroz2, i);
		} else {
			get_solar_noon(year, month, day, longitude, time_zone, day_saving, &hour, &minute, &second);
			if ( solar_noon && (s_n_month == month) && (s_n_day == day) ) {
				*solar_noon = hour * 10000 + minute * 100 + second;
			}
			hroz = 60*hour+minute;
			shift(rpots_daily, hroz);
		}

		/* aggregated */
		for ( i = 0; i < rows_per_day / aggr_rows; i++ ) {
			mean = 0.;
			for ( y = 0; y < aggr_rows; y++ ) {
				mean += rpots_daily[i*aggr_rows+y];
			}
			mean /= aggr_rows;
			rpots[row*(rows_per_day / aggr_rows)+i] = mean;
		}
	}

	/* free memory */
	free(rpots_daily);

	/* ok */
	return rpots;
}

/* */
PREC *get_rpot(DD *const details) {
	return get_rpot_with_solar_noon(details, 0, 0, NULL);
}

/*

	END OF RPOT COMPUTATION BLOCK

*/

void check_memory_leak(void) {
#ifdef _DEBUG
#if _WIN32
	_CrtSetReportMode(_CRT_WARN, _CRTDBG_MODE_DEBUG);
	_CrtSetReportMode(_CRT_ERROR, _CRTDBG_MODE_DEBUG);
	_CrtSetReportMode(_CRT_ASSERT, _CRTDBG_MODE_DEBUG);
	_CrtDumpMemoryLeaks();
#else /* _WIN32 */
	assert(0 && "no memory leak available for this platform");
#endif
#endif /* _DEBUG */
}

/* return -2 on error, -1 if not found */
int get_column_of(const char *const buffer, const char *const delimiter, const char * const string) {
	char *buffer_copy;
	char *p;
	char *token;
	int i;
	int ret;

	buffer_copy = string_copy(buffer);
	if ( ! buffer_copy) {
		return -2;
	}

	ret = -1;
	for ( i = 0, token = string_tokenizer(buffer_copy, delimiter, &p); token; token = string_tokenizer(NULL, delimiter, &p), ++i ) {
		if ( ! string_compare_i(token, string) ) {
			ret = i;
			break;
		}
	}
	free(buffer_copy);
	return ret;
}
