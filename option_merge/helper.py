class NotFound(Exception): pass
"""Used to signify no value was found"""

def value_at(data, path, chain=None):
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
                return value_at(data[key], path[len(key)+1:], chain=chain + [key])
            except NotFound:
                pass

    raise NotFound

def without_prefix(path, prefix=""):
    """
    Remove the prefix from a path

    If the prefix isn't on this path, just return the path itself

    If the path is the prefix, return the prefix
    """
    if not prefix or not path or prefix == path:
        return path

    if path.startswith("{0}.".format(prefix)):
        return path[len(prefix)+1:]

    return path

def prefixed_path_list(path, prefix=None):
    """Return the prefixed version of this path as a list"""
    if not prefix:
        return path

    if prefix is None:
        prefix = []

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

def dot_joiner(lst):
    """Join list of strings with a single dot in between each"""
    result = []
    for part in lst:
        while part and part.startswith("."):
            part = part[1:]

        while part and part.endswith("."):
            part = part[:-1]

        if part:
            result.append(part)

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

