import random
import time

class versioned_value(object):
    """
    A property that holds a cache of {prefix: {ignore_converters: value}}

    Where the entire cache is revoked if instance.version changes number
    """
    class NotYet(object): pass
    class First(object): pass

    def __init__(self, func):
        self.func = func
        self.cached_key = "_{0}_cached".format(self.func.__name__)
        self.expected_version_key = "_{0}_expected_version".format(self.func.__name__)

    def __get__(self, instance=None, owner=None):
        def returned(*args, **kwargs):
            version = getattr(instance, "version", 0)
            if version is -1:
                return self.func(instance, *args, **kwargs)

            if args:
                prefix = str(args[0])
            else:
                prefix = getattr(instance, "prefix_string", "")

            # Ignore_converters can be specified in three places, in this order
            # kwarg to the function
            # property on the path
            # property on the instance
            ignore_converters = kwargs.get('ignore_converters', getattr(prefix, 'ignore_converters', getattr(instance, 'ignore_converters', False)))

            cached = getattr(instance, self.cached_key, {})
            expected_version = getattr(instance, self.expected_version_key, self.First)

            if version != expected_version:
                cached = {}
                expected_version = version

            # We set the caches on the instance
            # so that they are garbage collected
            # When the instance gets deleted
            setattr(instance, self.cached_key, cached)
            setattr(instance, self.expected_version_key, expected_version)

            if cached.get(prefix, {}).get(ignore_converters, self.NotYet) is self.NotYet:
                if prefix not in cached:
                    cached[prefix] = {}
                try:
                    cached[prefix][ignore_converters] = (self.func(instance, *args, **kwargs), False)
                except KeyError as error:
                    cached[prefix][ignore_converters] = (error, True)

            val, is_error = cached[prefix][ignore_converters]
            if is_error:
                raise val
            else:
                return val
        return returned

class versioned_iterable(object):
    """
    A property that holds a cache of {instance: {prefix: {ignore_converters: iterator}}}

    Where the entire cache is revoked if instance.version changes number
    """
    class First(object): pass
    class NotYet(object): pass
    class Finished(object): pass

    def __init__(self, func):
        self.func = func
        self.cached_key = "_{0}_cached".format(self.func.__name__)
        self.value_cache_key = "_{0}_value_cache".format(self.func.__name__)
        self.expected_version_key = "_{0}_expected_version".format(self.func.__name__)

    def iterator_for(self, instance, prefix, ignore_converters, cached, value_cache):
        for item in value_cache[prefix][ignore_converters]:
            yield item

        iterator = cached[prefix][ignore_converters]
        if iterator is self.Finished:
            return
        ident = cached[prefix][ignore_converters] = "{0}:{1}".format(time.time(), random.random())

        try:
            while True:
                nxt = next(iterator)
                if cached.get(prefix, {}).get(ignore_converters) == ident:
                    value_cache[prefix][ignore_converters].append(nxt)
                yield nxt
        except StopIteration:
            iterator.close()
            if cached.get(prefix, {}).get(ignore_converters) == ident:
                cached[prefix][ignore_converters] = self.Finished

    def __get__(self, instance=None, owner=None):
        def returned(*args, **kwargs):

            version = getattr(instance, "version", 0)
            if version is -1:
                return self.func(instance, *args, **kwargs)

            if args:
                prefix = args[0]
            else:
                prefix = getattr(instance, "prefix_string", "")

            # Ignore_converters can be specified in three places, in this order
            # kwarg to the function
            # property on the path
            # property on the instance
            ignore_converters = kwargs.get('ignore_converters', getattr(prefix, 'ignore_converters', getattr(instance, 'ignore_converters', False)))

            cached = getattr(instance, self.cached_key, {})
            value_cache = getattr(instance, self.value_cache_key, {})
            expected_version = getattr(instance, self.expected_version_key, self.First)

            if version != expected_version:
                cached = {}
                value_cache = {}
                expected_version = version

            # We set the caches on the instance
            # so that they are garbage collected
            # When the instance gets deleted
            setattr(instance, self.cached_key, cached)
            setattr(instance, self.value_cache_key, value_cache)
            setattr(instance, self.expected_version_key, expected_version)

            if cached.get(prefix, {}).get(ignore_converters, self.NotYet) is not self.Finished:
                if prefix not in cached:
                    cached[prefix] = {}
                if prefix not in value_cache:
                    value_cache[prefix] = {}

                value_cache[prefix][ignore_converters] = []
                ret = self.func(instance, *args, **kwargs)
                if isinstance(ret, list):
                    value_cache[prefix][ignore_converters] = ret
                    cached[prefix][ignore_converters] = self.Finished
                else:
                    cached[prefix][ignore_converters] = ret
            return self.iterator_for(instance, prefix, ignore_converters, cached, value_cache)
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
        self.is_dict = True
        super(VersionedDict, self).__init__()

    def __setitem__(self, key, val):
        self.version += 1
        self.data[key] = val

    def __delitem__(self, key):
        self.version += 1
        del self.data[key]

    def __eq__(self, other):
        return self.data == other

    def __nonzero__(self):
        return True if self.data else False

    def __bool__(self):
        return bool(self.data)

    def keys(self):
        return self.data.keys()

    @versioned_value
    def reversed_keys(self):
        return list(reversed(sorted(self.keys(), key=lambda d: len(str(d)))))

    def values(self):
        return self.data.values()

    def update(self, other):
        self.data.update(other)

    def items(self):
        return self.data.items()

    def get(self, key, dflt=None):
        return self.data.get(key, dflt)

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

