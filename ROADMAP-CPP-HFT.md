# Roadmap C++ → Quant/HFT Developer

Plano de frente para o nicho mais competitivo de engenharia: escrever C++ low-latency em trading firm como função principal. Sem açúcar: este é um projeto de **18–36 meses**, com gates objetivos a cada etapa para decidir — com dados, não com esperança — se continua, ajusta ou converge para a porta lateral.

## O reality check que governa o plano

- **O bar:** entrevistas de C++ em HFT testam profundidade de linguagem (move semantics, templates, memory model), sistemas (cache, NUMA, syscalls), concorrência (atomics, lock-free), rede (UDP multicast, kernel bypass) e algoritmos sob pressão de tempo. A concorrência inclui gente de olimpíada de programação e PhDs. Ninguém entra com 8 semanas de estudo.
- **A geografia (seu maior problema estrutural):** HFT de verdade vive em NYC, Chicago e Austin. Boston tem principalmente **quant asset managers** (Arrowstreet, Acadian, PanAgora, GMO, Man Numeric, Wellington, Fidelity) — mid-frequency, muito Python, C++ em partes do stack — e pouquíssimo HFT puro. Sem mudança de cidade, o alvo realista local é: quant asset manager, market data/fintech de infraestrutura, ou remoto (raro no nicho). O plano assume isso e mira o funil local + o que for remoto.
- **A porta lateral existe e é sua vantagem injusta:** trading firms contratam **low-latency systems/production engineers** — Linux tuning, rede, kernel, observability — e pagam muito bem. Seu plano DevOps constrói exatamente isso. A trilha C++ e a trilha infra **convergem**: um SRE de trading firm que lê e escreve C++ tem caminho interno para trading systems. Entrar pela lateral e migrar por dentro é estatisticamente o caminho mais provável para você chegar a escrever C++ em produção financeira.
- **Renda durante a jornada:** o funil FTE atual continua sendo o que paga as contas. Este plano não o substitui no curto prazo — ele redireciona o *destino* (firmas financeiras entram no job-bot já) e adiciona a trilha técnica C++.

**Comp se der certo:** $250–450k+ total já em níveis iniciais de HFT — é por isso que o bar é o que é. **Probabilidade:** depende inteiramente de passar nos gates abaixo.

---

## Estrutura: 4 fases com gates

Cadência: ~2h/dia útil + bloco de fim de semana (a mesma do plano FTE, agora com C++ como prioridade). Toda sessão termina em código commitado em `cpp/` ou resposta de entrevista escrita.

```
Fase 0  Fundamentos C++ moderno          semanas 1–4     GATE 1
Fase 1  Profundidade + DSA em C++        meses 2–4       GATE 2
Fase 2  Sistemas, concorrência, rede     meses 5–8       GATE 3
Fase 3  Domínio de mercado + portfólio   meses 9–12      GATE 4 → aplicações
Fase 4  Interview grind + iteração       mês 12+
```

Regra de ouro dos gates: **falhou o gate → não avança**. Repete o bloco ou aciona a decisão de convergir para a porta lateral. Gate não é punição; é o que separa este plano de wishful thinking.

---

## Fase 0 — Fundamentos de C++ moderno (semanas 1–4)

Objetivo: sair de zero para escrever C++20 idiomático com toolchain profissional. Nada de "C com classes".

**Setup (dia 1):** clang (já vem no macOS), CMake, Ninja, sanitizers (ASan/UBSan habilitados por padrão nos builds de estudo), clang-format, clang-tidy, Catch2/GoogleTest. Estrutura `cpp/` no repo com template CMake reutilizável.

**Material:** *A Tour of C++* (Stroustrup, 3ª ed., C++20) — curto e denso, o livro certo para quem já programa — + learncpp.com como referência de consulta. Proibido: curso de 40h em vídeo.

**Semana a semana:**
- **S1:** tipos, RAII desde o dia 1, referências vs ponteiros, `const`, funções, `std::string`/`string_view`, `vector`. Exercícios diários pequenos com testes.
- **S2:** classes, construtores/destrutores, rule of zero/three/five, move semantics (introdução), `unique_ptr`/`shared_ptr` — **nunca `new`/`delete` nus**.
- **S3:** templates básicos, STL de verdade: containers e **complexidade de cada operação**, iterators, algorithms, lambdas.
- **S4:** error handling (exceções vs códigos), I/O, projeto integrador: **CLI de análise de CSV de trades** (parse, agregações, estatísticas) com testes e CMake limpo — seu primeiro código de portfólio.

