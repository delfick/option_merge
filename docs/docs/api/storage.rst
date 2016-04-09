.. _storage:

Storage
=======

This object stores the data the MergedOptions instances refers to. It stores
tuples of ``(prefix, data, source)`` where prefix is a :class:`Path` instance,
data is whatever is stored at that prefix, and source is a string as provided
when the data is stored.

You shouldn't need to access the storage directly, but rather access it via
the MergedOptions instance.

Having said that, it is a useful debugging technique to access ``storage.data``
on the MergedOptions instance.

