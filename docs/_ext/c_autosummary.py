"""
An autosummary-style overview table for the C domain.

``sphinx.ext.autosummary`` builds a table of names against the first sentence of
each docstring, but it is written against the Python domain throughout.

This adds ``.. c:autosummary::``, as an extension to Hawkmoth, which fills the
same role for C:

.. code-block:: rst

   .. c:autosummary::
      :header: Transform Summary
      :widths: 25 75

      affine <asdf_gwcs_affine_t>
      fitswcs_imaging <asdf_gwcs_fits_t>

Each content line is either ``name`` or ``display <name>``, the latter for when
the name to show differs from the declaration's own--a schema name against
the C type implementing it, say.

Declarations are read with hawkmoth's parser, the same one that generates the
API pages, so the docstrings are necessarily identical to what those pages
show.  Summaries come from autosummary's own ``extract_summary``, so the
"first stanza, then first sentence" rule matches upstream rather than being
reimplemented here.  Any C declaration kind works, not only structs.

Naming a declaration that the parser did not find is a warning, so a typo fails
the build under ``-W`` instead of quietly producing an empty row.

Configuration
-------------

``c_autosummary_headers``
    Globs, relative to ``hawkmoth_root``, of the headers to index.

The clang invocation is taken from hawkmoth's own ``hawkmoth_clang`` and
``hawkmoth_clang_c``.
"""

import inspect
import re
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.statemachine import StringList

from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

logger = logging.getLogger(__name__)


_DOMAIN_ROLES = {
    'StructDocstring': 'struct',
    'UnionDocstring': 'union',
    'EnumDocstring': 'enum',
    'EnumeratorDocstring': 'enumerator',
    'TypedefDocstring': 'type',
    'TypeAliasDocstring': 'type',
    'MacroDocstring': 'macro',
    'MacroFunctionDocstring': 'macro',
    'FunctionDocstring': 'func',
    'VarDocstring': 'var',
    'MemberDocstring': 'member',
}
"""
hawkmoth docstring class -> the C domain role that cross-references it

Ideally this would be a property on the individual classes, but it's not.
i.e. some ``EnumDoctring.directive == 'enum'``.  Something worth maybe
upstreaming a fix for.
"""


_index_cache = None
"""
Cached for the life of the process rather than on the build environment: the
environment is pickled between runs, so an index stored there would outlive
edits to the headers and silently serve stale summaries.
"""


def _extract_summary(body, document):
    """
    Call autosummary's ``extract_summary``, which took the document node
    before Sphinx 8.2 and its settings after.
    """
    from sphinx.ext.autosummary import extract_summary

    params = list(inspect.signature(extract_summary).parameters)
    takes_document = len(params) > 1 and params[1] == 'document'

    return extract_summary(body, document if takes_document
                           else document.settings)


def _docstring_body(lines):
    """Strip hawkmoth's leading directive line and un-indent what follows."""
    body = []
    seen_directive = False

    for line in lines:
        if not seen_directive:
            if line.lstrip().startswith('.. c:'):
                seen_directive = True
            continue

        body.append(line[3:] if line.startswith('   ') else line.strip())

    return body


def _build_index(config):
    """
    Index every documented C name as ``(role, docstring body)``

    Returns the index together with the headers it was built from, so callers
    can register them as dependencies.
    """
    global _index_cache

    if _index_cache is not None:
        return _index_cache

    from hawkmoth import parser
    from hawkmoth.docstring import DocstringProcessor

    processor = DocstringProcessor()
    clang_args = list(config.hawkmoth_clang) + list(config.hawkmoth_clang_c)
    root_dir = Path(config.hawkmoth_root)

    index = {}
    sources = []

    for pattern in config.c_autosummary_headers:
        for path in sorted(root_dir.glob(pattern)):
            try:
                root, _errors = parser.parse(
                    str(path), domain='c', clang_args=clang_args)
            except Exception as exc:  # a header we cannot parse has no entries
                logger.warning(
                    'c:autosummary: could not parse %s: %s', path, exc)
                continue

            sources.append(str(path))

            for doc in root.walk():
                name = doc.get_name()
                role = _DOMAIN_ROLES.get(type(doc).__name__)

                if not name or role is None or name in index:
                    continue

                lines, _offset = doc.get_docstring(processor)
                index[name] = (role, _docstring_body(lines))

    _index_cache = (index, sources)
    return _index_cache


class CAutosummary(SphinxDirective):
    """Build a two-column table of C declarations and their summaries."""

    has_content = True

    option_spec = {
        'header': directives.unchanged,
        'widths': directives.unchanged,
    }
    """
    Customize the table header

    This is one feature *not* found in Sphinx's autosummary...
    """

    def run(self):
        index, sources = _build_index(self.env.config)

        # Without this Sphinx does not know the page is derived from the
        # headers, and an incremental build would keep serving the summaries
        # read during the last full build.
        for source in sources:
            self.env.note_dependency(source)

        header = self.options.get('header', 'Name Summary').split(None, 1)
        widths = self.options.get('widths', '30 70')

        lines = [
            '.. list-table::',
            f'   :widths: {widths}',
            '   :header-rows: 1',
            '',
            f'   * - {header[0]}',
            f'     - {header[1] if len(header) > 1 else ""}',
        ]

        for entry in self.content:
            entry = entry.strip()

            if not entry:
                continue

            # display name <target>
            match = re.match(r'^(.*?)\s*<(.+)>$', entry)
            display, target = (
                (match.group(1).strip(), match.group(2).strip())
                if match else (None, entry))

            found = index.get(target)

            if found is None:
                logger.warning(
                    'c:autosummary: no documented C declaration named %r',
                    target, location=(self.env.docname, self.lineno))
                role, summary = 'expr', ''
            else:
                role, body = found
                summary = _extract_summary(body, self.state.document)

            title = f'{display} <{target}>' if display else target
            lines += [f'   * - :c:{role}:`{title}`', f'     - {summary}']

        node = nodes.Element()
        self.state.nested_parse(
            StringList(lines, source=''), self.content_offset, node)
        return node.children


def setup(app):
    app.setup_extension('hawkmoth')
    app.add_config_value('c_autosummary_headers', [], 'env')
    app.add_directive_to_domain('c', 'autosummary', CAutosummary)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
