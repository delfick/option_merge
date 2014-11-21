from option_merge.path import Path
import fnmatch
import six

class NotFound(Exception): pass
"""Used to signify no value was found"""

def value_at(data, path, called_from=None, chain=None):
    """Return the value at this path"""
    if not chain:
        chain = []

    if not path:
        return chain, data

    elif path and not isinstance(data, dict):
        raise NotFound

    keys = list(reversed(sorted(data.keys())))

    if path in keys:
        return chain + [path], data[path]

    for key in keys:
        if path.startswith("{0}.".format(key)):
            try:
                prefix = without_prefix(path, key)

                key = Path.convert(key, None, ignore_converters=Path.convert(path, None).ignore_converters)

                storage = getattr(data[key], "storage", None)
                if storage and called_from is storage:
                    raise NotFound

                return value_at(data[key], prefix, called_from, chain=chain+[key])
            except NotFound:
                pass

    raise NotFound

def without_prefix(path, prefix=""):
    """
    Remove the prefix from a path

    If the prefix isn't on this path, just return the path itself
    """
    if hasattr(path, 'without'):
        return path.without(prefix)

    if not prefix or not path:
        return path

    if prefix == path:
        return ""

    if path.startswith("{0}.".format(prefix)):
        return path[len(prefix)+1:]

    return path

def prefixed_path_list(path, prefix=None):
    """Return the prefixed version of this path as a list"""
    if not prefix:
        return path

    if prefix is None:
        prefix = []

    from option_merge.path import Path
    if isinstance(path, Path):
        return path.prefixed(prefix)
    else:
        return prefix + path

def prefixed_path_string(path, prefix=""):
    """Return the prefixed version of this string"""
    while path and path.startswith("."):
        path = path[1:]

    while path and path.endswith("."):
        path = path[:-1]

    while prefix and prefix.startswith("."):
        prefix = prefix[1:]

    while prefix and prefix.endswith("."):
        prefix = prefix[:-1]

    result = []
    if prefix:
        result.append(prefix)
    if path:
        result.append(path)
    return '.'.join(result)

def make_dict(first, rest, data):
    """Make a dictionary from a list of keys"""
    last = first
    result = {first: data}
    current = result
    for part in rest:
        current[last] = {}
        current = current[last]
        current[part] = data
        last = part

    return result

