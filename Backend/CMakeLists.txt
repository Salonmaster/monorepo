cmake_minimum_required(VERSION 3.21)
project(Backend VERSION 1.0.0)

# Dependencies
find_package(CLI11)
find_package(glaze REQUIRED CONFIG)
find_package(jsoncpp REQUIRED CONFIG)
find_package(Boost REQUIRED)
find_package(Drogon REQUIRED)
find_package(spdlog REQUIRED)

# Build settings
set(BUILD_SHARED_LIBS OFF)
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Os -ffunction-sections -fdata-sections -DNDEBUG")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,--gc-sections")

# Gather sources
file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS
    "${CMAKE_SOURCE_DIR}/src/*.cpp"
    "${CMAKE_SOURCE_DIR}/src/*.cc"
    "${CMAKE_SOURCE_DIR}/src/*.h"
)

# Define application name and version
add_definitions(-DAPP_NAME="${PROJECT_NAME}" -DAPP_VERSION="${PROJECT_VERSION}")

# Create executable with all source files
add_executable(${PROJECT_NAME} ${SOURCES})

# Link libraries
target_link_libraries(${PROJECT_NAME} PRIVATE
    Drogon::Drogon
    spdlog::spdlog
    CLI11::CLI11
    Boost::boost
    glaze::glaze
    jsoncpp_lib
)

# Static linking options (must be after add_executable)
target_link_options(${PROJECT_NAME} PRIVATE
    -static
    -static-libgcc
    -static-libstdc++
)

# Add include directories
target_include_directories(${PROJECT_NAME} PRIVATE ${CMAKE_SOURCE_DIR}/src)
target_include_directories(${PROJECT_NAME} PRIVATE ${Boost_INCLUDE_DIRS})
target_include_directories(${PROJECT_NAME} PRIVATE ${YAML_CPP_INCLUDE_DIRS})
