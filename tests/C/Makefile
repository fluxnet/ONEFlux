# enables most optimization flags
CC := gcc -O3

TEST01_SRC := test_01.c
TEST01_OBJ := $(TEST01_SRC:.c=.o)
TEST01_BIN := $(join ${TGTDIR}, test_01)
	
${TEST01_BIN}:
	@echo "Building ${TEST01_BIN}..."
	${CC} -w -c ${TEST01_SRC} ;\
	${CC} ${TEST01_OBJ} -w -lm -o ${TEST01_BIN}

clean:
	@echo "Cleaning up..."
	rm -vf ${TEST01_OBJ} ; rm -vf ${TEST01_BIN}	
	@echo "Done cleaning up"