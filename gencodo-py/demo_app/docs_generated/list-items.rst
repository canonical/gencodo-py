.. _ref_list_items:

list-items
==========

Display a list of items

**Usage:**

.. code-block:: bash

   democli list-items [--category CATEGORY] [--search SEARCH]
                          [--limit LIMIT] [--format {simple,detailed,json}]

Overview
--------

The list-items command shows a configurable list of items with various
filtering and display options.

You can filter by category, search by keyword, limit the number of results,
and choose between different output formats.

Options
-------

.. option:: --category

      Filter by category

.. option:: --search

      Search keyword in item names

.. option:: --limit

      Maximum number of items to show

   Default: ``10``

.. option:: --format

      Output format

   Default: ``simple``

Examples
--------

**List all items**

.. code-block:: bash

   democli list-items

**List items in fruit category**

.. code-block:: bash

   democli list-items --category fruit

**Search for items containing 'apple'**

.. code-block:: bash

   democli list-items --search apple

**Show only 5 items**

.. code-block:: bash

   democli list-items --limit 5

**Show detailed output**

.. code-block:: bash

   democli list-items --format detailed
