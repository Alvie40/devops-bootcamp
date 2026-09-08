#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>
#include <sstream>

#include "trade_stats.hpp"

using Catch::Approx;

namespace {

// O CSV de referencia do exercicio (ex01_trade_stats/trades.csv), inline.
// Manter aqui e nao ler o arquivo: teste que depende de I/O de disco falha por
// motivo errado (cwd, permissao) e esconde a regressao de verdade.
constexpr const char* kGabarito =
    "102.50,200\n"
    "104.00,100\n"
    "103.75,300\n"
    "101.10,150\n"
    "105.25,50\n";

ParseResult parse(const char* csv) {
  std::istringstream input{csv};
  return parse_trades(input);
}

}  // namespace

// ---------------------------------------------------------------- parse_trades

TEST_CASE("parse_trades le linhas bem formadas", "[parse]") {
  ParseResult result = parse(kGabarito);

  REQUIRE(result.trades.size() == 5);
  CHECK(result.malformed == 0);
  CHECK(result.trades[0].price == Approx(102.50));
  CHECK(result.trades[0].qty == 200);
  CHECK(result.trades[4].price == Approx(105.25));
  CHECK(result.trades[4].qty == 50);
}

TEST_CASE("parse_trades conta linha malformada sem interromper a leitura", "[parse]") {
  SECTION("linha sem virgula") {
    ParseResult result = parse("102.50,200\nlixo_sem_virgula\n104.00,100\n");
    CHECK(result.trades.size() == 2);
    CHECK(result.malformed == 1);
  }

  SECTION("preco nao numerico") {
    ParseResult result = parse("102.50,200\nabc,100\n");
    CHECK(result.trades.size() == 1);
    CHECK(result.malformed == 1);
  }

  SECTION("quantidade nao numerica") {
    ParseResult result = parse("102.50,200\n104.00,xyz\n");
    CHECK(result.trades.size() == 1);
    CHECK(result.malformed == 1);
  }

  SECTION("campo vazio dos dois lados da virgula") {
    ParseResult result = parse(",\n102.50,200\n");
    CHECK(result.trades.size() == 1);
    CHECK(result.malformed == 1);
  }

  SECTION("linha malformada no fim, sem newline final") {
    // Exatamente o caso do trades.csv do exercicio.
    ParseResult result = parse("102.50,200\ndfgdrgrgrgrg");
    CHECK(result.trades.size() == 1);
    CHECK(result.malformed == 1);
  }
}

TEST_CASE("parse_trades com stream vazio devolve nada, sem erro", "[parse]") {
  ParseResult result = parse("");
  CHECK(result.trades.empty());
  CHECK(result.malformed == 0);
}

TEST_CASE("parse_trades so com lixo nao produz trade valido", "[parse]") {
  // E o caso que faz o main sair com exit code 1.
  ParseResult result = parse("lixo\noutro lixo\n");
  CHECK(result.trades.empty());
  CHECK(result.malformed == 2);
}

TEST_CASE("parse_trades aceita sufixo depois do numero (comportamento do std::stod)", "[parse]") {
  // Documenta o que o parser faz HOJE, nao o que seria ideal: stod/stol param no
  // primeiro caractere invalido e nao lancam. "101.50abc" vira 101.50 em silencio.
  // Se um dia isso virar erro, este teste falha e a decisao fica visivel.
  ParseResult result = parse("101.50abc,200xyz\n");
  REQUIRE(result.trades.size() == 1);
  CHECK(result.malformed == 0);
  CHECK(result.trades[0].price == Approx(101.50));
  CHECK(result.trades[0].qty == 200);
}

// ----------------------------------------------------------------- estatisticas

TEST_CASE("estatisticas batem com o gabarito calculado na mao", "[stats]") {
  ParseResult result = parse(kGabarito);
  const std::vector<Trade>& trades = result.trades;
  REQUIRE(trades.size() == 5);

  CHECK(min_price(trades) == Approx(101.10));
  CHECK(max_price(trades) == Approx(105.25));
  CHECK(mean_price(trades) == Approx(103.32));
  // 82500 / 800 = 103.0656...
  CHECK(vwap(trades) == Approx(103.0656).epsilon(1e-6));
}

TEST_CASE("vwap difere da media simples quando as quantidades diferem", "[stats]") {
  // O ponto do exercicio: 100 com qty 1 e 200 com qty 99 tem media 150,
  // mas o dinheiro quase todo negociou a 200.
  std::vector<Trade> trades{{100.0, 1}, {200.0, 99}};
  CHECK(mean_price(trades) == Approx(150.0));
  CHECK(vwap(trades) == Approx(199.0));
}

TEST_CASE("com quantidades iguais vwap colapsa na media simples", "[stats]") {
  std::vector<Trade> trades{{100.0, 10}, {200.0, 10}, {300.0, 10}};
  CHECK(vwap(trades) == Approx(mean_price(trades)));
  CHECK(vwap(trades) == Approx(200.0));
}

TEST_CASE("um unico trade: as quatro estatisticas valem o proprio preco", "[stats]") {
  std::vector<Trade> trades{{101.75, 42}};
  CHECK(min_price(trades) == Approx(101.75));
  CHECK(max_price(trades) == Approx(101.75));
  CHECK(mean_price(trades) == Approx(101.75));
  CHECK(vwap(trades) == Approx(101.75));
}

TEST_CASE("min e max nao dependem da ordem de entrada", "[stats]") {
  std::vector<Trade> crescente{{100.0, 1}, {200.0, 1}, {300.0, 1}};
  std::vector<Trade> decrescente{{300.0, 1}, {200.0, 1}, {100.0, 1}};

  CHECK(min_price(crescente) == Approx(min_price(decrescente)));
  CHECK(max_price(crescente) == Approx(max_price(decrescente)));
  CHECK(min_price(crescente) == Approx(100.0));
  CHECK(max_price(crescente) == Approx(300.0));
}
