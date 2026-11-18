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
- By default (:confval:`revealjs_hr_notes` true), a transition line of
  at least four dashes (``----`` in reST, which emits an ``<hr>``;
  ``---`` in MyST) *ends the presented content of the current slide*:
  what follows (up to the next ``----``, heading or explicit break)
  becomes that slide's *audience notes* -- shown as ordinary text on
  the normal page, absent from the slides, and appended below the
  slide's real ``revealjs-notes`` speaker notes in the speaker view
  (``S``), separated from them by a horizontal rule.  A second
  ``----`` flushes the block and re-opens slide
  mode, so two consecutive ``----`` lines act as a plain slide break.
- With ``revealjs_hr_notes = False``, ``<hr>`` elements split slides
  when :confval:`revealjs_break_on_hr` is true (the behavior of
  earlier releases).
- The ``revealjs-break`` directive splits slides explicitly, in every
  mode.

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

``revealjs_hr_notes``
    Interpret ``<hr>`` elements (``----`` transitions) as the start of
    *audience notes* for the preceding slide instead of slide breaks:
    the text after the ``<hr>`` is kept out of the slides, stays on the
    normal page, and is appended below the slide's real speaker notes
    in the speaker view.  Default: ``True``.  Slide breaks then come
    from sections and the ``revealjs-break`` directive (two consecutive
    ``----`` lines also act as a break).

``revealjs_break_on_hr``
    With ``revealjs_hr_notes = False``: treat ``<hr>`` elements
    (``----`` transitions) as forced slide breaks.  Default: ``True``.
    (Ignored while ``revealjs_hr_notes`` is true.)

``revealjs_font_scale``
    Rescales the presentation's base font size when no reveal theme is
    loaded: the deck base becomes a percentage of the page's ambient
    body text size.  When a theme is loaded, the theme's own base font
    size (e.g. 40px) and type ratios are used as-is, so this has no
    effect.  Default: ``2.0``.

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

Directives
----------

``revealjs-notes``
    Hidden speaker notes for the slide they appear in (MyST:
    ``:::{revealjs-notes}``).  The body is parsed as ordinary text and
    rendered into that slide as a reveal.js notes element, visible only
    in the speaker view (press ``S`` during a presentation)::

        My page
        =======

        Some slide content.

        .. revealjs-notes::

           Talk track: mention X, then Y.  Roughly two minutes.

    Notes placed before the first section attach to the title slide;
    notes inside a section attach to that slide (including subslides).

``revealjs-break``
    Explicit slide break (MyST: ``:::{revealjs-break}``).  Emits a
    hidden marker that starts a new slide, in every ``<hr>`` mode::

        First slide.

        .. revealjs-break::

        Second slide.

Printing and resuming
---------------------

- Append ``&print-pdf`` to the presentation URL (e.g.
  ``page.html?revealjs&print-pdf``) and print to PDF from the browser
  (landscape, margins: none, background graphics: on) to get a handout
  with every slide on its own page.  Plain browser printing without
  ``print-pdf`` also works and produces a simplified text layout of
  the whole deck.
- Each deck remembers the slide it was last left on (per page, in the
  browser's local storage) and reopens there.  A ``#/2/0`` style hash
  link in the URL takes precedence.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import Directive
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
        'data-hr-notes': 'true' if app.config.revealjs_hr_notes else 'false',
        'data-break-on-hr': 'true' if app.config.revealjs_break_on_hr else 'false',
        'data-font-scale': str(app.config.revealjs_font_scale),
    })


