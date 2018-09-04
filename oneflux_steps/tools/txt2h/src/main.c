/*
	main.c

	this file is part of txt2h

	author: Alessio Ribeca <a.ribeca@unitus.it>
	owner: DIBAF - University of Tuscia, Viterbo, Italy

	scientific contact: Dario Papale <darpap@unitus.it>
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "../../../common/common.h"

/* */
static const char usage[] =	"usage: txt2h <inputfile> {outputfolder} <symbol>\n";
static const char missing_parameters[] = "missing parameters!";
static const char header[] =	""
								"/*\n"
								"	%s.h\n\n"
								"	author: Alessio Ribeca <a.ribeca@unitus.it>\n"
								"	owner: DIBAF - University of Tuscia, Viterbo, Italy\n\n"
								"	scientific contact: Dario Papale <darpap@unitus.it>\n\n"
								"	please note this is an automatically generated file\n"
								"	created with txt2h on %s\n"
								"*/\n\n"
;

/* */
char *get_date_time(void) {
	static char buffer[12+1];

	time_t t = time(NULL);
	struct tm tm = *localtime(&t);

	sprintf(buffer, "%04d%02d%02d%02d%02d", tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday, tm.tm_hour, tm.tm_min);

	return buffer;
}

/* */
int load_file_to_memory(const char *filename, char **result) {
	size_t size;
	FILE *f;

	size = 0;
	f = fopen(filename, "rb");
	if ( !f )  {
		*result = NULL;
		printf("unable to open %s\n", filename);
		return 0;
	}
	fseek(f, 0, SEEK_END);
	size = ftell(f);
	fseek(f, 0, SEEK_SET);
	*result = (char *)malloc((size+1)*sizeof**result);
	if ( ! *result ) {
		puts(err_out_of_memory);
		fclose(f);
		return 0;
	}
	if ( size != fread(*result, sizeof(char), size, f) )  {
		printf("unable to read %s\n", filename);
		fclose(f);
		free(*result);
		return 0;
	}
	fclose(f);
	(*result)[size] = '\0';

	return size;
}

/* */
int main(int argc, char *argv[]) {
	unsigned char *mem;
	char *input_file;
	char *output_path;
	char *symbol;
	char buffer[256];
	int err;
	size_t i;	
	size_t size;
	FILE *f;

	/* init */
	mem = NULL;
	err = 1;

	/* check args */
	if ( argc < 3 ) {
		puts(missing_parameters);
		puts(usage);
		goto end;
	}

	input_file = argv[1];
	if ( argc < 3 ) {
		output_path = NULL;
		symbol = argv[2];
	} else {
		output_path = argv[2];
		symbol = argv[3];
	}

	/* import file */
	size = load_file_to_memory(input_file, &mem);
	if ( ! mem ) {
		goto end;
	}

	/* */
	if ( ! output_path ) {
		sprintf(buffer, "%s.h", symbol); 
	} else {
		char arr[] = { FOLDER_DELIMITER, 0 };
		for ( i = 0; output_path[i]; ++i );
		sprintf(buffer, "%s%s%s.h", output_path, (output_path[i-1] == FOLDER_DELIMITER) ? "" : arr, symbol);
	}

	/* create filename */
	f = fopen(buffer, "wb");
	if ( ! f ) {
		printf("unable to create %s\n", buffer);
		goto end;
	}

	/* write header */
	fprintf(f, header, symbol, get_date_time());

	/* write var declaration */
	fprintf(f, "const unsigned char %s[] = {\n\n\t", symbol);

	/* write */
	for ( i = 0; i < size; i++ ) {
		if ( i && ! (i % 8) ) {
			fputs("\n\t", f);
		}
		fprintf(f, "0x%02X, ", mem[i]);
	}
	if ( ! (i % 8) ) {
		fputs("\n\t", f);
	}
	fputs("0x00\n};\n", f);
	fclose(f);

	/* ok */
	printf("successfully created %s.h\n", symbol);
	err = 0;

end:

	/* free memory */
	free(mem);

	/* ok ? */
	return err;
}
