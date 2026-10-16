"""List-table cells that cover several rows or columns.

The below docstring is machine generated.

Add the extension to ``extensions`` in conf.py::

    extensions = ['sphinx_misc_rkdarst.list_table_multicell']

``list-table`` makes one table cell out of each bullet of the second level, and
there is no way to say that a cell should also cover what is below it or to the
right of it. This extension adds a directive with the very same form under
another name, ``list-table-multicell``, which reads a marker at the start of a
cell for that::

    .. list-table-multicell:: Where the money went
       :header-rows: 1

       * - Region
         - Q1
         - Q2
       * - multirow(3) North
         - 12
         - 14
       * - multirow(0)
         - 9
         - 11
       * - multirow(0)
         - 15
         - 13
       * - South
         - multicolumn(2) the same figure for both quarters
         - multicolumn(0)

which is a table of three columns in which the "North" cell covers the three
rows of North's figures, and the middle cell of the last row covers both of the
quarter columns.

Nothing here needs setting up. The directive is only what ``list-table`` is with
the markers read, so a table without a marker in it comes out of the two
directives the same way, and ``list-table`` itself is left alone. The two conf.py
values of the section of that name are only for a build that has a reason of its
own to write the markers with other words than the ones of this file.

Markers
=======

A marker has to be the first thing in a cell, written in lower case, and one
cell can carry both of them, as in ``multicolumn(2) multirow(2) text`` or with
each one on a line of its own. The number in brackets is how many rows or
columns the cell covers *including* its own, so it has to be at least 2 to do
anything. A marker anywhere else in a cell is left as the text it is, and said
so, since that is likelier a slip than a thing meant. So is a marker that markup
puts in front of, as in bold or in a literal, which is not the first thing in the
cell either and is said so the same way.

========================  ====================================================
``multirow(n)``           Cover ``n`` rows: this one and ``n - 1`` below it.
``multicolumn(n)``        Cover ``n`` columns: this one and the ``n - 1`` to
                          their right.
``multirow(0)``           The cell holds nothing of its own, only the space a
``multicolumn(0)``        cell spanning onto it leaves, and it goes away.
========================  ====================================================

A span takes the space of other cells, and every cell it takes has to be in the
source, because ``list-table`` wants the same number of bullets in every row. A
covered cell is therefore written as a cell of its own holding nothing but
``multirow(0)``, or ``multicolumn(0)`` when it is the cell to its left that
covers it, and is taken out before the table is written out. An empty cell does
as well, but the marker says what the empty bullet was for, to whoever reads
the source and to this extension.


conf.py values
==============

Two values say what words the markers are written with, for a build that has a
reason of its own to want others than the words of this file::

    list_table_multicell_row_marker = "multirow"        # the default
    list_table_multicell_column_marker = "multicolumn"  # the default

The two have to hold words, and two different ones, since a word named twice
cannot tell a span of columns from one of rows. What does not is answered with
the two words of this file, and with something said about it. Both are read as
each table is read, and a change to either is a change to what every table of the
documentation means, which is why a build that sees one reads everything again.

The words are matched as they are written, upper case included. The check that
says so when a marker sits where it cannot be read follows them too, so a table
still written with the words of this file says nothing at all once they are
changed. A document written with other words than the ones above therefore asks
that whoever reads its source knows what they are, which is the only reason to
want them.


What it turns into
==================

The markers leave nothing behind. What is set instead are the ``morerows`` and
``morecols`` attributes of the docutils ``entry`` node, holding the number of
rows and columns *besides* the cell's own, which is what a table in
reStructuredText always carries and what the writers know what to do with:

* HTML: ``rowspan="n"`` and ``colspan="n"`` on the ``td`` or ``th``;
* LaTeX and PDF: ``\\sphinxmultirow`` and ``\\sphinxstartmulticolumn``, and both
  of them at once where a cell spans each way;
* the text writer: the same spans in the grid of cells it draws, the space of a
  covered cell left empty under the cell that covers it and a cell of two columns
  drawn over the two of them;
* the man page writer: nothing, as it says "table row spanning not supported"
  the way it does for the spans of any other table, with the rows below a cell
  that spans coming out one column to the left.

Problems are warnings, not errors, and carry the file and line of the
directive::

    index.rst:12: WARNING: list_table_multicell: row 4, column 1: multirow(6)
    would leave the body of the table, which has only 2 rows below it, and is
    shortened to 3

so ``suppress_warnings = ['list_table_multicell']`` silences them. What was
asked for is then adjusted rather than obeyed, so that the table stays
rectangular and the rest of it comes out as written.

Limits
======

* A span stays inside the head or the body part of the table where it starts,
  because a cell of a head, written as ``th``, cannot reach into the ``tbody``
  of the same table. A span that would leave it is cut short with a warning,
  and the ``multirow(0)`` cells below it become ordinary cells of their own.
* The text writer draws the spans in the grid of cells it draws. The man page
  writer cannot show one and says "table row spanning not supported", as it does
  for the spans of any other table, and the rows below a cell that spans come out
  one column to the left, since a covered cell is not in the doctree for it to
  leave empty. Nothing here can do anything about either. A table inside a cell
  stops both of them with an error of their own instead of being written, which
  is a limit of Sphinx and not of the markers.
* A table inside a cell is a table of its own and is not looked at, so a marker
  in it does nothing, and nothing of the outer table depends on it.
* With ``:stub-columns:`` set, the HTML writer counts the columns of a row that
  a cell spans into from the cells it finds there, so the stub styling can
  land on the wrong cell of such a row. How it is laid out is not affected.
* The cells of a row are still made by ``list-table``, which wants the same
  number of bullets in every row and says so before this extension ever sees
  the table.

References
==========

* ``docutils/parsers/rst/directives/tables.py``, the ``ListTable`` class: what
  is subclassed here. It makes a ``tgroup`` of ``row`` of ``entry`` out of a
  two-level bullet list, and sets nothing on an entry but its content.
* ``docutils/writers/_html_base.py``, ``visit_entry``: where ``morerows`` and
  ``morecols`` become ``rowspan`` and ``colspan``. The same attributes are what
  a grid table and a ``csv-table`` carry for the same thing, so nothing here is
  a form of its own, and a table this extension makes can be read back.
* ``sphinx/writers/latex.py``, ``visit_entry``: where they become
  ``\\sphinxmultirow`` and ``\\sphinxstartmulticolumn``, which is why a cell
  spanning rows and columns at once is no trouble for a PDF build.
* ``sphinx/writers/text.py``, ``visit_entry``: where they become the rowspan and
  colspan of the grid of cells it lays out, which is why the text output keeps
  the spans of a table too.
* The covered cells have to be taken out of the doctree rather than marked
  somehow, as no writer skips an ``entry`` on account of an attribute: it would
  be written as one more cell in the row.
"""

