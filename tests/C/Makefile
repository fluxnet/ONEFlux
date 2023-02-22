CC := gcc -O3
# copy file command (verbose, keep file metadata)
COPY = cp -v

SRCDIR := $(shell pwd)/
TGTDIR := ${HOME}/bin/oneflux/

# TEST_DIR := $(join ${SRCDIR}, )


METEO_PROC_DIR := $(join ${SRCDIR}, ../../oneflux_steps/meteo_proc/src/)
METEO_PROC_SRC := dataset.c
METEO_PROC_OBJ := $(METEO_PROC_SRC:.c=.o)
METEO_PROC_BIN := $(join ${TGTDIR}, meteo_proc)
METEO_TGT := test_meteo

TEST_METEO_DIR := ${SRCDIR}
TEST_METEO_SRC := test_meteo.c
TEST_METEO_OBJ := $(TEST_METEO_SRC:.c=.o)
TEST_METEO_BIN := $(join ${TGTDIR}, test_meteo)
TEST_METEO_TGT := test_meteo

COMMON_DIR := $(join ${SRCDIR}, ../../oneflux_steps/common/)
COMMON_SRC := common.c
COMMON_OBJ := $(COMMON_SRC:.c=.o)
COMMON_TGT := common

CHECK_PATH := /rds/project/rds-5mCMIDBOkPU/ma595/FluxNet/ONEFlux/tests/C/check-0.15.2/install/
CHECK_INCLUDE := $(join ${CHECK_PATH}, include)
CHECK_LIB := $(join ${CHECK_PATH}, lib)

${COMMON_TGT}:
	@echo "\nBuilding common objects..."
	cd ${COMMON_DIR} ;\
	${CC} -w -c ${COMMON_SRC}

${METEO_TGT}: ${COMMON_TGT}
	@echo "\nBuilding ${METEO_PROC_BIN}..."
	cd ${METEO_PROC_DIR}  ;\
	${CC} -w -c ${METEO_PROC_SRC} 

${TEST_METEO_BIN}: ${METEO_TGT} 
	@echo "\n${TEST_METEO_BIN}"
	${CC} -w -c ${TEST_METEO_SRC} ;\
	${CC} $(join ${METEO_PROC_DIR}, ${METEO_PROC_OBJ}) $(join ${COMMON_DIR}, ${COMMON_OBJ}) ${TEST_METEO_OBJ} -I ${METEO_PROC_DIR} -I ${CHECK_INCLUDE} -w -lm -L ${CHECK_LIB} -o ${TEST_METEO_BIN} -lcheck

# ${TEST_METEO_BIN}: ${COMMON_TGT}
# 	@echo "\n${TEST_METEO_BIN}"
# 	cd ${METEO_PROC_DIR} ;\
# 	${CC} -w -c ${METEO_PROC_SRC} ;\
# 	cd ${TEST_METEO_DIR} ;\
# 	${CC} -w -c ${TEST_METEO_SRC} ;\
# 	${CC} $(join ${METEO_PROC_DIR}, ${METEO_PROC_OBJ}) $(join ${COMMON_DIR}, ${COMMON_OBJ}) ${TEST_METEO_OBJ} -I ${METEO_PROC_DIR} -I/rds/project/rds-5mCMIDBOkPU/ma595/FluxNet/ONEFlux/tests/C/check-0.15.2/install/include -w -lm -L/rds/project/rds-5mCMIDBOkPU/ma595/FluxNet/ONEFlux/tests/C/check-0.15.2/install/lib -o ${TEST_METEO_BIN} -lcheck

meteo_test: directories ${TEST_METEO_BIN}
	@echo "\nBuild finished."

directories: ${TGTDIR}