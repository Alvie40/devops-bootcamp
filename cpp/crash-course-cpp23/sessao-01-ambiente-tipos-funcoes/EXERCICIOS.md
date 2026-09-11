# Sessão 1 — Exercícios

Entrega da sessão: programa com funções e namespace próprio.

## Exercício 1

A partir de `01_inicio.cpp`:

1. Crie `curso::triplo`, chame `dobro` e `triplo` em `main`, compile de novo.
2. Depois escreva **de propósito** uma chamada para uma função inexistente (ex.: `curso::quadruplo(21)`) e leia o primeiro erro do compilador antes de corrigir.

```bash
make run FILE=sessao-01-ambiente-tipos-funcoes/01_inicio.cpp
```

## Exercício 2

A partir de `02_funcoes.cpp`, escreva:

- `double celsius_para_fahrenheit(double celsius)` — para 20 °C, espere **68 °F**.
- `void trocar(int& a, int& b)` — depois de `trocar(3, 7)` (chamado sobre variáveis, não literais), espere `a == 7` e `b == 3`.

```bash
make run FILE=sessao-01-ambiente-tipos-funcoes/02_funcoes.cpp
```

Não avance para a sessão 2 sem conseguir refazer os dois sem olhar a solução.
