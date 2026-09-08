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

---

Date: 2026-09-08
Topic: C++ F0·S1·D1 (cont.) — Catch2, testabilidade e o custo do linkage interno
What I built: Suíte Catch2 v3 no trade_stats — 10 casos cobrindo parsing (5 formas de linha malformada, stream vazio, só lixo) e estatísticas (gabarito conferido na mão, VWAP≠média com qty diferentes, VWAP=média com qty iguais, trade único, independência de ordem). Para isso a lógica saiu do executável para uma lib (`trade_stats.hpp`/`.cpp` → `trade_stats_lib`) e o `main.cpp` virou só cabeamento de CLI. CMake: `option(FTE_BUILD_TESTS)`, Catch2 via FetchContent com tag fixa, `catch_discover_tests`, warnings movidos para um alvo INTERFACE.
What broke: (1) Não dava para testar nada: função que mora ao lado do `main()`, dentro do executável, não pode ser chamada pelo binário de teste — ele tem o `main()` dele. Obstáculo estrutural, não bug. (2) O namespace anônimo que eu tinha colocado ONTEM virou o impedimento direto: linkage interno é literalmente "ninguém fora deste .cpp me chama". (3) `format-check` falhou no arquivo de teste novo (ordem dos includes) — o alvo que criei ontem pegou meu próprio erro hoje, que é exatamente para isso que ele existe. (4) Descobri, escrevendo teste de caso ruim, que `std::stod`/`std::stol` PARAM no primeiro caractere inválido e não lançam: "101.50abc" vira 101.50 em silêncio e meu parser aceita. Não sabia.
How I fixed it: (1)+(2) Extraí `Trade`, as estatísticas e o parsing para uma lib linkada tanto pelo executável quanto pelos testes; o namespace anônimo saiu. Não é desfazer o commit de ontem — a regra continua "o linkage deve ser o menor que ainda atende os call sites REAIS", e o que mudou foi o requisito, não o critério: o teste virou call site legítimo em outra unidade de tradução. (3) Rodei o alvo `format` e conferi que o `format-check` volta a passar. (4) Escrevi um teste que DOCUMENTA o comportamento atual do stod em vez de escondê-lo — se um dia virar erro explícito, o teste falha e a decisão aparece. Ganho de tabela na extração: `parse_trades` passou a receber `std::istream&` em vez de caminho de arquivo, então o teste alimenta um `istringstream` e não toca em disco — teste que depende de arquivo falha por cwd/permissão e esconde a regressão de verdade. Por fim, não confiei na suíte só porque passou: quebrei o código de propósito três vezes (`<` por `>` no min_price, vwap ignorando a qty, parse sem contar malformada) e cada mutação derrubou o caso certo.
Interview questions: When should a symbol have internal vs external linkage? (o mínimo que atende os call sites reais — e testar É um call site; foi o que me obrigou a abrir o namespace anônimo em 24h) · Why can't you unit-test a function defined next to `main()`? · Should sanitizer flags apply to third-party dependencies? (sim — misturar código instrumentado com não instrumentado dá falso positivo de container-overflow no ASan quando um vector/string cruza a fronteira; já `-Werror` NÃO deve vazar para dependência, senão o build quebra por warning que não é meu — duas flags que andavam juntas e têm escopos opostos) · How do you know your tests actually test anything? (mutation testing: só conta depois que eu vi o teste falhar pelo motivo certo)
Skill status: C++ C+ (learning) — 2 dias de Fase 0; CMake/toolchain B (lib + testes + FetchContent + escopo de flags de pé); testes C (primeira suíte, ainda sem e2e)
Next action: F0·S1·D2 — referências vs ponteiros, `const`, `std::string_view`. Dívida registrada na seção 8 do NOTAS.txt: falta teste end-to-end do binário (argv, exit code, stderr — os 10 casos cobrem lógica, não cabeamento) e `ctest`/`format-check` continuam sem gatilho em hook ou CI. Vector vazio segue como precondição documentada e não testada, por ser UB; a saída real (`std::optional`/`std::expected`) é assunto da S4.
