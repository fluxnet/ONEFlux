# N/A  - 00_original_dataset
# N/A  - 00_fp_dataset
# N/A  - 01_qc_visual
# 02_qc_auto
# N/A  - 03_qc_visual_cross
# 04_ustar_mp
# N/A  - 05_ustar_cp
# N/A  - 06_meteo_era
# N/A  - 06a_meteo_narr
# 07_meteo_proc
# 07a_meteo_mds
# N/A  - 07b_meteo_ann
# 08_nee_proc
# N/A  - 08a_nee_gapfill_ann
# 09_energy_proc
# N/A  - 10_nee_partition_nt
# N/A  - 11_nee_partition_dt
# 12_ure
# N/A  - 13_nee_partition_sr

# original
# CC := gcc

# potentially includes non-IEEE floating point arithmetic
#CC := gcc -Ofast

# enables most optimization flags
CC := gcc -O3

# create directory command
MKDIR = mkdir -p

# copy file command (verbose, keep file metadata)
COPY = cp -av

SRCDIR := $(shell pwd)/
TGTDIR := ${HOME}/bin/oneflux/

COMMON_DIR := $(join ${SRCDIR}, common/)
COMMON_SRC := common.c
COMMON_OBJ := $(COMMON_SRC:.c=.o)
COMMON_TGT := common

TXT2H_DIR := $(join ${SRCDIR}, tools/txt2h/src/)
TXT2H_SRC := main.c
TXT2H_OBJ := $(TXT2H_SRC:.c=.o)
TXT2H_BIN := $(join ${TGTDIR}, txt2h)

QC_AUTO_DIR := $(join ${SRCDIR}, qc_auto/src/)
QC_AUTO_SRC := dataset.c main.c marginals.c rpot.c spike.c ustar.c
QC_AUTO_OBJ := $(QC_AUTO_SRC:.c=.o)
QC_AUTO_BIN := $(join ${TGTDIR}, qc_auto)

USTAR_MP_DIR := $(join ${SRCDIR}, ustar_mp/src/)
USTAR_MP_SRC := bootstrapping.c dataset.c main.c parser.c ustar.c
USTAR_MP_OBJ := $(USTAR_MP_SRC:.c=.o)
USTAR_MP_BIN := $(join ${TGTDIR}, ustar_mp)

USTAR_CP_SRC := $(join ${SRCDIR}, ustar_cp/bin/ustar_cp)
USTAR_CP_BIN := $(join ${TGTDIR}, ustar_cp)

GF_MDS_DIR := $(join ${SRCDIR}, tools/gf_mds/src/)
GF_MDS_SRC := dataset.c main.c
GF_MDS_OBJ := $(GF_MDS_SRC:.c=.o)
GF_MDS_BIN := $(join ${TGTDIR}, gf_mds)

SW_IN_POT_DIR := $(join ${SRCDIR}, tools/SW_IN_POT_Calculator/src/)
SW_IN_POT_SRC := main.c
SW_IN_POT_OBJ := $(SW_IN_POT_SRC:.c=.o)
SW_IN_POT_BIN := $(join ${TGTDIR}, sw_in_pot)

METEO_PROC_DIR := $(join ${SRCDIR}, meteo_proc/src/)
METEO_PROC_SRC := dataset.c main.c
METEO_PROC_OBJ := $(METEO_PROC_SRC:.c=.o)
METEO_PROC_BIN := $(join ${TGTDIR}, meteo_proc)

METEO_MDS_DIR := $(join ${SRCDIR}, tools/gf_mds/src/)
METEO_MDS_SRC := dataset.c main.c
METEO_MDS_OBJ := $(METEO_MDS_SRC:.c=.o)
METEO_MDS_BIN := $(join ${TGTDIR}, meteo_mds)

NEE_PROC_DIR := $(join ${SRCDIR}, nee_proc/src/)
NEE_PROC_SRC := dataset.c main.c randunc.c
NEE_PROC_OBJ := $(NEE_PROC_SRC:.c=.o)
NEE_PROC_BIN := $(join ${TGTDIR}, nee_proc)

ENERGY_PROC_DIR := $(join ${SRCDIR}, energy_proc/src/)
ENERGY_PROC_SRC := aggr.c dataset.c ecbcf.c main.c randunc.c
ENERGY_PROC_OBJ := $(ENERGY_PROC_SRC:.c=.o)
ENERGY_PROC_BIN := $(join ${TGTDIR}, energy_proc)

URE_DIR := $(join ${SRCDIR}, ure/src/)
URE_SRC := dataset.c main.c
URE_OBJ := $(URE_SRC:.c=.o)
URE_BIN := $(join ${TGTDIR}, ure)


