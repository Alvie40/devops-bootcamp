# Sessão 4 — Exercícios

Entrega da sessão: filtrar, ordenar e resumir medições.

## Exercício 7

A partir de `07_ranges.cpp`: depois de `std::ranges::sort(tempos)` nos dados `{50, 10, 80, 20, 120}`, monte um pipeline que:

1. Selecione tempos de pelo menos 20 ms (`views::filter`).
2. Converta para segundos (`views::transform`, dividir por 1000.0).
3. Pegue só os 3 primeiros (`views::take(3)`).

Resultado esperado, na ordem: `0.02, 0.05, 0.08`.

```bash
make run FILE=sessao-04-algoritmos-ranges-templates/07_ranges.cpp
```

## Exercício 8

Em `08_concepts.cpp`:

1. Inclua `<string>` e chame `quadrado(std::string{"x"})`. Leia o erro de restrição de concept — `std::string` não satisfaz `Numero` porque não é `std::integral` nem `std::floating_point`. Depois remova essa chamada.
2. Chame `maior(3, 7.0)`. `maior` exige o **mesmo** `T` nos dois parâmetros; `3` é `int` e `7.0` é `double`, então a dedução falha. Resolva de forma intencional: ou converta um dos dois (`maior(3, 7.0)` → `maior(3.0, 7.0)` ou `maior(3, static_cast<int>(7.0))`), ou reescreva `maior` para aceitar dois tipos distintos com `std::common_type_t`. Escolha uma e justifique por escrito qual perda de precisão ou de intenção cada uma implica.

```bash
make run FILE=sessao-04-algoritmos-ranges-templates/08_concepts.cpp
```
