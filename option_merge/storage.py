from option_merge.helper import value_at, NotFound, dot_joiner, make_dict
from delfick_error import ProgrammerError
from collections import namedtuple
import six

class Path(namedtuple("Path", ("path", "data", "source"))):

    def keys_after(self, prefix):
        """All the keys after prefix"""
        parts = [part for part in self.path]
        for part in self.path:
            if prefix.startswith("{0}.".format(part)) or prefix == part:
                prefix = prefix[len(part)+1:]
                parts.pop(0)
            elif not prefix and parts:
                yield parts[0]
                return
            else:
                raise NotFound

        if parts:
            yield parts[0]
        elif isinstance(self.data, dict):
            for key in self.data.keys():
                yield key

    def value_after(self, prefix):
        """Returns the value after prefix"""
        parts = [part for part in self.path]
        for part in self.path:
            if prefix.startswith("{0}.".format(part)) or prefix == part:
                prefix = prefix[len(part)+1:]
                parts.pop(0)
            elif not prefix and parts:
                return make_dict(parts[0], parts[1:], self.data)
            else:
                raise NotFound

        if parts:
            return make_dict(parts[0], parts[1:], self.data)
        elif isinstance(self.data, dict):
            if prefix:
                if prefix in self.data:
                    return self.data[prefix]
                else:
                    raise NotFound

        return self.data

class Storage(object):
    """Holds the dataz"""

    def __init__(self):
        self.data = []
        self.deleted = []

    ########################
    ###   USAGE
    ########################

    def add(self, path, data, source=None):
        """Add data at the beginning"""
        if isinstance(path, six.string_types):
            raise ProgrammerError("Path should be a list\tgot={0}".format(type(path)))
        self.data.insert(0, (path, data, source))

    def get(self, path):
        """Get a single value from a path"""
        for info in self.get_info(path):
            return info.data
        raise KeyError(path)

    def source_for(self, path):
        """Find all the sources for a given path"""
        sources = []
        for info in self.get_info(path):
            if dot_joiner(info.path) == path and not isinstance(info.data, dict):
                if isinstance(info.source, list):
                    return [thing for thing in info.source]
                else:
                    return [info.source]
            else:
                if info.source not in sources:
                    sources.append(info.source)

        if sources:
            return sources
        else:
            raise KeyError(path)

    def delete(self, path):
        """Delete the first instance of some path"""
        for index, (info_path, data, _) in enumerate(self.data):
            dotted_info_path = dot_joiner(info_path)
            if dotted_info_path == path:
                del self.data[index]
                return
            elif dotted_info_path.startswith("{0}.".format(path)):
                del self.data[index]
                return
            elif not dotted_info_path or path.startswith("{0}.".format(dotted_info_path)):
                remainder = path
                if info_path:
                    remainder = path[len(dotted_info_path)+1:]
                if self.delete_from_data(data, remainder):
                    return

        raise KeyError(path)

    ########################
    ###   IMPLEMENTATION
    ########################

    def get_info(self, path):
        yielded = False
        if not self.data and not path:
            return

        for info_path, data, source in self.data:
            dotted_info_path = dot_joiner(info_path)
            if not info_path or not path or path == dotted_info_path or path.startswith("{0}.".format(dotted_info_path)) or dotted_info_path.startswith("{0}.".format(path)):
                try:
                    get_at = path
                    if info_path:
                        get_at = path[len(dotted_info_path)+1:]
                    found_path, val = value_at(data, get_at)
                    if hasattr(data, "source_for"):
                        source = data.source_for(get_at)
                    yield Path(info_path + found_path, val, source)
                    yielded = True
                except NotFound:
                    pass

        if not yielded:
            raise KeyError(path)

    def keys_after(self, path):
        """Get all the keys after this path"""
        done = set()
        stopped = set()
        for info in self.get_info(path):
            for key in info.keys_after(path):
                joined = dot_joiner([path, key])
                if not any(s == joined or joined.startswith("{0}.".format(s)) for s in stopped):
                    if key not in done:
                        yield key
                        done.add(key)

            if not isinstance(info.data, dict):
                stopped.add(dot_joiner(info.path))

    def delete_from_data(self, data, path):
        if not path or not isinstance(data, dict):
            return False

        keys = list(reversed(sorted(data.keys())))
        if path in keys:
            del data[path]
            return True

        for key in keys:
            if path.startswith("{0}.".format(key)):
                if self.delete_from_data(data[key], path[len(key)+1:]):
                    return True

