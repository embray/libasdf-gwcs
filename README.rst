libasdf-gwcs
############

.. _begin-badges:

.. image:: https://github.com/asdf-format/libasdf-gwcs/workflows/Build/badge.svg
    :target: https://github.com/asdf-format/libasdf-gwcs/actions
    :alt: CI Status

.. _end-badges:

A `libasdf <https://github.com/asdf-format/libasdf>`__ extension library
implementing `GWCS <https://gwcs.readthedocs.io/>`__ (Generalized World
Coordinate System) support for ASDF files containing WCS transforms and
coordinate frames.


Introduction
============

libasdf-gwcs does two fairly different things.

The first is **(de)serialization**.  It registers extension types with libasdf
for the GWCS schemas, so that reading an ASDF file gives you WCS objects,
transforms and coordinate frames as C-native data structures rather than as
anonymous YAML mappings, and writes them back out again.  Three families of
schema are implemented:

* ``tag:stsci.edu:gwcs/``—the WCS object, its steps, and its coordinate
  frames (``frame``, ``frame2d``, ``celestial_frame``, etc.).
* ``tag:stsci.edu:asdf/transform/``—around forty transform (model) types,
  from ``shift`` and ``affine`` through the full set of spherical projections.
* ``tag:stsci.edu:asdf/coordinates/frames/``—the `Astropy-compatible
  reference frames
  <https://docs.astropy.org/en/stable/coordinates/index.html#built-in-frame-classes>`__
  attached to celestial frames (ICRS, Galactic, FK5, FK4, FK4NoETerms, etc.).

The second, and the more interesting one, is **evaluation**: actually applying
a WCS to coordinates.  Reading a WCS tells you how the pipeline is built;
evaluating it turns detector pixels into sky coordinates.  libasdf-gwcs ships
an evaluation engine that does this for real files, at speed, from C.

.. note::

   A note on terminology: throughout this documentation we use "GWCS" and "WCS"
   mostly interchangeably.  Where the distinction matters, it's that "WCS"
   refers to the general concept of a World Coordinate System (and not limited
   to the FITS WCS specification), whereas GWCS is the particular
   representation model for a WCS as defined by the ``gwcs`` Python package
   and associated ASDF schemas.


.. _getting-started:

Getting Started
===============

libasdf-gwcs is a plugin library for libasdf. Install libasdf first, then build
libasdf-gwcs pointing to it via ``PKG_CONFIG_PATH``.

**Autotools**:

.. code:: console

    $ ./autogen.sh
    $ ./configure PKG_CONFIG_PATH=/path/to/libasdf/lib/pkgconfig
    $ make
    $ sudo make install

**CMake**:

.. code:: console

    $ mkdir build && cd build
    $ cmake .. -DCMAKE_PREFIX_PATH=/path/to/libasdf -DENABLE_TESTING=YES
    $ make
    $ sudo make install

Note that the repository uses git submodules (for AST, STC and the µnit unit
test framework), so clone it with ``--recurse-submodules``:

.. code:: console

    $ git clone --recurse-submodules git@github.com:asdf-format/libasdf-gwcs.git

The build system also makes an effort to sync submodules when necessary but
this isn't always 100% reliable so it's best to go ahead and do that when
building from the git repository.


.. _linking:

Using libasdf-gwcs in your project
----------------------------------

libasdf extensions register themselves when the shared library that defines
them is loaded.  In practice that means your program must **link against both
libasdf-gwcs and libasdf**—there is currently no other supported mechanism
for loading third-party libasdf extensions, so the linkage has to be there at
build time, though in principle you could also use ``dlopen``.

libasdf-gwcs installs a pkg-config file which pulls libasdf in for you:

.. code:: console

    $ gcc myprog.c -o myprog $(pkg-config --cflags --libs libasdf-gwcs)

or, spelled out by hand:

.. code:: console

    $ gcc myprog.c -o myprog -lasdf-gwcs -lasdf

Include the umbrella header, alongside libasdf's own:

.. code:: c

   #include <asdf.h>
   #include <asdf/gwcs/gwcs.h>


Reading a WCS
-------------

This example opens a file, locates a WCS in it, and prints the pipeline.

It takes the file as its first argument and, optionally, the path to the WCS
within the ASDF tree as its second.  With no path given it searches the tree for
the first GWCS it can find—``asdf_value_is_gwcs`` is one of the predicates
the extension generates, and has exactly the signature libasdf's
``asdf_value_find`` expects, so the two compose directly.

