#include <iostream>
#include <memory>
#include <utility>
#include <vector>

std::vector<int> criar() {
    std::vector<int> valores{1, 2, 3};
    return valores;
}

int main() {
    auto original = criar();
    auto copia = original;
    auto destino = std::move(original);

    original.clear();
    original.push_back(99);
    std::cout << copia.size() << ' ' << destino.size() << '\n';
    std::cout << original.front() << '\n';

    auto primeiro = std::make_unique<int>(42);
    auto segundo = std::move(primeiro);
    std::cout << std::boolalpha << (primeiro == nullptr) << '\n';
    std::cout << *segundo << '\n';
}
