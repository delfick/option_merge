"""
Option_merge includes functionality to convert values on access.

This functionality is assisted by the Converter and Converters classes.

Converter is used to encapsulate a single converter, and converters is used to
group together multiple converters.
"""

from option_merge.versioning import versioned_value
from option_merge.joiner import dot_joiner

class Converter(object):
    """
    Encapsulates a single converter.

    It contains the converting logic as well as a list of paths that this
    conversion should be used against.

    It has a method "matches" that is used against each possible path and will
    check for exact matches against the ``convert_path``.
    """
    def __init__(self, convert, convert_path=None):
        self.convert = convert
        self.convert_path = convert_path
        self.convert_path_joined = dot_joiner(convert_path)

    def __call__(self, path, data):
        """Proxy the conversion logic in ``self.convert``"""
        return self.convert(path, data)

    def matches(self, path):
        """Check to see if this converter should be used against this path"""
        if hasattr(path, "joined"):
            joined_path = path.joined()
        else:
            joined_path = dot_joiner(path)
        return self.convert_path and joined_path == self.convert_path_joined

class Converters(object):
    """
    Holds a group of converters.

    Has logic to say whether the converters are activated.

    Also memoizes the results of conversion.
    """
    def __init__(self):
        self._waiting = {}
        self._converted = {}
        self._converters = []
        self.version = 0
        self.activated = False

    def __iter__(self):
        """
        Iterate through the converters

        Yield nothing if not activated yet
        """
        if not self.activated:
            return iter([])
        return iter(self._converters)

    def append(self, converter):
        """Add a converter, we store these as a list"""
        self._converters.append(converter)

    def activate(self):
        """Mark the converters as activated"""
        self.activated = True
        self.version += 1

    @versioned_value
    def matches(self, path):
        """
        Return (converter, matches) where converter is the matched converter or None

        And matches is a boolean signifying whether there was a match
        """
        for converter in self:
            if not hasattr(converter, "matches") or converter.matches(path):
                return converter, True

        return None, False
    matches.debug = True

    def converted(self, path):
        """Return whether this path has been converted yet"""
        if not self.activated:
            return False
        return path in self._converted

    def converted_val(self, path):
        """
        Return the converted value for this path

        This function should be guarded via the use of ``self.converted``
        """
        return self._converted[path]

    def waiting(self, path):
        """Return whether we're waiting for this path"""
        return path in self._waiting

    def done(self, path, value):
        """Mark a path as been replaced by the specified value"""
        if path in self._waiting:
            del self._waiting[path]
        self._converted[path] = value

    def started(self, path):
        """Mark this path as waiting"""
        self._waiting[path] = True

