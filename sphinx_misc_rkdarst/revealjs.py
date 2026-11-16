"""
revealjs - Turn any Sphinx page into a reveal.js presentation, in place.

The page is built completely normally.  Appending ``?revealjs`` to the
URL activates a small bootstrap script (loaded on every page) which
lazily loads reveal.js and transforms the page content into a
presentation, entirely client side.  Everything is static: no
server-side component, no separate output, no second build.

Slide splitting rules
---------------------

- The document title (h1) and any content before the first section
  become the title slide.
- Each top-level section (a ``<section>`` element in modern docutils
  output, ``<div class="section">`` in older ones) becomes a horizontal
  slide.  Nested sections become vertical (sub)slides.
- A transition line of at least four dashes (``----`` in reST, which
  emits an ``<hr>``; ``---`` in MyST) forces a slide break inside the
  current section, if :confval:`revealjs_break_on_hr` is true.

The ``_static/revealjs/`` directory contains our ``bootstrap.js``,
``transform.js`` and ``presentation.css``, plus all vendored reveal.js
files under ``upstream/`` - reveal.js 5.2.1, MIT license (everything
under ``upstream/`` is upstream code, see ``upstream/LICENSE`` there).
``bootstrap.js`` is loaded on every page but does nothing unless the
URL parameter is present.

Configuration
-------------

``revealjs_url_param``
    URL query parameter that activates presentation mode.  Default:
    ``'revealjs'``.

``revealjs_theme``
    Name of a reveal.js theme to load for the presentation (files from
    ``_static/revealjs/upstream/theme/<name>.min.css``).  Default:
    ``'simple'``.  Set to ``''`` to not load any reveal theme.

``revealjs_break_on_hr``
    Treat ``<hr>`` elements (``----`` transitions) as forced slide
    breaks.  Default: ``True``.
"""

from __future__ import annotations

from pathlib import Path

from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata

_STATIC = Path(__file__).parent / '_static'

# Builders that render HTML pages but should not include the bootstrap
# script (e.g. the epub builder, where scripts are inappropriate).
_EXCLUDED_BUILDERS = {'epub'}


def _add_html_assets(app: Sphinx) -> None:
    """Connect to 'builder-inited': register assets and static path."""
    builder = getattr(app, 'builder', None)
    if builder is None:
        return
    if getattr(builder, 'format', None) != 'html':
        return
    if getattr(builder, 'name', None) in _EXCLUDED_BUILDERS:
        return

    static_path = str(_STATIC)
    if static_path not in app.config.html_static_path:
        app.config.html_static_path.append(static_path)

    # The bootstrap script is the only thing loaded on every page; it
    # reads its configuration from these data attributes and lazily
    # loads everything else only when the URL parameter is present.
    app.add_js_file('revealjs/bootstrap.js', **{
        'data-param': str(app.config.revealjs_url_param),
        'data-theme': str(app.config.revealjs_theme),
        'data-break-on-hr': 'true' if app.config.revealjs_break_on_hr else 'false',
    })


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value('revealjs_url_param', 'revealjs', 'html')
    app.add_config_value('revealjs_theme', 'simple', 'html')
    app.add_config_value('revealjs_break_on_hr', True, 'html')

    app.connect('builder-inited', _add_html_assets)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
