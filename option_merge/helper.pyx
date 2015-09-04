cimport cython
from option_merge cimport merge

from option_merge.versioning import VersionedDict
from option_merge.joiner import dot_joiner

cdef public prefixed_path_list(path, prefix):
    """Return the prefixed version of this path as a list"""
    res_type = type(path)
    if prefix:
        res = prefix + path
    else:
        res = list(path)
    return res, dot_joiner(res, res_type)

cdef public prefixed_path_string(path, prefix):
    """Return the prefixed version of this string"""
    while path and path[0] == '.':
        path = path[1:]

    while path and path[-1] == ".":
        path = path[:-1]

    while prefix and prefix[0] == ".":
        prefix = prefix[1:]

    while prefix and prefix[-1] == ".":
        prefix = prefix[:-1]

    if not prefix:
        return path, path
    elif not path:
        return prefix, prefix
    else:
        res = "{0}.{1}".format(prefix, path)
        return res, res

cdef public make_dict(first, rest, data):
    """Make a dictionary from a list of keys"""
    last = first
    result = VersionedDict({first: data})
    current = result
    for part in rest:
        current[last] = VersionedDict({})
        current = current[last]
        current[part] = data
        last = part

    return result

cdef public merge_into_dict(target, source, dict seen, list ignore):
    """Merge source into target"""
    from option_merge import merge

    if ignore is None:
        ignore = []

    if hasattr(source, "as_dict"):
        source = source.as_dict(seen=seen, ignore=ignore)

    for key, val in source.items():
        if key in ignore:
            continue

        is_dict = lambda item: type(item) in (dict, VersionedDict, merge.MergedOptions) or isinstance(item, dict)
        if is_dict(val):
            if not is_dict(target.get(key)):
                target[key] = VersionedDict({})
            merge_into_dict(target[key], val, seen=seen, ignore=None)
        else:
            target[key] = val
