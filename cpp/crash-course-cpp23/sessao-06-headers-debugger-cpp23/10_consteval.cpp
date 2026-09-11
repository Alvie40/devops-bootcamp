#include <iostream>

consteval int dobro_constante(int valor) {
    return valor * 2;
}

constexpr int dobro(int valor) {
    if consteval {
        return dobro_constante(valor);
    } else {
        return valor * 2;
    }
}

int main() {
    constexpr int fixo = dobro(21);
    static_assert(fixo == 42);

    int entrada{};
    if (std::cin >> entrada) {
        if (entrada >= -1000 && entrada <= 1000) {
            std::cout << dobro(entrada) << '\n';
        }
    }
}
