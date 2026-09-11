#include <algorithm>
#include <charconv>
#include <cstddef>
#include <exception>
#include <expected>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <ranges>
#include <span>
#include <string>
#include <string_view>
#include <system_error>
#include <vector>

namespace monitor {
    constexpr int maximo_ms{1'000'000};

    struct Resumo {
        std::size_t quantidade{};
        int minimo{};
        int maximo{};
        double media{};
    };

    [[nodiscard]] std::expected<int, std::string>
    interpretar(std::string_view texto) {
        if (texto.empty()) {
            return std::unexpected(std::string{"valor vazio"});
        }

        int valor{};
        const char* fim = texto.data() + texto.size();
        const auto [posicao, erro] =
            std::from_chars(texto.data(), fim, valor);

        if (erro == std::errc::result_out_of_range) {
            return std::unexpected(std::string{"inteiro fora do intervalo"});
        }
        if (erro != std::errc{} || posicao != fim) {
            return std::unexpected(std::string{"inteiro invalido"});
        }
        if (valor < 0 || valor > maximo_ms) {
            return std::unexpected(std::string{"use 0 a 1000000 ms"});
        }
        return valor;
    }

    [[nodiscard]] std::expected<std::vector<int>, std::string>
    carregar(const std::string& caminho) {
        std::ifstream arquivo{caminho};
        if (!arquivo) {
            return std::unexpected("nao foi possivel abrir: " + caminho);
        }

        std::vector<int> valores;
        std::string linha;
        std::size_t numero_linha{};

        while (std::getline(arquivo, linha)) {
            ++numero_linha;
            if (!linha.empty() && linha.back() == '\r') {
                linha.pop_back();
            }
            if (linha.empty()) { continue; }

            const auto valor = interpretar(linha);
            if (!valor) {
                return std::unexpected(
                    "linha " + std::to_string(numero_linha) + ": " + valor.error());
            }
            valores.push_back(*valor);
        }

        if (arquivo.bad() || (arquivo.fail() && !arquivo.eof())) {
            return std::unexpected(std::string{"falha durante a leitura"});
        }
        if (valores.empty()) {
            return std::unexpected(std::string{"arquivo sem medicoes"});
        }
        return valores;
    }

    [[nodiscard]] std::expected<Resumo, std::string>
    resumir(std::span<const int> valores) {
        if (valores.empty()) {
            return std::unexpected(std::string{"nao ha dados para resumir"});
        }
        const auto [menor, maior] = std::ranges::minmax_element(valores);
        const double total = std::accumulate(valores.begin(), valores.end(), 0.0);
        return Resumo{
            .quantidade = valores.size(),
            .minimo = *menor,
            .maximo = *maior,
            .media = total / static_cast<double>(valores.size())
        };
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2 || argc > 3) {
        std::cerr << "Uso: ./analisador medicoes.txt [limite_ms]\n";
        return 1;
    }

    try {
        const auto limite = monitor::interpretar(argc == 3 ? argv[2] : "100");
        if (!limite) {
            std::cerr << "Limite: " << limite.error() << '\n';
            return 1;
        }

        const auto dados = monitor::carregar(argv[1]);
        if (!dados) {
            std::cerr << "Erro: " << dados.error() << '\n';
            return 1;
        }

        const auto resumo = monitor::resumir(*dados);
        if (!resumo) {
            std::cerr << "Erro: " << resumo.error() << '\n';
            return 1;
        }

        std::cout << "Quantidade: " << resumo->quantidade << '\n'
                  << "Minimo: " << resumo->minimo << " ms\n"
                  << "Maximo: " << resumo->maximo << " ms\n"
                  << "Media: " << std::fixed << std::setprecision(2)
                  << resumo->media << " ms\n"
                  << "Acima de " << *limite << " ms:";

        auto lentos = *dados | std::views::filter(
            [limite_ms = *limite](int valor) { return valor > limite_ms; });
        for (const int valor : lentos) {
            std::cout << ' ' << valor;
        }
        std::cout << '\n';
    } catch (const std::exception& erro) {
        std::cerr << "Falha: " << erro.what() << '\n';
        return 1;
    }
}
