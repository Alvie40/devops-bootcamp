CC := clang
CFLAGS := -std=c11 -Wall
CS50_LIBS := -lcs50

CMOCKA_PREFIX := $(shell brew --prefix cmocka)
CRITERION_PREFIX := $(shell brew --prefix criterion)

.PHONY: all test test-cmocka test-criterion clean

all: cat

cat: cat.c
	$(CC) $(CFLAGS) -o $@ $< $(CS50_LIBS)

# Same translation unit, but with main renamed out of the way so it can be
# linked into a test binary that brings its own main (cmocka/criterion).
cat_nomain.o: cat.c
	$(CC) $(CFLAGS) -Dmain=cat_main_disabled -c $< -o $@

test_cat_cmocka: test_cat_cmocka.c capture.h cat_nomain.o
	$(CC) $(CFLAGS) \
		-I$(CMOCKA_PREFIX)/include -L$(CMOCKA_PREFIX)/lib \
		test_cat_cmocka.c cat_nomain.o -o $@ -lcmocka $(CS50_LIBS)

test_cat_criterion: test_cat_criterion.c capture.h cat_nomain.o
	$(CC) $(CFLAGS) \
		-I$(CRITERION_PREFIX)/include -L$(CRITERION_PREFIX)/lib \
		test_cat_criterion.c cat_nomain.o -o $@ -lcriterion $(CS50_LIBS)

test-cmocka: test_cat_cmocka
	DYLD_LIBRARY_PATH=$(CMOCKA_PREFIX)/lib ./test_cat_cmocka

test-criterion: test_cat_criterion
	DYLD_LIBRARY_PATH=$(CRITERION_PREFIX)/lib ./test_cat_criterion --verbose

test: test-cmocka test-criterion

clean:
	rm -f cat cat_nomain.o test_cat_cmocka test_cat_criterion
	rm -rf cat.dSYM test_cat_cmocka.dSYM test_cat_criterion.dSYM