from __future__ import annotations

import re
from collections import namedtuple

from docutils import nodes
from docutils.parsers.rst.directives.tables import ListTable
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.typing import ExtensionMetadata

logger = logging.getLogger(__name__)

# The words markers are written with, unless a build asks for others. The two
# options are for a project that has a reason of its own to want other words,
# and are documented under "conf.py values" above and nowhere else.
DEFAULT_ROW_MARKER = "multirow"
DEFAULT_COLUMN_MARKER = "multicolumn"
ROW_MARKER_OPTION = "list_table_multicell_row_marker"
COLUMN_MARKER_OPTION = "list_table_multicell_column_marker"

# A marker word has to be a word, because it sits in front of the text of a
# cell, where anything looser could not be told apart from that text.
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]*")

# What one build reads, in both of the two ways a marker is looked for.
Markers = namedtuple("Markers", "row column leading stray")


def _marker_patterns(row, column):
    """The two expressions that a pair of marker words gives.

    The first reads a marker at the start of a cell, where it is the whole cell
    when nothing follows it on the line. The count is of rows or columns
    including the cell's own, so 0 says that the cell has none of its own and
    only fills the space another one spans onto.

    The second finds the same anywhere in a text, to say so when a marker sits
    where it cannot be read and would be left in the table as plain text. What a
    LaTeX macro writes is left alone, as that is a thing meant rather than a
    marker misplaced.
    """
    words = "|".join(re.escape(word) for word in (row, column))
    return (
        re.compile(rf"^({words})\((\d+)\)\s*"),
        re.compile(rf"(?<![\\\w])(?:{words})\(\d+\)"),
    )


