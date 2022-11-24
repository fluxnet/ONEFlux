# enables most optimization flags
CC := gcc -O3

# create directory command
MKDIR = mkdir -p

# copy file command (verbose, keep file metadata)
COPY = cp -av

SRCDIR := $(shell pwd)/
TGTDIR := 

COMMON_DIR := $(join ${SRCDIR}, ../../common/)
COMMON_SRC := common.c
COMMON_OBJ := $(COMMON_SRC:.c=.o)
COMMON_TGT := common

GF_MDS_DIR := $(join ${SRCDIR}, src)
GF_MDS_SRC := dataset.c main.c
GF_MDS_OBJ := $(GF_MDS_SRC:.c=.o)
GF_MDS_BIN := $(join ${TGTDIR}, gf_mds)

all: directories ${GF_MDS_BIN}
	@echo "\nBuild finished."

.PHONY: all clean ${COMMON_TGT} directories

directories: ${TGTDIR}

${TGTDIR}:
	@echo "\nCreating binary target directory..."
	${MKDIR} ${TGTDIR}

${COMMON_TGT}:
	@echo "\nBuilding common objects..."
	cd ${COMMON_DIR} ;\
	${CC} -w -c ${COMMON_SRC}

${GF_MDS_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${GF_MDS_BIN}..."
	cd ${GF_MDS_DIR} ;\
	${CC} -w -c ${GF_MDS_SRC} ;\
	${CC} ${GF_MDS_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ../${GF_MDS_BIN}

clean:
	@echo "\nCleaning up..."
	cd ${COMMON_DIR} ; rm -vf ${COMMON_OBJ}
	cd ${GF_MDS_DIR} ; rm -vf ${GF_MDS_OBJ} ; rm -vf ${GF_MDS_BIN}	
	@echo "Done cleaning up...\n"
