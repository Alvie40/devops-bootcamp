#include <iostream>
#include <string>
#include <string_view>

namespace curso {
    int somar(int a, int b) { return a + b; }
    double somar(double a, double b) { return a + b; }

    void incrementar(int& valor) { ++valor; }

    void mostrar(std::string_view texto, int repeticoes = 1) {
        for (int i{}; i < repeticoes; ++i) {
            std::cout << texto << '\n';
        }
    }
}

int main() {
    int numero{10};
    curso::incrementar(numero);
    curso::mostrar("C++23", 2);
    std::cout << numero << '\n';
    std::cout << curso::somar(2, 3) << '\n';
    std::cout << curso::somar(2.5, 3.0) << '\n';
}
