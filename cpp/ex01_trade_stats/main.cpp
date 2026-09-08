#include <fstream>
#include <print>

#include "trade_stats.hpp"

using std::println;

int main(int argc, char* argv[]) {
  if (argc < 2) {
    println(stderr, "uso: trade_stats <trades.csv>");
    return 1;
  }
  std::ifstream file(argv[1]);
  if (!file.is_open()) {
    println(stderr, "erro: nao abriu {}", argv[1]);
    return 1;
  }
  ParseResult parsed = parse_trades(file);
  if (parsed.trades.empty()) {
    println(stderr, "erro: nenhum trade valido em {}", argv[1]);
    return 1;
  }
  println("trades:     {}", parsed.trades.size());
  println("malformed:  {}", parsed.malformed);
  println("min:        {:.2f}", min_price(parsed.trades));
  println("max:        {:.2f}", max_price(parsed.trades));
  println("mean:       {:.2f}", mean_price(parsed.trades));
  println("vwap:       {:.2f}", vwap(parsed.trades));

  return 0;
}
