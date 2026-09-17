cmake_minimum_required(VERSION 3.21)

# Internal full package version
set(PACKAGE_VERSION 0.1.0b0)

# CMake-compatible project version
set(PROJECT_VERSION 0.1.0)

set(PACKAGE_URL https://github.com/asdf-format/libasdf-gwcs)
set(PACKAGE_BUGREPORT https://github.com/asdf-format/libasdf-gwcs/issues)

# Shared library compatibility version
set(PROJECT_SOVERSION 0.0.0)

project(libasdf-gwcs
    VERSION ${PROJECT_VERSION}
    LANGUAGES C
)

set(PACKAGE_NAME "${PROJECT_NAME}")

# Global includes
include(GNUInstallDirs)
include(FindPkgConfig)

# Local includes
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
include(SubmoduleInit)

set(STC_DIR ${CMAKE_SOURCE_DIR}/third_party/STC)
set(MUNIT_DIR ${CMAKE_SOURCE_DIR}/tests/munit)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED TRUE)

# Update git submodules
if(EXISTS "${CMAKE_SOURCE_DIR}/.git")
    list(APPEND submodules
        third_party/STC
        tests/munit
    )
    submodule_init("${submodules}")
endif()

include(ASDFGWCSOptions)

add_compile_options(-fvisibility=hidden)
add_compile_definitions(HAVE_CONFIG_H)
add_compile_definitions(ASDF_LOG_ENABLED)

# Find libasdf via pkg-config
pkg_check_modules(LIBASDF libasdf REQUIRED)

# Generate config.h
configure_file(${CMAKE_SOURCE_DIR}/config.h.cmake
    ${CMAKE_BINARY_DIR}/include/config.h @ONLY)
include_directories(${CMAKE_BINARY_DIR}/include)

if(ASDF_GWCS_WITH_AST)
    find_package(PkgConfig REQUIRED)
    # AST's YamlChan is what the ast_yaml backend drives, so both build
    # systems configure it against libfyaml (the autotools build passes
    # --with-yaml=fyaml).  libfyaml is already a transitive dependency via
    # libasdf, so this adds nothing new to the dependency set.
    pkg_check_modules(FYAML REQUIRED libfyaml)

    if(EXISTS "${CMAKE_SOURCE_DIR}/third_party/ast/CMakeLists.txt")
        include(ExternalProject)
        set(AST_INSTALL_DIR ${CMAKE_BINARY_DIR}/ast-install)
        # Pass through our prefix path so AST's find_library/find_path can
        # locate libfyaml on non-standard installs (e.g. Homebrew on macOS).
        ExternalProject_Add(ast_vendored
            SOURCE_DIR ${CMAKE_SOURCE_DIR}/third_party/ast
            CMAKE_ARGS
                -DCMAKE_INSTALL_PREFIX=<INSTALL_DIR>
                -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
                -DCMAKE_C_COMPILER=${CMAKE_C_COMPILER}
                -DCMAKE_PREFIX_PATH=${CMAKE_PREFIX_PATH}
                -DCMAKE_POSITION_INDEPENDENT_CODE=ON
                -DBUILD_SHARED_LIBS=OFF
                -DBUILD_TESTING=OFF
                -DAST_BUILD_FORTRAN=OFF
                -DAST_WITH_YAML=ON
                -DAST_YAML_BACKEND=fyaml
                # libfyaml's headers only use C11 <stdatomic.h> when
                # __STDC_VERSION__ >= 201112L; under AST's default C99 they
                # fall back to a hand-rolled atomics path that does not
                # compile.  The autotools build gets C11+ from the compiler
                # default, so ask for it explicitly here too, which the
                # AST CI also does I think.
                -DAST_C_STANDARD=11
                # AST is absorbed into libasdf-gwcs, so keep its ~2500 symbols
                # out of our exported ABI; they would otherwise collide with a
                # program linking its own libast.  ExternalProject does not
                # inherit the top-level add_compile_options.
                -DCMAKE_C_VISIBILITY_PRESET=hidden
            INSTALL_DIR ${AST_INSTALL_DIR}
        )
        set(AST_INCLUDE_DIR ${AST_INSTALL_DIR}/include)
        set(_ast_lib_dir ${AST_INSTALL_DIR}/lib)
        # AST's CMake build compiles ast_pal and ast_cminpack as OBJECT
        # libraries embedded directly into libast.a, so they don't need to
        # be listed separately here (unlike the autotools build).
        set(AST_LIBRARIES
            ${_ast_lib_dir}/libast.a
            ${_ast_lib_dir}/libast_grf_2.0.a
            ${_ast_lib_dir}/libast_grf_3.2.a
            ${_ast_lib_dir}/libast_grf_5.6.a
            ${_ast_lib_dir}/libast_grf3d.a
            ${_ast_lib_dir}/libast_err.a
            ${FYAML_LINK_LIBRARIES}
        )
        set(AST_LIBRARY ${AST_LIBRARIES})
    else()
        find_library(AST_LIBRARY NAMES ast REQUIRED)
        find_path(AST_INCLUDE_DIR NAMES ast.h REQUIRED)
    endif()
endif()

add_subdirectory(third_party)
add_subdirectory(src)
add_subdirectory(include)
if(ENABLE_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()
if(ENABLE_DOCS)
    add_subdirectory(docs)
endif()

# Generate and install pkg-config file
set(prefix ${CMAKE_INSTALL_PREFIX})
set(exec_prefix ${CMAKE_INSTALL_PREFIX})
set(libdir ${CMAKE_INSTALL_FULL_LIBDIR})
set(includedir ${CMAKE_INSTALL_FULL_INCLUDEDIR})
configure_file(${CMAKE_SOURCE_DIR}/libasdf-gwcs.pc.in
    ${CMAKE_BINARY_DIR}/libasdf-gwcs.pc @ONLY)
install(FILES ${CMAKE_BINARY_DIR}/libasdf-gwcs.pc
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/pkgconfig)

install(
    FILES
        LICENSE
        CHANGES.rst
    DESTINATION ${CMAKE_INSTALL_DATADIR}/${PROJECT_NAME}
)
