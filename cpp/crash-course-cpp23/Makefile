# Atalhos de compilação para o crash course de C++23.
# Uso típico dentro do nvim (:terminal) ou num painel de terminal ao lado:
#
#   make run FILE=sessao-01-ambiente-tipos-funcoes/01_inicio.cpp
#   make run FILE=sessao-05-optional-expected-projeto/projeto-analisador/analisador.cpp ARGS="medicoes.txt 100"
#   make sanitize FILE=sessao-03-classes-raii-movimento/05_raii.cpp
#   make anatomy FILE=sessao-01-ambiente-tipos-funcoes/01_inicio.cpp
#   make analisador
#   make headers-lab
#   make clean

CXX   ?= g++
STD   := -std=c++23
WARN  := -Wall -Wextra -Wpedantic
DEBUG := -g -O0
SAN   := -fsanitize=address,undefined -fno-omit-frame-pointer -O1
OUT   := /tmp/crash-course-cpp23

.PHONY: run sanitize anatomy analisador headers-lab clean

run:
	@test -n "$(FILE)" || (echo "uso: make run FILE=caminho/arquivo.cpp [ARGS=\"...\"]"; exit 1)
	$(CXX) $(STD) $(WARN) $(DEBUG) "$(FILE)" -o $(OUT)_run
	$(OUT)_run $(ARGS)

sanitize:
	@test -n "$(FILE)" || (echo "uso: make sanitize FILE=caminho/arquivo.cpp [ARGS=\"...\"]"; exit 1)
	$(CXX) $(STD) $(WARN) $(SAN) "$(FILE)" -o $(OUT)_san
	$(OUT)_san $(ARGS)

# Reproduz a seção 1 (pré-processador, assembly, objeto, link) para qualquer arquivo.
anatomy:
	@test -n "$(FILE)" || (echo "uso: make anatomy FILE=caminho/arquivo.cpp"; exit 1)
	$(CXX) $(STD) -E "$(FILE)" -o $(OUT)_anatomy.ii
	$(CXX) $(STD) -S $(DEBUG) "$(FILE)" -o $(OUT)_anatomy.s
	$(CXX) $(STD) -c "$(FILE)" -o $(OUT)_anatomy.o
	$(CXX) $(OUT)_anatomy.o -o $(OUT)_anatomy
	@echo "Gerado: $(OUT)_anatomy.ii (pré-processado), $(OUT)_anatomy.s (assembly), $(OUT)_anatomy.o (objeto), $(OUT)_anatomy (executável)"

analisador:
	$(CXX) $(STD) $(WARN) -Wconversion $(DEBUG) \
		sessao-05-optional-expected-projeto/projeto-analisador/analisador.cpp \
		-o sessao-05-optional-expected-projeto/projeto-analisador/analisador
	@echo "Rode: cd sessao-05-optional-expected-projeto/projeto-analisador && ./analisador medicoes.txt 100"

headers-lab:
	$(CXX) $(STD) $(WARN) -g -c sessao-06-headers-debugger-cpp23/headers-lab/calculo.cpp -o $(OUT)_calculo.o
	$(CXX) $(STD) $(WARN) -g -c sessao-06-headers-debugger-cpp23/headers-lab/main.cpp -o $(OUT)_main.o
	$(CXX) $(OUT)_main.o $(OUT)_calculo.o -o sessao-06-headers-debugger-cpp23/headers-lab/programa
	sessao-06-headers-debugger-cpp23/headers-lab/programa

clean:
	rm -f $(OUT)_run $(OUT)_san $(OUT)_anatomy $(OUT)_anatomy.ii $(OUT)_anatomy.s $(OUT)_anatomy.o \
		$(OUT)_calculo.o $(OUT)_main.o \
		sessao-05-optional-expected-projeto/projeto-analisador/analisador \
		sessao-06-headers-debugger-cpp23/headers-lab/programa
