from option_merge.helper import prefixed_path_list, prefixed_path_string, without_prefix, dot_joiner, make_dict
from option_merge.storage import Storage

from delfick_error import DelfickError
from collections import Mapping
import six

class BadPrefix(DelfickError): pass
"""Used to say a prefix value is not a dictionary"""

class KeyValuePairsConverter(object):
    """Converts a list of key,value pairs to a dictionary"""
    def __init__(self, pairs, source=None):
        self.pairs = pairs
        self.source = source

    def convert(self):
        """Return us a MergedOptions from our pairs"""
        return MergedOptions().using(*[make_dict(key[0], key[1:], value) for key, value in self.pairs], source=self.source)

class AttributesConverter(object):
    """Converts an object with particular attributes to a dictionary"""
    def __init__(self, obj, attributes=None, include_underlined=False, lift=None, ignoreable_values=None, source=None):
        self.obj = obj
        self.lift = lift
        self.source = source
        self.attributes = attributes
        self.ignoreable_values = ignoreable_values
        self.include_underlined = include_underlined

        if isinstance(self.lift, six.string_types):
            self.lift = [self.lift]

    def convert(self):
        """Return us a MergedOptions from our attributes"""
        options = MergedOptions()
        attributes = self.attributes
        if not attributes:
            attributes = dir(self.obj)
            if not self.include_underlined:
                attributes = [attr for attr in attributes if not attr.startswith("_")]

        for attr in attributes:
            if hasattr(self.obj, attr):
                val = getattr(self.obj, attr)
                if not self.ignoreable_values or val not in self.ignoreable_values:
                    options[attr] = val

        if self.lift:
            lifted = MergedOptions()
            lifted.storage.add(self.lift, options)
            return lifted
        else:
            return options

class ConverterProperty(object):
    """Creates a Property for accessing a converter"""
    def __init__(self, converter):
        self.converter = converter

    def __get__(self, obj=None, owner=None):
        return lambda *args, **kwargs: self.converter(*args, **kwargs).convert()

class MergedOptions(dict, Mapping):
    """
    Wrapper around multiple dictionaries to behave as one.

    Usage::

        options = MergedOptions.using(options1, options2, source="SomePlace")

    Is equivalent to::

        options = MergedOptions()
        options.update(options1, source="SomePlace")
        options.update(options2, source=SomePlace")

    The later an option is added, the more influence it has.
    i.e. when a key is accessed, later options are looked at first.

    When you delete a key, it removes it from the first dictionary it can find.
    This means a key can change value when deleted rather than disappearing altogether

    It will also merge deeply.

    So::

        options1 = {'a':{'b':1, 'c':3}, 'b':5}
        options2 = {'a':{'b':4'}, 'd':7}
        merged = MergedOptions.using(options1, options2)
        merged['a'] == MergedOptions(prefix='a', <same_options>, <same_overrides>)
        merged['a']['b'] == 4
        merged['a']['c'] == 3
        merged['d'] == 7
    """

    Attributes = ConverterProperty(AttributesConverter)
    KeyValuePairs = ConverterProperty(KeyValuePairsConverter)

    def __init__(self, prefix=None, storage=None):
        self.prefix_list = prefix
        if not self.prefix_list:
            self.prefix_list = []
        if isinstance(self.prefix_list, six.string_types):
            self.prefix_list = [self.prefix_list]
        self.prefix_string = dot_joiner(self.prefix_list)

        self.storage = storage
        if self.storage is None:
            self.storage = Storage()

    @classmethod
    def using(cls, *options, **kwargs):
        """Convenience for calling update multiple times"""
        source = kwargs.get("source")
        merged = cls()
        for opts in options:
            merged.update(opts, source=source)
        return merged

    def update(self, options, source=None):
        """Add new options"""
        if options is None: return
        self.storage.add(self.prefix_list, options, source=source)

    def __getitem__(self, path):
        """
        Access some path

        Return the first value it comes across
        Raise KeyError if nothing has the specified key
        """
        for val in self.values_for(path):
            if isinstance(val, dict):
                return self.prefixed(path)
            else:
                return val
        raise KeyError(path)

    def __contains__(self, path):
        """Implement membership in terms of __getitem__"""
        try:
            self[path]
            return True
        except KeyError:
            return False

    def get(self, path, default=None):
        """Get some path or return default value"""
        try:
            return self[path]
        except KeyError:
            return default

    def source_for(self, path):
        """Proxy self.storage.source_for"""
        if isinstance(path, list):
            path = dot_joiner(path)
        return self.storage.source_for(self.prefixed_path_string(path))

    def __setitem__(self, path, value):
        """Set a key in the storage"""
        self.storage.add(self.prefixed_path_list([path]), value)

    def __delitem__(self, path):
        """Delete a key from the storage"""
        self.storage.delete(self.prefixed_path_string(path))

    def __iter__(self):
        """Iterate over the keys"""
        return iter(self.keys())

    def __len__(self):
        """Get number of keys we have"""
        return len(list(self.keys()))

    def __eq__(self, other):
        """Equal to another merged options if has same storage and prefix"""
        return isinstance(other, self.__class__) and other.storage is self.storage and other.prefix_list == self.prefix_list

    def values_for(self, path):
        """Get all known values for some path"""
        if isinstance(path, list):
            path = dot_joiner(path)
        path = self.prefixed_path_string(path)
        for info in self.storage.get_info(path):
            yield info.value_after(path)

    def prefixed(self, path):
        """Return a MergedOptions prefixed to this path"""
        if isinstance(path, six.string_types):
            path = [path]
        return self.__class__(self.prefixed_path_list(path), storage=self.storage)

    def prefixed_path_list(self, path):
        """Proxy the prefixed_path_list helper with prefix from this instance"""
        return prefixed_path_list(path, self.prefix_list)

    def prefixed_path_string(self, path):
        """Proxy the prefixed_path_string helper with prefix from this instance"""
        return prefixed_path_string(path, self.prefix_string)

    def keys(self):
        """Return a de-duplicated list of the keys we know about"""
        for key in self.storage.keys_after(self.prefix_string):
            prefixless = without_prefix(key, self.prefix_list)
            if prefixless:
                yield prefixless

    def items(self):
        """Iterate over [(key, value), ...] pairs"""
        for key in self.keys():
            yield key, self[key]

    def values(self):
        """Return the values"""
        for key in self.keys():
            yield self[key]

    def __repr__(self):
        return "MergedOptions({0})".format(self.prefix_string)

