"""
Option_merge uses this Path object to encapsulate the idea of a path and the
converters that are available to use.

We are able to use this to store a reference to the root of the configuration
as well as whether the converters should be ignored or not.
"""

from option_merge.joiner import dot_joiner, join

from delfick_error import ProgrammerError
import six

class Path(object):
    """
    Encapsulate a path; a root configuration; a list of converters; and whether
    the converters should be used or not
    """
    @classmethod
    def convert(kls, path, configuration=None, converters=None, ignore_converters=None):
        """
        Get us a Path object from this path

        If already a Path object, then return a clone of the path
        """
        if isinstance(path, Path):
            return path.clone()
        else:
            return Path(path, configuration, converters, ignore_converters)

    def __init__(self, path, configuration=None, converters=None, ignore_converters=False):
        self.path = path
        self.converters = converters
        self.configuration = configuration
        self.ignore_converters = ignore_converters

    def __unicode__(self):
        return dot_joiner(self.path)

    def __str__(self):
        return dot_joiner(self.path)

    def __nonzero__(self):
        return bool(self.path)

    def __len__(self):
        if isinstance(self.path, six.string_types):
            if self.path:
                return 1
            else:
                return 0
        else:
            return len(self.path)

    def __iter__(self):
        if isinstance(self.path, six.string_types):
            if self.path:
                yield self.path
        else:
            for part in self.path:
                yield part

    def __repr__(self):
        return "<Path({0})>".format(unicode(self))

    def __eq__(self, other):
        return dot_joiner(other) == dot_joiner(self.path)

    def __ne__(self, other):
        return dot_joiner(other) != dot_joiner(self.path)

    def __add__(self, other):
        return self.using(join(self, other))

    def __hash__(self):
        return hash(dot_joiner(self.path))

    def without(self, base):
        """Return a clone of this path without the base"""
        if not self.startswith(dot_joiner(base)):
            from option_merge import helper as hp
            raise hp.NotFound()

        if isinstance(self.path, six.string_types):
            path = self.path[len(dot_joiner(base)):]
            while path.startswith("."):
                path = path[1:]
            return self.using(path)
        else:
            base = dot_joiner(base)
            if not base:
                res = [part for part in self.path]
            else:
                res = []
                for part in self.path:
                    if not base:
                        res.append(part)
                        continue

                    if base.startswith(unicode(part)):
                        base = base[len(dot_joiner(part)):]
                        while base.startswith('.'):
                            base = base[1:]
                    elif part.startswith(base):
                        res.append(part[len(base)])
                        base = ""

            return self.using(res)

    def prefixed(self, prefix):
        """Return a clone with this prefix to the path"""
        return self.using(join(prefix, self))

    def startswith(self, base):
        """Does the path start with this string?"""
        return dot_joiner(self.path).startswith(base)

    def endswith(self, suffix):
        """Does the path end with this string?"""
        return dot_joiner(self.path).endswith(suffix)

    def using(self, path, configuration=None, converters=None, ignore_converters=True):
        """Return a clone of this path and override with provided values"""
        if configuration is None:
            configuration = self.configuration
        if converters is None:
            converters = self.converters
        if isinstance(path, Path):
            path = path.path
        return self.__class__(path, configuration, converters, ignore_converters=ignore_converters)

    def clone(self):
        """Return a clone of this path with all the same values"""
        return self.using(self.path, self.configuration, self.converters, self.ignore_converters)

    def ignoring_converters(self, ignore_converters=True):
        """Return a clone of this path with ignore_converters set to True"""
        return self.using(self.path, ignore_converters=ignore_converters)

    def do_conversion(self, value):
        """
        Do the conversion on some path if any conversion exists

        Return (converted, did_conversion)

        Where ``did_conversion`` is a boolean indicating whether a conversion
        took place.
        """
        converter, found = self.find_converter()
        if not found:
            return value, False
        else:
            converted = converter(self, value)
            self.converters.done(self, converted)
            return converted, True

    def find_converter(self):
        """Find appropriate converter for this path"""
        if self.ignore_converters:
            return None, False

        if self.converters:
            for converter in self.converters:
                if not hasattr(converter, "matches") or converter.matches(self):
                    return converter, True

        return None, False

    def converted(self):
        """Determine if this path has been converted"""
        if self.converters:
            return self.converters.converted(self)
        return False

    def converted_val(self):
        """Return the converted value for this path"""
        return self.converters.converted_val(self)

    def joined(self):
        """Return the dot_join of of the path"""
        return dot_joiner(self.path)

