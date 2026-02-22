cmake_minimum_required(VERSION 3.28)
if(NOT DEFINED NLE_VERSION)
  if(DEFINED SKBUILD_PROJECT_VERSION)
    set(NLE_VERSION ${SKBUILD_PROJECT_VERSION})
  else()
    set(NLE_VERSION "0.0.0") # Unversioned.
  endif()
endif()

# Extract version number (major.minor.patch) as CMake doesn't like rc/dev
# suffixes
string(REGEX MATCH "^[0-9]+(\\.[0-9]+)*" CMAKE_NLE_VERSION "${NLE_VERSION}")
project(nle VERSION ${CMAKE_NLE_VERSION})

if(CMAKE_BUILD_TYPE MATCHES Debug)
  message("Debug build.")
  # Unclear if this is even necessary. `dsymutil rlmain -o rlmain.dSYM` seems to
  # have done the trick.
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g")
  set(CMAKE_XCODE_ATTRIBUTE_DEBUG_INFORMATION_FORMAT "dwarf-with-dsym")

  if(0)
    # address sanitizer.
    set(CMAKE_CXX_FLAGS_DEBUG
        "${CMAKE_CXX_FLAGS_DEBUG} -fno-omit-frame-pointer -fsanitize=address")
    set(CMAKE_C_FLAGS_DEBUG
        "${CMAKE_C_FLAGS_DEBUG} -fno-omit-frame-pointer -fsanitize=address")
    set(CMAKE_LINKER_FLAGS_DEBUG
        "${CMAKE_LINKER_FLAGS_DEBUG} -fno-omit-frame-pointer -fsanitize=address"
    )
  endif()
  if(MSVC)
    add_compile_options(/W4)
  else()
    add_compile_options(-Wall)
  endif()
elseif(CMAKE_BUILD_TYPE MATCHES Release)
  message("Release build.")
else()
  message("Some other build type.")
endif()

message(STATUS "Building nle backend version: ${CMAKE_NLE_VERSION}")

set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(HACKDIR
    "$ENV{HOME}/nethackdir.nle"
    CACHE STRING "Configuration files for nethack")

message(STATUS "HACKDIR set to: ${HACKDIR}")

# Playground vars
set(VARDIR ${HACKDIR})
set(INSTDIR ${HACKDIR})

# pybind11 via FetchContent
include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG v3.0.1
  EXCLUDE_FROM_ALL)
FetchContent_MakeAvailable(pybind11)

# de-boost-ified version of boost.context via FetchContent
FetchContent_Declare(
  deboost_context
  GIT_REPOSITORY https://github.com/septag/deboost.context.git
  GIT_HASH "259fc4103bad6bb484d5ff426ace56ac557107a4" EXCLUDE_FROM_ALL)
FetchContent_MakeAvailable(deboost_context)

add_compile_definitions(
  GCC_WARN
  NOCLIPPING
  NOMAIL
  NOTPARMDECL
  HACKDIR="${HACKDIR}"
  DEFAULT_WINDOW_SYS="rl"
  DLB
  NOCWD_ASSUMPTIONS
  NLE_USE_TILES)

set(NLE_SRC ${nle_SOURCE_DIR}/src)
set(NLE_INC ${nle_SOURCE_DIR}/include)
set(NLE_DAT ${nle_SOURCE_DIR}/dat)
set(NLE_UTIL ${nle_SOURCE_DIR}/util)
set(NLE_DOC ${nle_SOURCE_DIR}/doc)
set(NLE_SSYS ${nle_SOURCE_DIR}/sys/share)
set(NLE_WIN ${nle_SOURCE_DIR}/win)

set(NLE_SRC_GEN ${nle_BINARY_DIR}/src)
set(NLE_INC_GEN ${nle_BINARY_DIR}/include)
set(NLE_DAT_GEN ${nle_BINARY_DIR}/dat)
set(NLE_UTIL_GEN ${nle_BINARY_DIR}/util)

set(CMAKE_INSTALL_MESSAGE LAZY) # Don't tell us about up-to-date files.
add_subdirectory(util)
add_subdirectory(dat)

file(
  GLOB
  NETHACK_SRC
  "src/*.c"
  "sys/share/posixregex.c"
  "sys/share/ioctl.c"
  "sys/unix/unixunix.c"
  "sys/unix/unixmain.c"
  "sys/unix/unixres.c"
  "win/tty/*.c"
  "win/rl/winrl.cc")

# FetchContent for bzip2
include(FetchContent)
FetchContent_Declare(
  bzip2
  GIT_REPOSITORY git://sourceware.org/git/bzip2.git
  GIT_HASH fbc4b11da543753b3b803e5546f56e26ec90c2a7 EXCLUDE_FROM_ALL)