.. code:: c
   :test: test-gwcs-inspect
   :fixture: roman_l2_wcs.asdf

   #include <inttypes.h>
   #include <stdbool.h>
   #include <stdio.h>
   #include <asdf.h>
   #include <asdf/gwcs/gwcs.h>

   // Composite transforms nest arbitrarily deep, so the walk through the
   // transform tree truncates here for demonstration purposes; increase
   // it to see more of the tree.
   #define MAX_DEPTH 3

   int main(int argc, char **argv) {
       if (argc < 2) {
           fprintf(stderr, "usage: %s FILE [TREE-PATH]\n", argv[0]);
           return 1;
       }

       asdf_file_t *file = asdf_open(argv[1], "r");

       if (!file) {
           fprintf(stderr, "error opening %s\n", argv[1]);
           return 1;
       }

       asdf_gwcs_t *wcs = NULL;
       asdf_value_t *root = NULL;
       asdf_value_t *found = NULL;

       if (argc > 2) {
           // An explicit tree path was given: read the WCS directly.
           if (asdf_get_gwcs(file, argv[2], &wcs) != ASDF_VALUE_OK) {
               fprintf(stderr, "no GWCS at %s\n", argv[2]);
               return 1;
           }

           printf("WCS at: %s\n", argv[2]);
       } else {
           // Otherwise search the tree for the first GWCS in it.
           root = asdf_get_value(file, "");
           found = asdf_value_find(root, asdf_value_is_gwcs);

           if (!found) {
               fprintf(stderr, "no GWCS found in %s\n", argv[1]);
               return 1;
           }

           printf("WCS at: %s\n", asdf_value_path(found));
           asdf_value_as_gwcs(found, &wcs);
       }

       printf("name: %s\n", wcs->name ? wcs->name : "(unnamed)");

       if (wcs->pixel_shape) {
           printf("pixel_shape: [");

           for (uint32_t idx = 0; idx < wcs->pixel_ndim; idx++) {
               if (idx > 0)
                   fputs(", ", stdout);

               printf("%" PRIu64, wcs->pixel_shape[idx]);
           }

           printf("]\n");
       }

       printf("steps: %" PRIu32 "\n", wcs->n_steps);

       for (uint32_t idx = 0; idx < wcs->n_steps; idx++) {
           const asdf_gwcs_step_t *step = &wcs->steps[idx];
           const asdf_gwcs_frame_t *frame = step->frame;

           printf("[%d] %s (%s)\n", idx,
                  frame && frame->name ? frame->name : "(unnamed)",
                  frame ? asdf_gwcs_frame_type_name(frame) : "?");

           // The final step has no transform: it only names the frame that
           // the pipeline ends in.
           if (!step->transform)
               continue;

           // The step's transform, followed by everything nested beneath it
           // up to MAX_DEPTH.
           // Print a tree display of the step's transform and nested composite
           // transforms.
           asdf_gwcs_transform_iter_t *iter =
               asdf_gwcs_transform_iter_init(step->transform, MAX_DEPTH);

           const asdf_gwcs_transform_t *transform = step->transform;
           bool last = true;
           int depth = 0;

           // Bit d records whether the ancestor at depth d was the last of its
           // siblings, which is what decides between a "│" and a blank.
           uint32_t last_ancestors = 0;

           for (;;) {
               fputs(" ", stdout);

               for (int level = 0; level < depth; level++)
                   fputs((last_ancestors >> level) & 1 ? "   " : "│  ", stdout);

               printf("%s %s", last ? "└─" : "├─",
                      asdf_gwcs_transform_type_name(transform));

               // A transform may also carry a name of its own, which is the
               // file author's label for it rather than its type.
               if (transform->name)
                   printf(" (%s)", transform->name);

               printf("\n");

               if (last)
                   last_ancestors |= 1u << depth;
               else
                   last_ancestors &= ~(1u << depth);

               if (!asdf_gwcs_transform_iter_next(&iter))
                   break;

               transform = iter->value;
               last = iter->index + 1 == iter->size;
               depth = iter->depth + 1;
           }
       }

       asdf_value_destroy(found);
       asdf_value_destroy(root);
       asdf_gwcs_destroy(wcs);
       asdf_close(file);
       return 0;
   }

Compile and run it against one of the test files:

