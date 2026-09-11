#include <iostream>
#include <string>

namespace curso {
    int dobro(int valor) {
        return valor * 2;
    }
}

int main() {
    const std::string nome{"Alvaro"};
    std::cout << "Ola, " << nome << '\n';
    std::cout << "Dobro de 21: " << curso::dobro(21) << '\n';
}
