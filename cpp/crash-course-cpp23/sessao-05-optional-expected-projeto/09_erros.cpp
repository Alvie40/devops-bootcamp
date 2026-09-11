#include <algorithm>
#include <expected>
#include <iostream>
#include <optional>
#include <span>
#include <string>
#include <vector>

std::optional<int> maior(std::span<const int> valores) {
    if (valores.empty()) { return std::nullopt; }
    return *std::ranges::max_element(valores);
}

std::expected<double, std::string> dividir(double a, double b) {
    if (b == 0.0) {
        return std::unexpected(std::string{"divisao por zero"});
    }
    return a / b;
}

int main() {
    const std::vector<int> valores{10, 50, 20};
    if (const auto resultado = maior(valores)) {
        std::cout << *resultado << '\n';
    }

    const auto resultado = dividir(10.0, 0.0);
    if (!resultado) {
        std::cerr << resultado.error() << '\n';
        return 1;
    }
    std::cout << *resultado << '\n';
}