.. code:: console

   $ gcc gwcs-inspect.c -o gwcs-inspect $(pkg-config --cflags --libs libasdf-gwcs)
   $ ./gwcs-inspect tests/fixtures/roman_l2_wcs.asdf

which prints::

    WCS at: /roman/meta/wcs
    name: FIT-LVL2-GAIADR3_S3
    steps: 5
    [0] detector (frame2d)
     └─ compose
        ├─ compose
        │  ├─ compose
        │  │  ├─ concatenate
        │  │  │  ├─ shift
        │  │  │  └─ shift
        │  │  └─ concatenate
        │  │     ├─ shift
        │  │     └─ shift
        │  └─ compose
        │     ├─ compose
        │     │  ├─ remap_axes
        │     │  └─ concatenate
        │     └─ compose
        │        ├─ remap_axes
        │        └─ concatenate
        └─ concatenate
           ├─ shift
           └─ shift
    [1] v2v3 (frame2d)
     └─ compose (DVA_Correction)
        ├─ concatenate
        │  ├─ scale (dva_scale_v2)
        │  └─ scale (dva_scale_v3)
        └─ concatenate
           ├─ shift (dva_v2_shift)
           └─ shift (dva_v3_shift)
    [2] v2v3vacorr (frame2d)
     └─ compose (JWST tangent-plane linear correction. v1)
        ├─ compose
        │  ├─ compose
        │  │  ├─ compose
        │  │  │  ├─ compose
        │  │  │  └─ compose (TAN to cartesian 3D)
        │  │  └─ rotate_sequence_3d (optic_axis_to_det)
        │  └─ spherical_cartesian (c2s)
        └─ concatenate (deg_to_arcsec_2D)
           ├─ scale (deg_to_arcsec_1D)
           └─ scale (deg_to_arcsec_1D)
    [3] v2v3corr (frame2d)
     └─ compose (v23tosky)
        ├─ compose
        │  ├─ compose
        │  │  ├─ concatenate
        │  │  │  ├─ scale
        │  │  │  └─ scale
        │  │  └─ spherical_cartesian
        │  └─ rotate_sequence_3d
        └─ spherical_cartesian
    [4] world (celestial_frame)

The last step has no transform, since it only names the frame the pipeline
ends in.

Most transform types are leaves, but ``compose``, ``concatenate`` and
``divide``, etc. are built out of other transforms.  The iterator descends into
whatever a given transform holds, without the caller needing to know how that
type stores its parts, and ``MAX_DEPTH`` bounds the depth.

``pixel_shape`` is optional, and this particular file records it as ``null``,
which is why no shape is printed.  A file that does carry one, such as
``roman_l3_wcs.asdf``, reports it:

.. code:: console

    $ ./gwcs-inspect tests/fixtures/roman_l3_wcs.asdf
    WCS at: /wcs
    name: 270p65x48y69
    pixel_shape: [5000, 5000]
    steps: 2
    [0] detector (frame2d)
     └─ fitswcs_imaging
    [1] icrs (celestial_frame)


Evaluating a WCS
----------------

The second example evaluates the same WCS on a handful of pixels.

