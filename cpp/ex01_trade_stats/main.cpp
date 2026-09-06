#include <fstream>
#include <print>
#include <string>
#include <vector>

using std::println;

struct Trade {
  double price;
  long qty;
};

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
  println("lendo {}", argv[1]);
  return 0;
}
