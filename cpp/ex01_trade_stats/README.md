# Exercício 01 — trade_stats

**Fase 0 · Semana 1 · Dia 1 do [ROADMAP-CPP-HFT.md](../../ROADMAP-CPP-HFT.md).**
Regra: você escreve todo o código. Consultas permitidas: este README, cppreference.com, learncpp.com. Proibido: copiar solução pronta.

---

## Enunciado

Escreva um programa de linha de comando chamado `trade_stats` que:

1. Recebe **um argumento**: o caminho de um arquivo CSV de trades.
2. Cada linha do arquivo tem o formato `preço,quantidade` — ex.: `101.50,200`.
3. Lê todas as linhas e calcula, sobre os trades válidos:
   - **count** — quantidade de trades lidos;
   - **min** — menor preço;
   - **max** — maior preço;
   - **mean** — preço médio simples (soma dos preços ÷ count);
   - **VWAP** — preço médio ponderado por quantidade: `Σ(preço × qty) ÷ Σ(qty)`.
4. Imprime as estatísticas de forma legível.

### Regras de robustez (fazem parte do enunciado)

- **Linha malformada** (sem vírgula, número inválido) **não derruba o programa**: é ignorada, contada, e o total de malformadas aparece na saída.
- **Arquivo inexistente** ou chamado **sem argumento** → mensagem de erro clara em stderr e **exit code 1**.
- **Arquivo sem nenhum trade válido** → decisão sua (erro? saída zerada?), mas você precisa saber defender a escolha.

### Exemplo

Dado `trades.csv`:

```
101.50,200
102.00,100
100.75,300
101.10,150
103.25,50
lixo_sem_virgula
```

Uma saída aceitável (formato livre, conteúdo obrigatório):

```
trades:     5
malformed:  1
min:        100.75
max:        103.25
mean:       101.72
vwap:       101.3--   ← calcule você; confira na calculadora
```

**Teste de honestidade:** antes de codar, calcule o VWAP das SUAS 5 linhas na calculadora. O programa só está pronto quando os números batem.

### O que este exercício treina (dia 1 da Fase 0)

`struct`, `std::vector`, `std::string`, `std::ifstream` (**RAII** — o conceito do dia), `std::getline`, parsing com `find`/`substr`/`stod`/`stol`, exceções (`try/catch`), passagem por **`const` referência**, range-for.

---

## Passo a passo (cada etapa termina com build + rodada)

Ciclo de trabalho, sempre a partir de `cpp/`:
`nvim ex01_trade_stats/main.cpp` → editar → `cmake --build build` → `./build/ex01_trade_stats/trade_stats ex01_trade_stats/trades.csv`

### Etapa 0 — Gabarito
Crie `trades.csv` com 5 linhas suas. Calcule o VWAP na calculadora. Anote.

### Etapa 1 — O struct
Acima do `main`, declare o tipo do dado:

```cpp
struct Trade {
  double price;  // preço: número com decimais
  long qty;      // quantidade: inteiro
};
```

Um `struct` cria um tipo novo agrupando campos — `Trade` passa a ser tão válido quanto `int`.
**Checkpoint:** ainda compila (`cmake --build build`).

### Etapa 2 — Abrir o arquivo (RAII)
Adicione `#include <fstream>` e `#include <string>`. Após o check de `argc`:

```cpp
std::ifstream file(argv[1]);
if (!file.is_open()) {
  // SEU código: mensagem em std::cerr + return 1
}
```

`file` abre o arquivo na construção e **fecha sozinho no destrutor** quando sai de escopo — isso é RAII (*Resource Acquisition Is Initialization*). Ninguém chama `close()`; é impossível esquecer.
**Checkpoint:** rodar com arquivo inexistente → sua mensagem + `echo $?` mostra `1`.

### Etapa 3 — Ler linha a linha (com andaime)

```cpp
std::string line;
while (std::getline(file, line)) {
  std::cout << "li: " << line << "\n";  // andaime — sai na etapa 4
}
```

`getline` enche `line` e vira `false` no fim do arquivo — por isso serve de condição.
**Checkpoint:** imprime suas 5 linhas.

### Etapa 4 — Parsear e guardar
`#include <vector>`. Antes do loop: `std::vector<Trade> trades;` e `int malformed = 0;`.
Dentro do loop, substitua o andaime pelo plano:

1. `auto pos = line.find(',');` — posição da vírgula; `std::string::npos` se não houver → conta malformada, `continue`.
2. `line.substr(0, pos)` = texto do preço; `line.substr(pos + 1)` = texto da quantidade.
3. `std::stod(...)` → `double`; `std::stol(...)` → `long`. **Atenção:** com texto inválido elas **lançam exceção**. Envolva conversão + `push_back` em:

```cpp
try {
  // converter e trades.push_back(Trade{...});
} catch (const std::exception&) {
  ++malformed;
}
```

**Checkpoint:** imprimir `trades.size()` e `malformed` no final. CSV limpo → `5 / 0`. Adicione uma linha lixo → `5 / 1`.

### Etapa 5 — Funções de estatística
Acima do `main`, uma função por métrica, todas com esta assinatura de exemplo:

```cpp
double vwap(const std::vector<Trade>& trades) { /* seu código */ }
```

**Por que `const &` (pergunta de entrevista):** `&` = referência, evita copiar o vector inteiro na chamada; `const` = promessa de só leitura. Percorra com:

```cpp
for (const Trade& t : trades) { /* use t.price e t.qty */ }
```

Escreva `vwap`, `mean_price`, `min_price`, `max_price` — min/max na mão (inicie com o primeiro elemento, compare no loop). Pense no vector vazio: divisão por zero em `double` vira `nan`, não crash — trate antes (sua decisão da regra de robustez).

### Etapa 6 — Saída final
No `main`: imprimir count, malformed, min, max, mean, vwap.
**Checkpoint final:** VWAP do programa == VWAP da calculadora.

### Etapa 7 — Fechamento do dia
- `clang-format -i ex01_trade_stats/main.cpp`
- Voz alta, 60s: *"What is RAII?"* — apontando para o seu `ifstream`.
- Entrada no [career/study-log.md](../../career/study-log.md) — capriche no "what broke".
- Commit: `cpp f0.d1: toolchain + trade_stats`

---

## Definition of Done

- [ ] Compila limpo com `-Wall -Wextra -Wpedantic -Werror` + sanitizers (já configurados).
- [ ] VWAP confere com a calculadora.
- [ ] Linha malformada: contada, não derruba.
- [ ] Arquivo inexistente / sem argumento: erro claro, exit code 1.
- [ ] Todas as funções de estatística recebem `const std::vector<Trade>&`.
- [ ] Consegue explicar RAII em 60 segundos apontando para o próprio código.

Erros de compilação nas etapas 4–5 são esperados e são o aprendizado. Erro incompreensível → cole no Claude Code que eu traduzo.
