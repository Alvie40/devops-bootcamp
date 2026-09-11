# Sessão 3 — Exercícios

Entrega da sessão: classe que possui dados e libera recursos automaticamente.

## Exercício 5

A partir de `05_raii.cpp` (`monitor::Serie`):

1. Acrescente `limpar()` (esvazia `tempos_`).
2. Acrescente uma consulta ao maior tempo registrado — defina explicitamente o que acontece quando não há medições (ex.: `std::optional<int> maior() const`, retornando `std::nullopt` se vazio). Não adivinhe um valor sentinela tipo `-1`; isso mistura "sem dado" com "dado válido".
3. Verifique que `adicionar(-5)` **não** altera `tempos_` — a exceção deve ser lançada antes de qualquer `push_back`.
4. No `main` (ou numa função de teste manual), capture a exceção de `adicionar` com `try`/`catch` e imprima uma mensagem, sem derrubar o programa.

```bash
make run FILE=sessao-03-classes-raii-movimento/05_raii.cpp
```

## Exercício 6 (leitura de código, sem entrega nova)

Em `06_move.cpp`:

1. Comente a linha `auto segundo = std::move(primeiro);` e troque por `auto segundo = primeiro;`. Compile e leia o erro — `unique_ptr` não tem construtor de cópia, só de movimento.
2. Restaure o `std::move`. Explique em voz alta (ou por escrito, para o study-log) por que **não** seria válido fazer `*primeiro` depois dessa linha.

```bash
make run FILE=sessao-03-classes-raii-movimento/06_move.cpp
```