FetchContent_MakeAvailable(bzip2)

# Manually add bzip2 source files from the downloaded directory
set(BZIP2_SRC
    ${bzip2_SOURCE_DIR}/blocksort.c
    ${bzip2_SOURCE_DIR}/bzlib.c
    ${bzip2_SOURCE_DIR}/compress.c
    ${bzip2_SOURCE_DIR}/crctable.c
    ${bzip2_SOURCE_DIR}/decompress.c
    ${bzip2_SOURCE_DIR}/huffman.c
    ${bzip2_SOURCE_DIR}/randtable.c)

# EXCLUDE_FROM_ALL: Don't install this static library into /usr/local.
add_library(bz2_static STATIC EXCLUDE_FROM_ALL ${BZIP2_SRC})
target_include_directories(bz2_static PUBLIC ${bzip2_SOURCE_DIR})

# terminal emulator library
add_library(tmt STATIC "third_party/libtmt/tmt.c")
set_target_properties(tmt PROPERTIES C_STANDARD 11)

# libnethack library
add_library(nethack SHARED ${NETHACK_SRC})
add_dependencies(nethack util dat)
set_target_properties(nethack PROPERTIES CXX_STANDARD 14 SUFFIX ".so")
target_include_directories(
  nethack
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include ${NLE_INC_GEN} /usr/local/include
         ${CMAKE_CURRENT_SOURCE_DIR}/third_party/libtmt ${bzip2_SOURCE_DIR})
# target_link_directories(nethack PUBLIC /usr/local/lib)

# Careful with -DMONITOR_HEAP: Ironically, it fails to fclose FILE* heaplog.
# target_compile_definitions(nethack PUBLIC "$<$<CONFIG:DEBUG>:MONITOR_HEAP>")

target_link_libraries(nethack PUBLIC m fcontext bz2_static tmt)

# dlopen wrapper library
add_library(nethackdl STATIC "sys/unix/nledl.c")
target_include_directories(
  nethackdl PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
                   ${deboost_context_SOURCE_DIR}/include)
target_link_libraries(nethackdl PUBLIC dl)

# rlmain C++ (test) binary
add_executable(rlmain "sys/unix/rlmain.cc")
set_target_properties(rlmain PROPERTIES CXX_STANDARD 11)
target_link_libraries(rlmain PUBLIC nethackdl)
target_include_directories(rlmain PUBLIC ${NLE_INC_GEN})
add_dependencies(rlmain util) # For pm.h.

# pybind11 core python library.
pybind11_add_module(
  _pynethack
  win/rl/pynethack.cc
  src/monst.c
  src/decl.c
  src/drawing.c
  src/objects.c
  $<TARGET_OBJECTS:tile>)
target_link_libraries(_pynethack PUBLIC nethackdl)
set_target_properties(_pynethack PROPERTIES CXX_STANDARD 14)
target_include_directories(_pynethack PUBLIC ${NLE_INC_GEN})
add_dependencies(_pynethack util) # For pm.h.

# ttyrec converter library
add_library(
  converter STATIC ${CMAKE_CURRENT_SOURCE_DIR}/third_party/converter/converter.c
                   ${CMAKE_CURRENT_SOURCE_DIR}/third_party/converter/stripgfx.c)
target_include_directories(
  converter
  PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/third_party/libtmt
         ${CMAKE_CURRENT_SOURCE_DIR}/third_party/converter ${bzip2_SOURCE_DIR})
target_link_libraries(converter PUBLIC bz2_static tmt)
if(CMAKE_BUILD_TYPE MATCHES Debug)
  target_compile_options(converter PRIVATE -Wall -Wextra -pedantic -Werror)
endif()

# ttyrec reader executable
add_executable(ttyrec_reader EXCLUDE_FROM_ALL "third_party/converter/reader.c")
target_link_libraries(ttyrec_reader PUBLIC converter)
target_include_directories(
  ttyrec_reader PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/third_party/converter)

pybind11_add_module(_pyconverter third_party/converter/pyconverter.cc)
target_link_libraries(_pyconverter PUBLIC converter)
set_target_properties(_pyconverter PROPERTIES CXX_STANDARD 14)
target_include_directories(
  _pyconverter PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/third_party/converter)

# Only install if we are building as part of a Python project.
if(DEFINED SKBUILD_PROJECT_VERSION)
  install(
    TARGETS _pynethack _pyconverter nethack
    RUNTIME DESTINATION ${PYTHON_PACKAGE_NAME}
    LIBRARY DESTINATION ${PYTHON_PACKAGE_NAME}
    ARCHIVE DESTINATION ${PYTHON_PACKAGE_NAME})
endif()
