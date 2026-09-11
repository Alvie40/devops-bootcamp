#include <iostream>
#include <ranges>
#include <vector>

int main() {
    std::vector<int> valores{10, 20, 30};
    for (auto [indice, valor] : valores | std::views::enumerate) {
        std::cout << indice << ": " << valor << '\n';
    }

    auto dobrados = valores
        | std::views::transform([](int valor) { return valor * 2; })
        | std::ranges::to<std::vector<int>>();

    std::cout << dobrados.at(2) << '\n';
}