def _markers(config):
    """The markers of one build, which are the words of the module when there is
    no configuration to ask, as when docutils is on its own, or when what it
    holds could not be told apart from the text of a cell.

    A word that is not a word could not be told from the text of the cell it is
    written in front of, and one word named twice could not tell a span of
    columns from one of rows. Either is answered with the two words of the
    module, and with something said about it.
    """
    words = [getattr(config, option, None) or default
             for option, default in ((ROW_MARKER_OPTION, DEFAULT_ROW_MARKER),
                                     (COLUMN_MARKER_OPTION, DEFAULT_COLUMN_MARKER))]

    if not all(isinstance(word, str) and _WORD.fullmatch(word) for word in words):
        logger.warning("list_table_multicell: %s and %s have to hold a word to "
                       "write a marker with, so %s and %s are used instead",
                       ROW_MARKER_OPTION, COLUMN_MARKER_OPTION, DEFAULT_ROW_MARKER,
                       DEFAULT_COLUMN_MARKER, type="list_table_multicell", once=True)
        words = [DEFAULT_ROW_MARKER, DEFAULT_COLUMN_MARKER]
    elif words[0] == words[1]:
        logger.warning("list_table_multicell: the two marker options hold the "
                       "one word %r, in which a span of columns cannot be told "
                       "from one of rows, so %s and %s are used instead", words[0],
                       DEFAULT_ROW_MARKER, DEFAULT_COLUMN_MARKER,
                       type="list_table_multicell", once=True)
        words = [DEFAULT_ROW_MARKER, DEFAULT_COLUMN_MARKER]

    leading, stray = _marker_patterns(words[0], words[1])
    return Markers(words[0], words[1], leading, stray)


def _environment(state):
    """The build environment of a directive, or None when it is not Sphinx's."""
    settings = getattr(state.document, "settings", None)
    return getattr(settings, "env", None)


def _warner(docname, lineno):
    """Return a function reporting one problem of the table being built.

    The location points at the document and line the directive sits in, so the
    warning is shown with a file and line the way Sphinx shows its own.
    """

    def warn(message: str) -> None:
        logger.warning(
            "list_table_multicell: %s",
            message,
            location=(docname, lineno),
            type="list_table_multicell",
        )

    return warn


def _rows_of_table(table):
    """The rows of the table itself, each with the head or body part it is in.

    The part is what a span cannot leave, and is returned with the row so that
    this is known where the rows are walked. A table in a cell of this one is
    not come near, since only the children of this table's own ``tgroup`` are
    looked at.
    """
    rows = []
    for tgroup in table:
        if not isinstance(tgroup, nodes.tgroup):
            continue
        for part in tgroup:
            if isinstance(part, (nodes.thead, nodes.tbody)):
                rows.extend((part, row) for row in part if isinstance(row, nodes.row))
    return rows


def _columns_of_table(table):
    """How many columns the table has, or None when it does not say."""
    for tgroup in table:
        if isinstance(tgroup, nodes.tgroup):
            return tgroup.get("cols")
    return None


def _own_texts(entry):
    """The texts of a cell itself, in order, leaving out nested structures.

    A marker is only read in the cell's own paragraphs, so that a table or a
    list in a cell keeps whatever its own texts hold. Everything here counts for
    saying so when a marker sits where it cannot be read, wherever in the cell it
    sits.
    """
    texts = []
    for child in entry:
        if isinstance(child, nodes.Text):
            texts.append(child)
        elif isinstance(child, nodes.paragraph):
            texts.extend(child.findall(nodes.Text))
    return texts


def _leading_text(entry):
    """The text a cell starts with, or None when it starts with something else.

    This is where a marker is read, and nowhere else: markup or a structure in
    front of the text of a cell means that the marker is not the first thing in
    it, whatever order its texts come in. What comes back is the text and not the
    cell, so that a second marker in the same text, which is what a cell with its
    two markers on lines of their own holds, is read by the next turn of the
    reading.
    """
    block = entry[0] if len(entry) else None
    if isinstance(block, nodes.paragraph):
        block = block[0] if len(block) else None
    return block if isinstance(block, nodes.Text) else None


