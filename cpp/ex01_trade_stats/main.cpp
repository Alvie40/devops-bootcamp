#include <fstream>
#include <print>
#include <stdexcept>
#include <string>
#include <vector>

using std::println;

namespace {

struct Trade {
  double price;
  long qty;
};

double mean_price(const std::vector<Trade>& trades) {
  double sum = 0.0;
  for (const Trade& trade : trades) {
    sum += trade.price;
  }
  return sum / static_cast<double>(trades.size());
}

double vwap(const std::vector<Trade>& trades) {
  double notional = 0.0;
  long total_qty = 0;
  for (const Trade& trade : trades) {
    total_qty += trade.qty;
    notional += trade.price * static_cast<double>(trade.qty);
  }
  return notional / static_cast<double>(total_qty);
}

double min_price(const std::vector<Trade>& trades) {
  double lowest = trades[0].price;
  for (const Trade& trade : trades) {
    if (trade.price < lowest) {
      lowest = trade.price;
    }
  }
  return lowest;
}

double max_price(const std::vector<Trade>& trades) {
  double highest = trades[0].price;
  for (const Trade& trade : trades) {
    if (trade.price > highest) {
      highest = trade.price;
    }
  }
  return highest;
}

}  // namespace

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
  std::vector<Trade> trades;
  int malformed = 0;
  std::string line;
  while (std::getline(file, line)) {
    auto pos = line.find(',');
    if (pos == std::string::npos) {
      ++malformed;
      continue;
    }
    std::string price_str = line.substr(0, pos);
    std::string qty_str = line.substr(pos + 1);
    try {
      double price = std::stod(price_str);
      long qty = std::stol(qty_str);
      trades.push_back(Trade{price, qty});
    } catch (const std::exception&) {
      ++malformed;
    }
  }
  if (trades.empty()) {
    println(stderr, "erro: nenhum trade valido em {}", argv[1]);
    return 1;
  }
  println("trades:     {}", trades.size());
  println("malformed:  {}", malformed);
  println("min:        {:.2f}", min_price(trades));
  println("max:        {:.2f}", max_price(trades));
  println("mean:       {:.2f}", mean_price(trades));
  println("vwap:       {:.2f}", vwap(trades));

  return 0;
}
