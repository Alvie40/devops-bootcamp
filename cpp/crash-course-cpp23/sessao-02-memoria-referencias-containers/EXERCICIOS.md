# Sessão 2 — Exercícios

Entrega da sessão: manipular uma coleção sem perder referências.

## Exercício 3

Antes de rodar, **preveja** o resultado de:

```cpp
int a{5};
int b{8};
int& r{a};
r = b;
b = 9;
```

Resultado esperado: `a == 8`, `b == 9`, `r == 8` (`r` é só outro nome para `a`; atribuir a `r` atribui a `a`, e mudar `b` depois não afeta nenhum dos dois).

Escreva isso em `03_memoria.cpp`, compile e confirme.

```bash
make run FILE=sessao-02-memoria-referencias-containers/03_memoria.cpp
```

## Exercício 4

A partir de `04_containers.cpp`: receba cinco números em um `std::vector<double>`, calcule soma e média, e imprima quantos estão acima da média.

- Para `10, 20, 30, 40, 50`: média `30`, dois valores acima dela (`40` e `50`).
- Defina explicitamente o que seu programa faz com uma coleção vazia (não deixe indefinido — decida e documente com um comentário curto).

```bash
make run FILE=sessao-02-memoria-referencias-containers/04_containers.cpp
```

Cuidado: se você fizer `push_back` numa coleção enquanto guarda uma referência/ponteiro/view para um elemento antigo, essa referência pode invalidar por realocação. Não é o caso deste exercício, mas é a armadilha que a sessão 2 existe para evitar.
