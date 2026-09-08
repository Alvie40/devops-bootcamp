# Study log — FTE 8 semanas

Formato fixo por entrada (vira material de entrevista — "what broke / how I fixed it" são histórias prontas).

---

Date: 2026-08-22
Topic: S1·D1 — Terraform setup e primeiro apply
What I built:
What broke:
How I fixed it:
Interview questions: What is Terraform? · Why use IaC? · What does `terraform plan` do?
Skill status: Terraform C (learning) — dia 1
Next action: S1·D2 — variables, outputs, locals, data sources

---

Date: 2026-09-07
Topic: C++ F0·S1·D1 — trade_stats (RAII, const&, linkage interno)
What I built: CLI `trade_stats` em C++23 — lê CSV `preço,quantidade`, calcula count/min/max/mean/VWAP, conta linhas malformadas sem derrubar. Toolchain do zero: CMake + Ninja, `-Wall -Wextra -Wpedantic -Werror`, ASan/UBSan ligados por padrão, `.clang-format` (Google, ColumnLimit 100). Depois: alvos `format` e `format-check` no CMake.
What broke: (1) clang-tidy acusou `misc-use-internal-linkage` em `max_price` — e o mesmo defeito estava nas outras três funções e no `struct Trade`, o linter só não citou tudo na mesma passada. (2) `which clang-format` volta vazio no macOS e dá a falsa impressão de que falta instalar. (3) Indentação do `min_price` saiu com 4 espaços contra 2 do resto do arquivo — passou despercebido escrevendo à mão.
How I fixed it: (1) `struct Trade` + as quatro funções dentro de um `namespace { }` anônimo, não `static`: `static` não se aplica a tipos e já significa outras três coisas em C++; um bloco só cobre struct e funções e deixa óbvio na leitura que nada ali sai do arquivo. (2) O binário vem com os Command Line Tools mas fora do PATH — `/Library/Developer/CommandLineTools/usr/bin/clang-format`, ou `xcrun -f clang-format`; virou `find_program(... HINTS ...)` no CMake, com `else()` que só avisa em vez de dar FATAL_ERROR, para não travar o build de quem não tem a ferramenta. (3) clang-format no arquivo + alvo `format-check` (`--dry-run -Werror`) para não depender de vista. Conferi os números contra uma implementação independente em awk em vez de conferir o programa com ele mesmo: vwap 103.0656, bate.
Interview questions: What is RAII? (apontando para o `std::ifstream` — abre no construtor, fecha no destrutor, sobrevive ao caminho de exceção via stack unwinding; em C todo `return` antecipado é chance de vazar o handle) · Why pass by `const std::vector<T>&`? (`&` evita copiar o vector inteiro; `const` é promessa verificada pelo compilador de só leitura) · Internal vs external linkage — why does it matter? (símbolo externo abre porta para violação da ODR e bloqueia inlining/DCE, porque o compilador não pode assumir que conhece todos os call sites)
Skill status: C++ C (learning) — dia 1 da Fase 0; toolchain B (o setup está de pé e é reutilizável)
Next action: F0·S1·D2 — referências vs ponteiros, `const`, `std::string_view`. Dívida do dia 1 ainda aberta: nenhum test framework no CMake (o setup da Fase 0 pede Catch2/GoogleTest) e `format-check` não está plugado em hook nem CI — os quatro casos de robustez verificados à mão hoje são os primeiros testes candidatos.