.. code:: c
   :test: test-gwcs-evaluate
   :fixture: roman_l2_wcs.asdf

   #include <stdio.h>
   #include <asdf.h>
   #include <asdf/gwcs/gwcs.h>

   #define NPIX 4

   int main(int argc, char **argv) {
       if (argc < 2) {
           fprintf(stderr, "usage: %s FILE [TREE-PATH]\n", argv[0]);
           return 1;
       }

       // Evaluation is done by a backend; "ast_yaml" is the only one
       // currently built-in
       const asdf_gwcs_backend_t *backend = asdf_gwcs_backend_get("ast_yaml");

       if (!backend) {
           fprintf(stderr, "built without the ast_yaml backend; "
                           "cannot evaluate this WCS\n");
           return 0;
       }

       asdf_file_t *file = asdf_open(argv[1], "r");

       if (!file) {
           fprintf(stderr, "error opening %s\n", argv[1]);
           return 1;
       }

       asdf_gwcs_t *wcs = NULL;
       asdf_value_t *root = NULL;
       asdf_value_t *found = NULL;

       if (argc > 2) {
           if (asdf_get_gwcs(file, argv[2], &wcs) != ASDF_VALUE_OK) {
               fprintf(stderr, "no GWCS at %s\n", argv[2]);
               return 1;
           }
       } else {
           root = asdf_get_value(file, "");
           found = asdf_value_find(root, asdf_value_is_gwcs);

           if (!found) {
               fprintf(stderr, "no GWCS found in %s\n", argv[1]);
               return 1;
           }

           asdf_value_as_gwcs(found, &wcs);
       }

       // Loading the WCS into the backend is done once, then reused.
       asdf_gwcs_err_t err = ASDF_GWCS_OK;
       asdf_gwcs_eval_t *eval = asdf_gwcs_eval_create(file, wcs, backend, &err);

       if (!eval) {
           fprintf(stderr, "could not prepare the WCS: %s\n",
                   asdf_gwcs_strerror(err));
           return 1;
       }

       // Evaluate the pipeline's forward transformation for a file that
       // maps detector pixels to sky coordinates, in degrees.
       const double xin[NPIX] = {0.0, 2043.5, 4087.0, 100.0};
       const double yin[NPIX] = {0.0, 2043.5, 4087.0, 3988.0};
       double xout[NPIX];
       double yout[NPIX];

       err = asdf_gwcs_eval_2d(eval, xin, yin, xout, yout, NPIX);

       if (err != ASDF_GWCS_OK) {
           fprintf(stderr, "evaluation failed: %s\n", asdf_gwcs_strerror(err));
           return 1;
       }

       printf("%10s %10s %14s %14s\n", "x", "y", "ra", "dec");

       for (int idx = 0; idx < NPIX; idx++)
           printf("%10.1f %10.1f %14.8f %14.8f\n",
                  xin[idx], yin[idx], xout[idx], yout[idx]);

       asdf_gwcs_eval_destroy(eval);
       asdf_value_destroy(found);
       asdf_value_destroy(root);
       asdf_gwcs_destroy(wcs);
       asdf_close(file);
       return 0;
   }

Running it the same way should produce something like:

.. code:: console

    $ ./gwcs-evaluate tests/fixtures/roman_l2_wcs.asdf
             x          y             ra            dec
           0.0        0.0   -90.01309156    65.97427993
        2043.5     2043.5   -90.16747433    66.03550957
        4087.0     4087.0   -90.32317878    66.09718049
         100.0     3988.0   -90.02087992    66.09421294

Sky coordinates come back in degrees, with longitude in ``[-180, 180]``.

.. note::

    Python's GWCS reports the same positions in ``[0, 360)`` by default, so
    ``-90.013`` here is equivalent to ``269.987``.

A GWCS pipeline can begin and end in any coordinate frame, so a stored WCS is
not inherently "pixel to world"—that is simply the common case.  What
libasdf-gwcs evaluates is the **forward** transformation of the pipeline as
stored.  Evaluating the reverse direction, whether from a stored analytic
inverse or by solving numerically, is not yet supported.

More detail, including grid evaluation, is in the `usage documentation
<https://libasdf-gwcs.readthedocs.io/en/latest/usage/evaluation.html>`__.


Evaluation backends
===================

Evaluation is performed by a pluggable *backend*, described by
``asdf/gwcs/backend.h``.  A backend is looked up by name:

.. code:: c

   const asdf_gwcs_backend_t *backend = asdf_gwcs_backend_get("ast_yaml");

and passing ``NULL`` where a backend is expected selects a default.

The backend interface is **experimental**.  It is not currently supported for
third-party plugins: the interface is still being worked out and will change,
so for now it is deliberately not usable from outside the library.  Support for
third-party evaluation backends is planned for a future release, once the
design has settled.


.. _ast-backend:

AST support
-----------

`Starlink AST <https://starlink.eao.hawaii.edu/starlink/AST>`__ is currently
the **only** supported evaluation backend, registered under the name
``ast_yaml``.

A copy of AST is vendored with the libasdf-gwcs source, as a git submodule
under ``third_party/ast``.  There are a few things to know about it:

* **It is a fork.** AST support presently works only with the custom fork that
  is vendored here, which carries updates to `YamlChan
  <https://starlink.eao.hawaii.edu/devdocs/sun211.htx/sun211ss549.html>`__ and
  other changes not yet available in upstream AST.  Building against an
  external AST is supported—both build systems fall back to searching the
  system for it when the submodule is not present—but a stock upstream AST will
  not work yet.

* **It is linked statically by default.** The vendored AST is built as a static
  library and linked into ``libasdf-gwcs``, so there is no separate AST shared
  library to deploy.

* **This is temporary.** Work is underway to upstream the changes AST needs.
  Once a released version of AST includes them, vendoring and statically
  linking this fork will no longer be necessary.

