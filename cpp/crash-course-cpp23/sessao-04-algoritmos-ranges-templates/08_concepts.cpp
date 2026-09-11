#include <concepts>
#include <iostream>

template <typename T>
concept Numero = std::integral<T> || std::floating_point<T>;

template <Numero T>
constexpr T quadrado(T valor) {
    return valor * valor;
}

template <std::totally_ordered T>
constexpr T maior(T a, T b) {
    return a > b ? a : b;
}

int main() {
    static_assert(quadrado(4) == 16);
    std::cout << quadrado(2.5) << '\n';
    std::cout << maior(3, 7) << '\n';
}