all: directories ${TXT2H_BIN} ${QC_AUTO_BIN} ${USTAR_MP_BIN} ${USTAR_CP_BIN} ${GF_MDS_BIN} ${SW_IN_POT_BIN} ${METEO_PROC_BIN} ${METEO_MDS_BIN} ${NEE_PROC_BIN} ${ENERGY_PROC_BIN} ${URE_BIN}
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

${TXT2H_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${TXT2H_BIN}..."
	cd ${TXT2H_DIR} ;\
	${CC} -w -c ${TXT2H_SRC} ;\
	${CC} ${TXT2H_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${TXT2H_BIN}

${QC_AUTO_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${QC_AUTO_BIN}..."
	cd ${QC_AUTO_DIR} ;\
	${CC} -w -c ${QC_AUTO_SRC} ;\
	${CC} ${QC_AUTO_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${QC_AUTO_BIN}

${USTAR_MP_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${USTAR_MP_BIN}..."
	cd ${USTAR_MP_DIR} ;\
	${CC} -w -c ${USTAR_MP_SRC} ;\
	${CC} ${USTAR_MP_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${USTAR_MP_BIN}

${USTAR_CP_BIN}: ${COMMON_TGT}
	@echo "\nCopying ${USTAR_CP_BIN}..."
	${COPY} ${USTAR_CP_SRC} ${USTAR_CP_BIN};\

${GF_MDS_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${GF_MDS_BIN}..."
	cd ${GF_MDS_DIR} ;\
	${CC} -w -c ${GF_MDS_SRC} ;\
	${CC} ${GF_MDS_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${GF_MDS_BIN}

${SW_IN_POT_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${SW_IN_POT_BIN}..."
	cd ${SW_IN_POT_DIR} ;\
	${CC} -w -c ${SW_IN_POT_SRC} ;\
	${CC} ${SW_IN_POT_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${SW_IN_POT_BIN}

${METEO_PROC_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${METEO_PROC_BIN}..."
	cd ${METEO_PROC_DIR}  ;\
	${CC} -w -c ${METEO_PROC_SRC} ;\
	${CC} ${METEO_PROC_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${METEO_PROC_BIN}

${METEO_MDS_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${METEO_MDS_BIN}..."
	cd ${METEO_MDS_DIR} ;\
	${CC} -w -c ${METEO_MDS_SRC} ;\
	${CC} ${METEO_MDS_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${METEO_MDS_BIN}

${NEE_PROC_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${NEE_PROC_BIN}..."
	cd ${NEE_PROC_DIR}  ;\
	${CC} -w -c ${NEE_PROC_SRC} ;\
	${CC} ${NEE_PROC_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${NEE_PROC_BIN}

${ENERGY_PROC_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${ENERGY_PROC_BIN}..."
	cd ${ENERGY_PROC_DIR}  ;\
	${CC} -w -c ${ENERGY_PROC_SRC} ;\
	${CC} ${ENERGY_PROC_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${ENERGY_PROC_BIN}

${URE_BIN}: ${COMMON_TGT}
	@echo "\nBuilding ${URE_BIN}..."
	cd ${URE_DIR} ;\
	${CC} -w -c ${URE_SRC} ;\
	${CC} ${URE_OBJ} $(join ${COMMON_DIR}, ${COMMON_OBJ}) -w -lm -o ${URE_BIN}

clean:
	@echo "\nCleaning up..."
	cd ${COMMON_DIR} ; rm -vf ${COMMON_OBJ}
	cd ${TXT2H_DIR} ; rm -vf ${TXT2H_OBJ} ; rm -vf ${TXT2H_BIN}
	cd ${QC_AUTO_DIR} ; rm -vf ${QC_AUTO_OBJ} ; rm -vf ${QC_AUTO_BIN}
	cd ${USTAR_MP_DIR} ; rm -vf ${USTAR_MP_OBJ} ; rm -vf ${USTAR_MP_BIN}
	cd ${GF_MDS_DIR} ; rm -vf ${GF_MDS_OBJ} ; rm -vf ${GF_MDS_BIN}
	cd ${SW_IN_POT_DIR} ; rm -vf ${SW_IN_POT_OBJ} ; rm -vf ${SW_IN_POT_BIN}
	cd ${METEO_PROC_DIR} ; rm -vf ${METEO_PROC_OBJ} ; rm -vf ${METEO_PROC_BIN}
	cd ${METEO_MDS_DIR} ; rm -vf ${METEO_MDS_OBJ} ; rm -vf ${METEO_MDS_BIN}
	cd ${NEE_PROC_DIR} ; rm -vf ${NEE_PROC_OBJ} ; rm -vf ${NEE_PROC_BIN}
	cd ${ENERGY_PROC_DIR} ; rm -vf ${ENERGY_PROC_OBJ} ; rm -vf ${ENERGY_PROC_BIN}
	cd ${URE_DIR} ; rm -vf ${URE_OBJ} ; rm -vf ${URE_BIN}
	@echo "Done cleaning up...\n"
