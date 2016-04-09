.. _merged_options:

MergedOptions
=============

MergedOptions is a cursor into a ``Storage`` object and is the object that
users should be interacting with.

Instantition
------------

It is recommended you use one of the class methods on MergedOptions to create
a MergedOptions object.

.. automethod:: option_merge.MergedOptions.using

.. automethod:: option_merge.MergedOptions.Attributes

    This is way of extracting attributes from an object and creating a
    MergedOptions from that:

    .. code-block:: python

        obj = type("obj", (object, ), {"one": "two", "two": "three", "four": "five"})
        result = MergedOptions.Attributes(obj, ("one", "four"), lift="global")
        assertEqual(as_dict(), {"global": {"one": "two", "four": "five"}})

.. automethod:: option_merge.MergedOptions.KeyValuePairs

    This allows us to create a MergedOptions from (key, value) pairs.

    .. code-block:: python

        result = MergedOptions.KeyValuePairs([(["one"], "two"), (["three", "four"], "five")])
        assertEqual(result.as_dict(), {"one": "two", "three": {"four": "five"}})

Instance Methods
----------------

.. autoclass:: option_merge.MergedOptions
    :members: update, __getitem__, __setitem__, __delitem__, __iter__, __len__, __contains__, __eq__
              , get, source_for, values_for, as_dict, wrapped, values, keys, items
              , add_converter, install_converters

    .. note:: the options into MergedOptions should be ignored and left to the
     internals of option_merge.

