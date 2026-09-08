#pragma once

#include <istream>
#include <vector>

// Um trade lido do CSV.
struct Trade {
  double price;
  long qty;
};

// Resultado de uma leitura: os trades validos e quantas linhas foram descartadas.
struct ParseResult {
  std::vector<Trade> trades;
  int malformed = 0;
};

// Le linhas `preco,quantidade` do stream ate o fim. Linha sem virgula ou com
// numero invalido nao interrompe a leitura: e contada em `malformed` e ignorada.
ParseResult parse_trades(std::istream& input);

// Estatisticas. Precondicao de todas: `trades` nao pode estar vazio.
// Com vector vazio, min/max acessam trades[0] (UB) e mean/vwap dividem por zero.
// Quem chama garante isso — ver o guard em main.cpp.
double mean_price(const std::vector<Trade>& trades);
double vwap(const std::vector<Trade>& trades);
double min_price(const std::vector<Trade>& trades);
double max_price(const std::vector<Trade>& trades);
