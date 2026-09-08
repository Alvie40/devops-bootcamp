#include "trade_stats.hpp"

#include <stdexcept>
#include <string>

ParseResult parse_trades(std::istream& input) {
  ParseResult result;
  std::string line;
  while (std::getline(input, line)) {
    auto pos = line.find(',');
    if (pos == std::string::npos) {
      ++result.malformed;
      continue;
    }
    std::string price_str = line.substr(0, pos);
    std::string qty_str = line.substr(pos + 1);
    try {
      double price = std::stod(price_str);
      long qty = std::stol(qty_str);
      result.trades.push_back(Trade{price, qty});
    } catch (const std::exception&) {
      ++result.malformed;
    }
  }
  return result;
}

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
