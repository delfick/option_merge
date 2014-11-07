from option_merge.helper import value_at, NotFound, dot_joiner, make_dict
from delfick_error import ProgrammerError
from namedlist import namedlist
import fnmatch
import six

class Converter(namedlist("Converter", ["convert", ("convert_path", None)])):
    def __init__(self, *args, **kwargs):
        super(Converter, self).__init__(*args, **kwargs)
        self.converted = []
        self.activated = False

    def __call__(self, data):
        if self.activated:
            return self.convert(data)
        else:
            return data

    def activate(self):
        self.activated = True

    def done(self, path):
        if self.activated:
            self.converted.append(path)

class Path(namedlist("Path", ["path", "data", ("source", None)])):

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

        if not parts and prefix and isinstance(self.data, dict) and prefix not in self.data:
            raise NotFound

        if parts:
            yield parts[0]

        data = self.data
        if prefix:
            if prefix not in data:
                raise NotFound
            data = data[prefix]

        if isinstance(data, dict):
            for key in data.keys():
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

        data = self.data
        if prefix:
            if prefix not in data:
                raise NotFound
            data = data[prefix]

        return data

class Storage(object):
    """Holds the dataz"""

    def __init__(self):
        self.data = []
        self.deleted = []

    ########################
    ###   USAGE
    ########################

    def add(self, path, data, source=None, converter=None):
        """Add data at the beginning"""
        if isinstance(path, six.string_types):
            raise ProgrammerError("Path should be a list\tgot={0}".format(type(path)))
        self.data.insert(0, (path, data, source, converter))

    def get(self, path, set_val=True):
        """Get a single value from a path"""
        for info in self.get_info(path, set_val=set_val):
            return info.data
        raise KeyError(path)

    def source_for(self, path, chain=None, set_val=False):
        """Find all the sources for a given path"""
        sources = []
        if chain is None:
            chain = []
        if path in chain:
            return []

        for info in self.get_info(path, chain + [path], set_val=set_val):
            source = info.source
            if callable(info.source):
                source = info.source()

            if dot_joiner(info.path) == path and not isinstance(info.data, dict):
                if isinstance(source, list):
                    return [thing for thing in source]
                else:
                    return [source]
            else:
                if source not in sources:
                    sources.append(source)

        if sources:
            return sources
        else:
            raise KeyError(path)

    def delete(self, path):
        """Delete the first instance of some path"""
        for index, (info_path, data, _, _) in enumerate(self.data):
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

    def get_info(self, path, chain=None, set_val=True):
        yielded = False
        if not self.data and not path:
            return

        if chain is None:
            chain = []

        for index, (info_path, data, source, converter) in enumerate(self.data):
            dotted_info_path = dot_joiner(info_path)
            if not info_path or not path or path == dotted_info_path or path.startswith("{0}.".format(dotted_info_path)) or dotted_info_path.startswith("{0}.".format(path)):
                try:
                    get_at = path
                    if info_path:
                        get_at = path[len(dotted_info_path)+1:]
                    found_path, val = value_at(data, get_at, self)
                except NotFound:
                    continue

                full_path = dot_joiner(info_path + found_path)
                if converter and set_val and full_path not in converter.converted:
                    converter.done(full_path)
                    val = self.convert(converter, val, full_path)
                    if found_path:
                        nxt = data
                        for part in found_path[:-1]:
                            nxt = nxt[part]

                        if isinstance(nxt, dict):
                            nxt[found_path[-1]] = val
                    else:
                        if data is not val:
                            self.data[index] = (info_path, val, source, converter)

                source = self.make_source_for_function(data, get_at, chain, default=source)
                yield Path(info_path + found_path, val, source)
                yielded = True

        if not yielded:
            raise KeyError(path)

    def convert(self, converter, data, path):
        """Convert our value"""
        if hasattr(converter, "convert_path"):
            if converter.convert_path and not fnmatch.fnmatch(path, dot_joiner(converter.convert_path)):
                return data

        return converter(data)

    def make_source_for_function(self, obj, path, chain, default=None):
        """Return us a function that will get the source for some path on the specified obj"""
        def source_for():
            if hasattr(obj, "source_for"):
                return obj.source_for(path, chain)
            else:
                return default
        return source_for

    def keys_after(self, path):
        """Get all the keys after this path"""
        done = set()
        stopped = set()
        for info in self.get_info(path):
            if hasattr(info.data, "storage") and info.data.storage is self:
                continue

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
