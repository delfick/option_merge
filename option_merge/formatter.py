from option_merge.versioning import VersionedDict
from option_merge.merge import MergedOptions

import string
import types
import six

class NotSpecified(object):
    """The difference between None and not specified"""

class MergedOptionStringFormatter(string.Formatter):
    """
    Resolve format options into a MergedOptions dictionary
    """
    def __init__(self, all_options, option_path, chain=None, value=NotSpecified):
        if chain is None:
            if isinstance(option_path, list):
                chain = [thing for thing in option_path]
            else:
                chain = [option_path]
        self.chain = chain
        self.value = value
        self.option_path = option_path
        self.all_options = all_options
        super(MergedOptionStringFormatter, self).__init__()

    def format(self):
        """Format our option_path into all_options"""
        val = self.value
        if val is NotSpecified:
            val = self.get_string(self.option_path)

        if not isinstance(val, six.string_types):
            return val
        return super(MergedOptionStringFormatter, self).format(val)

    def special_get_field(self, value, args, kwargs, format_spec=None):
        raise NotImplementedError()

    def special_format_field(self, obj, format_spec):
        raise NotImplementedError()

    def with_option_path(self, value):
        """Clone this instance with the new value as option_path and no override value"""
        return self.__class__(self.all_options, value, chain=self.chain + [value], value=NotSpecified)

    def get_string(self, key):
        """Get a string from all_options"""
        return self.all_options[key]

    def get_field(self, value, args, kwargs, format_spec=None):
        """Also take the spec into account"""
        special = self.special_get_field(value, args, kwargs, format_spec)
        if special is not None:
            return special
        else:
            return self.with_option_path(value).format(), ()

    def format_field(self, obj, format_spec):
        """Know about any special formats"""
        special = self.special_format_field(obj, format_spec)
        if special:
            return special
        else:
            if type(obj) in (VersionedDict, MergedOptions) or isinstance(obj, dict) or any(isinstance(obj, typ) for typ in (types.LambdaType, types.FunctionType, types.MethodType, types.BuiltinFunctionType, types.BuiltinMethodType)):
                return obj
            else:
                return super(MergedOptionStringFormatter, self).format_field(obj, format_spec)

    def _vformat(self, format_string, args, kwargs, used_args, recursion_depth):
        """I really want to know what the format_string is so I'm taking from standard library string and modifying slightly"""
        if recursion_depth < 0:
            raise ValueError('Max string recursion exceeded')

        result = []

        for literal_text, field_name, format_spec, conversion in self.parse(format_string):

            # output the literal text
            if literal_text:
                result.append(literal_text)

            # if there's a field, output it
            if field_name is not None:
                # this is some markup, find the object and do
                #  the formatting

                # given the field_name, find the object it references
                #  and the argument it came from
                # Slight modification here to pass in the format_spec
                obj, arg_used = self.get_field(field_name, args, kwargs, format_spec)
                used_args.add(arg_used)

                # do any conversion on the resulting object
                obj = self.convert_field(obj, conversion)

                # expand the format spec, if needed
                format_spec = self._vformat(format_spec, args, kwargs,
                                            used_args, recursion_depth-1)

                # format the object and append to the result
                result.append(self.format_field(obj, format_spec))

        if len(result) == 1:
            return result[0]
        return ''.join(str(obj) for obj in result)

