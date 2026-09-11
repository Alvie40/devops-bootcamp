# Sessão 6 — Exercícios

Entrega da sessão: projeto organizado e explicado por você.

## Laboratório de linking (`headers-lab/`)

```bash
make headers-lab
```

Deve compilar `calculo.o` e `main.o` separadamente, linkar e imprimir `42`.

Agora tire `calculo.o` do comando final de link (edite temporariamente o `Makefile` ou rode a linha `g++ main.o calculo.o -o programa` sem o `calculo.o`) e observe o erro de **símbolo não resolvido** — isso acontece no linking, não na compilação: `main.cpp` compila sozinho porque só precisa da *declaração* em `calculo.hpp`; só falha quando o linker procura o corpo de `curso::dobro` e não encontra. Depois restaure o comando completo.

## Exercício 10 — debugger

Compile o analisador da sessão 5 com símbolos de depuração (já é o padrão do `make analisador`) e rode com LLDB:

```bash
lldb sessao-05-optional-expected-projeto/projeto-analisador/analisador
```

Dentro do LLDB:

```
breakpoint set --name monitor::interpretar
run ../ruim.txt
```

(crie antes um arquivo com uma linha `12abc`, ex. `printf "10\n12abc\n" > ruim.txt`).

Com o breakpoint parado dentro de `interpretar`, inspecione `posicao`, `fim` e `erro`:

```
frame variable texto
next
next
frame variable posicao fim erro
```

Explique por escrito por que checar **só** `erro != std::errc{}` não bastaria para rejeitar `"12abc"`: `std::from_chars` converte o prefixo válido (`12`) e para no primeiro caractere que não forma um inteiro, sem sinalizar erro nesse caso — é por isso que o código também compara `posicao != fim`, para garantir que a string inteira foi consumida.

## Laboratório de C++23 opcional (`novidades-cpp23/`)

```bash
make run FILE=sessao-06-headers-debugger-cpp23/novidades-cpp23/print_lab.cpp
```

`std::print`/`std::format`/`std::println` — validados nesta máquina.

```bash
make run FILE=sessao-06-headers-debugger-cpp23/novidades-cpp23/ranges_novidades.cpp
```

**Atenção:** este arquivo como está **não compila** nesta máquina — `std::views::enumerate` ainda não existe na libc++ do AppleClang 21 instalado aqui (confirmado ao montar este curso, 2026-09-10). `std::ranges::to<std::vector<int>>()` funciona normalmente. Para rodar o laboratório, comente o bloco do `enumerate` (linhas do `for` inicial) e mantenha só a parte de `transform` + `ranges::to`, ou vá direto rodar em [Compiler Explorer](https://godbolt.org/) com um Clang trunk/GCC 14+ para ver `enumerate` funcionando. Isso não é erro seu — é exatamente o tipo de "suporte de biblioteca separado do suporte de linguagem" que a seção 2 do curso avisa para conferir por conta própria.
