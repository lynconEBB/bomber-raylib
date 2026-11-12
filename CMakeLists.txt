cmake_minimum_required(VERSION 3.25)
project(BomberC C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)
FetchContent_Declare(raylib
    URL https://github.com/raysan5/raylib/archive/refs/tags/6.2.tar.gz
)
FetchContent_MakeAvailable(raylib)

add_executable(bomber src/main.c)
target_link_libraries(bomber PRIVATE raylib)
