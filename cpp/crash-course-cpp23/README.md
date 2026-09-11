# Crash course C++23 — do código ao programa funcionando

24 horas de prática, 6 sessões de 4 horas. Objetivo: escrever, compilar, depurar
e organizar pequenos programas em C++ moderno; entender quem possui cada recurso
e quando ele deixa de existir. Entrega final: um analisador de medições de
latência via terminal, com leitura de arquivo, validação e relatório.

Pressupõe familiaridade com variáveis, condições, laços e funções. Não precisa
dominar C antes. Digite os exemplos, preveja o resultado, compile e modifique.
~25% do tempo em leitura, ~75% em código. 24 horas são uma primeira passagem,
não uma promessa de domínio da linguagem.

## Como isto se encaixa no resto do repo

Este diretório é **material de referência e prática independente**, não uma
substituição do que já está rodando em [`cpp/ex01_trade_stats`](../ex01_trade_stats)
sob o [`ROADMAP-CPP-HFT.md`](../../ROADMAP-CPP-HFT.md). São propostas diferentes
de propósito:

- **`cpp/ex01_trade_stats`** — a Fase 0 do plano C++→HFT de verdade: CMake +
  Ninja + Catch2 + clang-tidy + sanitizers desde o dia 1, com gates e ritmo de
  ~2h/dia. É o que conta para o Gate 1.
- **`cpp/crash-course-cpp23`** (aqui) — os mesmos fundamentos (tipos, RAII,
  referências, classes, move, templates, containers) revisitados em ordem
  didática compacta, compilando cada arquivo isoladamente com `g++` puro (sem
  CMake), do jeito que a seção 12 deste curso ensina a organização manual de
  headers/linking antes de esconder tudo atrás de um build system. Útil como
  **revisão rápida** ou para consultar um conceito específico sem montar um
  projeto CMake novo — não para reiniciar o progresso da Fase 0.

Se um exercício daqui e um dia da Fase 0 cobrirem o mesmo tópico, vale a pena
fazer os dois: o crash course fixa o conceito isolado, a Fase 0 cobra o mesmo
conceito dentro do toolchain e do rigor de teste que valem para as entrevistas.

## Ambiente validado

Verificado nesta máquina em 2026-09-10:

```
$ g++ --version
Apple clang version 21.0.0 (clang-2100.3.34.2)
Target: arm64-apple-darwin27.0.0
InstalledDir: /Library/Developer/CommandLineTools/usr/bin
```

`g++` aqui é um alias para o AppleClang das Command Line Tools — não é o GCC
real. Isso não muda nada no curso (ele já avisa que Clang serve), mas explica
por que `g++ --version` imprime "Apple clang" em vez de um número de versão do
GCC.

Todos os 12 programas completos deste curso (sessões 1–6, incluindo o projeto
final e o laboratório de headers) foram compilados com
`-std=c++23 -Wall -Wextra -Wpedantic -g -O0` e executados nesta máquina; as
saídas batem com o que este README e os `EXERCICIOS.md` de cada sessão
descrevem. A única exceção conhecida: **`std::views::enumerate` não está
disponível** na libc++ instalada aqui (ver
[`sessao-06-headers-debugger-cpp23/EXERCICIOS.md`](sessao-06-headers-debugger-cpp23/EXERCICIOS.md)
para o que fazer). `std::ranges::to`, `std::print`/`std::format`/`std::println`
e `std::expected` funcionam normalmente.

## Como compilar (nvim + terminal)

Fluxo sugerido no nvim: `:vsplit term://zsh` (ou um painel de terminal ao lado
via tmux/kitty), editar o `.cpp` na esquerda, compilar/rodar na direita.

Um `Makefile` na raiz deste diretório evita redigitar os comandos `g++` da
seção 2:

```bash
make run FILE=sessao-01-ambiente-tipos-funcoes/01_inicio.cpp
make run FILE=sessao-05-optional-expected-projeto/projeto-analisador/analisador.cpp ARGS="medicoes.txt 100"
make sanitize FILE=sessao-03-classes-raii-movimento/05_raii.cpp   # ASan+UBSan
make anatomy FILE=sessao-01-ambiente-tipos-funcoes/01_inicio.cpp  # -E / -S / -c / link, separados
make analisador     # compila o projeto final da sessão 5
make headers-lab    # compila e linka o laboratório de headers da sessão 6
make clean
```

