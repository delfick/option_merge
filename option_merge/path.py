"""
Option_merge uses this Path object to encapsulate the idea of a path and the
converters that are available to use.

We are able to use this to store a reference to the root of the configuration
as well as whether the converters should be ignored or not.

It's purpose is to behave like a string regardless of whether it is a string
or a list of strings.
"""

from option_merge.joiner import dot_joiner, join
from option_merge.not_found import NotFound

import six

class Path(object):
    """
    Encapsulate a path; a root configuration; a list of converters; and whether
    the converters should be used or not

    A path may be just a string or a list of strings.
    """
    @classmethod
    def convert(kls, path, configuration=None, converters=None, ignore_converters=None, joined=None):
        """
        Get us a Path object from this path

        If path is already a Path instance, it is returned as is.

        Otherwise, a joined version of the string is created and used,
        along with the other kwargs to this function, to produce a new Path instance
        """
        path_type = type(path)
        if path_type is Path:
            return path
        else:
            joined = dot_joiner(path, item_type=path_type)
            return Path(path, configuration, converters, ignore_converters, joined=joined)

    def __init__(self, path, configuration=None, converters=None, ignore_converters=False, joined=None, joined_function=None):
        self.path = path
        self.path_type = type(self.path)
        self.path_is_string = self.path_type in (str, ) + six.string_types

        self._joined = joined
        self._joined_function = joined_function

        self.converters = converters
        self.configuration = configuration
        self.ignore_converters = ignore_converters

    def __unicode__(self):
        """alias for self.joined"""
        return self.joined()

    def __str__(self):
        """alias for self.joined"""
        return self.joined()

    def __nonzero__(self):
        """Whether we have any path or not"""
        return any(self.path)

    def __len__(self):
        """
        The length of our path

        * If we have no path, then 0
        * if path is a string, then 1
        * if path is an array, then the length of the array
        """
        if self.path_is_string:
            if self.path:
                return 1
            else:
                return 0
        else:
            if self.path_type in (list, tuple):
                if not any(item for item in self.path):
                    return 0
            return len(self.path)

    def __iter__(self):
        """Iterate through the parts of our path"""
        if self.path_is_string:
            if self.path:
                yield self.path
        else:
            for part in self.path:
                yield part

    def __repr__(self):
        return "<Path({0})>".format(str(self))

    def __eq__(self, other):
        """
        Compare the joined version of this path
        and the joined version of the other path
        """
        joined = self.joined()
        if not other and not joined:
            return True

        if other and joined:
            return dot_joiner(other) == self.joined()

        return False

    def __ne__(self, other):
        """Negation of whether other is equal to this path"""
        return not self.__eq__(other)

    def __add__(self, other):
        """Create a copy of this path joined with other"""
        if not other:
            return self.clone()
        else:
            return self.using(join(self, other))

    def __hash__(self):
        """The hash of the joined version of this path"""
        return hash(self.joined())

    def __getitem__(self, key):
        """
        If the path is a string, treat it as a list of that one string,
        otherwise, treat path as it is
        and get the index of the path as specified by key
        """
        path = self.path
        if self.path_is_string:
            path = [path]
        return path[key]

    def without(self, base):
        """Return a clone of this path without the base"""
        base_type = type(base)
        if base_type not in (str, ) + six.string_types:
            base = dot_joiner(base, base_type)

        if not self.startswith(base):
            raise NotFound()

        if self.path_is_string:
            path = self.path[len(base):]
            while path and path[0] == ".":
                path = path[1:]
            return self.using(path, joined=path)
        else:
            if not base:
                res = [part for part in self.path]
            else:
                res = []
                for part in self.path:
                    if not base:
                        res.append(part)
                        continue

                    part_type = type(part)
                    if part_type in (str, ) + six.string_types:
                        joined_part = part
                    else:
                        joined_part = dot_joiner(part, part_type)

                    if base.startswith(joined_part):
                        base = base[len(joined_part):]
                        while base and base[0] == ".":
                            base = base[1:]
                    elif joined_part.startswith(base):
                        res.append(joined_part[len(base):])
                        base = ""

            return self.using(res, joined=dot_joiner(res, list))

    def prefixed(self, prefix):
        """Return a clone with this prefix to the path"""
        if not prefix:
            return self.clone()
        else:
            return self.using(join(prefix, self))

    def first_part_is(self, key):
        """Return whether the first part of this path is this string"""
        if self.path_is_string:
            return self.path.startswith(str(key) + '.')
        if not self.path:
            return not bool(key)
        if self.path_type is list:
            return self.path[0] == key
        if self.path_type is Path:
            return self.path.first_part_is(key)
        return self.joined().startswith(str(key) + '.')

    def startswith(self, base):
        """Does the path start with this string?"""
        if self.path_is_string:
            return self.path.startswith(base)
        if not self.path:
            return not bool(base)
        if self.path_type is list and len(self.path) is 1:
            return self.path[0].startswith(base)
        return self.joined().startswith(base)

    def endswith(self, suffix):
        """Does the path end with this string?"""
        return self.joined().endswith(suffix)

    def using(self, path, configuration=None, converters=None, ignore_converters=False, joined=None):
        """Return a clone of this path and override with provided values"""
        if configuration is None:
            configuration = self.configuration
        if converters is None:
            converters = self.converters

        if path == self.path and self.configuration is configuration and self.converters is converters and self.ignore_converters is ignore_converters:
            return self

        joined_function = None
        if joined is None:
            if type(path) is Path:
                joined_function = lambda: dot_joiner(path.path, path.path_type)
            else:
                joined_function = lambda: dot_joiner(path)
        return self.__class__(path, configuration, converters, ignore_converters=ignore_converters, joined_function=joined_function)

    def clone(self):
        """Return a clone of this path with all the same values"""
        joined_function = lambda: dot_joiner(self.path, self.path_type)
        return self.__class__(self.path, self.configuration, self.converters, self.ignore_converters, joined_function=joined_function)

    def ignoring_converters(self, ignore_converters=True):
        """Return a clone of this path with ignore_converters set to True"""
        if self.ignore_converters == ignore_converters:
            return self
        return self.using(self.path, ignore_converters=ignore_converters, joined=self.joined())

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
            if hasattr(converted, "post_setup"):
                converted.post_setup()
            return converted, True

    def find_converter(self):
        """Find appropriate converter for this path"""
        if self.ignore_converters:
            return None, False
        return self.converters.matches(self)

    def converted(self):
        """Determine if this path has been converted"""
        if self.converters:
            return self.converters.converted(self)
        return False

    def converted_val(self):
        """Return the converted value for this path"""
        return self.converters.converted_val(self)

    def waiting(self):
        """Return whether we're waiting for this value"""
        return self.converters.waiting(self)

    def joined(self):
        """Return the dot_join of of the path"""
        joined = self._joined
        if self._joined is None and self._joined_function is not None:
            joined = self._joined = self._joined_function()

        if joined is None:
            if self.path_is_string:
                joined = self._joined = self.path
            else:
                joined = self._joined = dot_joiner(self.path, self.path_type)
        return joined

