.. _ref_greet:

greet
=====

Greet a specific person

**Usage:**

.. code-block:: bash

   democli greet [--formal] [--enthusiasm ENTHUSIASM] [--suffix SUFFIX]
                     name

Overview
--------

The greet command allows you to personalize your greeting by specifying
a name. You can also customize the greeting style and add an optional
message suffix.

This command demonstrates how to use positional and optional arguments
with craft_cli.

Options
-------

.. option:: --formal

      Use formal greeting style

   Default: ``False``

.. option:: --enthusiasm

      Enthusiasm level (1-5)

   Default: ``1``

.. option:: --suffix

      Optional message suffix

Examples
--------

**Greet Alice**

.. code-block:: bash

   democli greet Alice

**Greet Bob formally**

.. code-block:: bash

   democli greet Bob --formal

**Greet Charlie with enthusiasm**

.. code-block:: bash

   democli greet Charlie --enthusiasm 5

**Greet multiple people**

.. code-block:: bash

   democli greet Alice --suffix ', have a great day!'

See also
--------

- :ref:`hello <ref_hello>`
- :ref:`farewell <ref_farewell>`
