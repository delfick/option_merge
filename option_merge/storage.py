"""
The Storage class is used to encapsulate the underlying data structure for
MergedOptions.

It's main functionality is the ``get_info`` method which yields DataPath objects
which can be used to get keys and values for some path.

It is also used to get thesource for particular paths.
"""

from option_merge.versioning import versioned_iterable, versioned_value, VersionedDict
from option_merge.merge import MergedOptions
from option_merge.not_found import NotFound
from option_merge.value_at import value_at
from option_merge.joiner import dot_joiner
from option_merge import helper as hp
from option_merge.path import Path

from delfick_error import ProgrammerError

class DataPath(object):
    """
    Encapsulates a (path, data, source) triplet and getting keys and values from
    that path in the data.
    """

    def __init__(self, path, data, source=None):
        self.path = path
        self.data = data
        self.source = source

    @property
    def is_dict(self):
        is_dict = getattr(self, "_is_dict", None)
        if is_dict is None:
            is_dict = self._is_dict = type(self.data) in (dict, VersionedDict, MergedOptions) or isinstance(self.data, dict)
        return is_dict

    def items(self, prefix, want_one=False):
        """
        Yield (key, data, short_path) triplets for after this prefix
        We don't return values to avoid any lazy computations
        Where short_path is the path (not including the key) from data

        First we remove the prefix from the path.

        If there is more prefix than path
            Dig into the data

        If there is more path than prefix
            yield the next part of the pa

        If the prefix isn't in the path
            raise NotFound

        If the prefix isn't in combination of path and data
            raise NotFound
        """
        data = self.data
        joined = self.path.joined()
        joined_prefix = prefix.joined()

        if not prefix or joined == joined_prefix or joined.startswith(joined_prefix + '.'):
            shortened_path = self.path.without(prefix)
            if shortened_path:
                yield list(shortened_path)[0], data, list(shortened_path)[1:]
                return
            else:
                prefix = ""
        else:
            if not joined_prefix.startswith(joined):
                raise NotFound
            else:
                prefix = Path(prefix).without(self.path)

        while True:
            if not prefix and want_one:
                yield "", data, []
                return

            if type(data) not in (dict, VersionedDict, MergedOptions) and getattr(data, "is_dict", False) is not True:
                raise NotFound

            if not prefix:
                for key in data.keys():
                    yield key, data, []
                return

            found = False
            for key in reversed(sorted(data.keys(), key=len)):
                if prefix.startswith(key):
                    data = data[key]
                    prefix = prefix.without(key)
                    found = True
                    break

            if not found:
                raise NotFound

    def keys_after(self, prefix):
        """Yield the keys after this prefix"""
        for key, _, _ in self.items(prefix):
            yield key

    @versioned_value
    def value_after(self, prefix):
        """Returns the value after prefix"""
        for key, data, short_path in self.items(prefix, want_one=True):
            if short_path:
                return hp.make_dict(key, short_path, data)
            else:
                if key:
                    return hp.make_dict(key, short_path, data)
                else:
                    return data

