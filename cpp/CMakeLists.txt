cmake_minimum_required(VERSION 3.25)
project(fte_cpp CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_compile_options(-Wall -Wextra -Wpedantic -Werror)

# Sanitizers em todo build de estudo: pega bug de memória na hora, não em produção
add_compile_options(-fsanitize=address,undefined)
add_link_options(-fsanitize=address,undefined)

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
  list(FILTER FORMAT_SOURCES EXCLUDE REGEX "/(build|cmake-build-[^/]*)/")

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
