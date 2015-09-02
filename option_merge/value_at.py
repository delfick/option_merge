from option_merge.versioning import VersionedDict
from option_merge.merge import MergedOptions
from option_merge.not_found import NotFound
from option_merge.path import Path

def value_at(data, path, called_from=None, chain=None):
    """
    Return the value at this path

    It is assumed path is a Path object
    """
    if not chain:
        chain = []

    if not path:
        return chain, data

    data_type = type(data)
    if data_type not in (dict, VersionedDict, MergedOptions) and getattr(data, "is_dict", False) is not True:
        raise NotFound

    joined = path.joined()
    isMergedOptions = data_type is MergedOptions

    if not data:
        keys = []
    else:
        if hasattr(data, "reversed_keys"):
            keys = list(data.reversed_keys())
        else:
            keys = list(reversed(sorted(data.keys(), key=lambda d: len(str(d)))))

    if joined in keys:
        if isMergedOptions:
            da = data.get(path.path, ignore_converters=getattr(path, "ignore_converters", False))
        else:
            da = data[joined]

        if not chain:
            return path, da
        else:
            return chain + [path], da

    for key in keys:
        if path.first_part_is(key):
            try:
                if isMergedOptions:
                    nxt = data.get(key, ignore_converters=path.ignore_converters)
                else:
                    nxt = data[key]

                storage = getattr(nxt, "storage", None)
                if storage and called_from is storage:
                    raise NotFound

                prefix = path.without(key)
                if not prefix:
                    return chain+[key], nxt

                prefix = Path.convert(prefix).ignoring_converters(path.ignore_converters)
                return value_at(nxt, prefix, called_from, chain=chain+[key])
            except NotFound:
                pass

    raise NotFound

