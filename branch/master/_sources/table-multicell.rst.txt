Multi-cell list-tables
======================

``sphinx_misc_rkdarst.list_table_multicell`` adds a ``list-table-multicell``
directive, which is ``list-table`` with a marker read from the start of a cell:
``multirow(n)`` to cover ``n`` rows, ``multicolumn(n)`` to cover ``n`` columns,
and ``multirow(0)`` or ``multicolumn(0)`` in the cells that a span covers. The
whole of it is in the docstring of the module.

Covering rows
-------------

.. list-table-multicell::
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
     - 7
     - 8
   * - multirow(3) East
     - 22
     - 24
   * -
     - 19
     - 21
   * -
     - 25
     - 23
   * - West
     - 17
     - 18

Covering columns
----------------

.. list-table-multicell::
   :header-rows: 1

   * - Weekday
     - Morning
     - Afternoon
   * - Monday
     - meeting
     - nothing
   * - Tuesday
     - multicolumn(2) closed all day
     - multicolumn(0)
   * - Wednesday
     - meeting
     - meeting

Both at once
------------

A table in a cell stays a table of its own, markers and all.

.. list-table-multicell::
   :header-rows: 1

   * - Group
     - Part
     - Note
   * - multicolumn(2) multirow(2) Everything
     - multicolumn(0)
     - two rows and two columns
   * - multirow(0)
     - multirow(0)
     - another note
   * - other
     - a nested table:

       .. list-table::

          * - n1
            - n2
     - not spanned

Wrong on purpose
----------------

Each of these says so once while building, and makes the table come out as
close to what was meant as it can.

.. list-table-multicell::
   :header-rows: 1

   * - H1
     - H2
   * - multirow(6) more rows than there are
     - b
   * - multirow(0)
     - d

.. list-table-multicell::
   :header-rows: 1

   * - multirow(2) cannot reach past the head
     - h2
   * - a
     - b

.. list-table-multicell::

   * - multirow(0) with nothing over it
     - b
   * - text with multicolumn(2) in the middle of it
     - d