def _take_markers(entry, place, warn, markers):
    """Remove the markers at the start of a cell, and return what they ask for.

    Returns the number of rows and of columns the cell is to cover besides its
    own, and whether it was written as one that only fills the space another
    spans onto. A marker that asks for a single row or column is reported, as
    there is nothing for it to do.
    """
    extra_rows = extra_columns = 0
    filled = False
    while True:
        text = _leading_text(entry)
        if text is None:
            return extra_rows, extra_columns, filled
        match = markers.leading.match(str(text))
        if match is None:
            return extra_rows, extra_columns, filled

        marker, count = match.group(1), int(match.group(2))
        rest = str(text)[match.end() :]
        holder = text.parent  # the cell itself, or one of its own paragraphs
        if rest.strip():
            holder.replace(text, nodes.Text(rest))
        elif holder is entry:
            entry.remove(text)
        elif len(holder) == 1 and len(entry) == 1:
            entry.remove(holder)  # a cell that is only a marker holds nothing
        else:
            holder.remove(text)

        if count == 0:
            filled = True  # the cell holds nothing of its own, and goes away
        elif count == 1:
            what = "row" if marker == markers.row else "column"
            warn(f"{place}: {marker}(1) asks for one {what}, which is what the "
                 "cell already is, so it does nothing")
        elif marker == markers.row:
            extra_rows = count - 1
        else:
            extra_columns = count - 1


def _warn_on_stray_markers(entry, place, warn, markers):
    """Say so when a marker sits somewhere in a cell other than its start."""
    for text in _own_texts(entry):
        stray = markers.stray.search(str(text))
        if stray:
            warn(f"{place}: {stray.group(0)} is only read at the start of a cell, "
                 "and is left as text here")
            return



