"""
revealjs - Turn any Sphinx page into a reveal.js presentation, in place.

The page is built completely normally.  Appending ``?revealjs`` to the
URL activates a small bootstrap script (loaded on every page) which
lazily loads reveal.js and transforms the page content into a
presentation, entirely client side.  A URL parameter value selects the
theme at view time (``?revealjs=black`` presents with the black theme,
``?revealjs=none`` presents without any reveal theme).  Everything is
static: no server-side component, no separate output, no second build.

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
    ``'revealjs'``.  All URL forms activate (``?revealjs``,
    ``?revealjs=``, ``?revealjs=black``); a non-empty value selects the
    theme (see below).

``revealjs_theme``
    Name of a reveal.js theme to load for the presentation (files from
    ``_static/revealjs/upstream/theme/<name>.min.css``).  Default:
    ``'simple'``.  Set to ``''`` to not load any reveal theme.  The URL
    parameter value overrides this per view: ``?revealjs=<name>``
    presents with that theme, ``?revealjs=none`` presents with no
    theme, and an unknown name silently falls back to no theme (the
    404ing stylesheet is ignored).

``revealjs_break_on_hr``
    Treat ``<hr>`` elements (``----`` transitions) as forced slide
    breaks.  Default: ``True``.

``revealjs_font_scale``
    Rescales the presentation's base font size when no reveal theme is
    loaded: the deck base becomes a percentage of the page's ambient
    body text size.  When a theme is loaded, the theme's own base font
    size (e.g. 40px) and type ratios are used as-is, so this has no
    effect.  Default: ``1.0``.

``revealjs_options``
    Extra `reveal.js options <https://revealjs.com/config/>`__ as a
    dict, applied on every page, e.g.::

        revealjs_options = {'transition': 'slide', 'slideNumber': 'c/t'}

    Merged over the transform's defaults and injected into every page
    as JSON (a ``<meta name="revealjs-options">`` tag) that
    ``transform.js`` applies when it initializes reveal.js.

Per-page options
----------------

A page can override or extend :confval:`revealjs_options` with a
``revealjs-options`` field list field whose value is a JSON object
(MyST: front matter key ``revealjs-options``, value a *JSON string*).
The field is configuration and is removed from the rendered output::

    My page
    =======

    :revealjs-options: {"transition": "fade", "center": true}

Precedence: the transform's defaults, then ``window.revealjsOptions``
(a manual JavaScript hook), then :confval:`revealjs_options`, then the
page's ``revealjs-options`` field.  ``embedded`` is always forced back
to ``false`` - the deck is built in place and fullscreen (``embedded:
true`` would confine it to the page's content column).
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util import logging as sphinx_logging
from sphinx.util.typing import ExtensionMetadata

logger = sphinx_logging.getLogger(__name__)

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
        'data-font-scale': str(app.config.revealjs_font_scale),
    })


def _leading_field_lists(doctree: nodes.document):
    """Yield the leading field_list nodes of the document.

    docutils >= 0.22 wraps the document (title, docinfo-style field
    lists, ...) in a title ``<section>``, older versions keep them at
    the document level; both levels are checked, stopping at the first
    real content node.
    """
    parents = [doctree]
    idx = doctree.first_child_not_matching_class(nodes.PreBibliographic)
    if idx is not None and isinstance(doctree[idx], nodes.section):
        parents.append(doctree[idx])
    for parent in parents:
        for child in parent.children:
            if isinstance(child, nodes.field_list):
                yield child
                continue
            if isinstance(child, (nodes.title, nodes.docinfo,
                                  nodes.decoration, nodes.meta)):
                continue
            break


def _parse_options(raw: str, pagename: str) -> dict | None:
    """Parse a page's ``revealjs-options`` JSON string.  Smart quotes
    (which docutils substitutions can produce) are normalized."""
    raw = raw.translate(str.maketrans({'“': '"', '”': '"', '„': '"',
                                       '‘': "'", '’': "'"}))
    try:
        page_options = json.loads(raw)
    except ValueError:
        logger.warning('revealjs: the revealjs-options field of %s is '
                       'not valid JSON', pagename)
        return None
    if not isinstance(page_options, dict):
        logger.warning('revealjs: the revealjs-options field of %s is '
                       'not a JSON object', pagename)
        return None
    return page_options


def _add_doctree_options(
    app: Sphinx, doctree: nodes.document, docname: str,
) -> None:
    """Connect to 'doctree-resolved': extract the page's
    ``revealjs-options`` field (a reST field list; docutils >= 0.22 no
    longer turns leading field lists into docinfo that Sphinx
    collects), stash it on the doctree for 'html-page-context', and
    remove the field from the rendered output (it is configuration,
    not content)."""
    for field_list in _leading_field_lists(doctree):
        for field in list(field_list.children):
            name = field[0].astext().strip().lower() if len(field) == 2 else ''
            if name != 'revealjs-options':
                continue
            page_options = _parse_options(field[1].astext(), docname)
            if page_options:
                doctree.revealjs_page_options = page_options
            field_list.remove(field)
            if not len(field_list):
                field_list.parent.remove(field_list)
            break


def _add_page_options(
    app: Sphinx, pagename: str, templatename: str, context: dict, doctree
) -> None:
    """Connect to 'html-page-context': inject the merged reveal.js
    options (conf.py ``revealjs_options`` overridden by the page's
    ``revealjs-options`` field) as a JSON ``<meta>`` tag that
    ``transform.js`` reads."""
    builder = getattr(app, 'builder', None)
    if getattr(builder, 'format', None) != 'html':
        return
    if getattr(builder, 'name', None) in _EXCLUDED_BUILDERS:
        return

    merged = dict(app.config.revealjs_options or {})
    metadata = (getattr(app.env, 'metadata', None) or {}).get(pagename) or {}
    raw = metadata.get('revealjs-options')
    if raw:
        page_options = _parse_options(raw, pagename)
        if page_options:
            merged.update(page_options)
    if doctree is not None:
        page_options = getattr(doctree, 'revealjs_page_options', None)
        if page_options:
            merged.update(page_options)

    metatags = context.get('metatags') or ''
    metatags += (
        '<meta name="revealjs-options" content="%s">'
        % html.escape(json.dumps(merged), True)
    )
    context['metatags'] = metatags


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value('revealjs_url_param', 'revealjs', 'html')
    app.add_config_value('revealjs_theme', 'none', 'html')
    app.add_config_value('revealjs_break_on_hr', True, 'html')
    app.add_config_value('revealjs_font_scale', 2, 'html')
    app.add_config_value('revealjs_options', {}, 'html')

    app.connect('builder-inited', _add_html_assets)
    app.connect('doctree-resolved', _add_doctree_options)
    app.connect('html-page-context', _add_page_options)

    return {
        'version': '0.2',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