AST support can be disabled entirely:

============  ===========================================
Autotools     ``./configure --without-ast``
CMake         ``cmake .. -DASDF_GWCS_WITH_AST=OFF``
============  ===========================================

Without it, libasdf-gwcs still reads and writes GWCS objects exactly as before;
only evaluation becomes unavailable, and ``asdf_gwcs_eval_create`` reports
``ASDF_GWCS_ERR_BACKEND_NOT_AVAILABLE``.

.. note::

   The name ``"ast_yaml"`` for the AST backend is chosen because it is
   implemented on top of AST's own ``YamlChan`` interface which parses
   a GWCS defined in an ASDF file directly from the YAML text.

   This is a bit inefficient as libasdf-gwcs has to *re-serialize* the
   already parsed WCS back to YAML for this to work (though the overhead
   of this is typically marginal compared to WCS evaluation on several
   coordinate points).

   The backend name ``"ast"`` is reserved for a possible future backend that
   builds AST ``Mapping`` primitives in native C code directly from an already
   parsed WCS.


Development
===========

Building from git
-----------------

Requirements
^^^^^^^^^^^^

- `libasdf <https://github.com/asdf-format/libasdf>`__
- **CMake** or autotools (autoconf/automake/libtool)
- **pkg-config**
- **libstatgrab** (optional, for test utilities)

On **Debian/Ubuntu**:

.. code:: console

    $ sudo apt install build-essential pkg-config libstatgrab-dev

On **macOS** (with Homebrew):

.. code:: console

    $ brew install pkg-config libstatgrab

Notes
^^^^^

- Run ``make check`` (autotools) or ``ctest`` (CMake) to run tests.


.. _licensing:

Licensing
=========

libasdf-gwcs is distributed under a three-clause BSD license (see ``LICENSE``).
AST is licensed under the **GNU Lesser General Public License, version 3 or
later**.  Because AST is statically linked into libasdf-gwcs by default, that
combination deserves a clear explanation.

**Distributing source is unaffected.**  libasdf-gwcs's own source remains under
its BSD license and AST's source remains under the LGPL.  Nothing about
shipping the source tree, as this project does, is complicated by the two
licenses coexisting.

**Distributing binaries is where the LGPL applies.**  A libasdf-gwcs binary
with AST linked into it is what the LGPL calls a *Combined Work*.  It is a
common misconception that this makes the result LGPL-licensed; it does not.
Section 4 of the LGPLv3 explicitly permits conveying a Combined Work "under
terms of your choice"—libasdf-gwcs's BSD licensing is not displaced—as
long as those terms do not restrict modification of the AST portions or reverse
engineering for debugging such modifications (BSD terms plainly do not), and as
long as you also:

* **(§4a)** give prominent notice that AST is used in it and that AST is
  covered by the LGPL;
* **(§4b)** accompany it with a copy of both the GPLv3 and the LGPLv3;
* **(§4c)** include AST's copyright notice among any copyright notices the
  program displays while running;
* **(§4d)** do *one* of the following:

  * **(§4d0)** provide AST's Minimal Corresponding Source, plus the application
    code in a form that lets the recipient relink it against a modified version
    of AST; or
  * **(§4d1)** link AST through a shared-library mechanism that uses a copy
    already present on the user's system and works with an interface-compatible
    modified version.

  Because the AST here is a *fork*, linked statically, option §4d1 is not
  available—so §4d0 is the applicable route.

* **(§4e)** provide Installation Information, but only in the cases where
  GPLv3 §6 would require it (essentially, User Products); this does not arise
  for an ordinary library distribution.

**In practice libasdf-gwcs already satisfies §4d0**, because its own source is
published under a license that permits relinking against a modified AST.  The
obligations above are therefore mostly a concern for *downstream* users who
embed libasdf-gwcs, with AST statically linked, into a **proprietary**
application: they take on §4a–§4d with respect to the AST portion.

Anyone who would rather avoid the question entirely can build with
``--without-ast`` / ``-DASDF_GWCS_WITH_AST=OFF``, which yields a purely
BSD-licensed library without evaluation support.

Note also that AST itself bundles further components under their own terms,
including ERFA (BSD-3-Clause-style, derived from the IAU's SOFA), PAL, WCSLIB
and CMINPACK.  Their license texts ship within ``third_party/ast``.

*This summary is offered in good faith to explain the project's licensing
structure based on my understanding; it is not legal advice.*
