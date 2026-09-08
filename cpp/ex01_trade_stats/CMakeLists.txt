# A lógica sai do main.cpp para uma lib própria: função dentro do executável, ao
# lado de main(), não tem como ser chamada por um segundo binário. É por isso que
# `Trade` e as estatísticas deixaram o namespace anônimo — agora elas são usadas
# de outra unidade de tradução (o teste), então linkage externo aqui é correto,
# não regressão.
add_library(trade_stats_lib trade_stats.cpp)
target_include_directories(trade_stats_lib PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
target_link_libraries(trade_stats_lib PRIVATE project_warnings)

add_executable(trade_stats main.cpp)
target_link_libraries(trade_stats PRIVATE trade_stats_lib project_warnings)

if(FTE_BUILD_TESTS)
  add_executable(trade_stats_tests tests_trade_stats.cpp)
  target_link_libraries(trade_stats_tests
    PRIVATE trade_stats_lib project_warnings Catch2::Catch2WithMain
  )
  # Registra cada TEST_CASE individualmente no CTest, em vez de um caso só
  # "roda o binário": no relatório aparece qual teste caiu.
  catch_discover_tests(trade_stats_tests)
endif()
