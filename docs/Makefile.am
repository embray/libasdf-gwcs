# One page per public header, each a hawkmoth autodoc directive
api_header_pages = \
    api/backend.h.rst \
    api/coordinates/baseframe.h.rst \
    api/coordinates/fk.h.rst \
    api/core.h.rst \
    api/eval.h.rst \
    api/fitswcs_imaging.h.rst \
    api/frame.h.rst \
    api/frame2d.h.rst \
    api/frame_celestial.h.rst \
    api/grid.h.rst \
    api/gwcs.h.rst \
    api/step.h.rst \
    api/transform/affine.h.rst \
    api/transform/compose.h.rst \
    api/transform/concatenate.h.rst \
    api/transform/constant.h.rst \
    api/transform/divide.h.rst \
    api/transform/identity.h.rst \
    api/transform/polynomial.h.rst \
    api/transform/property/bounding_box.h.rst \
    api/transform/remap_axes.h.rst \
    api/transform/rotate_sequence_3d.h.rst \
    api/transform/scale.h.rst \
    api/transform/shift.h.rst \
    api/transform/spherical_cartesian.h.rst \
    api/transform/transform.h.rst \
    api/wcs.h.rst

# CMake-related files to include in the distribution
CMAKE_DIST = CMakeLists.txt

# Local Sphinx extensions; see docs/_ext/
SPHINX_EXT_DIST = \
    _ext/c_autosummary.py \
    _ext/index_grouping.py \
    _ext/schema_roles.py

EXTRA_DIST = \
    $(CMAKE_DIST) \
    $(SPHINX_EXT_DIST) \
    conf.py \
    changes.rst \
    development.rst \
    environment.yml \
    index.rst \
    links.rst \
    usage/reading-writing.rst \
    usage/evaluation.rst \
    api/index.rst \
    api/core.rst \
    api/wcs.rst \
    api/frames.rst \
    api/transforms.rst \
    api/evaluation.rst \
    $(api_header_pages) \
    _static/css/globalnav.css \
    _static/images/favicon.ico \
    _static/images/logo-dark-mode.png \
    _static/images/logo-light-mode.png