**GATE 1 (fim do mês 1):** ☐ escreve uma classe RAII correta de cabeça ☐ explica move vs copy com exemplo ☐ resolve 10 exercícios fáceis de LeetCode em C++ sem brigar com a linguagem ☐ o projeto compila com `-Wall -Wextra -Werror` + sanitizers limpos. Falhou → +2 semanas de fundamentos, uma vez só.

## Fase 1 — Profundidade de linguagem + DSA em C++ (meses 2–4)

Objetivo: o nível de linguagem que elimina 80% dos candidatos.

**Material:** *Effective Modern C++* (Meyers) — item a item, cada um vira flashcard de entrevista. DSA: refazer a trilha `dsa/` do repo **em C++** (arrays/hashing → two pointers → sliding window → stack → binary search → linked list → trees → heap → backtracking → graphs → DP), 4–5 problemas/semana com foco em **tempo**: mediums em ≤25 min.

**Temas obrigatórios (teoria + código toda semana):** value categories (lvalue/rvalue/xvalue), move semantics a fundo, perfect forwarding, template deduction, `constexpr`, virtual dispatch e seu custo, vtables, object layout, alignment, `std::variant`/`optional`/`expected`, allocators (introdução).

**Projeto do bloco: order book v1.** Limit order book com add/cancel/modify/match, price levels, testes de corretude. Primeiro ingênuo (`std::map`), depois medido e otimizado (vetores, intrusive containers) — **com benchmarks antes/depois** (Google Benchmark). Este projeto cresce pelo resto do plano.

**GATE 2 (fim do mês 4):** ☐ 60+ problemas LeetCode em C++, mediums consistentes em ≤25 min ☐ explica os ~40 itens principais do Meyers sem consultar ☐ order book v1 com testes e benchmark ☐ responde de cabeça: "what happens when you `push_back` into a full vector?", "why is `std::map` slow?", "when does RVO apply?". **Este é o gate mais importante do plano** — quem passa dele tem chance real; quem trava aqui deve convergir para a porta lateral sem culpa.

## Fase 2 — Sistemas, concorrência e rede low-latency (meses 5–8)

Objetivo: o que diferencia candidato de HFT de "C++ developer genérico". Aqui sua experiência de Linux/redes vira vantagem real.

**Temas e prática (cada um com experimento medido, não leitura):**
- **Memória e cache:** hierarquia, cache lines, false sharing, prefetch, layout de dados (AoS vs SoA), branch prediction. Medir tudo com `perf` (num Linux do Althora — macOS não serve para isso) e Google Benchmark.
- **Concorrência:** threads, mutexes e por que evitá-los no hot path, `std::atomic`, memory ordering (relaxed/acquire-release/seq_cst — de verdade, com exemplos que quebram), SPSC/MPMC queues, **lock-free ring buffer escrito do zero**. Livro: *C++ Concurrency in Action* (Williams).
- **Rede:** TCP vs UDP no contexto de market data, multicast, epoll/io_uring, serialização binária, endianness; conceitos de kernel bypass (DPDK/Solarflare) — saber explicar, não precisa operar.
- **Linux tuning (sua praia):** isolcpus, IRQ affinity, NUMA, huge pages, `taskset` — montar um mini-lab de latência no Althora e documentar.

**Projeto do bloco: feed handler.** Parser de **NASDAQ ITCH** (dados de amostra são públicos) alimentando o order book da Fase 1, com medição de latência por mensagem (histograma, p50/p99/p999) e um relatório de otimização honesto: o que tentou, o que mediu, o que melhorou.

**GATE 3 (fim do mês 8):** ☐ ring buffer SPSC lock-free correto (com teste de stress e explicação do memory ordering escolhido) ☐ explica false sharing com benchmark próprio mostrando a diferença ☐ feed handler processando ITCH real com números de latência documentados ☐ 100+ problemas LeetCode acumulados, hards ocasionais.

