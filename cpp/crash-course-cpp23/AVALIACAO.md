# Avaliação final

Você concluiu a primeira passagem quando consegue:

- [ ] Compilar um `.cpp` e explicar a diferença entre erro de compilação e de linking.
- [ ] Dizer quando usar valor, referência, ponteiro, `span` e `unique_ptr`.
- [ ] Explicar por que um `vector` local pode administrar dados de alocação dinâmica.
- [ ] Identificar uma referência/view pendurada e uma invalidação por realocação.
- [ ] Criar uma classe com membros que gerenciam seus próprios recursos.
- [ ] Distinguir cópia, movimento e elisão.
- [ ] Escrever uma lambda e justificar sua captura.
- [ ] Filtrar uma coleção e explicar quando o resultado é calculado.
- [ ] Retornar erro com `expected` e ausência com `optional`.
- [ ] Rodar o analisador em entradas válidas e inválidas e localizar uma falha no debugger.

## Respostas de revisão

| Pergunta | Resposta |
|---|---|
| `auto b = a;` copia um vector? | Sim, cria outro vector com cópia dos elementos |
| `auto& b = a;` copia? | Não; cria uma referência |
| `std::move(a)` isolado transfere recursos? | Não |
| `reserve(100)` permite acessar `v[99]` num vector vazio? | Não; `size()` continua zero |
| `span` ou `string_view` mantêm a origem viva? | Não |
| `std::expected` elimina todas as exceções da função? | Não |
| `constexpr` obriga toda chamada a ocorrer em compilação? | Não |
| `-std=c++23` garante `<print>` disponível? | Não (confirmado nesta máquina: `<print>` funciona, mas `views::enumerate` não — biblioteca e linguagem são independentes) |
| RAII serve só para memória? | Não; também arquivos, locks e outros recursos |

Se alguma resposta te surpreendeu, volte para a sessão correspondente antes
de seguir para o `ROADMAP-CPP-HFT.md` — lá o mesmo material é cobrado com
Catch2, sanitizers e um gate objetivo, sem margem para "quase entendi".
