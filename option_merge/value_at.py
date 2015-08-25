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
    if data_type not in (dict, VersionedDict, MergedOptions):
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
                prefix = Path.convert(without_prefix(path, key)).ignoring_converters(getattr(path, "ignore_converters", False))

                key = Path.convert(key, None, ignore_converters=Path.convert(path, None).ignore_converters)

                    nxt = data.get(key.path, ignore_converters=getattr(key, "ignore_converters", False))
                else:
                    nxt = data[key.path]

                storage = getattr(nxt, "storage", None)
                if storage and called_from is storage:
                    raise NotFound

                if not prefix:
                    return chain+[key.path], nxt
                return value_at(nxt, prefix, called_from, chain=chain+[key.path])
            except NotFound:
                pass

    raise NotFound

