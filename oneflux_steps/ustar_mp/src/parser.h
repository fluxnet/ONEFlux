/*
	parser.h

	this file is part of ustar_mp

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef PARSER_H
#define PARSER_H

/* includes */
#include "types.h"

/* prototypes */
SEASONS_GROUP *parse_seasons_group(const char *const string, int *const seasons_group_count);
void free_seasons_group(SEASONS_GROUP *seasons_group, const int seasons_group_count);

/* */
#endif