def _leading_field_lists(doctree: nodes.document):
    """Yield the leading field_list nodes of the document.

    docutils >= 0.22 wraps the document (title, docinfo-style field
    lists, ...) in a title ``<section>``, older versions keep them at
    the document level; both levels are checked, stopping at the first
    real content node (comments and system messages are skipped, so a
    comment between the title and the field list does not end the
    scan).
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
                                  nodes.decoration, nodes.meta,
                                  nodes.comment, nodes.system_message)):
                continue
            break


def _parse_options(raw: str, pagename: str) -> dict | None:
    """Parse a page's ``revealjs-options`` JSON string.  Leading and
    trailing whitespace is stripped (reST field bodies and MyST front
    matter can add it) and smart quotes (which docutils substitutions
    can produce) are normalized."""
    raw = raw.strip().translate(str.maketrans({'“': '"', '”': '"', '„': '"',
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
    ``revealjs-options`` fields (a reST field list; docutils >= 0.22 no
    longer turns leading field lists into docinfo that Sphinx
    collects), stash them for 'html-page-context', and
    remove them from the rendered output (they are configuration, not
    content).  All leading field lists are scanned and every
    ``revealjs-options`` field is consumed; with duplicates the last
    one wins.  The parsed options are recorded in ``env.metadata``
    (Sphinx pickles the doctree between the read and write phases and
    dynamically set doctree attributes do not reliably survive that
    round-trip; metadata does)."""
    page_options: dict | None = None
    consumed = False
    for field_list in _leading_field_lists(doctree):
        for field in list(field_list.children):
            name = field[0].astext().strip().lower() if len(field) == 2 else ''
            if name != 'revealjs-options':
                continue
            consumed = True
            page_options = _parse_options(field[1].astext(), docname) or page_options
            field_list.remove(field)
            if not len(field_list):
                field_list.parent.remove(field_list)
    if page_options:
        doctree.revealjs_page_options = page_options
    if consumed:
        # Canonical JSON, or '' when only invalid fields were found
        # (falsy, so _add_page_options skips it).
        metadata = app.env.metadata.setdefault(docname, {})
        metadata['revealjs-options'] = (
            json.dumps(page_options) if page_options else '')


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


class RevealjsNotes(Directive):
    """Hidden speaker notes for the enclosing slide.

    The body is parsed as ordinary text and emitted as a hidden
    ``revealjs-notes`` container; transform.js converts these to
    reveal.js ``<aside class="notes">`` elements inside the slide,
    which the notes plugin's speaker view (``S``) displays.  Notes
    before the first section attach to the title slide; notes inside a
    section attach to that slide (including subslides).
    """

    has_content = True

    def run(self) -> list[nodes.Node]:
        node = nodes.container(rawsource='\n'.join(self.content))
        node['classes'].append('revealjs-notes')
        # Hidden on the normal page via an inline style (docutils drops
        # non-style pass-through attributes like `hidden`).
        node['style'] = 'display: none'
        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


class RevealjsBreak(Directive):
    """Explicit slide break (a forced split of the current section).

    Emits a hidden ``<hr class="revealjs-break">`` marker that
    transform.js turns into a slide boundary.  Useful in the default
    ``revealjs_hr_notes`` mode, where a plain ``----`` transition
    introduces audience notes instead of splitting slides (and in any
    mode as a more explicit spelling of ``----``).
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self) -> list[nodes.Node]:
        if self.content:
            raise self.error('revealjs-break takes no content')
        # docutils renders a transition as <hr>; the class travels
        # with the node (transform.js treats it as a break in every
        # mode).
        node = nodes.transition()
        node['classes'].append('revealjs-break')
        return [node]


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value('revealjs_url_param', 'revealjs', 'html')
    app.add_config_value('revealjs_theme', 'none', 'html')
    app.add_config_value('revealjs_hr_notes', True, 'html')
    app.add_config_value('revealjs_break_on_hr', True, 'html')
    app.add_config_value('revealjs_font_scale', 2.0, 'html')
    app.add_config_value('revealjs_options', {}, 'html')
    app.add_directive('revealjs-notes', RevealjsNotes)
    app.add_directive('revealjs-break', RevealjsBreak)

    app.connect('builder-inited', _add_html_assets)
    app.connect('doctree-resolved', _add_doctree_options)
    app.connect('html-page-context', _add_page_options)

    return {
        'version': '0.2',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
