cmake_minimum_required(VERSION 3.25)
project(fte_cpp CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(FTE_BUILD_TESTS "Baixa o Catch2 e constroi os testes" ON)

# Sanitizers em todo build de estudo: pega bug de memória na hora, não em produção.
# Ficam GLOBAIS de propósito, valendo também para as dependências: misturar código
# instrumentado com não instrumentado faz o ASan dar falso positivo de
# container-overflow ao passar std::vector/std::string pela fronteira.
add_compile_options(-fsanitize=address,undefined)
add_link_options(-fsanitize=address,undefined)

# Warnings valem só para o NOSSO código, via este alvo INTERFACE. Se fossem
# add_compile_options() globais, o -Werror quebraria o build por warning de
# dependência de terceiros — erro que não é meu e que eu não posso consertar.
add_library(project_warnings INTERFACE)
target_compile_options(project_warnings INTERFACE -Wall -Wextra -Wpedantic -Werror)

if(FTE_BUILD_TESTS)
  # Catch2 v3 baixado no configure (precisa de rede na primeira vez; depois fica
  # em cache no diretório de build). SYSTEM marca os headers dele como headers de
  # sistema — sem isso, o -Werror do nosso alvo de teste dispara em warning vindo
  # de dentro do Catch2. Tag fixada: build reproduzível não segue branch.
  include(FetchContent)
  FetchContent_Declare(
    Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG v3.16.0
    GIT_SHALLOW TRUE
    SYSTEM
  )
  FetchContent_MakeAvailable(Catch2)

  enable_testing()
  list(APPEND CMAKE_MODULE_PATH "${catch2_SOURCE_DIR}/extras")
  include(Catch)  # traz catch_discover_tests()
endif()

add_subdirectory(ex01_trade_stats)

# Alvo de formatação: `cmake --build <dir> --target format` (ou `format-check` no CI).
# clang-format do Command Line Tools não fica no PATH no macOS, por isso os HINTS.
find_program(CLANG_FORMAT_BIN
  NAMES clang-format
  HINTS
    /Library/Developer/CommandLineTools/usr/bin
    /opt/homebrew/opt/llvm/bin
    /usr/local/opt/llvm/bin
)

if(CLANG_FORMAT_BIN)
  file(GLOB_RECURSE FORMAT_SOURCES CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.hpp"
    "${CMAKE_CURRENT_SOURCE_DIR}/*.h"
  )
  # Fora: diretórios de build (ficam dentro da árvore de fontes) e as fontes das
  # dependências baixadas pelo FetchContent — formatar código de terceiros seria
  # ruído puro no diff.
  list(FILTER FORMAT_SOURCES EXCLUDE REGEX "/(build|cmake-build-[^/]*|_deps)/")

  add_custom_target(format
    COMMAND "${CLANG_FORMAT_BIN}" -i --style=file ${FORMAT_SOURCES}
    COMMENT "clang-format -i em ${CMAKE_CURRENT_SOURCE_DIR}"
    VERBATIM
  )

  add_custom_target(format-check
    COMMAND "${CLANG_FORMAT_BIN}" --dry-run -Werror --style=file ${FORMAT_SOURCES}
    COMMENT "checando formatação (falha se algo estiver fora do .clang-format)"
    VERBATIM
  )
else()
  message(STATUS "clang-format nao encontrado: alvos 'format' e 'format-check' desabilitados")
endif()
