##############################################################################
# Aether Access - Ambient.ai Integration PoC
# CMake Build Configuration
#
# Author: FAM-HAL-v1.0-001
# Date: February 10, 2026
##############################################################################

cmake_minimum_required(VERSION 3.10)
project(aether_access_poc VERSION 1.0.0 LANGUAGES C)

# C Standard
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Compiler flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Werror=implicit-function-declaration")
set(CMAKE_C_FLAGS_DEBUG "-g -O0 -DDEBUG")
set(CMAKE_C_FLAGS_RELEASE "-O2 -DNDEBUG")

# Default to Debug build
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug)
endif()

message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C compiler: ${CMAKE_C_COMPILER}")
message(STATUS "System: ${CMAKE_SYSTEM_NAME}")

##############################################################################
# Platform-specific settings
##############################################################################

if(APPLE)
    message(STATUS "Building for macOS")
    find_library(SECURITY_FRAMEWORK Security)
    find_library(COREFOUNDATION_FRAMEWORK CoreFoundation)
endif()

##############################################################################
# Find dependencies
##############################################################################

# SQLite3
find_package(SQLite3 REQUIRED)
message(STATUS "SQLite3 found: ${SQLite3_LIBRARIES}")

# libcurl
find_package(CURL REQUIRED)
message(STATUS "CURL found: ${CURL_LIBRARIES}")

# pthreads
find_package(Threads REQUIRED)

##############################################################################
# Shared library
##############################################################################

set(SHARED_SOURCES
    shared/cJSON.c
    shared/json_serializer.c
    shared/uuid_utils.c
    shared/logger.c
)

set(SHARED_HEADERS
    shared/cJSON.h
    shared/event_types.h
    shared/json_serializer.h
    shared/uuid_utils.h
    shared/ipc_common.h
    shared/logger.h
)

add_library(poc_shared STATIC ${SHARED_SOURCES})
target_include_directories(poc_shared PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(poc_shared Threads::Threads)

if(APPLE)
    target_link_libraries(poc_shared ${SECURITY_FRAMEWORK})
endif()

##############################################################################
# App 1: HAL Access Engine
##############################################################################

set(HAL_ENGINE_SOURCES
    app1_hal_engine/main.c
    app1_hal_engine/hal_engine.c
    app1_hal_engine/wiegand_handler.c
    app1_hal_engine/card_database.c
    app1_hal_engine/access_logic.c
    app1_hal_engine/event_producer.c
    app1_hal_engine/ipc_publisher.c
    app1_hal_engine/config.c
)

add_executable(hal_engine ${HAL_ENGINE_SOURCES})
target_include_directories(hal_engine PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/shared
    ${CMAKE_CURRENT_SOURCE_DIR}/app1_hal_engine
)
target_link_libraries(hal_engine
    poc_shared
    SQLite::SQLite3
    Threads::Threads
)

##############################################################################
# App 2: Ambient.ai Event Forwarder
##############################################################################

set(FORWARDER_SOURCES
    app2_ambient_forwarder/main.c
    app2_ambient_forwarder/forwarder.c
    app2_ambient_forwarder/ipc_subscriber.c
    app2_ambient_forwarder/ambient_client.c
    app2_ambient_forwarder/retry_queue.c
    app2_ambient_forwarder/uuid_registry.c
    app2_ambient_forwarder/config.c
)

add_executable(ambient_forwarder ${FORWARDER_SOURCES})
target_include_directories(ambient_forwarder PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/shared
    ${CMAKE_CURRENT_SOURCE_DIR}/app2_ambient_forwarder
)
target_link_libraries(ambient_forwarder
    poc_shared
    CURL::libcurl
    SQLite::SQLite3
    Threads::Threads
)

##############################################################################
# Developer Tools
##############################################################################

# Tool: Badge Simulator
add_executable(simulate_badge tools/simulate_badge.c)
target_include_directories(simulate_badge PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(simulate_badge poc_shared)

# Tool: Event Monitor
add_executable(monitor_events tools/monitor_events.c)
target_include_directories(monitor_events PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(monitor_events poc_shared)

# Tool: Ambient.ai Test Client
add_executable(test_ambient tools/test_ambient.c)
target_include_directories(test_ambient PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/shared
    ${CMAKE_CURRENT_SOURCE_DIR}/app2_ambient_forwarder
)
target_link_libraries(test_ambient poc_shared CURL::libcurl)

# Tool: Log Viewer
add_executable(hal_logs tools/hal_logs.c)
target_include_directories(hal_logs PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(hal_logs poc_shared)

# Tool: System Status
add_executable(hal_status tools/hal_status.c)
target_include_directories(hal_status PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(hal_status poc_shared)

##############################################################################
# Tests
##############################################################################

enable_testing()

# Test: JSON Serializer
add_executable(test_json tests/test_json.c)
target_include_directories(test_json PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(test_json poc_shared)
add_test(NAME test_json COMMAND test_json)

# Test: UUID Utilities
add_executable(test_uuid tests/test_uuid.c)
target_include_directories(test_uuid PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(test_uuid poc_shared)
add_test(NAME test_uuid COMMAND test_uuid)

# Test: IPC
add_executable(test_ipc tests/test_ipc.c)
target_include_directories(test_ipc PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/shared)
target_link_libraries(test_ipc poc_shared)
add_test(NAME test_ipc COMMAND test_ipc)

##############################################################################
# Installation
##############################################################################

# Install executables
install(TARGETS hal_engine ambient_forwarder
    RUNTIME DESTINATION bin
)

# Install tools
install(TARGETS simulate_badge monitor_events test_ambient hal_logs hal_status
    RUNTIME DESTINATION bin
)

# Install configuration files
install(DIRECTORY config/
    DESTINATION etc/aether_poc
    FILES_MATCHING PATTERN "*.json"
)

# Install scripts
install(DIRECTORY scripts/
    DESTINATION bin
    USE_SOURCE_PERMISSIONS
    FILES_MATCHING PATTERN "*.sh"
)

##############################################################################
# Custom targets
##############################################################################

# Create runtime directories
add_custom_target(create_dirs
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_SOURCE_DIR}/data
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_SOURCE_DIR}/logs
    COMMENT "Creating runtime directories"
)

# Seed database
add_custom_target(seed_db
    COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/scripts/seed_database.sh
    DEPENDS create_dirs
    COMMENT "Seeding test database"
)

# Clean all
add_custom_target(clean_all
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}
    COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_CURRENT_SOURCE_DIR}/data/*.db
    COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_CURRENT_SOURCE_DIR}/logs/*.log
    COMMENT "Cleaning all build and runtime files"
)

message(STATUS "")
message(STATUS "=== Aether Access PoC Configuration ===")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "Install prefix: ${CMAKE_INSTALL_PREFIX}")
message(STATUS "")
message(STATUS "Targets:")
message(STATUS "  hal_engine         - HAL Access Engine")
message(STATUS "  ambient_forwarder  - Ambient.ai Event Forwarder")
message(STATUS "  simulate_badge     - Badge simulator tool")
message(STATUS "  monitor_events     - Event monitor tool")
message(STATUS "  test_ambient       - Ambient.ai test client")
message(STATUS "  hal_logs           - Log viewer tool")
message(STATUS "  hal_status         - System status tool")
message(STATUS "")
message(STATUS "Run 'make' to build all targets")
message(STATUS "=========================================")
