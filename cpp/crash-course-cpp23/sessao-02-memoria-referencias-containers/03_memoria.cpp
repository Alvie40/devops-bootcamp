#include <iostream>
#include <memory>
#include <vector>

int main() {
    int numero{10};
    int& referencia{numero};
    int* ponteiro{&numero};

    referencia = 20;
    *ponteiro = 30;
    std::cout << numero << '\n';
    std::cout << &numero << '\n';

    ponteiro = nullptr;
    if (ponteiro) {
        std::cout << *ponteiro << '\n';
    }

    auto dono = std::make_unique<int>(42);
    std::vector<int> dados{1, 2, 3};
    std::cout << *dono << " / " << dados.size() << '\n';
}
