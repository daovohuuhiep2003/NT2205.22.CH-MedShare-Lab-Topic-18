cmake_minimum_required(VERSION 3.16)
project(HEWorker LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(SEAL 4.1 REQUIRED)

add_executable(smoke_test smoke_test.cpp)
target_link_libraries(smoke_test PRIVATE SEAL::seal)

add_executable(seal_bfv_engine seal_bfv_engine.cpp)
target_link_libraries(seal_bfv_engine PRIVATE SEAL::seal)
