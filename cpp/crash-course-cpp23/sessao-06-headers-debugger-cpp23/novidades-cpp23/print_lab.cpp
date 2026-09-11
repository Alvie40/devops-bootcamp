#include <format>
#include <print>
#include <string>

int main() {
    const std::string nome{"Alvaro"};
    const auto mensagem = std::format("Media: {:.2f} ms", 12.345);
    std::println("Ola, {}", nome);
    std::println("{}", mensagem);
}
