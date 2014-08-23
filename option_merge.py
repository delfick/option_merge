from delfick_error import DelfickError
from collections import Mapping
from itertools import chain
from copy import deepcopy
import six

class NotFound: pass
"""Used to signify no value was found"""

class BadPrefix(DelfickError): pass
"""Used to say a prefix value is not a dictionary"""

class KeyValuePairsConverter(object):
    """Converts a list of key,value pairs to a dictionary"""
    def __init__(self, pairs):
        self.pairs = pairs

    def convert(self):
        """Return us a dictionary from our pairs"""
        options = MergedOptions()
        for key, value in self.pairs:
            options[str(key)] = value
        return options.overrides

class AttributesConverter(object):
    """Converts an object with particular attributes to a dictionary"""
    def __init__(self, obj, attributes=None, include_underlined=False, lift=None, ignoreable_values=None):
        self.obj = obj
        self.lift = lift
        self.attributes = attributes
        self.ignoreable_values = ignoreable_values
        self.include_underlined = include_underlined

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

        result = options.overrides
        if self.lift:
            lifted = MergedOptions()
            lifted[self.lift] = result
            result = lifted.overrides
        return result

class ConverterProperty(object):
    """Creates a Property for accessing a converter"""
    def __init__(self, converter):
        self.converter = converter

    def __get__(self, obj=None, owner=None):
        return lambda *args, **kwargs: self.converter(*args, **kwargs).convert()

