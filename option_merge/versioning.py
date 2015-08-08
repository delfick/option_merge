from functools import wraps
import uuid

import __builtin__
orig_isinstance = __builtin__.isinstance
def new_isinstance(obj, kls):
    if kls == dict and isinstance(obj, VersionedDict):
        return True
    return orig_isinstance(obj, kls)
__builtin__.isinstance = new_isinstance

class versioned_value(object):
    """
    A property that holds a cache of {prefix: {ignore_converters: value}}

    Where the entire cache is revoked if instance.version changes number
    """
    class NotYet(object): pass

    def __init__(self, func):
        self.func = func
        self.cached = {}
        self.value_cache = {}
        self.expected_version = 0

    def __get__(self, instance=None, owner=None):
        @wraps(self.func)
        def returned(*args, **kwargs):
            version = getattr(instance, "version", 0)
            if version is -1:
                return self.func(instance, *args, **kwargs)

            ignore_converters = kwargs.get('ignore_converters', False)

            if args:
                prefix = str(args[0])
            else:
                prefix = getattr(instance, "prefix_string", "")

            if version != self.expected_version:
                self.cached = {}
                self.expected_version = version

            if self.cached.get(prefix, {}).get(ignore_converters, self.NotYet) is self.NotYet:
                if prefix not in self.cached:
                    self.cached[prefix] = {}
                if prefix not in self.value_cache:
                    self.value_cache[prefix] = {}

                self.value_cache[prefix][ignore_converters] = self.func(instance, *args, **kwargs)
            return self.value_cache[prefix][ignore_converters]
        return returned

class versioned_iterable(object):
    """
    A property that holds a cache of {prefix: {ignore_converters: iterator}}

    Where the entire cache is revoked if instance.version changes number
    """
    class NotYet(object): pass
    class Finished(object): pass

    def __init__(self, func):
        self.func = func
        self.cached = {}
        self.value_cache = {}
        self.expected_version = 0

    def iterator_for(self, instance, prefix, ignore_converters):
        for item in self.value_cache[prefix][ignore_converters]:
            yield item

        iterator = self.cached[prefix][ignore_converters]
        if iterator is self.Finished:
            return
        ident = self.cached[prefix][ignore_converters] = uuid.uuid1()

        try:
            while True:
                nxt = iterator.next()
                if self.cached[prefix][ignore_converters] == ident:
                    self.value_cache[prefix][ignore_converters].append(nxt)
                yield nxt
        except StopIteration:
            iterator.close()
            self.cached[prefix][ignore_converters] = self.Finished

    def __get__(self, instance=None, owner=None):
        @wraps(self.func)
        def returned(*args, **kwargs):
            version = getattr(instance, "version", 0)
            if version is -1:
                return self.func(instance, *args, **kwargs)

            ignore_converters = kwargs.get('ignore_converters', False)

            if args:
                prefix = args[0]
            else:
                prefix = getattr(instance, "prefix_string", "")

            if version != self.expected_version:
                self.cached = {}
                self.value_cache = {}
                self.expected_version = version

            if self.cached.get(prefix, {}).get(ignore_converters, self.NotYet) is not self.Finished:
                if prefix not in self.cached:
                    self.cached[prefix] = {}
                if prefix not in self.value_cache:
                    self.value_cache[prefix] = {}

                self.value_cache[prefix][ignore_converters] = []
                ret = self.func(instance, *args, **kwargs)
                if isinstance(ret, list):
                    self.value_cache[prefix][ignore_converters] = ret
                    self.cached[prefix][ignore_converters] = self.Finished
                else:
                    self.cached[prefix][ignore_converters] = self.func(instance, *args, **kwargs)
            return self.iterator_for(instance, prefix, ignore_converters)
        return returned

class VersionedDict(object):
    """
    A wrapper for dictionaries that has a version property

    The version starts at 0 and is incremented whenever __setitem__ or __delitem__ is used
    """
    @classmethod
    def convert(kls, item):
        from option_merge import MergedOptions
        if isinstance(item, dict):
            if not isinstance(item, VersionedDict) and not isinstance(item, MergedOptions):
                return kls(item)
        return item

    def __init__(self, data):
        self.data = data
        self.version = 0
        super(VersionedDict, self).__init__()

    def __setitem__(self, key, val):
        self.version += 1
        self.data[key] = val

    def __delitem__(self, key):
        self.version += 1
        del self.data

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        return self.data[key]

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return self.data.__str__()

    def __unicode__(self):
        return self.data.__unicode__()

