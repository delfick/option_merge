from option_merge.joiner import dot_joiner
from option_merge.path import Path

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

    if hasattr(data, "reversed_keys"):
        keys = list(data.reversed_keys())
    else:
        keys = list(reversed(sorted(data.keys(), key=lambda d: len(str(d)))))

    from option_merge.merge import MergedOptions
    if path in keys:
        if isinstance(path, Path) and isinstance(data, MergedOptions):
            da = data.get(path.path, ignore_converters=getattr(path, "ignore_converters", False))
        else:
            da = data[path]

        if not chain:
            return path, da
        else:
            return chain + [path], da

    for key in keys:
        if path.startswith("{0}.".format(key)):
            try:
                prefix = Path.convert(without_prefix(path, key)).ignoring_converters(getattr(path, "ignore_converters", False))

                key = Path.convert(key, None, ignore_converters=Path.convert(path, None).ignore_converters)

                if isinstance(data, MergedOptions):
                    nxt = data.get(key.path, ignore_converters=getattr(key, "ignore_converters", False))
                else:
                    nxt = data[key.path]

                storage = getattr(nxt, "storage", None)
                if storage and called_from is storage:
                    raise NotFound

                return value_at(nxt, prefix, called_from, chain=chain+[key.path])
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
    from option_merge.path import Path
    if isinstance(path, Path):
        if prefix:
            res = path.prefixed(prefix)
        else:
            res = path.clone()
    else:
        if prefix:
            res = prefix + path
        else:
            res = list(path)
    return res, dot_joiner(res)

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

    if not prefix:
        return path, path
    elif not path:
        return prefix, prefix
    else:
        res = "{0}.{1}".format(prefix, path)
        return res, res

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

def merge_into_dict(target, source, seen=None, ignore=None):
    """Merge source into target"""
    if ignore is None:
        ignore = []

    if hasattr(source, "as_dict"):
        source = source.as_dict(seen=seen, ignore=ignore)

    for key, val in source.items():
        if key in ignore:
            continue

        if isinstance(val, dict):
            if not isinstance(target.get(key), dict):
                target[key] = {}
            merge_into_dict(target[key], val, seen=seen)
        else:
            target[key] = val
