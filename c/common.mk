# Shared build/test rules for CS50-style C exercises.
#
# Usage: from an exercise directory (e.g. c/mario/), create a Makefile with
# just one line:
#
#   include ../common.mk
#
# Assumes the exercise directory name matches its source file
# (mario/mario.c, cat/cat.c, ...). Test targets are skipped automatically
# when no test_<name>_cmocka.c / test_<name>_criterion.c exists.

CC := clang
CFLAGS := -std=c11 -Wall -I..
CS50_LIBS := -lcs50

CMOCKA_PREFIX := $(shell brew --prefix cmocka 2>/dev/null)
CRITERION_PREFIX := $(shell brew --prefix criterion 2>/dev/null)

NAME := $(notdir $(CURDIR))
SRC := $(NAME).c
NOMAIN_OBJ := $(NAME)_nomain.o
CMOCKA_TEST_SRC := test_$(NAME)_cmocka.c
CRITERION_TEST_SRC := test_$(NAME)_criterion.c
CMOCKA_BIN := test_$(NAME)_cmocka
CRITERION_BIN := test_$(NAME)_criterion

.PHONY: all test test-cmocka test-criterion clean

all: $(NAME)

$(NAME): $(SRC)
	$(CC) $(CFLAGS) -o $@ $< $(CS50_LIBS)

# Same translation unit, but with main renamed out of the way so it can be
# linked into a test binary that brings its own main (cmocka/criterion).
$(NOMAIN_OBJ): $(SRC)
	$(CC) $(CFLAGS) -Dmain=$(NAME)_main_disabled -c $< -o $@

ifneq ("$(wildcard $(CMOCKA_TEST_SRC))","")
$(CMOCKA_BIN): $(CMOCKA_TEST_SRC) $(NOMAIN_OBJ)
	$(CC) $(CFLAGS) \
		-I$(CMOCKA_PREFIX)/include -L$(CMOCKA_PREFIX)/lib \
		$(CMOCKA_TEST_SRC) $(NOMAIN_OBJ) -o $@ -lcmocka $(CS50_LIBS)

test-cmocka: $(CMOCKA_BIN)
	DYLD_LIBRARY_PATH=$(CMOCKA_PREFIX)/lib ./$(CMOCKA_BIN)
else
test-cmocka:
	@echo "no $(CMOCKA_TEST_SRC) in $(NAME)/, skipping cmocka tests"
endif

ifneq ("$(wildcard $(CRITERION_TEST_SRC))","")
$(CRITERION_BIN): $(CRITERION_TEST_SRC) $(NOMAIN_OBJ)
	$(CC) $(CFLAGS) \
		-I$(CRITERION_PREFIX)/include -L$(CRITERION_PREFIX)/lib \
		$(CRITERION_TEST_SRC) $(NOMAIN_OBJ) -o $@ -lcriterion $(CS50_LIBS)

test-criterion: $(CRITERION_BIN)
	DYLD_LIBRARY_PATH=$(CRITERION_PREFIX)/lib ./$(CRITERION_BIN) --verbose
else
test-criterion:
	@echo "no $(CRITERION_TEST_SRC) in $(NAME)/, skipping criterion tests"
endif

test: test-cmocka test-criterion

clean:
	rm -f $(NAME) $(NOMAIN_OBJ) $(CMOCKA_BIN) $(CRITERION_BIN)
	rm -rf $(NAME).dSYM $(CMOCKA_BIN).dSYM $(CRITERION_BIN).dSYM
