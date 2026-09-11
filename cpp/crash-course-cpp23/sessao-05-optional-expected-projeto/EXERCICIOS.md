# Sessão 5 — Exercícios

Entrega da sessão: analisador completo, incluindo entradas inválidas.

## Exercício 9

A partir de `09_erros.cpp`:

1. Teste `maior` com uma coleção vazia — confirme que retorna `std::nullopt` e que seu `main` não desreferencia sem checar.
2. Teste `dividir(10.0, 2.0)` — deve devolver `5.0` sem passar pelo branch de erro.
3. Acrescente uma função de conversão de texto para inteiro que **diferencie** texto inválido (`"abc"`) de valor fora do intervalo (ex.: um `enum class ErroConversao { Invalido, ForaDoIntervalo }` como `E` de `std::expected<int, ErroConversao>`, ou reaproveite o padrão de `interpretar` do projeto final na seção seguinte).

```bash
make run FILE=sessao-05-optional-expected-projeto/09_erros.cpp
```

Note que o programa termina com status `1` de propósito nesse arquivo (a divisão por zero é o caminho de erro esperado do exemplo) — isso é comportamento correto, não um bug para caçar.

## Projeto final — `projeto-analisador/analisador.cpp`

Já está compilado e validado nesta máquina. Rode os casos da tabela abaixo você mesmo antes de mexer no código, para ter a linha de base:

```bash
make analisador
cd sessao-05-optional-expected-projeto/projeto-analisador
./analisador medicoes.txt 100
```

| Experimento | Resultado esperado |
|---|---|
| `medicoes.txt`, limite 100 | `Quantidade: 5` / `Minimo: 10 ms` / `Maximo: 300 ms` / `Media: 100.00 ms` / `Acima de 100 ms: 120 300` |
| Um único valor `0`, limite `0` | Quantidade 1; mínimo, máximo e média zero; nenhum acima |
| Arquivo vazio ou só linhas vazias | Erro de ausência de medições |
| Linha `12abc` | Erro de inteiro inválido naquela linha |
| Linha `-1` ou `1000001` | Erro de intervalo permitido |
| Inteiro enorme (ex.: `99999999999999999999`) | Erro de intervalo do tipo |
| Arquivo inexistente | Erro de abertura |
| Limite `abc` | Erro de limite |

Todos os 8 casos foram conferidos nesta máquina (AppleClang 21) e batem com a tabela.

### Desafios (opcionais, na ordem sugerida)

1. Adicione a contagem de medições lentas (não só a lista).
2. Calcule a mediana sobre uma **cópia ordenada** de `*dados` — não ordene o vector original, que outras partes do programa ainda usam na ordem de leitura. Para os dados de exemplo, a mediana é `40`.
3. Exporte um resumo em texto com `std::ofstream`.
4. Separe o código em `monitor.hpp` (declarações de `Resumo` e das três funções) + `monitor.cpp` (implementação) + `main.cpp` (argumentos e apresentação) — use o laboratório de headers da sessão 6 como modelo antes de tentar isso aqui.

Não precisa de threads nem de API alguma para concluir o projeto.
