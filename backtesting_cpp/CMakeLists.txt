cmake_minimum_required(VERSION 3.9)
project(backtestingCpp VERSION 0.1.0)
set(CMAKE_CXX_STANDARD 17)
include(GNUInstallDirs)

include(CTest)
enable_testing()

find_package(HDF5 REQUIRED COMPONENTS C)

include_directories(${HDF5_INCLUDE_DIRS})

set(SOURCE_FILES main.cpp Database.cpp Utils.cpp strategies/Sma.cpp strategies/Psar.cpp strategies/Sma.cpp)

add_executable(${PROJECT_NAME} ${SOURCE_FILES})
#add_library(${PROJECT_NAME} SHARED ${SOURCE_FILES})

target_link_libraries(${PROJECT_NAME} ${HDF5_LIBRARIES} ${HDF5_C_LIBRARIES})
install(TARGETS ${PROJECT_NAME}
        LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
        PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
include(CPack)
