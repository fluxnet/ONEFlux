/*
	compiler.h

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#ifndef COMPILER_H
#define COMPILER_H

/* */
#if defined (__GNUC__)
	#define COMPILER "GNU C "__VERSION__
#elif defined (__LCC__)
	#define COMPILER "LCC"
#elif defined (__POCC__)
	#define COMPILER "PellesC"
#elif defined (_MSC_VER )
	#if _MSC_VER == 1200
		#define COMPILER "Ms VC++ 6.0"
	#elif _MSC_VER == 1300
		#define COMPILER "Ms VC++ 7.0"
	#elif _MSC_VER == 1310
		#define COMPILER "Ms VC++ 7.1"
	#elif _MSC_VER == 1400
		#define COMPILER "Ms VC++ 8.0"
	#elif _MSC_VER == 1500
		#define COMPILER "Ms VC++ 9.0"
	#else
		#define COMPILER "Ms VC++ Compiler"
	#endif
#else
	#define COMPILER "unknown"
#endif

/* */
#endif /* COMPILER_H */ 
