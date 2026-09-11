#include <iostream>
#include <map>
#include <span>
#include <string>
#include <vector>

double soma(std::span<const double> valores) {
    double resultado{};
    for (const auto valor : valores) {
        resultado += valor;
    }
    return resultado;
}

int main() {
    std::vector<double> tempos{10.0, 20.0, 30.0};
    tempos.push_back(40.0);
    std::cout << soma(tempos) << '\n';
    std::cout << tempos.at(0) << '\n';

    std::map<std::string, int> acessos{{"api", 3}, {"site", 5}};
    for (const auto& [nome, total] : acessos) {
        std::cout << nome << ": " << total << '\n';
    }
}