class MergedOptions(Mapping):
    """
    Wrapper around multiple dictionaries to behave as one.

    Usage::

        options = MergedOptions.using(options1, options2)

    Is equivalent to::

        options = MergedOptions()
        options.update(options1)
        options.update(options2)

    The later an option is added, the more influence it has.
    i.e. when a key is accessed, later options are looked at first.

    When options are added, copies are made.

    When you set a key on the merged options, it adds it to a special overrides dictionary.
    This overrides is looked at first when accessing a key.

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

    You may also get all values for a key with merged.values_for(path)
    Where path is a dot seperated path
    so merged.values_for("a.b") == [4, 1]

    You can also get all deeply nested keys with merged.all_keys()
    so merged.all_keys() == ["d", "a.b", "b", "a.c"]
    """

    Attributes = ConverterProperty(AttributesConverter)
    KeyValuePairs = ConverterProperty(KeyValuePairsConverter)

    def __init__(self, prefix=None, options=None, overrides=None):
        self.prefix = prefix
        self.options = options
        self.overrides = overrides

        if self.options is None:
            self.options = []

        if self.overrides is None:
            self.overrides = {}

    @classmethod
    def using(cls, *options):
        """Convenience for calling update multiple times"""
        merged = cls()
        for opts in options:
            merged.update(opts)
        return merged

    def update(self, options):
        """Add new options"""
        if options is None:
            return

        if not self.prefix:
            self.options.insert(0, deepcopy(options))
        else:
            for value in self.values_for(""):
                if isinstance(value, dict):
                    value.update(options)
                else:
                    value.options.insert(0, deepcopy(options))

                break

    def values_for(self, path):
        """
        Get all known values for some path

        First consult the overrides

        Then look at each option dictionary that has been registered.
        """
        results = []

        try:
            results.append(self.at_path(self.prefix_key(path), self.overrides))
        except (BadPrefix, KeyError):
            pass

        for opts in self.options:
            try:
                results.append(self.at_path(self.prefix_key(path), opts))
            except (BadPrefix, KeyError):
                pass

        for found in results:
            if found is not NotFound:
                yield found

    def __getitem__(self, key):
        """
        Access a key.

        Return the first value it comes across
        Raise KeyError if nothing has the specified key
        """
        for val in self.values_for(key):
            if isinstance(val, dict) or isinstance(val, MergedOptions):
                return self.prefixed(self.prefix_key(key).split('.'))
            else:
                return val
        raise KeyError(self.prefix_key(key))

    def __setitem__(self, key, value):
        """Set a key in the overrides"""
        split = self.prefix_key(key).split('.')
        start, last = split[:-1], split[-1]
        if not start:
            pathed = self.overrides
        else:
            pathed = self.after_prefix(self.overrides, prefix=start, create=True, silent=True)

        pathed[last] = value

    def __delitem__(self, key):
        """
        Delete a key from the first option dictionary that has it.

        Only deletes from the first occurrence, which means deleting a key
        may just change it's value than get rid of it.

        Raise a KeyError if the key doesn't exist
        """
        split = self.prefix_key(key).split('.')
        start, last = split[:-1], split[-1]

        prefixed_overrides = self.after_prefix(self.overrides, silent=True, prefix=start)
        if last in prefixed_overrides:
            del prefixed_overrides[last]
            self.clean_prefix(self.overrides)
            return

        for opts in self.options:
            prefixed_opts = self.after_prefix(opts, silent=True, prefix=start)
            if last in prefixed_opts:
                del prefixed_opts[last]
                self.clean_prefix(opts, start)
                return

        raise KeyError(self.prefix_key(key))

    def clean_prefix(self, opts, prefix=NotFound):
        """If our prefix to opts is an empty dictionary, then remove it"""
        if prefix is NotFound:
            prefix = self.prefix

        if prefix:
            start, last = prefix[:-1], prefix[-1]
            prefixed = self.after_prefix(opts, silent=True, prefix=start)
            if last in prefixed and prefixed[last] == {}:
                del prefixed[last]

    def prefix_key(self, key):
        """Return a key representing prefix on this class and extra key"""
        prefix = self.prefix or []
        if key:
            prefix = list(prefix) + key.split('.')
        return '.'.join(prefix)

    def after_prefix(self, opts, prefix=NotFound, silent=False, create=False):
        """
        Return part in provided opts after our prefix
        Only complain if the prefix doesn't exist if silent is False
        Otherwise just return an empty dictionary
        """
        if prefix is NotFound:
            prefix = self.prefix

        if prefix is None:
            return opts

        if isinstance(prefix, six.string_types):
            prefix = prefix.split(".")

        result = opts
        full_key = []
        for key in prefix:
            full_key.append(key)
            if key in result and (isinstance(result[key], dict) or isinstance(result[key], MergedOptions)):
                result = result[key]
            else:
                if silent:
                    if create:
                        result[key] = {}
                        result = result[key]
                    else:
                        return {}
                else:
                    if key in result:
                        raise BadPrefix("Value is not a dictionary", key='.'.join(full_key), found=type(result[key]))
                    else:
                        raise KeyError('.'.join(full_key))

        return result

    def at_path(self, path, opts):
        """Return value in provided opts after provided dot seperated string path"""
        if not path:
            return opts

        split = path.split('.')
        start, last = split[:-1], split[-1]
        prefixed = self.after_prefix(opts, prefix=start, silent=False)
        if last in prefixed:
            return prefixed[last]
        else:
            return NotFound

    def prefixed(self, prefix):
        """Return a MergedOptions object that is this object prefixed with our prefix and provided key"""
        return MergedOptions(prefix=prefix, options=self.options, overrides=self.overrides)

    def all_keys_from(self, opts, prefix=None):
        """Get us all deeply nested keys"""
        result = []
        if prefix is None:
            prefix = []

        if isinstance(opts, dict) or isinstance(opts, MergedOptions):
            for key in opts:
                for full_key in self.all_keys_from(opts[key], prefix + [key]):
                    result.append(full_key)
        else:
            result.append('.'.join(prefix))

        return set(result)

    def keys(self):
        """Return a de-duplicated list of the keys we know about"""
        prefixed_overrides = self.after_prefix(self.overrides, silent=True).keys()
        prefixed_opts = [self.after_prefix(opts, silent=True).keys() for opts in self.options]
        return list(set(chain.from_iterable(prefixed_opts + [prefixed_overrides])))

    def all_keys(self):
        """Return all keys in our options"""
        all_overrides = [list(self.all_keys_from(self.overrides))]
        opts_keys = [list(self.all_keys_from(opts)) for opts in self.options]
        if self.prefix:
            prefix_key = "{0}.".format('.'.join(self.prefix or ""))
        else:
            prefix_key = ""

        lst = list(key[len(prefix_key):] for key in list(chain.from_iterable(opts_keys + all_overrides)) if key.startswith(prefix_key))
        result = []
        for key in lst:
            key_with_dot = "{0}.".format(key)
            result = [thing for thing in result if not thing.startswith(key_with_dot)]
            result.append(key)
        return set(result)

    def __iter__(self):
        """Iterate over the keys"""
        return iter(self.keys())

    def __len__(self):
        """Get number of keys we have"""
        return len(list(self.keys()))

    def items(self):
        """Get everything as a concrete dictionary"""
        top = {}
        keys = self.all_keys()
        for key in keys:
            result = top
            split = key.split('.')
            start, last = split[:-1], split[-1]
            for part in start:
                if part not in result:
                    result[part] = {}
                result = result[part]

            if isinstance(result, dict) or isinstance(result, MergedOptions):
                result[last] = self[key]

                if isinstance(result[last], MergedOptions):
                    result[last] = dict(result[last].items())

        return top.items()

    def as_flat(self):
        """Return everything as flat list of [(key, val), ...]"""
        for key in self.all_keys():
            val = self[key]
            if not isinstance(val, dict) and not isinstance(val, MergedOptions):
                yield (key, val)

