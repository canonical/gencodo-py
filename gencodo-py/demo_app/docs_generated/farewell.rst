.. _ref_farewell:

farewell
========

Say goodbye to someone

**Usage:**

.. code-block:: bash

   democli farewell [--name NAME] [--style {casual,formal,sad}]
                        [--wish WISH]

Overview
--------

The farewell command provides a way to say goodbye in various styles.

Choose from casual, formal, or sad farewell styles. You can optionally
include a wish for the future or mention when you'll meet again.

Options
-------

.. option:: --name

      Name of the person (optional)

.. option:: --style

      Farewell style

   Default: ``casual``

.. option:: --wish

      Add a wish for the future

Examples
--------

**Simple goodbye**

.. code-block:: bash

   democli farewell

**Formal farewell to Bob**

.. code-block:: bash

   democli farewell --name Bob --style formal

**Sad goodbye**

.. code-block:: bash

   democli farewell --style sad

**Goodbye with future wish**

.. code-block:: bash

   democli farewell --wish 'see you soon'

See also
--------

- :ref:`greet <ref_greet>`
