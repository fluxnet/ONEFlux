# enables most optimization flags
CC := gcc -O3

TMETEO_PROC-DATASET_SRC := tMeteo_proc-dataset.c
TMETEO_PROC-DATASET_OBJ := $(TMETEO_PROC-DATASET_SRC:.c=.o)
TMETEO_PROC-DATASET_BIN := $(join ${TGTDIR}, test_meteo_proc-dataset)
	
${TMETEO_PROC-DATASET_BIN}:
	@echo "Building ${TMETEO_PROC-DATASET_BIN}..."
	${CC} -w -c ${TMETEO_PROC-DATASET_SRC} ;\
	${CC} ${TMETEO_PROC-DATASET_OBJ} -w -lm -o ${TMETEO_PROC-DATASET_BIN}

clean:
	@echo "Cleaning up..."
	rm -vf ${TMETEO_PROC-DATASET_OBJ} ; rm -vf ${TMETEO_PROC-DATASET_BIN}	
	@echo "Done cleaning up"