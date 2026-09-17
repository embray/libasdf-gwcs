set(EXECUTABLE_OUTPUT_PATH ${CMAKE_BINARY_DIR}/tests)
set(CTEST_BINARY_DIRECTORY ${CMAKE_BINARY_DIR}/tests)
set(FIXTURES_DIR ${CMAKE_CURRENT_SOURCE_DIR}/fixtures)
set(TEMP_DIR ${CMAKE_CURRENT_BINARY_DIR}/tmp)
set(nix_gnu_cflags -Wall -Wextra)
set(nix_clang_cflags -Wall -Wextra)
set(win_msvc_cflags /Wall)

# Environment applied to every test.  Prepending the build tree's library
# directory keeps an installed copy of libasdf-gwcs from shadowing the one
# just built (the loader searches LD_LIBRARY_PATH before DT_RUNPATH).
set(runtime
    "srcdir=set:${CMAKE_CURRENT_SOURCE_DIR};top_srcdir=set:${CMAKE_SOURCE_DIR};top_builddir=set:${CMAKE_BINARY_DIR};LD_LIBRARY_PATH=path_list_prepend:${CMAKE_BINARY_DIR}/src")

# Build munit+util static library
add_library(munit ${MUNIT_DIR}/munit.c)
if (CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_definitions(munit PRIVATE MUNIT_NO_FORK)
endif()

add_library(util util.c)
target_compile_definitions(util PRIVATE
    REFERENCE_FILES_DIR=\"${FIXTURES_DIR}\"
    FIXTURES_DIR=\"${FIXTURES_DIR}\"
    TEMP_DIR=\"${TEMP_DIR}\"
    _GNU_SOURCE
)
target_include_directories(util PRIVATE
    ${CMAKE_SOURCE_DIR}/tests
    ${LIBASDF_INCLUDE_DIRS}
)

# GWCS tests
file(GLOB source_files "test-*.c")
set(ext_pattern "(^.*/|\\.[^.]*$)")

foreach(source_file ${source_files})
    string(REGEX REPLACE ${ext_pattern} "" test_executable ${source_file})
    add_executable(${test_executable} ${source_file})
    if (CMAKE_C_COMPILER_ID STREQUAL "GNU")
        target_compile_options(${test_executable} PRIVATE ${nix_cflags} ${nix_gnu_cflags})
    elseif (CMAKE_C_COMPILER_ID MATCHES "Clang")
        target_compile_options(${test_executable} PRIVATE ${nix_cflags} ${nix_clang_cflags})
    elseif (CMAKE_C_COMPILER_ID STREQUAL "MSVC")
        target_compile_options(${test_executable} PRIVATE ${win_cflags} ${win_msvc_cflags})
    endif()

    target_compile_definitions(${test_executable} PRIVATE
        REFERENCE_FILES_DIR=\"${FIXTURES_DIR}\"
        FIXTURES_DIR=\"${FIXTURES_DIR}\"
        TEMP_DIR=\"${TEMP_DIR}\"
        _GNU_SOURCE
    )

    target_include_directories(${test_executable} SYSTEM PRIVATE
        ${CMAKE_SOURCE_DIR}/include
        ${CMAKE_SOURCE_DIR}/src
        ${CMAKE_SOURCE_DIR}/tests
        ${MUNIT_DIR}
        ${LIBASDF_INCLUDE_DIRS}
    )

    target_link_libraries(${test_executable} PRIVATE
        libasdf-gwcs
        munit
        util
        ${LIBASDF_LIBRARIES}
    )

    add_test(${test_executable} ${test_executable})
    set_tests_properties(${test_executable}
        PROPERTIES TIMEOUT 240)
    set_tests_properties(${test_executable}
        PROPERTIES
        SKIP_RETURN_CODE 127)

    set(ENV{OBJC_DISABLE_INITIALIZE_FORK_SAFETY} "YES")
    set_property(TEST ${test_executable}
        PROPERTY ENVIRONMENT_MODIFICATION "${runtime}")
endforeach()

if(ASDF_GWCS_WITH_AST)
    target_compile_definitions(test-gwcs-eval PRIVATE HAVE_AST)
    target_include_directories(test-gwcs-eval PRIVATE ${AST_INCLUDE_DIR})
    target_link_libraries(test-gwcs-eval PRIVATE ${AST_LIBRARY})
    if(TARGET ast_vendored)
        add_dependencies(test-gwcs-eval ast_vendored)
    endif()
endif()


# -------- Build and run optional doc tests ----------------------------------
# The example programs embedded in README.rst and the usage pages are marked
# with the ``:test:`` option; each is extracted, compiled against the freshly
# built libasdf-gwcs, and run, so the documentation cannot drift from the API.
if(ENABLE_TESTING_DOCS)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    set(DOC_EXAMPLES_DIR ${CMAKE_CURRENT_BINARY_DIR}/doc_examples)
    set(DOC_FILES
        ${CMAKE_SOURCE_DIR}/README.rst
        ${CMAKE_SOURCE_DIR}/docs/usage/reading-writing.rst
        ${CMAKE_SOURCE_DIR}/docs/usage/evaluation.rst
    )
    file(MAKE_DIRECTORY ${DOC_EXAMPLES_DIR})
    set(EXTRACT_DOC_EXAMPLES ${CMAKE_CURRENT_SOURCE_DIR}/scripts/extract_doc_examples.py)
    set(TEST_DOC_EXAMPLES ${DOC_EXAMPLES_DIR}/test-doc-examples.sh)

    # List the doctests to build, one per line: "name" or "name,arg" where arg
    # is the resolved fixture passed to the program.
    execute_process(
        COMMAND ${Python3_EXECUTABLE} ${EXTRACT_DOC_EXAMPLES}
                --list-tests
                --fixtures-dir ${CMAKE_CURRENT_SOURCE_DIR}/fixtures
                --out-dir ${DOC_EXAMPLES_DIR}
                ${DOC_FILES}
        OUTPUT_VARIABLE DOC_TEST_LIST
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    string(REGEX REPLACE "\n" ";" DOC_TEST_LINES "${DOC_TEST_LIST}")

    set(DOC_TESTS "")
    set(DOC_TEST_SOURCES "")
    foreach (line IN LISTS DOC_TEST_LINES)
        string(REPLACE "," ";" parts "${line}")
        list(GET parts 0 doctest)
        list(LENGTH parts nparts)
        if (nparts GREATER 1)
            list(GET parts 1 DOC_TEST_ARG_${doctest})
        else()
            set(DOC_TEST_ARG_${doctest} "")
        endif()
        list(APPEND DOC_TESTS ${doctest})
        list(APPEND DOC_TEST_SOURCES ${DOC_EXAMPLES_DIR}/${doctest}.c)
    endforeach()

    add_custom_command(
        OUTPUT ${TEST_DOC_EXAMPLES}
        COMMAND ${Python3_EXECUTABLE}
                ${EXTRACT_DOC_EXAMPLES}
                ${DOC_FILES}
                --out-dir ${DOC_EXAMPLES_DIR}
                --fixtures-dir ${CMAKE_CURRENT_SOURCE_DIR}/fixtures
        DEPENDS ${DOC_FILES} ${EXTRACT_DOC_EXAMPLES} libasdf-gwcs
        BYPRODUCTS ${DOC_TEST_SOURCES}
        COMMENT "Generating doc example sources"
        VERBATIM
    )

    add_custom_target(extract-doc-examples DEPENDS ${TEST_DOC_EXAMPLES})

    foreach (doctest IN LISTS DOC_TESTS)
        add_executable(${doctest} ${DOC_EXAMPLES_DIR}/${doctest}.c)
        # The project's own headers must precede any installed copy.
        target_include_directories(${doctest} BEFORE PRIVATE
            ${CMAKE_SOURCE_DIR}/include)
        target_include_directories(${doctest} SYSTEM PRIVATE
            ${LIBASDF_INCLUDE_DIRS})
        target_link_libraries(${doctest} PRIVATE libasdf-gwcs ${LIBASDF_LIBRARIES})
        add_dependencies(${doctest} extract-doc-examples)
        if (DOC_TEST_ARG_${doctest})
            add_test(NAME ${doctest}
                     COMMAND ${doctest} ${DOC_TEST_ARG_${doctest}})
        else()
            add_test(NAME ${doctest} COMMAND ${doctest})
        endif()
        set_property(TEST ${doctest}
            PROPERTY ENVIRONMENT_MODIFICATION "${runtime}")
    endforeach()
endif()
