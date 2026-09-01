set(DATHELP
    help
    hh
    cmdhelp
    keyhelp
    history
    opthelp
    optmenu
    wizhelp)

file(
  GLOB SPECIAL_LEVELS
  RELATIVE ${NH_DAT}
  asmodeus.lua
  baalz.lua
  bigrm-??.lua
  castle.lua
  fakewiz?.lua
  juiblex.lua
  knox.lua
  medusa-?.lua
  minend-?.lua
  minefill.lua
  minetn-?.lua
  oracle.lua
  orcus.lua
  sanctum.lua
  soko?-?.lua
  tower?.lua
  valley.lua
  wizard?.lua
  nhcore.lua
  nhlib.lua
  themerms.lua
  astral.lua
  air.lua
  earth.lua
  fire.lua
  water.lua)

file(
  GLOB QUEST_LEVELS
  RELATIVE ${NH_DAT}
  ???-goal.lua ???-fil?.lua ???-loca.lua ???-strt.lua)

set(DATDLB
    ${DATHELP}
    dungeon.lua
    tribute
    ${SPECIAL_LEVELS}
    ${QUEST_LEVELS}
    bogusmon
    data
    engrave
    epitaph
    oracles
    options
    quest.lua
    rumors)

file(MAKE_DIRECTORY ${NLE_DAT_GEN})

# Inputs to makedef and lev_comp (and transitive inputs to dgn_comp and dlb).
set(ALL_DAT_NOTGEN
    ${DATHELP}
    ${SPECIAL_LEVELS}
    ${QUEST_LEVELS}
    bogusmon.txt
    data.base
    dungeon.lua
    engrave.txt
    epitaph.txt
    oracles.txt
    quest.lua
    rumors.fal
    rumors.tru
    tribute)

# makedef and friends like having their inputs in the same directory.
foreach(filename ${ALL_DAT_NOTGEN})
  configure_file(${NLE_DAT}/${filename} ${filename} COPYONLY)
endforeach(filename)

# Dat files that are not inputs to any tools.
set(ALL_DAT_NOTGEN ${ALL_DAT_NOTGEN} license symbols)

add_custom_command(
  DEPENDS $<TARGET_FILE:makedefs> bogusmon.txt engrave.txt epitaph.txt
  OUTPUT bogusmon epitaph engrave
  COMMAND makedefs ARGS -s)

add_custom_command(
  DEPENDS $<TARGET_FILE:makedefs> data.base
  OUTPUT data
  COMMAND makedefs ARGS -d)

add_custom_command(
  DEPENDS $<TARGET_FILE:makedefs> rumors.tru rumors.fal
  OUTPUT rumors
  COMMAND makedefs ARGS -r)

add_custom_command(
  DEPENDS $<TARGET_FILE:makedefs> quest.txt
  OUTPUT quest.dat
  COMMAND makedefs ARGS -q)

add_custom_command(
  DEPENDS $<TARGET_FILE:makedefs> oracles.txt
  OUTPUT oracles
  COMMAND makedefs ARGS -h)

# Hack: Depend on date.h to avoid race.
add_custom_command(
  DEPENDS $<TARGET_FILE:makedefs> generate_date_h
  OUTPUT options
  COMMAND makedefs ARGS -v)

add_custom_command(
  OUTPUT perm record logfile xlogfile COMMAND ${CMAKE_COMMAND} -E touch perm
                                              record logfile xlogfile)

# Defensive dependencies for when we also build NetHack with make/make install.
list(TRANSFORM DATDLB PREPEND ${NLE_DAT_GEN}/ OUTPUT_VARIABLE
                                              NLE_DAT_GEN_DATDLB)

add_custom_command(
  DEPENDS dlb ${NLE_DAT_GEN_DATDLB}
  OUTPUT nhdat
  COMMAND LC_ALL=C $<TARGET_FILE:dlb> ARGS cf nhdat ${DATDLB})

set(ALL_DAT_GEN nhdat perm record logfile xlogfile)
list(TRANSFORM ALL_DAT_GEN PREPEND ${NLE_DAT_GEN}/)

add_custom_target(dat ALL DEPENDS ${ALL_DAT_GEN} ${ALL_DAT_NOTGEN})

install(FILES ${ALL_DAT_GEN} DESTINATION ${INSTDIR})
install(FILES ${ALL_DAT_NOTGEN} DESTINATION ${INSTDIR}/dat)
install(DIRECTORY DESTINATION ${INSTDIR}/save)
