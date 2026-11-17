revealjs demo
=============

Any page becomes a reveal.js presentation when you append
``?revealjs`` to the URL.

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

Forced breaks with ``----``
---------------------------

Long sections can be split into several slides with a transition line
of at least four dashes (``----`` in reST, ``---`` in MyST), which
emits an ``<hr>`` in the HTML.  Note that three dashes (``---``) are
*not* a transition in reST -- they render as a plain paragraph.

This paragraph is in the first slide of this section.

----

This paragraph is in a second slide: the ``----`` above forced a break.
In the normal page view, it shows as a horizontal rule.

Code blocks
~~~~~~~~~~~

Code blocks and other Sphinx content work inside slides::

    def hello():
        print("Hello from a slide!")

Lists
~~~~~

- Lists work normally
- More content

----

A second slide of the same subsection (forced by ``----``).


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
