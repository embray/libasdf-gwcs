AM_CPPFLAGS = \
    -I$(top_srcdir)/include \
    -I$(top_srcdir)/third_party/STC/include \
    -I$(top_srcdir)/src

munit_dir = $(top_builddir)/tests/munit
munit_submodule = $(munit_dir)/.git
munit_cflags = -std=gnu11 -I$(top_srcdir)/tests

$(munit_submodule):
	@if test -d $(top_srcdir)/.git; then \
	    echo "Initializing submodule tests/munit ..."; \
	    git submodule update --init tests/munit; \
	else \
	    echo "Skipping submodule init: not in a Git repository"; \
	fi

check_PROGRAMS = test-gwcs.unit test-gwcs-eval.unit

TESTS_ENVIRONMENT = top_builddir=$(top_builddir) top_srcdir=$(top_srcdir)
TESTS = $(check_PROGRAMS)

unit_test_cppflags = \
    $(AM_CPPFLAGS) \
    -DREFERENCE_FILES_DIR=\"$(abs_srcdir)/fixtures\" \
    -DFIXTURES_DIR=\"$(abs_srcdir)/fixtures\" \
    -DTEMP_DIR=\"$(abs_builddir)/tmp\" \
    -D_GNU_SOURCE

unit_test_cflags = $(munit_cflags) $(LIBASDF_CFLAGS) $(ASDF_GWCS_CFLAGS)
unit_test_ldflags = $(LDFLAGS)

if DEBUG
unit_test_cflags += -DMUNIT_NO_FORK
unit_test_ldflags += -rdynamic
endif

unit_test_ldadd = libmunit.a $(top_builddir)/libasdf-gwcs.la $(LIBASDF_LIBS)
if HAVE_AST
unit_test_ldadd += $(AST_LIBS) -lm
endif

check_LIBRARIES = libmunit.a
libmunit_a_SOURCES = util.c $(munit_dir)/munit.c
libmunit_a_CPPFLAGS = $(unit_test_cppflags)
libmunit_a_CFLAGS = $(unit_test_cflags) -w

# test-gwcs.unit
test_gwcs_unit_SOURCES = test-gwcs.c
test_gwcs_unit_CPPFLAGS = $(unit_test_cppflags)
test_gwcs_unit_CFLAGS = $(unit_test_cflags)
test_gwcs_unit_LDFLAGS = $(unit_test_ldflags)
test_gwcs_unit_LDADD = $(unit_test_ldadd)

# test-gwcs-eval.unit
test_gwcs_eval_unit_SOURCES = test-gwcs-eval.c
test_gwcs_eval_unit_CFLAGS = $(unit_test_cflags) $(AST_CFLAGS)
test_gwcs_eval_unit_LDFLAGS = $(unit_test_ldflags)
test_gwcs_eval_unit_LDADD = $(unit_test_ldadd) $(AST_LIBS)

if HAVE_AST
test_gwcs_eval_unit_CPPFLAGS = $(unit_test_cppflags) -DHAVE_AST
else
test_gwcs_eval_unit_CPPFLAGS = $(unit_test_cppflags)
endif

roman_build21_fixtures = \
    fixtures/roman/build21/r0000101001001001001_0001_wfi01_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi02_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi03_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi04_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi05_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi06_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi07_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi08_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi09_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi10_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi11_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi12_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi13_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi14_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi15_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi16_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi17_f158_cal.asdf \
    fixtures/roman/build21/r0000101001001001001_0001_wfi18_f158_cal.asdf

roman_build21_refs = \
    fixtures/roman/build21/ast_wcs_results.csv \
    fixtures/roman/build21/gwcs_wcs_results.csv

# Check the examples in the documentation
#
# The example programs embedded in README.rst and the usage pages are marked
# with the ``:test:`` option (see scripts/extract_doc_examples.py); each is
# extracted to a .c file, compiled against the freshly built libasdf-gwcs, and
# run as part of the test suite so the documentation cannot drift from the API.
if HAVE_PYTHON
DOC_EXAMPLES_DIR = $(builddir)/doc_examples

DOC_EXAMPLE_FILES = \
    $(top_srcdir)/README.rst \
    $(top_srcdir)/docs/usage/reading-writing.rst \
    $(top_srcdir)/docs/usage/evaluation.rst

# The extracted examples are compiled against the public headers, so a header
# change must force them to be rebuilt; otherwise a stale example binary can be
# run against a newer library with a different struct layout.
doc_example_headers = \
    $(wildcard $(top_srcdir)/include/asdf/gwcs/*.h) \
    $(wildcard $(top_srcdir)/include/asdf/gwcs/*/*.h) \
    $(wildcard $(top_srcdir)/include/asdf/gwcs/*/*/*.h)

DOC_EXAMPLE_DEPS = \
    $(DOC_EXAMPLE_FILES) \
    $(doc_example_headers) \
    $(srcdir)/scripts/extract_doc_examples.py \
    $(top_builddir)/libasdf-gwcs.la

TESTS += $(DOC_EXAMPLES_DIR)/test-doc-examples.sh

$(DOC_EXAMPLES_DIR)/test-doc-examples.sh: $(DOC_EXAMPLE_DEPS)
	$(AM_V_at)$(PYTHON3) $(srcdir)/scripts/extract_doc_examples.py \
	  $(DOC_EXAMPLE_FILES) \
	  --out-dir $(DOC_EXAMPLES_DIR) \
	  --fixtures-dir $(abs_srcdir)/fixtures $(QUIET_OUT)
	$(AM_V_at)for f in $(DOC_EXAMPLES_DIR)/*.c; do \
	    exe=$${f%.c}; \
	    $(LIBTOOL) --mode=link $(CC) \
	      -I$(top_srcdir)/include \
	      $(LIBASDF_CFLAGS) $(ASDF_GWCS_CFLAGS) \
	      $(unit_test_ldflags) \
	      $$f $(top_builddir)/libasdf-gwcs.la $(LIBASDF_LIBS) \
	      -o $$exe $(QUIET_OUT); \
	done
endif

QUIET_OUT = $(if $(filter 1,$(V)),, > /dev/null)

# CMake-related files to include in the distribution
CMAKE_DIST = CMakeLists.txt

EXTRA_DIST = \
    $(CMAKE_DIST) \
    munit.h \
    util.h \
    munit/COPYING \
    munit/munit.h \
    fixtures/roman_l2_wcs.asdf \
    fixtures/roman_l3_wcs.asdf \
    $(roman_build21_fixtures) \
    $(roman_build21_refs) \
    scripts/create_roman_fixture.py \
    scripts/extract_doc_examples.py

# Clean up extracted doc examples, and the per-run temp directories the test
# binaries create (their .pgid-* coordination files outlive the run by design,
# so nothing else removes them).
distclean-local:
	rm -rf $(builddir)/doc_examples $(builddir)/tmp

check-local: $(munit_submodule)