Se preferir digitar o comando `g++` você mesmo (recomendado pelo menos na
sessão 1, para internalizar o que cada flag faz):

```bash
g++ -std=c++23 -Wall -Wextra -Wpedantic -g -O0 caminho/arquivo.cpp -o /tmp/prog && /tmp/prog
```

## Roteiro de execução

| Sessão | Conteúdo | Distribuição das 4h | Entrega |
|---|---|---|---|
| 1 | Ambiente, compilação, tipos, namespaces, funções | 45min ambiente · 75min exemplos · 120min exercícios | Programa com funções e namespace próprio |
| 2 | Memória, referências, ponteiros, strings, containers | 60min conceitos · 120min prática · 60min depuração | Manipular uma coleção sem perder referências |
| 3 | Classes, RAII, ownership, cópia e movimento | 60min conceitos · 120min prática · 60min revisão | Classe que possui dados e libera recursos automaticamente |
| 4 | Algoritmos, lambdas, ranges, templates, concepts | 60min exemplos · 120min exercícios · 60min integração | Filtrar, ordenar e resumir medições |
| 5 | optional, expected, arquivos, projeto final | 45min erros · 75min arquivos · 120min projeto | Analisador completo, incluindo entradas inválidas |
| 6 | Headers, linking, debugger, novidades de C++23 | 90min organização · 60min debugger · 45min novidades · 45min avaliação | Projeto organizado e explicado por você |

Com duas horas por dia, divida cada sessão em dois dias. Só avance quando
conseguir fazer a entrega sem copiar a solução inteira.

## Estrutura

```
sessao-01-ambiente-tipos-funcoes/    01_inicio.cpp, 02_funcoes.cpp
sessao-02-memoria-referencias-containers/   03_memoria.cpp, 04_containers.cpp
sessao-03-classes-raii-movimento/    05_raii.cpp, 06_move.cpp
sessao-04-algoritmos-ranges-templates/   07_ranges.cpp, 08_concepts.cpp
sessao-05-optional-expected-projeto/  09_erros.cpp, projeto-analisador/
sessao-06-headers-debugger-cpp23/    10_consteval.cpp, headers-lab/, novidades-cpp23/
REFERENCIA.md   tabelas de consulta rápida (flags, tipos, containers, erros, C++23)
AVALIACAO.md    checklist final + respostas de revisão
```

Cada sessão tem seu próprio `EXERCICIOS.md` com os enunciados e as saídas
esperadas — sem solução pronta de propósito. Digite, preveja, compile.

## Debugger

Com um binário compilado com `-g -O0` (padrão de `make run`/`make analisador`):

```bash
lldb ./seu_programa
```

```
breakpoint set --name main
run argumentos aqui
frame variable
next
step
thread backtrace
continue
quit
```

Ver [`sessao-06-headers-debugger-cpp23/EXERCICIOS.md`](sessao-06-headers-debugger-cpp23/EXERCICIOS.md)
para um exercício guiado de debugger em cima do projeto final.

## Material complementar

- *A Tour of C++*, 3ª ed. (Stroustrup) — visão geral para quem já programa.
- CppCon, série "Back to Basics" por tema — assista depois de praticar o tema, não antes.
- [Compiler Explorer](https://godbolt.org/) — compare assembly com `-O0` vs `-O2`.
- *C++ Core Guidelines* — consulte quando surgir uma escolha real de ownership/interface.
- Tabelas de suporte por recurso: [cppreference C++23 compiler support](https://en.cppreference.com/w/cpp/compiler_support/23).

Primeira ação: abra `sessao-01-ambiente-tipos-funcoes/01_inicio.cpp` no nvim,
rode `make run FILE=sessao-01-ambiente-tipos-funcoes/01_inicio.cpp`, e comece
o [Exercício 1](sessao-01-ambiente-tipos-funcoes/EXERCICIOS.md).
