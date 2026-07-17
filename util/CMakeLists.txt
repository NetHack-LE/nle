message(NOTICE "*** CMakeLists.txt: ${CMAKE_CURRENT_LIST_FILE}")

find_program(FLEX_EXECUTABLE NAMES flex flex.exe)
find_program(BISON_EXECUTABLE NAMES bison bison.exe)

set(MAKEDEFS_SRC
    makedefs.c
    ${NLE_SRC}/monst.c
    ${NLE_SRC}/objects.c
    ${NLE_SRC}/alloc.c
    ${NLE_SRC}/date.c
    ${NLE_SRC}/hacklib.c
    panic.c)

set(MAKEDEFS_HEADERS ${NLE_INC_GEN}/date.h ${NLE_INC_GEN}/pm.h)

set(DLB_SRC dlb_main.c ${NLE_SRC}/dlb.c panic.c ${NLE_SRC}/alloc.c
            ${NLE_SRC}/hacklib.c)

file(MAKE_DIRECTORY ${NLE_INC_GEN} ${NLE_SRC_GEN})

message(NOTICE "-- LUA_INCLUDE: ${LUA_INCLUDE}")

add_executable(makedefs ${MAKEDEFS_SRC})
add_dependencies(makedefs lua_support)
target_include_directories(
  makedefs PRIVATE ${NLE_INC} ${NLE_INC_GEN} ${NLE_UTIL_GEN} ${LUA_INCLUDE}
                   ${deboost_context_SOURCE_DIR}/include)

add_executable(dlb ${DLB_SRC})
add_dependencies(dlb lua_support)
target_include_directories(
  dlb PRIVATE ${NLE_INC} ${NLE_INC_GEN} ${NLE_UTIL_GEN} ${LUA_INCLUDE}
              ${deboost_context_SOURCE_DIR}/include)

add_executable(recover recover.c ${NLE_SRC}/hacklib.c ${NLE_SRC}/version.c)
add_dependencies(recover lua_support)
target_compile_definitions(recover PRIVATE -DMINIMAL_FOR_RECOVER)
target_include_directories(
  recover PRIVATE ${NLE_INC} ${NLE_INC_GEN} ${NLE_UTIL_GEN} ${LUA_INCLUDE}
                  ${deboost_context_SOURCE_DIR}/include)

add_custom_command(
  DEPENDS makedefs
  OUTPUT ${NLE_INC_GEN}/date.h
  COMMAND $<TARGET_FILE:makedefs> ARGS -v)
add_custom_target(generate_date_h DEPENDS ${NLE_INC_GEN}/date.h)

add_custom_command(
  DEPENDS makedefs
  OUTPUT ${NLE_INC_GEN}/onames.h
  COMMAND $<TARGET_FILE:makedefs> ARGS -o)

add_custom_command(
  DEPENDS makedefs
  OUTPUT ${NLE_INC_GEN}/pm.h
  COMMAND $<TARGET_FILE:makedefs> ARGS -p)
add_custom_target(generate_pm_h DEPENDS ${NLE_INC_GEN}/pm.h)

add_custom_command(
  DEPENDS tilemap
  OUTPUT ${NLE_SRC_GEN}/tile.c
  COMMAND $<TARGET_FILE:tilemap>)
add_custom_target(generate_tile_c DEPENDS ${NLE_SRC_GEN}/tile.c)

add_custom_target(util DEPENDS ${MAKEDEFS_HEADERS} recover)

add_executable(
  tilemap ${NLE_WIN}/share/tilemap.c ${NLE_SRC}/monst.c ${NLE_SRC}/objects.c
          ${NLE_SRC}/drawing.c ${NLE_SRC}/hacklib.c)
target_include_directories(
  tilemap PUBLIC ${NLE_INC} ${NLE_INC_GEN} ${LUA_INCLUDE}
                 ${deboost_context_SOURCE_DIR}/include)
add_dependencies(tilemap util lua_support)

file(GLOB NETHACK_TILE_SRC ${NLE_WIN}/rl/tile2rgb.c ${NLE_WIN}/rl/nletiletxt.c
     ${NLE_WIN}/share/tiletext.c)
add_library(tile OBJECT ${NETHACK_TILE_SRC} ${NLE_SRC_GEN}/tile.c)
target_include_directories(tile PUBLIC ${NLE_INC} ${NLE_INC_GEN}
                                       ${NLE_WIN}/share ${LUA_INCLUDE})
add_dependencies(tile generate_pm_h generate_tile_c)

set(MAN_PAGES ${NLE_DOC}/makedefs.6 ${NLE_DOC}/dlb.6 ${NLE_DOC}/recover.6
              ${NLE_DOC}/nethack.6)

set(TXT_DOCS ${NLE_DOC}/makedefs.txt ${NLE_DOC}/dlb.txt ${NLE_DOC}/recover.txt
             ${NLE_DOC}/nethack.txt)

install(TARGETS makedefs dlb recover DESTINATION ${INSTDIR})
install(FILES ${MAN_PAGES} DESTINATION ${INSTDIR}/man)
install(FILES ${TXT_DOCS} DESTINATION ${INSTDIR}/doc)
