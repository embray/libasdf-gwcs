if HAVE_AST
SUBDIRS = ast

# Automake would otherwise put ast in DIST_SUBDIRS unconditionally, and `make
# dist' would recurse into a build directory that a --without-ast build never
# created.
DIST_SUBDIRS = ast

# AST is LGPL-3.0-or-later and is statically linked into libasdf-gwcs, so its
# license text must accompany any binary distribution (LGPLv3 section 4b).
ast_licensedir = $(docdir)
ast_license_DATA = ast/COPYING
else

# With AST disabled its sources are not distributed at all, so the tarball
# could not build the evaluation backend even where AST is available.  Refuse
# rather than ship one that quietly cannot.
dist-hook:
	@echo "make dist: this tree was configured with --without-ast, so the" >&2
	@echo "tarball would omit the vendored AST sources entirely." >&2
	@echo "Configure with AST enabled to build a distribution." >&2
	@exit 1
endif

# AST is a build-only dependency; don't recurse into its test suite
check-recursive: ;

# third_party headers to include
stc_dir = STC

# The minimal subset of STC needed to build libasdf-gwcs, which uses STC only
# for its cstr-keyed hashmaps (see src/types/).  Everything else is unused for
#now.
#
# Derived from the compiler's own dependency output (the .deps/*.Plo files).
stc_headers = \
    $(stc_dir)/include/stc/common.h \
    $(stc_dir)/include/stc/cstr.h \
    $(stc_dir)/include/stc/hmap.h \
    $(stc_dir)/include/stc/types.h \
    $(stc_dir)/include/stc/priv/cstr_prv.c \
    $(stc_dir)/include/stc/priv/cstr_prv.h \
    $(stc_dir)/include/stc/priv/linkage.h \
    $(stc_dir)/include/stc/priv/linkage2.h \
    $(stc_dir)/include/stc/priv/template.h \
    $(stc_dir)/include/stc/priv/template2.h \
    $(stc_dir)/include/stc/priv/utf8_prv.h \
    $(stc_dir)/include/stc/sys/finalize.h

stc_src = \
    $(stc_dir)/src/cstr_core.c

noinst_HEADERS = $(stc_headers)
noinst_LTLIBRARIES = libstc.la

libstc_la_SOURCES = $(stc_src)
# libasdf vendors its own copy of STC, and if these symbols are exported the
# dynamic linker binds libasdf's cregex calls to the copy here, so libasdf
# compiles regexes with one STC and matches them with another (how this was
# noticed).  More generally, shouldn't export those symbols.
# See also https://github.com/asdf-format/libasdf/pull/247
# which fixes this on the libasdf side
libstc_la_CFLAGS = $(AM_CFLAGS) -fvisibility=hidden
libstc_la_LDFLAGS = $(AM_LDFLAGS) -lm

# CMake-related files to include in the distribution
CMAKE_DIST = CMakeLists.txt

EXTRA_DIST = \
    $(CMAKE_DIST) \
    $(stc_dir)/LICENSE

if HAVE_AST
EXTRA_DIST += ast/COPYING
endif
