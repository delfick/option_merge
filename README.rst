Option Merge
============

This provides the `option_merge.MergedOptions` class, which allows you to treat
multiple python dictionaries as one.

Documentation can be found at http://option-merge.readthedocs.org/

Usage
-----

Either the classmethod shortcut:

.. code-block:: python

    options = MergedOptions.using(options1, options2)

Or with the update method:

.. code-block:: python

    options = MergedOptions()
    options.update(options1)
    options.update(options2)

And a separate override with `__setitem__` syntax:

.. code-block:: python

    options['a'] = 1
    options['b.c'] = 2
    options['b'] = {"d": 3}
    options[['b', 'e']] = 4

    options.as_dict() == {"a": 1, "b.c": 2, "b": {"d": 3, "e": 4}}

When options are added, copies are made.

When you delete a key, it removes it from the first dictionary it can find.
This means a key can change value when deleted rather than disappearing altogether

So:

.. code-block:: python

    options1 = {'a':{'b':1, 'c':3}, 'b':5}
    options2 = {'a':{'b':4', 'c':9}, 'd':7}
    options = MergedOptions.using(options1, options2)

    # options['a'] == MergedOptions(prefix='a', <same_options>, <same_overrides>)
    # options['a']['b'] == 4
    # options['a']['c'] == 9
    # options['d'] == 7

    del options['a']['c']
    # options['a']['c'] == 3

You may also get all values for a key with `merged.values_for(path)`
where `path` is a dot-separated path.
So `options.values_for("a.b") == [4, 1]`

You can also get all deeply nested keys with `merged.all_keys()`.
So `merged.all_keys() == ["d", "a.b", "b", "a.c"]`

Installation
------------

Use pip!:

.. code-block:: bash

    pip install option_merge

Or if you're developing it:

.. code-block:: bash

    pip install -e .
    pip install -e ".[tests]"

Tests
-----

Run the helpful script:

.. code-block:: bash

    ./test.sh

