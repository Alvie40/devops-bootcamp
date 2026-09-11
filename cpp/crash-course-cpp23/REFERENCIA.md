# Referência rápida

Consulta durante os exercícios — não precisa ler linear.

## Flags de compilação

| Opção | Efeito |
|---|---|
| `-std=c++23` | Seleciona C++23 |
| `-Wall -Wextra -Wpedantic` | Conjuntos úteis de diagnósticos (não todos os avisos possíveis) |
| `-g` | Informações de depuração |
| `-O0` | Desativa a maior parte das otimizações — facilita acompanhar o código |
| `-o nome` | Nome do executável |
| `-fsanitize=address,undefined -fno-omit-frame-pointer` | ASan+UBSan — usar com `-O1`, não `-O0` |

`-std=c++23` seleciona o padrão da **linguagem**; não instala recursos de
**biblioteca** ausentes. As duas coisas têm tabelas de suporte separadas —
confira sempre as duas para um recurso específico.

## Passagem de parâmetros — intenção habitual

| Parâmetro | Intenção |
|---|---|
| `int valor` | Receber um valor pequeno por cópia |
| `const std::string& texto` | Consultar uma string existente sem copiá-la |
| `std::string_view texto` | Consultar uma sequência de caracteres sem possuir os dados |
| `T& objeto` | Modificar um objeto existente |
| `T* objeto` | Observar um objeto, com possibilidade de `nullptr` se o contrato permitir |
| `std::unique_ptr<T> objeto` | Receber a propriedade exclusiva de uma alocação |

## Memória e ponteiros

| Expressão | Significado |
|---|---|
| `&numero` | Endereço de `numero` |
| `int* ponteiro` | Variável capaz de guardar endereço de um `int` |
| `*ponteiro` | Objeto apontado; exige um ponteiro válido para esse acesso |
| `int& referencia` | Outro nome para o objeto associado — não pode ser reconfigurada para outro objeto |
| `nullptr` | Valor de ponteiro nulo |

Referências também podem ficar penduradas quando o objeto morre — não são
garantia automática de lifetime correto. Overflow de inteiro com sinal é
comportamento indefinido; não conte com "voltar" ao menor valor.

## Containers e views

| Tipo | Quando usar | Possui elementos? |
|---|---|---|
| `std::string` | Texto mutável | Sim |
| `std::string_view` | Leitura de texto que já existe | Não |
| `std::vector<T>` | Sequência dinâmica contígua | Sim |
| `std::array<T, N>` | Sequência de tamanho fixo | Sim |
| `std::span<T>` | Acesso a uma sequência contígua existente | Não |
| `std::map<K,V>` | Chaves em ordem; busca logarítmica | Sim |
| `std::unordered_map<K,V>` | Tabela hash; busca média constante | Sim |

`span`/`string_view` **não prolongam a vida** da origem. Se `push_back`
provocar realocação, ponteiros/referências/iteradores/views anteriores para
elementos ficam inválidos.

## Ownership

| Necessidade | Escolha inicial |
|---|---|
| Objeto comum | Variável por valor |
| Coleção dinâmica | `std::vector<T>` |
| Objeto dinâmico com dono exclusivo | `std::unique_ptr<T>` |
| Vários donos necessários pelo desenho | `std::shared_ptr<T>` |
| Observar propriedade compartilhada sem mantê-la viva | `std::weak_ptr<T>` |

Não transforme todo objeto em smart pointer — valor e referência resolvem a
maioria dos casos. RAII serve para memória, arquivos, locks e outros
recursos, não só memória.

## Ausência, erros e alternativas

| Recurso | Expressa | Origem |
|---|---|---|
| `std::optional<T>` | Valor ou ausência | C++17 |
| `std::expected<T,E>` | Sucesso ou erro com informação | C++23 |
| Exceção | Falha propagada até um tratador | — |
| `std::variant<A,B>` | Uma alternativa tipada entre várias | C++17 |

`optional` não substitui automaticamente um ponteiro observador — possuir um
valor opcional e observar um objeto existente são contratos diferentes.
`expected` não impede que código interno lance exceções.

## O que estudar depois do núcleo (prioridade)

| Recurso | Origem | Prioridade |
|---|---|---|
| Deducing this | C++23 | Depois de referências e templates |
| Modules | C++20/23 | Depois de dominar headers e build |
| Coroutines | C++20 | Depois de lifetime e recursos |
| `std::generator` | C++23 | Quando precisar produzir sequências sob demanda |
| `std::mdspan` | C++23 | Para matrizes e computação numérica |
| `std::flat_map`/`flat_set` | C++23 | Após entender containers e medir seu caso |
| `std::jthread`, mutex, atomics | C++20+ | Segundo projeto (concorrência) |
| Herança, `virtual`, `override` | Base da linguagem | Quando houver substituição entre implementações |

## Simplificações a corrigir (do material original)

| Afirmação simplificada | Formulação correta |
|---|---|
| "Clang 17 / GCC 13 basta para C++23" | Linguagem e biblioteca têm tabelas próprias; confira cada recurso |
| "Move deixa vazio; não use depois" | O contrato varia; frequentemente o estado é válido mas não especificado |
| "Retorno é movimento automático/RVO" | Elisão e movimento são mecanismos diferentes; NRVO não é garantida |
| "Ponteiro ou melhor optional" | Observar um objeto e possuir um valor opcional são necessidades diferentes |
| "expected é mais barato" | Depende do tipo, compilador e frequência/forma dos erros |
| "map substitui tabela hash" | `unordered_map` é hash; `map` oferece ordenação |
| "flat_map tem a mesma interface e sempre ganha" | Há diferenças de interface, complexidade e invalidação; meça a carga concreta |
| "Alocação constante e try/catch começaram em C++23" | Ampliadas em C++20; lançar em expressão constante de C++23 não é permitido |
| "Lambda static elimina overhead" | Propriedade do operador de chamada; ganho depende da implementação |

Referência normativa (não é leitura inicial): rascunho público N4950,
especialmente as seções de estado após movimento e expressões constantes.
