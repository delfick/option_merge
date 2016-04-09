.. _design:

Design
======

MergedOptions is designed like a ``cursor`` looking at some ``storage`` where
each MergedOptions instance is just a different position in the same ``storage``.

Storage
-------

When you add data to a MergedOptions instance the code will store a tuple of
the ``prefix`` (path from the root of the options to this data), the ``data``
itself as a :class:`option_merge.versioning.VersionedDict`; and the ``source``
of the data, which is specified when you add data to the MergedOptions.

We are able to use this information to convert the storage into a dictionary; to
find nested values; and importantly, to memoize access to keys.

Everytime you access a dictionary in the ``MergedOptions`` you get back a new
instances of ``MergedOptions`` that has a different prefix into the same storage.

VersionedDict
-------------

To support memoizing values, all dictionaries are converted into a versioned dict.

This is just a normal dictionary but it supports a ``version`` that is incremented
each time the dictionary is modified in some way.

This way we can invalidate a cache of accessed values when the version of the
underlying data changes.

See :class:`option_merge.versioning.VersionedDict` for more information on this
data structure.

Data access
-----------

There are two ways to access data via a ``MergedOptions`` instance. The first is
via string access:

.. code-block:: python

    m = MergedOptions.using({"a": {"b": 3}})
    assert m["a.b"] == 3

And the second is via array access:

.. code-block:: python

    m = MergedOptions.using({"a": {"b": 3}})
    assert m[["a", "b"]] == 3

The string access will match on the longest match. This is a deliberate decision
so that keys are not split by dots:

.. code-block:: python

    m = MergedOptions.using({"a.b": 2, "a": {"b": 3}})
    assert m["a.b"] == 2
    assert m[["a", "b"]] == 3

In that example, ``a.b`` will match the "a.b" key rather than going into the
"a" key and accessing it's "b" member.

The array access, however, will not do such matching and treats each item in the
array as a full key.

Setting data
------------

Just like accessing data, there are two ways of setting data in a ``MergedOptions``:
with strings and with arrays.

In both cases, data is added to the storage, rather than trying to modify any
existing data.
