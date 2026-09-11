#include <algorithm>
#include <iostream>
#include <ranges>
#include <vector>

namespace views = std::views;

int main() {
    std::vector<int> tempos{50, 10, 80, 20, 120};
    std::ranges::sort(tempos);

    const int limite{50};
    const auto lento = [limite](int tempo) { return tempo > limite; };

    auto segundos = tempos
        | views::filter(lento)
        | views::transform([](int tempo) { return tempo / 1000.0; });

    for (const double valor : segundos) {
        std::cout << valor << '\n';
    }
    std::cout << std::ranges::count_if(tempos, lento) << '\n';
}
