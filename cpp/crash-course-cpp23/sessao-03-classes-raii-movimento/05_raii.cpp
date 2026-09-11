#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace monitor {
    class Serie {
    public:
        explicit Serie(std::string nome)
            : nome_{std::move(nome)} {}

        void adicionar(int tempo_ms) {
            if (tempo_ms < 0) {
                throw std::invalid_argument{"tempo negativo"};
            }
            tempos_.push_back(tempo_ms);
        }

        [[nodiscard]] std::size_t tamanho() const noexcept {
            return tempos_.size();
        }

        [[nodiscard]] const std::string& nome() const noexcept {
            return nome_;
        }

    private:
        std::string nome_;
        std::vector<int> tempos_;
    };
}

int main() {
    monitor::Serie serie{"api"};
    serie.adicionar(25);
    serie.adicionar(40);
    std::cout << serie.nome() << ": " << serie.tamanho() << '\n';
}
