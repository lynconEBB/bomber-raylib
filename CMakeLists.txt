cmake_minimum_required(VERSION 3.25)
project(BomberC C)

set(CMAKE_C_STANDARD 23)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)
FetchContent_Declare(raylib
    URL https://github.com/raysan5/raylib/archive/refs/tags/6.2.tar.gz
)
FetchContent_MakeAvailable(raylib)

add_executable(bomber
    src/main.c
    src/grid.c
    src/tilemap.c
    src/maps.c
    src/input.c
    src/entity.c
    src/movement.c
    src/game.c
)
target_link_libraries(bomber PRIVATE raylib)