def _apply_spans(table, warn, markers):
    """Read the markers of one table: set the spans and drop the covered cells.

    The rows are walked from the top and the cells of each row from the left,
    keeping count of the column each cell starts at, because that is what a
    span is about and it is not the same as the position of the cell in the
    row once cells have been eaten. ``covered`` holds the cells that a span
    from an earlier row reaches, and those are the ones taken out.
    """
    rows = _rows_of_table(table)
    if not rows:
        return
    columns = _columns_of_table(table)
    covered = {}  # (row, column) -> the row whose cell covers it
    remove = []

    for row_index, (part, row) in enumerate(rows):
        entries = [child for child in row if isinstance(child, nodes.entry)]
        column = position = 0
        while position < len(entries):
            entry = entries[position]
            position += 1
            place = f"row {row_index + 1}, column {column + 1}"

            if (row_index, column) in covered:
                # A cell from an earlier row reaches down over this one, so it
                # has to go. It holds a filler marker or nothing at all, or it
                # holds something it should not.
                _take_markers(entry, place, warn, markers)
                content = entry.astext().strip()
                if content:
                    warn(f"{place}: the cell that starts in row "
                         f"{covered[(row_index, column)] + 1} spans down over it, so "
                         f"what it holds, {content!r}, is dropped")
                remove.append(entry)
                column += 1
                continue

            extra_rows, extra_columns, filled = _take_markers(
                entry, place, warn, markers)
            _warn_on_stray_markers(entry, place, warn, markers)
            width = extra_columns + 1
            if filled:
                warn(f"{place}: {markers.row}(0) or {markers.column}(0) marks a cell "
                     "that another one spans onto, but nothing spans onto it here")

            if extra_columns and columns is not None and column + width > columns:
                # The span asks for columns the table does not have, so it stops
                # at the last one there is.
                room = columns - column
                what = "is dropped" if room == 1 else f"is shortened to {room}"
                warn(f"{place}: {markers.column}({width}) reaches past the "
                     f"{columns} columns of the table, and {what}")
                extra_columns = max(room - 1, 0)
                width = extra_columns + 1

            if extra_columns:
                overlapped = [
                    column + offset
                    for offset in range(1, width)
                    if (row_index, column + offset) in covered
                ]
                if overlapped:
                    warn(f"{place}: the cell spanning {width} columns covers the same "
                         f"cell as the one spanning down from row "
                         f"{covered[(row_index, overlapped[0])] + 1}")
                    extra_columns = 0
                    width = 1
                else:
                    merged = 0
                    for offset in range(1, width):
                        if position >= len(entries):
                            # The row runs out before the span does, so it
                            # covers only the cells there were, and says so.
                            what = ("is dropped" if not merged
                                    else f"is shortened to {merged + 1}")
                            warn(f"{place}: {markers.column}({width}) has no cell left "
                                 f"to its right to span onto, and {what}")
                            break
                        neighbour = entries[position]
                        position += 1
                        elsewhere = f"row {row_index + 1}, column {column + offset + 1}"
                        _take_markers(neighbour, elsewhere, warn, markers)
                        content = neighbour.astext().strip()
                        if content:
                            warn(f"{place}: the cell spanning over column "
                                 f"{column + offset + 1} is not empty, so what it "
                                 f"holds, {content!r}, is dropped")
                        remove.append(neighbour)
                        merged += 1
                    if merged:
                        entry["morecols"] = merged
                    width = merged + 1

            if extra_rows:
                # The rows this span may reach are those of the same part.
                reach = sum(1 for other, _ in rows[row_index + 1:] if other is part)
                if extra_rows > reach:
                    name = "head" if isinstance(part, nodes.thead) else "body"
                    if reach:
                        warn(f"{place}: {markers.row}({extra_rows + 1}) would leave the "
                             f"{name} of the table, which has only {reach} "
                             f"row{'' if reach == 1 else 's'} below it, and is "
                             f"shortened to {reach + 1}")
                    else:
                        warn(f"{place}: {markers.row}({extra_rows + 1}) would leave the "
                             f"{name} of the table, and is dropped")
                    extra_rows = reach
                if extra_rows:
                    entry["morerows"] = extra_rows
                    for below in range(row_index + 1, row_index + 1 + extra_rows):
                        for offset in range(width):
                            if (below, column + offset) in covered:
                                warn(f"row {below + 1}, column {column + offset + 1} is "
                                     "covered by two cells at once")
                            covered[(below, column + offset)] = row_index
            column += width

        if columns is not None and column != columns:
            warn(f"row {row_index + 1} fills {column} of the {columns} columns of "
                 "the table")

    for entry in remove:
        if entry.parent is not None:
            entry.parent.remove(entry)


class ListTableMultiCell(ListTable):
    """``list-table``, with the markers of the module docstring read from it.

    All of the stock directive does what it always does, options and the
    building of the table included. What is added is reading the markers once
    the table is built, from the nodes rather than the source, so that the
    table stays one table with all of the options working, and only the cells
    that ask for a span are touched.
    """

    def run(self):
        result = super().run()
        # A list-table that the stock directive could not make is an error node
        # rather than a table, and there are no markers to read in that.
        tables = [node for node in result if isinstance(node, nodes.table)]
        if not tables:
            return result

        env = _environment(self.state)
        warn = _warner(getattr(env, "docname", None), self.lineno)
        markers = _markers(getattr(env, "config", None))

        for table in tables:
            _apply_spans(table, warn, markers)
        return result


def setup(app: Sphinx) -> ExtensionMetadata:
    # Under a name of its own, and not over "list-table", so that a table
    # without markers stays the stock directive and a project cannot be
    # surprised by a marker it never wrote being read in it.
    app.add_directive("list-table-multicell", ListTableMultiCell)

    # The two words the markers are written with, for a project that has a
    # reason to want others. They are read as each table is read, and a change
    # to one of them is a change to what every table of the documentation means,
    # which is what "env" tells Sphinx. See "conf.py values" in the docstring:
    # a document written with other words than the ones of the docstring is a
    # thing to know about before one starts.
    app.add_config_value(ROW_MARKER_OPTION, DEFAULT_ROW_MARKER, "env", [str])
    app.add_config_value(COLUMN_MARKER_OPTION, DEFAULT_COLUMN_MARKER, "env", [str])

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
