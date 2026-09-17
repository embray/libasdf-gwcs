include(AddressAnalyzer)

option(ASDF_GWCS_WITH_AST "Enable AST evaluation backend" ON)

# Documentation
option(ENABLE_DOCS "Build the Sphinx documentation" OFF)
if (ENABLE_DOCS)
    set(SPHINX_FLAGS "-W" CACHE STRING "Flags to pass to sphinx-build")
endif ()

# Testing
option(ENABLE_TESTING "Enable unit tests" OFF)
option(ENABLE_TESTING_DOCS "Enable testing doc examples" OFF)
option(ENABLE_TESTING_ALL "Enable all tests (unit, doc examples, etc.)" OFF)

if(ENABLE_TESTING_ALL)
    set(ENABLE_TESTING YES CACHE BOOL "" FORCE)
    set(ENABLE_TESTING_DOCS YES CACHE BOOL "" FORCE)
endif()

set(CPACK_PACKAGE_VENDOR "STScI")
set(CPACK_SOURCE_GENERATOR "TGZ")
set(CPACK_SOURCE_IGNORE_FILES
        \\.git/
        \\.github/
        \\.idea/
        "cmake-.*/"
        build/
        ".*~$"
)
set(CPACK_VERBATIM_VARIABLES YES)
include(CPack)
