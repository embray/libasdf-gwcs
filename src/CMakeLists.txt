project(libasdf-gwcs)

set(libasdf_gwcs_sources
    backend.c
    coordinates/baseframe.c
    coordinates/fk4.c
    coordinates/fk5.c
    coordinates/frame_attributes.c
    core.c
    eval.c
    grid.c
    fitswcs_imaging.c
    frame.c
    frame2d.c
    frame_celestial.c
    step.c
    transform/affine.c
    transform/compose.c
    transform/concatenate.c
    transform/constant.c
    transform/divide.c
    transform/identity.c
    transform/polynomial.c
    transform/property/bounding_box.c
    transform/remap_axes.c
    transform/rotate_sequence_3d.c
    transform/scale.c
    transform/shift.c
    transform/spherical_cartesian.c
    transform/transform.c
    util.c
    wcs.c
)

add_library(libasdf_gwcs_objs OBJECT ${libasdf_gwcs_sources})
set_property(TARGET libasdf_gwcs_objs PROPERTY POSITION_INDEPENDENT_CODE 1)

add_library(libasdf-gwcs SHARED $<TARGET_OBJECTS:libasdf_gwcs_objs>)

target_include_directories(libasdf_gwcs_objs PUBLIC
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
    ${CMAKE_BINARY_DIR}/include
    ${STC_DIR}/include
    ${LIBASDF_INCLUDE_DIRS}
)

target_compile_options(libasdf_gwcs_objs PUBLIC ${LIBASDF_CFLAGS_OTHER})

# Make __FILE__ names relative to source root
target_compile_options(libasdf_gwcs_objs PRIVATE
    -fmacro-prefix-map=${CMAKE_SOURCE_DIR}/=
)

target_link_libraries(libasdf-gwcs PUBLIC
    stc
    ${LIBASDF_LIBRARIES}
)
target_link_directories(libasdf-gwcs PUBLIC ${LIBASDF_LIBRARY_DIRS})

# pkg_check_modules yields a bare "-lasdf", so CMake records no RPATH for it.
# Bake libasdf's directory into the build-tree RPATH, otherwise anything
# loading libasdf-gwcs.so has to be told where libasdf is out of band which
# bites when libasdf is installed to a non-standard prefix rather than
# system-wide.
#
# TODO: Figure out if this is a general problem or something to be fixed
# in libasdf's pc file.
set_target_properties(libasdf-gwcs PROPERTIES
    BUILD_RPATH "${LIBASDF_LIBRARY_DIRS}")

set_target_properties(libasdf-gwcs PROPERTIES
    SOVERSION ${PROJECT_SOVERSION}
    OUTPUT_NAME "asdf-gwcs"
)

if(ASDF_GWCS_WITH_AST)
    target_sources(libasdf_gwcs_objs PRIVATE backends/ast_yaml.c)
    target_compile_definitions(libasdf_gwcs_objs PRIVATE HAVE_AST)
    target_include_directories(libasdf_gwcs_objs PRIVATE ${AST_INCLUDE_DIR})
    target_link_libraries(libasdf-gwcs PUBLIC ${AST_LIBRARY})
    target_link_directories(libasdf-gwcs PUBLIC ${FYAML_LIBRARY_DIRS})
    if(TARGET ast_vendored)
        add_dependencies(libasdf_gwcs_objs ast_vendored)
    endif()
endif()

install(TARGETS libasdf-gwcs
    DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
