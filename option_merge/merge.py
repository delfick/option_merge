"""
This is the main class and the entry point for the programmer.

It provides a mechanism to treat multiple dictionaries as if they were one
dictionary.

Also provided is the ability to reference parts and still maintain the idea of it
being one dictionary.

With the ability to delete from the dictionary and the ability to convert values
on access.
"""

from option_merge.converter import Converters
from option_merge.joiner import dot_joiner
from option_merge.storage import Storage
from option_merge import helper as hp
from option_merge.path import Path

from delfick_error import DelfickError, ProgrammerError
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
        return MergedOptions().using(*[hp.make_dict(key[0], key[1:], value) for key, value in self.pairs], source=self.source)

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
            lifted.storage.add(Path.convert(self.lift), options)
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
        options.update(options2, source="SomePlace")

    The later an option is added, the more influence it has.
    i.e. when a key is accessed, later options are looked at first.

    When you delete a key, it removes it from the first dictionary it can find.
    This means a key can change value when deleted rather than disappearing altogether

    It will also merge deeply.

    So::

        options1 = {'a':{'b':1, 'c':3}, 'b':5}
        options2 = {'a':{'b':4'}, 'd':7}
        merged = MergedOptions.using(options1, options2)
        merged['a'] == MergedOptions(prefix='a', <same_options>)
        merged['a']['b'] == 4
        merged['a']['c'] == 3
        merged['d'] == 7
    """

    Attributes = ConverterProperty(AttributesConverter)
    KeyValuePairs = ConverterProperty(KeyValuePairsConverter)

    def __init__(self, prefix=None, storage=None, dont_prefix=None, converters=None, ignore_converters=False):
        self.prefix_list = prefix
        self.converters = converters
        self.dont_prefix = dont_prefix
        self.ignore_converters = ignore_converters
        if not self.dont_prefix:
            self.dont_prefix = []
        if not self.prefix_list:
            self.prefix_list = []
        if not self.converters:
            self.converters = Converters()
        if isinstance(self.prefix_list, six.string_types):
            self.prefix_list = [self.prefix_list]
        self.prefix_string = dot_joiner(self.prefix_list)

        self.storage = storage
        if self.storage is None:
            self.storage = Storage()

    @classmethod
    def using(cls, *options, **kwargs):
        """Convenience for calling update multiple times"""
        prefix = kwargs.get('prefix')
        storage = kwargs.get('storage')
        converters = kwargs.get('converters')
        dont_prefix = kwargs.get('dont_prefix')
        ignore_converters = kwargs.get("ignore_converters")
        merged = cls(
              prefix=prefix, storage=storage, dont_prefix=dont_prefix
            , converters=converters, ignore_converters=ignore_converters
            )

        for opts in options:
            merged.update(opts, **kwargs)
        return merged

    def update(self, options, source=None, **kwargs):
        """Add new options"""
        if options is None: return
        self.storage.add(Path(self.prefix_list), options, source=source)

    def __getitem__(self, path):
        """
        Access some path

        Return the first value it comes across
        Raise KeyError if nothing has the specified key
        """
        path = self.converted_path(path, ignore_converters=self.ignore_converters or getattr(path, "ignore_converters", False))
        for val, return_as_is in self.values_for(path, ignore_converters=path.ignore_converters):
            if return_as_is:
                return val

            if any(isinstance(val, unprefixed) for unprefixed in self.dont_prefix):
                return val
            elif isinstance(val, dict):
                return self.prefixed(path, already_prefixed=True)
            else:
                return val
        raise KeyError(path)

    def __contains__(self, path):
        """Ask storage if it has a path"""
        if isinstance(path, (list, tuple)):
            path = dot_joiner(path)

        try:
            self.storage.get(self.prefixed_path_string(path))
            return True
        except KeyError:
            return False

    def get(self, path, default=None):
        """Get some path or return default value"""
        try:
            return self[path]
        except KeyError:
            return default

    def source_for(self, path, chain=None):
        """Proxy self.storage.source_for"""
        path = Path.convert(path, self).ignoring_converters(True)
        return self.storage.source_for(path, chain)

    def __setitem__(self, path, value):
        """Set a key in the storage"""
        self.storage.add(self.converted_path([path]), value)

    def __delitem__(self, path):
        """Delete a key from the storage"""
        self.storage.delete(self.converted_path(path))

    def __iter__(self):
        """Iterate over the keys"""
        return iter(self.keys())

    def __len__(self):
        """Get number of keys we have"""
        return len(list(self.keys()))

    def __eq__(self, other):
        """Equal to another merged options if has same storage and prefix"""
        return isinstance(other, self.__class__) and other.storage is self.storage and other.prefix_list == self.prefix_list

    def values_for(self, path, converters=None, ignore_converters=False):
        """Get all known values for some path"""
        path = self.converted_path(path, converters=converters, ignore_converters=ignore_converters)
        if path.converted():
            yield path.converted_val(), True
            return

        if not path.ignore_converters and path.find_converter()[1]:
            yield path.do_conversion(self[path.ignoring_converters()])
            return

        for info in self.storage.get_info(path):
            try:
                yield info.value_after(path), False
            except hp.NotFound:
                pass

    def prefixed(self, path, ignore_converters=False, already_prefixed=False):
        """Return a MergedOptions prefixed to this path"""
        return self.__class__(
              self.converted_path(path, ignore_converters=ignore_converters)
            , storage=self.storage
            , dont_prefix=self.dont_prefix
            , converters=self.converters
            , ignore_converters=ignore_converters
            )

    def root(self):
        """Return a MergedOptions prefixed to this path"""
        return self.__class__(
              ""
            , storage=self.storage
            , dont_prefix=self.dont_prefix
            , converters=self.converters
            , ignore_converters=self.ignore_converters
            )

    def keys(self):
        """Return a de-duplicated list of the keys we know about"""
        return self.storage.keys_after(self.prefix_string)

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

    def converted_path(self, path, ignore_converters=True, converters=None):
        """Convert a path into a Path object with a prefixed path"""
        if isinstance(path, basestring):
            path = self.prefixed_path_string(path)
        elif isinstance(path, (list, tuple)):
            path = self.prefixed_path_list(path)

        if converters is None:
            converters = self.converters
        return Path.convert(path, self, converters=converters).ignoring_converters(ignore_converters)

    def prefixed_path_list(self, path):
        """Proxy the prefixed_path_list helper with prefix from this instance"""
        return hp.prefixed_path_list(path, self.prefix_list)

    def prefixed_path_string(self, path):
        """Proxy the prefixed_path_string helper with prefix from this instance"""
        return hp.prefixed_path_string(path, self.prefix_string)

    def add_converter(self, converter):
        """Add a converter to our collection"""
        if converter not in self.converters:
            self.converters.append(converter)

