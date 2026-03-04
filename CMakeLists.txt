cmake_minimum_required(VERSION 3.10)
project(AETHER_HAL C)

# Version information
set(AETHER_HAL_VERSION_MAJOR 2)
set(AETHER_HAL_VERSION_MINOR 0)
set(AETHER_HAL_VERSION_PATCH 0)
set(AETHER_HAL_VERSION "${AETHER_HAL_VERSION_MAJOR}.${AETHER_HAL_VERSION_MINOR}.${AETHER_HAL_VERSION_PATCH}")

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Find SQLite3 (Mac-compatible)
find_package(SQLite3 REQUIRED)

# Handle different SQLite3 target names
if(TARGET SQLite::SQLite3)
    set(SQLITE_TARGET SQLite::SQLite3)
elseif(TARGET SQLite3::SQLite3)
    set(SQLITE_TARGET SQLite3::SQLite3)
else()
    # Fallback for systems without modern CMake targets
    set(SQLITE_TARGET sqlite3)
    link_directories(${SQLite3_LIBRARY_DIRS})
endif()

# Include directories
include_directories(include)
include_directories(src)
include_directories(src/sdk_modules)
include_directories(${SQLite3_INCLUDE_DIRS})

# SDK Modules
set(SDK_SOURCES
    src/sdk_modules/common/sdk_types.c
    src/sdk_modules/common/sdk_database.c
    src/sdk_modules/timezones/timezone.c
    src/sdk_modules/permissions/permission.c
    src/sdk_modules/holidays/holiday.c
    src/sdk_modules/relays/relay.c
    src/sdk_modules/readers/reader.c
    src/sdk_modules/group_lists/group_list.c
    src/sdk_modules/access_points/access_point.c
    src/sdk_modules/areas/area.c
    src/sdk_modules/card_formats/card_format.c
)

# HAL Core Library
add_library(hal_core
    src/hal_core/hal.c
    src/hal_core/event_manager.c
    src/hal_core/card_database.c
    src/hal_core/access_logic.c
    src/hal_core/json_config.c
    src/hal_core/event_exporter.c
    src/hal_core/osdp_reader.c
    src/hal_core/osdp_secure_channel.c
    src/hal_core/osdp_sc_logging.c
    src/hal_core/diagnostic_logger.c
    src/utils/cJSON.c
    ${SDK_SOURCES}
)

# Find libcurl and OpenSSL early for hal_core
find_package(CURL REQUIRED)
find_package(OpenSSL REQUIRED)

target_link_libraries(hal_core PRIVATE ${SQLITE_TARGET} CURL::libcurl OpenSSL::Crypto m)

# SDK Wrapper
add_library(sdk_wrapper
    src/sdk_wrapper/sdk_interface.c
    src/sdk_wrapper/command_handler.c
)

# Utils
add_library(hal_utils
    src/utils/logging.c
    src/utils/queue.c
    src/utils/timestamp.c
)

# Test executable
add_executable(test_hal_unit tests/test_card_database.c)
target_link_libraries(test_hal_unit PRIVATE hal_core hal_utils ${SQLITE_TARGET})

# TimeZone test
add_executable(test_timezone tests/test_timezone.c)
target_link_libraries(test_timezone PRIVATE hal_core ${SQLITE_TARGET} m)

# Examples
add_executable(example_basic examples/basic_access.c)
target_link_libraries(example_basic PRIVATE hal_core sdk_wrapper hal_utils ${SQLITE_TARGET})

add_executable(example_events examples/event_subscription.c)
target_link_libraries(example_events PRIVATE hal_core sdk_wrapper hal_utils)

add_executable(example_provision examples/card_provisioning.c)
target_link_libraries(example_provision PRIVATE hal_core hal_utils ${SQLITE_TARGET})

# Install
install(TARGETS hal_core sdk_wrapper hal_utils
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)

install(FILES include/hal_public.h include/hal_types.h include/osdp_types.h
        DESTINATION include)

add_library(access_event src/sdk_modules/events/access_event.c)
add_executable(test_access_event tests/test_access_event.c)
target_link_libraries(test_access_event access_event)

add_executable(test_hal_integration tests/test_hal_integration.c)
target_link_libraries(test_hal_integration hal_core access_event)

add_library(relay src/sdk_modules/relays/relay.c)
add_executable(test_hal_complete tests/test_hal_complete.c)
target_link_libraries(test_hal_complete hal_core access_event relay)

find_package(SQLite3 REQUIRED)
add_library(event_database src/hal_core/event_database.c)
target_link_libraries(event_database SQLite::SQLite3)
add_executable(test_hal_with_db tests/test_hal_with_db.c)
target_link_libraries(test_hal_with_db hal_core access_event relay event_database SQLite::SQLite3)

add_library(config src/hal_core/config.c src/utils/cJSON.c)
target_link_libraries(config hal_core)
add_executable(test_config tests/test_config.c)
target_link_libraries(test_config config hal_core)

# SDK Module Tests
add_executable(test_sdk_permissions tests/test_sdk_permissions.c)
target_link_libraries(test_sdk_permissions hal_core)

add_executable(test_sdk_holidays tests/test_sdk_holidays.c)
target_link_libraries(test_sdk_holidays hal_core)

add_executable(test_sdk_integration tests/test_sdk_integration.c)
target_link_libraries(test_sdk_integration hal_core)

# Enhanced Access Logic with SDK Integration
add_library(access_logic_sdk src/hal_core/access_logic_sdk.c)
target_link_libraries(access_logic_sdk hal_core)

# Complete SDK Demo Example
add_executable(complete_sdk_demo examples/complete_sdk_demo.c)
target_link_libraries(complete_sdk_demo hal_core access_logic_sdk access_event)

# SDK Database Persistence Test
add_executable(test_sdk_database tests/test_sdk_database.c)
target_link_libraries(test_sdk_database hal_core ${SQLITE_TARGET})

# JSON Import/Export Test
add_executable(test_json_export examples/test_json_export.c)
target_link_libraries(test_json_export hal_core ${SQLITE_TARGET})

# Azure Panel Config Generator
add_executable(create_azure_configs create_azure_configs.c)
target_link_libraries(create_azure_configs hal_core ${SQLITE_TARGET})

# HAL Event Export Daemon
add_executable(hal_event_export_daemon hal_event_export_daemon.c)
target_link_libraries(hal_event_export_daemon hal_core ${SQLITE_TARGET} CURL::libcurl)

# Event Export Config Test
add_executable(test_event_export_config test_event_export_config.c)
target_link_libraries(test_event_export_config hal_core ${SQLITE_TARGET} CURL::libcurl)

# OSDP Reader Test
add_executable(test_osdp_reader tests/test_osdp_reader.c)
target_link_libraries(test_osdp_reader hal_core ${SQLITE_TARGET})

# OSDP Secure Channel Test
add_executable(test_osdp_secure_channel tests/test_osdp_secure_channel.c)
target_link_libraries(test_osdp_secure_channel hal_core ${SQLITE_TARGET} OpenSSL::Crypto)

# OSDP Secure Channel Demo
add_executable(osdp_secure_demo examples/osdp_secure_demo.c)
target_link_libraries(osdp_secure_demo hal_core ${SQLITE_TARGET} OpenSSL::Crypto)