class Storage(object):
    """
    Holds the data used by MergedOptions.

    It understands the different sources of data that makes up the whole, how to
    get information for particular paths, how to delete particular paths, and
    how to get the sources for particular paths.
    """

    def __init__(self):
        self.data = []
        self.deleted = []
        self._version = -1

    ########################
    ###   USAGE
    ########################

    def add(self, path, data, source=None):
        """Add data at the beginning"""
        if not isinstance(path, Path):
            raise ProgrammerError("Path should be a Path object\tgot={0}".format(type(path)))
        self._version += 1
        self.data.insert(0, (path, VersionedDict.convert(data), source))

    def get(self, path):
        """Get a single value from a path"""
        for info in self.get_info(path):
            return info.data
        raise KeyError(path)

    def source_for(self, path, chain=None):
        """Find all the sources for a given path"""
        sources = []
        if chain is None:
            chain = []
        if (path, self) in chain:
            return []
        if not path:
            return []

        for info in self.get_info(path, ignore_converters=True, chain=chain + [(path, self)]):
            source = info.source
            if callable(info.source):
                source = info.source()

            if info.path == path and not info.is_dict:
                if isinstance(source, list):
                    return list(source)
                elif source:
                    return [source]
            else:
                if source not in sources:
                    if source:
                        if isinstance(source, list):
                            sources.extend(source)
                        else:
                            sources.append(source)

        if len(sources) == 1:
            return sources[0]
        else:
            return sources

    def delete(self, path):
        """Delete the first instance of some path"""
        for index, (info_path, data, _) in enumerate(self.data):
            dotted_info_path = dot_joiner(info_path)
            if dotted_info_path == path:
                self._version += 1
                del self.data[index]
                return
            elif dotted_info_path.startswith("{0}.".format(path)):
                self._version += 1
                del self.data[index]
                return
            elif not dotted_info_path or path.startswith("{0}.".format(dotted_info_path)):
                remainder = path
                if info_path:
                    remainder = Path.convert(path).without(dotted_info_path)
                if self.delete_from_data(data, remainder):
                    return

        raise KeyError(path)

    ########################
    ###   IMPLEMENTATION
    ########################

    @property
    def version(self):
        if self._version > 0:
            return [self._version] + [getattr(item, "version", 0) for item in self.data]
        else:
            return -1

    @versioned_iterable
    def get_info(self, path, ignore_converters=False, chain=None):
        """Yield DataPath objects for this path in the data"""
        yielded = False
        if not self.data:
            return

        if chain is None:
            chain = []

        ignore_converters = ignore_converters or getattr(path, 'ignore_converters', False)
        path = Path.convert(path).ignoring_converters(ignore_converters)

        for info_path, data, source in self.data:
            for full_path, found_path, val in self.determine_path_and_val(path, info_path, data, source):
                source = self.make_source_for_function(val, found_path, chain, default=source)
                yield DataPath(full_path, val, source)
                yielded = True

        if not yielded:
            raise KeyError(path)

    def determine_path_and_val(self, path, info_path, data, source):
        """
        Yield the full_path, found_path and val for this path into this data and info_path

        Where found_path is the path relative to the data
        """
        joined_path = dot_joiner(path)
        joined_info_path = dot_joiner(info_path)
        if joined_path == joined_info_path:
            yield info_path, "", data
            return

        try:
            if not info_path:
                found_path, val = value_at(data, Path.convert(path), self)
                yield info_path + found_path, dot_joiner(found_path, list), val
                return

            if joined_path.startswith(joined_info_path + '.'):
                get_at = Path.convert(path).without(info_path)
                found_path, val = value_at(data, get_at, self)
                yield info_path + found_path, dot_joiner(found_path), val
                return

            # We are only part way into info_path
            path = Path.convert(path)
            for key, data, short_path in DataPath(Path.convert(info_path), data, source).items(path, want_one=True):
                yield path, "", hp.make_dict(key, short_path, data)
        except NotFound:
            pass

    def make_source_for_function(self, obj, path, chain, default=None):
        """Return us a function that will get the source for some path on the specified obj"""
        def source_for():
            if hasattr(obj, "source_for"):
                nxt = obj.source_for(path, chain)
                if nxt:
                    return nxt
            return default
        return source_for

    @versioned_iterable
    def keys_after(self, path, ignore_converters=False):
        """Get all the keys after this path"""
        done = set()
        stopped = set()
        for info in self.get_info(path, ignore_converters=ignore_converters):
            if hasattr(info.data, "storage") and info.data.storage is self:
                continue

            try:
                for key in info.keys_after(Path.convert(path)):
                    if path:
                        joined = dot_joiner([path, key], list)
                    else:
                        joined = key

                    if not any(s == joined or joined.startswith("{0}.".format(s)) for s in stopped):
                        if key not in done:
                            yield key
                            done.add(key)
            except NotFound:
                pass

            if not info.is_dict:
                stopped.add(dot_joiner(info.path))

    def delete_from_data(self, data, path):
        """Delete this path from the data"""
        if not path or (type(data) not in (dict, VersionedDict, MergedOptions) and not isinstance(data, dict)):
            return False

        keys = list(reversed(sorted(data.keys())))
        if path in keys:
            self._version += 1
            del data[path]
            return True

        for key in keys:
            if path.startswith("{0}.".format(key)):
                if self.delete_from_data(data[key], Path.convert(path).without(key)):
                    return True

    def as_dict(self, path, seen=None, ignore=None):
        """Return this path as a single dictionary"""
        result = {}
        if seen is None:
            seen = {}

        if path not in seen:
            seen[path] = []
        if self in seen[path]:
            return {}
        seen[path].append(self)

        for i in range(len(self.data)-1, -1, -1):
            prefix, data, _ = self.data[i]

            if prefix:
                prefixer = list(prefix)
                while prefixer:
                    key = prefixer.pop()
                    data = VersionedDict({key: data})

            val = data
            used = None
            found = False
            path_without_prefix = path
            while not found or path_without_prefix:
                if hasattr(data, "as_dict"):
                    val = val.as_dict(path_without_prefix, seen=seen, ignore=ignore)
                    path_without_prefix = ""

                try:
                    used, val = value_at(val, path_without_prefix, self)
                    found = True
                except NotFound:
                    found = False
                    break

                if used and path_without_prefix:
                    path_without_prefix = path_without_prefix.without(dot_joiner(used))

            if found and path_without_prefix == "":
                is_dict = lambda item: type(item) in (dict, VersionedDict, MergedOptions) or isinstance(item, dict)
                if not is_dict(val):
                    result = val
                else:
                    if not is_dict(result):
                        result = {}
                    hp.merge_into_dict(result, val, seen, ignore=ignore)

        return result

