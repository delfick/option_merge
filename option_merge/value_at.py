from option_merge.versioning import VersionedDict
from option_merge.merge import MergedOptions
from option_merge.not_found import NotFound
from option_merge.path import Path

def value_at(data, path, called_from=None, chain=None):
    """Return the value at this path"""
    if not chain:
        chain = []

    if not path:
        return chain, data

    data_type = type(data)
    if data_type not in (dict, VersionedDict, MergedOptions):
        raise NotFound

    if hasattr(data, "reversed_keys"):
        keys = list(data.reversed_keys())
    else:
        keys = list(reversed(sorted(data.keys(), key=lambda d: len(str(d)))))

    if Path.inside(path, keys):
        if isinstance(path, Path) and isinstance(data, MergedOptions):
            da = data.get(path.path, ignore_converters=getattr(path, "ignore_converters", False))
        else:
            if isinstance(path, Path):
                da = data[path.joined()]
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

                if not prefix:
                    return chain+[key.path], nxt
                return value_at(nxt, prefix, called_from, chain=chain+[key.path])
            except NotFound:
                pass

    raise NotFound

