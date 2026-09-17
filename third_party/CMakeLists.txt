project(stc)
# libasdf-gwcs uses STC only for its cstr-keyed hashmaps, so cstr_core is the
# only implementation unit needed; see third_party/Makefile.am for how the
# minimal set was derived.
add_library(stc STATIC
    ${STC_DIR}/src/cstr_core.c
)
set_property(TARGET stc PROPERTY POSITION_INDEPENDENT_CODE 1)
# libasdf vendors its own copy of STC, but we shouldn't export any symbols
# from STC's compiled internals.
# See also https://github.com/asdf-format/libasdf/pull/247
# which fixes this on the libasdf side
set_property(TARGET stc PROPERTY C_VISIBILITY_PRESET hidden)
target_link_libraries(stc PUBLIC m)
target_include_directories(stc PRIVATE
        STC/include
)
install(
    FILES STC/LICENSE
    RENAME LICENSE_STC.txt DESTINATION ${CMAKE_INSTALL_DATADIR}/${CMAKE_PROJECT_NAME}
)

# AST is LGPL-3.0-or-later and is statically linked into libasdf-gwcs, so its
# license text must accompany any binary distribution (LGPLv3 section 4b).
if (ASDF_GWCS_WITH_AST AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/ast/COPYING)
    install(
        FILES ast/COPYING
        RENAME LICENSE_AST.txt DESTINATION ${CMAKE_INSTALL_DATADIR}/${CMAKE_PROJECT_NAME}
    )
endif()