## Fase 3 — Domínio de mercado + portfólio + primeiras aplicações (meses 9–12)

**Domínio (o vocabulário que falta):** microestrutura de mercado — *Trading and Exchanges* (Harris) nos capítulos essenciais; tipos de ordem, matching rules, market making vs taking, latency arbitrage conceitual; protocolo FIX (ler e entender, montar um parser simples); opções e Greeks em nível de conversa.

**Portfólio final:** pipeline completo — **feed handler → order book → estratégia simulada → métricas de latência** — num repo público impecável: README com arquitetura, números de latência reproduzíveis, decisões de design justificadas. É o seu equivalente do capstone: o que prova que você não é "fez um curso de C++".

**Aplicações começam aqui (mês 9–10), em três anéis:**
1. **Anel local:** quant asset managers de Boston (Arrowstreet, Acadian, PanAgora, GMO, Man Numeric, Wellington, Fidelity) — vagas de C++/software engineer em trading/research tech. Configurar o job-bot para este filtro.
2. **Anel lateral (maior probabilidade):** low-latency **systems/production engineer** em trading firms e market data (Bloomberg, exchanges, fintechs de infra) — onde DevOps+C++ é exatamente o perfil. Migração interna para dev depois.
3. **Anel remoto/nacional:** o pouco de HFT remoto que existir + NYC se algum arranjo híbrido raro aparecer. Sem mudança de cidade, este anel é loteria — tratar como tal.

**GATE 4 (mês 12):** ☐ portfólio público completo com números ☐ 10 perguntas clássicas de C++ interview respondidas em voz alta no nível "por quê", não "o quê" ☐ primeiras 20 aplicações enviadas ☐ pelo menos 1 tech screen real feito (passar é bônus; fazer é o gate).

## Fase 4 — Interview grind (mês 12+)

Ciclo contínuo: mock interviews de C++ (Pramp/pares/gravação), banco de perguntas por firma, brainteasers/probabilidade básica (aparecem em quant shops — *Heard on the Street* como referência), post-mortem escrito de cada entrevista real no `career/study-log.md`. A cada trimestre: reavaliar com os dados do funil — taxa de resposta, em que rodada morre — e decidir entre insistir no anel 1/3 ou consolidar no anel 2.

---

## Decisões práticas já tomadas (para você vetar)

- **O plano FTE DevOps não é apagado:** ele vira o **anel 2** desta estratégia (é a porta lateral com maior probabilidade) e continua pagando as contas. Terraform/observability seguem em ritmo reduzido — são requisito das vagas do anel 2 também.
- **DSA migra de Python para C++** a partir da Fase 1 — um estudo serve aos dois funis.
- **Althora ganha função nova:** lab de latência Linux (perf, tuning, NUMA) — Fase 2 depende dele.
- **Job-bot:** adicionar filtros dos anéis 1 e 2 já (C++ finance Boston + low-latency systems engineer), para medir o mercado real enquanto você estuda.

## Cadência dupla acordada (2026-08-22)

Seg–sex ~2h30: **C++ 90 min (prioridade, lab primeiro) + Terraform 45 min (FTE S1–S2 em ritmo reduzido — cada semana do plano FTE vira ~2) + 15–20 min de fechamento** (1 pergunta de entrevista de cada trilha + study-log). Fim de semana alterna: sábado A = Terraform/Althora, sábado B = projeto C++. Dia apertado: C++ 60 + Terraform 20 — quem flexiona é o Terraform; os gates de C++ têm prazo. Método de ensino: todo conceito novo ancorado numa ponte com o que já domina (Terraform ↔ C++ ↔ Linux).

## Kill criteria honestos (releia a cada gate)

Convergir de vez para o anel 2 (sem drama — é um ótimo destino) se: **(a)** Gate 2 falhar duas vezes; **(b)** após 6 meses de aplicações do Gate 4, zero tech screens nos anéis 1 e 3; **(c)** o estudo de C++ virar tortura em vez de fascínio — nesse nicho, quem não gosta de verdade não sustenta o volume necessário; **(d)** o anel 2 entregar uma oferta boa antes — aceitar, e continuar a trilha C++ por dentro da firma.
