revealjs demo
=============

:revealjs-options: {"slideNumber": "c/t"}

Any page becomes a reveal.js presentation when you append
``?revealjs`` to the URL.  The options field above is explained in
`Per-page options`_ below.

A top-level section is a slide
------------------------------

This entire section becomes one horizontal slide.

.. image:: img1.png

A subsection is a subslide
~~~~~~~~~~~~~~~~~~~~~~~~~~

Nested sections become vertical (sub)slides.

Another subsection
~~~~~~~~~~~~~~~~~~

Another vertical subslide.

Breaking slides
---------------

A section can be split into several slides with an explicit
``revealjs-break`` directive (MyST: ``:::{revealjs-break}``), which
emits a hidden marker and starts a new slide -- in every ``<hr>``
configuration:

This paragraph is in the first slide of this section.

.. revealjs-break::

This paragraph is in a second slide: the directive above forced a
break.  On the normal page the marker is an invisible ``<hr>``.

Historically this was spelled with a ``----`` transition line
(``---`` in MyST).  By default a ``----`` now introduces *audience
notes* instead -- see `Audience notes`_ below -- and setting
``revealjs_hr_notes = False`` in conf.py restores the old
``----``-splits-slides behavior.  Note that three dashes (``---``) are
*not* a transition in reST -- they render as a plain paragraph.

Code blocks
~~~~~~~~~~~

Code blocks and other Sphinx content work inside slides::

    def hello():
        print("Hello from a slide!")

Lists
~~~~~

- Lists work normally
- More content

.. revealjs-break::

A second slide of the same subsection (forced by ``revealjs-break``).


Audience notes
--------------

By default (``revealjs_hr_notes = True``), a ``----`` transition ends
the slide's presented content: everything up to the next ``----``,
heading or explicit break becomes *audience notes* for the preceding
slide.  Readers see them as ordinary text on the normal page (the
``<hr>`` shows as a horizontal rule), the slide itself shows nothing
after its presented content, and the speaker view (``S``) lists them
below the slide's real ``revealjs-notes`` talk track, separated from
it by a horizontal rule.

.. revealjs-notes::

   Talk track for the audience-notes demo: this real note comes first
   in the speaker view; the audience notes for this slide appear below
   it.

----

This paragraph and the next are audience notes for the slide above:
they never appear on a slide, they show as ordinary text on the
normal page, and in the speaker view they follow the talk track.

Detailed elaboration belongs here -- background, caveats, numbers too
tedious for a slide.

----

This paragraph starts a new slide: the ``----`` above flushed the
audience-notes block and re-opened slide mode.


Page-only details
-----------------

Content that should appear on the normal page but never in the slides
is marked in one of two ways.  An ``epigraph`` is skipped:

.. epigraph::

   This epigraph is visible on the normal page, but completely missing
   from the presentation -- a lightweight convention for page-only
   details.

   -- the revealjs extension

Anything with the class ``revealjs-noslide`` is skipped too, for
example a container:

.. container:: revealjs-noslide

   This container is also shown on the page only.

This paragraph is in the same slide as the two page-only blocks above
would have been -- except that those two are absent from slides.
(Unlike `Audience notes`_, epigraphs and ``revealjs-noslide`` content
never reach the speaker view either.)

Speaker notes
-------------

The ``revealjs-notes`` directive attaches hidden speaker notes to the
slide it appears in.  They are invisible on the slide and in the
normal page; press ``S`` during a presentation to open the speaker
view, which shows the current and next slide plus the notes.

.. revealjs-notes::

   Talk track for this slide: introduce speaker notes, then demo the
   speaker view (``S``).  Notes never reach the audience.

Notes can contain any body text: **bold**, lists, even code.

.. revealjs-break::

This second slide of the section exists to show that the notes above
stayed with *its* slide.

Theme from the URL
------------------

A valued ``revealjs`` parameter overrides the theme configured with
``revealjs_theme``: ``?revealjs=simple`` presents with the vendored
``simple`` theme, ``?revealjs=none`` always presents unthemed.  Only
themes vendored under ``_static/revealjs/upstream/theme/`` can be
selected; an unknown name loads no theme, and the deck simply presents
unthemed.  This demo's ``conf.py`` leaves ``revealjs_theme`` at its
default ``'none'``, so plain ``?revealjs`` is already unthemed -- try
``?revealjs=simple`` for a themed deck.  Unthemed decks scale their
text from the page's own font size (``revealjs_font_scale``); themed
decks keep the theme's fixed sizes.

Per-page options
----------------

The ``revealjs-options`` field at the top of this page enables slide
numbers for this deck only (visible in presentation mode).  Its value
is a JSON object; it overrides the site-wide ``revealjs_options``
setting and is removed from the rendered page.  In reST it is a
docinfo-style field at the top of the page; in MyST a front-matter key
whose value is a *JSON string*::

    :revealjs-options: {"slideNumber": "c/t"}

With several ``revealjs-options`` fields, the last one wins.

Printing and resuming
---------------------

Load the deck with ``&print-pdf`` in the URL (for example
``revealjs-demo.html?revealjs&print-pdf``) and print to PDF from the
browser (landscape, margins: none, background graphics: on) to get a
handout with every slide on its own page.  Plain browser printing
(without ``print-pdf``) also works and produces a simplified text
layout of the whole deck.

The deck also remembers where you stopped reading: re-entering the
presentation reopens on the last viewed slide (per page, stored in the
browser's local storage).  A ``#/2/0`` style hash in the URL takes
precedence.
